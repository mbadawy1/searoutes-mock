# AGENTS.md — Shipping Line Schedule App

> Guidance for AI agents (Codespaces/Copilot, Claude Code, Gemini CLI, etc.). Keep changes small, test locally, and open reviewable PRs.

---

## CURRENT FOCUS
**Task:** Milestone 1 Complete — All tasks finished  
**Branch:** `main`  
**Status:** Ready for Milestone 2  
**Next:** Milestone 2 — Searoutes Live Provider

---

## ACCEPTANCE CRITERIA (MVP — Definition of Done)
- Type-ahead **From/To** accepts plain text like “Egypt” or “Alexandria” and fills the UN/LOCODE (e.g., **EGALY**).
- Choosing **dates** opens a calendar and results respect that departure window.
- Clicking **Search** renders the schedules table; clicking a row’s **Legs** shows per-leg details.
- I can **sort** by **ETD** and **Transit (days)**.
- **CSV** and **Excel** downloads include **exactly the same rows and order visible in the UI after filters & sort**.
- Works fully with the **mock provider** today; switching to **Searoutes** is just changing the Base URL + adding API key on the **server** (no UI changes).

---

## TL;DR for Agents
- One task → one PR → merge → next task.
- Stay within limits: ≤ ~300 LOC and ≤ 5 files per PR (unless the task explicitly allows more).
- Respect the API contract exactly (endpoints, params, column order).
- Prefer local **fixtures** for Milestone 1; live provider is optional and gated.

---

## Task Queue (work top to bottom)

### Task 1: Basic Backend Setup (+ CORS) ✅ COMPLETE
**Goal:** FastAPI app runs locally; frontend can talk to `/api`.
- [x] Create `backend/app/main.py` with minimal FastAPI app.
- [x] Add `GET /health` → `{ "ok": true }`.
- [x] Add CORS for `http://localhost:5173` (or use a Vite proxy).

**Verify:**
```bash
curl -s http://localhost:8000/health
```

### Task 2: Schedule Model ✅ COMPLETE
**Goal:** Lock schema used across app.
- [x] Create `backend/app/models/schedule.py` (Pydantic).
- [x] Fields: `id, origin, destination, etd, eta, vessel, voyage, imo?, routingType, transitDays, carrier, service?`.

**Verify:** module imports without errors.

### Task 3: Fixtures Loading ✅ COMPLETE
**Goal:** Provider returns sample schedules from disk.
- [x] Add `backend/app/providers/base.py` with `ScheduleFilter` (see aliasing below) and `Page(total:int=0, page:int=1, pageSize:int=50)`.
- [x] Add `backend/app/providers/fixtures.py` that loads `data/fixtures/schedules.sample.json`.
- [x] For now: ignore filters; return full list + `total`.

**Verify:**
```bash
python - <<'PY'
from backend.app.providers.fixtures import FixturesProvider
from backend.app.providers.base import ScheduleFilter, Page
items, meta = FixturesProvider().list(ScheduleFilter(), Page())
print(len(items), meta.total)
PY
```

### Task 4: Basic GET endpoint ✅ COMPLETE
**Goal:** Wire provider to public API.
- [x] Create `backend/app/routes/schedules.py` with `GET /api/schedules` returning **all fixtures** (no filters yet).
- [x] Register router in `backend/app/main.py`.

**Verify:**
```bash
curl -s http://localhost:8000/api/schedules | python -m json.tool | head
```

### Task 5: Ports search helper (backend) ✅ COMPLETE
**Goal:** Backend type-ahead data source.
- [x] Create `backend/app/routes/ports.py` with `GET /api/ports/search?q=<query>&limit=15`.
- [x] Read `data/ports.json` items `{ name, locode, country, countryName?, aliases[] }`.
- [x] Match case-insensitive across `name, aliases, locode, country`; simple scoring (exact LOCODE > name match > others).
- [x] Register router in `main.py`.

