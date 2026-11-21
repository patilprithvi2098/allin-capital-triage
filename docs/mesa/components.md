# Components map and architecture check
Image: design/components-map.png (source: design/build_map.py, rendered in Chrome). Static, numbered arrows 1 to 21 give the order; dashed arrows are test and feedback paths. Generic: applicants enter, no individual company is shown.

## Actor x Stage matrix
| Actor / system | Trigger | Input | Context | Processing | Output |
|---|---|---|---|---|---|
| Applicants (people) | Fill the public form or arrive by warm intro | Deck text, form answers | | | |
| Riya (people) | Weekly intake | Loads the batch; logs her own Take call / Pass first | | | Agree or Correct with a one-line why |
| Intake and checks (system) | Batch loaded | Parses deck and form | | Code compares numbers, team, funding between deck and form; checks sector and stage labels | Flags for the AI to judge |
| Source fetchers (system) | Application stored | | Fund site and portfolio, press and web search (Tavily), company site, regulator pages, competitor search | Loop cap and stop rule per field; Not Found recorded; no LinkedIn | Claims with sources, Not Found list |
| Thesis store (Supabase) | Memos and public sources | | Written and Observed thesis, versioned | Kushal approves changes | Criteria the AI scores against |
| AI section (Claude) | Evidence ready | | Thesis, evidence, corrections | 13 judgment points (thesis reconstruction, sector fit, founder quality, path to market, source supports claim, deck-vs-form materiality, competitors, missing-data type, portfolio overlap, recommendation, correction match, email draft, reply classification) | Per-criterion judgments with sources and confidence |
| Scoring matrix (rules in code) | AI judgments in | | Points per criterion (total 100) and gates | Sums points; overlap = Hold; outside areas and stage mismatch = flag | Score, gates, recommendation |
| Review screen (frontend) | Read ready | | Trust numbers from the eval report | | Recommendation, score, evidence, gaps, confidence, Riya's call, trust panel |
| Kushal (red) | Always, on every outcome | | Riya's notes, trust panel | Yes, No or Hold; Hold forced on portfolio overlap, low confidence, stage mismatch | Decision; corrections |
| Email agent (AI) + Resend | Kushal says Yes, then approves send | | | Drafts "we'd like to schedule a meeting, does this time work?"; sends in test mode to the operator's address only | Sent email |
| Calendar and reply handling | Email sent | Founder reply | Tue/Thu 30-minute slots, Aditya for deeptech | AI classifies the reply (yes, no, other time); proposes next slot | Held slot, back to Kushal |
| Corrections store (Supabase) | Any correction | Score, recommendation and email-draft corrections with the one-line why | | Retrieval for similar companies, capped, regression check | Corrections applied to later reads |
| Eval harness | Before release and after each change | About 300 cases incl. dummy companies; held-out memos | | A different model judges; pass and fail report; root cause, fix, rerun | Trust numbers, threshold tuning |

Red-border escalations: Kushal reviews every outcome (no auto-approve, no auto-reject); portfolio overlap or unverifiable portfolio forces Hold; low confidence forces Hold; stage mismatch forces Hold; Kushal approves every send.

## Architecture check
| Question | Answer for this build |
|---|---|
| Functional requirements | Read a weekly batch; source and score each application per criterion; flag conflicts and gaps; recommend; email and schedule after approval; learn from corrections; prove trust with evals |
| Non-functional | 2 to 3 users (Riya, Kushal, Aditya); about 10 to 25 applications a week; a batch read in minutes, not seconds; needs to be up on Mondays |
| Data store | Relational (Supabase Postgres): records relate (application, claim, source, correction) |
| Data model | applications, claims (with source and status Found/Not Found), scores per criterion, thesis versions, portfolio companies, corrections (kind: score or email), emails, calendar holds, eval cases and runs |
| API design | Writes validated server-side and safe to retry: send is idempotent per application, one hold per slot, one correction per action |
| Auth and permissions | Riya: load batch, log her call, correct. Kushal: decide, approve send, approve thesis changes. Aditya: read, joins deeptech calls |
| Single points of failure | Model API down: batch pauses with a clear error, nothing partial is shown as final. Search or fetch fails: the field becomes Not Found with the reason. Supabase down: read-only error state. Resend down: email stays drafted, retried, never double-sent |
| Cost and rate limits | Loop cap and stop rule per field; per-batch spend cap; cache fetched pages for 7 days; cached model results where the input repeats |
| Caching | Fetched pages and search results only |
| Files and media | Decks and forms in object storage, never the database |
| Background work | Gathering, scoring, evals and email sends run as jobs; the page never waits on them |

Data source with no API: founder background and competitor pages have no API; Reverse API Engineer is optional (a more complicated scraper). Not offered for login-gated pages (LinkedIn).
