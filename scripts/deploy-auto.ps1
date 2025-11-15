# =============================================================================
# KSM Main - Automated Deployment Script (PowerShell)
# =============================================================================
# Script untuk menjalankan deployment otomatis dari Windows
# Usage: .\deploy-auto.ps1 [dev|prod] [setup|update]
# =============================================================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("setup", "update")]
    [string]$Action = "update",
    
    [Parameter(Mandatory=$false)]
    [string]$SSHHost = "72.61.142.109",
    
    [Parameter(Mandatory=$false)]
    [string]$SSHUser = "root",
    
    [Parameter(Mandatory=$false)]
    [int]$SSHPort = 22
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Cyan "============================================================================="
Write-ColorOutput Cyan "KSM Main - Automated Deployment ($Environment - $Action)"
Write-ColorOutput Cyan "============================================================================="
Write-Output ""

# Configuration
if ($Environment -eq "dev") {
    $DeployPath = "/opt/ksm-main-dev"
    $Branch = "dev"
} else {
    $DeployPath = "/opt/ksm-main-prod"
    $Branch = "main"
}

Write-Output "Configuration:"
Write-Output "  Environment: $Environment"
Write-Output "  Action: $Action"
Write-Output "  SSH Host: ${SSHUser}@${SSHHost}:${SSHPort}"
Write-Output "  Deploy Path: $DeployPath"
Write-Output ""

# Check SSH connection (optional, will prompt for password if needed)
Write-ColorOutput Yellow "Note: SSH connection will prompt for password if SSH key is not configured"
Write-Output ""

# Execute based on action
if ($Action -eq "setup") {
    Write-ColorOutput Blue "Running setup script on server..."
    
    # Check if script exists on server, if not, clone repository first
    $scriptCheck = ssh -p $SSHPort "${SSHUser}@${SSHHost}" "if [ -f $DeployPath/scripts/deploy-setup.sh ]; then echo 'exists'; else echo 'not-exists'; fi"
    
    if ($scriptCheck -eq "not-exists") {
        Write-ColorOutput Yellow "Script not found on server. Cloning repository..."
        
        # Clone repository
        $cloneCommand = @"
cd /opt
rm -rf $DeployPath
git clone https://github.com/irmanshidayat/ksm-main.git $DeployPath
cd $DeployPath
git checkout $Branch
chmod +x scripts/deploy-setup.sh
chmod +x scripts/deploy-update.sh
"@
        ssh -p $SSHPort "${SSHUser}@${SSHHost}" $cloneCommand
        
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput Red "ERROR: Failed to clone repository!"
            exit 1
        }
        
        Write-ColorOutput Green "Repository cloned successfully"
    }
    
    # Run setup script
    Write-ColorOutput Blue "Executing setup script..."
    ssh -p $SSHPort "${SSHUser}@${SSHHost}" "cd $DeployPath; ./scripts/deploy-setup.sh $Environment"
    
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput Red "ERROR: Setup script failed!"
        exit 1
    }
    
} else {
    Write-ColorOutput Blue "Running update script on server..."
    
    # Check if deploy path exists
    $pathCheck = ssh -p $SSHPort "${SSHUser}@${SSHHost}" "if [ -d $DeployPath ]; then echo 'exists'; else echo 'not-exists'; fi"
    
    if ($pathCheck -eq "not-exists") {
        Write-ColorOutput Red "ERROR: Deploy path $DeployPath does not exist!"
        Write-Output "Please run setup first: .\deploy-auto.ps1 -Environment $Environment -Action setup"
        exit 1
    }
    
    # Pull latest changes
    Write-ColorOutput Blue "Pulling latest changes..."
    ssh -p $SSHPort "${SSHUser}@${SSHHost}" "cd $DeployPath; git pull origin $Branch"
    
    # Make sure scripts are executable
    ssh -p $SSHPort "${SSHUser}@${SSHHost}" "cd $DeployPath; chmod +x scripts/deploy-update.sh 2>/dev/null; true"
    
    # Run update script
    Write-ColorOutput Blue "Executing update script..."
    ssh -p $SSHPort "${SSHUser}@${SSHHost}" "cd $DeployPath; ./scripts/deploy-update.sh $Environment"
    
    if ($LASTEXITCODE -ne 0) {
        Write-ColorOutput Red "ERROR: Update script failed!"
        exit 1
    }
}

Write-Output ""
Write-ColorOutput Green "============================================================================="
Write-ColorOutput Green "Deployment completed successfully!"
Write-ColorOutput Green "============================================================================="
Write-Output ""

