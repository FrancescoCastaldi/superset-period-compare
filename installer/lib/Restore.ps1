# installer/lib/Restore.ps1
# Restores a target tree byte-for-byte from a rollback backup.

function Restore-PeriodCompareBackup {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$TargetDir,
        [string]$BackupDir = "",
        [switch]$DryRun
    )

    if (-not (Test-Path $TargetDir)) {
        throw "Target directory does not exist: $TargetDir"
    }

    # If no specific backup directory provided, find the most recent one
    if ([string]::IsNullOrWhiteSpace($BackupDir)) {
        $backupRoot = Join-Path $TargetDir ".backups"
        if (-not (Test-Path $backupRoot)) {
            throw "No backups found in $backupRoot"
        }
        $latestBackup = Get-ChildItem -Path $backupRoot -Directory -Filter "backup_*" | Sort-Object Name -Descending | Select-Object -First 1
        if (-not $latestBackup) {
            throw "No backup_* directory found in $backupRoot"
        }
        $BackupDir = $latestBackup.FullName
    }

    $manifestPath = Join-Path $BackupDir "backup-manifest.json"
    if (-not (Test-Path $manifestPath)) {
        throw "Backup manifest not found in $BackupDir"
    }

    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    Write-Host "Restoring from backup created at: $($manifest.timestamp)..." -ForegroundColor Cyan

    $restoredCount = 0
    $removedCount = 0
    $emptyFoldersToCheck = [System.Collections.Generic.List[string]]::new()

    foreach ($fileEntry in $manifest.files) {
        $relPath = $fileEntry.path
        $targetFile = Join-Path $TargetDir $relPath
        $backupFile = Join-Path $BackupDir $relPath

        if ($fileEntry.action -eq "modified") {
            if (-not (Test-Path $backupFile)) {
                Write-Warning "Backup file missing: $backupFile"
                continue
            }
            if ($DryRun) {
                Write-Host "[DRY-RUN] Would restore: $relPath" -ForegroundColor Cyan
            } else {
                $targetParent = Split-Path $targetFile -Parent
                if (-not (Test-Path $targetParent)) {
                    New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
                }
                Copy-Item -Path $backupFile -Destination $targetFile -Force
                # Data aggiornata, come in Patch.ps1: i build incrementali devono vedere il cambio.
                (Get-Item -LiteralPath $targetFile).LastWriteTime = Get-Date
                Write-Host "Restored: $relPath" -ForegroundColor Green
            }
            $restoredCount++
        } elseif ($fileEntry.action -eq "added") {
            if (Test-Path $targetFile) {
                $parentDir = Split-Path $targetFile -Parent
                if ($parentDir -and (-not $emptyFoldersToCheck.Contains($parentDir))) {
                    $emptyFoldersToCheck.Add($parentDir)
                }
                if ($DryRun) {
                    Write-Host "[DRY-RUN] Would remove added file: $relPath" -ForegroundColor Cyan
                } else {
                    Remove-Item -Path $targetFile -Force
                    Write-Host "Removed: $relPath" -ForegroundColor Yellow
                }
                $removedCount++
            }
        }
    }

    # Clean up empty parent directories left behind
    if (-not $DryRun) {
        foreach ($dir in ($emptyFoldersToCheck | Sort-Object Length -Descending)) {
            if ((Test-Path $dir) -and ((Get-ChildItem -Path $dir -Force).Count -eq 0)) {
                Remove-Item -Path $dir -Force
                Write-Host "Removed empty directory: $dir" -ForegroundColor DarkGray
            }
        }
    }

    Write-Host "`nRestore complete: $restoredCount files restored, $removedCount added files removed." -ForegroundColor Green
    return @{
        Restored = $restoredCount
        Removed = $removedCount
        BackupDir = $BackupDir
    }
}
