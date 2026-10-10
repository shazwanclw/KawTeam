import copy

import pytest
from test_workflow import case

from kawteam import tasks, workflow


def ready_case(target=1, budget=600000):
    c = case()
    c.update(taskWorkflowVersion=1, selectionTarget=target, vendorDecisions=[], budgetSen=budget)
    c["draft"]["body"] = ""
    for i, v in enumerate(c["vendors"]):
        v.update(
            executionMode="live",
            quantity=300,
            goodsSen=100000 + i * 10000,
            deliverySen=0,
            arrival="2026-10-23",
            specsConfirmed=True,
            validUntil="2026-10-25",
            liaisonStatus="ready",
        )
        c.setdefault("messages", []).append(
            {
                "id": "reply-" + v["id"],
                "vendorId": v["id"],
                "direction": "received",
                "body": "Final quote confirmed.",
                "kind": "final-quote",
                "time": "2026-10-11T01:00:00Z",
                "executionMode": "live",
            }
        )
        c["messages"][-1]["termsHash"] = tasks.term_token(c, v)
    return c


def queue(c):
    assert hasattr(tasks, "task_queue"), "Task approval queue is not implemented"
    return tasks.task_queue(c)


def test_only_completed_liaison_enters_ranked_active_slots():
    c = ready_case()
    c["vendors"][0]["liaisonStatus"] = "awaiting_reply"
    rows = queue(c)
    assert [r["status"] for r in rows] == ["approval_needed", "waitlist", "liaising"]
    assert rows[0]["vendorId"] == c["vendors"][1]["id"]


def test_rejection_promotes_waitlist_and_approval_closes_other_candidates():
    c = ready_case()
    first = queue(c)[0]["vendorId"]
    c = workflow.transition(c, "organiser", {"type": "reject-vendor", "vendorId": first})
    next_id = next(r for r in queue(c) if r["status"] == "approval_needed")["vendorId"]
    c = workflow.transition(c, "organiser", {"type": "approve-vendor", "vendorId": next_id})
    assert sum(r["status"] == "approved" for r in queue(c)) == 1
    assert sum(r["status"] == "not_selected" for r in queue(c)) == 1
    assert not any(r["status"] == "secured" for r in queue(c))


def test_multi_slots_and_total_budget_are_enforced():
    c = ready_case(2)
    assert sum(r["status"] == "approval_needed" for r in queue(c)) == 2
    for v in c["vendors"][:2]:
        c = workflow.transition(c, "organiser", {"type": "approve-vendor", "vendorId": v["id"]})
    with pytest.raises(ValueError, match="slot|waitlist"):
        workflow.transition(
            c, "organiser", {"type": "approve-vendor", "vendorId": c["vendors"][2]["id"]}
        )
    c = ready_case(2, 200000)
    c = workflow.transition(
        c, "organiser", {"type": "approve-vendor", "vendorId": c["vendors"][0]["id"]}
    )
    assert not any(r["status"] == "approval_needed" for r in queue(c))


def test_roles_and_premature_approval_are_blocked():
    c = ready_case()
    with pytest.raises(PermissionError):
        workflow.transition(
            c, "teammate", {"type": "approve-vendor", "vendorId": c["vendors"][0]["id"]}
        )
    c["vendors"][0]["liaisonStatus"] = "awaiting_reply"
    with pytest.raises(ValueError):
        workflow.transition(
            c, "organiser", {"type": "approve-vendor", "vendorId": c["vendors"][0]["id"]}
        )


def test_live_confirmation_cannot_be_fabricated_by_demo_action():
    c = ready_case()
    c = workflow.transition(
        c, "organiser", {"type": "approve-vendor", "vendorId": c["vendors"][0]["id"]}
    )
    with pytest.raises(ValueError, match="demo|controlled"):
        workflow.transition(
            c, "organiser", {"type": "confirm-vendor", "vendorId": c["vendors"][0]["id"]}
        )