**Verify:**
```bash
curl -s "http://localhost:8000/api/ports/search?q=egy" | python -m json.tool | head
```

### Task 5b: Carriers search helper (backend) ✅ COMPLETE
**Goal:** SCAC/name type-ahead data source.
- [x] Create `backend/app/routes/carriers.py` with `GET /api/carriers/search?q=<query>&limit=15`.
- [x] Read `data/carriers.json` items `{ name, scac, id? }` (seed with common carriers; expand as needed).
- [x] Match case-insensitive across `name, scac`; simple scoring (exact SCAC > name match > others).
- [x] Register router in `main.py`.

**Verify:**
```bash
curl -s "http://localhost:8000/api/carriers/search?q=msc" | python -m json.tool | head
```

### Task 6a: Filters (backend) ✅ COMPLETE
- [x] Add filters to `/api/schedules`: `origin`, `destination`, `from`, `to`, `equipment`, `carrier`, `routingType`.
- [x] Validate and map to provider filter. Default sort remains **ETD asc**.
- [x] Enhanced with comprehensive global test data (30 records)

### Task 6b: Sorting (backend) ✅ COMPLETE
- [x] Add `sort` param (`etd|transit`) with default `etd` ascending. **Sorting is server-side only**.
- [x] UI toggles sort → updates `?sort=` and refetches (no client-side reordering).

**Verify:**
```bash
curl -s "http://localhost:8000/api/schedules?origin=EGALY&destination=MATNG&from=2025-08-20&to=2025-09-05" | jq '.items[0]'
curl -s "http://localhost:8000/api/schedules?sort=transit" | jq '.items[0]'
```

### Task 6c: Pagination (backend) ✅ COMPLETE
- [x] Add `page`, `pageSize`; return `{ items, total, page, pageSize }`.
- [x] Verified with comprehensive testing (30 global records)

**Verify:**
```bash
curl -s "http://localhost:8000/api/schedules?page=1&pageSize=10" | jq '{count: (.items|length), total, page, pageSize}'
```

### Task 7: Search Form (UI + helpers, MVP) ✅ COMPLETE
**Goal:** Implement search form that drives the schedules table.
- [x] `frontend/src/ScheduleTable.tsx` (wire form → fetch → render)
- [x] `frontend/src/components/PortSelect.tsx` (already existed)
- [x] `frontend/src/components/DateRange.tsx` (new)
- [x] `frontend/src/api.ts` (fetch helpers)
- [x] `frontend/src/types.ts` (shared types)

**Behavior:**
- PortSelect: debounced (250ms) fetch to `/api/ports/search`, ↑/↓, Enter selects, Esc closes; value = **LOCODE** ✓
- DateRange: native inputs; validate `from ≤ to`; disable **Search** if invalid ✓
- Equipment: static select `20DC / 40DC / 40HC / 40RF / 45HC / 53HC` (implemented) ✓
- Carrier: dropdown backed by `/api/carriers/search`; fallback to static options ✓
- Submit → call `listSchedules(params)` ✓

**Verify:** manual: type "Egypt", pick a port → becomes LOCODE. Submit → table refreshes ✓

### Task 7b: Basic UX (status line, quick links, persist) ✅ COMPLETE
**Goal:** Add visible UX cues and shortcuts; keep logic minimal.
- [x] **Status line** above the table showing: `OK • HH:MM • N itineraries` on success; `Error` with brief message on failure.
- [x] **Quick links** for common port pairs (buttons): `EGALY→MATNG`, `EGDAM→NLRTM`. Clicking sets From/To ports + a default date window (today + 21d) and triggers search.
- [x] **Persist last search**: save params to `localStorage` and restore on load (including ports, dates, equipment, carrier).

**Verify (manual):**
- Load page → last search is prefilled; submit once to update the status line clock time ✓
- Click a quick link → form updates and results refresh ✓
- Break network → status line shows "Error" ✓

