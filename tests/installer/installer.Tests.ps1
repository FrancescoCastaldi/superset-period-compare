# tests/installer/installer.Tests.ps1
# Pester 3.4 test suite for the installer.
#
# Cases 3 to 5 run against a real Superset tree that contains user plugins. Point the
# PERIOD_COMPARE_TEST_TREE environment variable to such a tree to enable them; they
# are skipped when it is not set. The tree is restored byte for byte after each case.

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$InstallerScript = Join-Path $RepoRoot "installer\PeriodCompare.ps1"
$CompatFile = Join-Path $RepoRoot "compat\compat.json"
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
        It "Preserves user custom plugins and identical hashes across verify" {
            $customWorktree = $env:PERIOD_COMPARE_TEST_TREE
            if ($customWorktree -and (Test-Path $customWorktree)) {
                $userPluginsDir = Join-Path $customWorktree "superset-frontend\plugins"
                $userPlugins = Get-ChildItem -Path $userPluginsDir -Directory -Filter "superset-plugin-*"
                ($userPlugins.Count -gt 0) | Should Be $true

                # Capture hashes of entry files in user plugins
                $beforeHashes = @{}
                foreach ($plugin in $userPlugins) {
                    $pkgJson = Join-Path $plugin.FullName "package.json"
                    if (Test-Path $pkgJson) {
                        $beforeHashes[$pkgJson] = (Get-FileHash $pkgJson).Hash
                    }
                    $indexTs = Join-Path $plugin.FullName "src\index.ts"
                    if (Test-Path $indexTs) {
                        $beforeHashes[$indexTs] = (Get-FileHash $indexTs).Hash
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

    Context "Case 4: Automatic project directory recognition" {
        It "Automatically detects candidate project when TargetDir is omitted" {
            $customWorktree = $env:PERIOD_COMPARE_TEST_TREE
            if ($customWorktree -and (Test-Path $customWorktree)) {
                $env:CALLER_DIR = $customWorktree
                try {
                    # Verify action runs with no TargetDir passed, relying on auto-detection
                    & $InstallerScript -Action Verify
                    $? | Should Be $true
                } finally {
                    $env:CALLER_DIR = $null
                }
            }
        }
    }

    Context "Case 5: Full End-to-End Install, Verify, and Rollback on existing project" {
        It "Applies patch to existing custom project, protects user plugins, and restores cleanly" {
            $customWorktree = $env:PERIOD_COMPARE_TEST_TREE
            if ($customWorktree -and (Test-Path $customWorktree)) {
                $presetPath = Join-Path $customWorktree "superset-frontend\src\visualizations\presets\MainPreset.ts"
                $origPresetHash = (Get-FileHash $presetPath).Hash

                # Record hashes of user custom plugins
                $userPluginsDir = Join-Path $customWorktree "superset-frontend\plugins"
                $userPlugins = Get-ChildItem -Path $userPluginsDir -Directory -Filter "superset-plugin-*"
                $pluginFiles = @{}
                foreach ($p in $userPlugins) {
                    Get-ChildItem -Path $p.FullName -Recurse -File | ForEach-Object {
                        $pluginFiles[$_.FullName] = (Get-FileHash $_.FullName).Hash
                    }
                }

                # 1. Install patch with auto-build skip
                & $InstallerScript -Action Install -TargetDir $customWorktree -SkipBuild

                # 2. Check that MainPreset has markers and user plugins
                $patchedPreset = Get-Content $presetPath -Raw
                ($patchedPreset -like "*period-compare:begin*") | Should Be $true
                ($patchedPreset -like "*PeriodCompareFilterPlugin*") | Should Be $true
                ($patchedPreset -like "*HierarchicalTableChartPlugin*") | Should Be $true
                ($patchedPreset -like "*StratumBarChartPlugin*") | Should Be $true

                # Check user plugin files are untouched
                foreach ($fp in $pluginFiles.Keys) {
                    (Get-FileHash $fp).Hash | Should Be $pluginFiles[$fp]
                }

                # 3. Test idempotency: re-running install should not duplicate markers
                & $InstallerScript -Action Install -TargetDir $customWorktree -SkipBuild
                $secondPreset = Get-Content $presetPath -Raw
                $markerCount = ([regex]::Matches($secondPreset, "period-compare:begin")).Count
                $markerCount | Should Be 2

                # 4. Verify action reports valid state
                & $InstallerScript -Action Verify -TargetDir $customWorktree

                # 5. Uninstall and verify byte-for-byte rollback
                & $InstallerScript -Action Uninstall -TargetDir $customWorktree
                $restoredPresetHash = (Get-FileHash $presetPath).Hash
                $restoredPresetHash | Should Be $origPresetHash

                # User plugins still 100% untouched
                foreach ($fp in $pluginFiles.Keys) {
                    (Get-FileHash $fp).Hash | Should Be $pluginFiles[$fp]
                }

                # PeriodCompare directory should be cleaned up
                $pcFilterDir = Join-Path $customWorktree "superset-frontend\src\filters\components\PeriodCompare"
                (Test-Path $pcFilterDir) | Should Be $false
            }
        }
    }
}


Describe "Verify: upstream detection independent of line endings" {

    $VerifyScript = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")) "installer\lib\Verify.ps1"
    . $VerifyScript

    function New-VerifyFixture {
        param([string]$TargetContent, [string]$PayloadContent, [string]$UpstreamLfContent)
        $root = Join-Path $env:TEMP "pc_verify_$([guid]::NewGuid().ToString('N'))"
        $target = Join-Path $root "target"
        $payload = Join-Path $root "payload"
        New-Item -ItemType Directory -Path $target, $payload -Force | Out-Null
        [System.IO.File]::WriteAllText((Join-Path $target "a.txt"), $TargetContent, [System.Text.UTF8Encoding]::new($false))
        [System.IO.File]::WriteAllText((Join-Path $payload "a.txt"), $PayloadContent, [System.Text.UTF8Encoding]::new($false))
        $sha = [System.Security.Cryptography.SHA256]::Create()
        $hash = ([System.BitConverter]::ToString($sha.ComputeHash([System.Text.UTF8Encoding]::new($false).GetBytes($UpstreamLfContent)))).Replace("-", "")
        $compat = @{ version = "6.1.0"; files = @{ "a.txt" = @{ status = "modified"; upstream_sha256 = $hash } } }
        $compatFile = Join-Path $root "compat.json"
        [System.IO.File]::WriteAllText($compatFile, ($compat | ConvertTo-Json -Depth 5), [System.Text.UTF8Encoding]::new($false))
        return @{ Root = $root; Target = $target; Payload = $payload; Compat = $compatFile }
    }

    It "recognizes a CRLF file whose LF hash is in compat.json as upstream" {
        $fx = New-VerifyFixture -TargetContent "riga1`r`nriga2`r`n" -PayloadContent "patched`n" -UpstreamLfContent "riga1`nriga2`n"
        $r = Test-PeriodCompareInstallation -TargetDir $fx.Target -CompatFile $fx.Compat -PayloadDir $fx.Payload
        $r.MatchesUpstream | Should Be 1
        $r.ModifiedOrCustom | Should Be 0
        Remove-Item $fx.Root -Recurse -Force
    }

    It "recognizes an LF file as upstream" {
        $fx = New-VerifyFixture -TargetContent "riga1`nriga2`n" -PayloadContent "patched`n" -UpstreamLfContent "riga1`nriga2`n"
        $r = Test-PeriodCompareInstallation -TargetDir $fx.Target -CompatFile $fx.Compat -PayloadDir $fx.Payload
        $r.MatchesUpstream | Should Be 1
        Remove-Item $fx.Root -Recurse -Force
    }

    It "flags a file with genuinely different content as modified" {
        $fx = New-VerifyFixture -TargetContent "riga1`r`nMODIFICATA`r`n" -PayloadContent "patched`n" -UpstreamLfContent "riga1`nriga2`n"
        $r = Test-PeriodCompareInstallation -TargetDir $fx.Target -CompatFile $fx.Compat -PayloadDir $fx.Payload
        $r.MatchesUpstream | Should Be 0
        $r.ModifiedOrCustom | Should Be 1
        Remove-Item $fx.Root -Recurse -Force
    }

    It "recognizes a CRLF file equal to the LF payload as already patched" {
        $fx = New-VerifyFixture -TargetContent "patched`r`nlinea2`r`n" -PayloadContent "patched`nlinea2`n" -UpstreamLfContent "riga1`nriga2`n"
        $r = Test-PeriodCompareInstallation -TargetDir $fx.Target -CompatFile $fx.Compat -PayloadDir $fx.Payload
        $r.AlreadyPatched | Should Be 1
        Remove-Item $fx.Root -Recurse -Force
    }
}

Describe "Installer: file modification times" {

    $RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
    $InstallerScript = Join-Path $RepoRoot "installer\PeriodCompare.ps1"
    $PayloadDir = Join-Path $RepoRoot "payload"

    function New-MockSupersetTree {
        $root = Join-Path $env:TEMP "pc_mtime_$([guid]::NewGuid().ToString('N'))"
        $presetDir = Join-Path $root "superset-frontend\src\visualizations\presets"
        New-Item -ItemType Directory -Path $presetDir -Force | Out-Null
        $mock = "import {`n  TimeGrainFilterPlugin,`n} from 'src/filters/components';`nconst list = [`n  new TimeFilterPlugin().configure({ key: FilterPlugins.Time }),`n];"
        [System.IO.File]::WriteAllText((Join-Path $presetDir "MainPreset.ts"), $mock, [System.Text.UTF8Encoding]::new($false))
        return $root
    }

    # tsc -b and webpack decide what to recompile by comparing file timestamps: a file
    # copied with the old payload timestamp would be considered already compiled.
    It "after Install every payload file carries the installation timestamp" {
        $root = New-MockSupersetTree
        $before = (Get-Date).AddSeconds(-2)
        & $InstallerScript -Action Install -TargetDir $root -SkipBuild | Out-Null
        $stale = @()
        $prefixLength = $PayloadDir.ToString().Length
        foreach ($f in (Get-ChildItem $PayloadDir -Recurse -File)) {
            $rel = $f.FullName.Substring($prefixLength).TrimStart([char]92, [char]47)
            $t = Get-Item (Join-Path $root $rel)
            if ($t.LastWriteTime -lt $before) { $stale += $rel }
        }
        $stale.Count | Should Be 0
        & $InstallerScript -Action Uninstall -TargetDir $root | Out-Null
        Remove-Item -LiteralPath $root -Recurse -Force
    }

    It "after Uninstall restored files carry the restore timestamp" {
        $root = New-MockSupersetTree
        $existing = Join-Path $root "superset\config.py"
        New-Item -ItemType Directory -Path (Split-Path $existing -Parent) -Force | Out-Null
        [System.IO.File]::WriteAllText($existing, "ORIGINAL = 1`n", [System.Text.UTF8Encoding]::new($false))
        (Get-Item $existing).LastWriteTime = (Get-Date).AddYears(-1)
        & $InstallerScript -Action Install -TargetDir $root -SkipBuild | Out-Null
        $before = (Get-Date).AddSeconds(-2)
        & $InstallerScript -Action Uninstall -TargetDir $root | Out-Null
        (Get-Content $existing -Raw).Trim() | Should Be "ORIGINAL = 1"
        ((Get-Item $existing).LastWriteTime -ge $before) | Should Be $true
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}
