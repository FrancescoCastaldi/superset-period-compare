# installer/lib/BuildFrontend.ps1
# Optionally compiles superset-frontend assets after patching.

function Invoke-PeriodCompareFrontendBuild {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$TargetDir,
        [switch]$SkipBuild
    )

    if ($SkipBuild) {
        Write-Host "Frontend build skipped by user request (-SkipBuild)." -ForegroundColor Yellow
        return $true
    }

    $frontendDir = Join-Path $TargetDir "superset-frontend"
    if (-not (Test-Path $frontendDir)) {
        Write-Warning "superset-frontend not found in $TargetDir. Skipping build."
        return $false
    }

    Write-Host "Starting frontend build in $frontendDir..." -ForegroundColor Cyan
    Write-Host "Configuring NODE_OPTIONS=--max-old-space-size=8192..."
    $env:NODE_OPTIONS = "--max-old-space-size=8192"

    Push-Location $frontendDir
    try {
        Write-Host "Running npm run build..."
        npm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Frontend build returned code $LASTEXITCODE. You may rebuild manually via 'npm run build'."
            return $false
        }
        Write-Host "Frontend build completed successfully." -ForegroundColor Green
        return $true
    } finally {
        Pop-Location
    }
}
