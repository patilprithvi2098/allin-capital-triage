# Brief: All In Capital application triage (MESA Term 2, Case 3)

## Stage 0: agreed 2026-11-17
Problem: Riya and Kushal have a manual triage problem. Riya spends 19+ working days a quarter on applications that usually do not pass, and Kushal has no measured way to know how far he can trust a machine to do that work.
Core verb: make evidence-based application recommendations happen for Kushal when new companies apply, with a source for every claim, gaps named, corrections learned, and proof of how far the result can be trusted.
Users: Riya runs the weekly batch and corrects scores (one line of why). Kushal reads the reads and decides; Aditya joins only deeptech second calls.
Working means: Kushal can trust the output without redoing Riya's research (score per criterion, why, source, missing, confidence, corrections applied, take-the-call or not, backtest reliability). For the judge: the chain input, research, sources, score, gaps, recommendation, corrections, trust report is demonstrable, including edge cases and missing information.
Run mode: the tool runs alongside Riya's manual triage until measured evidence shows where it can and cannot be trusted. Carry-over: "agrees with Riya" must not be the only stop signal, because Riya's own sense of fit has drifted (see Pre-Build Decisions).

## Coverage map (agreed)
| Brief says | Build covers it | Status |
|---|---|---|
| whole pile, a read on each | Batch run, one read per application | Covered |
| scores against thesis, criterion by criterion | Written-thesis score and observed-thesis score side by side | Covered |
| source behind every claim | Every claim linked to a source | Covered |
| what it couldn't find | Gap list plus confidence; not-found is not the same as does-not-exist | Covered |
| whether we should take the call | Recommendation, never a decision | Covered |
| go find it across the internet | Public search with a recorded trail, cutoff date per company | Thin (allowed sources open) |
| correction should count next time | Stored correction with one-line reason, reused on similar companies | Covered |
| call booked | Tentative Tue/Thu 30-min hold; founder invite only after Kushal approves; Aditya for deeptech | Thin (test invites to own address only) |
| run against past deals, disagree: us or it | Backtest with held-out memos, memo reasoning stripped, disagreement report | Covered (about 4-6 test cases, stated honestly) |
| trust in writing, in numbers, agreed in advance | Eval suite with thresholds and severities set before running | Covered |
| portfolio conflict (meeting notes) | Overlap flag by what the company does; unverifiable means hold | Covered |
| Deciding or auto-rejecting | None | Excluded (case forbids) |
| Re-opening Ledgerly and older passes | None | Excluded (no data) |
| Emails to real founders | None until operator approves | Excluded |

## Known limits to state in the trust report
- Memos carry no application dates, so a hindsight cutoff for web search cannot be exact.
- The post-call founder assessment in memos must not be fed to the tool.
- Twelve memos can find where the tool breaks, not prove reliability.

## Nine Checks verdict (2026-11-17)
Resolve uncertainties first, then build. 01 YES, 02 YES, 03 UNCERTAIN (public founder background, fund thesis and portfolio: feasibility test on the 10 applicants), 04 YES, 05 YES, 08 YES, 06 YES (Kushal sees every outcome; doubtful conflict = hold), 07 YES, 09 UNCERTAIN (nobody owns the thesis; default Kushal owns, Riya proposes). Open: the 19-day baseline vs 11 applications a week in the notes.
Killed: auto-reject, rewriting the thesis to match decisions, LinkedIn founder scoring, auto-invite founders.

## Pre-Build Decisions (2026-11-17)
- End goal: partners spend time only on companies that deserve a call; no good company lost, no conflict missed; Riya's days freed.
- M1 primary: Riya's review time per application from ~30 min (confirm) to 5 min or less in 4 weeks, only while guardrails hold.
- Guardrails (critical): G1 missed portfolio conflict; G2 unsourced or invented claim; G3 "don't take the call" on a good company without evidence.
- Kill: a critical guardrail fails twice; Riya corrects over half of reads after 4 weeks; reviewing takes longer than manual. Fallback: Riya's manual triage (never stopped). Decider: Kushal.
- Stop running alongside Riya only on agreement with the fund's recorded decisions plus stable explainable error patterns, not agreement with Riya alone.

## Build Requirements Brief (agreed 2026-11-18)
Users: Riya loads the weekly batch, writes her own Take Call / Pass first, then sees the tool's read and marks Agree or Correct with a one-line reason. Kushal opens it Monday afternoon, reads the evidence, gaps and trust numbers, and leaves with Yes / No / Hold per application, tentative Tue/Thu holds, and an audit log of his corrections. Tool recommends; Kushal decides.