### Task 8: Results Table ✅ COMPLETE
- [x] `frontend/src/components/ResultsTable.tsx` (new): sticky header, loading/empty states.
- [x] Columns: **Departure (LOCODE)**, **Arrival (LOCODE)**, **Carrier+SCAC**, **Service**, **Vessel/Voyage/IMO**, **ETD**, **ETA**, **Transit (days)**, **Routing**.
- [x] Row expander "Legs" to show each leg (from→to + timestamps).
- [x] Integrated into ScheduleTable.tsx replacing embedded table

**Verify:** visually + no console errors ✓
### Task 8a: Fix Port Type-Ahead "Searching…" hang (UI bugfix) ✅ COMPLETE

**Goal:** Make the **From/To Port** selectors reliable and match the video mock: responsive suggestions, keyboard control, and robust error handling.

**Files**

* `frontend/src/components/PortSelect.tsx` ✅
* `frontend/src/api.ts` (minor)
* `frontend/src/types.ts` (minor)

**Changes**

* [x] Add **AbortController** per request to cancel stale fetches on every keystroke and unmount.
* [x] Add a **hard timeout** (6s) that clears "Searching…" and shows a concise error state.
* [x] Keep a **250 ms debounce**; ignore queries `< 2` chars; trim whitespace.
* [x] Render rich rows: **Port Name (Country)** — **UN/LOCODE**; bold the matched substring.
* [x] Keyboard UX: ↑/↓ moves, **Enter** selects, **Esc** closes, **Tab** confirms highlight.
* [x] Show states: **Searching… / No results / Error** (retry button).
* [x] Cache last **10** query→result sets in-memory to prevent flicker on re-type.
* [x] Normalize input so `ale`, `alex`, `EGALY` all resolve; **field value must be LOCODE** (`EGALY`).
* [x] Log fetch errors to console once (no noisy loops).

**Success criteria (manual)** ✅

* Type `Alex` in **To Port** → get a list including **Alexandria (EG) — EGALY** within \~1s. ✅
* Arrow-down + Enter fills the input with `EGALY` and closes the menu. ✅
* Turning off the backend or proxy shows **Error** (not a spinner forever), and **retry** works. ✅

**Test hints** ✅

* Temporarily throttle network in DevTools to verify timeout → error path. ✅
* Rapidly type `a l e x a` backspace to `ale` → no stuck "Searching…". ✅

### Task 8b: Replace native date inputs with a popover **Date Range** picker (UI) ✅ COMPLETE

**Goal:** Clicking either **Departure From/To** opens a calendar popover (like your screenshot). Selecting a range fills both fields; invalid ranges are blocked.

**Files**

* `frontend/src/components/DateRange.tsx` (replace native inputs) ✅
* `frontend/src/lib/date.ts` (format/parsing helpers) ✅
* `package.json` (add UI-only deps) ✅

**Dependencies (UI-only)**

* `react-day-picker` (range mode) and `date-fns` ✅

**Changes**

* [x] Use a **single popover** to pick a **From → To** range (two months visible, fast month nav). ✅
* [x] **Presets:** "Next 7 days" and "Next 14 days". ✅
* [x] Enforce **from ≤ to**; disable **Search** if invalid (same behavior you want). ✅
* [x] Display format in inputs: **dd/mm/yyyy**; convert to **ISO** when calling the API. ✅
* [x] Close popover on valid range selection; **Esc** closes without changes. ✅
* [x] Preserve manual typing with masked input; auto-correct partials where possible. ✅
* [x] **Enhanced accessibility:** Improved dark theme with proper contrast ratios (WCAG 4.5:1+). ✅
* [x] **Fixed white-on-white issue:** Range selection uses tinted accent with readable text. ✅

**Success criteria (manual)** ✅

* Click either date field → calendar opens. ✅
* Pick Aug 16 → Aug 30 → both inputs populate and popover closes. ✅
* Selecting `to < from` is not allowed; Search button stays disabled until fixed. ✅
* **Accessibility:** No more white-on-white text; all states have proper contrast. ✅

