# Security Policy

## Supported versions

Only the latest released version of this project is supported, for the Apache Superset line named in `compat/compat.json` (6.1.x).

## Reporting a vulnerability

Do not open a public issue. Use GitHub private vulnerability reporting on this repository (Security tab, "Report a vulnerability"), or write to info@francescocastaldi.it with:

- a description of the problem and its impact;
- the steps to reproduce it, and the Superset version used;
- any suggested fix.

You can expect an acknowledgement within a few days and a fix or a mitigation plan after the report is confirmed.

## Scope notes

- The installer only reads and writes files inside the target Superset tree and its `.backups/` folder. It does not make network requests.
- Test and end to end scripts use synthetic data and the development credentials of the Superset compose files (`admin` / `admin`), which are valid on localhost only. Never use them on a shared or production instance.
- Never commit credentials, tokens or `.env` files.
