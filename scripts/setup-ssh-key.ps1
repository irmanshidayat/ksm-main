# =============================================================================
# KSM Main - Setup SSH Key Script (PowerShell)
# =============================================================================
# 
# Script untuk copy public key ke server setelah koneksi SSH berhasil
# 
# Usage:
#   .\scripts\setup-ssh-key.ps1
#   .\scripts\setup-ssh-key.ps1 -KeyPath ~/.ssh/id_ed25519.pub
# =============================================================================

param(
    [string]$KeyPath = "$env:USERPROFILE\.ssh\id_ed25519.pub",
    [string]$Server = "ksm-server",
    [string]$User = "root"
)

Write-Host "🔑 Setup SSH Key untuk KSM Server" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

# Check if public key exists
if (-not (Test-Path $KeyPath)) {
    Write-Host "❌ Public key not found at: $KeyPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "Generate SSH key first:" -ForegroundColor Yellow
    Write-Host "  ssh-keygen -t ed25519 -C `"your-email@example.com`"" -ForegroundColor Gray
    exit 1
}

# Display public key
Write-Host "📋 Public Key:" -ForegroundColor Yellow
$publicKey = Get-Content $KeyPath
Write-Host $publicKey -ForegroundColor Gray
Write-Host ""

# Test connection first
Write-Host "🔍 Testing SSH connection..." -ForegroundColor Yellow
try {
    $testResult = ssh -o ConnectTimeout=5 -o BatchMode=yes $Server "echo 'Connection OK'" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ SSH connection successful!" -ForegroundColor Green
    } else {
        Write-Host "❌ SSH connection failed. Please ensure:" -ForegroundColor Red
        Write-Host "   1. Server is accessible" -ForegroundColor Gray
        Write-Host "   2. Port 22 is open" -ForegroundColor Gray
        Write-Host "   3. SSH service is running on server" -ForegroundColor Gray
        Write-Host ""
        Write-Host "   Error: $testResult" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Connection test error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Copy public key to server
Write-Host "📤 Copying public key to server..." -ForegroundColor Yellow
try {
    $publicKeyContent = Get-Content $KeyPath -Raw
    $command = "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '$($publicKeyContent.Trim())' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo 'Public key added successfully'"
    
    $result = ssh $Server $command 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Public key copied successfully!" -ForegroundColor Green
        Write-Host ""
        
        # Test key-based authentication
        Write-Host "🔐 Testing key-based authentication..." -ForegroundColor Yellow
        $authTest = ssh -o PasswordAuthentication=no $Server "echo 'Key authentication successful'" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Key-based authentication working!" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Key authentication test failed, but key was copied." -ForegroundColor Yellow
            Write-Host "   You may need to check server SSH configuration." -ForegroundColor Gray
        }
    } else {
        Write-Host "❌ Failed to copy public key" -ForegroundColor Red
        Write-Host "   Error: $result" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error copying key: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now connect using:" -ForegroundColor White
Write-Host "  ssh ksm-server" -ForegroundColor Yellow
Write-Host ""
Write-Host "Or with explicit command:" -ForegroundColor White
Write-Host "  ssh -p 22 root@72.61.142.109" -ForegroundColor Yellow
Write-Host ""

