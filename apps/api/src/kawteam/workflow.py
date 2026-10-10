"""Deterministic procurement services. AI/WorkBuddy execution is deliberately deferred."""

import copy
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from .tasks import task_transition


def seed():
    return json.loads(Path(__file__).with_name("seed.json").read_text(encoding="utf-8"))


def total(v):
    if v["deliverySen"] is None:
        return None
    return v["goodsSen"] + v["deliverySen"]


def fit(c, v):
    if v.get("quantity", 300) != c["quantity"]:
        return "Quantity mismatch"
    if v.get("executionMode", "demo") == "demo" and c["id"] != "case-totes":
        return "Sample quote for a different case"
    if total(v) is None or v["arrival"] is None:
        return "Missing terms"
    if total(v) > c["budgetSen"]:
        return "Above budget"
    if v["arrival"] > c["deadline"]:
        return "Arrives too late"
    if not v["specsConfirmed"]:
        return "Specifications unconfirmed"
    if (
        v.get("validUntil")
        and v["validUntil"] < datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date().isoformat()
    ):
        return "Quote expired"
    return "Meets your brief"


def digest(draft):
    fields = {k: draft.get(k) for k in ["recipient", "subject", "body", "revision", "vendorId"]}
    return hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()


def log(c, title, detail, kind="human"):
    now = datetime.now(ZoneInfo("Asia/Kuala_Lumpur"))
    c["events"].append(
        {
            "id": str(uuid4()),
            "title": title,
            "detail": detail,
            "time": now.strftime("%H:%M"),
            "occurredAt": now.isoformat(),
            "kind": kind,
        }
    )


def transition(original, actor, action):
    kind = action["type"]
    if kind in {'liaise-task', 'approve-vendor', 'reject-vendor', 'confirm-vendor'}:
        return task_transition(original, actor, action)
    if original.get('taskWorkflowVersion') and kind == 'choose':
        raise ValueError('Use the ranked task approval queue for this request.')
    if actor not in {"organiser", "teammate", "observer"} or actor == "observer":
        raise PermissionError("This profile is view-only.")
    if kind in {"choose", "approve", "reject", "send"} and actor != "organiser":
        raise PermissionError(
            "Only the organiser can approve, send or make the final vendor decision."
        )
    c = copy.deepcopy(original)
    d = c["draft"]
    if kind == "research":
        if c["id"] != "case-totes":
            raise ValueError(
                "Live search needs a configured provider. Sample tote offers cannot be used here."
            )
        if not c["vendors"]:
            c["vendors"] = seed()["cases"][0]["vendors"]
        c["stage"] = "decided" if c["selectedVendorId"] else "decision"
        log(
            c,
            "Sample comparison refreshed",
            "Controlled vendor data; no AI, live search or external email.",
            "research",
        )
    elif kind == "choose":
        v = next((v for v in c["vendors"] if v["id"] == action.get("vendorId")), None)
        if not v or fit(c, v) != "Meets your brief":
            raise ValueError(
                "This offer does not meet confirmed quantity, budget, specifications and delivery requirements."
            )
        c["selectedVendorId"] = v["id"]
        c["stage"] = "decided"
        log(
            c,
            "Your team made the decision",
            f"Organiser chose {v['name']}. No purchase, email or agreement issued.",
        )
    elif kind == "edit-draft":
        body = action.get("body", "").strip()
        if not body or len(body) > 10000:
            raise ValueError("Message must contain 1–10,000 characters.")
        d["body"] = body
        d["revision"] += 1
        d["status"] = "pending"
        for key in ["approvedHash", "approvedUntil", "sentId"]:
            d.pop(key, None)
        log(c, "Draft updated", "Previous approval invalidated; organiser review required.")
    elif kind in {"approve", "reject"}:
        if not d["body"].strip():
            raise ValueError("Prepare a message first.")
        if d.get("sentId"):
            raise ValueError("This exact draft has already been sent. Prepare a new draft.")
        d["status"] = "approved" if kind == "approve" else "rejected"
        d["approvedHash"] = digest(d) if kind == "approve" else None
        d["approvedUntil"] = int(time.time()) + 1800 if kind == "approve" else 0
        log(
            c,
            "Message approved" if kind == "approve" else "Message returned for revision",
            f"Exact draft revision {d['revision']}; no message sent yet.",
        )
    elif kind == "prepare":
        if c["id"] != "case-totes" or c["quantity"] != 300:
            raise ValueError(
                "Controlled supplier outreach is available only for the 300-tote sample."
            )
        vendor_id = action.get("vendorId", "willow")
        v = next((v for v in c["vendors"] if v["id"] == vendor_id), None)
        if not v or v.get("executionMode", "demo") != "demo":
            raise ValueError("Unknown controlled supplier.")
        if (
            sum(
                m.get("vendorId") == vendor_id and m["direction"] == "sent"
                for m in c.get("messages", [])
            )
            >= 3
        ):
            raise ValueError("Three-round limit reached for this supplier.")
        proposed = c["targetSen"] / 100
        c["draft"] = {
            "recipient": f"{vendor_id}@supplier.invalid",
            "subject": f"Quotation enquiry: {c['title']}",
            "body": f"Hello {v['name']},\n\nWe need {c['quantity']} cotton tote bags with one-colour printing, delivered to {c['location']} by {c['deadline']}. Can you offer an all-in price near RM{proposed:,.2f}, within our RM{c['budgetSen'] / 100:,.2f} ceiling? Please confirm quantity, printing, delivery, charges and quote validity.\n\nThis is a non-binding enquiry. Our team makes the final supplier decision.",
            "vendorId": vendor_id,
            "revision": d["revision"] + 1,
            "status": "pending",
        }
        log(
            c,
            "Counteroffer prepared",
            f"{v['name']}; exact message awaits organiser approval.",
            "mail",
        )
    elif kind == "send":
        if d.get("sentId"):
            raise ValueError("This draft has already been sent.")
        if (
            d["status"] != "approved"
            or d.get("approvedHash") != digest(d)
            or d.get("approvedUntil", 0) <= time.time()
        ):
            raise ValueError("Valid exact-message approval is required before sending.")
        if c["id"] != "case-totes" or c["quantity"] != 300:
            raise ValueError("No live email provider is connected. Controlled tote case only.")
        vendor_id = d.get("vendorId", "willow")
        if vendor_id not in {"campus", "meridian", "willow"}:
            raise ValueError("Recipient is not a controlled supplier.")
        d["sentId"] = str(uuid4())
        d["status"] = "sent"
        c.setdefault("messages", []).append(
            {
                "id": d["sentId"],
                "vendorId": vendor_id,
                "direction": "sent",
                "body": d["body"],
                "subject": d["subject"],
                "revision": d["revision"],
                "time": datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).isoformat(),
                "executionMode": "demo",
            }
        )
        c["stage"] = "decided" if c["selectedVendorId"] else "negotiation"
        log(
            c,
            "Message sent to controlled supplier",
            "Persisted demo outbox only; no external email.",
            "mail",
        )
    elif kind == "sync":
        sent = next(
            (
                m
                for m in reversed(c.get("messages", []))
                if m["direction"] == "sent" and not m.get("replied")
            ),
            None,
        )
        if not sent:
            raise ValueError("No pending controlled reply. Send an approved draft first.")
        sent["replied"] = True
        v = next(v for v in c["vendors"] if v["id"] == sent["vendorId"])
        price = {"campus": 155000, "meridian": 155000, "willow": 145000}[v["id"]]
        if v["id"] == "meridian":
            v["deliverySen"] = 21000
            v["arrival"] = "2026-10-23"
        else:
            v["goodsSen"] = price - v["deliverySen"]
        v.update(quantity=300, validUntil="2026-10-15", executionMode="demo")
        body = f"Our final all-in quote is RM{price / 100:,.2f} for 300 cotton totes with one-colour printing and delivery to Subang Jaya by {v['arrival']}. Valid until 15 October; artwork approval is still required."
        if price > c["budgetSen"]:
            body += " We cannot meet your budget; please consider another supplier."
        c["messages"].append(
            {
                "id": str(uuid4()),
                "vendorId": v["id"],
                "direction": "received",
                "body": body,
                "time": datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).isoformat(),
                "executionMode": "demo",
                "quoteRef": v["quoteRef"],
            }
        )
        c["stage"] = "decided" if c["selectedVendorId"] else "decision"
        log(
            c,
            "Controlled supplier reply received",
            f"{v['name']}: RM{price / 100:,.2f}. Final choice remains with your team.",
            "offer",
        )
        if price > c["budgetSen"]:
            log(
                c,
                "Backup supplier needed",
                "Current quote remains over budget; compare or prepare another supplier enquiry.",
                "research",
            )
    else:
        raise ValueError("Unknown action.")
    return c


