import base64
import hmac
from datetime import datetime
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
from .memory import extract_text, facts_from_text, intake, resolve_event, retrieve
from .projects import DEFAULT_SETTINGS, fresh_vendor, named_vendors, route, thread_id, workflow_plan
from .providers import chat_response, discover
from .repository import SupabaseRepository, payload_hash
from .schemas.domain import NewBrief
from .workflow import fit, log, outcome, transition


class ProfileBody(BaseModel):
    profile: Literal["organiser", "teammate", "observer"]


class ActionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal[
        "create", "research", "choose", "edit-draft", "approve", "reject", "prepare", "send", "sync"
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
        return {"product": "KawTeam", "status": "ok", "workbuddy": "deferred"}

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
        return {**snapshot, "profile": role, "storage": "supabase"}

    @app.get("/connections")
    def connections(role=Depends(actor)):
        return {
            "database": "connected",
            "ai": "configured" if settings.gemini_key else "setup_required",
            "search": "configured" if settings.tavily_key else "setup_required",
            "email": "controlled_demo_only",
            "workbuddy": "deferred",
            "model": settings.gemini_model,
        }

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
                event_settings = (
                    (repository.get("event", c.get("eventId")) or {}).get("assistantSettings", {})
                    if c.get("eventId")
                    else {}
                )
                cap = event_settings.get("shortlistSize", 3)
                c["shortlistVendorIds"] = [v["id"] for v in fresh_candidates[:cap]]
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
                    "name": body.message.strip().split("\n")[0][:65] or "New project",
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
        if body.taskId and not any(t["id"] == body.taskId for t in event.get("tasks", [])):
            raise ValueError("Task does not belong to the selected project.")
        conversation_id = thread_id(event["id"], body.taskId)
        thread = repository.get("thread", conversation_id) or {
            "id": conversation_id,
            "taskId": body.taskId,
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
            return {"assistant": existing, "eventId": event["id"], "state": state(role)}
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
                task_id=body.taskId,
            )
        try:
            answer = chat_response(body.message, event, context, thread["messages"], settings)
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
        mode, known_vendor = route(request_message, event, snapshot["cases"], thread)
        requested = (
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
        resulting_case = None
        if requested:
            brief = {
                **intake(request_message, event),
                **(pending.get("brief", {}) if pending else {}),
                **(answer.get("brief") or {}),
            }
            # Explicit new user values take priority over model output and document memory.
            brief.update(facts_from_text(request_message))
            brief.update(facts_from_text(body.message))
            if brief.get("budgetSen"):
                brief["targetSen"] = min(
                    brief.get("targetSen") or brief["budgetSen"], brief["budgetSen"]
                )
            missing = [
                k for k in ["quantity", "budgetSen", "deadline", "location"] if not brief.get(k)
            ]
            if mode == "liaise" and not known_vendor:
                assistant["body"] += (
                    "\n\nWhich vendor should I contact? Name a supplier from this project or choose one in assistant settings."
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
                                f"kawteam:{event['id']}:{body.taskId or 'main'}:{body.requestId}",
                            )
                        ),
                        event["id"],
                    )
                    c["sourceDocumentIds"] = [d["id"] for d in documents]
                    c["taskId"] = body.taskId
                    c["workflowMode"] = mode
                    if mode == "liaise":
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
                    c["shortlistVendorIds"] = [
                        v["id"]
                        for v in c["vendors"][
                            : event.get("assistantSettings", {}).get("shortlistSize", 3)
                        ]
                    ]
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
                            else "Public sources collected; supplier quotes and email approval are still needed."
                            if settings.tavily_key
                            else "Live vendor search and email are not connected yet; no outreach has been sent."
                        )
                    )
                except (ValueError, httpx.HTTPError) as error:
                    assistant["body"] += "\n\n" + str(error)
        thread = repository.append_message(
            event["id"], assistant, role, resulting_case, task_id=body.taskId
        )
        assistant = next(m for m in thread["messages"] if m.get("inReplyTo") == body.requestId)
        return {"assistant": assistant, "eventId": event["id"], "state": state(role)}

    return app


app = create_app()
