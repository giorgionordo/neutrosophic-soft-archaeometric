param(
    [string]$PaperDir = "",
    [switch]$ExportWorkbook,
    [switch]$CompileLatex
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $PaperDir) {
    $PaperDir = (Resolve-Path (Join-Path $RepoRoot "..\..")).Path
}

$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

$LatexFile = Join-Path $PaperDir "neutrosophic_soft_archeometric.tex"
$Workbook = Join-Path $PaperDir "datasets\Riace_Bronzes_Evidence_Dataset_v9_H21_synthesis.xlsx"
$PaperFigures = Join-Path $PaperDir "figures"

Push-Location $RepoRoot
try {
    if ($ExportWorkbook) {
        & $PythonExe "scripts\export_from_workbook.py" --workbook $Workbook
    }

    & $PythonExe "scripts\verify_results.py" --latex $LatexFile
    & $PythonExe -m unittest discover -s tests
    & $PythonExe "scripts\generate_figures.py"

    New-Item -ItemType Directory -Force -Path $PaperFigures | Out-Null
    Copy-Item -Force "figures\ivn_h21_h33_profile.pdf" $PaperFigures
    Copy-Item -Force "figures\h21_h33_weight_sensitivity.pdf" $PaperFigures
}
finally {
    Pop-Location
}

if ($CompileLatex) {
    Push-Location $PaperDir
    try {
        & pdflatex -interaction=nonstopmode "neutrosophic_soft_archeometric.tex"
        & bibtex "neutrosophic_soft_archeometric"
        & pdflatex -interaction=nonstopmode "neutrosophic_soft_archeometric.tex"
        & pdflatex -interaction=nonstopmode "neutrosophic_soft_archeometric.tex"
    }
    finally {
        Pop-Location
    }
}

Write-Host "Reproduction completed."

