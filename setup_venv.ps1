<#
.SYNOPSIS
    AetherisClassifier - Configuracao do Ambiente Virtual
.DESCRIPTION
    Cria uma virtual environment (.venv), atualiza o pip e instala
    todas as dependencias listadas no requirements.txt.
#>

$ErrorActionPreference = "Stop"
$VENV_DIR = ".venv"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " AetherisClassifier - Setup do Ambiente" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verifica se o Python existe
try {
    $pyVer = python --version 2>&1
    Write-Host "[INFO] $pyVer detectado." -ForegroundColor Green
} catch {
    Write-Host "[ERRO] Python nao encontrado! Instale o Python 3.10+ e tente novamente." -ForegroundColor Red
    exit 1
}

# Passo 1 - Criar a venv
if (Test-Path "$VENV_DIR\Scripts\python.exe") {
    Write-Host "[OK] Virtual environment ja existe em .venv" -ForegroundColor Green
} else {
    Write-Host "[1/3] Criando virtual environment..." -ForegroundColor Yellow
    python -m venv $VENV_DIR
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERRO] Falha ao criar venv." -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Virtual environment criada em .venv" -ForegroundColor Green
}

# Passo 2 - Atualizar pip
Write-Host "[2/3] Atualizando pip..." -ForegroundColor Yellow
& "$VENV_DIR\Scripts\python.exe" -m pip install --upgrade pip --quiet
Write-Host "[OK] Pip atualizado." -ForegroundColor Green

# Passo 3 - Instalar dependencias
Write-Host "[3/3] Instalando dependencias do requirements.txt..." -ForegroundColor Yellow
Write-Host ""
& "$VENV_DIR\Scripts\python.exe" -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[AVISO] Algumas dependencias podem ter falhado. Verifique acima." -ForegroundColor Yellow
} else {
    Write-Host "[OK] Todas as dependencias instaladas com sucesso." -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Instalacao concluida!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " Para ativar o ambiente, execute:" -ForegroundColor White
Write-Host "     .venv\Scripts\Activate" -ForegroundColor Yellow
Write-Host ""
Write-Host " Para iniciar o AetherisClassifier:" -ForegroundColor White
Write-Host "     python launcher.py" -ForegroundColor Yellow
Write-Host ""