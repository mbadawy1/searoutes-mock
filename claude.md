# CLAUDE.md — Autonomous Build Guide (Claude Code CLI orchestrating Gemini CLI)

> **Role:** Claude is the **orchestrator**. It plans, gates changes, runs commands, and opens PRs.  
> **Delegation:** Use **Gemini CLI** for heavy lifting (large codegen, multi-file edits, scaffolding, refactors, bulk tests/fixtures).  
> **Source of truth:** **AGENTS.md** is canonical for tasks/contracts. If anything conflicts, **AGENTS.md wins**.

---

## 🎯 Project Snapshot (mirror AGENTS.md)
- **Task:** Task 3 — Fixtures Loading
- **Branch:** `feat/fixtures-provider`
- **Status:** In Progress
- **Next:** Task 4 — Basic GET endpoint

**Work one task at a time.** Do not start the next task until current PR merges.

---

## 🧭 Guardrails
1) **One task → one PR → merge → next task.**
2) **Scope:** ≤ ~300 LOC and ≤ 5 files per PR (unless task explicitly allows more).
3) **Contracts:** Keep API envelopes, sort behavior, and export columns stable (see below).
4) **Server-only sorting.** UI toggles set `?sort=`; server re-fetches.
5) **Exports = all filtered rows** (ignore pagination) and match server sort order.
6) **No secrets in client.** Live provider keys stay server-side.
7) **When ambiguous:** implement the minimum, add a `TODO`, proceed.

---

## 📐 Contracts You Must Honor
- **Response envelope:** `{ "items": [...], "total": int, "page": int, "pageSize": int }`
- **Sorting:** `?sort=etd|transit` (default `etd`) — server-side only
- **Exports (CSV/XLSX):** export the full filtered+sorted dataset, not just the page
- **CSV column order (default unless AGENTS.md says otherwise):**  
  `originLocode,destinationLocode,etd,eta,vessel,voyage,carrier,routingType,transitDays,service`
- **Param aliases:** accept `from`/`to`, map internally to `date_from`/`date_to` via Pydantic aliases

---

## 🛠️ Environment Bootstrapping

### Python backend (FastAPI)
```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate

mkdir -p backend/app providers 2>/dev/null || true
[ -f backend/requirements.txt ] || printf "fastapi\nuvicorn[standard]\nhttpx\n" > backend/requirements.txt
pip install -r backend/requirements.txt
```

### Gemini CLI (heavy lifting)
- **Node 20+ required.** Install with `nvm` if needed.  
- **Install:** `npm i -g @google/gemini-cli`  
- **Run interactive in repo root:** `gemini`  
- **Run one-off:** `gemini -p "Your prompt"` (optionally `--include-directories backend,frontend,data`)

**Project files used by Gemini (create once):**
- `GEMINI.md` (root) — this repo context for Gemini
- `.gemini/commands/plan.toml` — slash command `/plan`
- `.gemini/commands/implement.toml` — slash command `/implement`
- `.gemini/settings.json` (optional) — directory/model defaults

Example TOMLs (keep them short and strict):

**`.gemini/commands/plan.toml`**
```toml
name = "plan"
description = "Summarize current task from AGENTS.md and propose minimal steps within scope."
prompt = """
You are assisting on the Shipping Line Schedule App. Read AGENTS.md Task Queue (top item only).
Output:
1) Task summary
2) Files to touch (≤5)
3) LOC estimate (≤300)
4) Risks and how to keep within contracts and scope
Do NOT propose changes outside the current task.
"""
```

**`.gemini/commands/implement.toml`**
```toml
name = "implement"
description = "Generate minimal patch (diff or full files) for the current task only."
prompt = """
Given the plan and contracts, produce UNIFIED DIFFs or full file contents.
Rules:
- Max ~300 LOC, ≤5 files
- Keep API envelopes/CSV order/params exactly as specified
- Prefer editing existing files; create only those listed in the task
- Include quick verification snippet or curl to smoke-test
"""
```

**Optional `.gemini/settings.json`**
```json
{
  "includeDirectories": ["backend", "frontend", "data", "."],
  "ignore": ["node_modules", ".venv", ".git", "dist", "build"],
  "model": "gemini-2.5-pro"
}
```

---

## 🤖 Orchestration Loop (Claude ↔ Gemini)

**Per task:**

1) **Plan (Claude):** Read AGENTS.md → CURRENT FOCUS → Task block → success criteria. Draft a 3–6 step plan.
2) **Preflight (Claude):**
   ```bash
   pip install black ruff pytest || true
   black --check backend -l 100 || true
   ruff backend --select ALL --ignore D || true
   pytest -q || true
   ```
3) **Estimate scope (Claude):** If patch > ~150 LOC, ≥ 3 files, or bulk boilerplate/tests → **delegate** to Gemini.
4) **Delegate (Claude):** Open `gemini` in repo root. Run `/plan`, confirm scope, then `/implement`. Ask for **unified diffs** or full files.
5) **Apply (Claude):** Review Gemini output; apply minimal patch; keep within limits.
6) **Verify (Claude):** Run smoke tests (AGENTS.md). Capture outputs.
7) **PR (Claude):** Open PR to `dev` using the template below.
8) **Update AGENTS.md CURRENT FOCUS** after merge. Stop.

---

## 🔁 Task Cues (for quick reference)
- **Task 3 (current):** Provider serves fixtures from disk; filters may be ignored for now; deterministic output.
- **Task 4 (next):** `GET /api/schedules` returns fixtures using the standard envelope; server-side sort.

---

## 📦 PR Template
**Task:** N — <title>  
**Scope:** files changed (≤ 5), ~LOC  
**Why:** 2–5 bullets

#### What changed
- …

#### Preflight output
<black/ruff/pytest logs>

#### Smoke tests
<curl/jq outputs or manual steps>

#### Limitations / TODO
- …

#### Affected files (≤ 5)
- backend/…
- frontend/…

---

## 🛑 Stop Conditions
- Task success criteria unmet
- Contract breakage (API, CSV, sorting)
- Scope budget exceeded
- Secrets or live keys in client code

---

## ✅ Final Checklist (per task)
- [ ] Within file/LOC budget
- [ ] All smoke tests pass
- [ ] No secrets in client
- [ ] PR opened to `dev` with template
- [ ] AGENTS.md CURRENT FOCUS updated post-merge
