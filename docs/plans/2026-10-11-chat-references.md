# Chat references and meaningful project names

Implement the user's requested composer changes within the existing compact design. Preserve explicit event names. Otherwise generate a concise sourcing/project label, never the full request. Keep deterministic naming available without an AI connection.

Show a Drive-link icon when there is no selected project or the project lacks a saved Drive source. Stage an optional link before submitting the request. Always offer a file attachment icon with a removable filename chip. Support the existing readable document formats (PDF, DOCX, XLSX, TXT, Markdown, CSV), up to 3 MB total. Validate before saving or running actions.

Send attached files through multipart chat. Save extracted references with task scope before the assistant reads them; keep their facts out of unrelated project tasks. Drive context remains shared project memory and requires existing access credentials. Retry identities cover the message, link and file contents to prevent duplicate tasks or changed references under the same request.

Verify concise naming, explicit event preservation, first-chat references, task isolation, invalid uploads and retries with backend tests. Verify icon visibility, staged Drive link, attachment removal and multipart submission through an isolated browser check. Update current product documentation.

The hamburger stays at a fixed screen position and toggles the sidebar; separate close buttons are removed. Failsafe is shown only when there are unresolved project issues, with All Task as the fallback when the last issue resolves.

Verified: 149 backend tests, Ruff, 45 frontend tests, TypeScript and ESLint; isolated reference and compact-chat browser checks passed. Tests intercepted browser gateway calls. Renamed the one existing automatically prompt-named project to T-shirt Sourcing through the saved backend. No supplier emails sent for this update.
