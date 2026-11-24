# Security audit report: All In Capital triage (run-1)

## Run
- **Profile:** quick (one hunter wave, one coverage critic, one independent verifier per candidate). This is a **partial pass**, not complete coverage.
- **Scope:** `app/`, `public/`, `scripts/`, `evals/harness.py`, `evals/judge.py` of `/Users/patilprithvi/AllInCapital`.
- **Source ref:** `8033b59` plus the uncommitted Phase 6 and 7 changes (reviewed as they stood on 2026-11-24).
- **Budget:** 12 agent calls; 9 spent (3 hunters, 1 critic, 5 verifiers). Reconnaissance was done by the parent from first-hand knowledge of the build instead of four reconnaissance agents; this is a departure from the method and is disclosed here.
- **Execution:** source review only. No OS-enforced sandbox with every required control was available, so no target code was run; every check is a source check. Nothing was sent to a deployment or provider.
- **Prior runs:** none.
- **Deferred (quick profile, critic):** (1) concurrent writes to outreach records from request threads, the draft thread and the agent loop; (2) the Vercel and Postgres/Supabase storage modes and open local mode.

## Posture
No confirmed vulnerability. The HTTP boundary (Host/Origin gate, signed cookies, JSON-only POST, role map), output escaping, store-path validation, secret handling and outbound URLs held under review. Four source-grounded leads could not be confirmed without running code; each names a real boundary and was worth fixing.

## Confirmed findings
None.

## Needs validation

| Lead | Trace | Blocker | Status after the audit |
|---|---|---|---|
| Scheduling agent acts on any inbox email whose subject carries the `[AIC-<company>]` token, without checking the sender (`outreach/mailer-replies-sender-not-bound`) | `app/mailer.py` replies (IMAP subject search, no From check) → `app/outreach.py` tick/decide → booking or suppression | No sandbox to run a tick with a stub inbox; Gmail delivery of an outside sender to INBOX is a deployment fact | **Fixed** in `470292d`: replies must come from the founder (or the operator in test mode); proposed times must be a Tue/Thu afternoon slot 24 h–14 days ahead. Regression tests in `tests/test_phase7.py`. |
| `/api/eval` swaps `os.environ` and the shared stores process-wide (`eval-process-global-env-and-store-swap`) | `app/evalpoints.py` route/schedule_tick → `os.environ.clear()` window → `app/auth.py` role → `app/httpd.py` `_signed_in` | Showing the race needs execution; local-only endpoint | **Fixed** in `470292d`: route takes explicit settings and a throwaway store; schedule_tick holds the outreach lock; no environment change. Regression test added. |
| Session cookie key derived only from the role passwords (`auth-cookie-key-derived-only-from-role-passwords`) | `app/httpd.py` login → `app/auth.py` `_secret`/`_sign`/`role` | Password entropy is a deployment secret | **Fixed** in `470292d`: cookies are signed with `SESSION_SECRET` (random, required on Vercel). Regression test added. |
| Web-search evidence URL rendered into an href with no scheme check (`public/app.js:src:web-evidence-href-scheme-unvalidated`) | `app/tavily.py` `_search` → read evidence → `GET /api/read` → `public/app.js` `src()` | Whether Tavily can return a non-http(s) URL; Chrome's handling of `javascript:` with `target=_blank` | **Fixed** in `470292d`: only http/https URLs are kept server-side and linked client-side. Regression test added. |

## Rejected
- `read/verify-quote-not-bound-to-claim`: the founder already writes the deck the quotes come from, so binding claim text to its quote removes no capability; the read is advisory and shows each quote. Kept as a read-quality note.

## Hardening notes (not findings)
- `app/gcal.py`, `evals/judge.py` and `app/calendar_ics.py` follow redirects on keyed or secret-bearing requests to fixed provider hosts; use the `_NoRedirect` opener.
- `scripts/set_env.py` rejects only `\n`; reject any value that `splitlines()` splits. `app/checks.py` cuts `.env` values at ` #`.
- `scripts/set_env.py` and `scripts/google_auth.py` write `.env` before `chmod 600`; create with mode 600.
- `scripts/google_auth.py` picks the newest `client_secret_*.json` in Downloads automatically; add PKCE and prefer an explicit path.
- Online login guessing has a 1 s delay per attempt but no lockout; stateless cookies stay valid up to 7 days after logout.
- `public/motion.js` writes a static company name with `innerHTML` (now noted for consistency).
- `app/read.py` gates drop when their synthetic quote is missing from the form text; prefer failing closed.
- `app/mailer.py` skips own messages by Message-ID substring; compare against stored sent IDs.

## Positive patterns
Constant-time cookie and password checks; role inside the MAC; Host and Origin checked before any work; JSON-only POST with SameSite=Strict cookies; FileStore path validation plus id allowlists; every interpolated string escaped; keys only in headers with no redirects on the main clients; test mode and allowlist enforced before any SMTP connection.

## Coverage
10 ledger units: 3 covered (body and store limits, DOM escaping, secrets and the OAuth script), 5 candidate (the four leads above plus the rejected quote-check claim), 2 deferred by the quick-profile critic. The ledger (`coverage-ledger.json`) and findings (`findings.json`) both pass the skill's validators.
