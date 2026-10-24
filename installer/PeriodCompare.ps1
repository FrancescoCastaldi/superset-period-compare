# installer/PeriodCompare.ps1
# Main entry point and CLI orchestrator for Superset Period Compare installer.

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("Install", "Uninstall", "Verify", "DryRun")]
    [string]$Action = "Install",

    [Parameter(Position = 1)]
    [string]$TargetDir = "",

    [string]$BackupDir = "",
    [switch]$SkipBuild,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Auto-detect target directory if not specified
if ([string]::IsNullOrWhiteSpace($TargetDir)) {
    # Check parent directory or standard paths
    $candidateParents = @(
        (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
        (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..\Repositories\superset-6.1.0")).Path,
        "D:\Actual\03_Sviluppo_Software\Repositories\_work\superset-6.1.0-pc"
    )
    foreach ($cand in $candidateParents) {
        if (Test-Path (Join-Path $cand "superset-frontend\src\visualizations\presets\MainPreset.ts")) {
            $TargetDir = $cand
            break
        }
    }
}

if ([string]::IsNullOrWhiteSpace($TargetDir) -or (-not (Test-Path $TargetDir))) {
    Write-Error "Could not automatically determine Superset target directory. Please specify -TargetDir <path>."
    exit 1
}

$ScriptDir = $PSScriptRoot
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
$PayloadDir = Join-Path $RepoRoot "payload"
$CompatFile = Join-Path $RepoRoot "compat.json"

# Import helper libraries
. (Join-Path $ScriptDir "lib\Backup.ps1")
. (Join-Path $ScriptDir "lib\Verify.ps1")
. (Join-Path $ScriptDir "lib\Patch.ps1")
. (Join-Path $ScriptDir "lib\Restore.ps1")
. (Join-Path $ScriptDir "lib\BuildFrontend.ps1")

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Apache Superset 6.1.0: Period Compare Installer" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Action:       $Action"
Write-Host "Target Dir:   $TargetDir"
Write-Host "Payload Dir:  $PayloadDir"
Write-Host "Compat File:  $CompatFile`n"

switch ($Action) {
    "Verify" {
        $report = Test-PeriodCompareInstallation -TargetDir $TargetDir -CompatFile $CompatFile -PayloadDir $PayloadDir
        Write-Host "Verification Report:" -ForegroundColor Cyan
        Write-Host "  Total Files:        $($report.TotalFiles)"
        Write-Host "  Matches Upstream:   $($report.MatchesUpstream)"
        Write-Host "  Already Patched:    $($report.AlreadyPatched)"
        Write-Host "  Modified/Custom:    $($report.ModifiedOrCustom)"
        Write-Host "  Missing Files:      $($report.Missing)"
        Write-Host "  MainPreset Markers: $($report.MainPresetHasMarkers)"
        if ($report.UserPlugins.Count -gt 0) {
            Write-Host "  User Custom Plugins Detected ($($report.UserPlugins.Count)): $($report.UserPlugins -join ', ')" -ForegroundColor Green
        } else {
            Write-Host "  User Custom Plugins: None detected"
        }
        break
    }

    "DryRun" {
        Write-Host "Running Dry-Run simulation (no files will be written)..." -ForegroundColor Yellow
        $report = Test-PeriodCompareInstallation -TargetDir $TargetDir -CompatFile $CompatFile -PayloadDir $PayloadDir
        if ($report.UserPlugins.Count -gt 0) {
            Write-Host "Protected user plugins: $($report.UserPlugins -join ', ')" -ForegroundColor Green
        }
        Install-PeriodComparePatch -TargetDir $TargetDir -PayloadDir $PayloadDir -DryRun
        Write-Host "Dry-Run simulation completed cleanly." -ForegroundColor Green
        break
    }

    "Install" {
        $report = Test-PeriodCompareInstallation -TargetDir $TargetDir -CompatFile $CompatFile -PayloadDir $PayloadDir
        if ($report.UserPlugins.Count -gt 0) {
            Write-Host "Preserving $($report.UserPlugins.Count) user custom plugin(s): $($report.UserPlugins -join ', ')" -ForegroundColor Green
        }

        if ($report.MainPresetHasMarkers -and ($report.AlreadyPatched -ge ($report.TotalFiles - 2))) {
            Write-Host "Superset is already patched with Period Compare (Idempotent: no new backup created)." -ForegroundColor Yellow
            break
        }

        # Create rollback backup first
        Write-Host "Step 1/3: Creating rollback backup..." -ForegroundColor Cyan
        $backupPath = New-PeriodCompareBackup -TargetDir $TargetDir -CompatFile $CompatFile
        Write-Host "Backup saved: $backupPath" -ForegroundColor Green

        # Apply patch
        Write-Host "`nStep 2/3: Applying Period Compare patch..." -ForegroundColor Cyan
        Install-PeriodComparePatch -TargetDir $TargetDir -PayloadDir $PayloadDir

        # Build frontend assets if not skipped
        Write-Host "`nStep 3/3: Frontend compilation..." -ForegroundColor Cyan
        if ($SkipBuild) {
            Write-Host "Skipping frontend compilation (-SkipBuild passed)." -ForegroundColor Yellow
        } else {
            Invoke-PeriodCompareFrontendBuild -TargetDir $TargetDir
        }

        Write-Host "`nInstallation finished successfully!" -ForegroundColor Green
        break
    }

    "Uninstall" {
        Write-Host "Uninstalling Period Compare and restoring original files..." -ForegroundColor Yellow
        Restore-PeriodCompareBackup -TargetDir $TargetDir -BackupDir $BackupDir
        Write-Host "Uninstall complete. Original tree restored byte-for-byte." -ForegroundColor Green
        break
    }
}
