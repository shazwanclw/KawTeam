import hashlib
import json
import ssl

import httpx
import truststore

from .config import Settings


def payload_hash(data):
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class SupabaseRepository:
    def __init__(self, settings: Settings):
        settings.validate()
        self.settings = settings

    def rpc(self, name, **params):
        body = {
            "p_workspace": self.settings.workspace,
            "p_secret": self.settings.database_secret,
            **params,
        }
        context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=context, timeout=20) as client:
            response = client.post(
                f"{self.settings.supabase_url}/rest/v1/rpc/{name}",
                headers={
                    "apikey": self.settings.publishable_key,
                    "Content-Type": "application/json",
                },
                json=body,
            )
        if response.status_code >= 400:
            code = response.json().get("code")
            if code in {"40001", "23505"}:
                raise ValueError(
                    "Stale revision: another teammate changed this record. Refresh and retry."
                )
            if code == "42501":
                raise PermissionError("Workspace access denied.")
            if "Idempotency" in response.text:
                raise ValueError("Idempotency key reused for a different action.")
            raise RuntimeError(
                f"Database request failed ({response.status_code}); no local fallback used."
            )
        return response.json()

    def snapshot(self):
        return self.rpc("kawteam_read")

    def upload(self, document, facts, actor):
        return self.rpc("kawteam_upload", p_document=document, p_facts=facts, p_actor=actor)

    def documents(self, event_id):
        return self.rpc("kawteam_documents", p_event=event_id)

    def drive_snapshot(
        self, event_id, expected, documents, archive_ids, facts, fact_keys, metadata, actor
    ):
        return self.rpc(
            "kawteam_drive_snapshot",
            p_event=event_id,
            p_expected=expected,
            p_documents=documents,
            p_archive=archive_ids,
            p_facts=facts,
            p_fact_keys=fact_keys,
            p_source=metadata,
            p_actor=actor,
        )

    def append_message(self, event_id, message, actor, case=None, task_id=None):
        return self.rpc(
            "kawteam_project_chat",
            p_event=event_id,
            p_task=task_id,
            p_message=message,
            p_case=case,
            p_actor=actor,
        )

    def start_task(self, event_id, task, message, actor):
        return self.rpc('kawteam_task_start', p_event=event_id, p_task=task, p_message=message, p_actor=actor)

    def get(self, kind, id):
        return self.rpc("kawteam_record", p_kind=kind, p_id=id)

    def prior(self, key, digest):
        return self.rpc("kawteam_request", p_key=key, p_hash=digest)

    def save(self, kind, data, expected, actor, key, digest):
        return self.rpc(
            "kawteam_commit",
            p_kind=kind,
            p_id=data["id"],
            p_data=data,
            p_expected=expected,
            p_actor=actor,
            p_key=key,
            p_hash=digest,
        )