**Test hints** ✅

* Toggle timezones in browser; ensure no off-by-one day shifts. ✅
* Verify query params sent to `/api/schedules` match the chosen range. ✅

**Implementation Notes:**

* Created comprehensive date utility library with format conversion helpers
* Implemented accessible dark theme with proper color contrast (indigo accent scheme)
* Added keyboard navigation support (Esc to close, focus management)
* Supports both manual typing (dd/mm/yyyy) and calendar selection
* Prevents past date selection and enforces valid date ranges
* Uses CSS-in-JS approach with CSS custom properties for theming


### Task 9: Export Buttons (UI) ✅ COMPLETE
- [x] Two buttons linking to `/api/schedules.csv?<qs>` and `/api/schedules.xlsx?<qs>`.
- [x] Disabled while loading or when empty.
- [x] **Exports ignore pagination and include all rows** matching current filters & sort.

**Verify:** clicking downloads; headers are correct. ✅

### Task 10: CSV export endpoint (backend) ✅ COMPLETE
- [x] `/api/schedules.csv` mirrors filters/sort; **ignores pagination**.
- [x] CSV columns in order (match UI LOCODE view):  
  `originLocode,destinationLocode,etd,eta,vessel,voyage,carrier,routingType,transitDays,service`.

**Verify:** ✅
```bash
curl -s -D /tmp/headers.txt "http://localhost:8003/api/schedules.csv" > /dev/null && cat /tmp/headers.txt | grep -i 'content-'
curl -s "http://localhost:8003/api/schedules.csv?sort=etd" | head -5
```

### Task 11: Row "Legs" details (frontend) ✅ COMPLETE
- [x] Expandable section renders per-leg origin/destination and timestamps based on the item's legs.
- [x] Added ScheduleLeg model to backend and legs field to Schedule model
- [x] Added sample legs data to transshipment schedules in fixtures
- [x] Implemented expandable rows in ResultsTable with "Legs" button
- [x] Shows detailed leg info: leg number, ports (LOCODE + names), vessel/voyage, ETD/ETA, transit days
- [x] Only displays "Legs" button for transshipment routes with legs data
- [x] Direct routes show "-" (disabled button) as expected

### Task 12: Sort toggle (UI → server) ✅ COMPLETE
- [x] Toggle **ETD** (default) / **Transit time**; update `?sort=` and refetch. No client-side sort.

### Task 13: Excel (.xlsx) export endpoint (backend) ✅ COMPLETE
- [x] `/api/schedules.xlsx` mirrors filters/sort & **ignores pagination** (sheet: **Schedules**).
- [x] **Allowed deps:** add `openpyxl` **or** `xlsxwriter` to `backend/requirements.txt`.

**Verify:**
```bash
curl -sI "http://localhost:8000/api/schedules.xlsx?origin=EGALY&destination=MATNG" | grep -i 'content-'
```

---

## Milestone 2 — Searoutes Live Provider (auth-first, swap without breaking UI)

**Why this order?** Keep UI and public API stable, then flip a provider flag to call Searoutes with your API key on the **server** only.

### Searoutes integration notes
- Auth header: `x-api-key: <YOUR_KEY>` (HTTP headers are case-insensitive). Some endpoints may require `Accept-Version`; keep it configurable (default unset or e.g. `"2.1"` if needed).
- Port search: `GET /geocoding/v2/port?query=<name|locode>` or `?locode=<UNLOCODE>`.
- Carrier search: `GET /search/v2/carriers?query=<name|scac>`.
- Itineraries (live schedules): `GET /itinerary/v2/execution` with `fromDate`, `toDate` for the departure window.
- Optional: `GET /itinerary/v2/proformas` for scheduled services; consider CO₂ endpoints later.

