# =============================================================================
# KSM Main - SSL/HTTPS Setup dengan Let's Encrypt (PowerShell)
# =============================================================================
# Script untuk setup SSL certificate menggunakan Let's Encrypt (Certbot)
# Usage: .\setup-ssl.ps1 -Environment [dev|prod] -Email "your-email@example.com"
# =============================================================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$Email = ""
)

# Colors
$ErrorColor = "Red"
$SuccessColor = "Green"
$WarningColor = "Yellow"
$InfoColor = "Cyan"

# Configuration
if ($Environment -eq "dev") {
    $Domain = "devreport.ptkiansantang.com"
    $DeployPath = "/opt/ksm-main-dev"
    $NginxConf = "nginx.dev.conf"
} else {
    $Domain = "report.ptkiansantang.com"
    $DeployPath = "/opt/ksm-main-prod"
    $NginxConf = "nginx.prod.conf"
}

if ([string]::IsNullOrEmpty($Email)) {
    Write-Host "⚠️  Warning: Email tidak diberikan" -ForegroundColor $WarningColor
    $Email = Read-Host "Masukkan email untuk Let's Encrypt"
    if ([string]::IsNullOrEmpty($Email)) {
        Write-Host "❌ ERROR: Email diperlukan!" -ForegroundColor $ErrorColor
        exit 1
    }
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $InfoColor
Write-Host "KSM Main - SSL/HTTPS Setup ($($Environment.ToUpper()))" -ForegroundColor $InfoColor
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $InfoColor
Write-Host ""
Write-Host "Domain: $Domain" -ForegroundColor $InfoColor
Write-Host "Email: $Email" -ForegroundColor $InfoColor
Write-Host "Deploy Path: $DeployPath" -ForegroundColor $InfoColor
Write-Host ""

# Check SSH connection
Write-Host "📡 Step 0: Testing SSH connection..." -ForegroundColor $InfoColor
$sshTest = ssh -o ConnectTimeout=5 -o BatchMode=yes root@72.61.142.109 "echo 'SSH OK'" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERROR: SSH connection failed!" -ForegroundColor $ErrorColor
    Write-Host "Pastikan SSH key sudah di-setup dengan benar" -ForegroundColor $WarningColor
    exit 1
}
Write-Host "✅ SSH connection successful" -ForegroundColor $SuccessColor
Write-Host ""

# Upload and run setup script on server
Write-Host "📤 Step 1: Uploading SSL setup script to server..." -ForegroundColor $InfoColor
$scriptContent = Get-Content "scripts\setup-ssl.sh" -Raw
$scriptContent | ssh root@72.61.142.109 "cat > /tmp/setup-ssl.sh && chmod +x /tmp/setup-ssl.sh"
Write-Host "✅ Script uploaded" -ForegroundColor $SuccessColor
Write-Host ""

# Run setup script on server
Write-Host "🚀 Step 2: Running SSL setup on server..." -ForegroundColor $InfoColor
Write-Host "This may take a few minutes..." -ForegroundColor $WarningColor
Write-Host ""

ssh root@72.61.142.109 "bash /tmp/setup-ssl.sh $Environment $Email"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $InfoColor
    Write-Host "✅ SSL Setup selesai!" -ForegroundColor $SuccessColor
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor $InfoColor
    Write-Host ""
    Write-Host "📋 Informasi:"
    Write-Host "   - Domain: $Domain"
    Write-Host "   - Environment: $Environment"
    Write-Host "   - Test SSL: curl -I https://$Domain"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ SSL Setup gagal!" -ForegroundColor $ErrorColor
    Write-Host "Cek log di server untuk detail error" -ForegroundColor $WarningColor
    exit 1
}

