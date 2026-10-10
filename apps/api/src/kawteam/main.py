import base64
import copy
import hmac
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal
from uuid import NAMESPACE_URL, uuid4, uuid5
from zoneinfo import ZoneInfo

import httpx
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from .auth import issue_session, verify_session
from .automation import Automation
from .config import Settings
from .contacts import contact_valid, discover_contact
from .drive import parse_drive_url, read_drive
from .enquiries import enquiry_body
from .failsafes import open_failsafe, refresh_context_failsafes, resolve_failsafe
from .gmail import DEFAULT_TOKEN_PATH, Gmail
from .liaison import Liaison, request_token
from .memory import extract_text, facts_from_text, intake, resolve_event, retrieve
from .progress import save_progress
from .projects import DEFAULT_SETTINGS, fresh_vendor, named_vendors, route, thread_id, workflow_plan
from .providers import chat_response, discover
from .quote_reply import extract_quote
from .repository import SupabaseRepository, payload_hash
from .schemas.domain import NewBrief
from .tasks import (
    current_decisions,
    invalidate_terms,
    project_name,
    selection_target,
    task_name,
    task_queue,
)
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


class AutomationBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    caseId: str | None = Field(default=None, min_length=1, max_length=150)


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
    driveUrl: str | None = Field(default=None, max_length=1000)
    message: str = Field(min_length=1, max_length=5000)
    eventId: str | None = Field(default=None, max_length=150)
    taskId: str | None = Field(default=None, max_length=150)
    requestId: str = Field(default_factory=lambda: str(uuid4()), max_length=150)


