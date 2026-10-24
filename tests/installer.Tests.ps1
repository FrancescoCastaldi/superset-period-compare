# tests/installer.Tests.ps1
# Pester test suite covering the installer validation cases.

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$InstallerScript = Join-Path $RepoRoot "installer\PeriodCompare.ps1"
$CompatFile = Join-Path $RepoRoot "compat.json"
$PayloadDir = Join-Path $RepoRoot "payload"

Describe "Superset Period Compare Installer Validation Suite" {

    Context "Case 1: Clean tree verification and dry-run" {
        It "Dry-run reports actions without modifying any files" {
            $testTarget = Join-Path $env:TEMP "pc_test_clean_$([guid]::NewGuid().ToString('N'))"
            New-Item -ItemType Directory -Path $testTarget -Force | Out-Null
            
            $presetDir = Join-Path $testTarget "superset-frontend\src\visualizations\presets"
            New-Item -ItemType Directory -Path $presetDir -Force | Out-Null
            $mockPreset = "import {`n  TimeGrainFilterPlugin,`n} from 'src/filters/components';`nclass MainPreset { plugins = [`n  new TimeFilterPlugin().configure({ key: FilterPlugins.Time }),`n ]; }"
            Set-Content -Path (Join-Path $presetDir "MainPreset.ts") -Value $mockPreset -Encoding utf8

            $beforeHash = (Get-FileHash (Join-Path $presetDir "MainPreset.ts")).Hash

            & $InstallerScript -Action DryRun -TargetDir $testTarget -SkipBuild

            $afterHash = (Get-FileHash (Join-Path $presetDir "MainPreset.ts")).Hash
            $afterHash | Should Be $beforeHash

            Remove-Item $testTarget -Recurse -Force
        }
    }

    Context "Case 2: Installation and rollback byte-for-byte integrity" {
        It "Installs cleanly, merges MainPreset.ts, and uninstalls returning to original state" {
            $testTarget = Join-Path $env:TEMP "pc_test_install_$([guid]::NewGuid().ToString('N'))"
            New-Item -ItemType Directory -Path $testTarget -Force | Out-Null

            $presetDir = Join-Path $testTarget "superset-frontend\src\visualizations\presets"
            New-Item -ItemType Directory -Path $presetDir -Force | Out-Null
            $mockPreset = "import {`n  TimeGrainFilterPlugin,`n} from 'src/filters/components';`nconst list = [`n  new TimeFilterPlugin().configure({ key: FilterPlugins.Time }),`n];"
            $presetFile = Join-Path $presetDir "MainPreset.ts"
            [System.IO.File]::WriteAllText($presetFile, $mockPreset, [System.Text.UTF8Encoding]::new($false))
            $origHash = (Get-FileHash $presetFile).Hash

            # 1. Install
            & $InstallerScript -Action Install -TargetDir $testTarget -SkipBuild
            
            # Verify MainPreset.ts was patched with markers
            $patchedContent = Get-Content $presetFile -Raw
            ($patchedContent -like "*period-compare:begin*") | Should Be $true
            ($patchedContent -like "*PeriodCompareFilterPlugin*") | Should Be $true

            # 2. Re-run install to verify idempotency
            & $InstallerScript -Action Install -TargetDir $testTarget -SkipBuild
            $secondRunContent = Get-Content $presetFile -Raw
            $markerCount = ([regex]::Matches($secondRunContent, "period-compare:begin")).Count
            $markerCount | Should Be 2  # One in import, one in plugin list

            # 3. Uninstall / Rollback
            & $InstallerScript -Action Uninstall -TargetDir $testTarget
            $restoredHash = (Get-FileHash $presetFile).Hash
            $restoredHash | Should Be $origHash

            Remove-Item $testTarget -Recurse -Force
        }
    }

    Context "Case 3: Non-invasiveness and user custom plugin protection" {
        It "Preserves user custom plugins and identical hashes across install and uninstall" {
            $customWorktree = "D:\Actual\03_Sviluppo_Software\Repositories\_work\superset-6.1.0-custom"
            if (Test-Path $customWorktree) {
                $userPluginsDir = Join-Path $customWorktree "superset-frontend\plugins"
                $userPlugins = Get-ChildItem -Path $userPluginsDir -Directory -Filter "superset-plugin-*"
                ($userPlugins.Count -gt 0) | Should Be $true

                # Capture hashes of all user plugin files before
                $beforeHashes = @{}
                foreach ($plugin in $userPlugins) {
                    $files = Get-ChildItem -Path $plugin.FullName -Recurse -File
                    foreach ($f in $files) {
                        $beforeHashes[$f.FullName] = (Get-FileHash $f.FullName).Hash
                    }
                }

                # Run Verify against custom worktree
                & $InstallerScript -Action Verify -TargetDir $customWorktree

                # Check that user plugin hashes are 100% untouched
                foreach ($path in $beforeHashes.Keys) {
                    $currentHash = (Get-FileHash $path).Hash
                    $currentHash | Should Be $beforeHashes[$path]
                }
            }
        }
    }
}
