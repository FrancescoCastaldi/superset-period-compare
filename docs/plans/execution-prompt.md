# Execution prompt: Superset Period Compare

> **Historical document.** This is the prompt that was used to run the initial implementation plan ([2026-10-24-period-compare.md](2026-10-24-period-compare.md)) with orchestrated agents. It is kept for the record and to show the working rules. Paths are written relative to the workspace.

How to use it:
1. Open a new session with the project repository as the working folder.
2. Recommended model: Sonnet 5.5 with high effort.
3. Paste everything between the line "PROMPT START" and "PROMPT END".
4. The session stops by itself at the gates. Answer "go ahead" to continue, or write the corrections.
5. To resume after a pause, paste only the "RESUME" section at the bottom.

---

## PROMPT START

You are the orchestrator of the **Superset Period Compare** project: a patch for Apache Superset 6.1.0 that adds the comparison between a reference period and a comparison period (freely chosen by the dashboard user) on a single timestamp field. The complete approved plan is in `docs/plans/2026-10-24-period-compare.md`. Read it entirely before doing anything, then read the `AGENTS.md` files of the workspace. The plan is the source of truth: if something in the code contradicts the plan, stop and tell me, do not improvise.

### 1. Goal in two lines
Superset 6.1.0 already has `time_offsets` with ranges (`"YYYY-MM-DD : YYYY-MM-DD"`, flag `DATE_RANGE_TIMESHIFTS_ENABLED`). What is missing is a native filter to choose the two periods, the connection to the charts (Table, Big Number, ECharts bars and lines, Pivot Table) and the alignment of the dates in time charts. The final result is a private repository with ONLY the modified files, the complete explanation and an automatic `.bat` installer that applies everything on an existing Superset 6.1.0, without touching the user's plugins.

### 2. Non negotiable principles
1. **Universal.** No customer name, schema, view, server, real column or real data in code, tests, patches, documents, fixtures, commits. Only generic examples (sales, tickets, services) and synthetic data. The date field is any time column of the dataset: no column name in the code.
2. **Zero regressions.** With the comparison off, all the charts behave as before. The existing tests of the touched plugins pass WITHOUT changes.
3. **Minimal and localized changes.** Reuse what exists (`time_offsets`, `compare.py`, `getMetricOffsetsMap`, `isTimeComparison`, the `Time` filter). No new engines, no Jinja, no `custom_form_data`, no second `TEMPORAL_RANGE` filter (it would be overwritten).
4. **The user's plugins are not touched.** No file inside `superset-frontend/plugins/superset-plugin-*` is written by the patch. The only file shared with the user's customizations is `MainPreset.ts`, changed only with an insertion between the markers `period-compare:begin/end`.
5. **Reversible and idempotent.** The installer can be rerun and undone byte for byte.
6. **TDD.** Red test, minimal code, green test. One commit per task, conventional message, `-s` signature. Update `[Unreleased]` in `CHANGELOG.md` at every task.
7. **Security.** Do not read or print files with credentials (`.env`, `cookies.txt`, `login.json`, `docker/.env*`, certificates). Do not copy anything from customer folders into the repository. No personal or healthcare data.
8. **Rules of the environment.** UTF-8 without BOM; no long dash or double hyphen as punctuation in documents and project code; in PowerShell use `;` and not `&&`.

