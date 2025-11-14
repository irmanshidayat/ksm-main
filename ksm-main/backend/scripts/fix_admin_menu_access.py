#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Admin Menu Access Script
Script untuk memastikan user admin memiliki role Admin dan permission menu
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import app - adjust import based on your app structure
try:
    from app import app
except ImportError:
    # If app is not directly importable, create it
    import sys
    import os
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, backend_dir)
    from app import app
from config.database import db
from models import User
from models import Role, UserRole
from models.menu_models import Menu, MenuPermission
from domains.role.services.permission_service import permission_service
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_admin_menu_access():
    """Fix admin user menu access"""
    with app.app_context():
        try:
            logger.info("🚀 Starting admin menu access fix...")
            
            # 1. Find or create Admin role
            admin_role = Role.query.filter_by(code='ADMIN').first()
            if not admin_role:
                logger.info("📋 Creating Admin role...")
                admin_role = Role(
                    name='Admin',
                    code='ADMIN',
                    description='Administrator dengan akses penuh',
                    level=1,
                    is_management=True,
                    is_active=True
                )
                db.session.add(admin_role)
                db.session.commit()
                logger.info("✅ Admin role created")
            else:
                logger.info(f"✅ Admin role found: {admin_role.name}")
            
            # 2. Find admin user
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                logger.error("❌ Admin user not found!")
                return
            
            logger.info(f"✅ Admin user found: {admin_user.username}")
            
            # 3. Assign Admin role to admin user if not exists
            user_role = UserRole.query.filter_by(
                user_id=admin_user.id,
                role_id=admin_role.id
            ).first()
            
            if not user_role:
                logger.info("📋 Assigning Admin role to admin user...")
                user_role = UserRole(
                    user_id=admin_user.id,
                    role_id=admin_role.id,
                    is_active=True,
                    is_primary=True
                )
                db.session.add(user_role)
                db.session.commit()
                logger.info("✅ Admin role assigned to admin user")
            else:
                logger.info("✅ Admin role already assigned to admin user")
                # Ensure it's active
                if not user_role.is_active:
                    user_role.is_active = True
                    db.session.commit()
                    logger.info("✅ Activated admin user role")
            
            # 4. Initialize default menus if not exists
            menus_count = Menu.query.count()
            if menus_count == 0:
                logger.info("📋 Initializing default menus...")
                permission_service.create_default_menus()
                logger.info("✅ Default menus created")
            
            # 5. Ensure Admin role has permission for all menus with show_in_sidebar = True
            all_menus = Menu.query.filter_by(is_active=True).all()
            logger.info(f"📋 Found {len(all_menus)} active menus")
            
            # Check if show_in_sidebar column exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('menu_permissions')]
            has_show_in_sidebar = 'show_in_sidebar' in columns
            
            permissions_created = 0
            permissions_updated = 0
            
            for menu in all_menus:
                # Use raw SQL query to avoid error if show_in_sidebar column doesn't exist
                from sqlalchemy import text
                result = db.session.execute(
                    text("""
                        SELECT id, menu_id, role_id, can_read, can_create, can_update, can_delete, is_active
                        FROM menu_permissions
                        WHERE menu_id = :menu_id AND role_id = :role_id
                        LIMIT 1
                    """),
                    {'menu_id': menu.id, 'role_id': admin_role.id}
                ).fetchone()
                
                permission_id = result[0] if result else None
                
                if not permission_id:
                    # Create permission with full access using raw SQL
                    if has_show_in_sidebar:
                        db.session.execute(
                            text("""
                                INSERT INTO menu_permissions 
                                (menu_id, role_id, can_read, can_create, can_update, can_delete, is_active, show_in_sidebar, granted_at)
                                VALUES (:menu_id, :role_id, 1, 1, 1, 1, 1, 1, NOW())
                            """),
                            {'menu_id': menu.id, 'role_id': admin_role.id}
                        )
                    else:
                        db.session.execute(
                            text("""
                                INSERT INTO menu_permissions 
                                (menu_id, role_id, can_read, can_create, can_update, can_delete, is_active, granted_at)
                                VALUES (:menu_id, :role_id, 1, 1, 1, 1, 1, NOW())
                            """),
                            {'menu_id': menu.id, 'role_id': admin_role.id}
                        )
                    permissions_created += 1
                    logger.info(f"✅ Created permission for menu: {menu.name}")
                else:
                    # Update permission to ensure full access using raw SQL
                    if has_show_in_sidebar:
                        update_result = db.session.execute(
                            text("""
                                UPDATE menu_permissions 
                                SET can_read = 1, can_create = 1, can_update = 1, can_delete = 1, is_active = 1, show_in_sidebar = 1
                                WHERE id = :permission_id
                            """),
                            {'permission_id': permission_id}
                        )
                    else:
                        update_result = db.session.execute(
                            text("""
                                UPDATE menu_permissions 
                                SET can_read = 1, can_create = 1, can_update = 1, can_delete = 1, is_active = 1
                                WHERE id = :permission_id
                            """),
                            {'permission_id': permission_id}
                        )
                    if update_result.rowcount > 0:
                        permissions_updated += 1
                        logger.info(f"✅ Updated permission for menu: {menu.name}")
            
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
    fix_admin_menu_access()

