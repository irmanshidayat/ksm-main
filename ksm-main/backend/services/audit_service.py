#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit Service - Best Practices Implementation
Service untuk mengelola audit logging dan monitoring
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from flask import request
from config.database import db
from models.role_management import AuditLog

logger = logging.getLogger(__name__)

class AuditService:
    """Service untuk mengelola audit logging"""
    
    # Standard audit actions
    ACTIONS = {
        'CREATE': 'Create',
        'UPDATE': 'Update', 
        'DELETE': 'Delete',
        'ASSIGN': 'Assign',
        'REVOKE': 'Revoke',
        'APPROVE': 'Approve',
        'REJECT': 'Reject',
        'LOGIN': 'Login',
        'LOGOUT': 'Logout',
        'ACCESS': 'Access',
        'EXPORT': 'Export',
        'IMPORT': 'Import'
    }
    
    # Standard resource types
    RESOURCE_TYPES = {
        'USER': 'User',
        'ROLE': 'Role',
        'PERMISSION': 'Permission',
        'DEPARTMENT': 'Department',
        'WORKFLOW': 'Workflow',
        'AUDIT': 'Audit',
        'SYSTEM': 'System'
    }
    
    def __init__(self):
        pass
    
    def initialize_audit_tables(self):
        """Initialize audit tables - must be called within app context"""
        try:
            # Check if audit logs already exist
            if AuditLog.query.count() > 0:
                logger.info("[INFO] Audit tables already exist, skipping initialization")
                return
            
            logger.info("[INIT] Initializing audit tables...")
            
            # Create initial audit log entry
            initial_log = AuditLog(
                user_id=1,  # System user
                action='CREATE',
                resource_type='SYSTEM',
                resource_id=1,
                additional_info={'description': 'Audit system initialized'},
                ip_address='127.0.0.1',
                user_agent='System Initialization'
            )
            
            db.session.add(initial_log)
            db.session.commit()
            logger.info("[SUCCESS] Audit tables initialized successfully")
            
        except Exception as e:
            logger.error(f"[ERROR] Error initializing audit tables: {e}")
            db.session.rollback()
            raise
    
    def log_action(self, user_id: int, action: str, resource_type: str, 
                   resource_id: int = None, old_values: Dict = None, 
                   new_values: Dict = None, additional_info: Dict = None) -> Optional[AuditLog]:
        """Log user action"""
        try:
            # Get request information
            ip_address = self.get_client_ip()
            user_agent = request.headers.get('User-Agent') if request else None
            
            # Create audit log entry
            audit_log = AuditLog.log_action(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent,
                additional_info=additional_info
            )
            
            logger.info(f"📝 Audit log created: {action} {resource_type} by user {user_id}")
            return audit_log
            
        except Exception as e:
            logger.error(f"❌ Error creating audit log: {e}")
            return None
    
    def log_user_creation(self, user_id: int, created_user_data: Dict) -> bool:
        """Log user creation"""
        try:
            self.log_action(
                user_id=user_id,
                action='CREATE',
                resource_type='USER',
                resource_id=created_user_data.get('id'),
                new_values=created_user_data,
                additional_info={'operation': 'user_creation'}
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Error logging user creation: {e}")
            return False
    
    def log_user_update(self, user_id: int, user_id_updated: int, 
                       old_values: Dict, new_values: Dict) -> bool:
        """Log user update"""
        try:
            self.log_action(
                user_id=user_id,
                action='UPDATE',
                resource_type='USER',
                resource_id=user_id_updated,
                old_values=old_values,
                new_values=new_values,
                additional_info={'operation': 'user_update'}
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Error logging user update: {e}")
            return False
    
    def log_user_deletion(self, user_id: int, deleted_user_data: Dict) -> bool:
        """Log user deletion"""
        try:
            self.log_action(
                user_id=user_id,
                action='DELETE',
                resource_type='USER',
                resource_id=deleted_user_data.get('id'),
                old_values=deleted_user_data,
                additional_info={'operation': 'user_deletion'}
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Error logging user deletion: {e}")
            return False
    
    def log_role_assignment(self, user_id: int, target_user_id: int, 
                           role_id: int, role_name: str) -> bool:
        """Log role assignment"""
        try:
            self.log_action(
                user_id=user_id,
                action='ASSIGN',
                resource_type='ROLE',
                resource_id=role_id,
                new_values={
                    'target_user_id': target_user_id,
                    'role_id': role_id,
                    'role_name': role_name
                },
                additional_info={'operation': 'role_assignment'}
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Error logging role assignment: {e}")
            return False
    
    def log_role_revocation(self, user_id: int, target_user_id: int, 
                           role_id: int, role_name: str) -> bool:
        """Log role revocation"""
        try:
            self.log_action(
                user_id=user_id,
                action='REVOKE',
                resource_type='ROLE',
                resource_id=role_id,
                old_values={
                    'target_user_id': target_user_id,
                    'role_id': role_id,
                    'role_name': role_name
                },
                additional_info={'operation': 'role_revocation'}
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Error logging role revocation: {e}")
            return False
    
    def log_permission_change(self, user_id: int, role_id: int, 
                             permission_id: int, granted: bool) -> bool:
        """Log permission change"""
        try:
            self.log_action(
                user_id=user_id,
                action='UPDATE',
                resource_type='PERMISSION',
                resource_id=permission_id,
                new_values={
                    'role_id': role_id,
                    'permission_id': permission_id,
                    'granted': granted
                },
                additional_info={'operation': 'permission_change'}
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Error logging permission change: {e}")
            return False
    
    def log_department_creation(self, user_id: int, department_data: Dict) -> bool:
        """Log department creation"""
        try:
            self.log_action(
                user_id=user_id,
                action='CREATE',
                resource_type='DEPARTMENT',
                resource_id=department_data.get('id'),
                new_values=department_data,
                additional_info={'operation': 'department_creation'}
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Error logging department creation: {e}")
            return False
    
    def log_workflow_action(self, user_id: int, workflow_id: int, 
                           action: str, workflow_data: Dict) -> bool:
        """Log workflow action"""
        try:
            self.log_action(
                user_id=user_id,
                action=action,
                resource_type='WORKFLOW',
                resource_id=workflow_id,
                new_values=workflow_data,
                additional_info={'operation': 'workflow_action'}
            )
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error logging workflow action: {e}")
            return False
    
    def log_login(self, user_id: int, login_data: Dict = None) -> bool:
        """Log user login"""
        try:
            self.log_action(
                user_id=user_id,
                action='LOGIN',
                resource_type='SYSTEM',
                additional_info={
                    'operation': 'user_login',
                    'login_data': login_data or {}
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error logging login: {e}")
            return False
    
    def log_logout(self, user_id: int) -> bool:
        """Log user logout"""
        try:
            self.log_action(
                user_id=user_id,
                action='LOGOUT',
                resource_type='SYSTEM',
                additional_info={'operation': 'user_logout'}
            )
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Error logging logout: {e}")
            return False
    
    def log_data_access(self, user_id: int, resource_type: str, 
                       resource_id: int, access_type: str) -> bool:
        """Log data access"""
        try:
            self.log_action(
                user_id=user_id,
                action='ACCESS',
                resource_type=resource_type,
                resource_id=resource_id,
                additional_info={
                    'operation': 'data_access',
                    'access_type': access_type
                }
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Error logging data access: {e}")
            return False
    
    def get_client_ip(self) -> str:
        """Get client IP address"""
        try:
            if request:
                # Check for forwarded IP
                if request.headers.get('X-Forwarded-For'):
                    return request.headers.get('X-Forwarded-For').split(',')[0].strip()
                elif request.headers.get('X-Real-IP'):
                    return request.headers.get('X-Real-IP')
                else:
                    return request.remote_addr
            return 'unknown'
        except Exception:
            return 'unknown'
    
    def get_user_activity(self, user_id: int, limit: int = 50, 
                         action: str = None, resource_type: str = None) -> List[Dict]:
        """Get user activity logs"""
        try:
            query = AuditLog.query.filter_by(user_id=user_id)
            
            if action:
                query = query.filter_by(action=action)
            
            if resource_type:
                query = query.filter_by(resource_type=resource_type)
            
            logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
            return [log.to_dict() for log in logs]
            
        except Exception as e:
            logger.error(f"❌ Error getting user activity: {e}")
            return []
    
    def get_resource_history(self, resource_type: str, resource_id: int, 
                           limit: int = 50) -> List[Dict]:
        """Get resource change history"""
        try:
            logs = AuditLog.get_resource_history(resource_type, resource_id, limit)
            return [log.to_dict() for log in logs]
            
        except Exception as e:
            logger.error(f"❌ Error getting resource history: {e}")
            return []
    
    def get_audit_statistics(self, days: int = 30) -> Dict:
        """Get audit statistics"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Total logs
            total_logs = AuditLog.query.filter(
                AuditLog.created_at >= since_date
            ).count()
            
            # Logs by action
            action_stats = {}
            for action in self.ACTIONS.keys():
                count = AuditLog.query.filter(
                    AuditLog.action == action,
                    AuditLog.created_at >= since_date
                ).count()
                action_stats[action] = count
            
            # Logs by resource type
            resource_stats = {}
            for resource_type in self.RESOURCE_TYPES.keys():
                count = AuditLog.query.filter(
                    AuditLog.resource_type == resource_type,
                    AuditLog.created_at >= since_date
                ).count()
                resource_stats[resource_type] = count
            
            # Most active users
            from sqlalchemy import func
            active_users = db.session.query(
                AuditLog.user_id,
                func.count(AuditLog.id).label('activity_count')
            ).filter(
                AuditLog.created_at >= since_date
            ).group_by(AuditLog.user_id).order_by(
                func.count(AuditLog.id).desc()
            ).limit(10).all()
            
            return {
                'total_logs': total_logs,
                'action_statistics': action_stats,
                'resource_statistics': resource_stats,
                'most_active_users': [
                    {'user_id': user_id, 'activity_count': count} 
                    for user_id, count in active_users
                ],
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting audit statistics: {e}")
            return {}
    
    def search_audit_logs(self, search_params: Dict) -> List[Dict]:
        """Search audit logs with filters"""
        try:
            query = AuditLog.query
            
            # Filter by user
            if 'user_id' in search_params:
                query = query.filter_by(user_id=search_params['user_id'])
            
            # Filter by action
            if 'action' in search_params:
                query = query.filter_by(action=search_params['action'])
            
            # Filter by resource type
            if 'resource_type' in search_params:
                query = query.filter_by(resource_type=search_params['resource_type'])
            
            # Filter by resource ID
            if 'resource_id' in search_params:
                query = query.filter_by(resource_id=search_params['resource_id'])
            
            # Filter by date range
            if 'start_date' in search_params:
                query = query.filter(AuditLog.created_at >= search_params['start_date'])
            
            if 'end_date' in search_params:
                query = query.filter(AuditLog.created_at <= search_params['end_date'])
            
            # Filter by IP address
            if 'ip_address' in search_params:
                query = query.filter(AuditLog.ip_address == search_params['ip_address'])
            
            # Order and limit
            limit = search_params.get('limit', 100)
            logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
            
            return [log.to_dict() for log in logs]
            
        except Exception as e:
            logger.error(f"❌ Error searching audit logs: {e}")
            return []
    
    def export_audit_logs(self, search_params: Dict, format: str = 'json') -> str:
        """Export audit logs"""
        try:
            logs = self.search_audit_logs(search_params)
            
            if format == 'json':
                import json
                return json.dumps(logs, indent=2, default=str)
            elif format == 'csv':
                import csv
                import io
                
                if not logs:
                    return ""
                
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)
                return output.getvalue()
            else:
                return str(logs)
                
        except Exception as e:
            logger.error(f"❌ Error exporting audit logs: {e}")
            return ""
    
    def cleanup_old_logs(self, days: int = 365):
        """Clean up old audit logs"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            old_logs = AuditLog.query.filter(
                AuditLog.created_at < cutoff_date
            ).all()
            
            for log in old_logs:
                db.session.delete(log)
            
            db.session.commit()
            logger.info(f"🧹 Cleaned up {len(old_logs)} old audit logs")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up old logs: {e}")
            db.session.rollback()
    
    def get_security_alerts(self, days: int = 7) -> List[Dict]:
        """Get security alerts from audit logs"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Suspicious activities
            alerts = []
            
            # Multiple failed logins
            failed_logins = db.session.query(
                AuditLog.user_id,
                AuditLog.ip_address,
                db.func.count(AuditLog.id).label('attempt_count')
            ).filter(
                AuditLog.action == 'LOGIN',
                AuditLog.created_at >= since_date,
                AuditLog.additional_info.contains({'success': False})
            ).group_by(AuditLog.user_id, AuditLog.ip_address).having(
                db.func.count(AuditLog.id) > 5
            ).all()
            
            for user_id, ip_address, count in failed_logins:
                alerts.append({
                    'type': 'multiple_failed_logins',
                    'user_id': user_id,
                    'ip_address': ip_address,
                    'count': count,
                    'severity': 'high'
                })
            
            # Unusual access patterns
            unusual_access = db.session.query(
                AuditLog.user_id,
                AuditLog.ip_address,
                db.func.count(AuditLog.id).label('access_count')
            ).filter(
                AuditLog.action == 'ACCESS',
                AuditLog.created_at >= since_date
            ).group_by(AuditLog.user_id, AuditLog.ip_address).having(
                db.func.count(AuditLog.id) > 100
            ).all()
            
            for user_id, ip_address, count in unusual_access:
                alerts.append({
                    'type': 'unusual_access_pattern',
                    'user_id': user_id,
                    'ip_address': ip_address,
                    'count': count,
                    'severity': 'medium'
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error getting security alerts: {e}")
            return []

# Export singleton instance
audit_service = AuditService()
