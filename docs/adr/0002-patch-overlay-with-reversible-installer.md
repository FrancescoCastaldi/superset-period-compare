# 0002. Distribute a file overlay with a reversible installer

Status: Accepted (2026-10-24)

## Context

The change touches about 25 upstream Superset files and adds about 9 new ones. Users run customized Superset trees that contain their own plugins, sometimes with thousands of line ending changes from Git on Windows. A fork or a pull request would not serve them, and a patch file would fail on any diverged context.

## Decision

Ship a `payload/` folder that mirrors the Superset layout and an installer (`installer/PeriodCompare.ps1`) that:

- creates a backup of every file it is about to change, with a manifest of SHA-256 hashes;
- copies the payload files, and merges `MainPreset.ts` only between the markers `period-compare:begin` and `period-compare:end`, so user plugins registered in the same file are preserved;
- is idempotent, and can roll back byte for byte (`Uninstall`);
- never touches `superset-frontend/plugins/superset-plugin-*`;
- sets the modification time of the files it writes to the current time, so incremental builds see them.

`compat/compat.json` records, for every modified file, the SHA-256 of the untouched upstream content with LF endings. `verify` normalizes line endings before comparing.

## Consequences

- Installation and removal are safe and reversible on customized trees.
- Files that user changes made diverge from upstream are overwritten by the payload version. The backup keeps the original, and `verify` reports them as customized before installing.
- The payload is bound to one Superset version. Other versions need a regenerated payload and manifest.
