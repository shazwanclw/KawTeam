from test_api import HEADERS, client


def sign_in(c, profile="organiser"):
    c.post("/session", headers=HEADERS, json={"profile": profile})


def test_project_tasks_and_settings_are_validated_and_role_protected():
    with client() as c:
        sign_in(c)
        task = c.post("/events/tech-night/tasks", headers=HEADERS, json={"name": "Shirt printing"})
        assert task.status_code == 200
        assert task.json()["tasks"][0]["name"] == "Shirt printing"
        settings = {
            "mode": "liaise",
            "instructions": "Prefer local vendors",
            "shortlistSize": 2,
            "preferredVendorId": None,
        }
        assert (
            c.post("/events/tech-night/settings", headers=HEADERS, json=settings).json()[
                "assistantSettings"
            ]
            == settings
        )
        assert (
            c.post(
                "/events/tech-night/settings",
                headers=HEADERS,
                json={**settings, "shortlistSize": 4},
            ).status_code
            == 422
        )
        sign_in(c, "observer")
        assert (
            c.post("/events/tech-night/tasks", headers=HEADERS, json={"name": "Denied"}).status_code
            == 403
        )


def test_task_chats_are_isolated_and_foreign_tasks_rejected():
    with client() as c:
        sign_in(c)
        event = c.post("/events/tech-night/tasks", headers=HEADERS, json={"name": "Shirts"}).json()
        task = event["tasks"][0]["id"]
        for task_id, message in [(task, "Remember shirt printing"), (None, "General conversation")]:
            assert (
                c.post(
                    "/chat",
                    headers=HEADERS,
                    json={"eventId": "tech-night", "taskId": task_id, "message": message},
                ).status_code
                == 200
            )
        threads = c.get("/state", headers=HEADERS).json()["threads"]
        assert len(threads) == 2
        assert len(next(t for t in threads if t.get("taskId") == task)["messages"]) == 2
        assert (
            c.post(
                "/chat",
                headers=HEADERS,
                json={"eventId": "tech-night", "taskId": "not-here", "message": "Hello"},
            ).status_code
            == 422
        )


def test_repeat_vendor_requires_fresh_terms_and_does_not_research(monkeypatch):
    from fastapi.testclient import TestClient
    from test_api import MemoryRepository

    from kawteam.config import Settings
    from kawteam.main import create_app

    repo = MemoryRepository()
    repo.rows[("case", "case-totes")]["eventId"] = "tech-night"
    repo.rows[("case", "case-totes")]["selectedVendorId"] = "willow"
    repo.rows[("event", "tech-night")]["facts"] = {
        "budgetSen": 200000,
        "quantity": 50,
        "deadline": "2026-10-25",
        "location": "Subang",
    }

    def forbidden(*args):
        raise AssertionError("Repeat vendor must skip discovery")

    monkeypatch.setattr("kawteam.main.discover", forbidden)
    settings = Settings(
        session_secret="s" * 48,
        gateway_secret="g" * 48,
        workspace="test",
        gemini_key="",
        tavily_key="configured",
    )
    with TestClient(create_app(settings, repo)) as c:
        sign_in(c)
        reply = c.post(
            "/chat",
            headers=HEADERS,
            json={
                "eventId": "tech-night",
                "message": "I want to buy 20 more shirts from Willow Supply Studio",
            },
        )
        assert reply.status_code == 200
        new_case = next(
            case
            for case in reply.json()["state"]["cases"]
            if case["id"] == reply.json()["assistant"]["caseId"]
        )
        assert new_case["workflowMode"] == "liaise"
        assert new_case["quantity"] == 20
        assert new_case["selectedVendorId"] is None
        vendor = new_case["vendors"][0]
        assert vendor["id"] == "willow"
        assert vendor["goodsSen"] == 0 and vendor["deliverySen"] is None
        assert vendor["arrival"] is None and vendor["specsConfirmed"] is False
        assert new_case["draft"]["status"] == "pending"
        assert new_case["draft"]["body"]


def test_unresolved_vendor_reference_asks_instead_of_researching():
    with client() as c:
        sign_in(c)
        response = c.post(
            "/chat",
            headers=HEADERS,
            json={"eventId": "tech-night", "message": "Buy 20 more shirts from that vendor"},
        )
        assert response.status_code == 200
        assert "caseId" not in response.json()["assistant"]
        assert "which vendor" in response.json()["assistant"]["body"].lower()


