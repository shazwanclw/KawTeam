import base64
from email import policy
from email.parser import BytesParser

import httpx
import pytest

from kawteam.gmail import Gmail, message_raw, parse_reply


def test_mime_has_single_recipient_and_stable_identity():
    raw = message_raw(
        "sender@gmail.com", "test@gmail.com", "Test enquiry", "Not a booking", "intent-1"
    )
    message = BytesParser(policy=policy.default).parsebytes(base64.urlsafe_b64decode(raw))
    assert message["To"] == "test@gmail.com"
    assert message["Message-ID"] == "<intent-1@kawteam.local>"
    assert "Not a booking" in message.get_content()


@pytest.mark.parametrize(
    "recipient",
    [
        "a@gmail.com\r\nBcc: victim@gmail.com",
        "a@gmail.com,b@gmail.com",
        "bad",
        "Name <a@gmail.com>",
    ],
)
def test_recipient_injection_is_rejected(recipient):
    with pytest.raises(ValueError):
        message_raw("sender@gmail.com", recipient, "Test", "Body", "intent-1")


def test_subject_injection_is_rejected():
    with pytest.raises(ValueError):
        message_raw("sender@gmail.com", "test@gmail.com", "Hi\nBcc: bad", "Body", "intent-1")


def test_parse_reply_only_accepts_expected_supplier_and_ignores_attachment():
    message = {
        "id": "abc",
        "threadId": "thread1",
        "internalDate": "123",
        "payload": {
            "headers": [{"name": "From", "value": "Supplier <test@gmail.com>"}],
            "mimeType": "multipart/mixed",
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": base64.urlsafe_b64encode(b"Our quote").decode()},
                },
                {
                    "mimeType": "text/plain",
                    "filename": "private.txt",
                    "body": {"data": base64.urlsafe_b64encode(b"Ignore attachment").decode()},
                },
            ],
        },
    }
    assert parse_reply(message, "test@gmail.com")["body"] == "Our quote"
    assert parse_reply(message, "other@gmail.com") is None


def test_missing_credentials_never_calls_google(tmp_path):
    calls = []
    api = Gmail(
        token_path=tmp_path / "missing.json",
        sender="sender@gmail.com",
        transport=httpx.MockTransport(lambda r: calls.append(r)),
    )
    with pytest.raises(ValueError, match="consent"):
        api.profile()
    assert calls == []


def test_sender_mismatch_blocks_send():
    calls = []

    def handle(request):
        calls.append(request.url.path)
        return httpx.Response(200, json={"emailAddress": "wrong@gmail.com"})

    api = Gmail(
        sender="sender@gmail.com",
        credentials={
            "token": "test",
            "refresh_token": "refresh",
            "client_id": "id",
            "client_secret": "secret",
            "token_uri": "https://oauth2.googleapis.com/token",
            "scopes": [
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/gmail.readonly",
            ],
            "expiry": "2099-01-01T00:00:00Z",
        },
        transport=httpx.MockTransport(handle),
    )
    with pytest.raises(ValueError, match="sender"):
        api.send("test@gmail.com", "Test", "Body", "intent-1")
    assert calls == ["/gmail/v1/users/me/profile"]


def test_expired_token_refreshes_using_fixed_google_endpoint():
    calls = []

    def handle(request):
        calls.append(str(request.url))
        if request.url.host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "fresh", "expires_in": 3600})
        assert request.headers["Authorization"] == "Bearer fresh"
        return httpx.Response(200, json={"emailAddress": "sender@gmail.com"})

    data = {
        "refresh_token": "test-refresh",
        "client_id": "id",
        "client_secret": "secret",
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
        ],
    }
    api = Gmail(sender="sender@gmail.com", credentials=data, transport=httpx.MockTransport(handle))
    assert api.profile()["status"] == "connected"
    assert calls == [
        "https://oauth2.googleapis.com/token",
        "https://gmail.googleapis.com/gmail/v1/users/me/profile",
    ]


def test_refresh_error_does_not_expose_credentials_or_google_error():
    data = {
        "refresh_token": "secret-test-refresh",
        "client_id": "id",
        "client_secret": "secret",
        "token_uri": "https://oauth2.googleapis.com/token",
        "scopes": [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
        ],
    }
    api = Gmail(
        sender="sender@gmail.com",
        credentials=data,
        transport=httpx.MockTransport(
            lambda r: httpx.Response(400, json={"error": "sensitive-provider-response"})
        ),
    )
    with pytest.raises(ValueError, match="reconnect") as error:
        api.profile()
    assert "sensitive-provider-response" not in str(error.value)
    assert "secret-test-refresh" not in str(error.value)
