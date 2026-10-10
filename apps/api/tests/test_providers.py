import pytest


def test_malformed_provider_briefs_and_citations_cannot_trigger_actions():
    from kawteam.providers import validate_answer

    for brief in ["bad brief", {"budgetSen": "1000"}, {"quantity": -1}]:
        with pytest.raises(ValueError):
            validate_answer({"reply": "Researching", "action": "find_vendors", "brief": brief}, [])
    with pytest.raises(ValueError):
        validate_answer({"reply": "Hello", "action": "none", "citations": "invented"}, [])
    result = validate_answer(
        {"reply": "Hello", "action": "none", "citations": ["real", "fake"]},
        [{"documentId": "real"}],
    )
    assert result["citations"] == ["real"]


def test_explicit_unknown_scope_remains_unknown_instead_of_inheriting_another_quantity():
    from kawteam.providers import validate_answer

    result = validate_answer(
        {
            "reply": "How many catering portions?",
            "action": "find_vendors",
            "brief": {"quantity": None, "budgetSen": 100000},
        },
        [],
    )
    assert "quantity" in result["brief"]
    assert result["brief"]["quantity"] is None


def test_chat_sends_actual_execution_status_to_model(monkeypatch):
    import json

    import httpx

    from kawteam.config import Settings
    from kawteam.providers import chat_response
    status = {"email": "configured", "websiteOutreach": "not_connected", "suppliersFound": 5, "verifiedContacts": 0, "emailsSent": 0}
    def handle(request):
        payload = json.loads(request.content)
        schema = payload['generationConfig']['responseJsonSchema']
        assert schema['properties']['action']['enum'] == ['none', 'find_vendors']
        assert schema['additionalProperties'] is False
        prompt = json.loads(payload["contents"][0]["parts"][0]["text"])
        assert prompt["executionStatus"] == status
        assert "executionStatus" in payload["systemInstruction"]["parts"][0]["text"]
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": json.dumps({"reply": "Five suppliers found; no email sent. Gmail is configured, but automatic outreach is not connected.", "action": "none", "citations": []})}]}}]})
    monkeypatch.setattr("kawteam.providers.client", lambda: httpx.Client(transport=httpx.MockTransport(handle)))
    result = chat_response("Did you email them?", {"name": "Tech Night", "executionStatus": status}, [], [], Settings(gemini_key="test"))
    assert "no email sent" in result["reply"]