def test_missing_facts_can_be_completed_in_followup_chat():
    with client() as c:
        sign_in(c)
        first = c.post(
            "/chat",
            headers=HEADERS,
            json={
                "eventId": "tech-night",
                "message": "Find vendors for 50 shirts with a budget of RM2000",
            },
        )
        assert first.json()["assistant"]["missingFacts"] == ["deadline", "location"]
        second = c.post(
            "/chat",
            headers=HEADERS,
            json={
                "eventId": "tech-night",
                "taskId": first.json()['taskId'],
                "message": "Deadline: 2026-10-25\nLocation: Subang Jaya",
            },
        )
        assert second.json()["assistant"]["caseId"]
        case = next(
            case
            for case in second.json()["state"]["cases"]
            if case["id"] == second.json()["assistant"]["caseId"]
        )
        assert case["quantity"] == 50 and case["budgetSen"] == 200000


def test_followup_budget_override_wins_and_project_references_are_ambiguous():
    with client() as c:
        sign_in(c)
        first = c.post(
            "/chat",
            headers=HEADERS,
            json={
                "eventId": "tech-night",
                "message": "Find vendors for 50 shirts with a budget of RM2000",
            },
        )
        second = c.post(
            "/chat",
            headers=HEADERS,
            json={
                "eventId": "tech-night",
                "taskId": first.json()["taskId"],
                "message": "Actually budget RM900. Deadline: 2026-10-25\nLocation: Subang",
            },
        )
        case = next(
            case
            for case in second.json()["state"]["cases"]
            if case["id"] == second.json()["assistant"]["caseId"]
        )
        assert case["budgetSen"] == 90000


def test_research_mode_preserves_entire_candidate_pool_for_liaison(monkeypatch):
    from fastapi.testclient import TestClient
    from test_api import MemoryRepository

    from kawteam.config import Settings
    from kawteam.main import create_app

    repo = MemoryRepository()
    repo.rows[("case", "case-totes")]["eventId"] = "tech-night"
    repo.rows[("case", "case-totes")]["selectedVendorId"] = "willow"
    repo.rows[("event", "tech-night")].update(
        {
            "facts": {
                "budgetSen": 200000,
                "quantity": 50,
                "deadline": "2026-10-25",
                "location": "Subang",
            },
            "assistantSettings": {"mode": "research", "shortlistSize": 2},
        }
    )
    monkeypatch.setattr(
        "kawteam.main.discover", lambda *args: repo.get("case", "case-totes")["vendors"]
    )
    settings = Settings(
        session_secret="s" * 48,
        gateway_secret="g" * 48,
        workspace="test",
        gemini_key="",
        tavily_key="configured",
    )
    with TestClient(create_app(settings, repo)) as c:
        sign_in(c)
        response = c.post(
            "/chat",
            headers=HEADERS,
            json={"eventId": "tech-night", "message": "Find vendors for shirts again"},
        )
        case = next(
            case
            for case in response.json()["state"]["cases"]
            if case["id"] == response.json()["assistant"]["caseId"]
        )
        assert case["workflowMode"] == "research"
        assert len(case["shortlistVendorIds"]) == 3
        assert case["selectedVendorId"] is None
        assert case["workflowPlan"][-1]["status"] == "pending"


def test_explicit_library_vendor_can_be_reused_across_projects_without_old_terms():
    with client() as c:
        sign_in(c)
        response = c.post(
            "/events/tech-night/settings",
            headers=HEADERS,
            json={"mode": "liaise", "preferredVendorId": "willow"},
        )
        assert response.status_code == 200
        c.post(
            "/events/tech-night/documents",
            headers=HEADERS,
            files={"file": ("plan.txt", b"Budget RM2000\nDeadline: 2026-10-25\nLocation: Subang")},
        )
        reply = c.post(
            "/chat",
            headers=HEADERS,
            json={"eventId": "tech-night", "message": "Buy 20 more shirts from that vendor"},
        )
        case = next(
            case
            for case in reply.json()["state"]["cases"]
            if case["id"] == reply.json()["assistant"]["caseId"]
        )
        assert case["vendors"][0]["id"] == "willow"
        assert case["vendors"][0]["goodsSen"] == 0
        assert case["selectedVendorId"] is None


def test_explicit_supplier_name_overrides_preference():
    from kawteam.projects import resolve_vendor
    from kawteam.workflow import seed

    case = seed()["cases"][0]
    case["eventId"] = "project"
    event = {"id": "project", "assistantSettings": {"preferredVendorId": "willow"}}
    other = next(v for v in case["vendors"] if v["id"] != "willow")
    assert (
        resolve_vendor("Contact " + other["name"], event, [case], {"messages": []})["id"]
        == other["id"]
    )


