# Test

Questa cartella contiene le quattro suite che coprono il progetto. Nessuna di queste viene copiata nell'albero di Superset dall'installer: `tools/make-payload.ps1` esclude `tests/`.

| Suite | Cartella | Test | Cosa verifica |
|:---|:---|:---:|:---|
| Installer (Pester 3.4) | `installer.Tests.ps1` | 5 contesti | dry-run, installazione, idempotenza, rollback byte per byte, protezione plugin utente, auto-detect della cartella |
| Aritmetica date (Node) | `frontend/verify-resolveComparison.mjs` | 28 | traslazione per mesi interi e per giorni, anni bisestili, chiusure mese |
| Contratto helper (Node) | `frontend/verify-applyDashboardComparison.mjs` | 5 | `applyDashboardComparison` e `resolveTimeOffsets` |
| Backend (pytest) | `backend/` | 17 | allineamento temporale, join, mapping degli override |

Il totale dei test backend e 17: 3 in `test_period_compare_backend.py` e 14 in `test_time_shifts.py`. Quest'ultimo e il file originale di Superset 6.1.0 esteso con i casi di Period Compare, quindi include anche i test upstream gia presenti.

## Come eseguirli

Installer (da Windows PowerShell, nella radice del repository):

```powershell
Invoke-Pester -Path .\tests\installer.Tests.ps1
```

Il caso 5 applica e poi rimuove la patch su un albero esistente, se presente in `..\_work\superset-6.1.0-custom`. Il rollback e verificato byte per byte.

Frontend (solo Node, nessuna dipendenza):

```powershell
node tests/frontend/verify-resolveComparison.mjs
node tests/frontend/verify-applyDashboardComparison.mjs
```

Backend (serve un albero Superset 6.1.0 con la patch applicata e il suo ambiente Python):

```powershell
Copy-Item tests\backend\*.py <superset>\tests\unit_tests\common\
cd <superset>
python -m pytest tests/unit_tests/common/test_period_compare_backend.py tests/unit_tests/common/test_time_shifts.py -q
```

`test_time_shifts.py` sostituisce il file omonimo di Superset.

## Note

- Su un PC con fuso orario diverso da UTC, due test upstream (`tests/unit_tests/models/core_test.py::test_dttm_sql_literal`) falliscono con uno scarto di un'ora. Non dipendono dalla patch.
- Tutti i test dell'installer usano `-SkipBuild`: la compilazione del frontend non e coperta.
