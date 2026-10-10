import base64
import copy
import hmac
import re
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import NAMESPACE_URL, uuid4, uuid5
from zoneinfo import ZoneInfo

import httpx
from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .auth import issue_session, verify_session
from .config import Settings
from .drive import parse_drive_url, read_drive
from .gmail import DEFAULT_TOKEN_PATH, Gmail
from .liaison import Liaison
from .memory import extract_text, facts_from_text, intake, resolve_event, retrieve
from .projects import DEFAULT_SETTINGS, fresh_vendor, named_vendors, route, thread_id, workflow_plan
from .providers import chat_response, discover
from .quote_reply import extract_quote
from .repository import SupabaseRepository, payload_hash
from .schemas.domain import NewBrief
from .tasks import invalidate_terms, project_name, selection_target, task_name, task_queue
from .workflow import fit, log, outcome, transition


class ProfileBody(BaseModel):
    profile: Literal["organiser", "teammate", "observer"]


class ActionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal[
        "create",
        "research",
        "choose",
        "edit-draft",
        "approve",
        "reject",
        "prepare",
        "send",
        "sync",
        "liaise-task",
        "approve-vendor",
        "reject-vendor",
        "confirm-vendor",
    ]
    caseId: str | None = Field(default=None, max_length=150)
    id: str | None = Field(default=None, max_length=150)
    vendorId: str | None = Field(default=None, max_length=150)
    body: str | None = Field(default=None, max_length=10000)
    brief: NewBrief | None = None
    expectedRevision: int = Field(default=0, ge=0)
    requestId: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=150)


class EventBody(BaseModel):
    driveUrl: str | None = Field(default=None, max_length=1000)
    name: str = Field(min_length=1, max_length=100)


class EmailContactBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendorId: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=254)
    expectedRevision: int = Field(ge=1)


class EmailSendBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendorId: str = Field(min_length=1, max_length=150)
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=9000)
    expectedRevision: int = Field(ge=1)
    requestId: str = Field(min_length=1, max_length=150, pattern=r"^[A-Za-z0-9_-]+$")


class EmailSyncBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expectedRevision: int = Field(ge=1)


class EmailQuoteBody(EmailSyncBody):
    vendorId: str = Field(min_length=1, max_length=150)
    providerMessageId: str = Field(min_length=1, max_length=150)


class DriveBody(BaseModel):
    url: str | None = Field(default=None, max_length=1000)


class AssistantSettingsBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["general", "research", "liaise"] = "general"
    instructions: str = Field(default="", max_length=2000)
    shortlistSize: int = Field(default=3, ge=1, le=3, strict=True)
    preferredVendorId: str | None = Field(default=None, max_length=150)


class ChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    eventId: str | None = Field(default=None, max_length=150)
    taskId: str | None = Field(default=None, max_length=150)
    requestId: str = Field(default_factory=lambda: str(uuid4()), max_length=150)


def create_case(brief, id, event_id=None):
    b = NewBrief.model_validate(brief)
    if b.deadline <= datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date():
        raise ValueError("Delivery date must be in the future.")
    return {
        **b.model_dump(mode="json", by_alias=True),
        "id": id,
        "eventId": event_id,
        "stage": "brief",
        "selectedVendorId": None,
        "vendors": [],
        "events": [],
        "messages": [],
        "draft": {
            "recipient": "No vendor yet",
            "subject": f"Quotation enquiry: {b.title}",
            "body": "",
            "revision": 1,
            "status": "pending",
        },
    }


