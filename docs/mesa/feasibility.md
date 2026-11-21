# Phase 0 feasibility (2026-11-18)

## Fund thesis (public wording)
- allincapital.vc: "a new type of VC fund that invests in Indian startups through a community of founders"; tagline "Going all in on founders who go all in". Leads pre-seed and seed rounds. Cheque USD 250K to 600K. No anti-thesis or exclusions stated.
- Press (March 2025): Fund II INR 200 Cr target plus INR 100 Cr greenshoe, focus consumer tech, deeptech, fintech, consumer brands, while staying sector-agnostic; first cheques and follow-ons.
- Inc42 feature: founder-market fit framework for pre-seed (title only read so far).
Cost of what is missing: no written criteria, weights or exclusions exist publicly, so the Written thesis is thin; most criteria come from the Observed thesis (memos), as planned.

## Portfolio (for the overlap gate)
- Fund page https://allincapital.vc/portfolio lists 22 companies (saved in case/portfolio.json). Directories (VCBacked, CB Insights, F4) report 65 to 80 investments, so the public list is partial.
- MeetRecord is on the fund's own page: "SaaS capturing intelligence from online sales and CS meetings". Talkbook (AI call summaries and CRM updates) overlaps it; Phase 2 must flag it.
- Worth noting for the thesis: QuestBook (Web 3.0) is in the portfolio while the memos pass Coinlane on category (crypto exchange); the category line is narrower than "no web3".
Cost: an applicant overlapping an unlisted portfolio company can be missed; every read says the list is partial.

## Founder findability
- All 10 applicant websites use the reserved .example domain, which never resolves, and every LinkedIn link is a placeholder.
- Web search for StockSathi / Aarav Deshmukh and GrainKind / Ritu Hegde found nothing (searched with the built-in web search; Tavily not run because there is no key yet).
Result: applicant and founder backgrounds are Not Found for all 10. Founder quality is scored from the deck and form only, capped, with confidence lowered, and every read states the cost. Real web search still applies to the fund, the portfolio, competitors, markets and regulation.

## Resend replies
- Current docs: Resend can receive email at the account's <id>.resend.app address (no own domain needed) and posts an email.received webhook. A webhook needs a public URL, so live reply reading works once deployed; locally, replies are pasted into Screen 2 and simulated in the evals.

## Keys
- Claude: accepted. Storage: files locally; Supabase project waiting for the operator's yes on a $0 quote.
- Tavily, Resend, judge model: not set yet (operator to create accounts). Judge needed by Phase 3, Tavily by Phase 1, Resend by Phase 5.
