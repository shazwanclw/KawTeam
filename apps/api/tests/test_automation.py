import copy

import pytest
from test_liaison import setup


def runner(service, resolver=None, interpreter=None):
    from kawteam.automation import Automation

    return Automation(
        service, resolver or (lambda vendor, case: None), interpreter or (lambda case, message: {})
    )


def authorise(repo):
    from kawteam.liaison import request_token

    case = repo.rows[("case", "live-task")]
    case["automation"] = {
        "requestHash": request_token(case),
        "authorisedBy": "organiser",
        "status": "queued",
    }


def test_no_send_without_task_authorisation_and_observer_cannot_tick():
    _repo, mail, service = setup()
    with pytest.raises(ValueError, match="authoris"):
        runner(service).tick("live-task", "teammate")
    with pytest.raises(PermissionError):
        runner(service).tick("live-task", "observer")
    assert mail.sent == []


def test_exhausted_contacts_expand_search_then_send_to_verified_replacement():
    from kawteam.automation import Automation

    repo, mail, service = setup()
    authorise(repo)
    case = repo.rows[("case", "live-task")]
    old = case["vendors"][0]
    old["sourceUrl"] = "https://old.example.com"
    old["outreachBlock"] = "No verified contact"
    fresh = {**copy.deepcopy(old), "id": "replacement", "sourceUrl": "https://new.example.com"}
    fresh.pop("outreachBlock")
    calls = []

    def research(c):
        calls.append(c["id"])
        return [copy.deepcopy(old), copy.deepcopy(fresh)]

    engine = Automation(service, lambda *args: None, lambda *args: {}, research)
    result = engine.tick("live-task", "teammate")
    assert len(result["vendors"]) == 2
    assert result["automation"]["status"] == "queued"
    assert result["automation"]["discoveryRounds"] == 1
    assert mail.sent == []
    engine.tick("live-task", "teammate")
    assert len(mail.sent) == 1
    assert len(calls) == 1


def test_replacement_search_stops_after_two_rounds_and_does_not_invent_contacts():
    from kawteam.automation import Automation
    repo, mail, service = setup()
    authorise(repo)
    case=repo.rows[('case','live-task')]
    case['vendors'][0]['outreachBlock']='No verified contact'
    calls=[]
    def research(c):
        calls.append(c['id'])
        return []
    engine=Automation(service,lambda *args: None,lambda *args: {},research)
    for _ in range(4):
        result=engine.tick('live-task','teammate')
    assert len(calls)==2
    assert result['automation']['status']=='needs_attention'
    assert mail.sent==[]


def test_initial_tick_sends_real_enquiry_once_and_never_selects_supplier():
    repo, mail, service = setup()
    authorise(repo)
    engine = runner(service)
    first = engine.tick("live-task", "teammate")
    assert first["messages"][-1]["direction"] == "sent"
    assert first["messages"][-1]["providerMessageId"] == "sent-1"
    engine.tick("live-task", "teammate")
    assert mail.sent == ["test@gmail.com"]
    assert repo.get("case", "live-task")["vendorDecisions"] == []


def test_changed_scope_does_not_send_old_request():
    repo, mail, service = setup()
    authorise(repo)
    repo.rows[("case", "live-task")]["quantity"] += 1
    with pytest.raises(ValueError, match="changed"):
        runner(service).tick("live-task", "teammate")
    assert mail.sent == []


def test_missing_contact_is_recorded_and_other_vendors_can_continue():
    repo, mail, service = setup()
    repo.rows[("case", "live-task")]["vendors"][0].pop("contact")
    authorise(repo)
    result = runner(service).tick("live-task", "teammate")
    assert result["vendors"][0]["outreachBlock"]
    assert mail.sent == []


def test_official_source_contact_can_send_without_manual_contact_form():
    repo, mail, service = setup()
    vendor = repo.rows[("case", "live-task")]["vendors"][0]
    vendor.pop("contact")
    vendor["sourceUrl"] = "https://print.example.com/shirts"
    authorise(repo)
    contact = {
        "email": "sales@print.example.com",
        "verifiedBy": "public_source",
        "sourceUrl": "https://print.example.com/contact",
        "evidenceExcerpt": "Shirt printing enquiries: sales@print.example.com",
        "serviceEvidence": "Shirt printing",
        "verifiedAt": "2026-10-11T00:00:00+00:00",
    }
    engine = runner(service, lambda vendor, case: copy.deepcopy(contact))
    engine.tick("live-task", "teammate")
    assert mail.sent == ["sales@print.example.com"]
    result = engine.tick("live-task", "teammate")
    assert mail.sent == ["sales@print.example.com"]
    assert result["vendors"][0]["contact"]["sourceUrl"].endswith("/contact")


