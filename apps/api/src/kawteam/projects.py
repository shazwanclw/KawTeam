import re
from copy import deepcopy

DEFAULT_SETTINGS = {
    "mode": "general",
    "instructions": "",
    "shortlistSize": 3,
    "preferredVendorId": None,
}


def thread_id(event_id, task_id=None):
    return f"event-{event_id}" + (f"-task-{task_id}" if task_id else "")


def named_vendors(message, cases):
    known = {v["id"]: v for c in cases for v in c.get("vendors", [])}
    return [
        v
        for v in known.values()
        if re.search(r"(?<!\w)" + re.escape(v["name"]) + r"(?!\w)", message, re.IGNORECASE)
    ]


def resolve_vendor(message, event, cases, thread):
    # Explicit names/preferences refer to the account library. Implicit references
    # refer only to this conversation scope, never another task's selected supplier.
    named = named_vendors(message, cases)
    if len(named) == 1:
        return named[0]
    if len(named) > 1:
        return None
    preferred = event.get("assistantSettings", {}).get("preferredVendorId")
    if preferred:
        return next((v for c in cases for v in c.get("vendors", []) if v["id"] == preferred), None)
    scoped = [
        c
        for c in cases
        if c.get("eventId") == event["id"] and c.get("taskId") == thread.get("taskId")
    ]
    known = {v["id"]: v for c in scoped for v in c.get("vendors", [])}
    if re.search(
        r"\b(?:same|that|previous|existing)\s+(?:vendor|supplier)|\bagain\b", message, re.IGNORECASE
    ):
        recent_ids = [
            m.get("caseId") for m in reversed(thread.get("messages", [])) if m.get("caseId")
        ]
        for case_id in recent_ids:
            c = next((c for c in scoped if c["id"] == case_id), None)
            if c and c.get("selectedVendorId") in known:
                return known[c["selectedVendorId"]]
            if c and c.get("workflowMode") == "liaise" and len(c.get("vendors", [])) == 1:
                return c["vendors"][0]
        selected = {c["selectedVendorId"] for c in scoped if c.get("selectedVendorId")}
        if len(selected) == 1:
            return known.get(next(iter(selected)))
    return None


def route(message, event, cases, thread):
    settings = {**DEFAULT_SETTINGS, **event.get("assistantSettings", {})}
    vendor = resolve_vendor(message, event, cases, thread)
    explicit_discovery = bool(
        re.search(
            r"\b(?:find|research|discover|search(?:\s+for)?|look\s+for)\b[^.!?\n]{0,60}\b(?:vendors?|suppliers?|caterers?|companies)\b",
            message,
            re.IGNORECASE,
        )
    )
    repeat = bool(
        re.search(
            r"\b(?:same|that|previous|existing)\s+(?:vendor|supplier)|\b(?:again|reorder)\b|\b\d+\s+more\s+(?:t-?shirts?|shirts?|bags?|units?|items?)\b",
            message,
            re.IGNORECASE,
        )
    )
    if settings["mode"] == "research" or (settings["mode"] == "general" and explicit_discovery):
        return "research", None
    mode = (
        "liaise"
        if settings["mode"] == "liaise" or repeat or vendor or named_vendors(message, cases)
        else "research"
    )
    return mode, vendor


def fresh_vendor(vendor):
    identity = {
        k: deepcopy(vendor[k])
        for k in [
            "id",
            "name",
            "initials",
            "location",
            "color",
            "sourceUrl",
            "evidenceExcerpt",
            "executionMode",
            "contact",
        ]
        if k in vendor
    }
    return {
        **identity,
        "goodsSen": 0,
        "deliverySen": None,
        "initialSen": 0,
        "arrival": None,
        "specsConfirmed": False,
        "quantity": None,
        "status": "Fresh quotation needed",
        "description": "Previously known supplier. Prior prices and delivery promises do not apply to this request.",
        "strengths": ["Existing supplier identity"],
        "concerns": [
            "Fresh quantity, specification, landed cost and delivery confirmation required"
        ],
        "quoteRef": "NEW-QUOTE-REQUIRED",
    }


def workflow_plan(mode, search_connected, shortlist):
    return [
        {
            "id": "context",
            "label": "Understand request",
            "status": "complete",
            "detail": "Project memory and latest chat details applied.",
        },
        {
            "id": "research",
            "label": "Research suppliers" if mode == "research" else "Use existing supplier",
            "status": "complete" if mode == "liaise" or shortlist else "blocked",
            "detail": "Research skipped; supplier identity reused."
            if mode == "liaise"
            else (
                "Public sources collected; commercial fit unverified."
                if search_connected and shortlist
                else "Search connection needed."
            ),
        },
        {
            "id": "shortlist",
            "label": "Verify candidate pool",
            "status": "pending" if shortlist else "blocked",
            "detail": f"{len(shortlist)} candidate(s) retained for liaison. Ranking needs final quotes.",
        },
        {
            "id": "outreach",
            "label": "Liaise with all suitable suppliers",
            "status": "blocked",
            "detail": "Verified supplier contacts and a connected email provider are required. Non-binding enquiries only; nothing sent.",
        },
        {
            "id": "quotes",
            "label": "Collect and compare fresh quotes",
            "status": "pending",
            "detail": "Confirm total cost, scope and delivery before deciding.",
        },
        {
            "id": "decision",
            "label": "Your approval, then supplier confirmation",
            "status": "pending",
            "detail": "Rank complete final replies for human approval. A separate supplier confirmation is required before secured.",
        },
    ]
