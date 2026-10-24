# Contributing

Thanks for helping improve Superset Period Compare.

## Before you start

- Read the [architecture](docs/architecture.md) and the [development guide](docs/development.md).
- The code in `payload/` is generated from a Superset worktree ([ADR 0003](docs/adr/0003-payload-generated-from-a-worktree.md)). Change the source there and regenerate; do not edit `payload/` by hand.
- Open an issue first for anything bigger than a small fix.

## Workflow

1. Create a branch from `main`: `feat/<topic>`, `fix/<topic>` or `docs/<topic>` (see [branching and releases](docs/branching-and-releases.md)).
2. Make one logical change per commit, with a [Conventional Commits](https://www.conventionalcommits.org/) message.
3. Run the checks that apply to your change (see below).
4. Update [CHANGELOG.md](CHANGELOG.md) under `[Unreleased]`.
5. Open a pull request using the template and tick the verification layers you actually ran.

## Checks

| You changed | Run |
|:---|:---|
| installer, launchers | `Invoke-Pester -Path tests/installer` |
| date logic, the helper | `node tests/frontend/verify-resolveComparison.mjs` and `node tests/frontend/verify-applyDashboardComparison.mjs` |
| backend files | the pytest suite in `tests/backend` inside a Superset 6.1.0 tree |
| anything in `payload/` | compile the patched tree (`npm run build-dev`) and run `scripts/e2e/verify-backend-compare.py` |

A green unit test run does not prove that the frontend builds. See [ADR 0004](docs/adr/0004-verify-against-the-real-build.md).

## Style

- UTF-8 without BOM. Line endings follow `.gitattributes`.
- Everything in the repository is written in English: documentation, comments, messages, test names.
- Keep the installer free of machine specific paths and of credentials. Test data must be synthetic.
- Plain punctuation in prose: commas, periods, colons and parentheses.

## Reporting problems

Use the issue templates. For security problems follow [SECURITY.md](SECURITY.md) and do not open a public issue.