def create_case(brief, id, event_id=None):
    brief = dict(brief)
    assumed_deadline = not brief.get("deadline")
    if assumed_deadline:
        brief["deadline"] = (datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date() + timedelta(days=14)).isoformat()
    if not brief.get("targetSen") and brief.get("budgetSen"):
        brief["targetSen"] = brief["budgetSen"]
    b = NewBrief.model_validate(brief)
    if b.deadline <= datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date():
        raise ValueError("Delivery date must be in the future.")
    return {
        **b.model_dump(mode="json", by_alias=True),
        "id": id,
        "eventId": event_id,
        "assumptions": ["deadline"] if assumed_deadline else [],
        "failsafes": [],
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

    def email_configured():
        return bool(settings.gmail_sender and (settings.gmail_authorized_user_json or Path(settings.gmail_token_path or DEFAULT_TOKEN_PATH).is_file()))

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
            "email": "configured" if email_configured() else "setup_required",
            "websiteOutreach": "available",
            "workbuddy": "desktop_tools_available",
            "workbuddyTrigger": "not_connected",
            "model": settings.gemini_model,
        }

    @app.get("/email/status")
    def email_status(role=Depends(actor)):
        return Gmail.from_settings(settings).profile()

    @app.post("/automation/tick")
    def automation_tick(body: AutomationBody, role=Depends(actor)):
        editable(role)
        if not email_configured():
            return {"processed": False, "reason": "Email is not configured."}
        if body.caseId:
            case = record("case", body.caseId)
        else:
            candidates = [c for c in repository.snapshot()["cases"] if c.get("automation", {}).get("status") in {"queued", "awaiting_replies"} or (c.get("automation", {}).get("status") == "review_ready" and any(d["status"] == "approved" for d in current_decisions(c)))]
            candidates.sort(key=lambda c: c["automation"].get("lastTickAt", ""))
            case = candidates[0] if candidates else None
        if not case:
            return {"processed": False}
        last_tick = case.get("automation", {}).get("lastTickAt")
        if last_tick and (datetime.now(ZoneInfo("Asia/Kuala_Lumpur")) - datetime.fromisoformat(last_tick)).total_seconds() < 12:
            return {"processed": False, "reason": "Task step already running or recently checked."}
        engine = Automation(email_service(), lambda vendor, case: discover_contact(vendor, case, settings), lambda case, message: extract_quote(case, message, settings))
        try:
            result = engine.tick(case["id"], role)
            if any(f["code"] == "provider_connection" and f["status"] == "open" for f in result.get("failsafes", [])):
                resolve_failsafe(result, "provider_connection")
                result = email_service().save(result, role)
        except (ValueError, RuntimeError, httpx.HTTPError) as error:
            if isinstance(error, ValueError) and ("Stale" in str(error) or "authoris" in str(error) or "changed" in str(error)):
                raise
            current = record("case", case["id"])
            current["automation"].update(status="needs_attention", error=str(error)[:500] if isinstance(error, ValueError) else "Provider step unavailable. Saved task data is retained.")
            open_failsafe(current, "provider_connection", "Outreach needs attention", current["automation"]["error"], [])
            result = email_service().save(current, role)
        save_progress(repository, result, role)
        return {"processed": True, "caseId": result["id"], "status": result["automation"]["status"]}

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
                c["workflowPlan"] = workflow_plan("research", True, c["shortlistVendorIds"], email_configured())
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
            if not document.get("taskId"):
                current_facts.update(facts_from_text(document["text"]))
        # Replace previously derived keys; unrelated project facts are retained.
        managed_keys = set(event.get("documentFactKeys", []))
        for document in old_documents:
            if not document.get("taskId"):
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
        return execute_chat(body, role)

    @app.post("/chat/references")
    def chat_references(payload: str = Form(...), files: list[UploadFile] = File(default=[]), role=Depends(actor)):
        editable(role)
        try:
            body = ChatBody.model_validate_json(payload)
        except ValueError as error:
            raise ValueError("Invalid chat request. Check your message.") from error
        if len(files) > 3:
            raise ValueError("Attach up to three files, with a combined size of 3 MB.")
        references = []
        total_size = 0
        for file in files:
            content = file.file.read(3 * 1024 * 1024 + 1)
            total_size += len(content)
            if total_size > 3 * 1024 * 1024:
                raise ValueError("Attached files must total 3 MB or less.")
            name = (file.filename or "document.txt").replace(chr(92), "/").split("/")[-1][:150]
            try:
                text = extract_text(name, content)
            except Exception as error:
                raise ValueError(str(error) if isinstance(error, ValueError) else "Could not read this file. Use a readable document.") from error
            references.append({"name": name, "text": text, "originalBase64": base64.b64encode(content).decode(), "size": len(content), "characters": len(text), "status": "ready"})
        return execute_chat(body, role, references)

    def execute_chat(body, role, references=None):
        editable(role)
        references = references or []
        if body.driveUrl:
            parse_drive_url(body.driveUrl)
        reference_hash = payload_hash({"drive": body.driveUrl, "files": [{"name": r["name"], "content": r["originalBase64"]} for r in references]}) if references or body.driveUrl else None
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
        for reference in references:
            digest = payload_hash({"task": task_id, "content": reference["originalBase64"]})
            reference.update(id=str(uuid5(NAMESPACE_URL, "chat-reference:" + digest)), contentDigest=digest, eventId=event["id"], taskId=task_id, source="chat", createdAt=datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).isoformat())
        user_message = {
            "referenceHash": reference_hash,
            "attachments": [{"id": r["id"], "name": r["name"]} for r in references],
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
        if previous_user and (previous_user["body"] != body.message or previous_user.get("referenceHash") != reference_hash):
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
        if body.driveUrl and event.get("driveSource", {}).get("url") != body.driveUrl:
            event = sync_drive(event["id"], DriveBody(url=body.driveUrl), role)
        for reference in references:
            repository.upload(reference, {}, role)
        event = repository.get("event", event["id"])
        documents = [d for d in repository.documents(event["id"]) if not d.get("taskId") or d["taskId"] == task_id]
        task_facts = {}
        for document in documents:
            if document.get("taskId") == task_id:
                task_facts.update(facts_from_text(document["text"]))
        event = {**event, "facts": {**event.get("facts", {}), **task_facts}}
        context = retrieve(event["id"], body.message, documents)
        if not any(m["id"] == body.requestId for m in thread["messages"]):
            thread = repository.append_message(event["id"], user_message, role, task_id=task_id)
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
            active_requests = provider_event["activeRequests"]
            provider_event["executionStatus"] = {
                "email": "configured" if email_configured() else "setup_required",
                "websiteOutreach": "available",
                "workbuddy": "desktop_tools_available",
                "suppliersFound": sum(len(c["vendors"]) for c in active_requests),
                "verifiedContacts": sum(contact_valid(v) for c in active_requests for v in c["vendors"]),
                "emailsSent": sum(m.get("direction") == "sent" and m.get("executionMode") == "live" for c in active_requests for m in c.get("messages", [])),
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
        if current_case and not current_case.get("vendors") and known_vendor:
            requested = True
        if current_case and not updated_requirements and not pending and not (known_vendor and not current_case.get("vendors")):
            requested = False
            if answer["provider"] == "setup_required" and re.search(
                r"\b(?:what|current|budget|summary|status|summarise|summarize)\b",
                body.message,
                re.IGNORECASE,
            ):
                assistant["provider"] = "saved_context"
                assistant["body"] = (
                    f"Budget: {'RM' + format(current_case['budgetSen'] / 100, ',.2f') if current_case.get('budgetSen') else 'not specified'}. This task has {len(current_case.get('vendors', []))} supplier sources and {sum(m.get('direction') == 'sent' and m.get('executionMode') == 'live' for m in current_case.get('messages', []))} real enquiries recorded."
                )
        resulting_case = None
        pause_outreach = bool(re.search(r"\b(?:do\s+not|don't|dont|never|stop|pause|cancel|no)\b.{0,40}\b(?:email|send|contact|outreach|liais\w*)\b|\b(?:research|search)\s+only\b|\bonly\s+(?:research|search)\b", body.message, re.IGNORECASE) or (current_case and re.match(r"\s*(?:stop|pause|cancel)\b", body.message, re.IGNORECASE)))
        if pause_outreach and current_case and not updated_requirements:
            requested = False
            resulting_case = copy.deepcopy(current_case)
            resulting_case["automation"] = {"requestHash": request_token(resulting_case), "authorisedBy": role, "status": "paused"}
            assistant["body"] = "Supplier outreach is paused. I won't start any further enquiries or clarifications for this task. Previously sent emails remain in its history."
            assistant["caseId"] = resulting_case["id"]
        explicit_outreach = bool(not pause_outreach and current_case and not updated_requirements and re.match(r"\s*(?:(?:okay|ok|yes|then|now|please|just|go\s+ahead(?:\s+and)?)[, ]+)*(?:(?:can|could|would|will)\s+you\s+)?(?:please\s+)?(?:email\s+(?:them|vendors?|suppliers?|these|those|all|the)\b|send\s+(?:(?:an?|the|them)\s+)?(?:emails?|enquir(?:y|ies)|quotation\s+requests?)\b|contact\s+(?:them|vendors?|suppliers?|the|all|these|those)\b|reach\s+out\b|(?:start|resume|continue)\s+(?:the\s+)?(?:outreach|liaison)\b)", body.message, re.IGNORECASE))
        if explicit_outreach:
            resulting_case = copy.deepcopy(current_case)
            resulting_case["automation"] = {"requestHash": request_token(resulting_case), "authorisedBy": role, "status": "queued"}
            for vendor in resulting_case["vendors"]:
                vendor.pop("outreachBlock", None)
            assistant["body"] = "Outreach is queued for this task. I'll verify the suppliers' public contact details, send non-binding enquiries, and check replies while KawTeam is open."
            assistant["caseId"] = resulting_case["id"]
        retry_requested = bool(current_case and re.match(r"\s*(?:retry|try again|resume)\b", body.message, re.IGNORECASE))
        if retry_requested:
            if not current_case.get("vendors"):
                requested = True
            else:
                resulting_case = copy.deepcopy(current_case)
                resulting_case["automation"] = {"requestHash": request_token(resulting_case), "authorisedBy": role, "status": "queued"}
                for vendor in resulting_case["vendors"]:
                    vendor.pop("outreachBlock", None)
                assistant["body"] = "I'm trying the available supplier routes again and will keep you updated."
                assistant["caseId"] = resulting_case["id"]
        if requested:
            brief = {
                **intake(request_message, event),
                **(
                    {
                        k: current_case.get(k)
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
                **{k: v for k, v in (answer.get("brief") or {}).items() if v is not None},
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
            try:
                c = create_case(
                    {
                        k: brief.get(k)
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
                if current_case:
                    c["assumptions"] = [] if overrides.get("deadline") else current_case.get("assumptions", [])
                explicit_total = "budgetSen" in overrides and overrides.get("budgetSource") != "unit"
                unit_budget = None if explicit_total and "unitBudgetSen" not in overrides else brief.get("unitBudgetSen") or (current_case or {}).get("unitBudgetSen")
                if explicit_total:
                    c.pop("unitBudgetSen", None)
                    c["budgetSource"] = "total"
                elif overrides.get("budgetSource"):
                    c["budgetSource"] = overrides["budgetSource"]
                if unit_budget:
                    c["unitBudgetSen"] = unit_budget
                    if c.get("quantity") and not explicit_total and (c.get("budgetSource") == "unit" or not c.get("budgetSen")):
                        c["budgetSen"] = unit_budget * c["quantity"]
                        c["targetSen"] = c["budgetSen"]
                c.update(taskWorkflowVersion=1, selectionTarget=target)
                c.setdefault("vendorDecisions", [])
                c["sourceDocumentIds"] = [d["id"] for d in documents]
                c["taskId"] = task_id
                c["workflowMode"] = mode
                if mode == "liaise" and known_vendor and (not current_case or not c["vendors"]):
                    c["vendors"] = [fresh_vendor(known_vendor)]
                    c["stage"] = "negotiation"
                    c["draft"].update(
                        {
                            "vendorId": known_vendor["id"],
                            "recipient": known_vendor["name"]
                            + " (contact verification required)",
                            "body": enquiry_body(c),
                        }
                    )
                    log(
                        c,
                        "Existing supplier reused",
                        "Research skipped. Prior quotation and approval cleared; fresh terms required.",
                        "negotiation",
                    )
                elif current_case and c["vendors"]:
                    # Retain known identities; an exhausted empty search can try again after edits.
                    pass
                elif mode == "liaise":
                    open_failsafe(c, "vendor_identity", "Which supplier should I use?", "The supplier reference is ambiguous. Name the business so I can continue the existing relationship.", ["vendor"])
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
                    mode, bool(settings.tavily_key), c["shortlistVendorIds"], email_configured()
                )
                resulting_case = c
                c["automation"] = {"requestHash": request_token(c), "authorisedBy": role, "status": "paused" if pause_outreach or (mode == "liaise" and not c["vendors"]) else "queued"}
                for vendor in c["vendors"]:
                    vendor.pop("outreachBlock", None)
                assistant["caseId"] = c["id"]
                refresh_context_failsafes(c)
                if not c["vendors"] and mode != "liaise":
                    open_failsafe(c, "research_unavailable", "No supplier source is available yet", "Live search is not connected." if not settings.tavily_key else "Search returned no supplier candidates. Add a known business or refine the request so I can try another route.", [])
                elif c["vendors"]:
                    resolve_failsafe(c, "research_unavailable")
                assistant["body"] = (
                    "Research saved; outreach is paused as requested."
                    if pause_outreach else
                    "The task is saved. Add the supplier's name in Failsafe so I can contact the right business."
                    if mode == "liaise" and not c["vendors"] else
                    "I'm preparing a fresh enquiry for the existing supplier and will check their replies."
                    if mode == "liaise" else
                    f"Found {len(c['vendors'])} supplier sources. I'm checking their business contacts next, then I'll send enquiries and follow up on replies. No emails have been sent yet."
                    if settings.tavily_key and email_configured() else
                    f"Found {len(c['vendors'])} supplier sources. Email isn't connected yet, so the enquiries haven't been sent."
                    if settings.tavily_key else
                    "Your task is saved. Live supplier search isn't connected yet."
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
