#Requires -Version 5.1
<#
.SYNOPSIS
  Instalación portable de El Tejido Arcano / ArcanaGraph Lab (Windows).

.EXAMPLE
  .\setup.ps1
  .\setup.ps1 -Python python3.13
#>
param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "==> El Tejido Arcano — setup" -ForegroundColor Cyan

if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) {
    Write-Error "No se encontró '$Python'. Instala Python 3.11+ y vuelve a intentar."
}

& $Python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Se requiere Python 3.11 o superior."
}

if (-not (Test-Path "env\Scripts\python.exe")) {
    Write-Host "==> Creando entorno virtual en .\env"
    & $Python -m venv env
}

$py = ".\env\Scripts\python.exe"
Write-Host "==> Instalando dependencias"
& $py -m pip install --upgrade pip
& $py -m pip install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "==> Creado .env desde .env.example"
}

$cards = Get-ChildItem "data\cards\major_*.json" -ErrorAction SilentlyContinue
if (-not $cards -or $cards.Count -lt 22) {
    Write-Host "==> Sembrando ADN de 22 Arcanos Mayores"
    & $py scripts\seed_major_arcana.py
    if (Test-Path "cartas") {
        & $py scripts\migrate_legacy_cartas.py
    }
    & $py scripts\validate_card_data.py
} else {
    Write-Host "==> data\cards ya tiene $($cards.Count) cartas"
}

$pngs = Get-ChildItem "cartas\*.png" -ErrorAction SilentlyContinue
if (-not $pngs) {
    Write-Warning "No hay PNGs en cartas\. Coloca las imágenes de los arcanos allí para el pipeline cromático."
}

Write-Host ""
Write-Host "Listo. Arranque:" -ForegroundColor Green
Write-Host "  .\env\Scripts\Activate.ps1"
Write-Host "  python -m streamlit run ui/app.py"
Write-Host "  python -m uvicorn api.main:app --reload --port 8000"
Write-Host "  python -m pytest tests -q"
