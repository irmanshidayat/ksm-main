# =============================================================================
# KSM Main - SSH Connection Test Script (PowerShell)
# =============================================================================
# 
# Script untuk test koneksi SSH ke server dengan port 22
# 
# Usage:
#   .\scripts\ssh-test.ps1 [host] [user]
# 
# Example:
#   .\scripts\ssh-test.ps1 72.61.142.109 root
# =============================================================================

param(
    [string]$Host = "72.61.142.109",
    [string]$User = "root",
    [int]$Port = 22
)

Write-Host "🔍 Testing SSH Connection..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "Host    : $Host" -ForegroundColor White
Write-Host "User    : $User" -ForegroundColor White
Write-Host "Port    : $Port" -ForegroundColor White
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

# Test 1: Ping Test
Write-Host "📡 Test 1: Ping Connectivity..." -ForegroundColor Yellow
try {
    $pingResult = Test-Connection -ComputerName $Host -Count 2 -Quiet
    if ($pingResult) {
        Write-Host "✅ Ping successful" -ForegroundColor Green
    } else {
        Write-Host "❌ Ping failed - Server may be down or unreachable" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Ping error: $_" -ForegroundColor Red
}
Write-Host ""

# Test 2: Port Connectivity
Write-Host "🔌 Test 2: Port $Port Connectivity..." -ForegroundColor Yellow
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $connection = $tcpClient.BeginConnect($Host, $Port, $null, $null)
    $wait = $connection.AsyncWaitHandle.WaitOne(3000, $false)
    
    if ($wait) {
        try {
            $tcpClient.EndConnect($connection)
            Write-Host "✅ Port $Port is open and accessible" -ForegroundColor Green
        } catch {
            Write-Host "❌ Port $Port connection failed: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ Port $Port connection timeout (3 seconds)" -ForegroundColor Red
    }
    $tcpClient.Close()
} catch {
    Write-Host "❌ Port test error: $_" -ForegroundColor Red
}
Write-Host ""

# Test 3: SSH Connection Test
Write-Host "🔐 Test 3: SSH Connection Test..." -ForegroundColor Yellow
Write-Host "Attempting SSH connection (this may take a few seconds)..." -ForegroundColor Gray

$sshCommand = "ssh -p $Port -o ConnectTimeout=10 -o StrictHostKeyChecking=no $User@$Host 'echo SSH connection successful'"
try {
    $sshResult = Invoke-Expression $sshCommand 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ SSH connection successful!" -ForegroundColor Green
        Write-Host "   Response: $sshResult" -ForegroundColor Gray
    } else {
        Write-Host "❌ SSH connection failed" -ForegroundColor Red
        Write-Host "   Error: $sshResult" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ SSH connection error: $_" -ForegroundColor Red
}
Write-Host ""

# Test 4: SSH Key Test (if key exists)
$sshKeyPath = "$env:USERPROFILE\.ssh\github_actions_deploy"
if (Test-Path $sshKeyPath) {
    Write-Host "🔑 Test 4: SSH Key Authentication Test..." -ForegroundColor Yellow
    $sshKeyCommand = "ssh -p $Port -i `"$sshKeyPath`" -o ConnectTimeout=10 -o StrictHostKeyChecking=no $User@$Host 'echo SSH key authentication successful'"
    try {
        $keyResult = Invoke-Expression $sshKeyCommand 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ SSH key authentication successful!" -ForegroundColor Green
        } else {
            Write-Host "❌ SSH key authentication failed" -ForegroundColor Red
            Write-Host "   Error: $keyResult" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ SSH key test error: $_" -ForegroundColor Red
    }
    Write-Host ""
} else {
    Write-Host "ℹ️  Test 4: SSH key not found at $sshKeyPath" -ForegroundColor Gray
    Write-Host "   Skipping SSH key authentication test" -ForegroundColor Gray
    Write-Host ""
}

# Summary
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "📋 Summary" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "To connect manually, use:" -ForegroundColor White
Write-Host "  ssh -p $Port $User@$Host" -ForegroundColor Yellow
Write-Host ""
Write-Host "If using SSH key:" -ForegroundColor White
Write-Host "  ssh -p $Port -i ~/.ssh/github_actions_deploy $User@$Host" -ForegroundColor Yellow
Write-Host ""

