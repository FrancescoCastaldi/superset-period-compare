# installer/lib/Backup.ps1
# Creates a byte-for-byte rollback backup of all files to be patched.

function New-PeriodCompareBackup {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$TargetDir,
        [Parameter(Mandatory = $true)]
        [string]$CompatFile,
        [string]$BackupDir = ""
    )

    if (-not (Test-Path $TargetDir)) {
        throw "Target directory does not exist: $TargetDir"
    }
    if (-not (Test-Path $CompatFile)) {
        throw "Compatibility manifest not found: $CompatFile"
    }

    $compat = Get-Content $CompatFile -Raw | ConvertFrom-Json
    $timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
    if ([string]::IsNullOrWhiteSpace($BackupDir)) {
        $BackupDir = Join-Path $TargetDir ".backups\backup_$timestamp"
    }

    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    }

    $manifest = @{
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
        target_dir = $TargetDir
        files = @()
    }

    foreach ($prop in $compat.files.PSObject.Properties) {
        $relPath = $prop.Name
        $targetFile = Join-Path $TargetDir $relPath

        if (Test-Path $targetFile) {
            $destFile = Join-Path $BackupDir $relPath
            $destSubdir = Split-Path $destFile -Parent
            if (-not (Test-Path $destSubdir)) {
                New-Item -ItemType Directory -Path $destSubdir -Force | Out-Null
            }
            Copy-Item -Path $targetFile -Destination $destFile -Force
            $fileHash = (Get-FileHash -Path $targetFile -Algorithm SHA256).Hash
            $manifest.files += @{
                path = $relPath
                sha256 = $fileHash
                action = "modified"
            }
        } else {
            $manifest.files += @{
                path = $relPath
                sha256 = $null
                action = "added"
            }
        }
    }

    $manifestPath = Join-Path $BackupDir "backup-manifest.json"
    $manifestJson = $manifest | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($manifestPath, $manifestJson, [System.Text.UTF8Encoding]::new($false))

    Write-Host "Rollback backup successfully created in: $BackupDir" -ForegroundColor Green
    return $BackupDir
}
