from test_api import HEADERS, client
from test_projects import sign_in


def send(c, message, **scope):
    response = c.post("/chat", headers=HEADERS, json={"message": message, **scope})
    assert response.status_code == 200, response.text
    return response.json()


def test_new_conversations_create_retry_safe_tasks_and_named_project():
    with client() as c:
        sign_in(c)
        body = {
            "requestId": "task-first",
            "message": "I want 50 shirts within RM5000 for event Sunway Got Talent",
        }
        first = send(c, **body)
        project = next(p for p in first["state"]["events"] if p["id"] == first["eventId"])
        assert project["name"] == "Sunway Got Talent"
        assert first.get("taskId")
        assert project["tasks"][0]["name"] == "T-shirt merchandise"
        retry = send(c, **body)
        assert retry["taskId"] == first["taskId"]
        assert (
            len(next(p for p in retry["state"]["events"] if p["id"] == first["eventId"])["tasks"])
            == 1
        )
        assert len(retry["state"]["threads"][0]["messages"]) == 2
        other = send(c, "Find catering", eventId=first["eventId"])
        assert other["taskId"] != first["taskId"]


def test_task_followups_update_request_in_place_and_clear_stale_terms():
    with client() as c:
        sign_in(c)
        first = send(
            c,
            "Find vendors for 50 shirts within RM2000 by 25 October 2026 in Subang Jaya.",
            eventId="tech-night",
        )
        assert first.get("taskId")
        case_id = first["assistant"]["caseId"]
        updated = send(
            c, "We only want 40 shirts now.", eventId="tech-night", taskId=first["taskId"]
        )
        cases = [r for r in updated["state"]["cases"] if r.get("taskId") == first["taskId"]]
        assert len(cases) == 1
        assert cases[0]["id"] == case_id
        assert cases[0]["quantity"] == 40
        assert updated["assistant"]["caseId"] == case_id
        answered = send(
            c, "What is my current budget?", eventId="tech-night", taskId=first["taskId"]
        )
        assert "2,000" in answered["assistant"]["body"]
        assert (
            len([r for r in answered["state"]["cases"] if r.get("taskId") == first["taskId"]]) == 1
        )
        thread = next(t for t in answered["state"]["threads"] if t.get("taskId") == first["taskId"])
        assert len(thread["messages"]) == 6


def test_specification_edits_refresh_terms_but_unchanged_facts_do_not():
    with client() as c:
        sign_in(c)
        first = send(
            c,
            "Find vendors for 50 shirts within RM2000 by 25 October 2026 in Subang Jaya.",
            eventId="tech-night",
        )
        edit = send(
            c, "Change the shirt colour to blue.", eventId="tech-night", taskId=first["taskId"]
        )
        request = next(r for r in edit["state"]["cases"] if r["id"] == first["assistant"]["caseId"])
        assert "blue" in request["goal"]
        same = send(c, "Our budget is still RM2000.", eventId="tech-night", taskId=first["taskId"])
        after = next(r for r in same["state"]["cases"] if r["id"] == request["id"])
        assert after["backendRevision"] == request["backendRevision"]


def test_multi_vendor_slots_are_separate_from_item_quantity():
    with client() as c:
        sign_in(c)
        result = send(
            c,
            "Find 10 vendors within RM5000 by 25 October 2026 in Subang Jaya.",
            eventId="tech-night",
        )
        assert result.get("taskId")
        case = next(r for r in result["state"]["cases"] if r["id"] == result["assistant"]["caseId"])
        assert case["selectionTarget"] == 10
        assert case["quantity"] == 1
        assert case["taskWorkflowVersion"] == 1


def test_missing_facts_continue_in_the_selected_task():
    with client() as c:
        sign_in(c)
        first = send(c, "Find vendors for 50 shirts within RM2000", eventId="tech-night")
        assert first.get("taskId")
        second = send(
            c,
            "Deadline: 2026-10-25\nLocation: Subang Jaya",
            eventId="tech-night",
            taskId=first["taskId"],
        )
        case = next(r for r in second["state"]["cases"] if r["id"] == second["assistant"]["caseId"])
        assert case["quantity"] == 50
        assert case["taskId"] == first["taskId"]


def test_legacy_case_conversation_is_materialised_without_losing_its_request():
    from fastapi.testclient import TestClient
    from test_api import MemoryRepository

    from kawteam.config import Settings
    from kawteam.main import create_app

    repo = MemoryRepository()
    repo.rows[("case", "case-totes")]["eventId"] = "tech-night"
    with TestClient(
        create_app(
            Settings(session_secret="s" * 48, gateway_secret="g" * 48, workspace="test"), repo
        )
    ) as c:
        sign_in(c)
        response = send(c, "What is this task about?", eventId="tech-night", taskId="case-totes")
        assert response["taskId"] == "case-totes"
        assert any(t["id"] == "case-totes" for t in response["state"]["events"][0]["tasks"])


def test_previous_general_conversation_remains_readable_when_resumed_as_task():
    from fastapi.testclient import TestClient
    from test_api import MemoryRepository

    from kawteam.config import Settings
    from kawteam.main import create_app

    repo = MemoryRepository()
    old = {
        "id": "old-user",
        "role": "user",
        "body": "Our earlier project note",
        "time": "2026-10-10T10:00:00Z",
    }
    repo.append_message("tech-night", old, "organiser")
    repo.append_message(
        "tech-night",
        {
            "id": "old-assistant",
            "role": "assistant",
            "body": "Saved note",
            "inReplyTo": "old-user",
            "time": "2026-10-10T10:00:01Z",
        },
        "organiser",
    )
    with TestClient(
        create_app(
            Settings(session_secret="s" * 48, gateway_secret="g" * 48, workspace="test"), repo
        )
    ) as c:
        sign_in(c)
        result = send(
            c, "Continue this conversation", eventId="tech-night", taskId="legacy-tech-night"
        )
        thread = next(
            t for t in result["state"]["threads"] if t.get("taskId") == "legacy-tech-night"
        )
        assert len(thread["messages"]) == 4
        assert thread["messages"][0]["body"] == old["body"]