def test_uncertain_send_is_never_automatically_retried():
    repo, mail, service = setup()
    authorise(repo)
    mail.fail = True
    engine = runner(service)
    result = engine.tick("live-task", "teammate")
    assert result["emailIntents"][0]["status"] == "uncertain"
    engine.tick("live-task", "teammate")
    assert len(mail.sent) == 1


def test_saved_reply_is_interpreted_then_missing_terms_are_requested_once():
    from kawteam.liaison import request_token

    repo, mail, service = setup()
    authorise(repo)
    interpretation = {
        "final": False,
        "confirmation": False,
        "quantity": None,
        "goodsSen": None,
        "deliverySen": None,
        "arrival": None,
        "specsConfirmed": False,
        "validUntil": None,
        "evidence": {},
    }
    engine = runner(service, interpreter=lambda case, message: interpretation)
    engine.tick("live-task", "teammate")
    mail.incoming = [
        {
            "providerMessageId": "reply-1",
            "providerThreadId": "thread-1",
            "rfcMessageId": "<reply-1@test.com>",
            "rfcInReplyTo": repo.get("case", "live-task")["emailIntents"][0]["rfcMessageId"],
            "body": "Thanks, what details do you need?",
            "receivedAtMs": 1,
        }
    ]
    engine.tick("live-task", "teammate")
    result = engine.tick("live-task", "teammate")
    assert result["messages"][-1]["quoteInterpretation"]["final"] is False
    engine.tick("live-task", "teammate")
    engine.tick("live-task", "teammate")
    assert len(mail.sent) == 2
    assert all(
        i["requestHash"] == request_token(result)
        for i in repo.get("case", "live-task")["emailIntents"]
    )


def test_chat_queues_task_outreach_and_tick_requires_editable_session(monkeypatch):
    from fastapi.testclient import TestClient
    from test_api import HEADERS

    from kawteam.config import Settings
    from kawteam.main import create_app

    repo, mail, _service = setup()
    settings = Settings(
        workspace="test",
        gateway_secret="g" * 48,
        session_secret="s" * 48,
        gmail_sender="sender@gmail.com",
        gmail_authorized_user_json="{}",
        tavily_key="test",
        gemini_key="",
    )
    monkeypatch.setattr("kawteam.main.Gmail.from_settings", lambda settings: mail)
    monkeypatch.setattr(
        "kawteam.main.discover", lambda *args: repo.get("case", "live-task")["vendors"]
    )
    monkeypatch.setattr(
        "kawteam.main.chat_response",
        lambda *args: {
            "reply": "I will find suitable suppliers.",
            "action": "find_vendors",
            "brief": {
                "title": "Shirts",
                "goal": "Find printed shirts",
                "quantity": 50,
                "budgetSen": 200000,
                "targetSen": 150000,
                "deadline": "2026-11-20",
                "location": "Subang Jaya",
            },
            "provider": "gemini",
            "citations": [],
        },
    )
    with TestClient(create_app(settings, repo)) as client:
        client.post("/session", headers=HEADERS, json={"profile": "organiser"})
        response = client.post(
            "/chat",
            headers=HEADERS,
            json={
                "message": "Find 50 printed shirts for RM2000 by 2026-11-20 in Subang Jaya",
                "eventId": "tech-night",
                "requestId": "new-outreach",
            },
        )
        assert response.status_code == 200
        case = next(
            c
            for c in response.json()["state"]["cases"]
            if c.get("taskId") == response.json()["taskId"]
        )
        assert case["automation"]["status"] == "queued"
        assert mail.sent == []
        response = client.post("/automation/tick", headers=HEADERS, json={"caseId": case["id"]})
        assert response.status_code == 200
        assert mail.sent == ["test@gmail.com"]
        client.post("/automation/tick", headers=HEADERS, json={"caseId": case["id"]})
        assert len(mail.sent) == 1
        client.post("/session", headers=HEADERS, json={"profile": "observer"})
        assert (
            client.post(
                "/automation/tick", headers=HEADERS, json={"caseId": case["id"]}
            ).status_code
            == 403
        )


