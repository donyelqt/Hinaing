# Hinaing Unified Deployment Engine (CTO Grade - Precision Edition)
# Usage: ./ship.ps1 -m "Your commit message"

param (
    [Parameter(Mandatory=$true)]
    [string]$m,
    [switch]$pull
)

$ErrorActionPreference = "Stop"
$ROOT_DIR = Get-Location
$BACKEND_DIR = Join-Path $ROOT_DIR "backend"

Write-Host "🚀 Starting Precision Deployment Pipeline..." -ForegroundColor Cyan

# --- OPTIONAL: Pull from origin main ---
if ($pull) {
    Write-Host "`n[PRE-FLIGHT] Pulling latest from GitHub main..." -ForegroundColor Yellow
    git pull origin main
    Write-Host "✅ Pull complete." -ForegroundColor Green
}

# --- PRE-FLIGHT: Identify Staged Files ---
$stagedFiles = git diff --cached --name-only

# If no staged files but -pull was used, get all files from main
if (-not $stagedFiles -and $pull) {
    Write-Host "[PRE-FLIGHT] No staged files, using all files from main..." -ForegroundColor Yellow
    $stagedFiles = "backend/"
}
if (-not $stagedFiles -and -not $pull) {
    Write-Host "❌ Error: No files are currently staged. Please use 'git add' first." -ForegroundColor Red
    exit 1
}

Write-Host "📦 Files staged for deployment:" -ForegroundColor Gray
$stagedFiles | ForEach-Object { Write-Host " - $_" -ForegroundColor Gray }

# --- PHASE 1: GitHub (Root Repository) ---
if (-not $pull) {
    Write-Host "`n[PHASE 1] Syncing Staged files to GitHub (origin)..." -ForegroundColor Yellow
    git commit -m "$m"
    git push origin main
    Write-Host "✅ GitHub Synchronization Complete." -ForegroundColor Green
} else {
    Write-Host "`n[PHASE 1] Skipped (using -pull flag - already from origin)" -ForegroundColor Gray
}

# --- PHASE 2: Hugging Face (Backend Folder Only) ---
Write-Host "`n[PHASE 2] Syncing Backend files to Hugging Face (hf)..." -ForegroundColor Yellow

# Check if any staged/committed files belong to the backend
if ($pull) {
    $backendFiles = "backend/"
} else {
    $backendFiles = $stagedFiles | Where-Object { $_ -like "backend/*" }
}

if ($backendFiles) {
    try {
        Write-Host "🚀 Extracting and pushing 'backend/' folder to Hugging Face..." -ForegroundColor Blue
        # CTO-GRADE: Using subtree split & forced push to handle the history transition perfectly
        $splitRev = git subtree split --prefix backend main
        git push hf "$($splitRev):main" --force
        Write-Host "✅ Hugging Face Deployment Complete." -ForegroundColor Green
    } catch {
        Write-Host "❌ Error: Hugging Face push failed. Check your internet or HF token." -ForegroundColor Red
    }
} else {
    Write-Host "💡 Skipping Phase 2: No backend files were modified." -ForegroundColor Gray
}

Write-Host "`n🏁 PIPELINE SUCCESSFUL: Precision update synchronized." -ForegroundColor Cyan
