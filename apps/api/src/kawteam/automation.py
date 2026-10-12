"""Bounded, resumable supplier steps. No supplier selection or order confirmation."""

from datetime import datetime, timedelta
from uuid import uuid4

import httpx

from .contacts import contact_valid
from .enquiries import enquiry_body
from .failsafes import open_failsafe, refresh_context_failsafes, resolve_failsafe
from .liaison import request_token
from .providers import supplier_priority
from .repository import payload_hash
from .tasks import current_decisions, now
from .workflow import fit, log


class Automation:
    def __init__(self, liaison, resolver, interpreter, researcher=None):
        self.liaison, self.resolver, self.interpreter = liaison, resolver, interpreter
        self.researcher = researcher

    def persist(self, case, actor, title=None, detail=None):
        refresh_context_failsafes(
            case,
            require_final=any(v.get("liaisonStatus") == "ready" for v in case.get("vendors", [])),
        )
        if title:
            log(case, title, detail, "liaison")
            case["events"][-1]["milestone"] = True
        return self.liaison.save(case, actor)

    def tick(self, case_id, actor):
        case = self.liaison.case(case_id, actor=actor)
        automation = case.get("automation", {})
        if automation.get("authorisedBy") not in {"organiser", "teammate"}:
            raise ValueError("Task outreach has not been authorised through chat.")
        scope = request_token(case)
        if automation.get("requestHash") != scope:
            raise ValueError("Task requirements changed; a new outreach request is required.")
        if automation.get("status") == "paused":
            raise ValueError("Task outreach is paused by the user.")
        instant = datetime.fromisoformat(now())
        if (
            automation.get("leaseUntil")
            and datetime.fromisoformat(automation["leaseUntil"]) > instant
        ):
            return case
        lease_id = str(uuid4())
        automation.update(
            lastTickAt=now(),
            leaseId=lease_id,
            leaseUntil=(instant + timedelta(seconds=180)).isoformat(),
        )
        case = self.persist(case, actor)  # CAS before a potentially external step.
        try:
            self.step(case, actor)
        finally:
            current = self.liaison.case(case_id, actor=actor)
            if current.get("automation", {}).get("leaseId") == lease_id:
                current["automation"].pop("leaseId", None)
                current["automation"].pop("leaseUntil", None)
                try:
                    self.persist(current, actor)
                except ValueError:
                    pass  # Another edit owns the latest revision; expired leases are resumable.
        return self.liaison.case(case_id, actor=actor)

    def step(self, case, actor):
        case_id, scope = case["id"], request_token(case)
        sender = self.liaison.mail.profile()["sender"]
        decisions = {d["vendorId"]: d["status"] for d in current_decisions(case)}
        target_filled = sum(
            status in {"approved", "secured"} for status in decisions.values()
        ) >= case.get("selectionTarget", 1)
        for vendor in sorted(case['vendors'], key=lambda v: supplier_priority(v, case), reverse=True):
            approved = decisions.get(vendor["id"]) == "approved"
            if (
                vendor.get("executionMode") != "live"
                or decisions.get(vendor["id"]) in {"rejected", "secured"}
                or vendor.get("outreachBlock")
                or (target_filled and not approved)
                or (
                    vendor.get("liaisonStatus") == "ready"
                    and fit(case, vendor) == "Meets your brief"
                    and not approved
                )
            ):
                continue
            intents = [
                i
                for i in case.get("emailIntents", [])
                if i["vendorId"] == vendor["id"] and i.get("gmailSender") == sender
            ]
            if any(i["status"] != "sent" for i in intents):
                vendor["outreachBlock"] = "Email outcome needs reconciliation; no automatic resend."
                return self.persist(case, actor)
            current_intents = [i for i in intents if i.get("requestHash") == scope]
            try:
                if not contact_valid(vendor) or (
                    vendor.get("contact", {}).get("verifiedBy") == "public_source"
                    and vendor["contact"].get("requestHash") != scope
                ):
                    contact = self.resolver(vendor, case)
                    if contact:
                        contact["requestHash"] = scope
                        vendor["contact"] = contact
                    if not contact_valid(vendor):
                        vendor["outreachBlock"] = (
                            "No unambiguous public business contact and relevant service evidence found."
                        )
                        return self.persist(
                            case,
                            actor,
                            "Supplier contact unavailable",
                            f"{vendor['name']}: no enquiry sent; contact or service evidence is missing.",
                        )
                    case = self.persist(
                        case,
                        actor,
                        "Supplier contact verified",
                        f"A source-backed enquiry address was found for {vendor['name']}.",
                    )
                    vendor = self.liaison.vendor(case, vendor["id"])
                    if current_intents or approved or any(
                        m.get('vendorId') == vendor['id'] and m.get('direction') == 'received'
                        and m.get('gmailSender') == sender and m.get('requestHash') == scope
                        for m in case['messages']
                    ):
                        return case
                replies = [
                    m
                    for m in case["messages"]
                    if m.get("vendorId") == vendor["id"]
                    and m.get("direction") == "received"
                    and m.get("gmailSender") == sender
                    and m.get("requestHash") == scope
                ]
                if not current_intents and not approved and not replies:
                    return self.send(case, vendor, actor, "initial")
                latest = (
                    max(replies, key=lambda m: int(m.get("receivedAtMs") or 0)) if replies else None
                )
                if latest and not latest.get("quoteInterpretation"):
                    return self.liaison.quote(
                        case_id,
                        vendor["id"],
                        latest["providerMessageId"],
                        case["backendRevision"],
                        actor,
                        self.interpreter,
                    )
                if (
                    latest
                    and not approved
                    and (
                        not case.get("quantity")
                        or (
                            latest["quoteInterpretation"].get("final")
                            and (not case.get("budgetSen") or not case.get("location"))
                        )
                    )
                ):
                    # Unknown user facts cannot be recovered by repeatedly asking the supplier.
                    refresh_context_failsafes(
                        case, require_final=bool(latest["quoteInterpretation"].get("final"))
                    )
                    continue
                if (
                    latest
                    and not approved
                    and latest["quoteInterpretation"].get("final")
                    and fit(case, vendor) != "Meets your brief"
                ):
                    step = "revision-" + latest["providerMessageId"]
                    if not any(
                        i["id"] == self.send_key(case, vendor, sender, step) for i in intents
                    ):
                        return self.send(case, vendor, actor, step)
                if (
                    latest
                    and not approved
                    and not latest["quoteInterpretation"].get("final")
                    and not latest["quoteInterpretation"].get("confirmation")
                ):
                    key = self.send_key(case, vendor, sender, latest["providerMessageId"])
                    if not any(i["id"] == key for i in intents):
                        return self.send(case, vendor, actor, latest["providerMessageId"])
            except (ValueError, RuntimeError, httpx.HTTPError, OSError) as error:
                # Reload after a send reservation or provider failure; never overwrite a receipt.
                current = self.liaison.case(case_id, actor=actor)
                if (
                    request_token(current) != scope
                    or (isinstance(error, ValueError) and "Stale" in str(error))
                    or current.get("automation", {}).get("status") == "paused"
                ):
                    return current
                saved = self.liaison.vendor(current, vendor["id"])
                saved["outreachBlock"] = (
                    str(error)[:500]
                    if isinstance(error, ValueError)
                    else "Supplier step unavailable; saved communication is retained."
                )
                return self.persist(
                    current,
                    actor,
                    "Supplier outreach needs attention",
                    f"{vendor['name']}: {saved['outreachBlock']}",
                )
        if any(
            i.get("gmailSender") == sender
            and i.get("requestHash") == scope
            and i["status"] == "sent"
            for i in case.get("emailIntents", [])
        ):
            case = self.liaison.sync(case_id, case["backendRevision"], actor)
        active = [
            v
            for v in case["vendors"]
            if v.get("executionMode") == "live"
            and decisions.get(v["id"]) not in {"rejected", "secured"}
            and (not target_filled or decisions.get(v["id"]) == "approved")
        ]
        exhausted = not active or all(v.get("outreachBlock") for v in active)
        if (
            exhausted
            and not target_filled
            and case.get("workflowMode") != "liaise"
            and self.researcher
            and case["automation"].get("discoveryRounds", 0) < 2
        ):
            case["automation"]["discoveryRounds"] = case["automation"].get("discoveryRounds", 0) + 1
            candidates = self.researcher(case)
            known = {
                v.get("sourceUrl", "").split("/")[2].lower().removeprefix("www.")
                for v in case["vendors"]
                if v.get("sourceUrl", "").startswith(("https://", "http://"))
            }
            fresh = []
            for v in candidates:
                host = (
                    v.get("sourceUrl", "").split("/")[2].lower().removeprefix("www.")
                    if v.get("sourceUrl", "").startswith(("https://", "http://"))
                    else None
                )
                if host and host not in known:
                    known.add(host)
                    fresh.append(v)
            case["vendors"].extend(fresh)
            case["outreachVendorIds"] = [v["id"] for v in case["vendors"]]
            case["shortlistVendorIds"] = list(case["outreachVendorIds"])
            case["automation"]["status"] = "queued"
            resolve_failsafe(case, "outreach_exhausted")
            return self.persist(
                case,
                actor,
                "Supplier search expanded",
                f"Found {len(fresh)} additional supplier sources after unavailable contacts. Contact verification continues; these sources have not been emailed yet.",
            )
        status = (
            "awaiting_replies"
            if any(
                decisions.get(v["id"]) == "approved"
                or (not v.get("outreachBlock") and v.get("liaisonStatus") != "ready")
                for v in active
            )
            else "review_ready"
            if any(v.get("liaisonStatus") == "ready" for v in active)
            else "needs_attention"
        )
        if not case["vendors"]:
            open_failsafe(
                case,
                "research_unavailable",
                "No supplier source is available yet",
                "Add a known business or refine the request to continue sourcing.",
                [],
            )
        elif active and all(v.get("outreachBlock") for v in active):
            open_failsafe(
                case,
                "outreach_exhausted",
                "No supplier can proceed yet",
                "All available supplier routes need attention. Check the task details or provide a verified business contact.",
                [],
            )
        else:
            resolve_failsafe(case, "outreach_exhausted")
        if case["automation"].get("status") != status:
            case["automation"]["status"] = status
            return self.persist(case, actor)
        return case

    @staticmethod
    def send_key(case, vendor, sender, step):
        return (
            "auto-"
            + payload_hash(
                {
                    "caseId": case["id"],
                    "vendorId": vendor["id"],
                    "requestHash": request_token(case),
                    "sender": sender,
                    "step": step,
                }
            )[:48]
        )

    def send(self, case, vendor, actor, step):
        sender = self.liaison.mail.profile()["sender"]
        body = enquiry_body(case, clarification=step != "initial")
        return self.liaison.send(
            case["id"],
            vendor["id"],
            ("Quotation enquiry: " + case["title"])[:200].replace("\n", " ").replace("\r", " "),
            body,
            case["backendRevision"],
            self.send_key(case, vendor, sender, step),
            actor,
        )