### Task 14: Provider toggle & config (server-side only)
**Files:** `backend/app/providers/searoutes.py`, `backend/app/main.py`, `backend/requirements.txt`, `.env.example`  
**Steps:**
- [ ] Add `.env.example`:
  ```
  PROVIDER=fixtures             # fixtures | searoutes
  SEAROUTES_BASE_URL=https://api.searoutes.com
  SEAROUTES_API_KEY=your-key-here
  SEAROUTES_ACCEPT_VERSION=
  API_TIMEOUT_SECONDS=10
  ```
- [ ] In `main.py`, select provider via `PROVIDER` env.
- [ ] Add `httpx` client with base URL, timeout, and **2 retries** on 429/5xx.
- [ ] (Dev-only) you may load env via `python-dotenv` if helpful.

**Verify:** environment loads; `PROVIDER=fixtures` remains default.

### Task 15: Port resolution (live)
**Goal:** Accept either plain text or UN/LOCODE and resolve to a port.
- [ ] Regex `^[A-Z]{2}[A-Z]{3}$` → treat as UN/LOCODE; else query by `?query=`.
- [ ] Map top result to `{ name, locode, country }`.

**Verify (requires key):**
```bash
python - <<'PY'
from backend.app.providers.searoutes import SearoutesProvider
p = SearoutesProvider()
print(p.resolve_port("EGALY")["locode"], p.resolve_port("Alexandria")["locode"])
PY
```

### Task 16: Carrier resolution (live)
- [ ] Implement `resolve_carrier(scac_or_name)` → `{ name, scac, id }` from `/search/v2/carriers`.
- [ ] Cache for 5 minutes in-process.

### Task 17: Itinerary fetch & mapping (live)
**Goal:** Fetch live itineraries and map to internal schema.
- [ ] Call `/itinerary/v2/execution` with:
  - Origin/destination: pass `fromLocode`/`toLocode` when UN/LOCODE given; otherwise resolve.
  - Date window: `fromDate`, `toDate` (UTC ISO-8601).
  - Carrier: resolve to SCAC when provided.
- [ ] Map response:
  - `etd` = first leg departure; `eta` = last leg arrival (UTC ISO).
  - `routingType`: `"Direct"` when one leg, else `"Transshipment"`.
  - `transitDays`: compute if absent (`ceil((eta-etd)/86400)`).
  - `vessel`, `voyage`, `imo` best-effort mapping.

**Verify:**
```bash
curl -s "http://localhost:8000/api/schedules?origin=EGALY&destination=ESVLC&from=2025-08-20&to=2025-09-05" | jq '.items | length'
```

### Task 18: Error handling + rate limits
- [ ] Map 4xx/5xx to structured errors `{ code, message }`; surface Searoutes request id if present.
- [ ] Backoff on 429 with jitter; cap retries; propagate a helpful error to the client.
- [ ] Unit test with `httpx.MockTransport`.

**Exit criteria for Milestone 2**
- [ ] Provider toggle works (`fixtures` ↔ `searoutes`) with no API/UI breaking changes.
- [ ] Port + carrier resolution implemented.
- [ ] Mapping preserves internal schema; UTC normalization.
- [ ] Contract tests pass for both providers.
- [ ] README and AGENTS.md updated (usage & limits).

## Repository Structure (expected)

```
backend/
  app/
    main.py
    models/
      schedule.py
    routes/
      schedules.py         # GET /api/schedules (+ .csv/.xlsx)
      ports.py             # GET /api/ports/search?q=
      carriers.py          # GET /api/carriers/search?q=
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
  vite.config.ts

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

> If files don’t exist yet, create minimal versions.

---

## Dev Environment

> Use the Vite dev server for TypeScript/TSX. Do **not** serve `.tsx` directly with a static server.

- **Python:** 3.11+  
- **Node:** 20+ (LTS)  
- **Package managers:** `pip`, `npm`  
- **OS:** Windows/macOS/Linux (WSL2 recommended on Windows)

### How to run the frontend (dev & prod)

**Dev**
```bash
# Node
nvm use 20

