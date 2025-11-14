#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk menghapus/menonaktifkan menu Knowledge AI dari database
"""

import os
import sys
import io

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from config.database import db
from domains.role.models.menu_models import Menu, MenuPermission


def remove_knowledge_ai_menu():
    """Menonaktifkan menu Knowledge AI dari database"""
    try:
        # Use existing app
        
        with app.app_context():
            # Cari menu dengan path /knowledge-ai atau /ksm-ai atau nama mengandung "Knowledge AI"
            menu_paths = ['/knowledge-ai', '/ksm-ai']
            menus_to_deactivate = []
            
            # Cari berdasarkan path
            for path in menu_paths:
                menu = Menu.query.filter_by(path=path).first()
                if menu:
                    menus_to_deactivate.append(menu)
                    print(f"Menu ditemukan berdasarkan path: {menu.name} ({menu.path})")
            
            # Cari berdasarkan nama yang mengandung "Knowledge AI"
            knowledge_ai_menus = Menu.query.filter(
                (Menu.name.ilike('%Knowledge AI%')) | 
                (Menu.name.ilike('%KSM AI%'))
            ).all()
            
            for menu in knowledge_ai_menus:
                if menu not in menus_to_deactivate:
                    menus_to_deactivate.append(menu)
                    print(f"Menu ditemukan berdasarkan nama: {menu.name} ({menu.path})")
            
            if not menus_to_deactivate:
                print("Tidak ada menu Knowledge AI yang ditemukan di database")
                return True
            
            # Nonaktifkan menu
            for menu in menus_to_deactivate:
                menu.is_active = False
                print(f"Menu {menu.name} ({menu.path}) dinonaktifkan")
                
                # Nonaktifkan semua permission terkait
                permissions = MenuPermission.query.filter_by(menu_id=menu.id).all()
                for perm in permissions:
                    perm.is_active = False
                    print(f"  - Permission ID {perm.id} untuk menu {menu.name} dinonaktifkan")
            
            db.session.commit()
            print(f"\nBerhasil menonaktifkan {len(menus_to_deactivate)} menu Knowledge AI")
            return True
            
    except Exception as e:
        if 'db' in locals() and hasattr(db, 'session'):
            db.session.rollback()
        print(f"Error removing Knowledge AI menu: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import io
    import sys
    # Set UTF-8 encoding for Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    success = remove_knowledge_ai_menu()
    if success:
        print("[SUCCESS] Menu Knowledge AI berhasil dinonaktifkan")
    else:
        print("[ERROR] Gagal menonaktifkan menu Knowledge AI")
        sys.exit(1)

