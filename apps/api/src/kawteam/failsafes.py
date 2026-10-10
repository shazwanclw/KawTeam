"""Durable last-resort attention records, separate from normal supplier waits."""

from uuid import NAMESPACE_URL, uuid5

from .tasks import now


def open_failsafe(case, code, title, detail, required_fields=None):
    records = case.setdefault("failsafes", [])
    existing = next((f for f in records if f["code"] == code and f["status"] == "open"), None)
    if existing:
        return existing
    record = {"id": str(uuid5(NAMESPACE_URL, f"{case['id']}:{code}:{len(records)}")), "code": code, "title": title, "detail": detail, "requiredFields": required_fields or [], "status": "open", "createdAt": now()}
    records.append(record)
    return record


def resolve_failsafe(case, code):
    for record in case.get("failsafes", []):
        if record["code"] == code and record["status"] == "open":
            record.update(status="resolved", resolvedAt=now())


def refresh_context_failsafes(case, require_final=False):
    if not case.get("quantity"):
        open_failsafe(case, "quantity", "How many items do you need?", "I'm asking suppliers for pricing tiers in the meantime. The final quantity is needed before a specific offer can be compared or selected.", ["quantity"])
    else:
        resolve_failsafe(case, "quantity")
    for field, title, detail in [
        ("budgetSen", "Set the spending limit", "Supplier pricing is available. Add a budget so I can check which offers fit your spending limit."),
        ("location", "Confirm delivery or collection", "The final offer needs a delivery destination or a collection arrangement. Enquiries can continue without a street address."),
    ]:
        if case.get(field):
            resolve_failsafe(case, field)
        elif require_final:
            open_failsafe(case, field, title, detail, [field])
    if case.get("vendors"):
        resolve_failsafe(case, "vendor_identity")