# Frontend
cd frontend
cp .env.example .env              # create if missing; see variables below
npm install
npm run dev -- --port 5175 --strictPort
# Open http://localhost:5175
```

**Prod build**
```bash
cd frontend
npm run build                     # outputs JS/CSS/HTML into dist/
npm run preview -- --port 5175 --strictPort
# or serve dist/ with any static server
```

**Backend (dev)**
```bash
cd backend
export API_PORT=8003
uvicorn app.main:app --host 0.0.0.0 --port $API_PORT --reload
# API base: http://localhost:8003
```

### Required env vars (frontend)

```
# .env (or .env.development)
VITE_PORT=5175
VITE_API_BASE=http://localhost:8003
```

### Ports & CORS contract (dev)

* Frontend must run on **5175** (fixed). If the port is busy, the dev server should **fail** instead of auto-switching (`--strictPort`).
* Backend must run on **8003** (fixed).
* CORS allow-list must include:
  * `http://localhost:5175`
  * `http://127.0.0.1:5175`

### Verifying it works

1. Start backend on **8003** → `GET http://localhost:8003/health` returns 200.
2. Start frontend on **5175** → `Search` loads, typing in ports shows suggestions, calendar opens.
3. Check DevTools → no `.tsx` network requests (means Vite is compiling TS → JS correctly).

### Troubleshooting quick hits

* **Blank page & .tsx requests**: you're not on Vite; stop any static server and run `npm run dev`.
* **CORS error**: add both localhost & 127.0.0.1 origins; confirm ports.
* **Claude changed ports**: ensure scripts use `--strictPort`; don't let tools "helpfully" bump ports.
* **TypeScript "may not disable emit" error**: We use Project References. Make sure `tsconfig.app.json` and `tsconfig.node.json` have `"noEmit": false` and `"emitDeclarationOnly": true`.

---

## Per-Task Preflight & Smoke Tests

### Preflight (must pass before coding)
```bash
# Backend env
python -m venv .venv
# PS: .\.venv\Scripts\Activate.ps1   |  bash: source .venv/bin/activate
pip install -r backend/requirements.txt

# Lint/format/tests (Python)
pip install black ruff pytest
black --check backend -l 100
ruff backend --select ALL --ignore D
pytest -q || true   # ok if no tests yet

# Frontend env
cd frontend && npm ci && cd ..

# Run dev servers locally in another shell:
# uvicorn backend.app.main:app --reload --port 8000
# npm --prefix frontend run dev
```

### Task-level Smoke Tests (run after implementing each task)

**Task 5 — Ports search**
```bash
curl -s "http://localhost:8000/api/ports/search?q=egy" | python -m json.tool | head
```

**Task 5b — Carriers search**
```bash
curl -s "http://localhost:8000/api/carriers/search?q=msc" | python -m json.tool | head
```

**Task 6a/6b — Filters + Sorting**
```bash
curl -s "http://localhost:8000/api/schedules?origin=EGALY&destination=MATNG&from=2025-08-20&to=2025-09-05" | jq '.items[0]'
curl -s "http://localhost:8000/api/schedules?sort=transit" | jq '.items[0]'
```

**Task 6c — Pagination**
```bash
curl -s "http://localhost:8000/api/schedules?page=1&pageSize=10" | jq '{count: (.items|length), total, page, pageSize}'
```

**Task 7 — Search form (UI)**
- Manual: type “Egypt” in **From**, pick a port → field becomes a LOCODE (e.g., `EGALY`).  
- Pick `From`/`To` dates; **Search**; confirm table refresh.

**Task 8 — Results table**
- Confirm columns: Departure/Arrival (LOCODE), Carrier+SCAC, Service, Vessel/Voyage/IMO, ETD, ETA, Transit, Routing.  
- Status line shows `OK • HH:MM • N itineraries`.

