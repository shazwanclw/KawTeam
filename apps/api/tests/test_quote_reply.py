import pytest
from test_liaison import setup

from kawteam.quote_reply import validate_quote
from kawteam.tasks import task_queue


def quote():
    return {
        "final": True,
        "quantity": 300,
        "goodsSen": 120000,
        "deliverySen": 0,
        "arrival": "2026-10-22",
        "specsConfirmed": True,
        "validUntil": "2026-10-20",
        "evidence": {
            "quantity": "300 units",
            "goodsSen": "RM1200",
            "deliverySen": "delivery included",
            "arrival": "2026-10-22",
            "specsConfirmed": "cotton, one-colour logo confirmed",
            "validUntil": "2026-10-20",
            "final": "Final quote",
        },
    }


TEXT = "Final quote: 300 units, RM1200, delivery included, delivery by 2026-10-22; cotton, one-colour logo confirmed. Valid until 2026-10-20."


def test_quote_requires_grounded_commercial_fields():
    assert validate_quote(quote(), TEXT)["goodsSen"] == 120000
    data = quote()
    data["evidence"]["deliverySen"] = "free shipping invented"
    with pytest.raises(ValueError, match="evidence"):
        validate_quote(data, TEXT)
    data = quote()
    data["goodsSen"] = 100000
    with pytest.raises(ValueError, match="amount"):
        validate_quote(data, TEXT)


def test_unknown_terms_do_not_become_final_quote():
    data = {
        "final": False,
        "quantity": None,
        "goodsSen": None,
        "deliverySen": None,
        "arrival": None,
        "specsConfirmed": False,
        "validUntil": None,
        "evidence": {},
    }
    assert not validate_quote(data, "We will check the price")["final"]
    data["final"] = True
    with pytest.raises(ValueError):
        validate_quote(data, "We will check the price")


def test_only_saved_supplier_reply_can_supply_quote_evidence():
    _repo, mail, service = setup()
    case = service.send(
        "live-task", "campus", "Quote", "Please provide quotation", 2, "test1", "teammate"
    )
    with pytest.raises(ValueError, match="reply"):
        service.quote(
            "live-task",
            "campus",
            "not-a-saved-reply",
            case["backendRevision"],
            "teammate",
            lambda c, m: quote(),
        )
    mail.incoming = [
        {
            "providerMessageId": "reply1",
            "providerThreadId": "thread-1",
            "body": TEXT,
            "sender": "test@gmail.com",
        }
    ]
    case = service.sync("live-task", case["backendRevision"], "teammate")
    case = service.quote(
        "live-task", "campus", "reply1", case["backendRevision"], "teammate", lambda c, m: quote()
    )
    assert case["messages"][-1]["kind"] == "final-quote"
    assert task_queue(case)[0]["status"] == "approval_needed"
    assert not case.get("vendorDecisions")


def test_confirmation_requires_current_human_approval_and_later_matching_reply():
    from datetime import datetime

    from kawteam.tasks import task_transition

    repo, mail, service = setup()
    case = service.send("live-task", "campus", "Quote", "Please quote", 2, "test1", "teammate")
    mail.incoming = [
        {
            "providerMessageId": "reply1",
            "providerThreadId": "thread-1",
            "body": TEXT,
            "sender": "test@gmail.com",
        }
    ]
    case = service.sync("live-task", case["backendRevision"], "teammate")
    case = service.quote(
        "live-task", "campus", "reply1", case["backendRevision"], "teammate", lambda c, m: quote()
    )
    case.setdefault("vendorDecisions", [])
    case = task_transition(case, "organiser", {"type": "approve-vendor", "vendorId": "campus"})
    repo.rows[("case", "live-task")] = case
    approved = case["vendorDecisions"][0]
    text = "Availability confirmed. " + TEXT
    mail.incoming.append(
        {
            "providerMessageId": "reply2",
            "providerThreadId": "thread-1",
            "body": text,
            "sender": "test@gmail.com",
            "receivedAtMs": str(
                int(datetime.fromisoformat(approved["approvedAt"]).timestamp() * 1000) + 1000
            ),
        }
    )
    case = service.sync("live-task", case["backendRevision"], "teammate")
    data = quote()
    data["final"] = False
    data["confirmation"] = True
    data["evidence"]["confirmation"] = "Availability confirmed"
    case = service.quote(
        "live-task", "campus", "reply2", case["backendRevision"], "teammate", lambda c, m: data
    )
    assert task_queue(case)[0]["status"] == "secured"
    assert case["messages"][-1]["kind"] == "commitment-confirmation"


