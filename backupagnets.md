# AGENTS.md — Shipping Line Schedule App

> Guidance for AI agents (Codex, Claude Code, etc.). Keep changes small, test locally, and open reviewable PRs.

---

## CURRENT FOCUS
**Task:** Task 3 — Fixtures Loading  
**Branch:** `feat/fixtures-provider`  
**Status:** In Progress  
**Next:** Task 4 — Basic GET endpoint

---

## Task Queue (work top to bottom)

### Task 1: Basic Backend Setup
- [ ] Create `backend/app/main.py` with minimal FastAPI app
- [ ] Add `GET /health` (returns `{ "ok": true }`)
- [ ] Verify: `curl http://localhost:8000/health` → 200

### Task 2: Schedule Model
- [ ] Create `backend/app/models/schedule.py` with the Pydantic model matching the fixture schema exactly
- [ ] No extra fields or renames

### Task 3: Fixtures Loading (current focus)
- [ ] Ensure `backend/app/providers/fixtures.py` loads `data/fixtures/schedules.sample.json`
- [ ] Verify: `FixturesProvider().list(ScheduleFilter(), Page())` returns 3 items

### Task 4: Basic GET endpoint
- [ ] Create `backend/app/routes/schedules.py` with `GET /api/schedules` returning all fixtures (no filters yet)
- [ ] Register router in `backend/app/main.py`
- [ ] Verify: `curl http://localhost:8000/api/schedules` returns JSON array
- **STOP:** Do **not** add filters/pagination/CSV yet

---

### Task 5: CSV export endpoint (backend, filters-aware)

**Goal:** Provide `/api/schedules.csv` that mirrors `/api/schedules` results & filters.
**Files to modify:**

* `backend/app/routes/schedules.py`
* `backend/app/providers/fixtures.py` (reuse existing list/filter logic)
* `backend/tests/test_schedules.py` (new tests for CSV)

**Success criteria:**

* `GET /api/schedules.csv?...` streams CSV with columns (in order):
  `origin,destination,etd,eta,vessel,voyage,carrier,routingType,transitDays`.
* Filter params identical to JSON endpoint: `origin,destination,from,to,carrier,routingType,page,pageSize` (apply same defaults and sorting by `etd`).
* Response headers include `Content-Type: text/csv; charset=utf-8` and `Content-Disposition: attachment; filename="schedules_<YYYYMMDD>.csv"`.

**Max changes:** ≤ 200 LOC, ≤ 3 files.

**Subtasks:**

* [ ] **5.1 Route:** Add `@router.get("/api/schedules.csv")` beside the JSON route.
* [ ] **5.2 Query mapping:** Reuse/parse the same query params used by `/api/schedules`.
* [ ] **5.3 Data fetch:** Call provider with same `ScheduleFilter` + `Page` and same default sort (`etd` asc).
* [ ] **5.4 CSV writer:** Use `csv` module; write header + rows in the same order as above; ensure dates are ISO strings.
* [ ] **5.5 Headers:** Set `Content-Type` and `Content-Disposition` with a sane filename; stream with `StreamingResponse`.
* [ ] **5.6 Tests:**

  * `curl -s "http://localhost:8000/api/schedules.csv" | head` shows header + rows.
  * Filtered request returns a strictly smaller/equal set matching the same JSON filters.
* [ ] **5.7 Error paths:** On bad params, return 400 with `{code,message}` JSON (consistent with JSON route), not a CSV blob.

---

### Task 6+: Filters → Sorting → Pagination (each as its own PR)
- Keep diffs ≤ 300 LOC / ≤ 5 files.

# Task 7: Search Form (UI + helpers, MVP)

**Goal:** Implement a simple search form that drives the schedules table.

## Files to modify:
- [ ] `frontend/src/ScheduleTable.tsx` (wire form → fetch → render)
- [ ] `frontend/src/components/PortSelect.tsx` (new)
- [ ] `frontend/src/components/DateRange.tsx` (new)
- [ ] `frontend/src/api.ts` (ensure it calls `/api/schedules` with query params)
- [ ] `backend/app/routes/ports.py` (new) + `data/ports.json` (seeded list)

