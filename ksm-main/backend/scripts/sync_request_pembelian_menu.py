#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk sinkronisasi menu Request Pembelian dengan database ksm_main
Memastikan menu dan submenu Request Pembelian ada di database dengan permission yang sesuai
"""

import os
import sys
import io
from datetime import datetime

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from config.database import db
from models.menu_models import Menu, MenuPermission
from models import Role


# Definisi menu Request Pembelian dan submenu-nya
REQUEST_PEMBELIAN_MENUS = {
    'parent': {
        'name': 'Request Pembelian',
        'path': '/request-pembelian',
        'icon': '🛒',
        'order_index': 9,
        'description': 'Manajemen Request Pembelian',
        'is_system_menu': True
    },
    'submenus': [
        {
            'name': 'Dashboard Request',
            'path': '/request-pembelian/dashboard',
            'icon': '📊',
            'order_index': 1,
            'description': 'Dashboard Request Pembelian',
            'is_system_menu': True
        },
        {
            'name': 'Daftar Request',
            'path': '/request-pembelian/daftar-request',
            'icon': '📋',
            'order_index': 2,
            'description': 'Daftar Request Pembelian',
            'is_system_menu': True
        },
        {
            'name': 'Vendor Penawaran Approval',
            'path': '/request-pembelian/vendor-penawaran',
            'icon': '📋',
            'order_index': 3,
            'description': 'Approval Penawaran Vendor',
            'is_system_menu': True
        },
        {
            'name': 'Upload Penawaran Vendor',
            'path': '/request-pembelian/upload-penawaran',
            'icon': '📄',
            'order_index': 4,
            'description': 'Upload Penawaran Vendor',
            'is_system_menu': True
        },
        {
            'name': 'Daftar Barang Vendor',
            'path': '/request-pembelian/daftar-barang-vendor',
            'icon': '📦',
            'order_index': 5,
            'description': 'Daftar Barang Vendor',
            'is_system_menu': True
        },
        {
            'name': 'Analisis Vendor',
            'path': '/request-pembelian/analisis-vendor',
            'icon': '🔍',
            'order_index': 6,
            'description': 'Analisis Vendor',
            'is_system_menu': True
        },
        {
            'name': 'Laporan Pembelian',
            'path': '/request-pembelian/laporan-pembelian',
            'icon': '📊',
            'order_index': 7,
            'description': 'Laporan Pembelian',
            'is_system_menu': True
        }
    ]
}


def check_database_status():
    """Cek status database dan menu yang ada"""
    print("\n" + "="*60)
    print("📊 CEK STATUS DATABASE")
    print("="*60)
    
    with app.app_context():
        # Cek apakah tabel menus ada
        try:
            menu_count = Menu.query.count()
            print(f"✅ Tabel menus ditemukan: {menu_count} menu tersedia")
        except Exception as e:
            print(f"❌ Error mengakses tabel menus: {str(e)}")
            return False
    
        # Cek menu Request Pembelian parent
        parent_menu = Menu.query.filter_by(path='/request-pembelian').first()
        if parent_menu:
            print(f"✅ Menu parent 'Request Pembelian' ditemukan (ID: {parent_menu.id})")
            print(f"   - Status: {'Aktif' if parent_menu.is_active else 'Tidak Aktif'}")
        else:
            print("⚠️  Menu parent 'Request Pembelian' belum ada di database")
        
        # Cek submenu
        if parent_menu:
            submenu_count = Menu.query.filter_by(parent_id=parent_menu.id).count()
            print(f"📋 Submenu yang ada: {submenu_count} dari {len(REQUEST_PEMBELIAN_MENUS['submenus'])} yang diharapkan")
            
            for submenu_def in REQUEST_PEMBELIAN_MENUS['submenus']:
                submenu = Menu.query.filter_by(path=submenu_def['path']).first()
                if submenu:
                    status = '✅' if submenu.is_active else '⚠️'
                    print(f"   {status} {submenu_def['name']} ({submenu_def['path']})")
                else:
                    print(f"   ❌ {submenu_def['name']} ({submenu_def['path']}) - BELUM ADA")
        
        # Cek role yang ada
        try:
            roles = Role.query.filter_by(is_active=True).all()
            print(f"\n👥 Role yang aktif: {len(roles)} role")
            for role in roles:
                print(f"   - {role.name} (ID: {role.id}, Level: {role.level})")
        except Exception as e:
            print(f"❌ Error mengakses tabel roles: {str(e)}")
            return False
        
        return True


def sync_request_pembelian_menu():
    """Sinkronisasi menu Request Pembelian dengan database"""
    print("\n" + "="*60)
    print("🔄 SINKRONISASI MENU REQUEST PEMBELIAN")
    print("="*60)
    
    try:
        with app.app_context():
            # 1. Buat/Update menu parent
            parent_data = REQUEST_PEMBELIAN_MENUS['parent']
            parent_menu = Menu.query.filter_by(path=parent_data['path']).first()
            
            if parent_menu:
                print(f"📝 Update menu parent: {parent_menu.name}")
                parent_menu.name = parent_data['name']
                parent_menu.icon = parent_data['icon']
                parent_menu.order_index = parent_data['order_index']
                parent_menu.description = parent_data['description']
                parent_menu.is_active = True
                parent_menu.is_system_menu = parent_data['is_system_menu']
                parent_menu.updated_at = datetime.utcnow()
            else:
                print(f"➕ Buat menu parent: {parent_data['name']}")
                parent_menu = Menu(
                    name=parent_data['name'],
                    path=parent_data['path'],
                    icon=parent_data['icon'],
                    parent_id=None,
                    order_index=parent_data['order_index'],
                    description=parent_data['description'],
                    is_active=True,
                    is_system_menu=parent_data['is_system_menu']
                )
                db.session.add(parent_menu)
            
            db.session.flush()  # Get the ID
            parent_id = parent_menu.id
            print(f"   ✅ Menu parent ID: {parent_id}")
            
            # 2. Buat/Update submenu
            created_submenus = []
            updated_submenus = []
            
            for submenu_data in REQUEST_PEMBELIAN_MENUS['submenus']:
                submenu = Menu.query.filter_by(path=submenu_data['path']).first()
                
                if submenu:
                    print(f"📝 Update submenu: {submenu.name}")
                    submenu.name = submenu_data['name']
                    submenu.icon = submenu_data['icon']
                    submenu.parent_id = parent_id
                    submenu.order_index = submenu_data['order_index']
                    submenu.description = submenu_data['description']
                    submenu.is_active = True
                    submenu.is_system_menu = submenu_data['is_system_menu']
                    submenu.updated_at = datetime.utcnow()
                    updated_submenus.append(submenu)
                else:
                    print(f"➕ Buat submenu: {submenu_data['name']}")
                    submenu = Menu(
                        name=submenu_data['name'],
                        path=submenu_data['path'],
                        icon=submenu_data['icon'],
                        parent_id=parent_id,
                        order_index=submenu_data['order_index'],
                        description=submenu_data['description'],
                        is_active=True,
                        is_system_menu=submenu_data['is_system_menu']
                    )
                    db.session.add(submenu)
                    created_submenus.append(submenu)
            
            db.session.flush()
            
            # 3. Dapatkan semua menu (parent + submenu) untuk permission
            all_menus = [parent_menu] + created_submenus + updated_submenus
            menu_ids = [m.id for m in all_menus]
            
            # 4. Dapatkan semua role yang aktif
            roles = Role.query.filter_by(is_active=True).all()
            print(f"\n🔐 Memberikan permission ke {len(roles)} role")
            
            # 5. Berikan permission untuk setiap role
            permissions_created = 0
            permissions_updated = 0
            
            for role in roles:
                print(f"\n   Role: {role.name} (ID: {role.id})")
                
                for menu in all_menus:
                    # Cek apakah permission sudah ada
                    permission = MenuPermission.query.filter_by(
                        menu_id=menu.id,
                        role_id=role.id
                    ).first()
                    
                    if permission:
                        # Update permission jika sudah ada
                        if not permission.can_read or not permission.show_in_sidebar or not permission.is_active:
                            permission.can_read = True
                            permission.can_create = True
                            permission.can_update = True
                            permission.can_delete = True
                            permission.show_in_sidebar = True
                            permission.is_active = True
                            permission.granted_at = datetime.utcnow()
                            permissions_updated += 1
                            print(f"      ✅ Update permission untuk {menu.name}")
                    else:
                        # Buat permission baru
                        permission = MenuPermission(
                            menu_id=menu.id,
                            role_id=role.id,
                            can_read=True,
                            can_create=True,
                            can_update=True,
                            can_delete=True,
                            show_in_sidebar=True,
                            is_active=True,
                            granted_at=datetime.utcnow()
                        )
                        db.session.add(permission)
                        permissions_created += 1
                        print(f"      ➕ Buat permission untuk {menu.name}")
            
            # Commit semua perubahan
            db.session.commit()
            
            print("\n" + "="*60)
            print("✅ SINKRONISASI SELESAI")
            print("="*60)
            print(f"📊 Ringkasan:")
            print(f"   - Menu parent: {'Updated' if parent_menu.id else 'Created'}")
            print(f"   - Submenu dibuat: {len(created_submenus)}")
            print(f"   - Submenu diupdate: {len(updated_submenus)}")
            print(f"   - Permission dibuat: {permissions_created}")
            print(f"   - Permission diupdate: {permissions_updated}")
            print(f"   - Total role yang diberi akses: {len(roles)}")
            
            return True
            
    except Exception as e:
        if 'db' in locals() and hasattr(db, 'session'):
            db.session.rollback()
        print(f"\n❌ Error sinkronisasi menu: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function"""
    print("\n" + "="*60)
    print("🚀 SINKRONISASI MENU REQUEST PEMBELIAN")
    print("="*60)
    
    # Cek status database
    if not check_database_status():
        print("\n❌ Gagal mengecek status database")
        sys.exit(1)
    
    # Konfirmasi (skip jika non-interactive mode)
    print("\n" + "="*60)
    if sys.stdin.isatty():
        response = input("Lanjutkan sinkronisasi? (y/n): ").strip().lower()
        if response != 'y':
            print("❌ Sinkronisasi dibatalkan")
            sys.exit(0)
    else:
        print("Non-interactive mode: Melanjutkan sinkronisasi...")
    
    # Jalankan sinkronisasi
    success = sync_request_pembelian_menu()
    
    if success:
        print("\n✅ Sinkronisasi menu Request Pembelian berhasil!")
        print("\n💡 Tips:")
        print("   - Menu akan muncul di sidebar setelah refresh halaman")
        print("   - Pastikan user memiliki role yang aktif untuk melihat menu")
        print("   - Admin memiliki akses penuh ke semua menu")
    else:
        print("\n❌ Gagal sinkronisasi menu Request Pembelian")
        sys.exit(1)


if __name__ == '__main__':
    main()

