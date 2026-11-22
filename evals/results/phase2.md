# Phase 2 eval results (2026-11-21 15:33)

Checks the saved reads of the last whole-batch run. Overlap stability, measured separately: Talkbook flagged against MeetRecord 3 of 3 runs.

| ID | Decision point | Input | Expected | Assertion | Severity | Result |
|---|---|---|---|---|---|---|
| P2-01 | portfolio overlap (K1) | Talkbook (AI call summaries and CRM updates); MeetRecord in the portfolio; application never names it | NO-GO with the MeetRecord overlap as a gate quoting the fund's portfolio line | hard | Critical | pass |
| P2-02 | gates | Settlr, Series A, INR 30 Cr | NO-GO; stage reason first, cheque reason also shown | hard | High | pass |
| P2-03 | gates | CareCorner, Other (Healthcare) | NO-GO with the outside-the-areas reason | hard | High | pass |
| P2-04 | whole batch | Read all 10 in one run | 10 saved reads, each with a recommendation | hard | High | pass |
| P2-05 | thesis versions | Batch run after Kushal approved v1 | every read states it used v1 | hard | High | pass |
| P2-06 | source check (K2) | All 10 saved reads | every deck, form and web quote is found in its source | hard | Critical | pass |
| P2-07 | overlap false alarm | The 9 applicants other than Talkbook | no portfolio-overlap gate | soft | Low | pass |
| P2-08 | partial portfolio | Every saved read | states the portfolio list is partial | hard | High | pass |
| P2-09 | hold-out (leak) | The thesis built from memos | built only from the 6 build memos; none of the 6 held-out memos | hard | Critical | pass |
| P2-10 | approval | Thesis v1 | approved by Kushal before reads used it | hard | High | pass |