def test_controlled_liaison_contacts_entire_pool_and_secured_requires_later_reply():
    c = case()
    c.update(taskWorkflowVersion=1, selectionTarget=1, vendorDecisions=[], budgetSen=200000)
    c = workflow.transition(c, "teammate", {"type": "liaise-task"})
    assert len({m["vendorId"] for m in c["messages"] if m["direction"] == "sent"}) == 3
    assert all(v["liaisonStatus"] == "ready" for v in c["vendors"])
    first = next(r for r in queue(c) if r["status"] == "approval_needed")["vendorId"]
    c = workflow.transition(c, "organiser", {"type": "approve-vendor", "vendorId": first})
    assert not any(r["status"] == "secured" for r in queue(c))
    c = workflow.transition(c, "organiser", {"type": "confirm-vendor", "vendorId": first})
    assert sum(r["status"] == "secured" for r in queue(c)) == 1
    assert c["vendorDecisions"][0]["confirmationMessageId"]
    before = copy.deepcopy(c)
    with pytest.raises(ValueError):
        workflow.transition(c, "organiser", {"type": "confirm-vendor", "vendorId": first})
    assert c == before


def test_secured_label_requires_matching_confirmation_evidence():
    c = ready_case()
    c = workflow.transition(
        c, "organiser", {"type": "approve-vendor", "vendorId": c["vendors"][0]["id"]}
    )
    c["vendorDecisions"][0]["status"] = "secured"
    assert not any(row["status"] == "secured" for row in queue(c))


def test_quote_changes_invalidate_approval_and_expired_quotes_cannot_confirm():
    c = case()
    c = workflow.transition(c, "organiser", {"type": "liaise-task"})
    c = workflow.transition(c, "organiser", {"type": "approve-vendor", "vendorId": "willow"})
    c["vendors"][2]["validUntil"] = "2020-01-01"
    with pytest.raises(ValueError):
        workflow.transition(c, "organiser", {"type": "confirm-vendor", "vendorId": "willow"})


def test_scope_changes_keep_history_but_remove_current_security_and_quotes():
    from kawteam.tasks import invalidate_terms

    c = ready_case()
    c = workflow.transition(
        c, "organiser", {"type": "approve-vendor", "vendorId": c["vendors"][0]["id"]}
    )
    invalidate_terms(c)
    assert c["vendorDecisions"][0]["status"] == "superseded"
    assert all(v["goodsSen"] == 0 and v["arrival"] is None for v in c["vendors"])
    assert not any(r["status"] in {"approved", "secured", "approval_needed"} for r in queue(c))


def test_final_reply_must_match_current_quote_terms():
    c = ready_case()
    c["vendors"][0]["goodsSen"] += 1
    row = next(r for r in queue(c) if r["vendorId"] == c["vendors"][0]["id"])
    assert row["status"] != "approval_needed"


def test_ten_supplier_task_can_approve_ten_and_closes_the_rest():
    c = ready_case(10, 2000000)
    prototype = copy.deepcopy(c["vendors"][0])
    c["vendors"] = []
    c["messages"] = []
    for i in range(12):
        v = {
            **prototype,
            "id": f"vendor-{i:02}",
            "name": f"Vendor {i:02}",
            "goodsSen": 100000 + i * 1000,
        }
        c["vendors"].append(v)
        c["messages"].append(
            {
                "id": f"quote-{i}",
                "vendorId": v["id"],
                "direction": "received",
                "kind": "final-quote",
                "termsHash": tasks.term_token(c, v),
            }
        )
    assert sum(r["status"] == "approval_needed" for r in queue(c)) == 10
    for v in c["vendors"][:10]:
        c = workflow.transition(c, "organiser", {"type": "approve-vendor", "vendorId": v["id"]})
    assert sum(r["status"] == "approved" for r in queue(c)) == 10
    assert sum(r["status"] == "not_selected" for r in queue(c)) == 2
    assert not any(r["status"] == "secured" for r in queue(c))
