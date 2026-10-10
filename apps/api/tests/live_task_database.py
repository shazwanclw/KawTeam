"""Opt-in transactional task/chat checks against a labelled disposable project."""

import copy
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from kawteam.config import Settings
from kawteam.main import create_case
from kawteam.repository import SupabaseRepository, payload_hash

repo = SupabaseRepository(Settings())
event_id = "qa-task-atomic-" + str(uuid4())
event = {"id": event_id, "name": "QA task atomic transaction", "facts": {}, "tasks": []}
repo.save("event", event, 0, "organiser", str(uuid4()), payload_hash(event))
tasks = [
    {"id": str(uuid4()), "name": name, "createdAt": "2026-10-11"} for name in ["Shirts", "Catering"]
]
users = [
    {"id": str(uuid4()), "role": "user", "body": name} for name in ["Find shirts", "Find catering"]
]
with ThreadPoolExecutor(max_workers=2) as pool:
    list(pool.map(lambda i: repo.start_task(event_id, tasks[i], users[i], "teammate"), range(2)))
assert len(repo.get("event", event_id)["tasks"]) == 2
earlier = {'id':str(uuid4()),'role':'user','body':'Earlier project note'}
repo.append_message(event_id, earlier, 'organiser')
legacy_task = {'id':'legacy-'+event_id,'name':'Earlier project conversation','sourceThreadId':'event-'+event_id}
repo.start_task(event_id, legacy_task, {'id':str(uuid4()),'role':'user','body':'Continue'}, 'organiser')
legacy = repo.get('thread', 'event-'+event_id+'-task-'+legacy_task['id'])
assert len(legacy['messages']) == 2 and legacy['messages'][0]['body'] == earlier['body']
assert len(repo.get('thread','event-'+event_id)['messages']) == 1
with ThreadPoolExecutor(max_workers=2) as pool:
    list(pool.map(lambda _: repo.start_task(event_id, tasks[0], users[0], "teammate"), range(2)))
assert len(repo.get("thread", f"event-{event_id}-task-{tasks[0]['id']}")["messages"]) == 1
try:
    repo.start_task(event_id, tasks[0], {**users[0], "body": "Changed retry"}, "teammate")
    raise AssertionError("Changed idempotent request was accepted")
except ValueError:
    pass
try:
    repo.start_task(event_id, {"id": "denied", "name": "Denied"}, users[0], "observer")
    raise AssertionError("Observer created a task")
except PermissionError:
    pass
assert len(repo.get("event", event_id)["tasks"]) == 3
request = create_case(
    {
        "title": "Shirts",
        "goal": "Test continuation",
        "quantity": 50,
        "budgetSen": 200000,
        "targetSen": 180000,
        "deadline": "2026-10-25",
        "location": "Subang Jaya",
    },
    str(uuid4()),
    event_id,
)
request["taskId"] = tasks[0]["id"]
assistant = {
    "id": str(uuid4()),
    "role": "assistant",
    "body": "Saved",
    "inReplyTo": users[0]["id"],
    "caseId": request["id"],
}
repo.append_message(event_id, assistant, "organiser", request, task_id=tasks[0]["id"])
request = repo.get("case", request["id"])
followup = {"id": str(uuid4()), "role": "user", "body": "40 shirts instead"}
repo.append_message(event_id, followup, "organiser", task_id=tasks[0]["id"])
updated = copy.deepcopy(request)
updated["quantity"] = 40
answer = {**assistant, "id": str(uuid4()), "inReplyTo": followup["id"]}
with ThreadPoolExecutor(max_workers=2) as pool:
    list(
        pool.map(
            lambda _: repo.append_message(
                event_id, answer, "organiser", updated, task_id=tasks[0]["id"]
            ),
            range(2),
        )
    )
saved = repo.get("case", request["id"])
assert saved["quantity"] == 40 and saved["backendRevision"] == 2
assert len(repo.get("thread", f"event-{event_id}-task-{tasks[0]['id']}")["messages"]) == 4
print('PASS: concurrent task creation/retry, observer rejection, preserved legacy history and atomic in-place case/chat completion.')
print("Disposable project:", event_id)
