import copy
import json

import pytest

from kawteam.automation import Automation
from kawteam.demo_scenarios import backup_query, build_demo, replacement_sql
from kawteam.liaison import Liaison
from kawteam.tasks import current_decisions, task_queue, task_transition
from kawteam.workflow import fit


def test_complete_consistent_simulated_relationships():
    data = build_demo()
    assert len(data["events"]) == 3
    assert len(data["cases"]) == 4
    projects = {p["id"]: p for p in data["events"]}
    assert len(data["documents"]) == 3
    for case in data["cases"]:
        assert case["sample"] and case["demoScenarioVersion"] == 1
        assert any(t["id"] == case["taskId"] for t in projects[case["eventId"]]["tasks"])
        thread = next(t for t in data["threads"] if t["taskId"] == case["taskId"])
        assert thread["id"] == f"event-{case['eventId']}-task-{case['taskId']}"
        assert {m["role"] for m in thread["messages"]} == {"assistant", "user"}
        assert not case.get("automation") and not case.get("emailIntents")
        for vendor in case["vendors"]:
            assert fit(case, vendor) == "Meets your brief"
            assert vendor["executionMode"] == "demo"
            assert vendor["contact"]["email"].endswith(".example")
            messages = [m for m in case["messages"] if m["vendorId"] == vendor["id"]]
            assert [m["direction"] for m in messages[:4]] == [
                "sent",
                "received",
                "sent",
                "received",
            ]
            assert all(m["executionMode"] == "demo" for m in messages)
            assert all(not m.get("providerMessageId") for m in messages)


def test_three_presentable_queue_states_and_repeat_supplier():
    cases = build_demo()["cases"]
    shirts, market, original, repeat = cases
    assert [r["status"] for r in task_queue(shirts)] == ["approval_needed"] + ["waitlist"] * 4
    market_queue = task_queue(market)
    assert market['quantity'] == 1 and market['selectionTarget'] == 10
    assert sum(r["status"] == "secured" for r in market_queue) == 2
    assert sum(r["status"] == "approved" for r in market_queue) == 1
    assert sum(r["status"] == "approval_needed" for r in market_queue) == 7
    assert sum(r["status"] == "waitlist" for r in market_queue) == 2
    assert current_decisions(original)[0]["status"] == "secured"
    assert current_decisions(repeat)[0]["status"] == "approved"
    assert repeat["workflowMode"] == "liaise"
    assert repeat["vendors"][0]["name"] == original["vendors"][0]["name"]
    for case in cases:
        for decision in case["vendorDecisions"]:
            selection = next(
                m
                for m in case["messages"]
                if m["vendorId"] == decision["vendorId"]
                and m["kind"] == "selection-confirmation-request"
            )
            assert selection["direction"] == "sent" and selection["approvalId"] == decision["id"]
            if decision["status"] == "secured":
                confirmation = next(
                    m for m in case["messages"] if m["id"] == decision["confirmationMessageId"]
                )
                assert selection["at"] < confirmation["at"]
    assert "one exhibitor placement" in market["messages"][0]["body"]
    assert "10 ten event vendors" not in market["messages"][0]["body"]


def test_demo_approval_rejection_and_confirmation_remain_separate():
    case = build_demo()["cases"][0]
    first = task_queue(case)[0]["vendorId"]
    rejected = task_transition(case, "organiser", {"type": "reject-vendor", "vendorId": first})
    assert (
        next(r for r in task_queue(rejected) if r["status"] == "approval_needed")["vendorId"]
        != first
    )
    approved = task_transition(case, "organiser", {"type": "approve-vendor", "vendorId": first})
    assert current_decisions(approved)[0]["status"] == "approved"
    confirmed = task_transition(
        approved, "organiser", {"type": "confirm-vendor", "vendorId": first}
    )
    assert current_decisions(confirmed)[0]["status"] == "secured"
    assert confirmed["messages"][-1]["executionMode"] == "demo"
    assert "No real order" in confirmed["messages"][-1]["body"]
    with pytest.raises(PermissionError):
        task_transition(case, "teammate", {"type": "approve-vendor", "vendorId": first})


def test_fixture_provenance_cannot_cross_cases_or_live_liaison():
    case = build_demo()["cases"][0]
    vendor = case["vendors"][0]
    for change in [{"sample": False}, {"demoScenarioVersion": 0}, {"id": "different-case"}]:
        altered = {**case, **change}
        assert fit(altered, vendor) == "Sample quote for a different case"
    altered = copy.deepcopy(vendor)
    altered["scenarioCaseId"] = "wrong"
    assert fit(case, altered) == "Sample quote for a different case"
    with pytest.raises(ValueError, match="not a sample supplier"):
        Liaison(None, None).vendor(case, vendor["id"])

    class Repo:
        def get(self, kind, id):
            return {**case, "backendRevision": 1}

    # No provider object is even provided: an accidental tick is denied before any external call.
    with pytest.raises(ValueError, match="has not been authorised"):
        Automation(Liaison(Repo(), None), None, None).tick(case["id"], "organiser")


def test_replacement_is_workspace_scoped_transactional_and_backup_checked():
    workspace = "a86971a9-7f0a-4169-9f29-d31a7ca719b1"
    sql = replacement_sql(workspace, "a" * 32)
    assert sql.startswith("begin;") and sql.rstrip().endswith("commit;")
    assert "lock table" in sql and "Workspace changed since backup" in sql
    assert "delete from public.kawteam_workspaces" not in sql
    assert "credential_digest" not in sql
    assert sql.count("delete from") == 2
    assert ".example" in sql
    assert "md5(payload::text)" in backup_query(workspace)
    with pytest.raises(ValueError):
        replacement_sql(workspace, "invalid")
    # Generator is reproducible and never sneaks changing timestamps/provider receipts into a reset.
    assert json.dumps(build_demo(), sort_keys=True) == json.dumps(build_demo(), sort_keys=True)
