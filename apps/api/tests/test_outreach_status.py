from kawteam.tasks import task_queue
from kawteam.workflow import seed


def test_uncontacted_supplier_is_not_reported_as_awaiting_reply():
    case = seed()["cases"][0]
    case["taskWorkflowVersion"] = 1
    case["messages"] = []
    vendor = case["vendors"][0]
    vendor["executionMode"] = "live"
    row = next(r for r in task_queue(case) if r["vendorId"] == vendor["id"])
    assert row["reason"] == "Contact details need verification; no email sent"
    vendor["contact"] = {"email": "test@gmail.com", "verifiedBy": "organiser"}
    row = next(r for r in task_queue(case) if r["vendorId"] == vendor["id"])
    assert row["reason"] == "Not contacted yet"
    case["messages"].append({"id": "sent", "vendorId": vendor["id"], "direction": "sent"})
    row = next(r for r in task_queue(case) if r["vendorId"] == vendor["id"])
    assert row["reason"] == "Enquiry sent; awaiting supplier reply"


def test_api_chat_provides_configured_mail_and_unsent_task_status(monkeypatch):
    from fastapi.testclient import TestClient
    from test_api import HEADERS, MemoryRepository

    from kawteam.config import Settings
    from kawteam.main import create_app
    repo = MemoryRepository()
    repo.rows[("event", "tech-night")]["tasks"] = [{"id": "shirts", "name": "Shirts"}]
    case = repo.rows[("case", "case-totes")]
    case.update(eventId="tech-night", taskId="shirts", taskWorkflowVersion=1)
    case["messages"] = []
    def response(message, event, context, history, settings):
        status = event["executionStatus"]
        assert status["email"] == "configured"
        assert status["websiteOutreach"] == "available"
        assert status["suppliersFound"] == 3
        assert status["verifiedContacts"] == 0
        assert status["emailsSent"] == 0
        return {"reply": "Three supplier results; none emailed. Gmail is configured, but automatic outreach is not connected.", "action": "none", "provider": "gemini", "citations": []}
    monkeypatch.setattr("kawteam.main.chat_response", response)
    settings = Settings(workspace="test", gateway_secret="g"*48, session_secret="s"*48, gmail_sender="test@gmail.com", gmail_authorized_user_json="{}", tavily_key="", gemini_key="")
    with TestClient(create_app(settings, repo)) as client:
        client.post("/session", headers=HEADERS, json={"profile": "organiser"})
        result = client.post("/chat", headers=HEADERS, json={"eventId": "tech-night", "taskId": "shirts", "message": "Have you emailed them?"})
        assert result.status_code == 200
        assert "none emailed" in result.json()["assistant"]["body"]
