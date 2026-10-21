<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# Project rules

Travel planner UI: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, shadcn/ui.

## Commands
- `npm run dev`: needs the backend running on :8000 (see `../AGENTS.md`).
- `npm run gen:api`: regenerates `lib/api/schema.ts` from the backend's OpenAPI spec (backend must be running).
- `npm run typecheck` and `npm run lint` must pass before you say a task is done.

## API
- The browser calls same-origin `/api/*`; `next.config.ts` forwards it to `BACKEND_URL`. Never call the backend URL from the browser.
- All requests go through `lib/travelApi.ts`. Types come from `lib/api/schema.ts`, which is generated: never edit it by hand.
- `weather` and `attractions` each have a `status`: `ok`, `unavailable` or `error`. Render each section independently; one failing section must not hide the other.
- `unavailable` is an expected gap (no retry button). `error` means something broke (offer a retry).
- Show `location` (name, region, country) so the user knows which city was used.
- 422 errors arrive as `ApiError.fields` (per input) and `ApiError.message`. Show field errors next to their inputs.

## UI
- Use components from `components/ui` (shadcn) before writing new ones. Add primitives only with `npx shadcn@latest add <name>`; don't hand-edit `components/ui`.
- Style with Tailwind classes and theme tokens (`bg-card`, `text-muted-foreground`, ...). No inline `style`, no hex colors, no arbitrary values like `w-[37px]`.
- Every input has a visible `<label>`. Button text says what the button does.
- Handle loading, error and every section status. Check the UI against `tests/fixtures/*.json`.
- Layouts must work at 375 px wide.

## Safety
- Render `recommendation` only with react-markdown. Never enable raw HTML (no `rehype-raw`) and never use `dangerouslySetInnerHTML`.
- Never put secrets in `NEXT_PUBLIC_*` variables.
- Don't add dependencies without asking.

## Testing
- Next.js renders a hidden `role="alert"` route announcer, so scope alert locators to `main`.