def test_negative_chat_instruction_pauses_previously_queued_outreach(monkeypatch):
    from fastapi.testclient import TestClient
    from test_api import HEADERS

    from kawteam.config import Settings
    from kawteam.main import create_app

    repo, mail, _ = setup()
    authorise(repo)
    repo.rows[("event", "tech-night")]["tasks"] = [{"id": "task-1", "name": "Shirts"}]
    monkeypatch.setattr(
        "kawteam.main.chat_response",
        lambda *args: {
            "reply": "I will not email anyone.",
            "action": "none",
            "provider": "gemini",
            "citations": [],
        },
    )
    settings = Settings(
        workspace="test",
        gateway_secret="g" * 48,
        session_secret="s" * 48,
        gmail_sender="sender@gmail.com",
        gmail_authorized_user_json="{}",
        tavily_key="",
        gemini_key="",
    )
    with TestClient(create_app(settings, repo)) as client:
        client.post("/session", headers=HEADERS, json={"profile": "organiser"})
        response = client.post(
            "/chat",
            headers=HEADERS,
            json={"message": "Do not email suppliers", "eventId": "tech-night", "taskId": "task-1"},
        )
        assert response.status_code == 200
        assert repo.get("case", "live-task")["automation"]["status"] == "paused"
        assert "queued" not in response.json()["assistant"]["body"]
        with pytest.raises(ValueError, match="paused"):
            runner(_).tick("live-task", "teammate")
    assert mail.sent == []


def test_active_task_lease_prevents_a_second_runner_from_sending():
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    repo, mail, service = setup()
    authorise(repo)
    repo.rows[("case", "live-task")]["automation"]["leaseUntil"] = (
        datetime.now(ZoneInfo("Asia/Kuala_Lumpur")) + timedelta(minutes=2)
    ).isoformat()
    runner(service).tick("live-task", "teammate")
    assert mail.sent == []


def test_post_approval_confirmation_is_interpreted_and_secures_matching_terms():
    from kawteam.liaison import request_token
    from kawteam.tasks import term_token

    repo, mail, service = setup()
    authorise(repo)
    case = repo.rows[("case", "live-task")]
    vendor = case["vendors"][0]
    vendor.update(
        quantity=case["quantity"],
        goodsSen=120000,
        deliverySen=0,
        arrival=case["deadline"],
        specsConfirmed=True,
        validUntil="2099-01-01",
        liaisonStatus="ready",
    )
    case["vendorDecisions"] = [
        {
            "id": "approval-1",
            "vendorId": vendor["id"],
            "status": "approved",
            "termsHash": term_token(case, vendor),
            "approvedAt": "2026-10-11T00:00:00+00:00",
        }
    ]
    body = f"Confirmed availability for {case['quantity']} units, goods RM1200, delivery free, arrival {case['deadline']}, valid 2099-01-01; specifications confirmed."
    case["messages"] = [
        {
            "id": "reply-1",
            "vendorId": vendor["id"],
            "direction": "received",
            "executionMode": "live",
            "gmailSender": mail.sender,
            "requestHash": request_token(case),
            "providerMessageId": "reply-1",
            "receivedAtMs": 1791676800001,
            "body": body,
        }
    ]
    data = {
        "final": False,
        "confirmation": True,
        "quantity": case["quantity"],
        "goodsSen": 120000,
        "deliverySen": 0,
        "arrival": case["deadline"],
        "specsConfirmed": True,
        "validUntil": "2099-01-01",
        "evidence": {
            key: body
            for key in [
                "confirmation",
                "quantity",
                "goodsSen",
                "deliverySen",
                "arrival",
                "specsConfirmed",
                "validUntil",
            ]
        },
    }
    result = runner(service, interpreter=lambda case, message: data).tick("live-task", "teammate")
    assert result["vendorDecisions"][0]["status"] == "secured"
    assert mail.sent == []


