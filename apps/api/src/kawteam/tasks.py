"""Task naming and evidence-backed, human-controlled supplier placements."""

import copy
import hashlib
import json
import re
from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo


def now():
    return datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).isoformat()


def project_name(message):
    match = re.search(
        r"\b(?:for\s+(?:(?:the|my|our)\s+)?(?:event|project)|(?:event|project)\s+(?:called|named|is))\s+[\"']?([^\n.!?\"']+)",
        message, re.IGNORECASE,
    )
    if match:
        name = re.split(r"\s+(?:with|within|by|under|in|budget|and|that)\b|,", match.group(1), flags=re.IGNORECASE)[0].strip()
        if name:
            return name[:100]
    for pattern, label in [
        (r"\b(?:(?:t[- ]?)?shirts?|shirt printing)\b", "T-shirt Sourcing"),
        (r"\b(?:totes?|bags?)\b", "Merchandise Sourcing"),
        (r"\b(?:catering|caterers?|food)\b", "Catering & Food"),
        (r"\b(?:venues?|halls?)\b", "Venue Sourcing"),
        (r"\b(?:photograph\w*|videograph\w*)\b", "Photography & Video"),
        (r"\b(?:sponsors?|sponsorship)\b", "Sponsorship Outreach"),
        (r"\b(?:scholarships?)\b", "Scholarship Outreach"),
        (r"\b(?:workshops?)\b", "Workshop Planning"),
        (r"\b(?:bazaars?|stallholders?|exhibitors?)\b", "Bazaar & Event Vendors"),
        (r"\b(?:equipment|sound|lighting|speakers)\b", "Event Equipment"),
        (r"\b(?:printing|banners?|posters?)\b", "Print & Production"),
        (r"\b(?:transport|buses?|coaches?)\b", "Event Transport"),
        (r"\b(?:vendors?|suppliers?|businesses|companies)\b", "Supplier Sourcing"),
    ]:
        if re.search(pattern, message, re.IGNORECASE):
            return label
    return "Project Planning"


def task_name(message):
    for pattern, label in [
        (r"\b(?:(?:t-?)?shirts?|shirt printing)\b", "T-shirt merchandise"),
        (r"\b(?:totes?|bags?)\b", "Tote merchandise"),
        (r"\b(?:catering|caterers?|food)\b", "Catering"),
        (r"\b(?:scholarships?)\b", "Scholarship outreach"),
        (r"\b\d+\s+(?:event\s+)?(?:vendors?|stallholders?|exhibitors?)\b", "Event vendors"),
    ]:
        if re.search(pattern, message, re.IGNORECASE):
            return label
    return message.strip().split("\n")[0][:80] or "New task"


def selection_target(message, default=1):
    match = re.search(
        r"\b(\d+)\s+(?:event\s+)?(?:vendors?|stallholders?|exhibitors?|partners?|sponsors?|scholarships?)\b",
        message,
        re.IGNORECASE,
    )
    if not match:
        return default
    target = int(match.group(1))
    if not 1 <= target <= 100:
        raise ValueError("A task can secure between 1 and 100 suppliers or placements.")
    return target


def term_token(c, v):
    fields = {
        k: c.get(k)
        for k in ["quantity", "budgetSen", "deadline", "location", "selectionTarget", "goal"]
    }
    fields["offer"] = {
        k: v.get(k)
        for k in [
            "id",
            "quantity",
            "goodsSen",
            "deliverySen",
            "arrival",
            "specsConfirmed",
            "validUntil",
            "quoteRef",
        ]
    }
    return hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()


def current_decisions(c):
    vendors = {v["id"]: v for v in c.get("vendors", [])}
    decisions = []
    for d in c.get("vendorDecisions", []):
        if d["status"] not in {"approved", "secured", "rejected"} or d["vendorId"] not in vendors:
            continue
        if d.get("termsHash") != term_token(c, vendors[d["vendorId"]]):
            continue
        proof = next(
            (
                m
                for m in c.get("messages", [])
                if m["id"] == d.get("confirmationMessageId")
                and m.get("kind") == "commitment-confirmation"
                and m.get("direction") == "received"
                and m.get("vendorId") == d["vendorId"]
                and m.get("approvalId") == d["id"]
                and m.get("termsHash") == d["termsHash"]
            ),
            None,
        )
        decisions.append(
            {**d, "status": "approved"} if d["status"] == "secured" and not proof else d
        )
    return decisions


