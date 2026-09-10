#requires -Version 7.0
<#
.SYNOPSIS
Prepare an isolated synthetic data root for packaged acceptance.

.DESCRIPTION
Runs packaging/prepare_acceptance_data.py with the build interpreter
(explicit -Python, standard venv, or Conda layout). The fixture directory
must be empty or absent; it receives a data root, an isolated locator under
localappdata/, and a README.txt with launch instructions.

.PARAMETER BaseDirectory
Empty (or absent) output directory for the synthetic fixture.

.PARAMETER Python
Explicit path to the interpreter. Defaults to the same resolution as
packaging/build.ps1.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$BaseDirectory,
    [string]$Python
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'toolchain.ps1')

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Resolve-BuildInterpreter -Explicit $Python -ProjectRoot $projectRoot

& $python (Join-Path $PSScriptRoot 'prepare_acceptance_data.py') $BaseDirectory
if ($LASTEXITCODE -ne 0) {
    throw "Acceptance data preparation failed with exit code $LASTEXITCODE."
}
