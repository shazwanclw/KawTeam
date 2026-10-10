"""Bounded Drive API reads; user links are identifiers, never fetch destinations."""

import json
import re
import ssl
import time
from urllib.parse import parse_qs, urlparse

import httpx
import truststore

from .memory import extract_text

ROOT = "https://www.googleapis.com/drive/v3/files"
MAX_BYTES = 3 * 1024 * 1024


def parse_drive_url(url):
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"drive.google.com", "docs.google.com"}
        or parsed.username
        or parsed.password
        or parsed.port
    ):
        raise ValueError("Use an HTTPS Google Drive folder or document link.")
    patterns = [r"/folders/([A-Za-z0-9_-]{10,200})(?:/|$)", r"/d/([A-Za-z0-9_-]{10,200})(?:/|$)"]
    match = next((m for pattern in patterns if (m := re.search(pattern, parsed.path))), None)
    id = match.group(1) if match else parse_qs(parsed.query).get("id", [""])[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,200}", id):
        raise ValueError("The Drive link needs a valid folder or file ID.")
    resource = parse_qs(parsed.query).get("resourcekey", [""])[0]
    if resource and not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", resource):
        raise ValueError("Invalid Drive resource key.")
    return id, resource


def read_drive(url, settings, session=None):
    id, resource = parse_drive_url(url)
    result = {
        "status": "awaiting_access",
        "documents": [],
        "errors": [],
        "message": "Drive link saved. Configure a Drive API key for publicly shared files or service-account access for shared private files.",
    }
    if not settings.drive_api_key and not settings.drive_service_account_json:
        return result
    headers = {}
    params = {"key": settings.drive_api_key} if settings.drive_api_key else {}
    if resource:
        headers["X-Goog-Drive-Resource-Keys"] = f"{id}/{resource}"
    if settings.drive_service_account_json:
        try:
            from google.auth.exceptions import GoogleAuthError
            from google.auth.transport.requests import Request
            from google.oauth2.service_account import Credentials

            info = json.loads(settings.drive_service_account_json)
            if info.get("token_uri") != "https://oauth2.googleapis.com/token":
                raise ValueError("Unexpected credential endpoint")
            credentials = Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/drive.readonly"]
            )
            auth_request = Request()
            credentials.refresh(
                lambda *args, **kwargs: auth_request(*args, **{**kwargs, "timeout": 8})
            )
            headers["Authorization"] = "Bearer " + credentials.token
            params = {}
        except (ValueError, KeyError, TypeError, GoogleAuthError):
            return {
                **result,
                "status": "error",
                "message": "Service-account credential setup failed. Existing memory is preserved.",
            }
    own_session = session is None
    session = session or httpx.Client(
        verify=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT), timeout=8, follow_redirects=False
    )
    deadline = time.monotonic() + 45
    requests = 0

    def get(path, query=None, binary=False):
        nonlocal requests
        requests += 1
        if requests > 45 or time.monotonic() > deadline:
            raise ValueError("Drive sync reached its bounded read limit; try a smaller folder.")
        with session.stream(
            "GET", ROOT + path, params={**params, **(query or {})}, headers=headers
        ) as response:
            if response.status_code in {401, 403, 404}:
                raise PermissionError(
                    "Drive access unavailable. Share the folder with the configured service account or enable public-link access."
                )
            if response.status_code != 200:
                raise ValueError(
                    f"Drive read failed ({response.status_code}); no content invented."
                )
            content = bytearray()
            for chunk in response.iter_bytes():
                if time.monotonic() > deadline:
                    raise ValueError("Drive sync elapsed-time limit reached; try a smaller folder.")
                content.extend(chunk)
                if len(content) > MAX_BYTES:
                    raise ValueError("File exceeds the 3 MB import limit.")
            return bytes(content) if binary else json.loads(content)

    try:
        root = get("/" + id, {"fields": "id,name,mimeType,size", "supportsAllDrives": "true"})
        queue = [(root, 0)]
        seen = set()
        folders = 0
        pages = 0
        while queue:
            file, depth = queue.pop(0)
            fid = file.get("id", "")
            if not re.fullmatch(r"[A-Za-z0-9_-]{10,200}", fid) or fid in seen:
                continue
            seen.add(fid)
            if file["mimeType"] == "application/vnd.google-apps.folder":
                folders += 1
                if depth >= 3 or folders > 10:
                    result["errors"].append(
                        {"name": file["name"], "message": "Folder traversal limit reached."}
                    )
                    continue
                token = None
                while True:
                    pages += 1
                    if pages > 10:
                        result["errors"].append(
                            {"name": file["name"], "message": "Pagination limit reached."}
                        )
                        break
                    listing = get(
                        "",
                        {
                            "q": f"'{fid}' in parents and trashed = false",
                            "fields": "nextPageToken,files(id,name,mimeType,size)",
                            "pageSize": 20,
                            "supportsAllDrives": "true",
                            "includeItemsFromAllDrives": "true",
                            **({"pageToken": token} if token else {}),
                        },
                    )
                    queue.extend((child, depth + 1) for child in listing.get("files", []))
                    token = listing.get("nextPageToken")
                    if not token:
                        break
                continue
            if len(result["documents"]) >= 20:
                result["errors"].append(
                    {"name": file["name"], "message": "Maximum 20 documents per sync."}
                )
                break
            try:
                if int(file.get("size", 0)) > MAX_BYTES:
                    raise ValueError("File exceeds 3 MB.")
                native = {
                    "application/vnd.google-apps.document": ("text/plain", ".txt"),
                    "application/vnd.google-apps.spreadsheet": (
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        ".xlsx",
                    ),
                    "application/vnd.google-apps.presentation": ("text/plain", ".txt"),
                }
                if file["mimeType"] in native:
                    mime, suffix = native[file["mimeType"]]
                    content = get("/" + fid + "/export", {"mimeType": mime}, True)
                    name = file["name"] + suffix
                else:
                    name = file["name"]
                    if not re.search(r"\.(pdf|docx|xlsx|txt|md|csv)$", name, re.IGNORECASE):
                        raise ValueError("Unsupported document type.")
                    content = get("/" + fid, {"alt": "media", "supportsAllDrives": "true"}, True)
                result["documents"].append(
                    {
                        "driveFileId": fid,
                        "name": name,
                        "text": extract_text(name, content),
                        "content": content,
                    }
                )
            except (ValueError, PermissionError, httpx.HTTPError, UnicodeError) as error:
                result["errors"].append(
                    {
                        "name": file["name"],
                        "message": str(error)
                        if not isinstance(error, httpx.HTTPError)
                        else "Drive network read failed.",
                    }
                )
        result["status"] = (
            "partial"
            if result["errors"] and result["documents"]
            else "error"
            if result["errors"]
            else "ready"
        )
        result["message"] = f"Read {len(result['documents'])} document(s)." + (
            " Some items need attention." if result["errors"] else ""
        )
    except (ValueError, PermissionError, httpx.HTTPError) as error:
        result["status"] = (
            "partial"
            if result["documents"]
            else "awaiting_access"
            if isinstance(error, PermissionError)
            else "error"
        )
        result["message"] = (
            str(error)
            if not isinstance(error, httpx.HTTPError)
            else "Drive network read failed. Existing memory is preserved."
        )
    finally:
        if own_session:
            session.close()
    return result
