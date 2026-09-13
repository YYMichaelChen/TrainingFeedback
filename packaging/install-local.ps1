#requires -Version 7.0
<#
.SYNOPSIS
Install a verified candidate into a versioned program directory and create
shortcuts, without touching any user data root.

.DESCRIPTION
Copies the candidate program directory to <InstallRoot>\<version>, verifies every
installed file against the candidate build manifest (path, size, SHA-256, and no
extra files), preserves the manifest and source identity next to the installed
version, creates Start Menu (and optionally desktop) shortcuts, and records the
installation facts. Existing versions are never overwritten unless -Force is
given, so an upgrade keeps the previous version available for rollback. The
script never reads or writes a data root; the user chooses that at first launch.

.PARAMETER CandidateRoot
Directory holding the candidate: a TrainingFeedback program directory plus its
TrainingFeedback.build-manifest.json.

.PARAMETER InstallRoot
Program installation parent directory, for example
'D:\Program Files\TrainingFeedback'. The version subdirectory is created here.

.PARAMETER DesktopShortcut
Also create a desktop shortcut.

.PARAMETER Force
Replace an already installed directory for the same version.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$CandidateRoot,
    [Parameter(Mandatory)][string]$InstallRoot,
    [switch]$DesktopShortcut,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-RelativeHashMap {
    param([Parameter(Mandatory)][string]$Root)
    $map = @{}
    foreach ($file in Get-ChildItem -LiteralPath $Root -Recurse -File) {
        $relative = $file.FullName.Substring($Root.Length + 1)
        $map[$relative] = [ordered]@{
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            bytes  = $file.Length
        }
    }
    return $map
}

function Compare-InstalledFiles {
    param(
        [Parameter(Mandatory)][hashtable]$Expected,
        [Parameter(Mandatory)][hashtable]$Actual
    )
    $problems = [System.Collections.Generic.List[string]]::new()
    foreach ($relative in $Expected.Keys) {
        if (-not $Actual.ContainsKey($relative)) {
            $problems.Add("missing $relative")
            continue
        }
        if ($Actual[$relative].sha256 -ne $Expected[$relative].sha256) {
            $problems.Add("hash mismatch $relative")
        }
        elseif ($Actual[$relative].bytes -ne $Expected[$relative].bytes) {
            $problems.Add("size mismatch $relative")
        }
    }
    foreach ($relative in $Actual.Keys) {
        if (-not $Expected.ContainsKey($relative)) {
            $problems.Add("unexpected file $relative")
        }
    }
    return $problems
}

$candidate = (Resolve-Path -LiteralPath $CandidateRoot).Path
$programDir = Join-Path $candidate 'TrainingFeedback'
$manifestPath = Join-Path $candidate 'TrainingFeedback.build-manifest.json'
foreach ($required in @($programDir, $manifestPath, (Join-Path $programDir 'TrainingFeedback.exe'))) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "Candidate is incomplete: $required is missing."
    }
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$version = $manifest.application_version
if (-not $version) {
    throw "Candidate manifest does not declare application_version: $manifestPath"
}

# The manifest is the candidate identity. Verify the source before installing so a
# damaged candidate is never copied into the program directory.
$expected = @{}
foreach ($entry in $manifest.artifact_hashes) {
    $expected[$entry.path] = [ordered]@{ sha256 = $entry.sha256.ToLowerInvariant(); bytes = [int64]$entry.bytes }
}
$sourceHashes = Get-RelativeHashMap -Root $programDir
$sourceProblems = @(Compare-InstalledFiles -Expected $expected -Actual $sourceHashes)
if ($sourceProblems.Count -gt 0) {
    throw "Candidate does not match its manifest: $($sourceProblems -join '; ')"
}

$targetParent = $InstallRoot
$target = Join-Path $targetParent $version
if (Test-Path -LiteralPath $target) {
    if (-not $Force) {
        throw "Version $version is already installed at $target. Use -Force to replace it."
    }
    Write-Host "Replacing existing installation: $target"
    [System.IO.Directory]::Delete($target, $true)
}
New-Item -Path $targetParent -ItemType Directory -Force | Out-Null
# Copy the candidate directory itself so the installed version directory is an
# exact copy and no wildcard expansion is involved.
Copy-Item -LiteralPath $programDir -Destination $target -Recurse

# Verify the installed copy, not the source, so a partial copy cannot be reported
# as a successful installation.
$installedHashes = Get-RelativeHashMap -Root $target
$problems = @(Compare-InstalledFiles -Expected $expected -Actual $installedHashes)
if ($problems.Count -gt 0) {
    throw "Installed files do not match the manifest: $($problems -join '; ')"
}

# Keep the candidate identity with the installed version so a later upgrade can
# be compared against what is actually running.
Copy-Item -LiteralPath $manifestPath -Destination (Join-Path $targetParent "TrainingFeedback-$version.build-manifest.json") -Force
$sourceIdentity = Join-Path $candidate 'source-identity.json'
if (Test-Path -LiteralPath $sourceIdentity) {
    Copy-Item -LiteralPath $sourceIdentity -Destination (Join-Path $targetParent "TrainingFeedback-$version.source-identity.json") -Force
}

$exe = Join-Path $target 'TrainingFeedback.exe'
$shell = New-Object -ComObject WScript.Shell
$shortcutTargets = [System.Collections.Generic.List[string]]::new()
$startMenu = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\TrainingFeedback.lnk'
$shortcutPaths = @($startMenu)
if ($DesktopShortcut) {
    $shortcutPaths += Join-Path ([Environment]::GetFolderPath('Desktop')) 'TrainingFeedback.lnk'
}
foreach ($path in $shortcutPaths) {
    $shortcut = $shell.CreateShortcut($path)
    $shortcut.TargetPath = $exe
    $shortcut.WorkingDirectory = $target
    $shortcut.IconLocation = $exe
    $shortcut.Description = "TrainingFeedback $version"
    $shortcut.Save()
    $shortcutTargets.Add($path)
}

$recordDir = Join-Path $targetParent 'install-records'
New-Item -Path $recordDir -ItemType Directory -Force | Out-Null
$record = [ordered]@{
    record_schema        = 1
    installed_at         = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    application          = 'TrainingFeedback'
    application_version  = $version
    install_directory    = $target
    entry_point          = $exe
    candidate_root       = $candidate
    manifest_sha256      = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
    manifest_file_count  = $expected.Count
    verified_files       = $installedHashes.Count
    manifest_verified    = $true
    shortcuts            = @($shortcutTargets)
    data_root_touched    = $false
}
$recordPath = Join-Path $recordDir "install-$version-$((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')).json"
$record | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $recordPath -Encoding utf8

Write-Host "Installed ${version}: $exe (verified $($installedHashes.Count) files)"
Write-Host "Shortcuts: $($shortcutTargets -join ', ')"
Write-Host "Install record: $recordPath"
Write-Host "The data root is chosen at first launch and is never created by this script."
