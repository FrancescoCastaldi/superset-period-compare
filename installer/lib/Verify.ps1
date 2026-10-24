# installer/lib/Verify.ps1
# Verifies target Superset tree compatibility, check status, and ensures user plugins safety.

function Get-LfNormalizedHash {
    # SHA256 of the content with CRLF reduced to LF. A Git clone on Windows with
    # core.autocrlf=true has CRLF files, while the hashes in compat.json and the
    # payload are computed on LF content.
    param([Parameter(Mandatory = $true)][string]$Path)

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $normalized = New-Object System.IO.MemoryStream
    for ($i = 0; $i -lt $bytes.Length; $i++) {
        if ($bytes[$i] -eq 13 -and ($i + 1) -lt $bytes.Length -and $bytes[$i + 1] -eq 10) { continue }
        $normalized.WriteByte($bytes[$i])
    }
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($sha.ComputeHash($normalized.ToArray()))).Replace("-", "")
    } finally {
        $sha.Dispose()
        $normalized.Dispose()
    }
}

function Test-PeriodCompareInstallation {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$TargetDir,
        [Parameter(Mandatory = $true)]
        [string]$CompatFile,
        [Parameter(Mandatory = $true)]
        [string]$PayloadDir
    )

    if (-not (Test-Path $TargetDir)) {
        return @{
            IsValid = $false
            Error = "Target directory does not exist: $TargetDir"
        }
    }
    if (-not (Test-Path $CompatFile)) {
        return @{
            IsValid = $false
            Error = "Compatibility manifest not found: $CompatFile"
        }
    }

    $compat = Get-Content $CompatFile -Raw | ConvertFrom-Json
    $results = @{
        IsValid = $true
        TargetDir = $TargetDir
        TotalFiles = 0
        MatchesUpstream = 0
        AlreadyPatched = 0
        ModifiedOrCustom = 0
        Missing = 0
        Details = @()
        UserPlugins = @()
    }

    # Inspect user custom plugins in plugins/superset-plugin-*
    $userPluginDir = Join-Path $TargetDir "superset-frontend\plugins"
    if (Test-Path $userPluginDir) {
        $customPlugins = Get-ChildItem -Path $userPluginDir -Directory -Filter "superset-plugin-*"
        foreach ($cp in $customPlugins) {
            $results.UserPlugins += $cp.Name
        }
    }

    foreach ($prop in $compat.files.PSObject.Properties) {
        $relPath = $prop.Name
        $fileInfo = $prop.Value
        $targetFile = Join-Path $TargetDir $relPath
        $payloadFile = Join-Path $PayloadDir $relPath
        $results.TotalFiles++

        if (-not (Test-Path $targetFile)) {
            if ($fileInfo.status -eq "added") {
                # New file not yet installed
                $results.Details += @{ Path = $relPath; Status = "NotInstalled" }
            } else {
                $results.Missing++
                $results.Details += @{ Path = $relPath; Status = "Missing" }
            }
            continue
        }

        $targetHash = Get-LfNormalizedHash -Path $targetFile

        # Check if already identical to payload
        if (Test-Path $payloadFile) {
            $payloadHash = Get-LfNormalizedHash -Path $payloadFile
            if ($targetHash -eq $payloadHash) {
                $results.AlreadyPatched++
                $results.Details += @{ Path = $relPath; Status = "AlreadyPatched" }
                continue
            }
        }

        # Check against upstream 6.1.0 baseline
        if ($fileInfo.upstream_sha256) {
            if ($targetHash -eq $fileInfo.upstream_sha256) {
                $results.MatchesUpstream++
                $results.Details += @{ Path = $relPath; Status = "MatchesUpstream" }
            } else {
                $results.ModifiedOrCustom++
                $results.Details += @{ Path = $relPath; Status = "CustomizedOrDiverged" }
            }
        } else {
            $results.ModifiedOrCustom++
            $results.Details += @{ Path = $relPath; Status = "ExistingNonUpstream" }
        }
    }

    # Check MainPreset.ts for period-compare markers
    $mainPresetPath = Join-Path $TargetDir "superset-frontend\src\visualizations\presets\MainPreset.ts"
    $hasMarkers = $false
    if (Test-Path $mainPresetPath) {
        $content = Get-Content $mainPresetPath -Raw
        if ($content -like "*period-compare:begin*") {
            $hasMarkers = $true
        }
    }
    $results.MainPresetHasMarkers = $hasMarkers

    return $results
}