## Success criteria:
- [ ] I can pick From and To using a dropdown with type-ahead (name/country/alias/LOCODE)
- [ ] Native date pickers pop for From date and To date
- [ ] Equipment select shows 20DC / 40DC / 40HC / 40RF
- [ ] Optional Carrier (SCAC) select with HLCU, CMAU, MSCU, ONEY, All
- [ ] Clicking Search updates the table (uses current `/api/schedules` contract)
- [ ] Last search persists across reloads

**Out of scope:** CSV/Excel wiring from UI (covered later), multi-carrier merging, pagination changes.

**Max changes:** ≤ 300 LOC, ≤ 5 files.

---

## 7.1 PortSelect component (type-ahead dropdown)

- [ ] Create `frontend/src/components/PortSelect.tsx`
- [ ] Props: `{ label: string; value: string; onChange(v: string): void }`
- [ ] Input supports free text; show dropdown on 2+ chars
- [ ] Debounce 250ms; call `GET /api/ports/search?q=<query>`
- [ ] Render options as Name (LOCODE, Country); on click set LOCODE (e.g., EGALY)
- [ ] Keyboard support: ↑/↓ to navigate, Enter to select, Esc to close
- [ ] If user pastes a valid LOCODE (e.g., NLRTM), accept it without search

**Verify:** type "Egypt" → see Alexandria/Damietta; select → field becomes EGALY/EGDAM.

---

## 7.2 DateRange component (native date pickers)

- [ ] Create `frontend/src/components/DateRange.tsx`
- [ ] Props: `{ from: string; to: string; onChange(next: {from:string;to:string}): void }`
- [ ] Use `<input type="date">`; default window = today → +14 days
- [ ] Validate from ≤ to; if invalid, disable Search and show inline hint

**Verify:** picking dates updates state; invalid range disables Search.

---

## 7.3 Equipment & Carrier selects

- [ ] In `ScheduleTable.tsx`, add Equipment `<select>` with: "" (Any), 20DC, 40DC, 40HC, 40RF (default empty)
- [ ] Add Carrier `<select>` with: "" (All), HLCU, CMAU, MSCU, ONEY
- [ ] (Optional) exclude MAEU by default

**Verify:** changing selects updates local state; no console errors.

---

## 7.4 Form → API wiring

- [ ] In `frontend/src/api.ts`, expose `listSchedules(params)` that calls: GET /api/schedules?origin=<LOCODE|text>&destination=<LOCODE|text>&from=<ISO date>&to=<ISO date>&equipment=<code>&carrier=<SCAC>
- [ ] In `ScheduleTable.tsx`, on Search, call `listSchedules` with current form values
- [ ] Show a small status line: "OK • HH:MM • N itineraries" or an error message

**Verify:** submit triggers a network call; table refreshes with results (fixtures today).

---

## 7.5 Ports search endpoint (backend helper)

- [ ] Create `backend/app/routes/ports.py` with `GET /api/ports/search?q=<query>&limit=15`
- [ ] Load `data/ports.json` (array of `{ name, locode, country, aliases[] }`)
- [ ] Match if q is substring of name/aliases/locode/country (case-insensitive)
- [ ] Return items sorted by a simple score (exact LOCODE > name match > others)
- [ ] Register router in `backend/app/main.py`

**Verify:** `curl "http://localhost:8000/api/ports/search?q=egy"` returns Alexandria/Damietta etc.

---

## 7.6 UX polish & persistence

- [ ] Disable Search while loading; re-enable on completion
- [ ] Save `{from,to,dates,equipment,carrier}` to localStorage on submit; hydrate on mount

**Verify:** reload keeps previous values; no flicker.

---

### Task 8: Export buttons (UI) — CSV & Excel

**Goal:** Two buttons in the page that download **exactly** what the user sees, using current query params.
**Files:** `frontend/src/ScheduleTable.tsx`, `frontend/src/api.ts` (helper to build querystring)

**Success criteria:**

* Buttons labeled **CSV** and **Excel** appear near the results title/status.
* **Disabled** while loading, or when `rows.length === 0`.
* Clicking opens a browser download of the current results (same filters & sort).

**Max changes:** ≤ 120 LOC, ≤ 2 files.

**Subtasks:**

