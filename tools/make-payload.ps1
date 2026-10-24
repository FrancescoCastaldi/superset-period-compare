# Tools: make-payload.ps1
# Extracts modified files and new files from the worktree into the payload/ folder,
# and generates compat.json containing SHA-256 hashes of the upstream 6.1.0 baseline.

param(
    [string]$WorktreePath = "D:\Actual\03_Sviluppo_Software\Repositories\_work\superset-6.1.0-pc",
    [string]$OutputDir = "$PSScriptRoot\..\payload",
    [string]$CompatFile = "$PSScriptRoot\..\compat.json",
    [string]$BaseTag = "6.1.0"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $WorktreePath)) {
    throw "Worktree path not found: $WorktreePath"
}

Write-Host "Analyzing git diff between $BaseTag and HEAD in $WorktreePath..."
$diffLines = git -C $WorktreePath diff --name-status $BaseTag HEAD

$compatMap = @{
    version = "6.1.0"
    generated_at = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    files = @{}
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$fileCount = 0

foreach ($line in $diffLines) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $parts = $line.Split("`t")
    $status = $parts[0].Trim()
    $relPath = $parts[1].Trim()

    # Skip files that should not be in the distribution payload
    if ($relPath -like "tests/*" -or $relPath -like "*verify-*.mjs") {
        continue
    }

    $srcFile = Join-Path $WorktreePath $relPath
    $destFile = Join-Path $OutputDir $relPath
    $destDir = Split-Path $destFile -Parent

    if (-not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }

    Copy-Item -Path $srcFile -Destination $destFile -Force
    $fileCount++

    # If file was modified (M), calculate original 6.1.0 hash for compatibility verification
    if ($status -eq "M") {
        $tempOriginal = [System.IO.Path]::GetTempFileName()
        try {
            # Il blob upstream va scritto byte per byte: la pipe di PowerShell con
            # Set-Content -NoNewline toglie gli a capo e aggiunge il BOM, e l'hash
            # non coinciderebbe mai con quello di un file reale.
            Start-Process -FilePath git -ArgumentList @("-C", $WorktreePath, "cat-file", "blob", "$($BaseTag):$relPath") -RedirectStandardOutput $tempOriginal -NoNewWindow -Wait
            $bytes = [System.IO.File]::ReadAllBytes($tempOriginal)
            $lf = New-Object System.IO.MemoryStream
            for ($i = 0; $i -lt $bytes.Length; $i++) {
                if ($bytes[$i] -eq 13 -and ($i + 1) -lt $bytes.Length -and $bytes[$i + 1] -eq 10) { continue }
                $lf.WriteByte($bytes[$i])
            }
            $sha = [System.Security.Cryptography.SHA256]::Create()
            $origHash = ([System.BitConverter]::ToString($sha.ComputeHash($lf.ToArray()))).Replace("-", "")
            $sha.Dispose(); $lf.Dispose()
            $compatMap.files[$relPath] = @{
                status = "modified"
                upstream_sha256 = $origHash
            }
        } finally {
            if (Test-Path $tempOriginal) { Remove-Item $tempOriginal -Force }
        }
    } elseif ($status -eq "A") {
        $compatMap.files[$relPath] = @{
            status = "added"
            upstream_sha256 = $null
        }
    }
}

$compatJson = $compatMap | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText($CompatFile, $compatJson, [System.Text.UTF8Encoding]::new($false))

Write-Host "Payload generated successfully: $fileCount files copied to $OutputDir."
Write-Host "Compatibility manifest written to $CompatFile."
