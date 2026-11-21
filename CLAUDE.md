This project uses the MESA framework.
Plan: docs/mesa/ (execution-prompt.md, phases.md, brief.md, components.md).
Look: DESIGN.md (follow exactly).
Say "build phase N" to build; every phase runs current docs (context7), DESIGN.md and playwright-qa before it counts as done.
Runs locally on 127.0.0.1 or on Vercel behind APP_PASSWORD; secrets stay in .env or Vercel environment variables and are never committed; every email goes only to OPERATOR_EMAIL until the operator switches test mode off.