* [ ] **8.1 State wiring:** Read current form/query params (origin, destination, dates, carrier, equipment if used, sort).
* [ ] **8.2 URL builder:** Utility to serialize current params into a querystring.
* [ ] **8.3 CSV button:** Link to `/api/schedules.csv?<qs>` (plain `<a href>` so the browser downloads).
* [ ] **8.4 Excel button:** Link to `/api/schedules.xlsx?<qs>` (added in Task 13).
* [ ] **8.5 Disabled rules:** Disable both buttons when `loading===true` or no rows.
* [ ] **8.6 Filename hint (optional):** Add `download` attribute to `<a>` with a suggested filename like `schedules_<from>_<to>`.
* [ ] **8.7 Verify:**

  * With results on screen, pressing **CSV** downloads a file with the exact row count (ignoring pagination if server streams the full filtered set).
  * With empty results, both buttons are disabled.

---

# Task 9: Carrier list source (optional)

- [ ] `GET /api/carriers/search?q=` returning `{ name, scac }` (static JSON)
- [ ] Populate carrier `<select>` from this endpoint on load; fallback to hardcoded list

---

## Additional Notes

- [ ] Generate minimal `ports.py` and `PortSelect.tsx` stubs aligned to this plan so an agent can start with compile-ready files, if they are created, check them and update as nesscarry.

---

### Task 10: Results Table (UI, MVP)

**Goal:** Render schedules in a human-readable table with the exact columns you asked for.
**Files to modify/create:**

* `frontend/src/ScheduleTable.tsx` (wire data → table)
* `frontend/src/components/ResultsTable.tsx` (new)
* `frontend/src/lib/format.ts` (new, date/number helpers)
* `frontend/src/types.ts` (extend row/leg types if needed)

**Columns (in order):**
Departure (LOCODE), Arrival (LOCODE), Carrier + SCAC, Service, Vessel / Voyage / IMO, ETD, ETA, Transit (days), Routing (Direct or Transshipment ×N)

**Success criteria:**

* [ ] Table renders all columns above from the current `/api/schedules` payload.
* [ ] ETD/ETA display as local datetime strings (ISO parsing; no timezone math needed for MVP).
* [ ] Routing shows “Direct” if 1 leg, else “Transshipment ×N”.
* [ ] Status line shows: `OK • HH:MM • <N> itineraries`.
* [ ] No console errors; page is responsive down to 1024px.

**Out of scope:** sorting & row expansion (handled in Tasks 11–12).
**Max changes:** ≤ 300 LOC, ≤ 5 files.

#### 10.1 Types & helpers

* [ ] Add/confirm `ScheduleRow` and `ScheduleLeg` in `frontend/src/types.ts`:

  * `carrier`, `scac`, `serviceId`, `vessel`, `voyage`, `imo`, `fromLocode`, `toLocode`, `etd`, `eta`, `transitDays`, `legs[]`
* [ ] `frontend/src/lib/format.ts`: `fmtDateTime(str)`, `fmtBadge(text)` (simple wrappers)

#### 10.2 Table scaffold

* [ ] Create `frontend/src/components/ResultsTable.tsx` exporting `<ResultsTable rows={ScheduleRow[]}/>`
* [ ] Render table with `<thead>` and `<tbody>`; sticky header CSS OK

#### 10.3 Column renderers

* [ ] Departure/Arrival: show `fromLocode` / `toLocode` monospace
* [ ] Carrier + SCAC: `carrier` plus a small rounded badge for `scac`
* [ ] Service: `serviceId` monospace
* [ ] Vessel/Voyage/IMO: “Vessel Voyage” on first line, `IMO nnnnnnn` muted on second
* [ ] ETD/ETA: `fmtDateTime(etd|eta)`
* [ ] Transit (days): right-aligned integer
* [ ] Routing: computed text per legs length

#### 10.4 Empty & loading states

* [ ] When `rows.length === 0`, show muted “No itineraries found for your query.”
* [ ] While fetching (prop flag from parent), show “Loading…”

#### 10.5 Wire into page

* [ ] In `ScheduleTable.tsx`, after search completes, map API response → `ScheduleRow[]` and pass to `<ResultsTable/>`
* [ ] Update status line time and count on each refresh

