$ErrorActionPreference = "SilentlyContinue"

$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RuntimeDir = Join-Path $AppDir ".runtime"
$PidFile = Join-Path $RuntimeDir "server.pid"

if (Test-Path $PidFile) {
    Get-Content $PidFile | ForEach-Object {
        $id = [int]$_
        $process = Get-Process -Id $id
        if ($process) {
            Stop-Process -Id $id -Force
        }
    }
    Remove-Item -LiteralPath $PidFile -Force
}
