# Development Guide

How to build the patch and verify it against a real Apache Superset 6.1.0, using Docker.

## 1. Where the patch comes from

`payload/` is generated, not edited by hand. The source of truth is a Superset checkout (a worktree of the `6.1.0` tag) where the changes are committed. `scripts/make-payload.ps1` copies the changed files into `payload/` and rewrites `compat/compat.json`:

```powershell
powershell -File scripts/make-payload.ps1 -WorktreePath D:\Path\To\superset-worktree
```

Edit the code in the Superset worktree, commit it there, regenerate the payload and commit the result here.

## 2. Verification layers

| Layer | Command | What it proves |
|:---|:---|:---|
| Installer | `Invoke-Pester tests/installer` | install, idempotency, rollback, hashes, timestamps |
| Logic | `node tests/frontend/*.mjs`, backend pytest | date arithmetic, helper contract, alignment |
| Compilation | `npm run build-dev` in the Superset frontend | the patch compiles with the real TypeScript project |
| Backend end to end | `scripts/e2e/verify-backend-compare.py` | the API returns the same numbers as direct SQL |
| Browser | open the test dashboard with a comparison active | the filter, the charts and the requests work together |

The first two layers use simplified copies of the code and do not run the TypeScript compiler. Only the compilation and the browser layers caught the defects listed in the [changelog](../CHANGELOG.md).

## 3. Running Superset in Docker

Use the Docker Compose files of the Superset checkout: `docker-compose.yml` (full development stack) or `docker-compose-light.yml` (database, backend and frontend only).

```powershell
# from this repository: apply the patch to the Superset checkout
powershell -File installer\PeriodCompare.ps1 -Action Install -TargetDir D:\Path\To\superset -SkipBuild

# from the Superset checkout: start the stack
docker compose up -d
```

### Compile once, do not use the webpack dev server on Windows

The dev server runs `webpack-dev-server` with `watchOptions.poll: 2000`. When the sources live on a Windows bind mount, polling every file every 2 seconds saturates the node process and the bundles are served at roughly 30 KB/s. The page stays blank for minutes.

Compile once and let the Flask backend serve the files from `superset/static/assets`:

```powershell
docker exec <superset-node-container> sh -c "cd /app/superset-frontend && npm run build-dev"
```

Do not stop or kill the container while the build runs: the output is written at the end and an interrupted build leaves a manifest that refers to missing files (404 on `spa.*.js`).

A compose override that keeps `node_modules` on a Docker volume instead of the bind mount also makes `npm install` and the build much faster.

### Why a green test run is not enough

`tsc -b` and webpack compare file timestamps with outputs that already exist (`lib/*.d.ts`). A file copied with an older timestamp is considered already compiled. The installer therefore sets the modification time of the files it writes to the current time. If you copy payload files by hand, touch them.

## 4. Test data and dashboard

The scripts in `scripts/e2e/` run inside the Superset container and use synthetic data only:

```powershell
docker cp scripts\e2e\. <superset-container>:/tmp/e2e
docker exec <superset-container> python /tmp/e2e/load-fixtures-postgres.py --host db --database pcdata
docker exec <superset-container> python /tmp/e2e/setup-test-dashboard.py --db-host db
docker exec <superset-container> python /tmp/e2e/verify-backend-compare.py --pg-host db
```

Use `--host db-light` and `--db-host db-light` with the light compose file.

`setup-test-dashboard.py` creates the database, the dataset, five charts (Table, Big Number, Line, Bar, Pivot) and a dashboard with the PeriodCompare filter. `set-dashboard-default.py` sets a default reference and comparison period, so the dashboard opens with the comparison already applied:

```powershell
docker exec <superset-container> python /tmp/e2e/set-dashboard-default.py --reference "2026-09-01 : 2026-10-01" --comparison "2026-08-01 : 2026-09-01" --type values
```

Development credentials of the Superset compose files (`admin` / `admin`) are valid on localhost only.

## 5. Typical problems

| Symptom | Cause | Fix |
|:---|:---|:---|
| TS2305 `has no exported member 'applyDashboardComparison'` | stale `lib/*.d.ts` and old timestamps | reinstall with the current installer, which refreshes timestamps |
| Blank page, bundles served very slowly | webpack dev server polling a Windows bind mount | compile once with `npm run build-dev` |
| 404 on `spa.*.js` | build interrupted before the output was complete | rerun the build and let it finish |
| Dashboard freezes with a comparison active, no chart request reaches the backend | render loop in the filter | fixed: the data mask is applied once per distinct state |
| Big Number comparison chart missing | feature flag off | enable `CHART_PLUGINS_EXPERIMENTAL` |