---

### Task 11: Row “Legs” Details (expand/collapse)

**Goal:** Per-row details to show each leg’s from/to + timestamps.
**Files:** `frontend/src/components/ResultsTable.tsx`

**Success criteria:**

* [ ] Each row has an expander (▶/▼ or “Details”) that reveals a panel listing all legs.
* [ ] For each leg show: `#` badge, `fromLocode → toLocode`, `fromTime → toTime`, `(transitDays d)`.
* [ ] Keyboard accessible: `Enter`/`Space` toggles; `aria-expanded` set correctly.
* [ ] Expansion does not reflow other rows excessively (use `<details>` or a simple toggle div).

**Subtasks:**

* [ ] 11.1 Add `expandedRowId` state (or per-row toggle)
* [ ] 11.2 Implement details panel markup & styles
* [ ] 11.3 Accessibility attributes (`aria-controls`, `aria-expanded`)
* [ ] 11.4 Snapshot or DOM test (optional)

---

### Task 12: Sorting (ETD default, Transit time secondary)

**Goal:** Allow sorting by ETD (default) and Transit time. MVP = client-side.
**Files:** `frontend/src/ScheduleTable.tsx`, `frontend/src/components/ResultsTable.tsx`

**Success criteria:**

* [ ] A **Sort by** control with options: **ETD (earliest first)** (default) and **Transit time**.
* [ ] Sorting is stable and applied before rendering rows.
* [ ] No API changes required (client-side only).
  *(Optional later: pass `sortBy=TRANSIT_TIME` to backend/remote when enabled.)*

**Subtasks:**

* [ ] 12.1 Add `sortBy` state in `ScheduleTable.tsx` (`"ETD" | "TRANSIT"`)
* [ ] 12.2 Implement `sortRows(rows, sortBy)`:

  * ETD: ascending by parsed datetime
  * TRANSIT: ascending by `transitDays` (fallback 0 if missing)
* [ ] 12.3 Wire control changes to re-sort and re-render
* [ ] 12.4 Optional: clickable header sort icons (keep off for MVP unless tiny)

**Verify:**

* [ ] With 3+ rows, toggle “Sort by” and confirm order updates correctly.
* [ ] Default is ETD ascending after each new search.

---

### Notes for the agent

* Keep CSS minimal; prefer utility styles already used in the project.
* Don’t change the API contract; map whatever the backend returns to the required columns.
* For dates, use `new Date(iso).toLocaleString()`; no extra libs.
* If the payload lacks `transitDays`, you may sum leg `transitDays` or compute `(eta−etd)/86400` (ceil).

---

### Task 13: Excel (.xlsx) export endpoint (backend)

**Goal:** Provide `/api/schedules.xlsx` mirroring the CSV/JSON filters and column order.
**Files to modify:**

* `backend/app/routes/schedules.py`
* `backend/requirements.txt` (add `openpyxl`)
* `backend/tests/test_schedules.py` (xlsx tests)

**Success criteria:**

* `GET /api/schedules.xlsx?...` returns a single worksheet named **Schedules**.
* Columns (A→I) match CSV order and headers:
  `origin, destination, etd, eta, vessel, voyage, carrier, routingType, transitDays`.
* First row is header; subsequent rows are values; `transitDays` is a number; `etd/eta` written as ISO text (MVP).
* Response headers include `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` and `Content-Disposition: attachment; filename="schedules_<YYYYMMDD>.xlsx"`.

**Max changes:** ≤ 220 LOC, ≤ 3 files.

**Subtasks:**

* [ ] **13.1 Dependency:** Append `openpyxl>=3.1` to `backend/requirements.txt` and install.
* [ ] **13.2 Route:** Add `@router.get("/api/schedules.xlsx")`.
* [ ] **13.3 Query mapping:** Same params and defaults as JSON/CSV.
* [ ] **13.4 Workbook build:**

  * Create workbook with `openpyxl.Workbook()`, pick active sheet, name **Schedules**.
  * Append header row; iterate items to append data rows in exact column order.
* [ ] **13.5 Streaming:** Write workbook to `BytesIO`, then return `StreamingResponse`.
* [ ] **13.6 Tests:**

  * Call `/api/schedules.xlsx` and assert non-zero content length.
  * (Optional) Load with `openpyxl.load_workbook(BytesIO(content))` and assert header row + a known cell match.
