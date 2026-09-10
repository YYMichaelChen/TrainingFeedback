#requires -Version 7.0
# Shared build-toolchain helpers for packaging/*.ps1 (dot-source this file).

Set-StrictMode -Version Latest

function Resolve-BuildInterpreter {
    <#
    .SYNOPSIS
    Resolve the Python interpreter used for packaging tasks.

    .DESCRIPTION
    Order: explicit -Python value, then the standard-venv layout
    (.venv/Scripts/python.exe), then the Conda layout (.venv/python.exe).
    Fails with a readable message when no candidate exists or the explicit
    value is not a file.
    #>
    param(
        [string]$Explicit,
        [Parameter(Mandatory = $true)][string]$ProjectRoot
    )
    if ($Explicit) {
        $candidate = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Explicit)
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            throw "Explicit build interpreter not found: $candidate"
        }
        return $candidate
    }
    $layouts = @(
        (Join-Path $ProjectRoot '.venv' 'Scripts' 'python.exe'),  # standard venv
        (Join-Path $ProjectRoot '.venv' 'python.exe')             # conda env named .venv
    )
    foreach ($candidate in $layouts) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }
    $lines = @("Build interpreter not found. Checked:")
    $lines += @($layouts | ForEach-Object { "  $_" })
    $lines += @(
        "Create a standard venv (python -m venv .venv) or a Conda env at .venv,",
        "or pass an explicit interpreter with -Python."
    )
    throw ($lines -join [Environment]::NewLine)
}

function Get-PythonFact {
    <#
    .SYNOPSIS
    Run a short Python snippet with the build interpreter and return stdout.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Interpreter,
        [Parameter(Mandatory = $true)][string]$Code
    )
    $output = & $Interpreter -c $Code 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python probe failed ($Interpreter): $output"
    }
    return ($output | Out-String).Trim()
}

function Get-PinnedRequirement {
    <#
    .SYNOPSIS
    Read the pinned version of a requirement (name==version) from a requirements file.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$RequirementsFile,
        [Parameter(Mandatory = $true)][string]$Name
    )
    $match = Select-String -LiteralPath $RequirementsFile -Pattern "(?i)^$([regex]::Escape($Name))==(\S+)"
    if (-not $match) {
        throw "Pinned requirement '$Name' not found in $RequirementsFile."
    }
    return $match.Matches[0].Groups[1].Value
}

function Assert-PinnedPackage {
    <#
    .SYNOPSIS
    Fail unless the installed package version matches the pinned version.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Interpreter,
        [Parameter(Mandatory = $true)][string]$RequirementsFile,
        [Parameter(Mandatory = $true)][string]$Name
    )
    $pinned = Get-PinnedRequirement -RequirementsFile $RequirementsFile -Name $Name
    $actual = Get-PythonFact -Interpreter $Interpreter -Code "import importlib.metadata as m; print(m.version('$Name'))"
    if ($actual -ne $pinned) {
        throw "$Name $pinned required by requirements-build.txt, found $actual. Run: & '$Interpreter' -m pip install -r '$RequirementsFile'"
    }
    return $actual
}
