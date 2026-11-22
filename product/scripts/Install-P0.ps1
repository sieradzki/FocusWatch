# Install the synthetic P0 for the current user. Does not start a watcher or register autostart.
[CmdletBinding()]
param([string]$Destination = (Join-Path $env:LOCALAPPDATA 'FocusWatch-Synthetic-P0'))
$ErrorActionPreference = 'Stop'
$target = [IO.Path]::GetFullPath($Destination)
if (Test-Path -LiteralPath $target) { throw 'Choose a new destination for this P0 installation.' }
$stage = Join-Path (Split-Path -Parent $target) ("focuswatch-p0-install-" + [guid]::NewGuid())
$null = New-Item -ItemType Directory -Path $stage
try {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'focuswatch-agent.exe') -Destination $stage
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'report') -Destination $stage -Recurse
    [IO.Directory]::Move($stage, $target)
} finally {
    if (Test-Path -LiteralPath $stage) {
        $resolvedStage = (Resolve-Path -LiteralPath $stage).Path
        if ((Split-Path -Parent $resolvedStage) -eq (Split-Path -Parent $target) -and
            (Split-Path -Leaf $resolvedStage) -match '^focuswatch-p0-install-[0-9a-f-]{36}$') {
            Remove-Item -LiteralPath $resolvedStage -Recurse -Force
        }
    }
}
Write-Output $target
