# Authentication Integration — FeelY account backend

Status: Markdown integration brief only. No app/backend changes or loop execution authorized by this document. The owner starts the Claude–Codex loop from Android Studio after preparation.

## Source of truth
Owner supplied https://github.com/Lunatreon/FeelY and app/api/routes/auth.py. Read from the repository default branch (main) on 2026-10-03.

Inspected:
- app/api/routes/auth.py — blob c43705e840c469b7f5ab07b82563187d3dd936f2
- app/schemas/auth.py — blob 1a1d2fe7ce0568b6613fc86c77271ab1e0700074
- app/schemas/user.py — blob f7f067c8082db82917ad4b23cdde783489f45343
- app/api/router.py — blob 16706b331e47ff330159b635ba54e4d13099fbe3
- app/main.py — blob 7e80fb15b025848dd8ca4851198cb1a4e3006212

These are file blob identifiers, not a pinned repository commit. Recheck related files at one recorded commit before implementation. Repository access does not establish a deployed endpoint, working email delivery, enabled Google login, or mobile client configuration.

## API base — owner-confirmed, not independently verified live
The owner has confirmed the API base as `https://api.feel-y.com/api/v1`. Treat this as the configured value, not as proof the deployment is reachable: a prior live check against it returned HTTP 403 / error 1010. Do not assume deployed settings are verified, and implement genuine network-error/unexpected-response handling rather than assuming success. The account milestone's `FEELY_API_BASE` environment variable carries this value into the build (see agent/milestones.py); if that variable is absent the controller blocks the account milestone rather than guessing a host.

## Recheck of docs/ANDROID_AND_TERMS.md — could not be independently performed (2026-10-06)
This preparation session had no authenticated access to github.com/Lunatreon/FeelY: `gh` is not installed in this environment, and unauthenticated fetches to the repository (github.com, raw.githubusercontent.com, and api.github.com) all returned HTTP 404, consistent with a private repository. The file could not be re-read here.

The owner separately reported that `docs/ANDROID_AND_TERMS.md` in that repository states: versioned acceptance now exists via a `terms_acceptances` store, but access enforcement on authenticated routes and recording of the presented language remain gaps in the inspected implementation. Record this as an **owner-reported, not independently confirmed** finding. Do not implement against it as settled fact; the account milestone's brief treats it as unverified and asks the implementing agent to say so rather than build around an assumed server contract. Whoever next has authenticated repository access should re-read that file directly and update this section with a verified quote or correction.

## Confirmed contract
Auth routes are mounted below /auth, itself below settings.api_v1_prefix. Do not hard-code /api/v1 or infer the deployed host from the repository URL — use the owner-confirmed base above instead of a second guess.

| Route relative to auth prefix | Input / behavior |
| --- | --- |
| POST /login | JSON email_or_username and password; returns access_token and token_type=bearer. Login may reject unverified email with 403. |
| POST /register | JSON email, username, password; optional website honeypot and captcha_token. Returns UserRead (201), not an access token. Verification depends on backend settings. |
| GET /captcha/config | Exposes enabled/provider/site_key/action. Respect configured registration verification; do not bypass it. |
| GET /google/config | Exposes enabled and client_id. This alone does not prove Android credential compatibility. |
| POST /google | JSON credential, verified by the server; returns Token. Account linking can return 409. |
| POST /email-verification/request | JSON email; generic response avoids exposing whether an account exists. |
| POST /email-verification/confirm | JSON token; rejects invalid/expired links. |
| POST /password-reset/request | JSON email; can return 503 when delivery is unconfigured and 429 for rate limits. |
| POST /password-reset/confirm | JSON token and new_password; successful reset does not return an access token. |

Login identifiers: 3–320 characters. Passwords: 8–128 characters in the inspected schema. Registration usernames: 3–80 characters using letters, digits, underscore, period, or hyphen. Match server validation rather than inventing a competing policy.

## Agent implementation brief
Use this backend as the integration reference instead of creating a separate account system. Inspect security/token expiry, authenticated-user routes, tests, deployment documentation, and mobile credential support before choosing a client design. Do not import journals or personal-map data merely because the backend contains them.

Implement genuine success/error/loading/cancel states, token expiry handling, sign-out, recovery, and verification behavior. Do not assume a refresh, revocation, or logout endpoint: none appears in the inspected auth route file. Verify the rest of the API. Store tokens using an appropriate platform-backed strategy, never plaintext logs; do not store passwords. Use HTTPS for deployed endpoints and a deliberate local-test configuration.

Localize user-facing outcomes into German and English. Existing server detail strings are English; map known outcomes to localized messages without logging sensitive response contents. Unexpected errors should remain truthful and non-sensitive. Respect rate limits instead of retrying indefinitely.

Google login should be wired only after credential type/audience/client registration is verified. Registration with enabled CAPTCHA needs a supported user-completed flow. Never disable verification to make automation pass.

## AGB acceptance — required gap investigation
No versioned AGB acceptance field or endpoint was found in these inspected auth routes and request/response schemas. This is not a claim about the entire repository. Search the remaining code and migrations first.

The full companion requires affirmative acceptance of current localized terms, with account, version, presented language, and timestamp; valid prior acceptance avoids unnecessary repeated prompts. A checkbox stored only on one phone cannot fulfill the cross-device requirement. Determine the actual backend contract or propose a reviewed migration/API change as a separately scoped task. Do not add unsupported JSON fields and assume they were saved.

Terms acceptance must gate access appropriately, including a returning login. Keep privacy information and optional choices distinct. Draft legal text is not approved launch content.

## Prerequisites for end-to-end verification
- API base URL confirmed (`https://api.feel-y.com/api/v1`); live reachability from a build/test environment is still unverified (403/error 1010 on a prior check) and must be supplied to the controller as `FEELY_API_BASE` before the account milestone will start.
- Non-production test environment/account; do not request secrets in chat or put them in Markdown.
- Email delivery/verification and password-reset test path.
- Google Android client configuration if Google is included in release.
- Confirmed terms-acceptance API and approved DE/EN legal content.

The agents can implement the adapter, contract tests, and mock-server tests while environment details are unresolved. Mock tests do not establish live integration success. Keep missing deployment/legal prerequisites visible in the launch checklist.

## Scope and execution ownership
The current assistant co-creates Markdown and provides launch instructions only. Do not interpret an updated brief as permission for the assistant to launch Claude or change implementation code. The existing loop remains stopped.

The owner starts the automated build. The loop must first support the agreed multi-task sequence and updated QA. App agents currently cannot edit build files or orchestration; any required setup/backend work must have its own explicit scope rather than quietly bypassing those controls. Backend production changes, deployment, purchases, and credential provisioning are not authorized here.
