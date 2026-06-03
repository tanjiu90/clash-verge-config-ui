$ErrorActionPreference = "Stop"

$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Port = if ($env:CLASH_VERGE_CONFIG_UI_PORT) { [int]$env:CLASH_VERGE_CONFIG_UI_PORT } else { 8787 }
$Url = "http://127.0.0.1:$Port"
$RuntimeDir = Join-Path $AppDir ".runtime"
$PidFile = Join-Path $RuntimeDir "server.pid"

function Get-PythonRunner {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{ File = "python"; Prefix = @() }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{ File = "py"; Prefix = @("-3") }
    }
    throw "Python 3.10+ was not found. Install Python and enable Add python.exe to PATH."
}

if (-not $env:CLASH_UI_IDLE_TIMEOUT) {
    $env:CLASH_UI_IDLE_TIMEOUT = "1800"
}

New-Item -Path $RuntimeDir -ItemType Directory -Force | Out-Null

$python = Get-PythonRunner
$pythonFile = $python.File
$pythonPrefix = $python.Prefix
& $pythonFile @($pythonPrefix + @("-c", "import yaml")) | Out-Null
if ($LASTEXITCODE -ne 0) {
    & $pythonFile @($pythonPrefix + @("-m", "pip", "install", "-r", (Join-Path $AppDir "requirements.txt")))
}

$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $listener) {
    $process = Start-Process -FilePath $pythonFile -ArgumentList ($pythonPrefix + @("app.py")) -WorkingDirectory $AppDir -WindowStyle Hidden -PassThru
    Set-Content -Path $PidFile -Value $process.Id -Encoding ASCII
    Start-Sleep -Seconds 1
}

Start-Process $Url
