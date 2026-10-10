from test_api import HEADERS, client


def test_optional_drive_link_is_saved_without_claiming_ingestion():
    with client() as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        event = c.post(
            "/events",
            headers=HEADERS,
            json={
                "name": "Workshop",
                "driveUrl": "https://drive.google.com/drive/folders/abcdefghijk123",
            },
        ).json()
        assert event["driveSource"]["status"] == "awaiting_access"
        assert event["driveSource"]["fileCount"] == 0
        assert event["driveSource"]["lastSyncedAt"] is None
        assert (
            c.post(
                "/events",
                headers=HEADERS,
                json={"name": "Bad", "driveUrl": "https://evil.test/folder"},
            ).status_code
            == 422
        )
        assert (
            c.post("/events/" + event["id"] + "/drive", headers=HEADERS, json={}).json()[
                "driveSource"
            ]["status"]
            == "awaiting_access"
        )
        c.post("/session", headers=HEADERS, json={"profile": "observer"})
        assert (
            c.post("/events/" + event["id"] + "/drive", headers=HEADERS, json={}).status_code == 403
        )


def test_no_project_first_prompt_is_saved_and_retry_reuses_project():
    with client() as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        body = {"message": "Help plan my shirt printing", "requestId": "home-first"}
        first = c.post("/chat", headers=HEADERS, json=body)
        assert first.status_code == 200
        second = c.post("/chat", headers=HEADERS, json=body)
        assert first.json()["eventId"] == second.json()["eventId"]
        assert len(second.json()["state"]["events"]) == 2
        thread = next(
            t for t in second.json()["state"]["threads"] if t["eventId"] == second.json()["eventId"]
        )
        assert len(thread["messages"]) == 2 and thread["messages"][0]["body"] == body["message"]
        assert (
            c.post(
                "/chat", headers=HEADERS, json={**body, "message": "Different prompt"}
            ).status_code
            == 409
        )


def test_no_project_explicit_name_uses_known_project_but_generic_prompt_does_not():
    with client() as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        response = c.post("/chat", headers=HEADERS, json={"message": "What is Tech Night about?"})
        assert response.json()["eventId"] == "tech-night"
        response = c.post("/chat", headers=HEADERS, json={"message": "Hello there"})
        assert response.json()["eventId"] != "tech-night"


def test_drive_adapter_exports_native_documents_and_preserves_partial_results():
    import httpx

    from kawteam.config import Settings
    from kawteam.drive import read_drive

    def handler(request):
        if request.url.path.endswith("/abcdefghijk123"):
            return httpx.Response(
                200,
                json={
                    "id": "abcdefghijk123",
                    "name": "Plans",
                    "mimeType": "application/vnd.google-apps.folder",
                },
            )
        if request.url.path.endswith("/files"):
            return httpx.Response(
                200,
                json={
                    "files": [
                        {
                            "id": "document12345",
                            "name": "Proposal",
                            "mimeType": "application/vnd.google-apps.document",
                        },
                        {"id": "image1234567", "name": "Photo.jpg", "mimeType": "image/jpeg"},
                    ]
                },
            )
        if request.url.path.endswith("/export"):
            return httpx.Response(200, content=b"Budget RM2000\n50 shirts")
        raise AssertionError(str(request.url))

    with httpx.Client(transport=httpx.MockTransport(handler)) as session:
        result = read_drive(
            "https://drive.google.com/drive/folders/abcdefghijk123",
            Settings(drive_api_key="key"),
            session,
        )
        assert result["status"] == "partial"
        assert result["documents"][0]["text"] == "Budget RM2000\n50 shirts"
        assert len(result["errors"]) == 1


def test_drive_failed_refresh_preserves_saved_project_memory(monkeypatch):
    import httpx

    from kawteam.config import Settings
    from kawteam.drive import read_drive

    def denied(request):
        return httpx.Response(403, json={"error": "denied"})

    with httpx.Client(transport=httpx.MockTransport(denied)) as session:
        result = read_drive(
            "https://drive.google.com/drive/folders/abcdefghijk123",
            Settings(drive_api_key="key"),
            session,
        )
        assert result["status"] == "awaiting_access" and not result["documents"]
    with client() as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        c.post(
            "/events/tech-night/documents",
            headers=HEADERS,
            files={"file": ("budget.txt", b"Budget RM1000")},
        )
        monkeypatch.setattr("kawteam.main.read_drive", lambda *args: result)
        c.post(
            "/events/tech-night/drive",
            headers=HEADERS,
            json={"url": "https://drive.google.com/drive/folders/abcdefghijk123"},
        )
        state = c.get("/state", headers=HEADERS).json()
        assert len(state["documents"]) == 1
        assert state["events"][0]["facts"]["budgetSen"] == 100000
        assert state["events"][0]["driveSource"]["lastSyncedAt"] is None


def test_drive_link_rejects_host_confusion_credentials_and_arbitrary_ports():
    import pytest

    from kawteam.drive import parse_drive_url

    for url in [
        "https://drive.google.com.evil.test/drive/folders/abcdefghijk123",
        "https://user@drive.google.com/drive/folders/abcdefghijk123",
        "http://drive.google.com/drive/folders/abcdefghijk123",
        "https://drive.google.com:444/drive/folders/abcdefghijk123",
        "https://drive.google.com/open?id=bad",
    ]:
        with pytest.raises(ValueError):
            parse_drive_url(url)


