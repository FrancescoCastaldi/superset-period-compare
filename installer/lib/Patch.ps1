# installer/lib/Patch.ps1
# Applies Period Compare payload files and merges MainPreset.ts safely.

function Merge-MainPreset {
    param(
        [string]$MainPresetPath,
        [switch]$DryRun
    )

    if (-not (Test-Path $MainPresetPath)) {
        throw "MainPreset.ts not found at: $MainPresetPath"
    }

    $content = [System.IO.File]::ReadAllText($MainPresetPath, [System.Text.Encoding]::UTF8)

    if ($content.Contains("period-compare:begin")) {
        Write-Host "MainPreset.ts already contains PeriodCompare registration (skipping)." -ForegroundColor Yellow
        return $true
    }

    # Detect newline style of the file (\r\n vs \n)
    $nl = if ($content.Contains("`r`n")) { "`r`n" } else { "`n" }

    # 1. Add import
    $importTarget = "TimeGrainFilterPlugin,"
    $importSnippet = "TimeGrainFilterPlugin,$nl  // period-compare:begin$nl  PeriodCompareFilterPlugin,$nl  // period-compare:end"

    if (-not $content.Contains($importTarget)) {
        throw "Could not locate import anchor in MainPreset.ts"
    }

    $newContent = $content.Replace($importTarget, $importSnippet)

    # 2. Add plugin instantiation
    $pluginTarget = "new TimeFilterPlugin().configure({ key: FilterPlugins.Time }),"
    $pluginSnippet = "new TimeFilterPlugin().configure({ key: FilterPlugins.Time }),$nl        // period-compare:begin$nl        new PeriodCompareFilterPlugin().configure({$nl          key: FilterPlugins.PeriodCompare,$nl        }),$nl        // period-compare:end"

    if (-not $newContent.Contains($pluginTarget)) {
        throw "Could not locate plugin instantiation anchor in MainPreset.ts"
    }

    $newContent = $newContent.Replace($pluginTarget, $pluginSnippet)

    if (-not $DryRun) {
        [System.IO.File]::WriteAllText($MainPresetPath, $newContent, [System.Text.UTF8Encoding]::new($false))
        Write-Host "MainPreset.ts successfully merged with PeriodCompare markers." -ForegroundColor Green
    } else {
        Write-Host "[DRY-RUN] Would merge MainPreset.ts with PeriodCompare markers." -ForegroundColor Cyan
    }

    return $true
}

function Install-PeriodComparePatch {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$TargetDir,
        [Parameter(Mandatory = $true)]
        [string]$PayloadDir,
        [switch]$DryRun
    )

    if (-not (Test-Path $TargetDir)) {
        throw "Target directory does not exist: $TargetDir"
    }
    if (-not (Test-Path $PayloadDir)) {
        throw "Payload directory does not exist: $PayloadDir"
    }

    $payloadFiles = Get-ChildItem -Path $PayloadDir -Recurse -File
    $appliedCount = 0

    foreach ($file in $payloadFiles) {
        $relPath = $file.FullName.Substring($PayloadDir.Length).TrimStart("\", "/")
        $targetFile = Join-Path $TargetDir $relPath
        $targetDirForFile = Split-Path $targetFile -Parent

        # MainPreset.ts is merged rather than blind-overwritten to protect user plugins
        if ($relPath -like "*MainPreset.ts") {
            Merge-MainPreset -MainPresetPath $targetFile -DryRun:$DryRun | Out-Null
            $appliedCount++
            continue
        }

        if ($DryRun) {
            Write-Host "[DRY-RUN] Would copy: $relPath" -ForegroundColor Cyan
        } else {
            if (-not (Test-Path $targetDirForFile)) {
                New-Item -ItemType Directory -Path $targetDirForFile -Force | Out-Null
            }
            Copy-Item -Path $file.FullName -Destination $targetFile -Force
            # Copy-Item conserva la data del payload. tsc -b e webpack confrontano le date
            # con gli output gia generati (lib/*.d.ts): con una data piu vecchia il file
            # verrebbe considerato gia compilato e la patch non avrebbe effetto.
            (Get-Item -LiteralPath $targetFile).LastWriteTime = Get-Date
            Write-Host "Applied: $relPath" -ForegroundColor Green
        }
        $appliedCount++
    }

    Write-Host "`nPatch operation completed: $appliedCount files processed." -ForegroundColor Green
    return $appliedCount
}