* [ ] **13.7 Error paths:** On validation errors, return JSON 400 (do **not** return a corrupt XLSX).

---

### Notes that keep agents aligned

* Keep **JSON, CSV, and XLSX** exports consistent: **same filters, same default sorting**. The CSV task originally existed but needed these details.
* The original UI task for export buttons is now explicit and disable-safe.
* Do **not** change the JSON contract or add network calls; exports operate on the same provider data locally (fixtures by default). See repo guardrails & provider notes.

---
## TL;DR for Agents

- **Scope:** Implement a small shipping-schedule web app (backend + React frontend). Prefer **small, reviewable diffs**.
- **Non-goals (for now):** No real external APIs. Use **local fixtures** in `data/fixtures/*.json`. Do **not** add new dependencies without explicit instruction in a task.
- **Branching:** Open PRs into `dev` (not `main`). Use **squash merge**.
- **Limits:** Max ~300 changed lines per PR, ≤ 5 files unless asked otherwise.

---

## Repository Structure (expected)

```
backend/
  app/
    main.py
    models/
      schedule.py
    routes/
      schedules.py         # GET /api/schedules (+ .csv)
      ports.py             # GET /api/ports/search?q=
    providers/
      base.py              # provider interface + shared types
      fixtures.py          # reads data/fixtures/*.json
      searoutes.py         # (optional, later) live API mapping
  tests/
    test_schedules.py
  requirements.txt

frontend/
  src/
    api.ts                 # listSchedules(params) & helpers
    types.ts               # ScheduleRow, ScheduleLeg
    lib/
      format.ts            # fmtDateTime, small utils
    components/
      PortSelect.tsx       # type-ahead for ports
      DateRange.tsx        # native date pickers (from/to)
      ResultsTable.tsx     # renders the main table + legs details
    ScheduleTable.tsx      # page/container: form + results + sort
  package.json
  vite.config.ts           # or CRA/Next config

data/
  fixtures/
    schedules.sample.json
  ports.json               # used by /api/ports/search
  carriers.json            # (optional) for carrier select

.github/
  workflows/
    ci.yml                 # (optional) CI

.devcontainer/             # (optional) Codespaces
  devcontainer.json

README.md
AGENTS.md
```

```

If files don’t exist, create minimal versions.

---

## Dev Environment

- **Python:** 3.11+
- **Node:** 20+ (LTS)
- **Package managers:** `pip`, `npm`
- **OS:** Windows/macOS/Linux (WSL2 recommended on Windows)

### Install & Run (local)

**Backend**
```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

**API base URL:** frontend should call `http://localhost:8000` in dev.

---

## Test, Lint, Format (must run before PR)

**Python**
```bash
pip install -r backend/requirements.txt
pip install black ruff pytest
black backend -l 100
ruff backend --select ALL --ignore D
pytest -q
```

**JS/TS**
```bash
cd frontend
npm run lint
npm test --silent || true   # if tests present
npm run typecheck || true   # if configured
```

Include command outputs (or a brief summary) in the PR description.

---

## Coding Conventions

- **Python:** FastAPI style, Pydantic models. Keep functions small; prefer pure logic.
- **TS/React:** Functional components + hooks. Fetch wrappers in `frontend/src/api.ts`.
- **Formatting:** Respect Black, Ruff, ESLint, Prettier. Don’t reformat unrelated files.
- **Errors:** Typed error payloads; show toast or inline message on the client.

---

## Security & Secrets

- **No secrets in code.** Use environment variables if/when added later.
- **No network** unless a task explicitly authorizes it.

---

## Product Requirements (Milestone 1 — Offline)

### Data Model (Fixture)
Use these exact keys:
```json
{
  "id": "uuid-or-stable-id",
  "origin": "Port Said, EG",
  "destination": "Valencia, ES",
  "etd": "2025-08-20T12:00:00Z",
  "eta": "2025-08-31T08:00:00Z",
  "vessel": "MSC Example",
  "voyage": "EX123",
  "routingType": "Direct|Transshipment",
  "transitDays": 11,
  "carrier": "MSC"
}
```

