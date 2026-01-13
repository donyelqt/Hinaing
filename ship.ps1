# Hinaing Unified Deployment Engine (CTO Grade - Precision Edition)
# Usage: ./ship.ps1 -m "Your commit message"

param (
    [Parameter(Mandatory=$true)]
    [string]$m
)

$ErrorActionPreference = "Stop"
$ROOT_DIR = Get-Location
$BACKEND_DIR = Join-Path $ROOT_DIR "backend"

Write-Host "🚀 Starting Precision Deployment Pipeline..." -ForegroundColor Cyan

# --- PRE-FLIGHT: Identify Staged Files ---
$stagedFiles = git diff --cached --name-only
if (-not $stagedFiles) {
    Write-Host "❌ Error: No files are currently staged. Please use 'git add' first." -ForegroundColor Red
    exit 1
}

Write-Host "📦 Files staged for deployment:" -ForegroundColor Gray
$stagedFiles | ForEach-Object { Write-Host " - $_" -ForegroundColor Gray }

# --- PHASE 1: GitHub (Root Repository) ---
Write-Host "`n[PHASE 1] Syncing Staged files to GitHub (origin)..." -ForegroundColor Yellow
git commit -m "$m"
git push origin main
Write-Host "✅ GitHub Synchronization Complete." -ForegroundColor Green

# --- PHASE 2: Hugging Face (Backend Repository) ---
Write-Host "`n[PHASE 2] Syncing Backend files to Hugging Face (hf)..." -ForegroundColor Yellow
if (Test-Path $BACKEND_DIR) {
    # Find which staged files belong to the backend
    $backendFiles = $stagedFiles | Where-Object { $_ -like "backend/*" }
    
    if ($backendFiles) {
        Set-Location $BACKEND_DIR
        
        # Sync the staging area for the sub-repo
        foreach ($file in $backendFiles) {
            $relativePath = $file.Substring(8) # Remove 'backend/' prefix
            if (Test-Path $relativePath) {
                git add $relativePath
            }
        }
        
        try {
            git commit -m "$m"
            Write-Host "🚀 Pushing to Hugging Face Production..." -ForegroundColor Blue
            git push -f hf master:main
        } catch {
            Write-Host "💡 Note: Backend changes were already synced or nothing new for HF." -ForegroundColor Gray
        }
        
        Set-Location $ROOT_DIR
        Write-Host "✅ Hugging Face Deployment Triggered." -ForegroundColor Green
    } else {
        Write-Host "💡 Skipping Phase 2: No backend files were staged." -ForegroundColor Gray
    }
}

Write-Host "`n🏁 PIPELINE SUCCESSFUL: Precision update synchronized." -ForegroundColor Cyan
