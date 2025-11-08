#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk Generate EMAIL_DOMAIN_ENCRYPTION_KEY
Script ini akan generate encryption key untuk email domain password encryption
"""

import os
import sys
from cryptography.fernet import Fernet

def generate_encryption_key():
    """Generate encryption key untuk EMAIL_DOMAIN_ENCRYPTION_KEY"""
    
    print("="*70)
    print("🔐 GENERATE EMAIL_DOMAIN_ENCRYPTION_KEY")
    print("="*70)
    print()
    
    # Generate key
    key = Fernet.generate_key()
    key_string = key.decode()
    
    print("✅ Encryption key berhasil di-generate!")
    print()
    print("📋 KEY YANG DI-GENERATE:")
    print("-"*70)
    print(key_string)
    print("-"*70)
    print()
    
    # Cek apakah .env ada
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(current_dir, '.env')
    env_example_path = os.path.join(current_dir, 'env.example')
    
    print("📝 INSTRUKSI:")
    print("-"*70)
    
    if os.path.exists(env_path):
        print(f"✅ File .env ditemukan di: {env_path}")
        print()
        print("Tambahkan atau update baris berikut di file .env:")
        print()
        print(f"EMAIL_DOMAIN_ENCRYPTION_KEY={key_string}")
        print()
        
        # Tanya apakah ingin update otomatis
        try:
            response = input("Apakah Anda ingin update .env secara otomatis? (y/n): ").strip().lower()
            if response == 'y':
                update_env_file(env_path, key_string)
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Dibatalkan oleh user")
            print()
            print("⚠️  Silakan tambahkan key secara manual ke .env:")
            print(f"EMAIL_DOMAIN_ENCRYPTION_KEY={key_string}")
    else:
        print(f"⚠️  File .env tidak ditemukan di: {env_path}")
        print()
        print("Cara menggunakan key ini:")
        print("1. Buat file .env (copy dari env.example jika ada)")
        print("2. Tambahkan baris berikut:")
        print()
        print(f"EMAIL_DOMAIN_ENCRYPTION_KEY={key_string}")
        print()
        
        if os.path.exists(env_example_path):
            print(f"💡 Tip: Anda bisa copy dari {env_example_path}")
    
    print()
    print("="*70)
    print("⚠️  PENTING:")
    print("="*70)
    print("1. Simpan key ini dengan AMAN - jangan share ke publik")
    print("2. Key ini HARUS sama dengan yang digunakan saat menyimpan password domain")
    print("3. Jika key berbeda, password yang sudah dienkripsi TIDAK BISA didekripsi")
    print("4. Jika lupa key, generate key baru dan UPDATE ulang password domain")
    print("="*70)
    
    return key_string

def update_env_file(env_path, key_string):
    """Update .env file dengan key baru"""
    try:
        # Baca file .env
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Cek apakah EMAIL_DOMAIN_ENCRYPTION_KEY sudah ada
        key_found = False
        updated_lines = []
        
        for line in lines:
            if line.strip().startswith('EMAIL_DOMAIN_ENCRYPTION_KEY='):
                # Update existing key
                updated_lines.append(f'EMAIL_DOMAIN_ENCRYPTION_KEY={key_string}\n')
                key_found = True
            else:
                updated_lines.append(line)
        
        # Jika key tidak ditemukan, tambahkan di akhir
        if not key_found:
            # Cari section EMAIL DOMAIN ENCRYPTION
            insert_index = len(updated_lines)
            for i, line in enumerate(updated_lines):
                if 'EMAIL DOMAIN ENCRYPTION' in line.upper() or 'EMAIL_DOMAIN_ENCRYPTION_KEY' in line.upper():
                    # Cari baris kosong setelah section atau key berikutnya
                    for j in range(i, len(updated_lines)):
                        if updated_lines[j].strip() == '' or (j < len(updated_lines) - 1 and updated_lines[j+1].strip().startswith('#')):
                            insert_index = j + 1
                            break
                    break
            
            # Insert key
            updated_lines.insert(insert_index, f'EMAIL_DOMAIN_ENCRYPTION_KEY={key_string}\n')
        
        # Tulis kembali file .env
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        print()
        print("✅ File .env berhasil di-update!")
        print(f"   Key telah ditambahkan/updated di: {env_path}")
        print()
        print("⚠️  Jangan lupa restart aplikasi agar perubahan berlaku!")
        
    except Exception as e:
        print()
        print(f"❌ Error saat update .env: {str(e)}")
        print()
        print("⚠️  Silakan update .env secara manual:")
        print(f"EMAIL_DOMAIN_ENCRYPTION_KEY={key_string}")

if __name__ == "__main__":
    try:
        generate_encryption_key()
    except KeyboardInterrupt:
        print("\n\n❌ Dibatalkan oleh user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)

