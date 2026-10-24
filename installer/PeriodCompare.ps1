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
function Resolve-SupersetTargetDirectory {
    param(
        [string]$ExplicitTarget
    )

    $isSuperset = {
        param([string]$path)
        if ([string]::IsNullOrWhiteSpace($path) -or (-not (Test-Path $path))) { return $false }
        $hasPreset = Test-Path (Join-Path $path "superset-frontend\src\visualizations\presets\MainPreset.ts")
        $hasBackend = (Test-Path (Join-Path $path "superset\models\helpers.py")) -or (Test-Path (Join-Path $path "superset\config.py"))
        return ($hasPreset -and $hasBackend)
    }

    if (-not [string]::IsNullOrWhiteSpace($ExplicitTarget)) {
        if (& $isSuperset $ExplicitTarget) {
            return (Resolve-Path $ExplicitTarget).Path
        } else {
            Write-Warning "Specified target '$ExplicitTarget' may not be a complete Superset project."
            return (Resolve-Path $ExplicitTarget).Path
        }
    }

    $rawCandidates = [System.Collections.Generic.List[string]]::new()

    # 1. Caller working directory (from CALLER_DIR env var set by batch wrappers)
    if (-not [string]::IsNullOrWhiteSpace($env:CALLER_DIR)) {
        $rawCandidates.Add($env:CALLER_DIR)
    }

    # 2. Current working directory
    $rawCandidates.Add((Get-Location).Path)

    # 3. Sibling folders and worktrees
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
    $parentReposDir = Split-Path $repoRoot -Parent
    if (Test-Path $parentReposDir) {
        Get-ChildItem -Path $parentReposDir -Directory | ForEach-Object {
            $rawCandidates.Add($_.FullName)
        }
        $workDir = Join-Path $parentReposDir "_work"
        if (Test-Path $workDir) {
            Get-ChildItem -Path $workDir -Directory | ForEach-Object {
                $rawCandidates.Add($_.FullName)
            }
        }
    }

    # 4. Standard local workspace locations
    $rawCandidates.Add("D:\Actual\03_Sviluppo_Software\Repositories\_work\superset-6.1.0-custom")
    $rawCandidates.Add("D:\Actual\03_Sviluppo_Software\Repositories\_work\superset-6.1.0-pc")
    $rawCandidates.Add("D:\Actual\03_Sviluppo_Software\Repositories\superset-6.1.0")

    $scored = @()
    $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)

    foreach ($cand in $rawCandidates) {
        if ([string]::IsNullOrWhiteSpace($cand) -or (-not (Test-Path $cand))) { continue }
        $resolved = (Resolve-Path $cand).Path
        if ($seen.Contains($resolved)) { continue }
        $seen.Add($resolved) | Out-Null

        if (& $isSuperset $resolved) {
            $score = 10
            if (-not [string]::IsNullOrWhiteSpace($env:CALLER_DIR) -and ($resolved -eq (Resolve-Path $env:CALLER_DIR).Path)) {
                $score += 100
            }
            if ($resolved -eq (Get-Location).Path) {
                $score += 80
            }
            $pluginsDir = Join-Path $resolved "superset-frontend\plugins"
            $hasCustomPlugins = $false
            if (Test-Path $pluginsDir) {
                $customPlugins = Get-ChildItem -Path $pluginsDir -Directory -Filter "superset-plugin-*"
                if ($customPlugins.Count -gt 0) {
                    $hasCustomPlugins = $true
                    $score += 50
                }
            }
            if ($resolved -like "*custom*") { $score += 30 }
            if ($resolved -like "*_work*") { $score += 20 }

            $scored += [PSCustomObject]@{
                Path = $resolved
                Score = $score
                HasCustomPlugins = $hasCustomPlugins
            }
        }
    }

    if ($scored.Count -eq 0) {
        return $null
    }

    $sorted = $scored | Sort-Object Score -Descending

    Write-Host "[AUTO-DETECT] Discovered $($sorted.Count) Superset project location(s):" -ForegroundColor Cyan
    foreach ($item in $sorted) {
        $tag = if ($item.HasCustomPlugins) { " (Custom user plugins detected)" } else { "" }
        $marker = if ($item.Path -eq $sorted[0].Path) { " [SELECTED]" } else { "" }
        Write-Host "  -> $($item.Path)$tag$marker" -ForegroundColor $(if ($marker) { "Green" } else { "DarkGray" })
    }

    return $sorted[0].Path
}

$TargetDir = Resolve-SupersetTargetDirectory -ExplicitTarget $TargetDir

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
        Install-PeriodComparePatch -TargetDir $TargetDir -PayloadDir $PayloadDir -DryRun | Out-Null
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
        Install-PeriodComparePatch -TargetDir $TargetDir -PayloadDir $PayloadDir | Out-Null

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
