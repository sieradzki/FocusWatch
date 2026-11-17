param([string]$WorkDir)
$ErrorActionPreference = 'Stop'
if (-not $WorkDir) { $WorkDir = Join-Path ([IO.Path]::GetTempPath()) ('FocusWatch-PairedUI-' + [Guid]::NewGuid().ToString('N')) }
$WorkDir = [IO.Path]::GetFullPath($WorkDir)
New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null
$env:DOTNET_CLI_TELEMETRY_OPTOUT='1'
$env:AVALONIA_TELEMETRY_OPTOUT='1'
$env:DOTNET_GENERATE_ASPNET_CERTIFICATE='false'
$env:DOTNET_NOLOGO='1'
$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1'
$env:DOTNET_CLI_WORKLOAD_UPDATE_NOTIFY_DISABLE='1'
$env:DOTNET_CLI_HOME=Join-Path $WorkDir 'dotnet-home'
$env:NUGET_PACKAGES=Join-Path $WorkDir 'packages'
$env:NUGET_HTTP_CACHE_PATH=Join-Path $WorkDir 'nuget-http-cache'
$env:npm_config_cache=Join-Path $WorkDir 'npm-cache'
$env:ELECTRON_CACHE=Join-Path $WorkDir 'electron-cache'
foreach($part in @('avalonia','electron')) {
  $destination=Join-Path $WorkDir $part
  New-Item -ItemType Directory -Path $destination -Force | Out-Null
  Copy-Item -Path (Join-Path $PSScriptRoot ($part+'/*')) -Destination $destination -Force
}
dotnet restore (Join-Path $WorkDir 'avalonia/ReportProbe.csproj') --locked-mode --configfile (Join-Path $WorkDir 'avalonia/NuGet.Config') --verbosity minimal
if($LASTEXITCODE -ne 0) { throw 'Avalonia restore failed' }
dotnet publish (Join-Path $WorkDir 'avalonia/ReportProbe.csproj') -c Release --no-restore -o (Join-Path $WorkDir 'avalonia/publish')
if($LASTEXITCODE -ne 0) { throw 'Avalonia publish failed' }
npm ci --prefix (Join-Path $WorkDir 'electron') --ignore-scripts --no-audit --no-fund
if($LASTEXITCODE -ne 0) { throw 'npm restore failed' }
node (Join-Path $WorkDir 'electron/node_modules/electron/install.js')
if($LASTEXITCODE -ne 0) { throw 'Electron download failed' }
npm --prefix (Join-Path $WorkDir 'electron') run build
if($LASTEXITCODE -ne 0) { throw 'Renderer bundle failed' }
Write-Output "Prepared temporary work directory: $WorkDir"
