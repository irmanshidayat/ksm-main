#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Admin Menu Access - Simple Version
Script sederhana untuk memastikan user admin memiliki role dan permission menu
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from config.database import db
from sqlalchemy import text
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_admin_menu_simple():
    """Fix admin menu access using raw SQL"""
    with app.app_context():
        try:
            logger.info("🚀 Starting admin menu access fix (simple version)...")
            
            # 1. Get admin user ID
            admin_result = db.session.execute(
                text("SELECT id FROM users WHERE username = 'admin' LIMIT 1")
            ).fetchone()
            
            if not admin_result:
                logger.error("❌ Admin user not found!")
                return
            
            admin_user_id = admin_result[0]
            logger.info(f"✅ Admin user found: ID={admin_user_id}")
            
            # 2. Get or create Admin role
            role_result = db.session.execute(
                text("SELECT id FROM roles WHERE code = 'ADMIN' LIMIT 1")
            ).fetchone()
            
            if not role_result:
                logger.info("📋 Creating Admin role...")
                db.session.execute(
                    text("""
                        INSERT INTO roles (name, code, description, level, is_management, is_active, created_at, updated_at)
                        VALUES ('Admin', 'ADMIN', 'Administrator dengan akses penuh', 1, 1, 1, NOW(), NOW())
                    """)
                )
                db.session.commit()
                role_result = db.session.execute(
                    text("SELECT id FROM roles WHERE code = 'ADMIN' LIMIT 1")
                ).fetchone()
            
            admin_role_id = role_result[0]
            logger.info(f"✅ Admin role found: ID={admin_role_id}")
            
            # 3. Assign Admin role to admin user if not exists
            user_role_result = db.session.execute(
                text("""
                    SELECT id FROM user_roles 
                    WHERE user_id = :user_id AND role_id = :role_id 
                    LIMIT 1
                """),
                {'user_id': admin_user_id, 'role_id': admin_role_id}
            ).fetchone()
            
            if not user_role_result:
                logger.info("📋 Assigning Admin role to admin user...")
                db.session.execute(
                    text("""
                        INSERT INTO user_roles (user_id, role_id, is_active, is_primary, created_at, updated_at)
                        VALUES (:user_id, :role_id, 1, 1, NOW(), NOW())
                    """),
                    {'user_id': admin_user_id, 'role_id': admin_role_id}
                )
                db.session.commit()
                logger.info("✅ Admin role assigned to admin user")
            else:
                # Ensure it's active
                db.session.execute(
                    text("""
                        UPDATE user_roles 
                        SET is_active = 1, is_primary = 1 
                        WHERE id = :id
                    """),
                    {'id': user_role_result[0]}
                )
                db.session.commit()
                logger.info("✅ Admin role already assigned, activated")
            
            # 4. Get all active menus
            menus = db.session.execute(
                text("SELECT id, name FROM menus WHERE is_active = 1")
            ).fetchall()
            
            logger.info(f"📋 Found {len(menus)} active menus")
            
            # 5. Check if show_in_sidebar column exists
            columns_result = db.session.execute(
                text("SHOW COLUMNS FROM menu_permissions LIKE 'show_in_sidebar'")
            ).fetchone()
            has_show_in_sidebar = columns_result is not None
            
            permissions_created = 0
            permissions_updated = 0
            
            # 6. Create/update permissions for all menus
            for menu_id, menu_name in menus:
                # Check if permission exists
                perm_result = db.session.execute(
                    text("""
                        SELECT id FROM menu_permissions 
                        WHERE menu_id = :menu_id AND role_id = :role_id 
                        LIMIT 1
                    """),
                    {'menu_id': menu_id, 'role_id': admin_role_id}
                ).fetchone()
                
                if not perm_result:
                    # Create permission
                    if has_show_in_sidebar:
                        db.session.execute(
                            text("""
                                INSERT INTO menu_permissions 
                                (menu_id, role_id, can_read, can_create, can_update, can_delete, is_active, show_in_sidebar, granted_at)
                                VALUES (:menu_id, :role_id, 1, 1, 1, 1, 1, 1, NOW())
                            """),
                            {'menu_id': menu_id, 'role_id': admin_role_id}
                        )
                    else:
                        db.session.execute(
                            text("""
                                INSERT INTO menu_permissions 
                                (menu_id, role_id, can_read, can_create, can_update, can_delete, is_active, granted_at)
                                VALUES (:menu_id, :role_id, 1, 1, 1, 1, 1, NOW())
                            """),
                            {'menu_id': menu_id, 'role_id': admin_role_id}
                        )
                    permissions_created += 1
                    logger.info(f"✅ Created permission for menu: {menu_name}")
                else:
                    # Update permission
                    if has_show_in_sidebar:
                        result = db.session.execute(
                            text("""
                                UPDATE menu_permissions 
                                SET can_read = 1, can_create = 1, can_update = 1, can_delete = 1, is_active = 1, show_in_sidebar = 1
                                WHERE id = :id
                            """),
                            {'id': perm_result[0]}
                        )
                    else:
                        result = db.session.execute(
                            text("""
                                UPDATE menu_permissions 
                                SET can_read = 1, can_create = 1, can_update = 1, can_delete = 1, is_active = 1
                                WHERE id = :id
                            """),
                            {'id': perm_result[0]}
                        )
                    if result.rowcount > 0:
                        permissions_updated += 1
                        logger.info(f"✅ Updated permission for menu: {menu_name}")
            
            db.session.commit()
            
            logger.info(f"✅ Created {permissions_created} new permissions")
            logger.info(f"✅ Updated {permissions_updated} existing permissions")
            logger.info("✅ Admin menu access fix completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error fixing admin menu access: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise

if __name__ == "__main__":
    fix_admin_menu_simple()