### Backend API (FastAPI)

- **GET `/api/schedules`** — returns JSON array of schedules from fixtures.
  - **Query params (all optional):** `origin`, `destination`, `from` (ISO date), `to` (ISO date), `routingType` (enum), `carrier`.
  - **Filtering:** case-insensitive contains for text fields; date range inclusive.
  - **Sorting:** default `etd` ascending.
  - **Pagination:** `page`, `pageSize` (default 25, max 100). Return `{ items, page, total }`.

- **GET `/api/schedules.csv`** — same filter logic; return CSV columns in this order:  
  `origin,destination,etd,eta,vessel,voyage,carrier,routingType,transitDays`.

### Frontend UI

- **Page:** `ScheduleTable.tsx`
  - Columns: Origin, Destination, ETD (local & UTC tooltip), ETA, Vessel/Voyage, Carrier, Routing Type, Transit Days.
  - Controls: origin/destination inputs, date range pickers, routing type select, carrier select, page size select, CSV export button.
  - Keep component under ~300 lines; factor utilities to `frontend/src/lib/*` if needed.
  - If > 500 rows, consider simple virtualization later.

---

## Milestone 2 — Live Data (optional enablement)

- **Goal:** Swap fixtures for a real schedules API **without changing** the public schema or frontend.
- **Default:** Keep fixtures. Live provider runs only when explicitly enabled.

### Toggle & Environment
Create `.env` and commit `.env.example`:
```
# .env.example
PROVIDER=fixtures           # fixtures | searoutes (or other)
SEAROUTES_BASE_URL=https://api.searoutes.com
SEAROUTES_API_KEY=your-key-here
API_TIMEOUT_SECONDS=10
```
Never commit `.env`. Mask secrets in logs.

### Allowed Dependencies (only when enabling live provider)
- **Runtime:** `httpx>=0.27,<0.28`, `pydantic-settings>=2.4,<3`
- **Tests:** Prefer `httpx.MockTransport` (or `respx`), with small fixtures.

### Network Policy
- Outbound requests **only** to `SEAROUTES_BASE_URL`.
- Timeouts: `API_TIMEOUT_SECONDS` (default 10s), retries (max 2) on 429/5xx with jittered backoff.
- User-agent: `searoutes-schedule/1.0 (+repo)`.

### Provider Architecture
```
backend/app/providers/
  base.py          # Provider interface + shared types
  fixtures.py      # Reads data/fixtures/schedules.sample.json
  searoutes.py     # Maps remote API -> internal schema
```

### Searoutes Provider (v2) Mapping
- **Auth header:** `x-api-key: <SEAROUTES_API_KEY>`
- **Endpoints:**
  - `GET /geocoding/v2/port` — port lookup by `locode` or `query`.
  - `GET /search/v2/carriers` — carrier lookup by name/SCAC.
  - `GET /itinerary/v2/execution` — schedules for carrier + origin/destination, accepts `fromDate`, `toDate`, `sortBy=TRANSIT_TIME|CO2`.
  - (Optional) `GET /itinerary/v2/proformas/{hash}` — details per itinerary.
- **Param mapping:**
  - `origin`, `destination`: if UN/LOCODE-like (`EGPSD`), send as `fromLocode`/`toLocode`; else resolve via geocoding and choose top match.
  - `carrier`: accept SCAC or name; resolve to `carrierScac`.
  - Dates: UI `from` → `fromDate`, `to` → `toDate` (UTC ISO8601).
- **Response → schema:**
  - One leg ⇒ `routingType = "Direct"`. Multiple ⇒ `"Transshipment"`.
  - `etd` = first leg departure; `eta` = last leg arrival (UTC ISO8601).
  - `vessel` from `asset.name` when present; fallback to `serviceId`.
  - `voyage` best-effort from service/leg identifiers; may be empty if absent.
  - `transitDays` = ceil((eta - etd) / 86400) if missing.
- **Errors:** Map 4xx/5xx to `{ code, message }`, include request id if present.

### Files agents may touch (live data)
- `backend/app/providers/*`
- `backend/app/main.py` (provider selection only)
- `backend/requirements.txt`
- `tests/*` (provider tests and mocks)
- `README.md`, `AGENTS.md` (docs)

