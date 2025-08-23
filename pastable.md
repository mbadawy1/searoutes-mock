Got it — from your video + notes, the **port type-ahead is stuck on “Searching…”** and the **date fields don’t open a proper calendar popover**. They’re not behaving the way you want, so let’s add two small, blocking UX tasks *before* exports.

Below are **ready-to-paste blocks** for **AGENTS.md**.
**Where to put them:** insert **right after “Task 8 — Results Table”** and **before “Task 9 — Export Buttons (UI)”**.
(So they become **Task 8a** and **Task 8b**. Keep your current Task 9+ numbers as-is.)

---

### Task 8a: Fix Port Type-Ahead “Searching…” hang (UI bugfix)

**Goal:** Make the **From/To Port** selectors reliable and match the video mock: responsive suggestions, keyboard control, and robust error handling.

**Files**

* `frontend/src/components/PortSelect.tsx`
* `frontend/src/api.ts` (minor)
* `frontend/src/types.ts` (minor)

**Changes**

* [ ] Add **AbortController** per request to cancel stale fetches on every keystroke and unmount.
* [ ] Add a **hard timeout** (e.g., 6s) that clears “Searching…” and shows a concise error state.
* [ ] Keep a **250 ms debounce**; ignore queries `< 2` chars; trim whitespace.
* [ ] Render rich rows: **Port Name (Country)** — **UN/LOCODE**; bold the matched substring.
* [ ] Keyboard UX: ↑/↓ moves, **Enter** selects, **Esc** closes, **Tab** confirms highlight.
* [ ] Show states: **Searching… / No results / Error** (retry button).
* [ ] Cache last **10** query→result sets in-memory to prevent flicker on re-type.
* [ ] Normalize input so `ale`, `alex`, `EGALY` all resolve; **field value must be LOCODE** (`EGALY`).
* [ ] Log fetch errors to console once (no noisy loops).

**Success criteria (manual)**

* Type `Alex` in **To Port** → get a list including **Alexandria (EG) — EGALY** within \~1s.
* Arrow-down + Enter fills the input with `EGALY` and closes the menu.
* Turning off the backend or proxy shows **Error** (not a spinner forever), and **retry** works.

**Test hints**

* Temporarily throttle network in DevTools to verify timeout → error path.
* Rapidly type `a l e x a` backspace to `ale` → no stuck “Searching…”.

---

### Task 8b: Replace native date inputs with a popover **Date Range** picker (UI)

**Goal:** Clicking either **Departure From/To** opens a calendar popover (like your screenshot). Selecting a range fills both fields; invalid ranges are blocked.

**Files**

* `frontend/src/components/DateRange.tsx` (replace native inputs)
* `frontend/src/lib/date.ts` (format/parsing helpers)
* `package.json` (add UI-only deps)

**Dependencies (UI-only)**

* `react-day-picker` (range mode) and `date-fns`

**Changes**

* [ ] Use a **single popover** to pick a **From → To** range (two months visible, fast month nav).
* [ ] **Presets:** “Next 7 days” and “Next 14 days”.
* [ ] Enforce **from ≤ to**; disable **Search** if invalid (same behavior you want).
* [ ] Display format in inputs: **dd/mm/yyyy**; convert to **ISO** when calling the API.
* [ ] Close popover on valid range selection; **Esc** closes without changes.
* [ ] Preserve manual typing with masked input; auto-correct partials where possible.

**Success criteria (manual)**

* Click either date field → calendar opens.
* Pick Aug 16 → Aug 30 → both inputs populate and popover closes.
* Selecting `to < from` is not allowed; Search button stays disabled until fixed.

**Test hints**

* Toggle timezones in browser; ensure no off-by-one day shifts.
* Verify query params sent to `/api/schedules` match the chosen range.

---

If you want, I can also produce **patch snippets** (AbortController wiring for `PortSelect.tsx` and a minimal `DateRange.tsx` with `react-day-picker`) so you can paste them straight in.
