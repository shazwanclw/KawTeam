"""Evidence-based chat updates, separate from internal agent steps."""

from .liaison import request_token
from .projects import thread_id
from .repository import payload_hash
from .tasks import now
from .workflow import fit


def progress_message(case):
    scope = request_token(case)
    messages = [m for m in case.get("messages", []) if m.get("executionMode") == "live" and m.get("requestHash") == scope]
    sent = sum(m.get("direction") == "sent" for m in messages)
    replied = len({m.get("vendorId") for m in messages if m.get("direction") == "received"})
    ready = sum(v.get("liaisonStatus") == "ready" and fit(case, v) == "Meets your brief" for v in case.get("vendors", []))
    status = case.get("automation", {}).get("status")
    if not sent and status != "needs_attention":
        return None
    key = "workflow-" + payload_hash({"case": case["id"], "scope": scope, "sent": sent, "replied": replied, "ready": ready, "attention": status == "needs_attention"})[:48]
    body = f"Sent {sent} supplier message{'s' if sent != 1 else ''}."
    if replied:
        body += f" {replied} supplier{'s have' if replied != 1 else ' has'} replied."
    if ready:
        body += f" {ready} quotation{'s are' if ready != 1 else ' is'} ready to review."
    elif status == "needs_attention":
        body += " The remaining routes need attention; check Failsafe."
    else:
        body += " I'll check replies and continue the conversation."
    return {"id": key, "inReplyTo": key, "role": "assistant", "body": body, "provider": "workflow", "caseId": case["id"], "time": now(), "citations": []}


def save_progress(repository, case, actor):
    message = progress_message(case)
    if not message:
        return
    thread = repository.get("thread", thread_id(case["eventId"], case["taskId"]))
    if not thread or len(thread["messages"]) >= 150 or any(m.get("id") == message["id"] for m in thread["messages"]):
        return
    thread["messages"].append(message)
    try:
        repository.save("thread", thread, thread["backendRevision"], actor, message["id"], payload_hash(thread))
    except ValueError as error:
        if "Stale" not in str(error):
            raise
        # The next tick retries after a concurrent chat edit; never overwrite it.
