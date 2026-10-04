param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $BotArgs
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"

if (Test-Path -LiteralPath $VenvPython) {
    $PythonCommand = @($VenvPython)
} elseif (Get-Command "python" -ErrorAction SilentlyContinue) {
    $PythonCommand = @("python")
} elseif (Get-Command "py" -ErrorAction SilentlyContinue) {
    $PythonCommand = @("py", "-3")
} else {
    throw "Python was not found. Create venv\Scripts\python.exe or install Python on PATH."
}

Set-Location -LiteralPath $ProjectRoot
if ($PythonCommand.Length -gt 1) {
    & $PythonCommand[0] @($PythonCommand[1..($PythonCommand.Length - 1)]) "index.py" @BotArgs
} else {
    & $PythonCommand[0] "index.py" @BotArgs
}