def test_explicit_workspace_name_overrides_preference_and_duplicate_names_are_ambiguous():
    from kawteam.projects import resolve_vendor

    event = {"id": "project", "assistantSettings": {"preferredVendorId": "willow"}}
    cases = [
        {
            "id": "a",
            "eventId": "elsewhere",
            "vendors": [
                {"id": "campus", "name": "Campus Print"},
                {"id": "willow", "name": "Willow Supply"},
            ],
        }
    ]
    assert resolve_vendor("Contact Campus Print", event, cases, {"messages": []})["id"] == "campus"
    cases.append(
        {"id": "b", "eventId": "elsewhere", "vendors": [{"id": "campus-2", "name": "Campus Print"}]}
    )
    assert resolve_vendor("Contact Campus Print", event, cases, {"messages": []}) is None


def test_implicit_supplier_reference_never_crosses_task_scope():
    from kawteam.projects import resolve_vendor

    event = {"id": "project"}
    cases = [
        {
            "id": "a",
            "eventId": "project",
            "taskId": "shirts",
            "selectedVendorId": "campus",
            "vendors": [{"id": "campus", "name": "Campus Print"}],
        }
    ]
    assert (
        resolve_vendor("Contact that vendor", event, cases, {"taskId": "catering", "messages": []})
        is None
    )
    assert (
        resolve_vendor("Contact that vendor", event, cases, {"taskId": None, "messages": []})
        is None
    )
    assert (
        resolve_vendor("Contact that vendor", event, cases, {"taskId": "shirts", "messages": []})[
            "id"
        ]
        == "campus"
    )


def test_more_vendors_is_discovery_not_reorder():
    from kawteam.projects import route

    event = {"id": "project", "assistantSettings": {"mode": "general"}}
    assert route("Find more vendors for catering", event, [], {"messages": []})[0] == "research"
    assert (
        route("I need 20 more shirts from that vendor", event, [], {"messages": []})[0] == "liaise"
    )


def test_ambiguous_named_supplier_returns_clarification_without_new_case():
    from fastapi.testclient import TestClient
    from test_api import MemoryRepository

    from kawteam.config import Settings
    from kawteam.main import create_app

    repo = MemoryRepository()
    vendors = repo.rows[("case", "case-totes")]["vendors"]
    vendors[0]["name"] = "Shared Printing"
    vendors[1]["name"] = "Shared Printing"
    repo.rows[("event", "tech-night")]["assistantSettings"] = {
        "mode": "general",
        "preferredVendorId": "willow",
    }
    settings = Settings(
        session_secret="s" * 48,
        gateway_secret="g" * 48,
        workspace="test",
        gemini_key="",
        tavily_key="",
    )
    with TestClient(create_app(settings, repo)) as c:
        sign_in(c)
        result = c.post(
            "/chat",
            headers=HEADERS,
            json={"eventId": "tech-night", "message": "Contact Shared Printing"},
        )
        assert "which vendor" in result.json()["assistant"]["body"].lower()
        assert "caseId" not in result.json()["assistant"]


def test_research_refresh_retains_human_choice_and_exact_approved_draft(monkeypatch):
    import copy

    from fastapi.testclient import TestClient
    from test_api import MemoryRepository

    from kawteam.config import Settings
    from kawteam.main import create_app
    from kawteam.workflow import digest

    repo = MemoryRepository()
    old = copy.deepcopy(repo.rows[("case", "case-totes")])
    old["id"] = "refresh-case"
    old["eventId"] = "tech-night"
    old["selectedVendorId"] = "willow"
    old["draft"].update({"vendorId": "willow", "status": "approved", "approvedUntil": 9999999999})
    old["draft"]["approvedHash"] = digest(old["draft"])
    draft = copy.deepcopy(old["draft"])
    repo.rows[("case", "refresh-case")] = copy.deepcopy(old)
    repo.rows[("event", "tech-night")]["assistantSettings"] = {"shortlistSize": 1}
    new_vendor = {
        **copy.deepcopy(old["vendors"][0]),
        "id": "new-vendor",
        "name": "New Search Candidate",
    }
    monkeypatch.setattr("kawteam.main.discover", lambda *args: [new_vendor])
    settings = Settings(
        session_secret="s" * 48,
        gateway_secret="g" * 48,
        workspace="test",
        gemini_key="",
        tavily_key="configured",
    )
    with TestClient(create_app(settings, repo)) as c:
        sign_in(c)
        result = c.post(
            "/actions",
            headers=HEADERS,
            json={"type": "research", "caseId": "refresh-case", "expectedRevision": 1},
        )
        assert result.status_code == 200
        case = next(case for case in result.json()["cases"] if case["id"] == "refresh-case")
        assert case["selectedVendorId"] == "willow"
        assert case["draft"] == draft
        assert {"new-vendor", "willow"} <= {v["id"] for v in case["vendors"]}
        assert case["shortlistVendorIds"] == ["new-vendor"]
        assert case["workflowPlan"][1]["status"] == "complete"
        assert case["workflowPlan"][-1]["status"] == "complete"
