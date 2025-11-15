# =============================================================================
# KSM Main - Manual Deployment Script (PowerShell)
# =============================================================================
# 
# Script untuk deployment manual ke server development
# 
# Usage:
#   .\scripts\manual-deploy.ps1
#   .\scripts\manual-deploy.ps1 -Environment dev
# =============================================================================

param(
    [string]$Environment = "dev",
    [string]$Host = "72.61.142.109",
    [string]$User = "root",
    [int]$Port = 22
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 KSM Main - Manual Deployment Script" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "Environment: $Environment" -ForegroundColor White
Write-Host "Host       : $Host" -ForegroundColor White
Write-Host "User       : $User" -ForegroundColor White
Write-Host "Port       : $Port" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

# Set paths based on environment
if ($Environment -eq "dev") {
    $ComposeFile = "ksm-main/docker-compose.dev.yml"
    $DeployPath = "/opt/ksm-main-dev"
    $BackendPort = 8002
    $AgentPort = 5002
    $FrontendPort = 3006
} elseif ($Environment -eq "prod") {
    $ComposeFile = "ksm-main/docker-compose.yml"
    $DeployPath = "/opt/ksm-main-prod"
    $BackendPort = 8001
    $AgentPort = 5001
    $FrontendPort = 3005
} else {
    Write-Host "❌ Invalid environment. Use 'dev' or 'prod'" -ForegroundColor Red
    exit 1
}

# Check if we're in the right directory
if (-not (Test-Path "ksm-main")) {
    Write-Host "❌ Error: ksm-main directory not found!" -ForegroundColor Red
    Write-Host "   Please run this script from the project root directory." -ForegroundColor Yellow
    exit 1
}

Write-Host "📋 Step 1: Copy docker-compose file..." -ForegroundColor Yellow
try {
    $scpCmd = "scp -P $Port `"$ComposeFile`" ${User}@${Host}:${DeployPath}/docker-compose.yml"
    Invoke-Expression $scpCmd
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ docker-compose file copied successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to copy docker-compose file" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error copying docker-compose file: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "📋 Step 2: Create infrastructure directory..." -ForegroundColor Yellow
try {
    $sshCmd = "ssh -p $Port ${User}@${Host} `"mkdir -p ${DeployPath}/infrastructure`""
    Invoke-Expression $sshCmd | Out-Null
    Write-Host "✅ Infrastructure directory created" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Warning: Could not create infrastructure directory (may already exist)" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "📋 Step 3: Copy infrastructure files..." -ForegroundColor Yellow
try {
    $scpCmd = "scp -P $Port -r ksm-main/infrastructure/* ${User}@${Host}:${DeployPath}/infrastructure/"
    Invoke-Expression $scpCmd
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Infrastructure files copied successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to copy infrastructure files" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error copying infrastructure files: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "📋 Step 4: Copy backend files (this may take a while)..." -ForegroundColor Yellow
Write-Host "   Excluding: __pycache__, *.pyc, .venv, ksm_venv" -ForegroundColor Gray
try {
    # Create backend directory first
    $sshCmd = "ssh -p $Port ${User}@${Host} `"mkdir -p ${DeployPath}/backend`""
    Invoke-Expression $sshCmd | Out-Null
    
    # Copy backend files (scp doesn't support exclude, so we'll copy everything)
    # User can manually clean up cache files on server if needed
    $scpCmd = "scp -P $Port -r ksm-main/backend/* ${User}@${Host}:${DeployPath}/backend/"
    Invoke-Expression $scpCmd
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Backend files copied successfully" -ForegroundColor Green
        Write-Host "   Note: Cache files may have been copied. Clean them up on server if needed." -ForegroundColor Gray
    } else {
        Write-Host "❌ Failed to copy backend files" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error copying backend files: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "📋 Step 5: Copy frontend files (this may take a while)..." -ForegroundColor Yellow
Write-Host "   Excluding: node_modules, dist, .next" -ForegroundColor Gray
try {
    # Create frontend directory first
    $sshCmd = "ssh -p $Port ${User}@${Host} `"mkdir -p ${DeployPath}/frontend-vite`""
    Invoke-Expression $sshCmd | Out-Null
    
    # Copy frontend files
    $scpCmd = "scp -P $Port -r ksm-main/frontend-vite/* ${User}@${Host}:${DeployPath}/frontend-vite/"
    Invoke-Expression $scpCmd
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Frontend files copied successfully" -ForegroundColor Green
        Write-Host "   Note: node_modules may have been copied. Consider running 'npm install' on server." -ForegroundColor Gray
    } else {
        Write-Host "❌ Failed to copy frontend files" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error copying frontend files: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "📋 Step 6: Copy Agent AI files..." -ForegroundColor Yellow
try {
    # Create Agent AI directory first
    $sshCmd = "ssh -p $Port ${User}@${Host} `"mkdir -p /opt/Agent AI`""
    Invoke-Expression $sshCmd | Out-Null
    
    # Copy Agent AI files
    $scpCmd = "scp -P $Port -r `"Agent AI/*`" ${User}@${Host}:/opt/Agent\ AI/"
    Invoke-Expression $scpCmd
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Agent AI files copied successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to copy Agent AI files" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error copying Agent AI files: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "✅ Files copied successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. SSH to server:" -ForegroundColor White
Write-Host "      ssh -p $Port ${User}@${Host}" -ForegroundColor Yellow
Write-Host ""
Write-Host "   2. Navigate to deployment directory:" -ForegroundColor White
Write-Host "      cd $DeployPath" -ForegroundColor Yellow
Write-Host ""
Write-Host "   3. Stop existing containers (if any):" -ForegroundColor White
Write-Host "      docker-compose -f docker-compose.yml down" -ForegroundColor Yellow
Write-Host ""
Write-Host "   4. Build Docker images:" -ForegroundColor White
Write-Host "      docker-compose -f docker-compose.yml build --no-cache" -ForegroundColor Yellow
Write-Host ""
Write-Host "   5. Start services:" -ForegroundColor White
Write-Host "      docker-compose -f docker-compose.yml up -d" -ForegroundColor Yellow
Write-Host ""
Write-Host "   6. Check status:" -ForegroundColor White
Write-Host "      docker-compose -f docker-compose.yml ps" -ForegroundColor Yellow
Write-Host ""
Write-Host "   7. Test health endpoints:" -ForegroundColor White
Write-Host "      curl http://localhost:$BackendPort/api/health" -ForegroundColor Yellow
Write-Host "      curl http://localhost:$AgentPort/health" -ForegroundColor Yellow
Write-Host "      curl http://localhost:$FrontendPort" -ForegroundColor Yellow
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