def create_app(settings=None, repository=None):
    settings = settings or Settings()
    repository = repository or SupabaseRepository(settings)
    app = FastAPI(title="KawTeam API", version="0.3.0")

    def email_service():
        return Liaison(repository, Gmail.from_settings(settings))

    @app.exception_handler(PermissionError)
    async def denied(request, error):
        return JSONResponse(status_code=403, content={"detail": str(error)})

    @app.exception_handler(ValueError)
    async def invalid(request, error):
        message = str(error)
        return JSONResponse(
            status_code=409 if "Stale" in message or "Idempotency" in message else 422,
            content={"detail": message[:800]},
        )

    @app.exception_handler(RuntimeError)
    async def unavailable(request, error):
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Backend connection unavailable. Your saved data has not been replaced with fixtures."
            },
        )

    def gateway(request: Request):
        if not hmac.compare_digest(
            request.headers.get("x-kawteam-gateway", ""), settings.gateway_secret
        ):
            raise HTTPException(403, "Use the KawTeam frontend gateway.")

    def actor(request: Request, _=Depends(gateway)):
        token = request.cookies.get("kawteam_session")
        if not token:
            raise HTTPException(401, "Choose a demo profile to begin.")
        try:
            return verify_session(token, settings.workspace, settings.session_secret)
        except ValueError as error:
            raise HTTPException(401, "Session expired. Choose a profile again.") from error

    def editable(role):
        if role == "observer":
            raise PermissionError("This profile is view-only.")

    def record(kind, id):
        found = repository.get(kind, id)
        if not found:
            raise HTTPException(404, "Record not found in this workspace.")
        return found

    def save(kind, data, expected, role, key=None, source=None):
        return repository.save(
            kind, data, expected, role, key or str(uuid4()), payload_hash(source or data)
        )

    @app.get("/health")
    def health():
        return {"product": "KawTeam", "status": "ok", "workbuddy": "desktop_tools_available", "workbuddyTrigger": "not_connected"}

    @app.post("/session", dependencies=[Depends(gateway)])
    def session(body: ProfileBody, response: Response):
        response.set_cookie(
            "kawteam_session",
            issue_session(body.profile, settings.workspace, settings.session_secret),
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
            max_age=86400,
            path="/",
        )
        return {"profile": body.profile, "mode": "public-hackathon-demo"}

    @app.get("/state")
    def state(role=Depends(actor)):
        snapshot = repository.snapshot()
        for case in snapshot["cases"]:
            for vendor in case["vendors"]:
                vendor["serverFit"] = fit(case, vendor)
            case["approvalQueue"] = task_queue(case)
        return {**snapshot, "profile": role, "storage": "supabase"}

    @app.get("/connections")
    def connections(role=Depends(actor)):
        return {
            "database": "connected",
            "ai": "configured" if settings.gemini_key else "setup_required",
            "search": "configured" if settings.tavily_key else "setup_required",
            "email": "configured" if settings.gmail_authorized_user_json or Path(settings.gmail_token_path or DEFAULT_TOKEN_PATH).is_file() else "setup_required",
            "workbuddy": "desktop_tools_available",
            "workbuddyTrigger": "not_connected",
            "model": settings.gemini_model,
        }

    @app.get("/email/status")
    def email_status(role=Depends(actor)):
        return Gmail.from_settings(settings).profile()

    @app.post("/cases/{case_id}/email/contact")
    def email_contact(case_id: str, body: EmailContactBody, role=Depends(actor)):
        return email_service().contact(case_id, body.vendorId, body.email, body.expectedRevision, role)

    @app.post("/cases/{case_id}/email/send")
    def email_send(case_id: str, body: EmailSendBody, role=Depends(actor)):
        return email_service().send(case_id, body.vendorId, body.subject, body.body, body.expectedRevision, body.requestId, role)

    @app.post("/cases/{case_id}/email/sync")
    def email_sync(case_id: str, body: EmailSyncBody, role=Depends(actor)):
        return email_service().sync(case_id, body.expectedRevision, role)

    @app.post("/cases/{case_id}/email/quote")
    def email_quote(case_id: str, body: EmailQuoteBody, role=Depends(actor)):
        return email_service().quote(case_id, body.vendorId, body.providerMessageId, body.expectedRevision, role, lambda c, m: extract_quote(c, m, settings))

    @app.post("/actions")
    def action(body: ActionBody, role=Depends(actor)):
        editable(role)
        data = body.model_dump(mode="json", by_alias=True, exclude_none=True)
        fingerprint = payload_hash(data)
        previous = repository.prior(body.requestId, fingerprint)
        if previous:
            return state(role)
        if body.type == "create":
            if not body.brief or not body.id:
                raise ValueError("A brief and case ID are required.")
            c = create_case(body.brief.model_dump(mode="json", by_alias=True), body.id)
        else:
            c = record("case", body.caseId)
            if c["backendRevision"] != body.expectedRevision:
                raise ValueError("Stale revision. Refresh and retry.")
            if body.type == "research" and c["id"] != "case-totes":
                fresh_candidates = discover(c, settings.tavily_key)
                protected_ids = {c.get("selectedVendorId"), c["draft"].get("vendorId")}
                # Preserve exact approved recipient identity even for legacy drafts
                # without a structured vendor ID; never detach a human decision.
                retain_all = c["draft"].get("status") == "approved" and not c["draft"].get(
                    "vendorId"
                )
                retained = [v for v in c["vendors"] if retain_all or v["id"] in protected_ids]
                retained_ids = {v["id"] for v in retained}
                c["vendors"] = [
                    v for v in fresh_candidates if v["id"] not in retained_ids
                ] + retained
                c["shortlistVendorIds"] = [v["id"] for v in fresh_candidates]
                c["outreachVendorIds"] = list(c["shortlistVendorIds"])
                c["workflowMode"] = "research"
                c["workflowPlan"] = workflow_plan("research", True, c["shortlistVendorIds"])
                if c.get("selectedVendorId"):
                    c["workflowPlan"][-1].update(
                        {
                            "status": "complete",
                            "detail": "Your previous explicit supplier decision is retained. New research does not change it.",
                        }
                    )
                c["stage"] = "decided" if c.get("selectedVendorId") else "research"
                log(
                    c,
                    "Public vendor sources collected",
                    f"{len(fresh_candidates)} new public candidates; custom quotations still required. Existing decision and draft identity retained.",
                    "research",
                )
            else:
                c = transition(c, role, data)
        save("case", c, body.expectedRevision, role, body.requestId, data)
        return state(role)

    @app.get("/cases/{case_id}/report")
    def report(case_id: str, role=Depends(actor)):
        return outcome(record("case", case_id))

    @app.post("/events")
    def new_event(body: EventBody, role=Depends(actor)):
        editable(role)
        name = body.name.strip()
        if not name:
            raise ValueError("Event name cannot be blank.")
        if len(repository.snapshot()["events"]) >= 20:
            raise ValueError("This hackathon workspace supports up to 20 events.")
        event = {
            "id": str(uuid4()),
            "name": name,
            "facts": {},
            "createdAt": datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).isoformat(),
            "sample": False,
            "tasks": [],
            "assistantSettings": dict(DEFAULT_SETTINGS),
        }
        if body.driveUrl:
            parse_drive_url(body.driveUrl)
            event["driveSource"] = {
                "url": body.driveUrl,
                "status": "awaiting_access",
                "fileCount": 0,
                "lastSyncedAt": None,
                "message": "Drive link saved; awaiting authorised sync.",
            }
        event = save("event", event, 0, role)
        return sync_drive(event["id"], DriveBody(), role) if body.driveUrl else event

    @app.post("/events/{event_id}/tasks")
    def new_task(event_id: str, body: EventBody, role=Depends(actor)):
        editable(role)
        event = record("event", event_id)
        name = body.name.strip()
        if not name:
            raise ValueError("Task name cannot be blank.")
        tasks = event.get("tasks", [])
        if len(tasks) >= 30:
            raise ValueError("Maximum 30 tasks per project.")
        event["tasks"] = [
            *tasks,
            {
                "id": str(uuid4()),
                "name": name,
                "createdAt": datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).isoformat(),
            },
        ]
        return save("event", event, event["backendRevision"], role)

    @app.post("/events/{event_id}/settings")
    def assistant_settings(event_id: str, body: AssistantSettingsBody, role=Depends(actor)):
        editable(role)
        event = record("event", event_id)
        if body.preferredVendorId and not any(
            v["id"] == body.preferredVendorId
            for c in repository.snapshot()["cases"]
            for v in c.get("vendors", [])
        ):
            raise ValueError("Preferred supplier must be in the saved vendor library.")
        event["assistantSettings"] = body.model_dump()
        return save("event", event, event["backendRevision"], role)

    @app.post("/events/{event_id}/drive")
    def sync_drive(event_id: str, body: DriveBody, role=Depends(actor)):
        editable(role)
        event = record("event", event_id)
        url = body.url or event.get("driveSource", {}).get("url")
        if not url:
            raise ValueError("Add a Google Drive folder or document link first.")
        parse_drive_url(url)
        result = read_drive(url, settings)
        previous = event.get("driveSource", {})
        source_changed = previous.get("url") != url
        succeeded = bool(result["documents"]) or result["status"] == "ready"
        documents = []
        for item in result["documents"]:
            content = item["content"]
            documents.append(
                {
                    "id": str(uuid5(NAMESPACE_URL, f"drive:{event_id}:{item['driveFileId']}")),
                    "eventId": event_id,
                    "name": item["name"],
                    "text": item["text"],
                    "originalBase64": base64.b64encode(content).decode(),
                    "size": len(content),
                    "contentDigest": payload_hash(
                        {"event": event_id, "file": base64.b64encode(content).decode()}
                    ),
                    "status": "ready",
                    "characters": len(item["text"]),
                    "createdAt": datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).isoformat(),
                    "driveFileId": item["driveFileId"],
                    "sourceUrl": url,
                }
            )
        metadata = {
            "url": url,
            "status": result["status"],
            "fileCount": len(documents)
            if succeeded
            else 0
            if source_changed
            else previous.get("fileCount", 0),
            "lastSyncedAt": datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).isoformat()
            if succeeded
            else None
            if source_changed
            else previous.get("lastSyncedAt"),
            "message": result["message"],
            "errors": result.get("errors", [])[:20],
        }
        if (
            source_changed
            and not succeeded
            and (previous.get("lastSyncedAt") or previous.get("memorySource"))
        ):
            metadata["memorySource"] = previous.get("memorySource") or {
                "url": previous["url"],
                "fileCount": previous.get("fileCount", 0),
                "lastSyncedAt": previous.get("lastSyncedAt"),
            }
        if not succeeded:
            event["driveSource"] = metadata
            return save("event", event, event["backendRevision"], role)
        old_documents = repository.documents(event_id)
        ids = {d["id"] for d in documents}
        archive_ids = [
            d["id"]
            for d in old_documents
            if d.get("driveFileId")
            and (
                d.get("sourceUrl") != url
                or result["status"] == "ready"
                or d.get("driveFileId") in {n["driveFileId"] for n in documents}
            )
            and d["id"] not in ids
        ]
        active_documents = [
            d for d in old_documents if d["id"] not in ids and d["id"] not in archive_ids
        ] + documents
        if len(active_documents) > 20:
            raise ValueError("Maximum 20 current project documents. Use a smaller Drive folder.")
        current_facts = {}
        for document in active_documents:
            current_facts.update(facts_from_text(document["text"]))
        # Replace previously derived keys; unrelated project facts are retained.
        managed_keys = set(event.get("documentFactKeys", []))
        for document in old_documents:
            managed_keys.update(facts_from_text(document["text"]))
        facts = {k: v for k, v in event.get("facts", {}).items() if k not in managed_keys}
        facts.update(current_facts)
        metadata["fileCount"] = sum(bool(d.get("driveFileId")) for d in active_documents)
        return repository.drive_snapshot(
            event_id,
            event["backendRevision"],
            documents,
            archive_ids,
            facts,
            list(current_facts),
            metadata,
            role,
        )

    @app.post("/events/{event_id}/documents")
    def upload(event_id: str, file: UploadFile = File(...), role=Depends(actor)):
        editable(role)
        record("event", event_id)
        content = file.file.read(3 * 1024 * 1024 + 1)
        name = (file.filename or "document.txt").replace("\\", "/").split("/")[-1][:150]
        try:
            text = extract_text(name, content)
        except Exception as error:
            raise ValueError(
                str(error)
                if isinstance(error, ValueError)
                else "Could not read this document. Upload a supported text-based file."
            ) from error
        source_digest = payload_hash(
            {"event": event_id, "file": base64.b64encode(content).decode()}
        )
        document = {
            "id": str(uuid4()),
            "eventId": event_id,
            "name": name,
            "text": text,
            "originalBase64": base64.b64encode(content).decode(),
            "size": len(content),
            "contentDigest": source_digest,
            "status": "ready",
            "characters": len(text),
            "createdAt": datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).isoformat(),
        }
        return repository.upload(document, facts_from_text(text), role)

    @app.get("/documents/{document_id}")
    def document(document_id: str, role=Depends(actor)):
        d = record("document", document_id)
        return {k: v for k, v in d.items() if k != "originalBase64"}

    @app.post("/chat")
    def chat(body: ChatBody, role=Depends(actor)):
        editable(role)
        snapshot = repository.snapshot()
        event = resolve_event(body.message, snapshot["events"], body.eventId)
        if not event:
            if body.eventId or body.taskId:
                raise ValueError(
                    "Selected project or task is unavailable. Choose an existing project."
                )
            project_id = str(
                uuid5(NAMESPACE_URL, f"kawteam-home:{settings.workspace}:{body.requestId}")
            )
            event = repository.get("event", project_id)
            if not event:
                if len(snapshot["events"]) >= 20:
                    raise ValueError("Maximum 20 projects in this hackathon workspace.")
                event = {
                    "id": project_id,
                    "name": project_name(body.message),
                    "facts": {},
                    "tasks": [],
                    "assistantSettings": dict(DEFAULT_SETTINGS),
                    "createdAt": datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).isoformat(),
                    "sample": False,
                    "initialRequestId": body.requestId,
                    "initialPrompt": body.message,
                }
                event = save(
                    "event",
                    event,
                    0,
                    role,
                    "home-project-" + project_id,
                    {"message": body.message, "requestId": body.requestId},
                )
            elif event.get("initialPrompt") != body.message:
                raise ValueError("Idempotency key reused for a different message.")
        task_id = body.taskId or str(
            uuid5(
                NAMESPACE_URL, f"kawteam-task:{settings.workspace}:{event['id']}:{body.requestId}"
            )
        )
        task = next((t for t in event.get("tasks", []) if t["id"] == task_id), None)
        legacy_case = next(
            (
                c
                for c in snapshot["cases"]
                if c["id"] == task_id and c.get("eventId") == event["id"]
            ),
            None,
        )
        legacy_thread = (
            repository.get("thread", thread_id(event["id"]))
            if task_id == "legacy-" + event["id"]
            else None
        )
        if body.taskId and not task and not legacy_case and not legacy_thread:
            raise ValueError("Task does not belong to the selected project.")
        user_message = {
            "id": body.requestId,
            "role": "user",
            "body": body.message,
            "time": datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).isoformat(),
        }
        if not task:
            task = {
                "id": task_id,
                "name": legacy_case["title"] if legacy_case else task_name(body.message),
                "createdAt": user_message["time"],
                "initialRequestId": body.requestId,
            }
            if legacy_thread:
                task.update(name="Earlier project conversation", sourceThreadId=legacy_thread["id"])
            event = repository.start_task(event["id"], task, user_message, role)
        conversation_id = thread_id(event["id"], task_id)
        thread = repository.get("thread", conversation_id) or {
            "id": conversation_id,
            "taskId": task_id,
            "eventId": event["id"],
            "messages": [],
            "backendRevision": 0,
        }
        previous_user = next((m for m in thread["messages"] if m["id"] == body.requestId), None)
        if previous_user and previous_user["body"] != body.message:
            raise ValueError("Idempotency key reused for a different message.")
        existing = next(
            (m for m in thread["messages"] if m.get("inReplyTo") == body.requestId), None
        )
        if existing:
            return {
                "assistant": existing,
                "eventId": event["id"],
                "taskId": task_id,
                "state": state(role),
            }
        if len(thread["messages"]) >= 150:
            raise ValueError("Conversation limit reached for this hackathon workspace.")
        documents = repository.documents(event["id"])
        context = retrieve(event["id"], body.message, documents)
        if not any(m["id"] == body.requestId for m in thread["messages"]):
            thread = repository.append_message(
                event["id"],
                {
                    "id": body.requestId,
                    "role": "user",
                    "body": body.message,
                    "time": datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).isoformat(),
                },
                role,
                task_id=task_id,
            )
        try:
            provider_event = {
                **event,
                "activeTask": task,
                "activeRequests": [
                    c
                    for c in snapshot["cases"]
                    if c.get("eventId") == event["id"]
                    and (c.get("taskId") == task_id or c["id"] == task_id)
                ],
            }
            answer = chat_response(
                body.message, provider_event, context, thread["messages"], settings
            )
        except (
            ValueError,
            KeyError,
            IndexError,
            TypeError,
            RuntimeError,
            httpx.HTTPError,
        ) as error:
            answer = {
                "reply": str(error)
                if isinstance(error, ValueError)
                else "AI connection failed. Your message and event memory are saved.",
                "action": "none",
                "citations": [],
                "provider": "error",
            }
        assistant = {
            "id": str(uuid4()),
            "role": "assistant",
            "body": answer["reply"],
            "citations": answer.get("citations", []),
            "provider": answer["provider"],
            "inReplyTo": body.requestId,
            "time": datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).isoformat(),
        }
        last_answer = next(
            (m for m in reversed(thread["messages"]) if m["role"] == "assistant"), {}
        )
        pending = last_answer.get("pendingRequest")
        request_message = (pending.get("message", "") + "\n" if pending else "") + body.message
        scoped_cases = [
            c
            for c in snapshot["cases"]
            if c.get("eventId") == event["id"]
            and (c.get("taskId") == task_id or c["id"] == task_id)
        ]
        current_case = next(
            (c for c in reversed(scoped_cases) if c["id"] == last_answer.get("caseId")),
            scoped_cases[-1] if scoped_cases else None,
        )
        mode, known_vendor = route(request_message, event, snapshot["cases"], thread)
        overrides = facts_from_text(body.message)
        # "Make it 40" is a quantity update only within a known task.
        if current_case and "quantity" not in overrides:
            changed_quantity = re.search(
                r"\b(?:make it|only (?:want|need)|change (?:it|quantity) to)\s+(\d+)\b",
                body.message,
                re.IGNORECASE,
            )
            if changed_quantity:
                overrides["quantity"] = int(changed_quantity.group(1))
        target = selection_target(
            request_message, current_case.get("selectionTarget", 1) if current_case else 1
        )
        spec_edit = bool(
            re.search(
                r"\b(?:change|update|switch|instead|make|different)\b", body.message, re.IGNORECASE
            )
            and re.search(
                r"\b(?:colou?r|material|design|printing|size|specifications?)\b",
                body.message,
                re.IGNORECASE,
            )
        )
        model_edit = (
            answer.get("action") == "find_vendors"
            and any(
                value is not None and value != current_case.get(key)
                for key, value in (answer.get("brief") or {}).items()
            )
            if current_case
            else False
        )
        updated_requirements = bool(
            current_case
            and (
                any(value != current_case.get(key) for key, value in overrides.items())
                or target != current_case.get("selectionTarget", 1)
                or spec_edit
                or model_edit
            )
        )
        requested = updated_requirements or (
            bool(pending)
            or answer.get("action") == "find_vendors"
            or (
                answer["provider"] == "setup_required"
                and any(
                    word in body.message.lower()
                    for word in [
                        "vendor",
                        "supplier",
                        "catering",
                        "partner",
                        "shirts",
                        "shirt printing",
                    ]
                )
            )
        )
        if (
            answer["provider"] == "setup_required"
            and (known_vendor or named_vendors(body.message, snapshot["cases"]))
            and any(
                word in body.message.lower()
                for word in ["contact", "negotiate", "quote", "buy", "order", "print"]
            )
        ):
            requested = True
        if current_case and not updated_requirements and not pending:
            requested = False
            if answer["provider"] == "setup_required" and re.search(
                r"\b(?:what|current|budget|summary|status|summarise|summarize)\b",
                body.message,
                re.IGNORECASE,
            ):
                assistant["provider"] = "saved_context"
                assistant["body"] = (
                    f"Saved task details: {current_case['quantity']} items; budget RM{current_case['budgetSen'] / 100:,.2f}; deadline {current_case['deadline']}; location {current_case['location']}. Live supplier liaison is not connected."
                )
        resulting_case = None
        if requested:
            brief = {
                **intake(request_message, event),
                **(
                    {
                        k: current_case[k]
                        for k in [
                            "title",
                            "goal",
                            "quantity",
                            "budgetSen",
                            "targetSen",
                            "deadline",
                            "location",
                        ]
                    }
                    if current_case
                    else {}
                ),
                **(pending.get("brief", {}) if pending else {}),
                **(answer.get("brief") or {}),
            }
            # Explicit new user values take priority over model output and document memory.
            brief.update(facts_from_text(request_message))
            brief.update(overrides)
            if (
                not current_case
                and selection_target(request_message) > 1
                and not brief.get("quantity")
            ):
                brief["quantity"] = 1
            brief["title"] = task["name"]
            if current_case and updated_requirements:
                brief["goal"] = (current_case["goal"] + "\nUpdated requirement: " + body.message)[
                    -2000:
                ]
            if current_case and target != current_case.get("selectionTarget", 1) and not overrides:
                brief["goal"] = current_case["goal"]
            if brief.get("budgetSen"):
                brief["targetSen"] = min(
                    brief.get("targetSen") or brief["budgetSen"], brief["budgetSen"]
                )
            missing = [
                k for k in ["quantity", "budgetSen", "deadline", "location"] if not brief.get(k)
            ]
            if mode == "liaise" and not known_vendor and not current_case:
                assistant["body"] += (
                    "\n\nWhich vendor should I contact? Name a supplier from this project or use Connections to start a fresh enquiry."
                )
                assistant["pendingRequest"] = {"message": request_message, "brief": brief}
            elif missing:
                assistant["pendingRequest"] = {"message": request_message, "brief": brief}
                assistant["missingFacts"] = missing
                assistant["body"] += (
                    "\n\nI still need: "
                    + ", ".join(missing)
                    + ". Tell me in chat or link authorised Google Drive context."
                )
            else:
                try:
                    c = create_case(
                        {
                            k: brief[k]
                            for k in [
                                "title",
                                "goal",
                                "quantity",
                                "budgetSen",
                                "targetSen",
                                "deadline",
                                "location",
                            ]
                        },
                        str(
                            uuid5(
                                NAMESPACE_URL,
                                f"kawteam:{event['id']}:{task_id}:{body.requestId}",
                            )
                        ),
                        event["id"],
                    )
                    if current_case:
                        updated_brief = {
                            k: c[k]
                            for k in [
                                "title",
                                "goal",
                                "quantity",
                                "budgetSen",
                                "targetSen",
                                "deadline",
                                "location",
                            ]
                        }
                        # Preserve historical messages/decisions but invalidate prior scope and quote commitments.
                        c = copy.deepcopy(current_case)
                        invalidate_terms(c)
                        c.update(updated_brief)
                        log(
                            c,
                            "Task requirements updated",
                            "Fresh supplier terms and new approval are required. Previous decisions are retained as superseded history.",
                            "human",
                        )
                        c["events"][-1]["milestone"] = True
                    c.update(taskWorkflowVersion=1, selectionTarget=target)
                    c.setdefault("vendorDecisions", [])
                    c["sourceDocumentIds"] = [d["id"] for d in documents]
                    c["taskId"] = task_id
                    c["workflowMode"] = mode
                    if mode == "liaise" and known_vendor and not current_case:
                        c["vendors"] = [fresh_vendor(known_vendor)]
                        c["stage"] = "negotiation"
                        c["draft"].update(
                            {
                                "vendorId": known_vendor["id"],
                                "recipient": known_vendor["name"]
                                + " (contact verification required)",
                                "body": f"Hello {known_vendor['name']}, please provide a fresh, non-binding quotation for {c['quantity']} units: {c['goal']}. Budget ceiling RM{c['budgetSen'] / 100:.2f}; delivery to {c['location']} by {c['deadline']}. Confirm specifications, delivery charges and validity. This enquiry is not an order or agreement.",
                            }
                        )
                        log(
                            c,
                            "Existing supplier reused",
                            "Research skipped. Prior quotation and approval cleared; fresh terms required.",
                            "negotiation",
                        )
                    elif current_case:
                        # Already-discovered identities are retained; edits need fresh quotes, not stale confirmations.
                        pass
                    elif settings.tavily_key:
                        c["vendors"] = discover(c, settings.tavily_key)
                        c["stage"] = "research"
                    else:
                        log(
                            c,
                            "Research connection needed",
                            "Request saved from chat; live search is not configured. No vendors contacted.",
                            "research",
                        )
                    c["shortlistVendorIds"] = [v["id"] for v in c["vendors"]]
                    c["outreachVendorIds"] = list(c["shortlistVendorIds"])
                    c["workflowPlan"] = workflow_plan(
                        mode, bool(settings.tavily_key), c["shortlistVendorIds"]
                    )
                    resulting_case = c
                    assistant["caseId"] = c["id"]
                    assistant["body"] += (
                        "\n\nYour supplier request is saved with the event context. "
                        + (
                            "Existing supplier reused; a fresh enquiry is drafted. No message has been sent."
                            if mode == "liaise"
                            else "Public sources collected for the entire candidate pool; verified contact details and final quotation replies are still needed. Approval happens after liaison."
                            if settings.tavily_key
                            else "Live vendor search is not connected yet; no outreach has been sent."
                        )
                    )
                except (ValueError, httpx.HTTPError) as error:
                    assistant["body"] += "\n\n" + str(error)
        thread = repository.append_message(
            event["id"], assistant, role, resulting_case, task_id=task_id
        )
        assistant = next(m for m in thread["messages"] if m.get("inReplyTo") == body.requestId)
        return {
            "assistant": assistant,
            "eventId": event["id"],
            "taskId": task_id,
            "state": state(role),
        }

    return app


app = create_app()
