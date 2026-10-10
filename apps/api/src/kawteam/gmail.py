"""Gmail provider. No arbitrary inbox listing, attachment downloads or automatic send retry."""

import base64
import json
import re
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from email.utils import parseaddr
from html import unescape
from pathlib import Path

import httpx

from .providers import client

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]
TOKEN_URI = "https://oauth2.googleapis.com/token"
API = "https://gmail.googleapis.com/gmail/v1/users/me"
DEFAULT_TOKEN_PATH = Path(__file__).parents[2] / ".secrets/gmail-token.json"


def email_address(value):
    if (
        not isinstance(value, str)
        or not re.fullmatch(
            r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", value
        )
        or len(value) > 254
    ):
        raise ValueError("Provide a single verified email address without a display name.")
    return value.lower()


def message_raw(sender, recipient, subject, body, intent_id, reply_to=None):
    sender, recipient = email_address(sender), email_address(recipient)
    if not subject.strip() or len(subject) > 200 or "\r" in subject or "\n" in subject:
        raise ValueError("Email subject must be one line, up to 200 characters.")
    if not body.strip() or len(body) > 10000:
        raise ValueError("Email body must contain between 1 and 10000 characters.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,150}", intent_id):
        raise ValueError("Invalid email intent identifier.")
    message = EmailMessage()
    message["From"], message["To"], message["Subject"] = sender, recipient, subject
    message["Message-ID"] = f"<{intent_id}@kawteam.local>"
    if reply_to:
        if not re.fullmatch(r"<[^<>\s\r\n]{1,250}>", reply_to):
            raise ValueError("Invalid reply message identifier.")
        message["In-Reply-To"] = reply_to
        message["References"] = reply_to
    message.set_content(body)
    return base64.urlsafe_b64encode(message.as_bytes()).decode()


def store_token(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data), encoding="utf-8")
    temporary.replace(path)


def parse_reply(message, expected_sender):
    payload = message.get("payload", {})
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
    if parseaddr(headers.get("from", ""))[1].lower() != email_address(expected_sender):
        return None

    def body(part, mime):
        if part.get("filename"):
            return ""
        if part.get("mimeType") == mime:
            encoded = part.get("body", {}).get("data", "")[:150000]
            try:
                return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).decode(
                    "utf-8", errors="replace"
                )[:20000]
            except (ValueError, TypeError):
                return ""
        return "\n".join(filter(None, (body(p, mime) for p in part.get("parts", [])[:20])))[:20000]

    text = body(payload, "text/plain")
    if not text:
        html = body(payload, "text/html")
        html = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = unescape(re.sub(r"<[^>]+>", " ", html))[:20000]
    if not text.strip():
        return None
    return {
        "providerMessageId": message["id"],
        "providerThreadId": message["threadId"],
        "body": text.strip(),
        "subject": headers.get("subject", "")[:200],
        "rfcMessageId": headers.get("message-id"),
        "rfcInReplyTo": headers.get("in-reply-to"),
        "receivedAtMs": message.get("internalDate"),
        "sender": email_address(expected_sender),
    }


class Gmail:
    def __init__(self, token_path=DEFAULT_TOKEN_PATH, sender="", credentials=None, transport=None):
        self.path = Path(token_path or DEFAULT_TOKEN_PATH)
        self.sender = email_address(sender) if sender else ""
        self.credentials = credentials
        self.transport = transport
        self.persist = credentials is None

    @classmethod
    def from_settings(cls, settings):
        try:
            credentials = (
                json.loads(settings.gmail_authorized_user_json)
                if settings.gmail_authorized_user_json
                else None
            )
        except ValueError as error:
            raise ValueError(
                "Gmail server credentials are invalid; reconnect Google consent."
            ) from error
        return cls(
            settings.gmail_token_path or DEFAULT_TOKEN_PATH, settings.gmail_sender, credentials
        )

    def session(self):
        return httpx.Client(transport=self.transport, timeout=35) if self.transport else client()

    def token(self):
        if self.credentials is None:
            if not self.path.is_file():
                raise ValueError(
                    "Gmail consent is not connected. Run the local Gmail authorisation command."
                )
            try:
                self.credentials = json.loads(self.path.read_text(encoding="utf-8"))
            except (ValueError, OSError) as error:
                raise ValueError(
                    "Gmail credentials could not be read; reconnect Google consent."
                ) from error
        data = self.credentials
        if data.get("token_uri") not in {
            TOKEN_URI,
            "https://accounts.google.com/o/oauth2/token",
        } or not set(SCOPES).issubset(set(data.get("scopes", []))):
            raise ValueError("Gmail credentials require send and read-only consent with Google.")
        try:
            expires = datetime.fromisoformat(data.get("expiry", "1970-01-01T00:00:00Z"))
            expires = expires.replace(tzinfo=UTC) if expires.tzinfo is None else expires
        except ValueError as error:
            raise ValueError("Gmail token expiry is invalid; reconnect consent.") from error
        if not data.get("token") or expires <= datetime.now(UTC) + timedelta(seconds=60):
            if not all(data.get(k) for k in ["refresh_token", "client_id", "client_secret"]):
                raise ValueError("Gmail refresh permission is missing; reconnect consent.")
            with self.session() as session:
                response = session.post(
                    TOKEN_URI,
                    data={
                        "grant_type": "refresh_token",
                        **{k: data[k] for k in ["refresh_token", "client_id", "client_secret"]},
                    },
                )
            if response.status_code != 200:
                raise ValueError("Google rejected Gmail token refresh; reconnect consent.")
            refreshed = response.json()
            if not refreshed.get("access_token"):
                raise ValueError("Google returned no Gmail access token.")
            data.update(
                token=refreshed["access_token"],
                expiry=(
                    datetime.now(UTC) + timedelta(seconds=int(refreshed.get("expires_in", 3600)))
                ).isoformat(),
            )
            if self.persist:
                store_token(self.path, data)
        return data["token"]

    def request(self, method, path, **kwargs):
        with self.session() as session:
            response = session.request(
                method, API + path, headers={"Authorization": f"Bearer {self.token()}"}, **kwargs
            )
        if response.status_code >= 400:
            raise ValueError(
                f"Gmail request failed ({response.status_code}). Check API enablement, account consent and quota."
            )
        return response.json()

    def profile(self):
        data = self.request("GET", "/profile")
        actual = email_address(data["emailAddress"])
        if not self.sender or actual != self.sender:
            raise ValueError("The authorised Gmail account does not match the configured sender.")
        return {"sender": actual, "status": "connected"}

    def send(self, recipient, subject, body, intent_id, thread_id=None, reply_to=None):
        raw = message_raw(self.sender, recipient, subject, body, intent_id, reply_to)
        self.profile()
        payload = {"raw": raw}
        if thread_id:
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,150}", thread_id):
                raise ValueError("Invalid saved Gmail thread identifier.")
            payload["threadId"] = thread_id
        result = self.request("POST", "/messages/send", json=payload)
        if not result.get("id") or not result.get("threadId"):
            raise RuntimeError(
                "Gmail receipt was incomplete; reconcile the saved intent before retrying."
            )
        return {
            "providerMessageId": result["id"],
            "providerThreadId": result["threadId"],
            "rfcMessageId": f"<{intent_id}@kawteam.local>",
        }

    def replies(self, thread_id, supplier):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,150}", thread_id):
            raise ValueError("Invalid saved Gmail thread identifier.")
        self.profile()
        data = self.request("GET", f"/threads/{thread_id}", params={"format": "full"})
        return [
            reply
            for message in data.get("messages", [])[-30:]
            if (reply := parse_reply(message, supplier)) is not None
        ]
