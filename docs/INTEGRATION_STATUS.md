# KawTeam integration status and next inputs

Updated 11 October 2026. Status is based on code/configuration and recorded checks, not on the presence of a key alone. No secrets are documented. See [current product specification](CURRENT_PRODUCT_SPEC.md).

## Verified and pending

| Service | Current evidence | Remaining work |
|---|---|---|
| Supabase | Configured; API reads saved projects; seven migrations applied; task/chat transactions tested | Deployment environment and final deployed checks |
| Gemini | `GEMINI_API_KEY` present; adapter succeeded; website chat returned and saved a Gemini reply after backend reload | Usage/error handling and deployed smoke test |
| Tavily | `TAVILY_API_KEY` present; real bounded supplier search returned five source candidates | Contact verification, broader sourcing and live liaison handoff |
| Google Drive | Adapter and persisted snapshot/retrieval exist; neither credential configured | Authorised folder, credential and actual ingestion test |
| WorkBuddy | Custom KawTeam entry exists in desktop MCP configuration; local stdio discovery/call passes; user reports connection okay | Independently captured WorkBuddy call, execution tools, task runner and website trigger |
| Gmail | `Downloads/Email API.json` exists; Desktop OAuth client structure and Google endpoints verified without exposing secrets | Sender consent/token, send/read adapter, durable reply processing and controlled-inbox test |
| Vercel | Next.js/FastAPI deployment roots prepared; no public deployment verified | Account/GitHub access, environment values, two deployments and deployed acceptance |

The backend reports AI/search as configured, email as controlled_demo_only and WorkBuddy execution as deferred. The last label reflects unimplemented execution, not a decision to abandon WorkBuddy: connection setup is now underway.

## Gemini and Tavily

Use `apps/api/.env`, not frontend public variables. Existing keys are already working; do not request replacement keys without an actual provider failure.

```dotenv
GEMINI_API_KEY=YOUR_PRIVATE_KEY
GEMINI_MODEL=gemini-3.5-flash-lite
TAVILY_API_KEY=YOUR_PRIVATE_KEY
```

The current configured model passed a live request. Restart/reload FastAPI after environment edits; configured status only means a value is loaded, so keep actual success/failure evidence separate. Provider usage is bounded; no paid upgrade or billing was enabled by the implementation.

Tavily is web discovery, not email or a complete social-platform API. Its free plan was checked as 1,000 credits/month with no card required; check [current provider pricing](https://www.tavily.com/pricing) before relying on quotas. Do not promise free unlimited use or reliable access to private/logged-in social content.

## Google Drive access

Provide an intended folder/document URL plus one supported server credential:

- `GOOGLE_DRIVE_API_KEY`: Drive API enabled, publicly accessible files only.
- `GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON`: full service-account JSON; share the private folder with its `client_email` as reader.

A Gemini key is not automatically Drive authorisation. A private folder URL alone is insufficient. No Google user sign-in flow or continuous Drive sync exists. Refresh currently reads a bounded snapshot on demand. Credentials stay on the backend.

## Gmail setup: client supplied; authorisation next

A dedicated Gmail inbox is recommended; personal Gmail can be authorised if chosen. Do not ask for its password. The user reports setup complete and supplied `Downloads/Email API.json`. The file is a Desktop-app (`installed`) OAuth client with client ID/secret and the expected Google authorisation/token endpoints. This verifies its format, not sender consent, enabled API or working mail access. The documented preparation is Google's local OAuth testing route:

1. Select/create a Google Cloud project and enable Gmail API.
2. Configure Google Auth Platform Branding with KawTeam.
3. Set Audience to External, keep Testing, and add the intended sender as a test user.
4. Create a Desktop-app OAuth client called KawTeam Local and download its JSON.
5. Keep the JSON outside the repository, for example Downloads, and provide only its local filename/path.

Then implement a local authorisation command, request only required send/read permissions, let the user consent in Google's browser page, and store credentials outside public source/client bundles. Tokens may need reauthorisation under Google's testing rules. Validate production authorisation separately; the initial local client is not a claim of a production-ready public OAuth service.

Source: [Google Gmail Python quickstart](https://developers.google.com/workspace/gmail/api/quickstart/python), [Gmail scopes](https://developers.google.com/workspace/gmail/api/auth/scopes).

No Gmail environment names, connection command or callback route are implemented yet. Do not invent one in setup instructions. Start with two or three controlled inboxes; test thread correlation, recipient validation, reply parsing, retry/uncertain-send handling and final confirmation. No supplier email has been sent during current verification.

## WorkBuddy direction and access

```text
Gemini -> website conversation / request understanding
WorkBuddy -> KawTeam MCP tools -> shared API / saved task state
Website -> WorkBuddy runner: still unresolved
```

WorkBuddy's Models API-key screen connects external models into WorkBuddy; it is not proof of an API allowing KawTeam to start its agent. Personal Google-sign-in credits do not establish Tencent Cloud Enterprise entitlements. Hosted Managed Agents access has not been obtained.

The user's actual UI path is Connectors -> MCP Server Management -> Add MCP. Its configuration file is `%USERPROFILE%/.workbuddy-ai/mcp.json`. Preserve unrelated entries. The one installed KawTeam tool is `kawteam_health`; it cannot search, read projects, send mail or update supplier tasks.

See [WorkBuddy integration guide](integration/workbuddy.md) for configuration and acceptance. The agent needs real scoped tools, limits, durable checkpoints and a verified start/resume mechanism. Do not install unofficial personal-account-to-API proxies or assume an undocumented endpoint to satisfy deployment.

## Deployment and submission

Target zero out-of-pocket hosting with two Vercel projects from the same repository: web root `apps/web`, API root `apps/api`, plus the existing Supabase project. Recheck eligibility and current limits before publishing; this is a target, not an unlimited-service guarantee.

Use server-only secrets, HTTPS API URL, `COOKIE_SECURE=true`, and the matching web/API gateway secret. Replace the local API URL on deployment. Vercel request functions cannot be assumed to run an always-on desktop WorkBuddy process or a continuous inbox-polling loop.

Remaining submission inputs: team/group name, campus branch, presentation PDF and final public application/repository verification. Original supplied deadline: 11 October 2026, 09:30 MYT, with a 30-minute buffer; operational cutoff 09:00, target 08:45. No submission receipt or final public URLs have been verified.
