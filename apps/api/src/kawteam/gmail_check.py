"""Opt-in controlled inbox acceptance test. Never contacts real suppliers."""

import argparse

from .config import Settings
from .gmail import Gmail
from .liaison import Liaison
from .repository import SupabaseRepository, payload_hash
from .tasks import now

CASE_ID = "qa-email-20261011"
PROJECT_ID = "qa-email-connection"
RECIPIENT = "shazwan1512alt@gmail.com"
SENDER = "shazwan15122005@gmail.com"


def main():
    parser = argparse.ArgumentParser(
        description="One authorised KawTeam email test, persisted in a clearly labelled QA project."
    )
    parser.add_argument("action", choices=["send", "replies"])
    args = parser.parse_args()
    settings = Settings()
    mail = Gmail.from_settings(settings)
    if mail.profile()["sender"] != SENDER:
        raise ValueError("This controlled test is authorised only for the configured test sender.")
    repo = SupabaseRepository(settings)
    liaison = Liaison(repo, mail)
    case = repo.get("case", CASE_ID)
    if args.action == "send":
        if not repo.get("event", PROJECT_ID):
            event = {
                "id": PROJECT_ID,
                "name": "QA · Email connection test",
                "sample": False,
                "facts": {},
                "createdAt": now(),
                "tasks": [{"id": CASE_ID, "name": "Controlled inbox test", "createdAt": now()}],
            }
            repo.save("event", event, 0, "organiser", "qa-mail-project", payload_hash(event))
        if not case:
            case = {
                "id": CASE_ID,
                "eventId": PROJECT_ID,
                "taskId": CASE_ID,
                "taskWorkflowVersion": 1,
                "title": "Controlled inbox test (not a supplier request)",
                "goal": "Verify one authorised test email and matching reply. No commercial offer or booking.",
                "quantity": 1,
                "selectionTarget": 1,
                "budgetSen": 100,
                "targetSen": 100,
                "deadline": "2026-12-31",
                "location": "Controlled inboxes",
                "stage": "brief",
                "selectedVendorId": None,
                "messages": [],
                "events": [],
                "draft": {
                    "recipient": RECIPIENT,
                    "subject": "[KawTeam TEST] Email connection check",
                    "body": "",
                    "revision": 1,
                    "status": "pending",
                },
                "vendors": [
                    {
                        "id": "controlled-inbox",
                        "name": "Controlled test inbox (not a supplier)",
                        "initials": "QA",
                        "location": "Test only",
                        "color": "peach",
                        "executionMode": "live",
                        "goodsSen": 0,
                        "deliverySen": None,
                        "arrival": None,
                        "specsConfirmed": False,
                        "status": "Awaiting test reply",
                        "description": "User-authorised test recipient",
                        "strengths": [],
                        "concerns": [],
                        "quoteRef": "",
                    }
                ],
            }
            case = repo.save("case", case, 0, "organiser", "qa-mail-task", payload_hash(case))
        if not case["vendors"][0].get("contact"):
            case = liaison.contact(
                CASE_ID, "controlled-inbox", RECIPIENT, case["backendRevision"], "organiser"
            )
        case = liaison.send(
            CASE_ID,
            "controlled-inbox",
            "[KawTeam TEST] Email connection check",
            "This is the single email connection test authorised by Shazwan. No supplier request, booking or payment is being made.\n\nPlease reply to this email with: KawTeam email test received.\n\nThank you,\nKawTeam",
            case["backendRevision"],
            "qa-email-test-20261011",
            "organiser",
        )
        print(
            "Authorised test email receipt saved. Sender: "
            + SENDER
            + "; recipient: "
            + RECIPIENT
            + ". Rerunning does not send a second email."
        )
    else:
        if not case:
            raise ValueError("Send the authorised test first.")
        case = liaison.sync(CASE_ID, case["backendRevision"], "organiser")
        replies = [
            m
            for m in case["messages"]
            if m.get("direction") == "received" and m.get("executionMode") == "live"
        ]
        print(f"Controlled test replies saved: {len(replies)}. No other inbox threads were read.")


if __name__ == "__main__":
    main()
