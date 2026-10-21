# Windows launcher. Keeps all new packages inside the project folder.
param([switch]$Check)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

function Test-StreamlitPython([string]$Candidate) {
    if (-not (Test-Path -LiteralPath $Candidate)) { return $false }
    try {
        & $Candidate -c "import streamlit, tzdata" 2>$null
        return $LASTEXITCODE -eq 0
    } catch { return $false }
}

# The first path is portable; the second uses the environment prepared in Codex.
$taskCandidates = @(
    (Join-Path $PSScriptRoot '.venv\Scripts\python.exe'),
    (Join-Path $PSScriptRoot '..\..\work\.venv\Scripts\python.exe')
)
$taskPython = $null
foreach ($candidate in $taskCandidates) {
    if (Test-StreamlitPython $candidate) {
        $taskPython = (Resolve-Path -LiteralPath $candidate).Path
        break
    }
}

if (-not $taskPython) {
    $basePython = $null
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try {
            $detected = & py -3 -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0) { $basePython = $detected | Select-Object -Last 1 }
        } catch { $basePython = $null }
    }
    if (-not $basePython) {
        $candidate = Get-Command python -ErrorAction SilentlyContinue
        if ($candidate -and $candidate.Source -notlike '*WindowsApps*') {
            $basePython = $candidate.Source
        }
    }
    if (-not $basePython) {
        $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
        if (Test-Path -LiteralPath $bundledPython) { $basePython = $bundledPython }
    }
    if (-not $basePython) {
        Write-Host 'Install Python 3.12 or newer from https://www.python.org/downloads/'
        Write-Host 'Then double-click Start WaterBuddy.cmd again.'
        exit 1
    }
    & $basePython -c "import sys; assert sys.version_info >= (3, 10), 'Python 3.10 or newer is required'"
    if ($LASTEXITCODE -ne 0) { throw 'Please install a current Python version.' }

    $taskTemp = Join-Path $PSScriptRoot '.cache'
    New-Item -ItemType Directory -Force -Path $taskTemp | Out-Null
    $env:TEMP = $taskTemp
    $env:TMP = $taskTemp
    Write-Host 'Setting up WaterBuddy. The first run needs an internet connection...'
    & $basePython -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
    $taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    & $taskPython -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Package download failed. Check your connection and try again.' }
}

if ($Check) {
    Write-Host "WaterBuddy is ready. Python: $taskPython"
    exit 0
}

Write-Host ''
Write-Host 'WaterBuddy is starting at http://localhost:8501'
Write-Host 'Keep this window open while using the app. Press Ctrl+C to stop it.'
& $taskPython -m streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --server.headless false
