#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Script: Remind Exp Docs Environment Configuration
Copy env.example to .env and restart backend
"""

import os
import shutil
import sys
from datetime import datetime

def setup_environment():
    """Setup environment untuk Remind Exp Docs"""
    
    print("🔧 SETTING UP REMIND EXP DOCS ENVIRONMENT")
    print("="*60)
    
    # Get current directory
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_example_path = os.path.join(current_dir, 'env.example')
    env_path = os.path.join(current_dir, '.env')
    
    print(f"📁 Current directory: {current_dir}")
    print(f"📄 env.example path: {env_example_path}")
    print(f"📄 .env path: {env_path}")
    
    # Check if env.example exists
    if not os.path.exists(env_example_path):
        print(f"❌ env.example not found at: {env_example_path}")
        return False
    
    # Backup existing .env if exists
    if os.path.exists(env_path):
        backup_path = f"{env_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"📦 Backing up existing .env to: {backup_path}")
        shutil.copy2(env_path, backup_path)
    
    # Copy env.example to .env
    try:
        shutil.copy2(env_example_path, env_path)
        print(f"✅ Successfully copied env.example to .env")
    except Exception as e:
        print(f"❌ Failed to copy env.example to .env: {str(e)}")
        return False
    
    # Verify .env file
    if os.path.exists(env_path):
        print(f"✅ .env file created successfully")
        
        # Read and display key configurations
        with open(env_path, 'r') as f:
            content = f.read()
            
        print("\n📋 KEY CONFIGURATIONS:")
        print("-" * 40)
        
        # Extract key configurations
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('REMIND_EXP_') or line.strip().startswith('TELEGRAM_'):
                if not line.strip().startswith('#'):
                    print(f"  {line.strip()}")
        
        print("\n🎯 NEXT STEPS:")
        print("1. ✅ Environment file (.env) created")
        print("2. 🔄 Restart backend server: python app.py")
        print("3. 📱 Test notification: python scripts/send_telegram_report.py --type stats")
        print("4. ⏰ Wait for scheduled time to see automatic notifications")
        
        return True
    else:
        print(f"❌ .env file not created")
        return False

def main():
    """Main function"""
    print("🚀 REMIND EXP DOCS ENVIRONMENT SETUP")
    print("="*60)
    
    success = setup_environment()
    
    if success:
        print("\n" + "="*60)
        print("✅ ENVIRONMENT SETUP COMPLETED!")
        print("="*60)
        print("📱 Your Remind Exp Docs Telegram integration is ready!")
        print("🔄 Please restart your backend server to apply changes.")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ ENVIRONMENT SETUP FAILED!")
        print("="*60)
        print("Please check the error messages above and try again.")
        print("="*60)
        sys.exit(1)

if __name__ == '__main__':
    main()
