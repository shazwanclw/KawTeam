from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from test_api import HEADERS, MemoryRepository
from test_automation import authorise, runner
from test_liaison import setup

from kawteam.config import Settings
from kawteam.main import create_app, create_case
from kawteam.tasks import task_queue


def test_quantity_and_location_can_be_unknown_and_deadline_defaults_to_two_weeks():
    case = create_case({"title": "Shirts", "goal": "Find printed shirts", "budgetSen": 200000}, "new", "project")
    assert case["quantity"] is None and case["location"] is None
    assert case["deadline"] == (datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date() + timedelta(days=14)).isoformat()
    assert "deadline" in case["assumptions"]


def test_sparse_enquiry_omits_unknown_details_and_requests_pricing_tiers():
    repo, mail, service = setup()
    case = repo.rows[("case", "live-task")]
    case.update(quantity=None, location=None)
    authorise(repo)
    result = runner(service).tick("live-task", "teammate")
    body = result["messages"][-1]["body"]
    assert "Quantity: None" not in body and "Delivery to:" not in body
    assert "pricing tiers" in body.lower()
    assert "RM1500" in body
    assert mail.sent == ["test@gmail.com"]


def test_unknown_user_quantity_cannot_be_approved_even_if_supplier_offers_a_quantity():
    repo, _, _ = setup()
    case = repo.rows[("case", "live-task")]
    case.update(quantity=None, budgetSen=None)
    case["vendors"][0].update(liaisonStatus="ready", quantity=100, goodsSen=100000, deliverySen=0, arrival=case["deadline"], specsConfirmed=True)
    rows = task_queue(case)
    assert all(r["status"] != "approval_needed" for r in rows)
    assert "quantity" in rows[0]["reason"].lower()


def test_chat_researches_sparse_request_and_failsafe_resolves_when_quantity_is_supplied(monkeypatch):
    repo = MemoryRepository()
    settings = Settings(workspace="test", gateway_secret="g"*48, session_secret="s"*48, tavily_key="test", gemini_key="", gmail_sender="test@gmail.com", gmail_authorized_user_json="{}")
    calls = []
    def discover(case, key):
        calls.append(case["quantity"])
        return []
    monkeypatch.setattr("kawteam.main.discover", discover)
    monkeypatch.setattr("kawteam.main.chat_response", lambda *args: {"reply": "I'll start looking.", "action": "find_vendors", "provider": "gemini", "citations": [], "brief": {"title": "Shirts", "goal": "Find printed shirts", "budgetSen": 200000}})
    with TestClient(create_app(settings, repo)) as client:
        client.post("/session", headers=HEADERS, json={"profile": "organiser"})
        result = client.post("/chat", headers=HEADERS, json={"eventId": "tech-night", "message": "Find shirt printers, budget RM2000"})
        assert result.status_code == 200
        case_id = result.json()["assistant"]["caseId"]
        case = repo.get("case", case_id)
        assert case["automation"]["status"] == "queued"
        assert calls == [None]
        assert "quantity" in [f["code"] for f in case["failsafes"] if f["status"] == "open"]
        assert "I still need" not in result.json()["assistant"]["body"]
        assert "approve" not in result.json()["assistant"]["body"].lower()
        response = client.post("/chat", headers=HEADERS, json={"eventId": "tech-night", "taskId": result.json()["taskId"], "message": "We need 50 shirts"})
        assert response.status_code == 200
        updated = repo.get("case", case_id)
        assert updated["quantity"] == 50
        assert all(f["status"] == "resolved" for f in updated["failsafes"] if f["code"] == "quantity")


def test_failsafes_are_stable_and_optional_location_does_not_trigger_one():
    from kawteam.failsafes import refresh_context_failsafes
    case = {"id": "case", "quantity": None, "budgetSen": 200000, "location": None, "deadline": "2026-11-01", "vendors": []}
    refresh_context_failsafes(case)
    original = case["failsafes"][0]["id"]
    refresh_context_failsafes(case)
    assert len(case["failsafes"]) == 1 and case["failsafes"][0]["id"] == original
    case["quantity"] = 50
    refresh_context_failsafes(case)
    assert case["failsafes"][0]["status"] == "resolved"


def test_per_unit_price_is_not_mistaken_for_total_budget():
    from kawteam.memory import facts_from_text
    unknown = facts_from_text("Find shirts for less than RM40 each")
    assert unknown["unitBudgetSen"] == 4000
    assert "budgetSen" not in unknown
    known = facts_from_text("Find 50 shirts for less than RM40 each")
    assert known["budgetSen"] == 200000 and known["unitBudgetSen"] == 4000