def test_concurrent_contact_save_does_not_turn_a_cas_conflict_into_a_supplier_block():
    repo, mail, service = setup()
    case = repo.rows[("case", "live-task")]
    saved_contact = case["vendors"][0].pop("contact")
    authorise(repo)

    def resolve(vendor, case):
        current = repo.get("case", "live-task")
        current["vendors"][0]["contact"] = copy.deepcopy(saved_contact)
        service.save(current, "teammate")
        return copy.deepcopy(saved_contact)

    result = runner(service, resolve).tick("live-task", "teammate")
    assert "outreachBlock" not in result["vendors"][0]
    assert mail.sent == []


def test_failed_contact_does_not_prevent_outreach_to_another_supplier():
    repo, mail, service = setup()
    case = repo.rows[("case", "live-task")]
    another = dict(copy.deepcopy(case["vendors"][0]), id="second", name="Second supplier")
    case["vendors"][0].pop("contact")
    case["vendors"].append(another)
    authorise(repo)
    engine = runner(service)
    engine.tick("live-task", "teammate")
    engine.tick("live-task", "teammate")
    assert mail.sent == ["test@gmail.com"]
    assert repo.get("case", "live-task")["emailIntents"][0]["vendorId"] == "second"


@pytest.mark.parametrize(
    "message",
    ["List vendor email addresses", "Show their contact details", "What emails have been sent?"],
)
def test_reading_contact_details_does_not_authorise_outreach(monkeypatch, message):
    from fastapi.testclient import TestClient
    from test_api import HEADERS

    from kawteam.config import Settings
    from kawteam.main import create_app

    repo, mail, _ = setup()
    repo.rows[("event", "tech-night")]["tasks"] = [{"id": "task-1", "name": "Shirts"}]
    monkeypatch.setattr(
        "kawteam.main.chat_response",
        lambda *args: {
            "reply": "Here are the saved details.",
            "action": "none",
            "provider": "gemini",
            "citations": [],
        },
    )
    settings = Settings(
        workspace="test",
        gateway_secret="g" * 48,
        session_secret="s" * 48,
        gmail_sender="sender@gmail.com",
        gmail_authorized_user_json="{}",
        tavily_key="",
        gemini_key="",
    )
    with TestClient(create_app(settings, repo)) as client:
        client.post("/session", headers=HEADERS, json={"profile": "organiser"})
        response = client.post(
            "/chat",
            headers=HEADERS,
            json={"message": message, "eventId": "tech-night", "taskId": "task-1"},
        )
        assert response.status_code == 200
        assert "automation" not in repo.get("case", "live-task")
    assert mail.sent == []


def test_complete_above_budget_quote_gets_a_bounded_revision_request():
    from kawteam.liaison import request_token

    repo, mail, service = setup()
    authorise(repo)
    case = repo.rows[("case", "live-task")]
    vendor = case["vendors"][0]
    vendor.update(
        liaisonStatus="ready",
        quantity=case["quantity"],
        goodsSen=case["budgetSen"] + 1,
        deliverySen=0,
        arrival=case["deadline"],
        specsConfirmed=True,
    )
    case["messages"] = [
        {
            "id": "quote",
            "vendorId": vendor["id"],
            "direction": "received",
            "executionMode": "live",
            "gmailSender": mail.sender,
            "requestHash": request_token(case),
            "providerMessageId": "quote-1",
            "receivedAtMs": 1,
            "quoteInterpretation": {"final": True, "confirmation": False},
        }
    ]
    engine = runner(service)
    engine.tick("live-task", "teammate")
    assert mail.sent == ["test@gmail.com"]
    engine.tick("live-task", "teammate")
    assert len(mail.sent) == 1


def test_no_more_unselected_supplier_enquiries_after_target_slots_are_filled():
    from kawteam.tasks import term_token

    repo, mail, service = setup()
    authorise(repo)
    case = repo.rows[("case", "live-task")]
    first = case["vendors"][0]
    first.update(liaisonStatus="ready")
    case["vendors"].append(dict(copy.deepcopy(first), id="second", liaisonStatus="discovered"))
    case["vendorDecisions"] = [
        {
            "id": "decision",
            "vendorId": first["id"],
            "status": "approved",
            "termsHash": term_token(case, first),
            "approvedAt": "2026-10-11T00:00:00+00:00",
        }
    ]
    runner(service).tick("live-task", "teammate")
    assert mail.sent == []