def task_queue(c):
    from .contacts import contact_valid
    from .workflow import fit, total

    decisions = {d["vendorId"]: d for d in current_decisions(c)}
    # Older explicit decisions remain approvals, never fabricated confirmations.
    if not c.get("taskWorkflowVersion") and c.get("selectedVendorId"):
        decisions[c["selectedVendorId"]] = {"status": "approved"}
    occupied = [
        v
        for v in c["vendors"]
        if decisions.get(v["id"], {}).get("status") in {"approved", "secured"}
    ]
    remaining_budget = (c.get("budgetSen") or 0) - sum(total(v) or 0 for v in occupied)
    slots = max(0, c.get("selectionTarget", 1) - len(occupied))
    ready, other = [], []
    for v in c["vendors"]:
        decision = decisions.get(v["id"])
        reason = fit(c, v)
        final_reply = any(
            m.get("vendorId") == v["id"]
            and m.get("direction") == "received"
            and m.get("kind") == "final-quote"
            and m.get("termsHash") == term_token(c, v)
            for m in c.get("messages", [])
        )
        row = {"vendorId": v["id"], "termsHash": term_token(c, v), "reason": reason}
        if decision:
            row["status"] = decision["status"]
            other.append(row)
        elif v.get("liaisonStatus") == "ready" and final_reply and reason == "Meets your brief":
            ready.append(row)
        else:
            row["status"] = (
                "needs_terms"
                if v.get("liaisonStatus") == "ready" and reason != "Meets your brief"
                else "liaising"
            )
            sent = any(m.get("vendorId") == v["id"] and m.get("direction") == "sent" for m in c.get("messages", []))
            replied = any(m.get("vendorId") == v["id"] and m.get("direction") == "received" for m in c.get("messages", []))
            row["reason"] = (
                v["outreachBlock"] if v.get("outreachBlock")
                else reason if row["status"] == "needs_terms"
                else "Reply received; final quotation needs validation" if replied
                else "Enquiry sent; awaiting supplier reply" if sent
                else "Contact details need verification; no email sent" if v.get("executionMode") == "live" and not contact_valid(v)
                else "Not contacted yet" if v.get("executionMode") == "live"
                else "Final quotation reply required"
            )
            other.append(row)
    by_id = {v["id"]: v for v in c["vendors"]}
    ready.sort(
        key=lambda r: (
            total(by_id[r["vendorId"]]),
            by_id[r["vendorId"]]["arrival"],
            by_id[r["vendorId"]]["name"],
        )
    )
    for index, row in enumerate(ready):
        row["rank"] = index + 1
        if not slots:
            row["status"] = "not_selected"
        elif total(by_id[row["vendorId"]]) > remaining_budget:
            row.update(status="needs_terms", reason="Above the remaining task budget")
        else:
            row["status"] = "approval_needed" if index < slots else "waitlist"
    return ready + other


def invalidate_terms(c):
    from .projects import fresh_vendor

    for d in c.get("vendorDecisions", []):
        if d["status"] in {"approved", "secured", "rejected"}:
            d["status"] = "superseded"
    c["vendors"] = [fresh_vendor(v) for v in c["vendors"]]
    c["selectedVendorId"] = None
    c["stage"] = "negotiation" if c["vendors"] else "brief"
    c["draft"].update(body="", status="pending", revision=c["draft"]["revision"] + 1)
    for key in ["approvedHash", "approvedUntil", "sentId"]:
        c["draft"].pop(key, None)