def test_progress_counts_only_recorded_current_scope_and_is_stable():
    from kawteam.liaison import request_token
    from kawteam.progress import progress_message
    repo, _, _ = setup()
    case = repo.rows[("case", "live-task")]
    assert progress_message(case) is None
    case["messages"] = [{"direction": "sent", "executionMode": "live", "requestHash": request_token(case)}, {"direction": "sent", "executionMode": "live", "requestHash": "old"}]
    first = progress_message(case)
    assert "Sent 1 supplier message" in first["body"]
    assert first["id"] == progress_message(case)["id"]


def test_all_contact_routes_exhausted_opens_failsafe_only_after_trying_candidates():
    repo, _, service = setup()
    case = repo.rows[("case", "live-task")]
    case["vendors"][0].pop("contact")
    authorise(repo)
    engine = runner(service)
    first = engine.tick("live-task", "teammate")
    assert not any(f["code"] == "outreach_exhausted" for f in first.get("failsafes", []))
    second = engine.tick("live-task", "teammate")
    assert any(f["code"] == "outreach_exhausted" and f["status"] == "open" for f in second["failsafes"])


def test_collection_is_a_fulfilment_arrangement_not_an_unknown_address():
    from kawteam.enquiries import enquiry_body
    from kawteam.memory import facts_from_text
    facts = facts_from_text("We will collect from the supplier")
    assert facts["location"].startswith("Collection")
    assert "Fulfilment: Collection" in enquiry_body({"goal": "Shirts", **facts})


def test_explicit_total_budget_overrides_prior_per_item_limit():
    repo = MemoryRepository()
    settings = Settings(workspace="test", gateway_secret="g"*48, session_secret="s"*48, gemini_key="", tavily_key="", gmail_sender="", gmail_authorized_user_json="")
    with TestClient(create_app(settings, repo)) as client:
        client.post("/session", headers=HEADERS, json={"profile": "organiser"})
        first = client.post("/chat", headers=HEADERS, json={"eventId": "tech-night", "message": "Find 50 shirts for less than RM40 each"}).json()
        second = client.post("/chat", headers=HEADERS, json={"eventId": "tech-night", "taskId": first["taskId"], "message": "Change total budget to RM1000"}).json()
        case = repo.get("case", second["assistant"]["caseId"])
        assert case["budgetSen"] == 100000 and not case.get("unitBudgetSen")


def test_model_nulls_do_not_erase_saved_scope_in_budget_edit(monkeypatch):
    repo = MemoryRepository()
    settings = Settings(workspace="test", gateway_secret="g"*48, session_secret="s"*48, gemini_key="", tavily_key="", gmail_sender="", gmail_authorized_user_json="")
    with TestClient(create_app(settings, repo)) as client:
        client.post("/session", headers=HEADERS, json={"profile": "organiser"})
        first = client.post("/chat", headers=HEADERS, json={"eventId": "tech-night", "message": "Find 50 shirts within RM2000 by 25 October 2026 in Subang Jaya."}).json()
        monkeypatch.setattr("kawteam.main.chat_response", lambda *a: {"reply": "Updated.", "action": "find_vendors", "provider": "gemini", "brief": {"quantity": None, "location": None, "deadline": None, "budgetSen": 100000}})
        second = client.post("/chat", headers=HEADERS, json={"eventId": "tech-night", "taskId": first["taskId"], "message": "Change budget to RM1000"}).json()
        case = repo.get("case", second["assistant"]["caseId"])
        assert case["quantity"] == 50 and case["location"] == "Subang Jaya" and case["deadline"] == "2026-10-25"


def test_total_and_item_constraints_are_kept_separately():
    from kawteam.memory import facts_from_text
    facts = facts_from_text("Find 50 shirts, total budget RM1000, under RM40 each")
    assert facts["budgetSen"] == 100000 and facts["unitBudgetSen"] == 4000
    assert facts["budgetSource"] == "total"


def test_per_item_limit_is_enforced_even_with_larger_total_budget():
    from kawteam.workflow import fit
    repo, _, _ = setup()
    case = repo.rows[("case", "live-task")]
    case.update(quantity=50, budgetSen=500000, unitBudgetSen=4000)
    vendor = case["vendors"][0]
    vendor.update(quantity=50, goodsSen=250000, deliverySen=0, arrival=case["deadline"], specsConfirmed=True)
    assert fit(case, vendor) == "Above item price limit"


def test_progress_is_saved_once_in_existing_task_transcript():
    from kawteam.liaison import request_token
    from kawteam.progress import save_progress
    repo, _, _ = setup()
    case = repo.rows[("case", "live-task")]
    thread_id = f"event-{case['eventId']}-task-{case['taskId']}"
    repo.rows[("thread", thread_id)] = {"id": thread_id, "eventId": case["eventId"], "taskId": case["taskId"], "backendRevision": 1, "messages": []}
    case["messages"] = [{"direction": "sent", "executionMode": "live", "requestHash": request_token(case)}]
    save_progress(repo, case, "teammate")
    save_progress(repo, case, "teammate")
    thread = repo.get("thread", thread_id)
    assert len(thread["messages"]) == 1 and thread["messages"][0]["time"]