def outcome(c):
    ranked = sorted(
        (v for v in c["vendors"] if fit(c, v) == "Meets your brief"),
        key=lambda v: (total(v), v["id"]),
    )
    recommended = ranked[0] if ranked else None
    pending = any(m["direction"] == "sent" and not m.get("replied") for m in c.get("messages", []))
    status = (
        "awaiting_supplier_reply"
        if pending
        else "verified_offer_ready_for_review"
        if recommended
        else "conditional_offer"
        if any(total(v) is None for v in c["vendors"])
        else "no_qualifying_offer"
    )
    savings = None
    if (
        recommended
        and recommended.get("executionMode", "demo") == "demo"
        and c["id"] == "case-totes"
        and c["quantity"] == 300
        and recommended["initialSen"] > 0
    ):
        savings = max(0, recommended["initialSen"] - total(recommended))
    return {
        "caseId": c["id"],
        "title": c["title"],
        "goal": c["goal"],
        "quantity": c["quantity"],
        "budgetSen": c["budgetSen"],
        "deadline": c["deadline"],
        "location": c["location"],
        "status": status,
        "recommendedVendorId": recommended["id"] if recommended else None,
        "selectedVendorId": c["selectedVendorId"],
        "potentialSavingsSen": savings,
        "savingsPercent": round(savings / recommended["initialSen"] * 100, 1)
        if savings is not None
        else None,
        "savingsLabel": "Simulated potential savings" if savings is not None else None,
        "candidates": [
            {
                "id": v["id"],
                "name": v["name"],
                "totalSen": total(v),
                "fit": fit(c, v),
                "arrival": v["arrival"],
                "quoteRef": v["quoteRef"],
                "executionMode": v.get("executionMode", "demo"),
                "sourceUrl": v.get("sourceUrl"),
                "conditions": v["concerns"],
            }
            for v in c["vendors"]
        ],
        "messages": c.get("messages", []),
        "events": c["events"],
        "draftStatus": c["draft"]["status"],
        "generatedAt": datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).isoformat(),
        "caveats": [
            "Recommendation is for team review; no order or agreement exists.",
            "Controlled sample quotes are fictional; public search results are not confirmed quotes.",
            "WorkBuddy execution is deferred. No external email transport is connected.",
        ],
    }