**Task 9 — Export buttons (UI)**
- With results, **CSV** and **Excel** links present and **enabled**; disabled when loading or empty.
- Confirm exports include **all rows** matching current filters/sort (not just the current page).

**Task 10 — CSV export**
```bash
curl -sI "http://localhost:8000/api/schedules.csv?origin=EGALY&destination=MATNG" | grep -i 'content-type\|content-disposition'
curl -s "http://localhost:8000/api/schedules.csv?origin=EGALY&destination=MATNG" | head -5
```

**Task 11 — Row legs details (UI)**
- Click “Details” (or expander). Legs list shows `# fromLocode → toLocode`, times, `(Nd)`.

**Task 12 — Sort toggle (UI → server)**
- Toggle Sort: **ETD** (default) vs **Transit**. Order changes accordingly after refetch.

**Task 13 — Excel export**
```bash
curl -sI "http://localhost:8000/api/schedules.xlsx?origin=EGALY&destination=MATNG" | grep -i 'content-type\|content-disposition'
```

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
> **Note:** UI columns use **LOCODEs** for Departure/Arrival; fixtures use names. Either enrich fixtures later with `originLocode`/`destinationLocode`, or map name→LOCODE in the UI using `data/ports.json` (acceptable for MVP).

### Backend API (FastAPI)
- **GET `/api/schedules`** — returns schedules from fixtures.
  - **Query params (all optional):** `origin`, `destination`, `from` (ISO date), `to` (ISO date), `equipment`, `routingType` (enum), `carrier`, `sort` (`etd|transit`), `page`, `pageSize`.
  - **Filtering:** case-insensitive contains for text; date range inclusive.
  - **Sorting:** default `etd` ascending (server-side).
  - **Pagination:** return `{ items, page, pageSize, total }`.

- **GET `/api/schedules.csv`** — same filters/sort; **ignores pagination**; CSV columns in order:  
  `originLocode,destinationLocode,etd,eta,vessel,voyage,carrier,routingType,transitDays,service`.

- **GET `/api/ports/search`** — helper for type-ahead (see Task 5).

- **GET `/api/carriers/search`** — helper for type-ahead (SCAC/name).
  - **Query:** `q` (string), `limit` (default 15)
  - **Match:** case-insensitive contains across `name`, `scac`.

### Export parity with UI
- CSV/XLSX must reflect the **same rows and order** visible in the UI after filters & sort.
- Column order matches the spec above; extra columns are **not** added in exports.
- **Exports include all rows** (not just the current page).

---

## Agent Operating Instructions (per task / per PR)
**You are an automated coding agent. Follow these steps in order; do not skip or combine tasks.**

1) Read the **CURRENT FOCUS** block and the top item in **Task Queue**. Do **only** that task.  
2) **Preflight**:  
   - Run the commands in **Per-Task Preflight & Smoke Tests → Preflight**.  
   - If preflight fails, fix the **minimum** necessary files to make preflight pass before starting the task.  
3) **Scope**:  
   - Touch only the files listed in the task (≤ 5 files) and keep total changes ≤ ~300 LOC.  
   - Do not add new dependencies unless the task explicitly allows it.  
4) **Implement**:  
   - Follow the task’s subtasks in order. Stop when **Success criteria** pass.  
   - Respect API contracts and params exactly as written in AGENTS.md.  
5) **Verify**:  
   - Run the **Smoke Tests** for this task (below). Paste the outputs into the PR body.  
6) **Open PR**:  
   - Base branch: `dev`. Use the **PR Template** below. Title: `feat(scope): task N — <short title>`.  
   - If something is ambiguous, leave a TODO and proceed—do not expand scope.  
7) **Handoff**:  
   - Update **CURRENT FOCUS** (Task/Branch/Status/Next).  
   - Stop. Do not start the next task.

---

## Coding Conventions

