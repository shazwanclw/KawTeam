import copy

from fastapi.testclient import TestClient

from kawteam.config import Settings
from kawteam.workflow import seed


class MemoryRepository:
    def __init__(self):
        self.rows = {("case", c["id"]): dict(c, backendRevision=1) for c in seed()["cases"]}
        self.rows[("event", "tech-night")] = {
            "id": "tech-night",
            "name": "Tech Night",
            "facts": {},
            "backendRevision": 1,
        }
        self.requests = {}

    def snapshot(self):
        return {
            "version": 2,
            **{
                name: [copy.deepcopy(v) for (k, _), v in self.rows.items() if k == kind]
                for name, kind in [
                    ("cases", "case"),
                    ("events", "event"),
                    ("documents", "document"),
                    ("threads", "thread"),
                ]
            },
        }

    def get(self, kind, id):
        return copy.deepcopy(self.rows.get((kind, id)))

    def documents(self, event_id):
        return [
            copy.deepcopy(v)
            for (k, _), v in self.rows.items()
            if k == "document" and v["eventId"] == event_id and v.get("status") != "archived"
        ]

    def upload(self, document, facts, actor):
        from kawteam.repository import payload_hash

        existing = next(
            (
                d
                for d in self.documents(document["eventId"])
                if d["contentDigest"] == document["contentDigest"]
            ),
            None,
        )
        if existing:
            return {k: v for k, v in existing.items() if k not in {"text", "originalBase64"}}
        event = self.get("event", document["eventId"])
        event["facts"] = {**event["facts"], **facts}
        event["memoryVersion"] = event.get("memoryVersion", 0) + 1
        backup = copy.deepcopy((self.rows, self.requests))
        try:
            result = self.save(
                "document",
                document,
                0,
                actor,
                "upload-doc-" + document["id"],
                payload_hash(document),
            )
            self.save(
                "event",
                event,
                event["backendRevision"],
                actor,
                "upload-event-" + document["id"],
                payload_hash(event),
            )
            return {k: v for k, v in result.items() if k not in {"text", "originalBase64"}}
        except Exception:
            self.rows, self.requests = backup
            raise

    def drive_snapshot(
        self, event_id, expected, documents, archive_ids, facts, fact_keys, metadata, actor
    ):
        from uuid import uuid4

        from kawteam.repository import payload_hash

        event = self.get("event", event_id)
        if event["backendRevision"] != expected:
            raise ValueError("Stale revision")
        backup = copy.deepcopy((self.rows, self.requests))
        try:
            for document in documents:
                old = self.get("document", document["id"])
                self.save(
                    "document",
                    document,
                    old["backendRevision"] if old else 0,
                    actor,
                    str(uuid4()),
                    payload_hash(document),
                )
            for document_id in archive_ids:
                document = self.get("document", document_id)
                document["status"] = "archived"
                self.save(
                    "document",
                    document,
                    document["backendRevision"],
                    actor,
                    str(uuid4()),
                    payload_hash(document),
                )
            event.update({"facts": facts, "documentFactKeys": fact_keys, "driveSource": metadata})
            return self.save("event", event, expected, actor, str(uuid4()), payload_hash(event))
        except Exception:
            self.rows, self.requests = backup
            raise

    def append_message(self, event_id, message, actor, case=None, task_id=None):
        from kawteam.projects import thread_id
        from kawteam.repository import payload_hash

        conversation_id = thread_id(event_id, task_id)
        thread = self.get("thread", conversation_id) or {
            "id": conversation_id,
            "taskId": task_id,
            "eventId": event_id,
            "messages": [],
            "backendRevision": 0,
        }
        prior = next(
            (
                m
                for m in thread["messages"]
                if (
                    m["id"] == message["id"]
                    if message["role"] == "user"
                    else m.get("inReplyTo") == message["inReplyTo"]
                )
            ),
            None,
        )
        if prior:
            if message["role"] == "user" and prior["body"] != message["body"]:
                raise ValueError("Idempotency key reused")
            return thread
        backup = copy.deepcopy((self.rows, self.requests))
        try:
            if case:
                self.save("case", case, 0, actor, "chat-case-" + case["id"], payload_hash(case))
            thread["messages"].append(message)
            return self.save(
                "thread",
                thread,
                thread["backendRevision"],
                actor,
                "chat-message-" + message["id"],
                payload_hash(message),
            )
        except Exception:
            self.rows, self.requests = backup
            raise

    def prior(self, key, digest):
        if key not in self.requests:
            return None
        old_digest, result = self.requests[key]
        if old_digest != digest:
            raise ValueError("Idempotency key reused")
        return result

    def save(self, kind, data, expected, actor, key, digest):
        prior = self.prior(key, digest)
        if prior:
            return prior
        old = self.rows.get((kind, data["id"]), {})
        if old.get("backendRevision", 0) != expected:
            raise ValueError("Stale revision")
        result = copy.deepcopy(dict(data, backendRevision=expected + 1))
        self.rows[(kind, data["id"])] = result
        self.requests[key] = (digest, result)
        return copy.deepcopy(result)