| # | Requirement (testable) | Coverage line | Serves |
|---|---|---|---|
| 1 | Reconstruct the thesis from public sources and memos: Written and Observed versions, gap shown, versioned, sourced, owner Kushal. All criteria come from here, none hard-coded | portfolio/thesis, score per criterion | M1, G3 |
| 2 | Read the whole weekly batch in one run | whole pile | M1 |
| 3 | Score every application against both theses side by side; state which was used | criterion by criterion | G3 |
| 4 | Founder quality scored separately from path to market | criterion by criterion | G3 |
| 5 | Every material claim has a source (link or deck page) that resolves and supports it; pass/fail check | source behind every claim | G2 |
| 6 | Public search outside the deck with a recorded trail and a cutoff date per company | go find it | M1 |
| 7 | "Not Found" is never treated as "does not exist" | what it couldn't find | G2, G3 |
| 8 | Two rules. Founder-supplied fact missing (e.g. repeat rate on a D2C form): that criterion's score drops. Externally unfindable fact: confidence drops and score is capped, not zeroed | what it couldn't find | G3 |
| 9 | Overlap with a portfolio company judged by what it does (problem, buyer, workflow); overlap or unverifiable portfolio = Hold and flag, Aditya's default-no | portfolio conflict | G1 |
| 10 | Riya's own call is locked in before the tool's read is shown | run alongside Riya | trust data |
| 11 | Correction memory: after a correction, the next similar application shows "Correction #N applied" and its score moves toward the correction | correction counts next time | repeat errors |
| 12 | Recommendation only: no auto-approve, no auto-reject | take the call | governance |
| 13 | After Kushal approves Take Call, tool proposes Tue/Thu 30-min slots (Aditya for deeptech); hold placed only on his click; founder invite stays in draft | call booked | M1 |
| 14 | Blind backtest on held-out memos with decisions, reasoning and post-call assessment stripped, search cut off by date | run against past deals | trust |
| 15 | Disagreement report: each disagreement marked "we were wrong" or "the tool was wrong" | us or it | trust |
| 16 | Eval suite (input, expected, assertion, severity) with thresholds agreed in advance, run by a harness, judged by a different model from the one that wrote the read | trust in numbers in advance | G1-G3 |

First screen: one complete application. Banner: Take call / Do not / Hold, Confidence, Trust display (held-out cases tested, disagreements, unverifiable parts, never a bare "10/12"), Riya's independent call. Below: both scores with founder and path to market separate, why, evidence with links, missing info, conflict check. Buttons: Approve & propose hold | Pass | Flag missing info for Riya (internal task, no founder contact) | Log correction.

Exclusions and the cost of leaving each out:
1. No auto-approve or auto-reject: Kushal clicks on every application; no review volume is removed.
2. No outbound founder emails or invites: Kushal sends each approved invite himself; scheduling busywork shrinks but does not vanish.
3. No logins or LinkedIn: deep founder graphs behind login walls stay unreached; those become "Not Found" and Riya checks edge cases by hand.
4. Ledgerly out of the backtest (no memo in the pack): one fewer data point.
5. Riya not replaced yet: no net labour saving until trust is shown.

Judged by: week 1 sourced claims, founder-background found rate, gaps shown (5, 6, 7); week 4 M1 (13, 2); critical stops G1 (9), G2 (5, 7), G3 (3, 4, 8); trust test (14, 15, 16).

## Council changes (2026-11-18, kept only where they fit the case and the agreed brief)
Applied:
- Build order: (1) founder-findability test by hand on the 10 applicants (count usable public backgrounds; if under half, founder criteria are mostly "Not Found" and the design says so); (2) one application read end to end with a source on every claim, Not Found labels and the Hold rule; (3) Riya's call first, then the tool's read; (4) portfolio check; (5) all 10 applications; (6) backtest; (7) calendar last, kept thin (req 13 stays).
- Req 1: the Observed thesis is a hypothesis Kushal approves, never authors. Versioning and owner stay.
- Req 3 stays: a score per criterion, no single weighted overall number.
- Req 9: the portfolio list is found from public sources only (the case forbids asking for it). If it cannot be found, say so and state the cost: every application becomes a Hold.
- Req 11 additions: each applied correction shows why it matched ("similar because ..."); Riya can reject the match; a cap on how far one correction moves a score; a regression check that earlier eval cases still pass after a correction.
- Req 14 and 15: report counts with the sample size, never percentages, with an explicit leakage warning (memos undated, so search cannot be cut off exactly; post-investment press for invested companies; memo text can leak its verdict). State that the 6 passes are survivorship-skewed and that thesis-building and testing must use separate memos (hold out before building).
- Req 16: start with about 15 hand-written cases (planted MeetRecord-style overlap, a fake claim, a good company with no evidence) plus human-labelled gold cases; the harness, pre-agreed thresholds and the cross-model judge are still delivered.
- M1: "5 minutes or less" is our proposal, not the case's. Time Riya on real applications before claiming it.
- New: privacy. Memos and founder data sent to third-party model or search providers are named in the trust report; test data stays free of anything beyond the case files.
- New: "trust" has pass/fail definitions per named failure mode, agreed before running.
- Assumption recorded: whether Kushal accepts any written thesis is unknown (the case gives only files); the thesis is shown as a hypothesis for him to correct.
Ignored (deviates from the case or brief): cutting the calendar, dropping per-criterion scores, replacing the harness and judge, asking Kushal for the portfolio list, resurfacing old passes, outbound sourcing, warm intros.

