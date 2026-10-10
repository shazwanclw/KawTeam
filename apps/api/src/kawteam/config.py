import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / ".env")


@dataclass
class Settings:
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    publishable_key: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    workspace: str = os.getenv("KAWTEAM_WORKSPACE_ID", "")
    database_secret: str = os.getenv("KAWTEAM_DATABASE_SECRET", "")
    session_secret: str = os.getenv("KAWTEAM_SESSION_SECRET", "")
    gateway_secret: str = os.getenv("KAWTEAM_GATEWAY_SECRET", "")
    tavily_key: str = os.getenv("TAVILY_API_KEY", "")
    gemini_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    drive_api_key: str = os.getenv("GOOGLE_DRIVE_API_KEY", "")
    drive_service_account_json: str = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON", "")
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    gmail_oauth_client_path: str = os.getenv("GMAIL_OAUTH_CLIENT_PATH", "")
    gmail_token_path: str = os.getenv("GMAIL_TOKEN_PATH", "")
    gmail_authorized_user_json: str = os.getenv("GMAIL_AUTHORIZED_USER_JSON", "")
    gmail_sender: str = os.getenv("GMAIL_SENDER", "")

    def validate(self):
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
