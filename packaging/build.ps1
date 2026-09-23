#requires -Version 7.0
<#
.SYNOPSIS
Build the portable Windows directory layout at dist/TrainingFeedback/.

.DESCRIPTION
Resolves the build interpreter (explicit -Python, standard venv, or Conda
layout), verifies the pinned packaging dependencies and the declared
Python/PySide6 build baseline, isolates binary discovery from unrelated PATH
entries, runs the spec, checks that the output is complete and free of user
data, and records a build manifest with versions, source revision, and artifact
hashes next to the output directory.

.PARAMETER Python
Explicit path to the build interpreter. Defaults to .venv\Scripts\python.exe
(standard venv) or .venv\python.exe (Conda layout).

.PARAMETER Installer
Also compile the directory build into a conventional Windows Setup.exe with
Inno Setup 6. The installer upgrades the same per-user program directory and
does not own the application's data root.

.PARAMETER ISCC
Explicit path to Inno Setup's ISCC.exe. When -Installer is used and this is
omitted, standard Inno Setup 6 locations and PATH are checked.
#>
[CmdletBinding()]
param(
    [string]$Python,
    [switch]$Installer,
    [string]$ISCC
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'toolchain.ps1')

# Declared build baseline; change only after verifying a new toolchain.
$BaselinePythonMajorMinor = '3.12'
$BaselinePySide6 = '6.11.2'

$projectRoot = Split-Path -Parent $PSScriptRoot
$spec = Join-Path $PSScriptRoot 'training_feedback.spec'
$icon = Join-Path $projectRoot 'icon' 'TrainingFeedback.ico'
$requirements = Join-Path $PSScriptRoot 'requirements-build.txt'
$pyproject = Join-Path $projectRoot 'pyproject.toml'
$installerSpec = Join-Path $PSScriptRoot 'training_feedback.iss'
$distDir = Join-Path $projectRoot 'dist'
$outputDir = Join-Path $distDir 'TrainingFeedback'
$manifestPath = Join-Path $distDir 'TrainingFeedback.build-manifest.json'
$installerOutputDir = Join-Path $distDir 'installer'

$python = Resolve-BuildInterpreter -Explicit $Python -ProjectRoot $projectRoot
& $python (Join-Path $PSScriptRoot 'build_catalog.py') --verify (Join-Path $projectRoot 'src/training_feedback/catalog')
if ($LASTEXITCODE -ne 0) {
    throw 'Program catalog verification failed.'
}
if (-not (Test-Path -LiteralPath $icon)) {
    throw "Packaged icon missing: $icon"
}

# Pinned packaging dependencies.
$pyinstallerVersion = Assert-PinnedPackage -Interpreter $python -RequirementsFile $requirements -Name 'pyinstaller'
$hooksVersion = Assert-PinnedPackage -Interpreter $python -RequirementsFile $requirements -Name 'pyinstaller-hooks-contrib'

# Declared build baseline.
$pythonVersion = Get-PythonFact -Interpreter $python -Code "import platform; print(platform.python_version())"
$pythonArchitecture = Get-PythonFact -Interpreter $python -Code "import platform; print(platform.machine())"
$pySide6Version = Get-PythonFact -Interpreter $python -Code "import importlib.metadata as m; print(m.version('PySide6'))"
$pythonPrefix = Get-PythonFact -Interpreter $python -Code "import sys; print(sys.prefix)"
$pythonBasePrefix = Get-PythonFact -Interpreter $python -Code "import sys; print(sys.base_prefix)"
if (-not $pythonVersion.StartsWith("$BaselinePythonMajorMinor.")) {
    throw "Build baseline is Python $BaselinePythonMajorMinor.x, found $pythonVersion. Verify the new toolchain before updating the baseline in packaging/build.ps1."
}
if ($pySide6Version -ne $BaselinePySide6) {
    throw "Build baseline is PySide6 $BaselinePySide6, found $pySide6Version. Verify the new toolchain before updating the baseline in packaging/build.ps1."
}

$applicationVersion = (Select-String -LiteralPath $pyproject -Pattern '^version = "(.+)"').Matches[0].Groups[1].Value

