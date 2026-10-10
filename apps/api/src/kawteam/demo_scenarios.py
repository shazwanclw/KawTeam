"""Offline, explicitly simulated presentation records. Never calls a provider."""

import argparse
import base64
import json
from pathlib import Path

from .tasks import term_token


def stamp(day, hour=10, minute=0):
    return f"2026-10-{day:02d}T{hour:02d}:{minute:02d}:00+08:00"


def build_demo():
    snapshot = {"version": 2, "events": [], "cases": [], "threads": [], "documents": []}

    def project(id, name, date, facts, context):
        event = {
            "id": id,
            "name": name,
            "sample": True,
            "demoScenarioVersion": 1,
            "createdAt": stamp(1),
            "memoryVersion": 1,
            "tasks": [],
            "facts": {"eventDate": date, **facts},
        }
        snapshot["events"].append(event)
        text = (
            f"# {name}\n\nSIMULATED PRESENTATION CONTEXT — no real booking or email.\n\n{context}"
        )
        snapshot["documents"].append(
            {
                "id": f"demo-{id}-brief",
                "eventId": id,
                "name": f"{name} — demo brief.md",
                "text": text,
                "originalBase64": base64.b64encode(text.encode()).decode(),
                "mime": "text/markdown",
                "size": len(text.encode()),
                "characters": len(text),
                "status": "ready",
                "sample": True,
                "createdAt": stamp(1),
                "scope": "project",
            }
        )
        return event

    def case(project, id, title, goal, quantity, budget, deadline, location, target=1, day=9):
        task = {"id": id, "name": title, "createdAt": stamp(day, 9)}
        project["tasks"].append(task)
        c = {
            "id": id,
            "eventId": project["id"],
            "taskId": id,
            "title": title,
            "goal": goal,
            "quantity": quantity,
            "budgetSen": budget,
            "targetSen": budget,
            "deadline": deadline,
            "location": location,
            "selectionTarget": target,
            "stage": "decision",
            "selectedVendorId": None,
            "taskWorkflowVersion": 1,
            "sample": True,
            "demoScenarioVersion": 1,
            "vendors": [],
            "messages": [],
            "vendorDecisions": [],
            "events": [],
            "failsafes": [],
            "assumptions": [],
            "draft": {
                "recipient": "Simulated suppliers only",
                "subject": title,
                "body": "",
                "status": "pending",
                "revision": 1,
            },
        }
        snapshot["cases"].append(c)
        thread = {
            "id": f"event-{project['id']}-task-{id}",
            "eventId": project["id"],
            "taskId": id,
            "messages": [
                {
                    "id": f"{id}-user",
                    "role": "user",
                    "body": goal,
                    "time": stamp(day, 9),
                    "caseId": id,
                }
            ],
        }
        snapshot["threads"].append(thread)
        return c, thread

    def milestone(c, title, detail, day, hour, kind="offer"):
        c["events"].append(
            {
                "id": f"{c['id']}-milestone-{len(c['events'])}",
                "title": title,
                "detail": detail,
                "time": f"{hour:02d}:00",
                "occurredAt": stamp(day, hour),
                "kind": kind,
                "milestone": True,
            }
        )

    def vendor(c, slug, name, goods, delivery, arrival, detail, day=9, decision=None):
        v = {
            "id": slug,
            "name": name,
            "initials": "".join(x[0] for x in name.split()[:2]),
            "location": c["location"],
            "color": "sage",
            "goodsSen": goods,
            "deliverySen": delivery,
            "initialSen": goods + delivery + 15000,
            "arrival": arrival,
            "quantity": c["quantity"],
            "specsConfirmed": True,
            "validUntil": "2026-10-20",
            "status": "Final offer",
            "description": detail,
            "strengths": ["Complete final terms received", "Within the requested delivery window"],
            "concerns": ["Written artwork or setup confirmation required before fulfilment"],
            "quoteRef": f"DEMO-{slug.upper()}-FINAL",
            "executionMode": "demo",
            "sample": True,
            "scenarioCaseId": c["id"],
            "liaisonStatus": "ready",
            "contact": {"email": f"{slug}@vendors.example", "provenance": "simulated"},
        }
        c["vendors"].append(v)
        if c["id"] == "demo-market-vendors":
            scope = f"one exhibitor placement within our ten-exhibitor event, setup by {c['deadline']} at {c['location']}; quote your individual support cost within the event's RM{c['budgetSen'] / 100:,.2f} aggregate support ceiling"
        elif c["id"] == "demo-shirts":
            scope = f"50 black cotton T-shirts with a white one-colour logo, all-in ceiling RM{c['budgetSen'] / 100:,.2f}, delivery by {c['deadline']} at {c['location']}"
        else:
            scope = f"{c['quantity']} {'additional ' if c['id'] == 'demo-workshop-extra-lunch' else ''}vegetarian lunch packs with no nuts, ingredient labels and cutlery, all-in ceiling RM{c['budgetSen'] / 100:,.2f}, delivery 11:30 on {c['deadline']} at {c['location']}"
        final = f"Final quotation {v['quoteRef']}: RM{goods / 100:,.2f} plus RM{delivery / 100:,.2f} logistics; RM{(goods + delivery) / 100:,.2f} total. Scope: {scope}. Arrival {arrival}. {detail} Valid until 20 October 2026. Awaiting your team's final selection."
        rounds = [
            (
                "sent",
                "enquiry",
                f"Hello {name}, please quote for {scope}. Include all costs, availability and specifications. This is a non-binding enquiry.",
            ),
            (
                "received",
                "quote",
                f"Thank you. Our initial estimate is RM{v['initialSen'] / 100:,.2f}. {detail} We can meet the date; please confirm your artwork or setup requirements.",
            ),
            (
                "sent",
                "negotiation",
                "Please confirm a final all-in price, exact scope and arrival date. Can you reduce the cost while retaining the specification? We are comparing complete offers; this is not an order.",
            ),
            ("received", "final-quote", final),
        ]
        for index, (direction, kind, body) in enumerate(rounds):
            message = {
                "id": f"{c['id']}-{slug}-{index}",
                "vendorId": slug,
                "direction": direction,
                "kind": kind,
                "subject": f"Re: {c['title']} — quotation enquiry",
                "body": body,
                "at": stamp(day, 10 + index, len(c["vendors"]) % 50),
                "executionMode": "demo",
                "sample": True,
            }
            if kind == "final-quote":
                message["termsHash"] = term_token(c, v)
            c["messages"].append(message)
        if decision:
            d = {
                "id": f"demo-decision-{c['id']}-{slug}",
                "vendorId": slug,
                "status": decision,
                "termsHash": term_token(c, v),
                "approvedAt": stamp(day, 14),
                "executionMode": "demo",
                "actor": "organiser",
            }
            c["vendorDecisions"].append(d)
            c["messages"].append(
                {
                    "id": f"{c['id']}-{slug}-selection",
                    "vendorId": slug,
                    "direction": "sent",
                    "kind": "selection-confirmation-request",
                    "approvalId": d["id"],
                    "termsHash": d["termsHash"],
                    "subject": f"Re: {c['title']} — organiser selection",
                    "body": f"Simulated organiser selection: our team reviewed and approved quotation {v['quoteRef']} at RM{(goods + delivery) / 100:,.2f} all-in. Please separately confirm the exact quoted scope and arrival {arrival}. This is a presentation-only message; no real order, payment or booking is being sent.",
                    "at": stamp(day, 14, 5),
                    "executionMode": "demo",
                    "sample": True,
                }
            )
            if decision in {"secured", "approved"} and c["selectionTarget"] == 1:
                c["selectedVendorId"] = slug
            if decision == "secured":
                confirmation = {
                    "id": f"{c['id']}-{slug}-confirmation",
                    "vendorId": slug,
                    "direction": "received",
                    "kind": "commitment-confirmation",
                    "approvalId": d["id"],
                    "termsHash": d["termsHash"],
                    "subject": f"Re: {c['title']} — confirmation",
                    "body": f"Simulated confirmation: {name} confirms the exact approved scope, RM{(goods + delivery) / 100:,.2f} all-in, arrival {arrival}. No real booking or payment exists.",
                    "at": stamp(day, 15),
                    "executionMode": "demo",
                    "sample": True,
                }
                c["messages"].append(confirmation)
                d.update(confirmedAt=confirmation["at"], confirmationMessageId=confirmation["id"])
        return v

    def answer(thread, body, day=10):
        thread["messages"].append(
            {
                "id": f"{thread['taskId']}-assistant-{len(thread['messages'])}",
                "role": "assistant",
                "body": body,
                "time": stamp(day, 16),
                "provider": "controlled_demo",
                "caseId": thread["taskId"],
                "inReplyTo": thread["messages"][0]["id"],
            }
        )

    merch = project(
        "sunway-got-talent",
        "Sunway Got Talent",
        "2026-10-30",
        {"location": "Bandar Sunway, Selangor", "attendees": 250, "budgetSen": 200000},
        "Student talent showcase, 250 attendees, 30 October. Merch task: 50 black cotton T-shirts, one-colour white logo, sizes XS–XXL, RM2,000 including delivery by 24 October. Organiser reviews the artwork proof. Prioritise reliable delivery, then landed cost.",
    )
    c, t = case(
        merch,
        "demo-shirts",
        "T-shirt merchandise",
        "Find 50 black cotton T-shirts with our white event logo for Sunway Got Talent. Budget RM2,000 including delivery to Bandar Sunway by 24 October. Liaise with every suitable supplier and compare final terms.",
        50,
        200000,
        "2026-10-24",
        "Bandar Sunway, Selangor",
    )
    for row in [
        ("threadcraft", "Threadcraft Studio", 165000, 5000, "2026-10-22"),
        ("inkloom", "Inkloom Apparel", 175000, 5000, "2026-10-23"),
        ("campus-stitch", "Campus Stitch Co", 182000, 0, "2026-10-22"),
        ("cottonlane", "Cottonlane Print", 185000, 5000, "2026-10-24"),
        ("formwear", "Formwear Collective", 192000, 5000, "2026-10-23"),
    ]:
        vendor(
            c,
            *row,
            "180 gsm black cotton, white one-colour screen print; digital artwork proof and size split included.",
        )
    milestone(
        c,
        "Contacted 5 suppliers",
        "Simulated non-binding enquiries and two-way negotiations completed with all five suitable studios.",
        9,
        10,
        "mail",
    )
    milestone(
        c,
        "Five final offers compared",
        "Threadcraft's RM1,700 all-in offer ranks first; four valid alternatives remain on the waitlist. Savings against its opening quote: RM150.",
        10,
        13,
    )
    milestone(
        c,
        "T-shirt supplier ready for review",
        "One organiser approval slot is open; no supplier has been selected or secured.",
        10,
        14,
        "human",
    )
    answer(
        t,
        "I compared complete replies from five studios. Threadcraft is the best fit at RM1,700 including printing and delivery on 22 October. The other four offers are saved as alternatives, with the full liaison history beside each supplier. This presentation scenario uses simulated messages only.",
    )

    bazaar = project(
        "kampus-weekend-market",
        "Kampus Weekend Market",
        "2026-10-31",
        {"location": "Subang Jaya, Selangor", "attendees": 600, "budgetSen": 500000},
        "Student market on 31 October, 10 exhibitor placements, RM5,000 total exhibitor support ceiling. Setup complete by 30 October. Campus supplies tables and power; exhibitors provide products, signage and required licences. Avoid duplicate categories. All replies are simulated.",
    )
    c, t = case(
        bazaar,
        "demo-market-vendors",
        "Ten event vendors",
        "Find 10 suitable event vendors for Kampus Weekend Market, within RM5,000 total support. Confirm their setup at Subang Jaya by 30 October, product categories and any support costs. We will select the exhibitors ourselves.",
        1,
        500000,
        "2026-10-30",
        "Subang Jaya, Selangor",
        10,
    )
    categories = [
        ("daily-brew", "Daily Brew Cart", "Coffee and cold brew", "secured"),
        ("paper-petal", "Paper Petal Studio", "Stationery and illustrated prints", "secured"),
        ("crumb-club", "Crumb Club Bakery", "Packaged cookies and brownies", "approved"),
        ("loop-lab", "Loop Lab Crafts", "Upcycled bags", None),
        ("plant-pocket", "Plant Pocket", "Mini plants", None),
        ("scent-house", "Scent House Studio", "Candles", None),
        ("bead-bar", "Bead Bar Collective", "Handmade accessories", None),
        ("snap-soda", "Snap Soda Stand", "Craft soda", None),
        ("little-zine", "Little Zine Corner", "Independent books", None),
        ("clay-day", "Clay Day Ceramics", "Ceramic gifts", None),
        ("woven-warmth", "Woven Warmth", "Textile gifts", None),
        ("sticker-society", "Sticker Society", "Stickers and postcards", None),
    ]
    for i, (slug, name, category, decision) in enumerate(categories):
        vendor(
            c,
            slug,
            name,
            25000 + i * 1000,
            0,
            "2026-10-30",
            f"One exhibitor placement: {category}. Setup 30 October, 15:00–17:00; attendance 31 October, 10:00–18:00. Support includes transport and signage. Campus provides one table and power. Applicable licence and clean-up responsibilities confirmed.",
            decision=decision,
        )
    milestone(
        c,
        "Contacted 12 suppliers",
        "All twelve fictional exhibitors replied with categories, setup availability and final support terms.",
        9,
        10,
        "mail",
    )
    milestone(
        c,
        "Two exhibitors secured",
        "Daily Brew and Paper Petal have separate simulated confirmations matching organiser-approved terms.",
        9,
        15,
    )
    milestone(
        c,
        "Seven exhibitor approvals available",
        "Two secured, one approved awaiting confirmation, seven open review slots and two waitlisted alternatives. RM10,000 is not implied: approved support is counted inside the RM5,000 aggregate ceiling.",
        10,
        14,
        "human",
    )
    answer(
        t,
        "Twelve exhibitors completed liaison. Daily Brew and Paper Petal are secured in this simulated scenario; Crumb Club is approved and awaiting confirmation. Seven placements are ready for your review, with two alternatives on the waitlist. The selected categories and all-in support costs are saved with each row.",
    )

    workshop = project(
        "build-together-workshop",
        "Build Together Workshop",
        "2026-10-28",
        {"location": "Taylor's University, Subang Jaya", "attendees": 70, "budgetSen": 120000},
        "Hands-on student workshop on 28 October, 70 attendees. The original 50 vegetarian-friendly lunch packs are confirmed with Green Table Kitchen. An additional 20 packs require a fresh quotation under RM360, using the known supplier rather than researching again. No nuts; ingredient labels and delivery at 11:30 required.",
    )
    c, t = case(
        workshop,
        "demo-workshop-lunch",
        "Workshop lunch catering",
        "Find 50 vegetarian-friendly lunch packs under RM850 for Build Together Workshop. Deliver to Taylor's University by 28 October at 11:30. Include ingredient labels, no nuts and disposable cutlery.",
        50,
        85000,
        "2026-10-28",
        "Taylor's University, Subang Jaya",
        day=7,
    )
    vendor(
        c,
        "green-table",
        "Green Table Kitchen",
        75000,
        3000,
        "2026-10-28",
        "50 vegetarian lunch packs, ingredient labels, no nuts and cutlery; delivery 11:30.",
        day=7,
        decision="secured",
    )
    vendor(
        c,
        "fresh-fork",
        "Fresh Fork Catering",
        79000,
        4000,
        "2026-10-28",
        "50 vegetarian lunch packs, ingredient labels, no nuts and cutlery; delivery 11:30.",
        day=7,
    )
    c["stage"] = "decided"
    milestone(
        c,
        "Lunch catering secured",
        "Green Table's RM780 offer was approved by the organiser and separately confirmed in the simulated reply. Fresh Fork was not selected.",
        7,
        15,
    )
    answer(
        t,
        "Green Table confirmed the approved RM780 all-in terms for 50 lunch packs, arriving at 11:30 on 28 October. The ingredient labels, no-nuts specification and cutlery are included. This is a simulated booking, with no real email or payment.",
        7,
    )
    c, t = case(
        workshop,
        "demo-workshop-extra-lunch",
        "Twenty extra lunch packs",
        "Use Green Table Kitchen again: we now need 20 more vegetarian lunch packs for Build Together Workshop. Keep the same no-nuts menu, labels and delivery slot. Budget RM360 including any additional delivery charge; request a fresh quote without researching new suppliers.",
        20,
        36000,
        "2026-10-28",
        "Taylor's University, Subang Jaya",
        day=10,
    )
    c["workflowMode"] = "liaise"
    vendor(
        c,
        "green-table",
        "Green Table Kitchen",
        30000,
        0,
        "2026-10-28",
        "20 additional vegetarian lunch packs, no nuts, ingredient labels and cutlery. Combined delivery with the original order at 11:30; no extra transport charge.",
        day=10,
        decision="approved",
    )
    c["stage"] = "decided"
    milestone(
        c,
        "Existing supplier reused",
        "Green Table's saved relationship was reused; no discovery search was repeated. Fresh terms apply to the additional 20 packs.",
        10,
        10,
        "mail",
    )
    milestone(
        c,
        "Extra lunch quotation approved",
        "The organiser approved RM300 for 20 extra packs. Supplier confirmation is still pending, so these additional packs are not yet secured.",
        10,
        14,
        "human",
    )
    answer(
        t,
        "I went directly to Green Table and obtained a fresh RM300 quote for 20 additional packs, with no extra delivery fee. Your saved approval is recorded; the additional packs remain awaiting their separate confirmation. The original 50-pack order stays secured. All correspondence here is simulated.",
    )
    return snapshot