- **Python:** FastAPI style, Pydantic models. Keep functions small; prefer pure logic.  
- **TS/React:** Functional components + hooks. Fetch wrappers in `frontend/src/api.ts`.  
- **Formatting:** Respect Black, Ruff, ESLint, Prettier. Don’t reformat unrelated files.  
- **Errors:** Typed error payloads; show toast or inline message on the client.

---

## Security & Secrets

- **No secrets in code.** Use environment variables if/when added later.  
- **No outbound network** unless a task explicitly authorizes it.

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

### PR Template (copy/paste)
**Task:** N — <task title>  
**Scope:** files changed (≤ 5), ~LOC  
**Why:** 2–5 bullets explaining the change

#### What changed
- Bullet
- Bullet

#### Preflight output
<copy/paste Black/Ruff/Pytest + npm install results>

#### Smoke tests
<copy/paste the relevant curl / jq output (or describe manual UI steps)>

#### Limitations / TODO
- Bullet or “none”

#### Affected files (≤ 5)
- backend/…
- frontend/…

---

## File-level Guardrails
- **Allowed:** files listed here, plus minimal tests/fixtures.  
- **Disallowed without approval:** new top-level folders; new libraries; broad refactors; CI changes.  
- **Commit hygiene:** small, atomic commits. No drive-by formatting.

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

## Example Code — aliases for reserved `from`/`to`
**Use aliases so we can safely accept `from`/`to` in query params while using different internal names.**

```python
# backend/app/providers/base.py
from pydantic import BaseModel, Field
from typing import Optional

class ScheduleFilter(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    date_from: Optional[str] = Field(default=None, alias="from")
    date_to: Optional[str] = Field(default=None, alias="to")
    equipment: Optional[str] = None
    carrier: Optional[str] = None
    routingType: Optional[str] = None
    sort: Optional[str] = "etd"
    page: int = 1
    pageSize: int = 50

    class Config:
        allow_population_by_field_name = True
        populate_by_name = True
```

```python
# backend/app/routes/schedules.py
from fastapi import APIRouter, Query
from ..providers.fixtures import FixturesProvider
from ..providers.base import ScheduleFilter, Page

router = APIRouter()
provider = FixturesProvider()

@router.get("/api/schedules")
def list_schedules(
    origin: str | None = None,
    destination: str | None = None,
    date_from: str | None = Query(None, alias="from"),
    date_to: str | None = Query(None, alias="to"),
    equipment: str | None = None,
    carrier: str | None = None,
    routingType: str | None = None,
    sort: str = "etd",
    page: int = 1,
    pageSize: int = 50,
):
    filt = ScheduleFilter(
        origin=origin, destination=destination,
        date_from=date_from, date_to=date_to,
        equipment=equipment, carrier=carrier,
        routingType=routingType, sort=sort,
        page=page, pageSize=pageSize
    )
    items, meta = provider.list(filt, Page(total=0, page=page, pageSize=pageSize))
    return {"items": items, "total": meta.total, "page": meta.page, "pageSize": meta.pageSize}
```

---

## Encoding & Line Endings
- Use UTF-8. On Windows, CRLF is fine; normalize with:
  `git config --global core.autocrlf true`
- Avoid smart quotes; use plain ASCII quotes in code and docs.

---

## "If browsers can't read TS/TSX, how do I use this?"

You **never ship TypeScript to the browser.** During development, Vite **transpiles** TS/TSX to plain JavaScript **on the fly**. For production, `npm run build` emits **plain JS** in `dist/`. Browsers load those JS files like any other site. Type annotations are stripped out; only JavaScript runs.

---

## Why ports kept changing (and how we stop it)

* Many dev servers (and some tools like Claude Code) auto-pick a free port if the requested one is busy. That breaks CORS and `API_BASE` assumptions.
* We force stability by:
  * Frontend: `--strictPort` on **5175** (fail fast if taken).
  * Backend: always start on **8003** (or fail). Don't rotate to 8001/8002/8003.
  * Config in one place (`VITE_API_BASE`) so the UI never hard-codes a port.