# PyInstaller searches PATH for transitive DLLs. Limit that search to the
# selected interpreter and Windows so unrelated developer tools cannot leak
# incompatible same-named binaries into the candidate.
$pathBeforeBuild = $env:PATH
$isolatedPathEntries = @(
    (Split-Path -Parent $python),
    $pythonPrefix,
    (Join-Path $pythonPrefix 'Scripts'),
    (Join-Path $pythonPrefix 'DLLs'),
    (Join-Path $pythonPrefix 'Library\bin'),
    $pythonBasePrefix,
    (Join-Path $pythonBasePrefix 'Scripts'),
    (Join-Path $pythonBasePrefix 'DLLs'),
    (Join-Path $pythonBasePrefix 'Library\bin'),
    (Join-Path $env:SystemRoot 'System32'),
    $env:SystemRoot
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique
try {
    $env:PATH = $isolatedPathEntries -join [System.IO.Path]::PathSeparator
    & $python -m PyInstaller --clean --noconfirm `
        --distpath $distDir `
        --workpath (Join-Path $projectRoot 'build') `
        $spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed with exit code $LASTEXITCODE."
    }
}
finally {
    $env:PATH = $pathBeforeBuild
}

$exe = Join-Path $outputDir 'TrainingFeedback.exe'
foreach ($required in @($exe, (Join-Path $outputDir '_internal' 'sqlite3.dll'))) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Build artifact missing: $required"
    }
}
$catalogDir = Join-Path $outputDir '_internal/training_feedback/catalog'
& $python (Join-Path $PSScriptRoot 'build_catalog.py') --verify $catalogDir
if ($LASTEXITCODE -ne 0) {
    throw 'Packaged catalog verification failed.'
}
$catalogDatabase = Join-Path $catalogDir 'catalog.sqlite3'
$leaked = Get-ChildItem -LiteralPath $outputDir -Recurse -File |
    Where-Object {
        $_.Name -match '^(locator\.json|.*\.sqlite3(-wal|-shm|-journal)?)$' -and
        $_.FullName -ne $catalogDatabase
    }
if ($leaked) {
    throw "Build output must not contain user data: $($leaked.FullName -join ', ')"
}

# Build manifest: identifies the candidate and records artifact hashes.
$sourceRevision = $null
$sourceDirty = $null
try {
    $sourceRevision = (& git -C $projectRoot rev-parse HEAD 2>$null)
    if ($LASTEXITCODE -eq 0) {
        $sourceDirty = [bool](& git -C $projectRoot status --porcelain)
    }
    else {
        $sourceRevision = $null
    }
}
catch {
    $sourceRevision = $null
}

$files = Get-ChildItem -LiteralPath $outputDir -Recurse -File
$hashes = foreach ($file in $files) {
    [ordered]@{
        path   = $file.FullName.Substring($outputDir.Length + 1)
        sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        bytes  = $file.Length
    }
}
$manifest = [ordered]@{
    manifest_schema            = 1
    built_at                   = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    application                = 'TrainingFeedback'
    application_version        = $applicationVersion
    output_directory           = "dist/TrainingFeedback"
    entry_point                = "dist/TrainingFeedback/TrainingFeedback.exe"
    interpreter                = $python
    python_version             = $pythonVersion
    architecture               = $pythonArchitecture
    pyside6_version            = $pySide6Version
    pyinstaller_version        = $pyinstallerVersion
    pyinstaller_hooks_contrib  = $hooksVersion
    isolated_binary_discovery  = $true
    source_revision            = $sourceRevision
    source_dirty               = $sourceDirty
    file_count                 = $hashes.Count
    artifact_hashes            = $hashes
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8

Write-Host "Build OK: $exe"
Write-Host "Manifest: $manifestPath (files: $($hashes.Count), Python $pythonVersion $pythonArchitecture, PySide6 $pySide6Version)"

if ($Installer) {
    if (-not (Test-Path -LiteralPath $installerSpec -PathType Leaf)) {
        throw "Installer specification missing: $installerSpec"
    }

    $isccCandidates = [System.Collections.Generic.List[string]]::new()
    if ($ISCC) {
        $isccCandidates.Add($ISCC)
    }
    else {
        $isccCandidates.Add('iscc.exe')
        $isccCandidates.Add((Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'))
        $isccCandidates.Add((Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'))
        $isccCandidates.Add((Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe'))
    }
    $isccPath = $null
    foreach ($candidate in $isccCandidates) {
        if ($candidate -eq 'iscc.exe') {
            $command = Get-Command $candidate -ErrorAction SilentlyContinue
            if ($command) {
                $isccPath = $command.Source
                break
            }
            continue
        }
        $resolved = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($candidate)
        if (Test-Path -LiteralPath $resolved -PathType Leaf) {
            $isccPath = $resolved
            break
        }
    }
    if (-not $isccPath) {
        throw "Inno Setup compiler not found. Install Inno Setup 6 or pass -ISCC 'C:\Path\ISCC.exe'."
    }

    New-Item -Path $installerOutputDir -ItemType Directory -Force | Out-Null
    # ISCC receives each PowerShell array item as one argument, so embedded
    # quote characters would become part of the preprocessor value.
    $sourceArg = "/DSourceDir=$outputDir"
    $outputArg = "/DOutputDir=$installerOutputDir"
    & $isccPath "/DAppVersion=$applicationVersion" $sourceArg $outputArg $installerSpec
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compilation failed with exit code $LASTEXITCODE."
    }
    $installerPath = Join-Path $installerOutputDir "TrainingFeedback-$applicationVersion-Setup.exe"
    if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
        throw "Inno Setup reported success but the installer is missing: $installerPath"
    }
    $installerFile = Get-Item -LiteralPath $installerPath
    $installerManifest = [ordered]@{
        manifest_schema        = 1
        built_at               = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        application            = 'TrainingFeedback'
        application_version    = $applicationVersion
        installer              = $installerFile.Name
        installer_sha256       = (Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash.ToLowerInvariant()
        installer_bytes        = $installerFile.Length
        inno_setup_compiler     = $isccPath
        payload_build_manifest = $manifest
    }
    $installerManifestPath = Join-Path $installerOutputDir "TrainingFeedback-$applicationVersion-Setup.build-manifest.json"
    $installerManifest | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $installerManifestPath -Encoding utf8
    Write-Host "Installer OK: $installerPath"
    Write-Host "Installer manifest: $installerManifestPath"
}
