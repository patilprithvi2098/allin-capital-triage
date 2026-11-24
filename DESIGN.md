# DESIGN.md: All In Capital triage
Chosen direction: Quantum Minimalist (colours and fonts supplied by the operator), layout from the rough Screen 1 to 4 renders in `mesa-previews/`, motion from `mesa-previews/motion-preview.html`. Agreed 2026-11-18.
Feel: a partner opens this on Monday afternoon between calls. It must feel calm, dense with numbers, sharp and impossible to misread. Evidence comes before decoration; cobalt marks the one thing that matters on each screen. Nothing playful over the data.

## Colour tokens (CSS variables)
```css
:root {
  --surface: #F8F9FA;       /* Crisp White: page */
  --surface-2: #FFFFFF;     /* cards */
  --ink: #0A0A0C;           /* Deep Space Black: text on light, dark bands */
  --ink-2: #16171A;         /* raised surface on dark */
  --text-muted: #5A5F66;    /* on light */
  --text-muted-dark: #9AA0A6; /* on dark */
  --border: #DADDE1;
  --accent: #0047FF;        /* Electric Cobalt: fills, links on light */
  --on-accent: #FFFFFF;
  --accent-text-dark: #7A98FF; /* cobalt tint for text and numbers on dark bands only */
  --success: #1B7F4B; --warning: #8A5A00; --danger: #C0261B; --info: #0047FF;
}
```
Roles: 60% surface, 30% ink bands, 10% accent. Accent only on: the primary action, the recommendation on the dark band, the one number that matters, links, focus rings, the evidence beam.
Contrast checked (WCAG): ink on surface 18.77; cobalt on surface 5.96; white on cobalt 6.28; **cobalt on ink 3.15 FAIL for text, so dark bands use the tint 7.31**; muted 6.10 on light and 7.49 on dark; success, warning, danger on white 5.02, 5.93, 5.94.
Status is never colour alone: always an icon (check, triangle, cross) plus a label.
Chart tints (Portfolio donut, 2026-11-24): `--chart-1` #0029A3, `--chart-2` #9DB4FF, `--chart-3` #0047FF, `--chart-4` #D6E0FF, `--chart-5` #5C82FF, `--chart-other` #6B7280, in that order so neighbouring slices alternate dark and light. One cobalt ramp fails the dataviz validator's lightness-band and chroma checks and two tints sit under 3:1 on white; kept on purpose (one ramp of cobalt tints is this file's rule), so every slice is named in a text legend with amount and share, slices have a 2 px gap and a border ring, and the company table carries the same numbers.

## Type
Headings: Space Grotesk 500 and 700. Body: Inter 400, 500, 600. Numbers: tabular figures (`font-variant-numeric: tabular-nums`), right-aligned in tables. Both fonts are on the "avoid" list for their overuse; the operator chose them on purpose, so they stay.
Scale: 12 / 14 / 16 / 20 / 24 / 32 / 44. Small caps labels at 12 with letter-spacing .06 to .08em. Left-aligned text, no gradient text.

## Layout and shape
Desktop: top bar (ink) with nav (Batch and read, Outreach, Thesis and corrections, Trust report); Screen 1 is a split view (list 380 px, read fills the rest). Spacing scale 4 / 8 / 12 / 16 / 24 / 32 / 48. One radius: 4 px. Borders (1 px) over shadows; one shadow only for popovers. Density: comfortable for reading, compact in tables.
Breakpoints: phone < 640, tablet < 1024, desktop. On phone the list and the read stack and the read opens in place.
Icons: Lucide, 1.5 px stroke, one set. No emoji.

## Screens
Two logins, each showing only what that person needs.

