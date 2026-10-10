"""Durable task-scoped communication. Agents cannot approve suppliers or verify contacts."""

import copy
import re
from datetime import datetime
from uuid import uuid4

import httpx

from .gmail import email_address, message_raw
from .projects import fresh_vendor
from .repository import payload_hash
from .tasks import now, term_token
from .workflow import log


def request_token(case):
    return payload_hash(
        {
            k: case.get(k)
            for k in ["quantity", "budgetSen", "deadline", "location", "selectionTarget", "goal"]
        }
    )


class Liaison:
    def __init__(self, repository, mail):
        self.repo, self.mail = repository, mail

    def case(self, case_id, expected=None, actor="teammate"):
        if actor not in {"organiser", "teammate"}:
            raise PermissionError("This profile is view-only.")
        case = self.repo.get("case", case_id)
        if not case or not case.get("eventId") or not case.get("taskId"):
            raise ValueError("A saved project task is required for live liaison.")
        if expected is not None and case["backendRevision"] != expected:
            raise ValueError("Stale revision. Refresh the task before continuing.")
        case.setdefault("messages", [])
        case.setdefault("events", [])
        case.setdefault("selectionTarget", 1)
        case.setdefault("vendorDecisions", [])
        return copy.deepcopy(case)

    def save(self, case, actor):
        return self.repo.save(
            "case", case, case["backendRevision"], actor, str(uuid4()), payload_hash(case)
        )

    def vendor(self, case, vendor_id):
        vendor = next((v for v in case["vendors"] if v["id"] == vendor_id), None)
        if not vendor or vendor.get("executionMode", "demo") != "live":
            raise ValueError("Choose a real supplier saved in this task, not a sample supplier.")
        return vendor

    def contact(self, case_id, vendor_id, address, expected, actor):
        if actor != "organiser":
            raise PermissionError(
                "Only the organiser can register a human-verified supplier contact."
            )
        case = self.case(case_id, expected, actor)
        vendor = self.vendor(case, vendor_id)
        address = email_address(address)
        if case.get("emailIntents") and vendor.get("contact", {}).get("email") != address:
            raise ValueError("A contacted supplier address cannot be changed within this task.")
        identity = fresh_vendor(vendor)
        vendor.update(identity)
        vendor["contact"] = {
            "email": address,
            "verifiedBy": "organiser",
            "verifiedAt": now(),
            "provenance": "human-confirmed",
        }
        log(
            case,
            "Supplier contact verified",
            f"The organiser registered the contact for {vendor['name']}.",
            "human",
        )
        case["events"][-1]["milestone"] = True
        return self.save(case, actor)

    def send(self, case_id, vendor_id, subject, body, expected, request_id, actor):
        case = self.case(case_id, actor=actor)
        vendor = self.vendor(case, vendor_id)
        address = vendor.get("contact", {}).get("email")
        if not address or vendor["contact"].get("verifiedBy") != "organiser":
            raise ValueError("A verified supplier contact is required before sending.")
        # All messages on this endpoint are explicitly non-binding. Confirmation is a separate future action.
        if re.search(
            r"\b(?:confirm(?:ed)?\s+(?:the\s+)?(?:booking|order)|accept\s+(?:the\s+)?(?:offer|quote)|place\s+(?:the\s+)?order|go\s+ahead\s+with\s+(?:the\s+)?(?:order|booking))\b",
            body,
            re.IGNORECASE,
        ):
            raise ValueError(
                "This tool sends non-binding enquiries only. Final commitments require the organiser's decision and a separate confirmation flow."
            )
        prefix = "Non-binding quotation enquiry from KawTeam. This message does not confirm an order, booking or payment. Final selection requires the organiser's explicit approval.\n\n"
        outgoing = prefix + body
        sender = self.mail.profile()["sender"]
        digest = payload_hash(
            {
                "vendorId": vendor_id,
                "recipient": address,
                "subject": subject,
                "body": outgoing,
                "gmailSender": sender,
            }
        )
        intents = case.setdefault("emailIntents", [])
        prior = next((intent for intent in intents if intent["id"] == request_id), None)
        if prior:
            if prior["digest"] != digest:
                raise ValueError("Idempotency key reused for different email contents.")
            if prior["status"] == "sent":
                return case
            raise ValueError(
                "Email intent already reserved or uncertain; reconcile the sender's Sent folder before any new send."
            )
        if case["backendRevision"] != expected:
            raise ValueError("Stale revision. Refresh the task before sending.")
        if len(intents) >= 60 or sum(i["vendorId"] == vendor_id for i in intents) >= 4:
            raise ValueError(
                "Task outreach limit reached (60 messages per task; four per supplier)."
            )
        if any(i["vendorId"] == vendor_id and i["status"] != "sent" for i in intents):
            raise ValueError(
                "An earlier supplier send is unresolved; reconcile it before continuing."
            )
        message_raw(sender, address, subject, outgoing, request_id)
        sent = [
            i
            for i in intents
            if i["vendorId"] == vendor_id
            and i["status"] == "sent"
            and i.get("gmailSender") == sender
            and i.get("requestHash") == request_token(case)
        ]
        thread = sent[-1].get("providerThreadId") if sent else None
        replies = [
            m
            for m in case.get("messages", [])
            if m.get("vendorId") == vendor_id
            and m.get("direction") == "received"
            and m.get("rfcMessageId")
            and m.get("gmailSender") == sender
            and m.get("requestHash") == request_token(case)
        ]
        intent = {
            "id": request_id,
            "digest": digest,
            "vendorId": vendor_id,
            "recipient": address,
            "subject": subject,
            "body": outgoing,
            "status": "reserved",
            "createdAt": now(),
            "termsHash": term_token(case, vendor),
            "gmailSender": sender,
            "requestHash": request_token(case),
        }
        intents.append(intent)
        case = self.save(
            case, actor
        )  # Compare-and-swap reservation happens before any external send.
        try:
            receipt = self.mail.send(
                address,
                subject,
                outgoing,
                request_id,
                thread_id=thread,
                reply_to=replies[-1]["rfcMessageId"] if replies else None,
            )
        except (ValueError, RuntimeError, OSError, TimeoutError, httpx.HTTPError) as error:
            current = self.case(case_id, actor=actor)
            saved_intent = next(i for i in current["emailIntents"] if i["id"] == request_id)
            saved_intent["status"] = "uncertain"
            self.save(current, actor)
            raise ValueError(
                "Email outcome is uncertain; automatic resend is blocked. Check the sender's Sent folder and reconcile this intent."
            ) from error
        current = self.case(case_id, actor=actor)
        saved_intent = next(i for i in current["emailIntents"] if i["id"] == request_id)
        saved_intent.update(receipt, status="sent", sentAt=now())
        vendor = self.vendor(current, vendor_id)
        vendor["liaisonStatus"] = "awaiting_reply"
        current["messages"].append(
            {
                "id": str(uuid4()),
                "vendorId": vendor_id,
                "direction": "sent",
                "kind": "enquiry",
                "body": outgoing,
                "subject": subject,
                "at": now(),
                "executionMode": "live",
                "termsHash": intent["termsHash"],
                "gmailSender": sender,
                "requestHash": intent["requestHash"],
                **receipt,
            }
        )
        log(
            current,
            "Supplier enquiry sent",
            f"A non-binding enquiry was delivered to {vendor['name']}; awaiting reply.",
            "liaison",
        )
        current["events"][-1]["milestone"] = True
        return self.save(current, actor)

    def sync(self, case_id, expected, actor):
        case = self.case(case_id, expected, actor)
        sender = self.mail.profile()["sender"]
        pairs = {
            (i["vendorId"], i["providerThreadId"])
            for i in case.get("emailIntents", [])
            if i["status"] == "sent" and i.get("gmailSender") == sender
        }
        if not pairs:
            raise ValueError(
                "No saved supplier threads for the configured sender. Earlier mailbox history is retained, but cannot be read through this account."
            )
        if len(pairs) > 20:
            raise ValueError("Reply sync is bounded to 20 supplier threads per task.")
        known = {
            m.get("providerMessageId")
            for m in case.get("messages", [])
            if m.get("gmailSender") == sender
        }
        count = 0
        for vendor_id, thread in sorted(pairs):
            vendor = self.vendor(case, vendor_id)
            for reply in self.mail.replies(thread, vendor["contact"]["email"]):
                if reply["providerMessageId"] in known:
                    continue
                enquiries = [
                    i
                    for i in case["emailIntents"]
                    if i.get("gmailSender") == sender
                    and i.get("vendorId") == vendor_id
                    and i.get("providerThreadId") == thread
                    and i.get("status") == "sent"
                ]
                in_reply_to = reply.get("rfcInReplyTo")
                matched = next(
                    (i for i in enquiries if in_reply_to and i.get("rfcMessageId") == in_reply_to),
                    None,
                )
                hashes = {i.get("requestHash") for i in enquiries}
                # Missing thread headers are acceptable only when the entire thread has one request scope.
                scope = (
                    matched.get("requestHash")
                    if matched
                    else next(iter(hashes))
                    if len(hashes) == 1
                    else None
                )
                case["messages"].append(
                    {
                        **reply,
                        "id": str(uuid4()),
                        "vendorId": vendor_id,
                        "direction": "received",
                        "kind": "supplier-reply",
                        "at": now(),
                        "executionMode": "live",
                        "gmailSender": sender,
                        "requestHash": scope,
                    }
                )
                known.add(reply["providerMessageId"])
                vendor["liaisonStatus"] = "reply_received"
                count += 1
        if not count:
            return case
        log(
            case,
            "Supplier replies received",
            f"{count} new supplier replies saved. Commercial terms need validation before final approval.",
            "liaison",
        )
        case["events"][-1]["milestone"] = True
        return self.save(case, actor)

    def quote(self, case_id, vendor_id, message_id, expected, actor, interpreter):
        from .quote_reply import validate_quote
        from .tasks import current_decisions

        case = self.case(case_id, expected, actor)
        vendor = self.vendor(case, vendor_id)
        decision = next((d for d in current_decisions(case) if d["vendorId"] == vendor_id), None)
        replies = [
            m
            for m in case["messages"]
            if m.get("vendorId") == vendor_id
            and m.get("direction") == "received"
            and m.get("executionMode") == "live"
        ]
        message = next((m for m in replies if m.get("providerMessageId") == message_id), None)
        latest = max(replies, key=lambda m: int(m.get("receivedAtMs") or 0)) if replies else None
        # For fixtures/legacy timestamps, break ties by existing append order.
        if replies and all(not m.get("receivedAtMs") for m in replies):
            latest = replies[-1]
        if not message or message != latest:
            raise ValueError("Interpret only the latest saved supplier reply for this task.")
        if message.get("requestHash") != request_token(case):
            raise ValueError(
                "Supplier reply does not belong to the current request. Send a fresh enquiry and obtain matching terms."
            )
        if message.get("quoteInterpretation"):
            return case
        data = validate_quote(interpreter(case, message), message["body"])
        if data["confirmation"]:
            if not decision or decision["status"] != "approved":
                raise ValueError(
                    "Supplier confirmation needs a current organiser-approved decision first."
                )
            candidate = {
                **vendor,
                **{
                    k: data[k]
                    for k in [
                        "quantity",
                        "goodsSen",
                        "deliverySen",
                        "arrival",
                        "specsConfirmed",
                        "validUntil",
                    ]
                },
            }
            from .workflow import fit

            if (
                term_token(case, candidate) != decision["termsHash"]
                or fit(case, candidate) != "Meets your brief"
            ):
                raise ValueError(
                    "Supplier confirmation does not match the valid approved quotation terms."
                )
            approved_ms = datetime.fromisoformat(decision["approvedAt"]).timestamp() * 1000
            if int(message.get("receivedAtMs") or 0) <= approved_ms:
                raise ValueError("Supplier confirmation must be received after the human approval.")
            saved_decision = next(d for d in case["vendorDecisions"] if d["id"] == decision["id"])
            saved_decision.update(
                status="secured", confirmationMessageId=message["id"], confirmedAt=now()
            )
            message.update(
                kind="commitment-confirmation",
                approvalId=decision["id"],
                termsHash=decision["termsHash"],
                quoteInterpretation=data,
                interpretedAt=now(),
            )
            vendor["liaisonStatus"] = "secured"
            log(
                case,
                "Supplier availability confirmed",
                f"{vendor['name']} confirmed the exact approved terms in a later received reply. No payment or purchase was made.",
                "liaison",
            )
            case["events"][-1]["milestone"] = True
            return self.save(case, actor)
        if decision:
            raise ValueError(
                "A supplier decision already exists on these terms; do not overwrite it with another quote."
            )
        message["quoteInterpretation"] = data
        message["interpretedAt"] = now()
        if data["final"]:
            vendor.update(
                {
                    k: data[k]
                    for k in [
                        "quantity",
                        "goodsSen",
                        "deliverySen",
                        "arrival",
                        "specsConfirmed",
                        "validUntil",
                    ]
                }
            )
            vendor.update(
                quoteRef="GMAIL-" + message_id,
                liaisonStatus="ready",
                status="Final quotation received",
                evidenceExcerpt=message["body"][:2000],
            )
            message["kind"] = "final-quote"
            message["termsHash"] = term_token(case, vendor)
            case["stage"] = "decision"
            log(
                case,
                "Supplier quotation ready for review",
                f"{vendor['name']}: a complete quotation was extracted from the saved reply. The organiser makes the final choice.",
                "liaison",
            )
            case["events"][-1]["milestone"] = True
        else:
            vendor["liaisonStatus"] = "needs_terms"
        return self.save(case, actor)
