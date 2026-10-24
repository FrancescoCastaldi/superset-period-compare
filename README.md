# Superset Period Compare

A modular, reversible patch for Apache Superset 6.1.0 that lets a dashboard compare a reference period with a comparison period on any time column.

## What it does

In business dashboards a primary need is to compare a metric (revenue, orders, support tickets, visits) between two time ranges freely chosen by the user: the current month against the previous one, this year against last year, or two arbitrary windows picked on a calendar.

In Apache Superset this has historically required database workarounds: Cartesian SQL views, heavy self joins, duplicated rows or complex Jinja filters that business users cannot manage.

Superset Period Compare solves it with the native machinery of Superset 6.1.0:

1. It adds a native dashboard filter called **PeriodCompare** (period comparison filter).
2. It gives the user presets (previous period, previous month, previous year) or a second calendar window for a custom comparison period.
3. It shows the data as actual values side by side, absolute difference, percentage change or ratio.
4. It aligns dates on time series by granularity (day, week, month), avoiding gaps and misalignments between months of different length or leap years.
5. It installs with one command, never touches user plugins and can be removed, restoring the original files byte for byte.

## Supported charts

- **Table**: metrics and comparison columns side by side, or as a variation.
- **Big Number with Time Period Comparison**: the main KPI and its variation against the comparison period (needs the `CHART_PLUGINS_EXPERIMENTAL` feature flag).
- **ECharts Timeseries (Line, Bar, Smooth Line, Step Line)**: overlaid series with exact date alignment.
- **Pivot Table v2**: aggregated pivot matrix with comparison columns.

## Quick start

Requirements: Apache Superset 6.1.0 and Windows PowerShell 5.1 or later. Node 20 is needed only to rebuild the frontend.

```cmd
git clone https://github.com/FrancescoCastaldi/superset-period-compare.git
cd superset-period-compare

:: 1. Check the target without changing anything
bin\dry-run.bat D:\Path\To\Your\Superset

:: 2. Apply the patch (a safety backup is created first)
bin\install.bat D:\Path\To\Your\Superset

:: 3. Roll back at any time
bin\uninstall.bat D:\Path\To\Your\Superset
```

After installing, rebuild the frontend (`npm run build`) or run your usual build. Details and Docker notes are in [docs/installation.md](docs/installation.md).

## Verification status

| Area | Status |
|:---|:---|
| Backend comparison (`/api/v1/chart/data`) | 27 of 27 checks match direct SQL (`scripts/e2e/verify-backend-compare.py`) |
| Installer (install, rollback, hashes, timestamps) | 11 Pester tests |
| Date arithmetic and helper contract | 28 and 5 Node tests |
| Backend unit tests | 17 pytest tests |
| TypeScript build inside Superset 6.1.0 | compiled with no TypeScript errors |
| Behaviour in the browser with a comparison active | being validated, see the [changelog](CHANGELOG.md) |

The test suites do not run the TypeScript compiler. See [tests/README.md](tests/README.md) and [docs/development.md](docs/development.md).

## Repository layout

```
.
├── .github/              CI and release workflows, issue and PR templates, CODEOWNERS, Dependabot
├── bin/                  Windows launchers: install, uninstall, verify, dry-run
├── compat/               compat.json: SHA-256 of the untouched upstream files (LF endings)
├── docs/                 architecture, installation, upgrading, data contract, development
│   ├── adr/              architecture decision records
│   ├── demo/             static HTML demo of the filter
│   └── plans/            implementation plans
├── installer/            PeriodCompare.ps1 and its libraries (backup, verify, patch, restore, build)
├── payload/              the files copied into the Superset tree, with the Superset layout
├── scripts/              make-payload.ps1
│   └── e2e/              data loader, dashboard setup and backend verification for a running Superset
└── tests/                installer (Pester), backend (pytest), frontend (Node)
```

## Documentation

- [Architecture](docs/architecture.md): data flow, temporal alignment and design decisions.
- [Installation and rollback](docs/installation.md): launchers, CLI options, backups and Docker.
- [Data contract](docs/data-contract.md): payloads and `extraFormData` structures.
- [Upgrading](docs/upgrading.md): moving the patch to Superset 6.2 or 7.
- [Migrating from Cartesian views](docs/migrating-from-cartesian-views.md): retiring the old helper views.
- [Development guide](docs/development.md): building and testing the patch against a real Superset in Docker.
- [Branching and releases](docs/branching-and-releases.md): workflow, commit convention and versioning.
- [Architecture decision records](docs/adr/README.md).
- [Changelog](CHANGELOG.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security issues: see [SECURITY.md](SECURITY.md).

## License

No license has been chosen yet. The files in `payload/` are modified copies of Apache Superset, which is released under the Apache License 2.0. Choose and add a `LICENSE` file before sharing the repository.