SNAPSHOT_SQL = """select jsonb_build_object('records', coalesce((select jsonb_agg(to_jsonb(r) order by kind,id) from public.kawteam_records r where workspace_id='{workspace}'), '[]'::jsonb), 'actions', coalesce((select jsonb_agg(to_jsonb(a) order by request_id) from public.kawteam_actions a where workspace_id='{workspace}'), '[]'::jsonb))"""


def backup_query(workspace):
    from uuid import UUID

    workspace = str(UUID(workspace))
    return f"with backup as ({SNAPSHOT_SQL.format(workspace=workspace)} as payload) select payload, md5(payload::text) as digest from backup;"


def replacement_sql(workspace, expected_digest):
    from uuid import UUID

    workspace = str(UUID(workspace))
    if len(expected_digest) != 32 or any(c not in "0123456789abcdef" for c in expected_digest):
        raise ValueError("Supply the digest from a securely saved, fresh database backup.")
    rows = []
    for collection, kind in [
        ("events", "event"),
        ("cases", "case"),
        ("threads", "thread"),
        ("documents", "document"),
    ]:
        for data in build_demo()[collection]:
            payload = json.dumps(data, ensure_ascii=False).replace("'", "''")
            rows.append(f"('{workspace}','{kind}','{data['id']}','{payload}'::jsonb,1)")
    return f"""begin;
lock table public.kawteam_records, public.kawteam_actions in exclusive mode;
do $check$ declare current_digest text; begin
select md5(({SNAPSHOT_SQL.format(workspace=workspace)})::text) into current_digest;
if current_digest <> '{expected_digest}' then raise exception 'Workspace changed since backup; aborting replacement'; end if;
end $check$;
delete from public.kawteam_actions where workspace_id='{workspace}';
delete from public.kawteam_records where workspace_id='{workspace}';
insert into public.kawteam_records(workspace_id,kind,id,data,revision) values
{",\n".join(rows)};
commit;
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workspace")
    parser.add_argument("--expected-digest")
    parser.add_argument("--backup-query", action="store_true")
    args = parser.parse_args()
    if args.backup_query:
        output = backup_query(args.workspace)
    elif args.expected_digest:
        output = replacement_sql(args.workspace, args.expected_digest)
    else:
        output = json.dumps(build_demo(), ensure_ascii=False, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    print(f"Wrote offline demo artifact: {args.output.name}; no database/provider calls made.")


if __name__ == "__main__":
    main()
