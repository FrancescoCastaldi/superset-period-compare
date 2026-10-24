# End to end helpers

Python scripts that run inside the Superset container (they need `psycopg2`, already installed there) and use synthetic data only. The full procedure is in the [development guide](../../docs/development.md).

| Script | What it does |
|:---|:---|
| `synthetic-data-generator.py` | creates sales and support ticket data (10,000 rows each, 2025 to 2026, fixed seed) in SQLite |
| `load-fixtures-postgres.py` | loads that data into a PostgreSQL database `pcdata` with typed `DATE` and `TIMESTAMP` columns |
| `setup-test-dashboard.py` | creates, through the REST API, the database, the dataset, 5 charts and a dashboard with the PeriodCompare filter; idempotent |
| `set-dashboard-default.py` | sets the default reference and comparison period of the filter, so the dashboard opens with the comparison applied |
| `verify-backend-compare.py` | queries `/api/v1/chart/data` for 8 cases and compares 27 values with direct SQL; exits with 1 on any difference |

Copy the folder into the container and run the scripts there:

```powershell
docker cp scripts\e2e\. <superset-container>:/tmp/e2e
docker exec <superset-container> python /tmp/e2e/load-fixtures-postgres.py --host db --database pcdata
docker exec <superset-container> python /tmp/e2e/setup-test-dashboard.py --db-host db
docker exec <superset-container> python /tmp/e2e/verify-backend-compare.py --pg-host db
```

The scripts use the development credentials of the Superset compose files (`admin` / `admin`) on `http://localhost:8088`. Do not point them at a shared or production instance.