**Riya (the human in the loop)**
1. **Batch and decision.** Decision: Go (take the call) or No-go (reject). Fields in order: company, what it does, sector label it picked, stage, raise; the recommendation (GO or NO-GO), score against the benchmark, confidence; "Why yes" and "Why no" side by side, each line with its source; score by criterion (points, one-line why, source); one table for evidence and deck-versus-form differences (claim, deck, form, outside source, status). Actions: exactly two buttons, Go and No-go, with a reason box below (required when her call differs from the recommendation). Empty: no batch loaded. Error: says what stopped, never shows a partial read as final. Phone: stacked.
2. **Email draft.** Appears automatically when the final call is Go. Editable subject and body, proposed Tuesday or Thursday slots (Aditya added for deeptech), test-mode bar; one action, Send. Her edits are stored as corrections (feedback loop 2).
3. **Scheduling (read-only).** Every sent email with status (sent, follow-up sent, counter-proposed, booked), the next step the agent will take, and the email history for the selected company. No buttons.

**Kushal (read-only)**
4. **Outcomes.** Every application this week: recommendation, Riya's call, agree or disagree, her reason, meeting status. Plus thesis versions waiting for his approval (his only button) and a link to the trust report.
6. **Portfolio** (addition beyond the case; sample data, not labelled on screen at the operator's request, 2026-11-18). Money strip: total invested, cash in the bank, incoming capital, free to deploy. Sector distribution donut (top 5 plus Other, direct labels, one ramp of cobalt tints, legend as text). Portfolio table of fictional companies: sector, invested, current valuation, multiple, revenue trend sparkline, runway, health (icon plus label: Healthy, Watch, At risk) with the reason, last update. Rows open a drop-down brief. No "simulated" or "sample" tags anywhere on screen; public figures keep their source and date.
5. **Trust report.** As before: counts by severity, kill criteria, backtest with leak check, failures with causes, judge against human; small-sample caveat always shown.

First thing Riya sees: one complete application with GO or NO-GO and the why, and the two buttons.

## Motion (operator override of the three-moment default: one hero, four moments, one ambient)
Reduced motion: every layer becomes an instant final state. No flashing faster than 3 per second. Entry motion is movement only, no fades (a fade made the contrast checker flag text in the Sprinto build). Never over tables or evidence. Motion goes in a polish phase after the logic works. Free only; plain JavaScript, canvas and CSS in the preview; React Bits (MIT + Commons Clause, no attribution), Magic UI (MIT) and GSAP (free) are the options if the final stack is React. Check licences at use.
| Layer | Where | Meaning | Duration |
|---|---|---|---|
| Hero | Batch run: ten applications travel Intake, Gather, Judge, Score, Review; stages glow; "Read n of 10" | The system working through the pile | about 3.4 s per application, staggered |
| 1 Decision reveal | When a read finishes, the verdict decrypts (text scrambles then resolves) and the score counts up | The read is ready; where the verdict came from | 500 to 700 ms (above the 300 ms feedback norm, kept as part of the hero tier) |
| 2 Counters | Score bars fill and numbers tick up | Where the score comes from | 800 to 900 ms |
| 3 Evidence beam | Click a claim; a beam with a travelling dot draws to its source | Traceability | 650 ms |
| 4 Decision took effect | "Correction #N applied" badge pulses once; a booked meeting snaps into place on the scheduling dashboard | A correction changed this read, or the agent booked the call | 450 to 900 ms |
| Ambient | Cobalt dot grid and linking lines on black bands only; paused when the tab is hidden | Atmosphere | continuous |
Phone: hero and ambient run only if the phone test stays smooth, otherwise static. Verified in Chrome in real time (no console errors, no negative numbers, reduced motion instant); phone not yet tested.

## Do / Don't
Do: lead with the recommendation and trust numbers; show source and date on external figures; keep "Not Found" as its own state; use cobalt text only on light surfaces and the tint on dark.
Don't: cobalt text on the black bands (fails contrast); purple or indigo gradients; glassmorphism or glow beyond the stage glow in the hero; emoji as icons; hero-plus-three-cards layouts; lorem ipsum, "John Doe" or round fake numbers; thick coloured side stripe on cards; gradient text; buzzwords ("seamless", "cutting-edge", "supercharge"); claims of certainty; implying this is an official All In Capital product.
Accent covers about 10% of a screen. One radius, one shadow style, one spacing scale; no one-off values. Impeccable detector to run in build mode on each screen.