@pytest.mark.parametrize("problem", ["no_approval", "before_approval", "different_price"])
def test_confirmation_cannot_bypass_human_choice_or_change_terms(problem):
    from datetime import datetime

    from kawteam.tasks import task_transition

    repo, mail, service = setup()
    case = service.send("live-task", "campus", "Quote", "Please quote", 2, "test1", "teammate")
    mail.incoming = [
        {
            "providerMessageId": "reply1",
            "providerThreadId": "thread-1",
            "body": TEXT,
            "sender": "test@gmail.com",
        }
    ]
    case = service.sync("live-task", case["backendRevision"], "teammate")
    case = service.quote(
        "live-task", "campus", "reply1", case["backendRevision"], "teammate", lambda c, m: quote()
    )
    case = task_transition(case, "organiser", {"type": "approve-vendor", "vendorId": "campus"})
    approved_ms = int(
        datetime.fromisoformat(case["vendorDecisions"][0]["approvedAt"]).timestamp() * 1000
    )
    if problem == "no_approval":
        case["vendorDecisions"] = []
    repo.rows[("case", "live-task")] = case
    text = "Availability confirmed. " + TEXT
    data = quote()
    if problem == "different_price":
        text = text.replace("RM1200", "RM1300")
        data["goodsSen"] = 130000
        data["evidence"]["goodsSen"] = "RM1300"
    mail.incoming.append(
        {
            "providerMessageId": "reply2",
            "providerThreadId": "thread-1",
            "body": text,
            "sender": "test@gmail.com",
            "receivedAtMs": str(approved_ms + (-1000 if problem == "before_approval" else 1000)),
        }
    )
    case = service.sync("live-task", case["backendRevision"], "teammate")
    data.update(final=False, confirmation=True)
    data["evidence"]["confirmation"] = "Availability confirmed"
    with pytest.raises(ValueError):
        service.quote(
            "live-task", "campus", "reply2", case["backendRevision"], "teammate", lambda c, m: data
        )
    assert all(d["status"] != "secured" for d in repo.get("case", "live-task")["vendorDecisions"])


def test_reply_to_old_request_cannot_become_current_quote_after_edit():
    from kawteam.tasks import invalidate_terms

    repo, mail, service = setup()
    case = service.send("live-task", "campus", "Quote", "Please quote", 2, "test1", "teammate")
    mail.incoming = [
        {
            "providerMessageId": "reply1",
            "providerThreadId": "thread-1",
            "body": TEXT,
            "sender": "test@gmail.com",
        }
    ]
    case = service.sync("live-task", case["backendRevision"], "teammate")
    invalidate_terms(case)
    case["goal"] += " Now use organic cotton instead."
    repo.rows[("case", "live-task")] = case
    assert case["vendors"][0]["contact"]["email"] == "test@gmail.com"
    with pytest.raises(ValueError, match="current request"):
        service.quote(
            "live-task",
            "campus",
            "reply1",
            case["backendRevision"],
            "teammate",
            lambda c, m: quote(),
        )


def test_latest_reply_uses_received_timestamp_instead_of_sync_append_order():
    _repo, mail, service = setup()
    case = service.send("live-task", "campus", "Quote", "Please quote", 2, "test1", "teammate")
    mail.incoming = [
        {
            "providerMessageId": "newer",
            "providerThreadId": "thread-1",
            "body": TEXT,
            "sender": "test@gmail.com",
            "receivedAtMs": "2000",
        },
        {
            "providerMessageId": "older",
            "providerThreadId": "thread-1",
            "body": TEXT,
            "sender": "test@gmail.com",
            "receivedAtMs": "1000",
        },
    ]
    case = service.sync("live-task", case["backendRevision"], "teammate")
    with pytest.raises(ValueError, match="latest"):
        service.quote(
            "live-task",
            "campus",
            "older",
            case["backendRevision"],
            "teammate",
            lambda c, m: quote(),
        )
    case = service.quote(
        "live-task", "campus", "newer", case["backendRevision"], "teammate", lambda c, m: quote()
    )
    assert task_queue(case)[0]["status"] == "approval_needed"
