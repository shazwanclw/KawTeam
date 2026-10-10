"""Enquiries built from known user facts; unknown quantities and addresses are omitted."""


def enquiry_body(case, clarification=False):
    facts = []
    if case.get("quantity"):
        facts.append(f"Quantity: {case['quantity']}.")
    else:
        facts.append("Please share your minimum order quantity and pricing tiers; the final quantity is still being determined.")
    if case.get("budgetSen"):
        facts.append(f"Total budget ceiling: RM{case['budgetSen'] / 100:.2f}, including delivery.")
    elif case.get("unitBudgetSen"):
        facts.append(f"Item price ceiling: RM{case['unitBudgetSen'] / 100:.2f} per item.")
    if case.get("location"):
        facts.append(f"{'Fulfilment' if case['location'].startswith('Collection from supplier') else 'Delivery to'}: {case['location']}.")
    if case.get("deadline"):
        assumed = "deadline" in case.get("assumptions", [])
        facts.append(f"{'Preferred arrival' if assumed else 'Required arrival no later than'} {case['deadline']}{' (provisional date; please advise your lead time)' if assumed else ''}.")
    body = f"Hello,\n\nPlease share a non-binding quotation for this request:\n{case['goal']}\n\n" + "\n".join(facts)
    body += "\n\nPlease include the item specifications, quantity or pricing tiers, goods cost in RM, delivery charges separately where available (or confirm collection), estimated arrival/lead time, and quotation validity. Please use YYYY-MM-DD for dates. This is an enquiry, not an order.\n\nThank you,\nKawTeam"
    if clarification:
        body = "Thank you for your reply. Please clarify the outstanding details and restate the updated quotation terms below.\n\n" + body
    return body
