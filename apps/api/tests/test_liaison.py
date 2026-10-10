import copy

import pytest
from test_api import MemoryRepository

from kawteam.liaison import Liaison


def test_ordinary_acknowledgement_after_approval_preserves_terms_and_future_confirmation():
    from kawteam.liaison import request_token
    from kawteam.tasks import term_token
    repo, _mail, service = setup()
    case = repo.rows[("case", "live-task")]
    vendor = case["vendors"][0]
    original_price = vendor["goodsSen"]
    case["vendorDecisions"] = [{"id": "decision", "vendorId": vendor["id"], "status": "approved", "termsHash": term_token(case, vendor), "approvedAt": "2026-10-11T00:00:00+00:00"}]
    case["messages"] = [{"id": "ack", "vendorId": vendor["id"], "direction": "received", "executionMode": "live", "requestHash": request_token(case), "providerMessageId": "ack", "receivedAtMs": 1791676800001, "body": "We are checking availability."}]
    data = {"final": False, "confirmation": False, "quantity": None, "goodsSen": None, "deliverySen": None, "arrival": None, "specsConfirmed": False, "validUntil": None, "evidence": {}}
    result = service.quote("live-task", vendor["id"], "ack", 2, "teammate", lambda *args: data)
    assert result["messages"][-1]["quoteInterpretation"]["confirmation"] is False
    assert result["vendorDecisions"][0]["status"] == "approved"
    assert result["vendors"][0]["goodsSen"] == original_price


class Mail:
    def __init__(self):
        self.sender = "sender@gmail.com"
        self.sent = []
        self.incoming = []
        self.fail = False

    def profile(self):
        return {"sender": self.sender, "status": "connected"}

    def send(self, recipient, subject, body, intent_id, **kwargs):
        self.sent.append(recipient)
        if self.fail:
            raise TimeoutError("private provider error")
        return {
            "providerMessageId": "sent-1",
            "providerThreadId": "thread-1",
            "rfcMessageId": f"<{intent_id}@kawteam.local>",
        }

    def replies(self, thread_id, supplier):
        assert thread_id == "thread-1"
        return copy.deepcopy(self.incoming)


def setup():
    repo, mail = MemoryRepository(), Mail()
    case = repo.rows[("case", "case-totes")]
    case["id"] = "live-task"
    case["taskWorkflowVersion"] = 1
    case["taskId"] = "task-1"
    case["eventId"] = "tech-night"
    case["vendors"] = [dict(case["vendors"][0], executionMode="live")]
    repo.rows[("case", "live-task")] = copy.deepcopy(case)
    service = Liaison(repo, mail)
    service.contact("live-task", "campus", "test@gmail.com", 1, "organiser")
    return repo, mail, service


def test_verified_contact_required_and_observer_cannot_send():
    repo, mail, service = setup()
    with pytest.raises(PermissionError):
        service.send(
            "live-task", "campus", "Quotation", "Non-binding enquiry", 2, "request1", "observer"
        )
    repo.rows[("case", "live-task")]["vendors"][0].pop("contact")
    with pytest.raises(ValueError, match="contact"):
        service.send(
            "live-task", "campus", "Quotation", "Non-binding enquiry", 2, "request1", "teammate"
        )
    assert mail.sent == []


def test_send_intent_is_durable_and_retry_never_duplicates():
    _repo, mail, service = setup()
    result = service.send(
        "live-task", "campus", "Quotation", "Non-binding enquiry", 2, "request1", "teammate"
    )
    assert result["emailIntents"][0]["status"] == "sent"
    assert result["messages"][-1]["providerMessageId"] == "sent-1"
    service.send(
        "live-task", "campus", "Quotation", "Non-binding enquiry", 2, "request1", "teammate"
    )
    assert mail.sent == ["test@gmail.com"]
    with pytest.raises(ValueError, match="Idempotency"):
        service.send(
            "live-task",
            "campus",
            "Quotation",
            "Changed body",
            result["backendRevision"],
            "request1",
            "teammate",
        )


def test_uncertain_send_remains_blocked_for_reconciliation():
    repo, mail, service = setup()
    mail.fail = True
    with pytest.raises(ValueError, match="uncertain"):
        service.send(
            "live-task", "campus", "Quotation", "Non-binding enquiry", 2, "request1", "teammate"
        )
    assert repo.get("case", "live-task")["emailIntents"][0]["status"] == "uncertain"
    with pytest.raises(ValueError, match="reconcile"):
        service.send(
            "live-task", "campus", "Quotation", "Non-binding enquiry", 2, "request1", "teammate"
        )
    assert len(mail.sent) == 1


def test_sync_deduplicates_and_does_not_fabricate_final_quote():
    _repo, mail, service = setup()
    case = service.send(
        "live-task", "campus", "Quotation", "Non-binding enquiry", 2, "request1", "teammate"
    )
    mail.incoming = [
        {
            "providerMessageId": "reply1",
            "providerThreadId": "thread-1",
            "body": "Thanks, we will check pricing",
            "sender": "test@gmail.com",
        }
    ]
    case = service.sync("live-task", case["backendRevision"], "teammate")
    assert case["messages"][-1]["kind"] == "supplier-reply"
    assert case["vendors"][0]["liaisonStatus"] != "ready"
    again = service.sync("live-task", case["backendRevision"], "teammate")
    assert len(again["messages"]) == len(case["messages"])


def test_agent_cannot_register_arbitrary_contact_as_verified():
    _repo, _mail, service = setup()
    with pytest.raises(PermissionError):
        service.contact("live-task", "campus", "victim@gmail.com", 2, "teammate")


def test_http_timeout_is_uncertain_and_binding_order_is_rejected():
    import httpx

    repo, mail, service = setup()
    with pytest.raises(ValueError, match="non-binding"):
        service.send(
            "live-task", "campus", "Order", "Please confirm the booking", 2, "binding1", "teammate"
        )

    def timed_out(*args, **kwargs):
        raise httpx.ReadTimeout("private details")

    mail.send = timed_out
    with pytest.raises(ValueError, match="uncertain"):
        service.send(
            "live-task",
            "campus",
            "Quotation",
            "Please quote this request",
            2,
            "timeout1",
            "teammate",
        )
    assert repo.get("case", "live-task")["emailIntents"][0]["status"] == "uncertain"


def test_mailbox_switch_never_reads_old_sender_threads_or_reuses_old_receipt():
    _repo, mail, service = setup()
    case = service.send(
        "live-task", "campus", "Quotation", "Non-binding enquiry", 2, "request1", "teammate"
    )
    assert case["emailIntents"][0]["gmailSender"] == "sender@gmail.com"
    mail.sender = "new@gmail.com"
    mail.replies = lambda *args: pytest.fail(
        "Old sender thread must not be read through the new account"
    )
    with pytest.raises(ValueError, match="saved supplier threads"):
        service.sync("live-task", case["backendRevision"], "teammate")
    with pytest.raises(ValueError, match="Idempotency"):
        service.send(
            "live-task",
            "campus",
            "Quotation",
            "Non-binding enquiry",
            case["backendRevision"],
            "request1",
            "teammate",
        )