def task_transition(original, actor, action):
    from .workflow import log, total

    if actor not in {"organiser", "teammate"}:
        raise PermissionError("This profile is view-only.")
    kind = action["type"]
    if kind != "liaise-task" and actor != "organiser":
        raise PermissionError("Only the organiser can approve or reject a supplier.")
    c = copy.deepcopy(original)
    c.setdefault("selectionTarget", 1)
    c.setdefault("vendorDecisions", [])
    c["taskWorkflowVersion"] = 1
    if kind == "liaise-task":
        if (
            c["id"] != "case-totes"
            or c["quantity"] != 300
            or c["location"] != "Subang Jaya, Selangor"
        ):
            raise ValueError(
                "Controlled liaison is available only for the original tote demo scope."
            )
        if current_decisions(c):
            raise ValueError(
                "This task already has supplier decisions. Continue its existing workflow."
            )
        if any(v.get("executionMode", "demo") != "demo" for v in c["vendors"]):
            raise ValueError("A connected email provider is required for live suppliers.")
        if any(v.get("liaisonStatus") == "ready" for v in c["vendors"]):
            raise ValueError("Controlled liaison has already completed.")
        for v in c["vendors"]:
            if v["id"] == "meridian":
                v.update(deliverySen=21000, arrival="2026-10-23", specsConfirmed=True)
            if v["id"] not in {"campus", "meridian", "willow"}:
                raise ValueError("Unknown controlled supplier.")
            # Two bounded, explicitly simulated rounds across the entire pool.
            for round_number in (1, 2):
                c.setdefault("messages", []).extend(
                    [
                        {
                            "id": str(uuid4()),
                            "vendorId": v["id"],
                            "direction": "sent",
                            "body": f"Non-binding enquiry round {round_number}: {c['quantity']} printed totes, total budget RM{c['budgetSen'] / 100:.2f}, delivery by {c['deadline']}. Please confirm all costs and specifications.",
                            "time": now(),
                            "executionMode": "demo",
                            "replied": True,
                        },
                        {
                            "id": str(uuid4()),
                            "vendorId": v["id"],
                            "direction": "received",
                            "body": f"{'Final quote' if round_number == 2 else 'Initial quote'}: RM{(total(v) or 0) / 100:.2f}, {c['quantity']} totes, delivery by {v['arrival']}. {'Terms ready for your review; your decision is still needed.' if round_number == 2 else 'We are checking the final details.'}",
                            "kind": "final-quote" if round_number == 2 else "quote",
                            "time": now(),
                            "executionMode": "demo",
                        },
                    ]
                )
            v.update(liaisonStatus="ready", quantity=c["quantity"], executionMode="demo")
            c["messages"][-1]["termsHash"] = term_token(c, v)
        c["stage"] = "decision"
        log(
            c,
            f"Contacted {len(c['vendors'])} suppliers",
            "Two controlled liaison rounds completed. Saved quotations are ready for human review; no external email.",
            "mail",
        )
        c["events"][-1]["milestone"] = True
        return c
    row = next((r for r in task_queue(c) if r["vendorId"] == action.get("vendorId")), None)
    v = next((v for v in c["vendors"] if v["id"] == action.get("vendorId")), None)
    if not row or not v:
        raise ValueError("Supplier is not part of this task.")
    if kind in {"approve-vendor", "reject-vendor"}:
        if row["status"] != "approval_needed":
            raise ValueError(
                "This supplier is not in an active approval slot; complete liaison or advance the waitlist first."
            )
        d = {
            "id": str(uuid4()),
            "vendorId": v["id"],
            "status": "approved" if kind == "approve-vendor" else "rejected",
            "termsHash": row["termsHash"],
            "approvedAt": now(),
            "executionMode": v.get("executionMode", "demo"),
        }
        c["vendorDecisions"].append(d)
        c["selectedVendorId"] = (
            v["id"]
            if kind == "approve-vendor" and c["selectionTarget"] == 1
            else c.get("selectedVendorId")
        )
        c["stage"] = (
            "decided"
            if sum(d["status"] in {"approved", "secured"} for d in current_decisions(c))
            >= c["selectionTarget"]
            else "decision"
        )
        log(
            c,
            "Supplier approved" if kind == "approve-vendor" else "Supplier declined",
            f"{v['name']}. "
            + (
                "Awaiting separate supplier confirmation; no order or payment placed."
                if kind == "approve-vendor"
                else "The next suitable waitlisted supplier can now be reviewed. No rejection email was sent."
            ),
        )
    elif kind == "confirm-vendor":
        from .demo_scope import controlled_demo_offer

        if not controlled_demo_offer(c, v):
            raise ValueError(
                "This action only checks a controlled demo confirmation, never live suppliers."
            )
        d = next(
            (
                d
                for d in current_decisions(c)
                if d["vendorId"] == v["id"] and d["status"] == "approved"
            ),
            None,
        )
        if not d:
            raise ValueError("A current approved supplier is required before confirmation.")
        message = {
            "id": str(uuid4()),
            "vendorId": v["id"],
            "direction": "received",
            "kind": "commitment-confirmation",
            "approvalId": d["id"],
            "termsHash": d["termsHash"],
            "body": f"Controlled demo: {v['name']} confirms availability on the exact approved quotation terms. No real order or contract exists.",
            "time": now(),
            "executionMode": "demo",
        }
        c.setdefault("messages", []).append(message)
        d.update(status="secured", confirmedAt=message["time"], confirmationMessageId=message["id"])
        log(c, "Supplier secured in demo", message["body"], "offer")
    else:
        raise ValueError("Unknown task action.")
    c["events"][-1]["milestone"] = True
    return c
