"""Opt-in saved task UI check. Restore sample and remove only this run's QA project."""

import copy
import json
import os
import subprocess
from pathlib import Path
from uuid import uuid4

from kawteam.config import Settings
from kawteam.repository import SupabaseRepository, payload_hash

repo = SupabaseRepository(Settings())
original = repo.get("case", "case-totes")
if original.get("taskWorkflowVersion") or original.get("selectedVendorId"):
    raise SystemExit(
        "The sample has prior decisions; use a dedicated fixture before running this check."
    )
web = Path(__file__).parents[2] / "web"
artifact = web / "test-results/task-flow-created.json"
if artifact.exists():
    artifact.unlink()
try:
    fixture = copy.deepcopy(original)
    fixture["budgetSen"] = 200000
    fixture["goal"] = fixture["goal"].replace("RM1,500", "RM2,000")
    repo.save(
        "case",
        fixture,
        original["backendRevision"],
        "organiser",
        str(uuid4()),
        payload_hash(fixture),
    )
    subprocess.run(
        ["node", "tests/task-flow-browser.mjs"],
        cwd=web,
        check=True,
        env={**os.environ, "KAWTEAM_ALLOW_SAMPLE_MUTATION": "1"},
    )
    changed = repo.get("case", "case-totes")
    assert len({m["vendorId"] for m in changed["messages"] if m["direction"] == "sent"}) == 3
    assert changed["vendorDecisions"][0]["status"] == "rejected"
    confirmed = next(d for d in changed["vendorDecisions"] if d["status"] == "secured")
    assert confirmed["confirmationMessageId"]
    print(
        "PASS: all three sample suppliers liaised with; only the human-approved supplier secured after its separate confirmation."
    )
finally:
    current = repo.get("case", "case-totes")
    repo.save(
        "case",
        original,
        current["backendRevision"],
        "organiser",
        str(uuid4()),
        payload_hash(original),
    )
    print("Original sample restored. QA project ID is recorded for scoped cleanup.")
    if artifact.exists():
        print("QA project:", json.loads(artifact.read_text())["id"])
