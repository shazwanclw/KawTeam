"""Local Desktop OAuth consent. Run from apps/api with python -m kawteam.gmail_auth."""

import argparse
import json
import ssl

import truststore
from google_auth_oauthlib.flow import InstalledAppFlow

from .config import Settings
from .gmail import DEFAULT_TOKEN_PATH, SCOPES, Gmail, email_address, store_token


def main():
    parser = argparse.ArgumentParser(
        description="Connect the KawTeam Gmail sender using Google consent."
    )
    parser.add_argument("--client", default=Settings().gmail_oauth_client_path)
    parser.add_argument("--sender", default=Settings().gmail_sender)
    parser.add_argument("--token", default=Settings().gmail_token_path or str(DEFAULT_TOKEN_PATH))
    args = parser.parse_args()
    sender = email_address(args.sender)
    truststore.inject_into_ssl()
    ssl.create_default_context()  # Initialise the system certificate store before OAuth requests.
    flow = InstalledAppFlow.from_client_secrets_file(
        args.client, SCOPES, autogenerate_code_verifier=True
    )
    credentials = flow.run_local_server(
        host="127.0.0.1",
        port=0,
        timeout_seconds=600,
        open_browser=True,
        authorization_prompt_message="Google consent opened. Select the configured sender and grant send/read-only access.",
        success_message="Google consent received. You may close this tab.",
        access_type="offline",
        prompt="consent",
        login_hint=sender,
    )
    if credentials is None or not credentials.refresh_token:
        raise ValueError("Google consent did not return offline refresh permission. Try again.")
    data = json.loads(credentials.to_json())
    # Verify account identity before saving a token for later email actions.
    profile = Gmail(sender=sender, credentials=data).profile()
    store_token(args.token, data)
    print(f"Gmail connected: {profile['sender']}. Token stored locally; no email was sent.")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 - CLI boundary must redact OAuth codes/URLs.
        # OAuth responses can contain sensitive URLs/codes. Never print the raw exception.
        print(
            f"Gmail authorisation did not finish ({type(error).__name__}). Check Google consent/test users and retry."
        )
        raise SystemExit(1) from None