### 3. Folders
- Project repository: the `superset-period-compare` folder (initialize it with `git init -b main` in Phase 6.1, not before).
- Working checkout: create with `git worktree add` from the `6.1.0` tag of the Superset clone a clean copy in `_work/superset-6.1.0-pc` (branch `period-compare`). A second "customized" copy in `_work/superset-6.1.0-custom` for the non invasiveness tests (with the user's 5 plugins copied from the original tree and its `MainPreset.ts`).
- NEVER modify the original `superset-6.1.0` tree (6,367 dirty entries because of line endings, it contains files with credentials). Read from it only what is needed to copy the plugins.
- Python 3.11 with `uv`; Node 20 (like the user's `Dockerfile`); `npm ci --legacy-peer-deps`; heap 8192 or more.
- Do not touch the dashboards of other projects on the server.

### 4. How you work: agents
Use the Agent tool. At most 3 agents in parallel. Every agent receives: the path of the plan, its file perimeter (section 6 of the plan), the contract `docs/CONTRACT.md` when it exists, the rules of section 2 above, and must deliver: list of files touched, tests run with outcome, what did not succeed. No agent writes outside its own perimeter. When an agent finishes, you check the result (diff and tests) before declaring it done.

Ready briefs (adapt only the path of the working copies):

- **Agent E (environment and data)**: Phase 0 and Phase 8. Creates the checkouts, the venv, installs the dependencies, runs the baseline tests (backend: `tests/unit_tests/common/test_time_shifts.py`, `test_query_context_processor.py`, `tests/unit_tests/pandas_postprocessing/test_compare.py`; frontend: `plugin-chart-table`, `plugin-chart-echarts`, `superset-ui-core`, `nativeFilters/utils.test.ts`), configures Superset on SQLite with a test `superset_config` (test credentials generated locally, never reused, never in the repository). Then in Phase 8: a multi domain synthetic fixture generator with all the date column variants of section 8 of the plan, demo dashboard, benchmark.
- **Agent K (contract)**: Phase 1. Writes `docs/CONTRACT.md` (keys `time_range`, `time_compare`, `comparison_type`, offset format, column names, alignment rule with shift in whole months or days) and the signatures of `applyDashboardComparison` and `resolveTimeOffsets` with red interface tests.
- **Agent A (backend)**: Phase 2. Files: `superset/models/helpers.py` (shift and alignment for range offsets, join by grain), `superset/common/query_object.py` (ends with a time), `superset/constants.py` (`time_compare`, `comparison_type` in the override mappings), config. Tests in `tests/unit_tests/common/` and an integration test on `/api/v1/chart/data`.
- **Agent B (frontend core)**: Phase 3. `packages/superset-ui-core/src/query/constants.ts` and types, `packages/superset-ui-chart-controls/src/utils/applyDashboardComparison.ts` (new, exported), `isTimeComparison.ts`, the `follow_dashboard_comparison` control in `sections/timeComparison.tsx`, merge tests in `nativeFilters/utils.test.ts`.
- **Agent C (native filter)**: Phase 4. `src/filters/components/PeriodCompare/` (model: `Time/`), pure functions `resolveComparison.ts` with at least 25 tests, `reference_column` control, registrations (`src/constants.ts`, `components/index.ts`, anchor in `MainPreset.ts`, `FILTER_SUPPORTED_TYPES`), every place that treats `filter_time` in the filters window, Italian and English translations.
- **Agent D (charts, in sequence)**: Phase 5. First Table and Big Number, then ECharts bars and lines, finally Pivot Table. Every chart calls `applyDashboardComparison` at the start of `buildQuery` and `transformProps`; the existing tests pass without changes.
- **Agent I (installer and documents)**: Phase 6, parallel to A and B. Repository skeleton, `tools/make-payload.ps1`, `installer/PeriodCompare.ps1` with the libraries, `install.bat`, `uninstall.bat`, `verify.bat`, `dry-run.bat`, Pester tests (the 8 cases of section 8), complete README and `docs/*`.
- **Agent R (reviewer)**: at every gate. Read only. Checks the diff, the rules of section 2, reuse instead of duplication, runs `/simplify` on the new code, scans the repository for secrets and customer names.

### 5. Order, gates and what you must show me
Follow phases 0-11 of the plan. At every gate (G0 ... G6) stop and write a summary of at most 8 lines: what is done, tests passed with numbers, what is left, new risks, and the question "go ahead?". Do not move to the next phase without my answer at gates G0, G1, G4 and G6. You can pass the other gates by yourself if all the tests are green and the reviewer found no blocking problems.

Gate G0 in particular: besides the baseline, tell me free RAM, disk space, time of `npm ci`, and whether the frontend build is feasible. If it is not, switch to plan B of the plan (Jest plus `tsc` plus API test) and tell me.

### 6. Final verification before the push
1. `pytest` of the new tests and the existing ones on time and offsets: all green.
2. Jest of the touched packages and plugins: all green, existing tests unchanged.
3. `tsc --noEmit` on the touched packages.
4. Installer Pester: all cases green on a clean tree and on a customized tree (hashes of the user's plugins identical before and after).
5. End to end test on a local Superset with synthetic data: two periods chosen, four charts checked against a hand written SQL query, with screenshots.
6. Comparison off = behavior identical to before.
7. Universality matrix (date column types, grains, two different datasets in the same dashboard).
8. Final scan: no secret, no personal data, no customer name, schema or server in the repository; `.gitignore` from the template; `CHANGELOG.md` with the `0.1.0` release.

### 7. Phase 11: private repository
Only after my explicit go ahead on the G6 summary: `git init -b main` (if not already done), final commit, `gh repo create FrancescoCastaldi/superset-period-compare --private --source . --remote origin --push`. GitHub only, private repository, no Bitbucket remote. Then `gh repo view` to confirm it is private, and tell me the address.

### 8. If something does not add up
If an existing test fails because of a change of yours, fix the change, not the test. If the plan is impossible to follow at some point (for example a Superset function is different from how it is described), stop, explain what you found with path and line, and propose an alternative: do not proceed with an assumption. If a command would require touching what is out of perimeter (original tree, the user's plugins, server), do not run it and ask.

Start now: read the plan and the `AGENTS.md` files, then launch Agent E for Phase 0 and stop at gate G0.

## PROMPT END

---

## RESUME (paste after a pause or in a new session)

Resume the Superset Period Compare project. Read `docs/plans/2026-10-24-period-compare.md` and `git log --oneline` in the project repository and in the `_work/superset-6.1.0-pc` checkout (branch `period-compare`) to understand where we are. List the phases already completed (ticked tasks in the plan and commits), the phase in progress and the tests that pass today. Rerun the baseline tests of the phase in progress to verify the state, write me a summary of 8 lines and stop waiting for the go ahead. The rules are the same as section 2 of the execution prompt: universal, zero regressions, user plugins intact, no secrets, push only after my confirmation.
