> Superseded 2026-11-18: the operator chose Quantum Minimalist (Deep Space Black, Crisp White, Electric Cobalt; Space Grotesk and Inter). The locked look is in /DESIGN.md. Sections 1, 2, 9 and 10 (firm facts, voice, imagery, do/don't) still apply; the colour and type sections below are the rejected Neo-Industrialist option.

# Brand guidelines: All In Capital triage build
Direction: The Neo-Industrialist (supplied by the operator, 2026-11-18). Working title for the tool: "All In Capital Triage". This is a course-build brand layer for an internal tool, not the fund's official identity. No official logo was supplied, so none is drawn.

## 1. The firm (facts, with sources; re-check before any external use)
- Name: All In Capital. Mumbai. Founders: Kushal Bhagia and Aditya Singh. Established June 2022 (about 4 years 5 months at 2026-11-18).
- Fund I: about $10 M at launch, reported $11 M deployed across 51 startups.
- Fund II: target INR 200 Cr plus INR 100 Cr greenshoe (up to INR 300 Cr); first close INR 85 Cr (two outlets say INR 100 Cr), March 2025. Final close not confirmed.
- Focus: fintech, deeptech, consumer tech, consumer brands; pre-seed and seed.
- Every figure shown in the product carries "as reported" and a date. Sources disagree on cheque size ($100K to $600K), so cheque size is never shown as fact.

## 2. Feel and voice
Feel: calculated, sophisticated, sharp, growth-oriented. A partner opens it on Monday afternoon and must read it without effort and without doubt.
Voice: plain, specific, numbers first. Say "Not Found", "Hold", "Confidence: Low", never "unfortunately" or "we're excited". Sentence case. No buzzwords (revolutionise, seamless, cutting-edge, supercharge). Never claim certainty the evidence does not give.

## 3. Colour
Roles: 60% surface, 30% secondary, 10% accent.
```css
:root {
  --carbon: #18191A;      /* primary: dark surface, text on light */
  --alabaster: #EFECE6;   /* secondary: light surface, text on dark */
  --cyan: #00F2FE;        /* accent: only on carbon, or as a fill with carbon text */
  --teal-ink: #006B73;    /* accent as text or link on alabaster */
  --carbon-2: #232526;    /* raised surface on dark */
  --stone-2: #D6D2C8;     /* borders and raised surface on light */
  --text-muted-light: #55585A;  /* on alabaster */
  --text-muted-dark: #A3A5A6;   /* on carbon */
  /* status, light theme / dark theme; always paired with an icon and a label */
  --success: #1E7A4A;  --success-d: #4ADE80;
  --warning: #8A5A00;  --warning-d: #FBBF24;
  --danger:  #B3261E;  --danger-d:  #FF6B61;
  --info:    #006B73;  --info-d:    #00F2FE;
}
```
Contrast checked (WCAG ratios):
| Pair | Ratio | Use |
|---|---|---|
| carbon on alabaster | 14.93 | body text, light theme |
| alabaster on carbon | 14.93 | body text, dark theme |
| cyan on carbon | 12.69 | accent text and icons on dark |
| carbon on cyan | 12.69 | text inside accent buttons |
| cyan on carbon-2 | 11.09 | accent on raised dark |
| **cyan on alabaster** | **1.18 FAIL** | never; use teal-ink or a cyan fill with carbon text |
| muted #55585A on alabaster | 6.08 | secondary text, light |
| muted #A3A5A6 on carbon | 7.12 | secondary text, dark |
| teal-ink on alabaster | 5.32 | links, info |
| success / warning / danger on alabaster | 4.52 / 5.03 / 5.54 | status text, light |
| success / warning / danger on carbon | 10.10 / 10.55 / 6.31 | status text, dark |
Accent rule: cyan covers about 10% of a screen: the primary action, the recommendation chip, the one number that matters, focus rings. If everything is cyan, nothing is.
Default theme: light (alabaster) for reading evidence; carbon for the header and the trust panel. A full dark theme uses the -d status colours.

## 4. Type
Headings: Epilogue (600 and 800). Alternative if Epilogue fails to load: Archivo (600 and 800). Body: Work Sans (400, 500, 600). Numbers: Work Sans with tabular figures (`font-variant-numeric: tabular-nums`), right-aligned in data views; verify the feature renders in the build.
Scale: 12 / 14 / 16 / 20 / 24 / 32 / 48. Headings tight (line-height 1.15), body 1.5. Left-aligned text; no gradient text; no all-caps paragraphs (small caps labels at 12 px with letter-spacing only).

## 5. Wordmark and marks
Text wordmark only: "All In Capital" in Epilogue 800, carbon on alabaster or alabaster on carbon, with a single cyan square (0.5 em) before it on carbon only. Minimum clear space: height of the "A". No logo is invented; if the operator supplies one, it replaces the square.

## 6. Layout, shape, density
Grid: 12 columns desktop, 4 phone; split view (list left, one application right). Spacing scale 4 / 8 / 12 / 16 / 24 / 32 / 48. One radius: 4 px (sharp, architectural). Borders over shadows: 1 px stone-2 on light, 1 px #303233 on dark; one shadow only for popovers. Density: comfortable on reading screens, compact on tables. Breakpoints: phone < 640, tablet < 1024, desktop.
Iconography: Lucide, 1.5 px stroke, one set throughout; no emoji.

## 7. Data and evidence components
- Score per criterion: number with tabular figures plus a bar; confidence shown beside it (High / Medium / Low) as text and icon, never colour alone.
- Evidence: every claim is a row with a source link or deck page; "Not Found" is a first-class state with its own icon, not an empty cell.
- Trust panel (carbon surface, cyan numbers): held-out cases tested, disagreements, unverifiable parts; never a bare fraction.
- Conflict flag: danger status with label "Possible portfolio overlap: needs review".
- Charts follow the dataviz rules: one accent, direct labels, no 3D.

## 8. Motion
Subtle, feedback only: 150 to 200 ms on state changes (Agree/Correct, correction applied badge, hold placed). Flow arrows on the components map are static in the image; the app may draw the "correction applied" path once. `prefers-reduced-motion`: no transitions, instant state change.

## 9. Imagery and illustration
No stock photography, no founder photos, no mood boards. Diagrams are flat, carbon lines on alabaster, cyan only for the path being explained.

## 10. Do and don't
Do: lead with the recommendation and the trust numbers; show source and date on every external figure; keep status as icon plus label.
Don't: cyan text on alabaster; purple or indigo gradients; glassmorphism or glow; the thick coloured stripe down one side of a card; lorem ipsum or round fake numbers; Inter, Roboto, Geist, Plus Jakarta Sans, Space Grotesk or Fraunces; claims of certainty; the fund's name used to imply an official All In Capital product.