def test_drive_sync_persists_extracted_facts_and_sanitized_metadata(monkeypatch):
    monkeypatch.setattr(
        "kawteam.main.read_drive",
        lambda *args: {
            "status": "ready",
            "documents": [
                {
                    "driveFileId": "document12345",
                    "name": "Proposal.txt",
                    "text": "Budget RM2000\n50 shirts",
                    "content": b"Budget RM2000\n50 shirts",
                }
            ],
            "errors": [],
            "message": "Read 1 document.",
        },
    )
    with client() as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        response = c.post(
            "/events",
            headers=HEADERS,
            json={
                "name": "New project",
                "driveUrl": "https://docs.google.com/document/d/document12345/edit",
            },
        )
        assert response.status_code == 200
        assert response.json()["driveSource"]["status"] == "ready"
        assert response.json()["driveSource"]["lastSyncedAt"]
        assert response.json()["facts"] == {"budgetSen": 200000, "quantity": 50}


def test_modified_drive_document_and_reverted_content_replace_current_memory(monkeypatch):
    text = ["Budget RM1000", "Budget RM2000", "Budget RM1000"]

    def read(*args):
        value = text.pop(0)
        return {
            "status": "ready",
            "documents": [
                {
                    "driveFileId": "document12345",
                    "name": "Budget.txt",
                    "text": value,
                    "content": value.encode(),
                }
            ],
            "errors": [],
            "message": "Read one document.",
        }

    monkeypatch.setattr("kawteam.main.read_drive", read)
    with client() as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        for expected in [100000, 200000, 100000]:
            response = c.post(
                "/events/tech-night/drive",
                headers=HEADERS,
                json={"url": "https://drive.google.com/drive/folders/abcdefghijk123"},
            )
            assert response.status_code == 200
            assert response.json()["facts"]["budgetSen"] == expected
            state = c.get("/state", headers=HEADERS).json()
            active = [d for d in state["documents"] if d.get("status") != "archived"]
            assert len(active) == 1


def test_changed_drive_source_failure_does_not_relabel_old_sync_as_new_success(monkeypatch):
    monkeypatch.setattr(
        "kawteam.main.read_drive",
        lambda *args: {
            "status": "ready",
            "documents": [
                {
                    "driveFileId": "document12345",
                    "name": "Budget.txt",
                    "text": "Budget RM1000",
                    "content": b"Budget RM1000",
                }
            ],
            "errors": [],
            "message": "Read one.",
        },
    )
    with client() as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        original = "https://drive.google.com/drive/folders/abcdefghijk123"
        c.post("/events/tech-night/drive", headers=HEADERS, json={"url": original})
        monkeypatch.setattr(
            "kawteam.main.read_drive",
            lambda *args: {
                "status": "awaiting_access",
                "documents": [],
                "errors": [],
                "message": "No access.",
            },
        )
        result = c.post(
            "/events/tech-night/drive",
            headers=HEADERS,
            json={"url": "https://drive.google.com/drive/folders/newfolder12345"},
        ).json()
        assert result["driveSource"]["fileCount"] == 0
        assert result["driveSource"]["lastSyncedAt"] is None
        assert result["driveSource"]["memorySource"]["url"] == original
        assert result["facts"]["budgetSen"] == 100000


def test_removed_drive_fact_is_not_carried_into_current_memory(monkeypatch):
    texts = ["Budget RM1000\n50 shirts", "50 shirts"]

    def read(*args):
        text = texts.pop(0)
        return {
            "status": "ready",
            "documents": [
                {
                    "driveFileId": "document12345",
                    "name": "Plan.txt",
                    "text": text,
                    "content": text.encode(),
                }
            ],
            "errors": [],
            "message": "Read one.",
        }

    monkeypatch.setattr("kawteam.main.read_drive", read)
    with client() as c:
        c.post("/session", headers=HEADERS, json={"profile": "organiser"})
        for _ in range(2):
            result = c.post(
                "/events/tech-night/drive",
                headers=HEADERS,
                json={"url": "https://drive.google.com/drive/folders/abcdefghijk123"},
            )
        assert result.json()["facts"] == {"quantity": 50}


def test_drive_elapsed_limit_is_checked_while_streaming(monkeypatch):
    import httpx

    from kawteam.config import Settings
    from kawteam.drive import read_drive

    clock = [0]
    monkeypatch.setattr("kawteam.drive.time.monotonic", lambda: clock[0])

    class SlowStream(httpx.SyncByteStream):
        def __iter__(self):
            clock[0] = 46
            yield b'{"id":"abcdefghijk123","name":"File","mimeType":"text/plain"}'

    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=SlowStream()))
    ) as session:
        result = read_drive(
            "https://drive.google.com/file/d/abcdefghijk123/view",
            Settings(drive_api_key="key"),
            session,
        )
        assert result["status"] == "error"
        assert "elapsed-time limit" in result["message"]
