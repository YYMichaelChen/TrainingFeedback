#requires -Version 7.0
<#
.SYNOPSIS
Build the portable Windows directory layout at dist/TrainingFeedback/.

.DESCRIPTION
Verifies the build interpreter, the pinned PyInstaller version
(requirements-build.txt) and the packaged icon, then runs the spec and
checks that the output is complete and free of user data.
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv' 'python.exe'
$spec = Join-Path $PSScriptRoot 'training_feedback.spec'
$icon = Join-Path $projectRoot 'icon' 'TrainingFeedback.ico'
$requirements = Join-Path $PSScriptRoot 'requirements-build.txt'
$outputDir = Join-Path $projectRoot 'dist' 'TrainingFeedback'

if (-not (Test-Path -LiteralPath $python)) {
    throw "Build interpreter not found: $python (create the project .venv first)."
}
if (-not (Test-Path -LiteralPath $icon)) {
    throw "Packaged icon missing: $icon"
}

$pyinstallerVersion = & $python -m PyInstaller --version
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is not installed; run: & '$python' -m pip install -r '$requirements'"
}
$pinned = (Select-String -LiteralPath $requirements -Pattern '^pyinstaller==(\S+)').Matches.Groups[1].Value
if ($pyinstallerVersion -ne $pinned) {
    throw "PyInstaller $pinned required by requirements-build.txt, found $pyinstallerVersion."
}

& $python -m PyInstaller --clean --noconfirm `
    --distpath (Join-Path $projectRoot 'dist') `
    --workpath (Join-Path $projectRoot 'build') `
    $spec
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed with exit code $LASTEXITCODE."
}

$exe = Join-Path $outputDir 'TrainingFeedback.exe'
foreach ($required in @($exe, (Join-Path $outputDir '_internal' 'sqlite3.dll'))) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Build artifact missing: $required"
    }
}
$leaked = Get-ChildItem -LiteralPath $outputDir -Recurse -File |
    Where-Object { $_.Name -match '^(locator\.json|.*\.sqlite3(-wal|-shm|-journal)?)$' }
if ($leaked) {
    throw "Build output must not contain user data: $($leaked.FullName -join ', ')"
}

Write-Host "Build OK: $exe"
