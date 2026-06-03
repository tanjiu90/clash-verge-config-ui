$ErrorActionPreference = "Stop"

$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Get-PythonRunner {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{ File = "python"; Prefix = @() }
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{ File = "py"; Prefix = @("-3") }
    }
    throw "Python 3.10+ was not found. Install Python and enable Add python.exe to PATH."
}

$python = Get-PythonRunner
$pythonFile = $python.File
$pythonPrefix = $python.Prefix
& $pythonFile @($pythonPrefix + @("-m", "pip", "install", "-r", (Join-Path $AppDir "requirements.txt")))

$shortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "Clash Verge Config UI.lnk"
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $AppDir "start-ui.bat"
$shortcut.WorkingDirectory = $AppDir
$shortcut.Description = "Start Clash Verge Config UI"
$shortcut.Save()

Write-Host "Install complete. Desktop shortcut: $shortcutPath"