### What NOT to change
- Frontend types or API contract.
- Unrelated modules/CI.
- Default provider or network enablement.

### PR Checklist (Live Data)
- [ ] Provider added under `backend/app/providers/searoutes.py`
- [ ] Env toggles documented; `.env.example` updated; `.env` ignored
- [ ] `httpx` client with timeout and 2 retries; strict base URL
- [ ] Port + carrier resolution implemented
- [ ] Mapping preserves internal schema; UTC normalization
- [ ] Contract tests pass for fixtures + searoutes providers
- [ ] README and AGENTS.md updated (usage & limits)

---

## File-level Guardrails
- **Allowed:** files listed here, plus minimal test/fixture files.
- **Disallowed without approval:** new top-level folders; new libraries; broad refactors; CI changes.
- **Commit hygiene:** small, atomic commits. No drive-by formatting.

---

## PR Policy (what to open and how)
- **Base branch:** `dev`.
- **Title:** Conventional commits, e.g., `feat(frontend): schedule table with filters`.
- **Body checklist:**
  - [ ] What changed & why (2–5 bullets)
  - [ ] Commands run (copy/paste)
  - [ ] Screenshots or terminal logs (if relevant)
  - [ ] Limitations/TODOs
  - [ ] Affected files list (≤ 5 ideally)

---

## Self-Review Checklist (before PR)
- [ ] All **Test/Lint/Format** commands ran cleanly
- [ ] No new deps unless explicitly allowed (live provider only)
- [ ] Fixture shape unchanged; API contract intact
- [ ] Backend filtering, sorting, pagination per spec
- [ ] CSV endpoint returns correct columns & order
- [ ] UI renders and filters without console errors
- [ ] Total diff size within limits (≤ 5 files, ~300 LOC)

---

## Hard Rules
- ONE feature per PR/session
- NO refactoring of unrelated code
- NO new dependencies without approval (except listed for live provider)
- STOP after the success criteria pass
- ASK before making assumptions; prefer TODOs over guesses

---

## Task Template
**Goal:** _one-sentence description_  
**Files to modify:** _explicit list_  
**Success criteria:** _exact check to run_  
**Out of scope:** _what NOT to do_  
**Max changes:** _≤ 300 LOC, ≤ 5 files_

---

## Quick Start for Claude CLI
1. Read **CURRENT FOCUS** and open the top task.
2. Implement **ONLY** what the task asks.
3. Run the verification command(s).
4. Open a PR into `dev` with the body checklist.
5. **Stop.** Wait for the next task.

---

## Phased Delivery (progressive disclosure)
1. Skeleton (structure only)
2. Core logic (happy path)
3. Error handling
4. Tests
5. Edge cases/optimizations

---

## Searoutes Provider Steps (micro-PRs)
1. Class + config only (`searoutes.py` stub, env wiring)
2. Port geocoding only
3. Carrier resolution only
4. Schedule fetch (`/itinerary/v2/execution`)
5. Response mapping → internal schema
6. Timeouts/retries + small cache
7. Contract tests + docs

---

## Example Task — Add GET /api/schedules
**Prerequisite:** `backend/app/main.py` exists and runs

**Instructions:**
1. Create `backend/app/routes/schedules.py`
2. Add a single GET endpoint that returns all fixtures
3. Register the router in `main.py`

**Code sketch:**
```python
# backend/app/routes/schedules.py
from fastapi import APIRouter
from ..providers.fixtures import FixturesProvider
from ..providers.base import ScheduleFilter, Page

router = APIRouter()
provider = FixturesProvider()

@router.get("/api/schedules")
def list_schedules():
    items, _ = provider.list(ScheduleFilter(), Page())
    return items
```

**Verify:** `curl http://localhost:8000/api/schedules` returns JSON array  
**STOP HERE:** no filters/pagination/CSV yet

---

## Encoding & Line Endings
- Use UTF-8. On Windows, CRLF line endings are fine; normalize with:
  `git config --global core.autocrlf true`
- Avoid smart quotes; use plain ASCII quotes in code and docs.
## Self-Review Checklist
See `docs/SELF_REVIEW.md` for complete checklist before opening PR.






































