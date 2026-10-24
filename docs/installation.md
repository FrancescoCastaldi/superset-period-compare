# Installation and Maintenance Guide

This document describes how to install, verify, roll back and deploy Superset Period Compare.

## 1. Quick batch commands

The `bin/` folder contains four ready to use Windows batch launchers:

| File | Purpose | Example |
|:---|:---|:---|
| `bin\verify.bat` | Checks the target tree and the state of the patch | `bin\verify.bat D:\Superset` |
| `bin\dry-run.bat` | Simulates the installation without writing any file | `bin\dry-run.bat D:\Superset` |
| `bin\install.bat` | Creates a backup, applies the patch and merges `MainPreset.ts` | `bin\install.bat D:\Superset` |
| `bin\uninstall.bat` | Rolls back byte for byte and restores the original tree | `bin\uninstall.bat D:\Superset` |

All launchers take the path of the Superset 6.1.0 root as the first argument. When it is omitted, the installer looks for a Superset tree in the calling directory, the current directory and the sibling folders of this repository, and prefers trees that contain custom plugins.

## 2. PowerShell options

The orchestrator can be called directly:

```powershell
powershell -ExecutionPolicy Bypass -File installer\PeriodCompare.ps1 -Action Install -TargetDir "D:\MySuperset" -SkipBuild
```

Supported parameters:

- `-Action`: the requested operation (`Install`, `Uninstall`, `Verify`, `DryRun`).
- `-TargetDir`: full path of the Apache Superset folder.
- `-SkipBuild`: skips the npm build of the frontend assets (useful for tests or when the build runs in a Docker container).
- `-BackupDir`: a specific backup to restore with `Uninstall`. When omitted, the most recent backup in `.backups/` is used.

## 3. Backup and idempotent rollback

1. **Automatic backup.** Before changing any file the installer creates `.backups\backup_YYYYMMDD_HHMMSS\` inside the target folder.
2. **Integrity manifest.** The backup contains `backup-manifest.json` with, for every file, the relative path, the SHA-256 hash and the original action (modified or added).
3. **Idempotency.** Running `install.bat` on a tree that is already patched is detected through the markers and neither overwrites the original backup nor duplicates entries.
4. **Exact rollback.** `uninstall.bat` puts every modified file back in its original version and removes every file added by Period Compare.
5. **Timestamps.** Installing and restoring set the modification time of the copied files to the current time. `tsc -b` and webpack decide what to recompile by comparing timestamps with outputs that already exist (`lib/*.d.ts`): a file that keeps an older timestamp would be treated as already compiled.

## 4. Verifying a tree

`bin\verify.bat` compares every patched file with the hashes in `compat/compat.json` and with the payload. Hashes are computed on the content with LF line endings, so a Git checkout on Windows with `core.autocrlf=true` is recognized correctly. The report shows how many files match the untouched upstream release, how many are already patched and how many are custom.

## 5. Docker environments

For environments built from a Dockerfile:

1. Copy the `payload` folder into the image before the frontend build step:
   ```dockerfile
   COPY superset-period-compare/payload /app/superset-src
   ```
2. Or mount the folder and run `PeriodCompare.ps1` while preparing the image, before `npm run build`.
3. Make sure `DATE_RANGE_TIMESHIFTS_ENABLED = True` in your `superset_config.py` (the patch already enables it by default).
4. Enable the `CHART_PLUGINS_EXPERIMENTAL` feature flag if you want the "Big Number with Time Period Comparison" chart.

The development server of webpack can be very slow when the sources live on a Windows bind mount, because `webpack.config.js` polls every file every 2 seconds. Compile once with `npm run build-dev` and let the Flask backend serve the result. See [development.md](development.md).
