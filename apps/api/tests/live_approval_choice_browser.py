"""Exercise an explicit human choice in the overview, then restore the sample."""

import subprocess
from pathlib import Path
from uuid import uuid4

from kawteam.config import Settings
from kawteam.repository import SupabaseRepository, payload_hash

repo = SupabaseRepository(Settings())
original = repo.get("case", "case-totes")
if original.get("selectedVendorId"):
    raise RuntimeError("The sample already has a human choice; do not replace it for QA.")
try:
    subprocess.run(
        ["node", "tests/approval-choice-browser.mjs"],
        cwd=Path(__file__).parents[2] / "web",
        check=True,
    )
    updated = repo.get("case", "case-totes")
    assert updated["selectedVendorId"] == "willow"
    assert len(updated.get("messages", [])) == len(original.get("messages", []))
    print("PASS: an explicit overview decision did not send supplier messages.")
finally:
    current = repo.get("case", "case-totes")
    repo.save(
        "case", original, current["backendRevision"], "organiser", str(uuid4()), payload_hash(original)
    )
    print("Original sample case restored.")