def client():
    from kawteam.main import create_app

    settings = Settings(
        session_secret="s" * 48,
        gateway_secret="g" * 48,
        workspace="test",
        gemini_key="",
        tavily_key="",
    )
    return TestClient(create_app(settings, MemoryRepository()))


HEADERS = {"x-kawteam-gateway": "g" * 48}


def test_unsigned_requests_denied_and_observer_cannot_mutate():
    with client() as c:
        assert c.get("/state").status_code == 403
        assert c.get("/state", headers=HEADERS).status_code == 401
        assert c.post("/session", headers=HEADERS, json={"profile": "observer"}).status_code == 200
        result = c.post(
            "/actions",
            headers=HEADERS,
            json={
                "type": "choose",
                "caseId": "case-totes",
                "vendorId": "willow",
                "expectedRevision": 1,
            },
        )
        assert result.status_code == 403


def test_mutation_requires_server_role_and_rejects_stale_revision():
    with client() as c:
        c.post("/session", headers=HEADERS, json={"profile": "teammate"})
        payload = {
            "type": "choose",
            "caseId": "case-totes",
            "vendorId": "willow",
            "expectedRevision": 1,
        }
        assert c.post("/actions", headers=HEADERS, json=payload).status_code == 403
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        assert c.post("/actions", headers=HEADERS, json=payload).status_code == 200
        assert c.post("/actions", headers=HEADERS, json=payload).status_code == 409


def test_duplicate_request_is_idempotent_and_edited_body_cannot_reuse_key():
    with client() as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        payload = {
            "type": "approve",
            "caseId": "case-totes",
            "expectedRevision": 1,
            "requestId": "fixed-request",
        }
        assert c.post("/actions", headers=HEADERS, json=payload).status_code == 200
        assert c.post("/actions", headers=HEADERS, json=payload).status_code == 200
        payload["type"] = "reject"
        assert c.post("/actions", headers=HEADERS, json=payload).status_code == 409


def test_event_upload_and_chat_memory_persist_without_ai_key():
    with client() as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        uploaded = c.post(
            "/events/tech-night/documents",
            headers=HEADERS,
            files={"file": ("budget.txt", b"Budget RM1000. Location: Subang Jaya")},
        )
        assert uploaded.status_code == 200
        reply = c.post(
            "/chat",
            headers=HEADERS,
            json={"eventId": "tech-night", "message": "What is the budget for Tech Night?"},
        )
        assert reply.status_code == 200
        assert reply.json()["assistant"]["provider"] == "setup_required"
        assert reply.json()["assistant"]["citations"]
        state = c.get("/state", headers=HEADERS).json()
        assert state["events"][0]["facts"]["budgetSen"] == 100000
        assert len(state["threads"]) == 1


def test_bad_upload_is_rejected_and_observer_cannot_upload():
    with client() as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        assert (
            c.post(
                "/events/tech-night/documents", headers=HEADERS, files={"file": ("bad.exe", b"bad")}
            ).status_code
            == 422
        )


def test_upload_retry_is_sanitized_and_does_not_double_memory_version():
    with client() as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        for _ in range(2):
            response = c.post(
                "/events/tech-night/documents",
                headers=HEADERS,
                files={"file": ("budget.txt", b"Budget RM1000")},
            )
            assert response.status_code == 200
            assert "originalBase64" not in response.json()
            assert "text" not in response.json()
        state = c.get("/state", headers=HEADERS).json()
        assert state["events"][0]["memoryVersion"] == 1


def test_chat_request_retry_does_not_duplicate_cases_and_changed_message_is_rejected():
    with client() as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        c.post(
            "/events/tech-night/documents",
            headers=HEADERS,
            files={
                "file": (
                    "proposal.txt",
                    b"Budget RM1500\n300 tote bags\nDeadline: 2026-10-25\nLocation: Subang Jaya",
                )
            },
        )
        body = {
            "eventId": "tech-night",
            "requestId": "same-request",
            "message": "Find vendors within RM1000",
        }
        first = c.post("/chat", headers=HEADERS, json=body)
        second = c.post("/chat", headers=HEADERS, json=body)
        assert first.status_code == second.status_code == 200
        assert first.json()["assistant"] == second.json()["assistant"]
        assert len(second.json()["state"]["cases"]) == 3
        body["message"] = "Find vendors within RM900"
        assert c.post("/chat", headers=HEADERS, json=body).status_code == 409
        c.post("/session", headers=HEADERS, json={"profile": "observer"})
        assert (
            c.post(
                "/events/tech-night/documents",
                headers=HEADERS,
                files={"file": ("proposal.txt", b"hello")},
            ).status_code
            == 403
        )