## Mentor changes (2026-11-18, from the operator's mentor; these override earlier lines where they conflict)
Reversals of earlier decisions:
- Emails and meeting scheduling are IN scope (was Exclusion 2 and req 13). After Kushal approves Take Call, the system drafts and sends "we'd like to schedule a meeting, does this time work?" through Resend, and a scheduling agent proposes Tue/Thu 30-minute slots (Aditya for deeptech) and handles the reply. Safeguards kept: Kushal approves every outcome before anything is sent; during build and test every send goes only to the operator's own address (recipient allowlist), real founder addresses only after the operator turns that on.
- A points-based scoring matrix with one final score is IN (reverses the council edit that dropped a single overall score). Points per criterion, the sum is the score, per-criterion detail stays visible. Pass/fail recommendation derives from the score plus the gates (overlap = Hold). Weights and thresholds are proposals until Kushal approves and the backtest and evals tune them.
- Reverse API Engineer is optional. It is a more complicated scraper; whatever builds the scraper, the loop cap and stop rule must be defined.
Added:
- Source map required, one row per scoring criterion: what information is needed; the pages and sources a person would use; which are free or have a free route; a scraper only if no free channel exists; loop cap and stop rule ("I have what I need" defined per field). LinkedIn is named as not scalable and stays excluded (login wall); find other sources.
- Competition definition: criteria for "who counts as a competitor" are given to the system explicitly, not left to the model.
- Two feedback loops: (1) corrections to scores and recommendations by Riya or Kushal; (2) corrections to email drafts.
- Evals: identify every point where AI uses judgment, one test group per point; about 300 test cases including many dummy companies; a harness runs them and reports passed/failed; root-cause each failure, fix, rerun; production only after the suite passes. Hard rules in code are not the risk; AI judgment points are.
- Lecture 7 deck (uploaded after the operator's last check) to be read when shared; the email and scheduling steps follow it.
Interpretation notes: "Priya or Ruchan" read as Riya or Kushal; "RIA" read as Reverse API Engineer; "Tably" probably Tavily (web search API with a free tier), to confirm.

## Confirmations and lecture 7 (Evals) adopted (2026-11-18)
- Confirmed by the operator: web search is Tavily; email is Resend (test mode: operator's address only); the 100-point matrix weights are approved as proposed (founder quality 25, path to market 20, evidence quality 20, defensibility 15, sector fit 10, capital fit 10; gates outside the points).
- Test case shape (lecture 7): Input, Expected behaviour, Assertion (HARD = code checks, SOFT = a judge checks a short list that must all hold), Severity (Critical = kill, High = counts against the pass-rate threshold, Low = logged). Kill criteria are written before the test cases. Test cases are drafted with the lecture's partition prompt, reviewed by a human, then run by a harness over HTTP only.
- Harness self-checks: break it on purpose (a forced wrong output must be caught), run it twice (same verdict), include a test that should fail. Judge model is a different family from the agent's model; 5 to 10 percent of results graded blind by a person; every judge-vs-human mismatch logged.
- Decision tables to write, one per judgment point: sector fit and gates, source sufficiency and loop cap, founder and criterion scoring, portfolio overlap, correction relevance and conflict, correction worth storing, reply meaning (not interested lands on a suppression list; ambiguous goes to a human), scheduling (confirm, counter once, escalate at the cap, timeout boundary), tool failures (calendar timeout retried, email failure skipped, permanent calendar error aborts, record update failing after a booking escalates).
- Adversarial rows: instructions hidden in deck text, form answers or fetched pages must not change a score, recommendation or send.
- Draft kill criteria (proposed, operator to confirm): K1 a planted portfolio overlap is not flagged; K2 a claim reaches a read with no source or a source that does not contain it; K3 an externally unfindable fact is scored as a negative fact; K4 any email or invite goes out without Kushal's approval, or to an address outside the test allowlist; K5 text inside a deck, form or fetched page changes a score, recommendation or send; K6 any application is auto-rejected or auto-advanced; K7 the scheduling loop runs past its cap or a timeout escalates late; K8 a "not interested" reply is not suppressed from further contact.
- Source note: a LinkedIn post screenshot (author not visible) was supplied as an All In Capital post about investor thesis (check size, fund lifecycle, portfolio construction, sector discipline, stage focus). Treated as unverified and attributed to the operator; its statistics are not used. Its five dimensions inform the gates: stage, cheque-size fit, deployment status, similar bets already in the portfolio.

## Mentor review of the screens (2026-11-18) — overrides earlier lines where they conflict
- Recommendation is binary: **Go** (take the call) or **No-go** (reject), each with "why yes" and "why no" reasons and sources. No Hold. Score at or above the benchmark = Go; below = No-go. Missing information counts against reaching the benchmark. Gates (portfolio overlap, outside the areas, stage) become No-go reasons. Benchmark is set from the backtest and evals.
- Riya is the human in the loop. Her screen has only two buttons (Go / No-go) and a free-text reason, required when her call differs from the recommendation. A disagreement with its reason is the signal for feedback loop 1.
- When the final call is Go (she agrees with Go, or overrides a No-go), a draft email is generated automatically. Screen 2: Riya edits and sends; her edits are feedback loop 2.
- After send, the agent runs on its own: reads replies, follows up when the founder has not replied within X days, finds new slots on the calendar when asked, counter-proposes until a time is agreed, and books the meeting on the calendar. Riya takes no action; she gets a read-only dashboard of status and email history.
- Every criterion keeps its reasons and sources so Riya can validate them.
- Trust report stays (required for this case).
- Declutter: Riya sees only what she needs, mainly the why. Deck-vs-form differences and evidence become one table.
- Two separate views behind a login: Riya and Kushal, each showing only what that person needs. A role matrix to be drawn up.
Open questions raised by this review (operator to decide):
1. Riya's blind call (req 10): the mentor's flow has her agree or disagree after seeing the recommendation. Keep the blind-first step or drop it?
2. The case says Kushal sees every outcome before anything is decided; the mentor's flow lets Riya decide and send. How does Kushal see outcomes first?
3. Calendar: finding free slots and booking needs real calendar access (for example Google Calendar). Which calendar, and test on the operator's own?
4. Scheduling loop: the lecture asks for a cap that escalates; the mentor says loop until agreed. Keep a cap that hands back to Riya?
Resolved by the operator, in line with the mentor (2026-11-18):
1. No blind call. Riya sees the recommendation and clicks Go or No-go; a reason is required when she disagrees. (Anchoring risk is named in the trust report.)
2. Kushal has his own login with a read-only view of every outcome (recommendation, Riya's call, her reason, meeting status), the thesis approvals and the trust report. He takes no action in the flow; nothing waits for him. Recorded deviation: the case text says Kushal sees outcomes "before anything is decided"; here he sees them as they happen.
3. Calendar: Google Calendar on the operator's own account in test mode; the agent reads free slots and books the meeting there.
4. Scheduling runs until a time is agreed and booked, with follow-ups every 3 days when the founder is silent. A technical safety stop (10 rounds) exists only to prevent a runaway loop and is tested in the evals; it is not a step for Riya.
Superseded by this: Hold as a recommendation; Riya's locked blind call; Kushal approving sends; Flag missing info, Correct a score and Pass buttons on Riya's screen.

## Addition beyond the case: Kushal's portfolio dashboard (operator, 2026-11-18)
Not asked for by the case and not judged by it; kept off the critical path as its own phase.
- Outcomes table rows open a drop-down brief (what it does, stage, raise, founders, recommendation with top reasons).
- Sector-wise fund distribution: donut with the top 5 sectors plus Other (a pie past 5 slices is unreadable).
- Past investments: portfolio table (invested, current valuation, multiple, revenue trend, last update) using **fictional company names**, never the real portfolio: invented figures about real companies under a real fund's name would mislead.
- Company health: Healthy / Watch / At risk with the reason, computed by rules in code from the sample facts (runway, growth, burn, days since last update); a simulator moves the numbers so it looks live.
- Money: total invested, cash in the bank, incoming capital, free to deploy. Anchored to public facts where they exist (Fund I about $11 M deployed; Fund II INR 85 Cr first close of a INR 200 Cr target, March 2025); bank balance and capital calls are sample figures.
- Evals: rule tests for the health score; the brief reuses the read.
- On-screen labels (operator decision, 2026-11-18): nothing is shown as "simulated" or "sample". The companies stay fictional names, and this file plus the seed data record that the figures are invented. Public figures keep their source and date on screen.
