#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service terpusat untuk manajemen user-role.
Semua logika assign/remove/list role user dipusatkan di sini
agar tidak duplikasi di banyak controller.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from config.database import db
from models import UserRole, Role


class UserRoleService:
    """Service untuk operasi pada relasi user <-> role"""

    @staticmethod
    def list_user_roles(user_id: int, only_active: bool = True) -> List[UserRole]:
        query = UserRole.query.filter_by(user_id=user_id)
        if only_active:
            query = query.filter_by(is_active=True)
        return query.order_by(UserRole.is_primary.desc(), UserRole.assigned_at.desc()).all()

    @staticmethod
    def list_user_roles_with_details(user_id: int, only_active: bool = True) -> List[Dict[str, Any]]:
        assignments = UserRoleService.list_user_roles(user_id=user_id, only_active=only_active)
        results: List[Dict[str, Any]] = []
        for assignment in assignments:
            role: Optional[Role] = Role.query.get(assignment.role_id)
            results.append({
                **assignment.to_dict(),
                'role': role.to_dict() if hasattr(role, 'to_dict') and role else ({
                    'id': role.id,
                    'name': getattr(role, 'name', None)
                } if role else None)
            })
        return results

    @staticmethod
    def get_primary_role(user_id: int) -> Optional[Role]:
        primary_assignment = UserRole.query.filter_by(user_id=user_id, is_active=True, is_primary=True).first()
        if not primary_assignment:
            # fallback: pertama yang aktif jika tidak ada flag primary
            primary_assignment = UserRole.query.filter_by(user_id=user_id, is_active=True).order_by(UserRole.assigned_at.asc()).first()
        if not primary_assignment:
            return None
        return Role.query.get(primary_assignment.role_id)

    @staticmethod
    def assign_role(user_id: int, role_id: int, assigned_by: Optional[int] = None, is_primary: bool = False, expires_at: Optional[datetime] = None) -> UserRole:
        # Cegah duplikasi assignment aktif yang sama
        existing = UserRole.query.filter_by(user_id=user_id, role_id=role_id, is_active=True).first()
        if existing:
            # Update flag primary/expiry bila perlu
            if is_primary and not existing.is_primary:
                # reset primary lain
                UserRole.query.filter_by(user_id=user_id, is_active=True, is_primary=True).update({'is_primary': False})
                existing.is_primary = True
            if expires_at:
                existing.expires_at = expires_at
            db.session.commit()
            return existing

        # Jika ada assignment non-aktif, aktifkan kembali daripada membuat baris baru
        inactive_existing = UserRole.query.filter_by(user_id=user_id, role_id=role_id, is_active=False).first()
        if inactive_existing:
            if is_primary:
                UserRole.query.filter_by(user_id=user_id, is_active=True, is_primary=True).update({'is_primary': False})
                inactive_existing.is_primary = True
            inactive_existing.is_active = True
            inactive_existing.assigned_by = assigned_by
            inactive_existing.assigned_at = datetime.utcnow()
            inactive_existing.expires_at = expires_at
            db.session.commit()
            return inactive_existing

        if is_primary:
            # pastikan hanya satu primary
            UserRole.query.filter_by(user_id=user_id, is_active=True, is_primary=True).update({'is_primary': False})

        assignment = UserRole(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            is_active=True,
            is_primary=is_primary,
            assigned_at=datetime.utcnow(),
            expires_at=expires_at
        )
        db.session.add(assignment)
        db.session.commit()
        return assignment

    @staticmethod
    def remove_role(user_id: int, role_id: int, soft: bool = True) -> bool:
        assignment = UserRole.query.filter_by(user_id=user_id, role_id=role_id, is_active=True).first()
        if not assignment:
            return False
        if soft:
            assignment.is_active = False
        else:
            db.session.delete(assignment)
        db.session.commit()
        return True


    @staticmethod
    def set_primary_role(user_id: int, role_id: int) -> bool:
        """Set satu role sebagai primary untuk user, auto-unset lainnya."""
        # Pastikan assignment ada dan aktif
        assignment = UserRole.query.filter_by(user_id=user_id, role_id=role_id, is_active=True).first()
        if not assignment:
            return False
        # Unset primary lain
        UserRole.query.filter_by(user_id=user_id, is_active=True, is_primary=True).update({'is_primary': False})
        assignment.is_primary = True
        db.session.commit()
        return True

    @staticmethod
    def deactivate_user_role(user_id: int, role_id: int) -> bool:
        """Soft deactivate satu assignment role aktif."""
        return UserRoleService.remove_role(user_id=user_id, role_id=role_id, soft=True)

    @staticmethod
    def revoke_user_role_by_assignment(user_id: int, user_role_id: int) -> Dict[str, Any]:
        """Revoke (soft deactivate) satu assignment berdasarkan ID assignment.
        - Validasi bahwa assignment milik user_id
        - Cegah menghapus Admin terakhir di sistem
        - Mengembalikan dict hasil operasi untuk respons konsisten
        """
        # Cari assignment aktif berdasarkan id dan user_id
        assignment = UserRole.query.filter_by(id=user_role_id, user_id=user_id, is_active=True).first()
        if not assignment:
            return { 'ok': False, 'error': 'Assignment tidak ditemukan atau sudah nonaktif' }

        # Ambil role terkait
        role = Role.query.get(assignment.role_id)
        role_name = getattr(role, 'name', '').lower() if role else ''

        # Jika role adalah admin, pastikan bukan admin aktif terakhir
        if role_name == 'admin':
            # Hitung jumlah assignment admin aktif selain assignment ini
            active_admin_count = db.session.query(UserRole).join(Role, Role.id == UserRole.role_id) \
                .filter(UserRole.is_active == True) \
                .filter(Role.name.ilike('admin')) \
                .filter(UserRole.id != assignment.id) \
                .count()
            if active_admin_count <= 0:
                return { 'ok': False, 'error': 'Tidak dapat menghapus admin terakhir' }

        # Soft deactivate assignment
        assignment.is_active = False
        db.session.commit()

        return {
            'ok': True,
            'user_id': assignment.user_id,
            'user_role_id': assignment.id,
            'role_id': assignment.role_id
        }

    @staticmethod
    def replace_user_roles(user_id: int, new_role_ids: List[int], primary_role_id: Optional[int] = None, assigned_by: Optional[int] = None) -> Dict[str, Any]:
        """Ganti seluruh daftar roles aktif user agar persis sama dengan new_role_ids.
        - Aktifkan role yang belum aktif
        - Nonaktifkan role yang tidak ada di daftar
        - Set primary jika diberikan
        """
        # Role aktif saat ini
        current_active_assignments = UserRole.query.filter_by(user_id=user_id, is_active=True).all()
        current_role_ids = {a.role_id for a in current_active_assignments}
        target_role_ids = set(new_role_ids or [])

        # Nonaktifkan yang tidak ada di target
        to_deactivate = current_role_ids - target_role_ids
        if to_deactivate:
            UserRole.query.filter(
                UserRole.user_id == user_id,
                UserRole.role_id.in_(list(to_deactivate)),
                UserRole.is_active == True
            ).update({'is_active': False}, synchronize_session=False)

        # Aktifkan/tambahkan yang baru
        to_add = target_role_ids - current_role_ids
        for rid in to_add:
            assignment = UserRole(
                user_id=user_id,
                role_id=rid,
                assigned_by=assigned_by,
                is_active=True,
                is_primary=False,
                assigned_at=datetime.utcnow()
            )
            db.session.add(assignment)

        # Set primary
        if primary_role_id:
            # Unset semua
            UserRole.query.filter_by(user_id=user_id, is_active=True, is_primary=True).update({'is_primary': False})
            # Set primary ke role yang ada di target dan aktif
            primary_assignment = UserRole.query.filter_by(user_id=user_id, role_id=primary_role_id, is_active=True).first()
            if primary_assignment:
                primary_assignment.is_primary = True

        db.session.commit()

        updated = UserRoleService.list_user_roles_with_details(user_id=user_id, only_active=True)
        return {
            'user_id': user_id,
            'roles': updated,
            'primary_role_id': primary_role_id
        }


