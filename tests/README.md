# Tests

This folder holds the suites that cover the project. The installer does not copy any of them into the Superset tree: `scripts/make-payload.ps1` excludes `tests/`.

| Suite | Location | Tests | What it checks |
|:---|:---|:---:|:---|
| Installer (Pester 3.4) | `installer/installer.Tests.ps1` | 11 | dry run, install, idempotency, byte for byte rollback, user plugin protection, auto detection, line ending independent hashes, file timestamps |
| Date arithmetic (Node) | `frontend/verify-resolveComparison.mjs` | 28 | whole month and day shifts, leap years, month ends |
| Helper contract (Node) | `frontend/verify-applyDashboardComparison.mjs` | 5 | `applyDashboardComparison` and `resolveTimeOffsets` |
| Backend (pytest) | `backend/` | 17 | temporal alignment, joins, override mappings |
| End to end (Python) | `../scripts/e2e/verify-backend-compare.py` | 27 checks | values returned by a running patched Superset against direct SQL |

The backend total is 17: 3 in `test_period_compare_backend.py` and 14 in `test_time_shifts.py`. The latter is the original Superset 6.1.0 file extended with the Period Compare cases, so it also contains upstream tests.

## How to run them

Installer (Windows PowerShell, from the repository root):

```powershell
Invoke-Pester -Path .\tests\installer
```

Cases 3 to 5 apply and then remove the patch on a real Superset tree with custom plugins. They run only when the environment variable `PERIOD_COMPARE_TEST_TREE` points to such a tree, and the rollback is verified byte for byte.

Frontend (Node only, no dependencies):

```powershell
node tests/frontend/verify-resolveComparison.mjs
node tests/frontend/verify-applyDashboardComparison.mjs
```

Backend (needs a Superset 6.1.0 tree with the patch applied and its Python environment):

```powershell
Copy-Item tests\backend\*.py <superset>\tests\unit_tests\common\
cd <superset>
python -m pytest tests/unit_tests/common/test_period_compare_backend.py tests/unit_tests/common/test_time_shifts.py -q
```

`test_time_shifts.py` replaces the file with the same name in Superset.

End to end against a running Superset: see [../docs/development.md](../docs/development.md).

## Notes

- On a PC whose time zone is not UTC, two upstream tests (`tests/unit_tests/models/core_test.py::test_dttm_sql_literal`) fail with a one hour offset. They do not depend on the patch.
- None of these suites runs the TypeScript compiler. To check that the frontend builds, compile the patched Superset tree (`npm run build-dev`) and look for TypeScript errors. See [../docs/development.md](../docs/development.md).
