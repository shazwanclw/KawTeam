"""
Application configuration for KawTeam backend.

Reads environment variables (with dotenv fallback) and exposes them
through a single ``Settings`` dataclass. Call ``settings.validate()``
at startup to fail fast on missing or malformed credentials.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / ".env")


@dataclass
class Settings:
    """Central configuration read from environment variables.

    All fields have safe empty-string defaults so the object can always
    be constructed; call :meth:`validate` to enforce the required subset
    before the app starts serving requests.
    """

    # Supabase connection
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    publishable_key: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    workspace: str = os.getenv("KAWTEAM_WORKSPACE_ID", "")

    # Server secrets — used for session tokens, database auth and gateway HMAC
    database_secret: str = os.getenv("KAWTEAM_DATABASE_SECRET", "")
    session_secret: str = os.getenv("KAWTEAM_SESSION_SECRET", "")
    gateway_secret: str = os.getenv("KAWTEAM_GATEWAY_SECRET", "")

    # AI provider keys
    tavily_key: str = os.getenv("TAVILY_API_KEY", "")
    gemini_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    # Google Drive integration (optional)
    drive_api_key: str = os.getenv("GOOGLE_DRIVE_API_KEY", "")
    drive_service_account_json: str = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON", "")

    # Cookie settings
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"

    # Gmail integration (optional — for supplier outreach)
    gmail_oauth_client_path: str = os.getenv("GMAIL_OAUTH_CLIENT_PATH", "")
    gmail_token_path: str = os.getenv("GMAIL_TOKEN_PATH", "")
    gmail_authorized_user_json: str = os.getenv("GMAIL_AUTHORIZED_USER_JSON", "")
    gmail_sender: str = os.getenv("GMAIL_SENDER", "")

    def validate(self) -> None:
        """Raise ``RuntimeError`` if essential configuration is missing.

        Checks that Supabase credentials are present and that each server
        secret meets the minimum length (32 characters) to resist brute
        force attacks on HMAC tokens.
        """
        if (
            not self.supabase_url.startswith("https://")
            or not self.publishable_key
            or not self.workspace
        ):
            raise RuntimeError("Configure Supabase URL, publishable key and workspace ID.")
        if min(len(self.database_secret), len(self.session_secret), len(self.gateway_secret)) < 32:
            raise RuntimeError(
                "Configure the three server secrets with at least 32 characters each."
            )
