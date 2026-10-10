import io

from fastapi.testclient import TestClient
from test_api import HEADERS, MemoryRepository

from kawteam.config import Settings
from kawteam.main import create_app
from kawteam.tasks import project_name


def client(repo):
    settings = Settings(workspace="test", gateway_secret="g" * 48, session_secret="s" * 48, gemini_key="", tavily_key="", gmail_sender="", gmail_authorized_user_json="")
    return TestClient(create_app(settings, repo))


def test_project_names_are_short_and_preserve_explicit_events():
    assert project_name("I want to buy a tshirt for less than RM40, I heard in email Muhda") == "T-shirt Sourcing"
    assert project_name("Find 50 shirts under RM2000") == "T-shirt Sourcing"
    assert project_name("Find catering within RM1000") == "Catering & Food"
    assert project_name("Find 50 shirts for event Sunway Got Talent within RM2000") == "Sunway Got Talent"
    assert len(project_name("Can you help me arrange a business thing with quite a few different details?")) < 40


def test_first_chat_file_is_read_before_response_and_is_task_scoped(monkeypatch):
    import json
    repo = MemoryRepository()
    contexts = []
    monkeypatch.setattr("kawteam.main.chat_response", lambda message, event, context, *args: contexts.append(context) or {"reply": "Reference read.", "action": "none", "provider": "gemini"})
    with client(repo) as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        payload = {"requestId": "reference-first", "message": "Find shirts using this brief"}
        response = c.post("/chat/references", headers=HEADERS, data={"payload": json.dumps(payload)}, files={"files": ("brief.txt", io.BytesIO(b"We need 50 shirts. Budget RM2000."), "text/plain")})
        assert response.status_code == 200, response.text
        first = response.json()
        assert contexts[0][0]["excerpt"].startswith("We need 50")
        docs = repo.documents(first["eventId"])
        assert docs[0]["taskId"] == first["taskId"]
        assert not repo.get("event", first["eventId"])["facts"]
        retry = c.post("/chat/references", headers=HEADERS, data={"payload": json.dumps(payload)}, files={"files": ("brief.txt", b"We need 50 shirts. Budget RM2000.", "text/plain")})
        assert retry.status_code == 200 and retry.json()["taskId"] == first["taskId"]
        assert len(repo.documents(first["eventId"])) == 1
        c.post("/chat", headers=HEADERS, json={"eventId": first["eventId"], "message": "Arrange catering"})
        assert contexts[-1] == []


def test_invalid_file_does_not_create_a_project():
    repo = MemoryRepository()
    with client(repo) as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        response = c.post("/chat/references", headers=HEADERS, data={"payload": '{"message":"Find shirts"}'}, files={"files": ("photo.png", b"image", "image/png")})
        assert response.status_code == 422
        assert len(repo.snapshot()["events"]) == 1


def test_drive_sync_does_not_promote_task_attachment_facts_into_project_memory(monkeypatch):
    repo = MemoryRepository()
    repo.rows[("document", "task-file")] = {"id": "task-file", "eventId": "tech-night", "taskId": "shirts", "text": "We need 50 shirts. Budget RM2000.", "status": "ready"}
    monkeypatch.setattr("kawteam.main.read_drive", lambda *a: {"status": "ready", "documents": [], "errors": [], "message": "Empty folder"})
    with client(repo) as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        result = c.post("/events/tech-night/drive", headers=HEADERS, json={"url": "https://drive.google.com/drive/folders/abcdefghijk123"})
        assert result.status_code == 200
        assert result.json()["facts"] == {}
