#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit Trail Service - Best Practices Implementation
Sistem audit trail untuk compliance dan monitoring yang komprehensif
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import request, current_app
from sqlalchemy import and_, or_, func, desc
import hashlib

logger = logging.getLogger(__name__)

class AuditTrailService:
    """Service untuk audit trail dengan best practices"""
    
    def __init__(self):
        self.retention_policy = self._load_retention_policy()
        self.sensitive_fields = self._load_sensitive_fields()
    
    def _load_retention_policy(self) -> Dict:
        """Load data retention policy"""
        return {
            'user_activities': 365,  # 1 tahun
            'system_events': 2555,   # 7 tahun
            'security_events': 2555, # 7 tahun
            'data_changes': 1095,    # 3 tahun
            'access_logs': 365,      # 1 tahun
            'approval_logs': 1095,   # 3 tahun
            'notification_logs': 180 # 6 bulan
        }
    
    def _load_sensitive_fields(self) -> List[str]:
        """Load sensitive fields yang perlu di-mask"""
        return [
            'password', 'password_hash', 'token', 'secret', 'key',
            'ssn', 'credit_card', 'bank_account', 'personal_id',
            'phone', 'email', 'address', 'salary', 'benefits'
        ]
    
    def log_user_activity(self, user_id: int, activity_type: str, 
                         resource_type: str = None, resource_id: int = None,
                         old_values: Dict = None, new_values: Dict = None,
                         additional_data: Dict = None) -> Dict:
        """Log user activity dengan best practices"""
        try:
            from models.audit_models import UserActivityLog, db
            
            # Mask sensitive data
            old_values_masked = self._mask_sensitive_data(old_values) if old_values else None
            new_values_masked = self._mask_sensitive_data(new_values) if new_values else None
            
            # Create activity log
            activity_log = UserActivityLog(
                user_id=user_id,
                activity_type=activity_type,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values_masked,
                new_values=new_values_masked,
                additional_data=additional_data,
                ip_address=self._get_client_ip(),
                user_agent=request.headers.get('User-Agent', ''),
                session_id=self._get_session_id(),
                timestamp=datetime.utcnow(),
                success=True
            )
            db.session.add(activity_log)
            db.session.commit()
            
            logger.info(f"✅ Logged user activity: {activity_type} by user {user_id}")
            
            return {
                'log_id': activity_log.id,
                'activity_type': activity_type,
                'timestamp': activity_log.timestamp.isoformat(),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error logging user activity: {str(e)}")
            return {
                'log_id': None,
                'activity_type': activity_type,
                'timestamp': datetime.utcnow().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def log_system_event(self, event_type: str, event_category: str,
                        description: str, severity: str = 'info',
                        additional_data: Dict = None) -> Dict:
        """Log system event dengan best practices"""
        try:
            from models.audit_models import SystemEventLog, db
            
            # Create system event log
            system_log = SystemEventLog(
                event_type=event_type,
                event_category=event_category,
                description=description,
                severity=severity,
                additional_data=additional_data,
                ip_address=self._get_client_ip(),
                user_agent=request.headers.get('User-Agent', ''),
                timestamp=datetime.utcnow(),
                success=True
            )
            db.session.add(system_log)
            db.session.commit()
            
            logger.info(f"✅ Logged system event: {event_type} - {description}")
            
            return {
                'log_id': system_log.id,
                'event_type': event_type,
                'timestamp': system_log.timestamp.isoformat(),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error logging system event: {str(e)}")
            return {
                'log_id': None,
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def log_security_event(self, event_type: str, user_id: int = None,
                          description: str = None, severity: str = 'medium',
                          additional_data: Dict = None) -> Dict:
        """Log security event dengan best practices"""
        try:
            from models.audit_models import SecurityEventLog, db
            
            # Create security event log
            security_log = SecurityEventLog(
                event_type=event_type,
                user_id=user_id,
                description=description,
                severity=severity,
                additional_data=additional_data,
                ip_address=self._get_client_ip(),
                user_agent=request.headers.get('User-Agent', ''),
                timestamp=datetime.utcnow(),
                success=True
            )
            db.session.add(security_log)
            db.session.commit()
            
            # Check for security alerts
            self._check_security_alerts(security_log)
            
            logger.info(f"✅ Logged security event: {event_type} - {description}")
            
            return {
                'log_id': security_log.id,
                'event_type': event_type,
                'timestamp': security_log.timestamp.isoformat(),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error logging security event: {str(e)}")
            return {
                'log_id': None,
                'event_type': event_type,
                'timestamp': datetime.utcnow().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def log_data_change(self, user_id: int, table_name: str, record_id: int,
                       change_type: str, old_values: Dict = None,
                       new_values: Dict = None, additional_data: Dict = None) -> Dict:
        """Log data change dengan best practices"""
        try:
            from models.audit_models import DataChangeLog, db
            
            # Mask sensitive data
            old_values_masked = self._mask_sensitive_data(old_values) if old_values else None
            new_values_masked = self._mask_sensitive_data(new_values) if new_values else None
            
            # Create data change log
            change_log = DataChangeLog(
                user_id=user_id,
                table_name=table_name,
                record_id=record_id,
                change_type=change_type,
                old_values=old_values_masked,
                new_values=new_values_masked,
                additional_data=additional_data,
                ip_address=self._get_client_ip(),
                user_agent=request.headers.get('User-Agent', ''),
                timestamp=datetime.utcnow(),
                success=True
            )
            db.session.add(change_log)
            db.session.commit()
            
            logger.info(f"✅ Logged data change: {change_type} on {table_name}.{record_id}")
            
            return {
                'log_id': change_log.id,
                'change_type': change_type,
                'timestamp': change_log.timestamp.isoformat(),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error logging data change: {str(e)}")
            return {
                'log_id': None,
                'change_type': change_type,
                'timestamp': datetime.utcnow().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def log_access_attempt(self, user_id: int = None, resource_type: str = None,
                          resource_id: int = None, access_type: str = None,
                          success: bool = True, failure_reason: str = None) -> Dict:
        """Log access attempt dengan best practices"""
        try:
            from models.audit_models import AccessLog, db
            
            # Create access log
            access_log = AccessLog(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                access_type=access_type,
                success=success,
                failure_reason=failure_reason,
                ip_address=self._get_client_ip(),
                user_agent=request.headers.get('User-Agent', ''),
                timestamp=datetime.utcnow()
            )
            db.session.add(access_log)
            db.session.commit()
            
            # Check for suspicious access patterns
            if not success:
                self._check_suspicious_access(access_log)
            
            logger.info(f"✅ Logged access attempt: {access_type} on {resource_type}.{resource_id}")
            
            return {
                'log_id': access_log.id,
                'access_type': access_type,
                'success': success,
                'timestamp': access_log.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error logging access attempt: {str(e)}")
            return {
                'log_id': None,
                'access_type': access_type,
                'success': False,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def _mask_sensitive_data(self, data: Dict) -> Dict:
        """Mask sensitive data dalam audit log"""
        if not data:
            return data
        
        masked_data = data.copy()
        
        for key, value in masked_data.items():
            if any(sensitive_field in key.lower() for sensitive_field in self.sensitive_fields):
                if isinstance(value, str) and len(value) > 4:
                    masked_data[key] = value[:2] + '*' * (len(value) - 4) + value[-2:]
                else:
                    masked_data[key] = '***MASKED***'
        
        return masked_data
    
    def _get_client_ip(self) -> str:
        """Get client IP address"""
        try:
            if request.headers.get('X-Forwarded-For'):
                return request.headers.get('X-Forwarded-For').split(',')[0].strip()
            elif request.headers.get('X-Real-IP'):
                return request.headers.get('X-Real-IP')
            else:
                return request.remote_addr
        except:
            return 'unknown'
    
    def _get_session_id(self) -> str:
        """Get session ID"""
        try:
            return request.cookies.get('session', 'unknown')
        except:
            return 'unknown'
    
    def _check_security_alerts(self, security_log):
        """Check for security alerts"""
        try:
            # Check for multiple failed login attempts
            if security_log.event_type == 'failed_login':
                self._check_failed_login_pattern(security_log.user_id, security_log.ip_address)
            
            # Check for suspicious IP addresses
            if security_log.ip_address:
                self._check_suspicious_ip(security_log.ip_address)
            
            # Check for privilege escalation attempts
            if security_log.event_type == 'privilege_escalation':
                self._alert_privilege_escalation(security_log)
            
        except Exception as e:
            logger.error(f"❌ Error checking security alerts: {str(e)}")
    
    def _check_failed_login_pattern(self, user_id: int, ip_address: str):
        """Check for failed login pattern"""
        try:
            from models.audit_models import SecurityEventLog
            
            # Check failed logins in last 15 minutes
            recent_failed_logins = SecurityEventLog.query.filter(
                SecurityEventLog.event_type == 'failed_login',
                SecurityEventLog.timestamp >= datetime.utcnow() - timedelta(minutes=15),
                or_(
                    SecurityEventLog.user_id == user_id,
                    SecurityEventLog.ip_address == ip_address
                )
            ).count()
            
            if recent_failed_logins >= 5:
                # Create security alert
                self._create_security_alert(
                    'multiple_failed_logins',
                    f'Multiple failed login attempts detected: {recent_failed_logins} attempts',
                    'high',
                    {'user_id': user_id, 'ip_address': ip_address, 'attempts': recent_failed_logins}
                )
        
        except Exception as e:
            logger.error(f"❌ Error checking failed login pattern: {str(e)}")
    
    def _check_suspicious_ip(self, ip_address: str):
        """Check for suspicious IP address"""
        try:
            # This would integrate with threat intelligence feeds
            # For now, just log the check
            logger.info(f"Checking suspicious IP: {ip_address}")
        
        except Exception as e:
            logger.error(f"❌ Error checking suspicious IP: {str(e)}")
    
    def _alert_privilege_escalation(self, security_log):
        """Alert on privilege escalation attempts"""
        try:
            self._create_security_alert(
                'privilege_escalation',
                f'Privilege escalation attempt detected: {security_log.description}',
                'critical',
                {'user_id': security_log.user_id, 'event_id': security_log.id}
            )
        
        except Exception as e:
            logger.error(f"❌ Error alerting privilege escalation: {str(e)}")
    
    def _check_suspicious_access(self, access_log):
        """Check for suspicious access patterns"""
        try:
            from models.audit_models import AccessLog
            
            # Check for multiple failed access attempts
            recent_failed_access = AccessLog.query.filter(
                AccessLog.ip_address == access_log.ip_address,
                AccessLog.success == False,
                AccessLog.timestamp >= datetime.utcnow() - timedelta(minutes=10)
            ).count()
            
            if recent_failed_access >= 10:
                # Create security alert
                self._create_security_alert(
                    'suspicious_access_pattern',
                    f'Suspicious access pattern detected: {recent_failed_access} failed attempts',
                    'medium',
                    {'ip_address': access_log.ip_address, 'attempts': recent_failed_access}
                )
        
        except Exception as e:
            logger.error(f"❌ Error checking suspicious access: {str(e)}")
    
    def _create_security_alert(self, alert_type: str, description: str, 
                              severity: str, additional_data: Dict = None):
        """Create security alert"""
        try:
            from models.audit_models import SecurityAlert, db
            
            alert = SecurityAlert(
                alert_type=alert_type,
                description=description,
                severity=severity,
                additional_data=additional_data,
                status='active',
                created_at=datetime.utcnow()
            )
            db.session.add(alert)
            db.session.commit()
            
            # Send notification to security team
            # This would integrate with notification system
            
            logger.warning(f"🚨 Security alert created: {alert_type} - {description}")
        
        except Exception as e:
            logger.error(f"❌ Error creating security alert: {str(e)}")
    
    def get_audit_logs(self, log_type: str = None, user_id: int = None,
                      start_date: datetime = None, end_date: datetime = None,
                      limit: int = 100, offset: int = 0) -> Dict:
        """Get audit logs dengan filtering"""
        try:
            logs = []
            total_count = 0
            
            if log_type == 'user_activity' or not log_type:
                user_logs, user_count = self._get_user_activity_logs(
                    user_id, start_date, end_date, limit, offset
                )
                logs.extend(user_logs)
                total_count += user_count
            
            if log_type == 'system_event' or not log_type:
                system_logs, system_count = self._get_system_event_logs(
                    start_date, end_date, limit, offset
                )
                logs.extend(system_logs)
                total_count += system_count
            
            if log_type == 'security_event' or not log_type:
                security_logs, security_count = self._get_security_event_logs(
                    user_id, start_date, end_date, limit, offset
                )
                logs.extend(security_logs)
                total_count += security_count
            
            if log_type == 'data_change' or not log_type:
                change_logs, change_count = self._get_data_change_logs(
                    user_id, start_date, end_date, limit, offset
                )
                logs.extend(change_logs)
                total_count += change_count
            
            if log_type == 'access' or not log_type:
                access_logs, access_count = self._get_access_logs(
                    user_id, start_date, end_date, limit, offset
                )
                logs.extend(access_logs)
                total_count += access_count
            
            # Sort by timestamp
            logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return {
                'logs': logs[:limit],
                'total_count': total_count,
                'has_more': len(logs) > limit
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting audit logs: {str(e)}")
            return {'logs': [], 'total_count': 0, 'has_more': False}
    
    def _get_user_activity_logs(self, user_id: int = None, start_date: datetime = None,
                               end_date: datetime = None, limit: int = 100, offset: int = 0):
        """Get user activity logs"""
        try:
            from models.audit_models import UserActivityLog
            
            query = UserActivityLog.query
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            if start_date:
                query = query.filter(UserActivityLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(UserActivityLog.timestamp <= end_date)
            
            logs = query.order_by(desc(UserActivityLog.timestamp)).offset(offset).limit(limit).all()
            total_count = query.count()
            
            return [log.to_dict() for log in logs], total_count
            
        except Exception as e:
            logger.error(f"❌ Error getting user activity logs: {str(e)}")
            return [], 0
    
    def _get_system_event_logs(self, start_date: datetime = None, end_date: datetime = None,
                              limit: int = 100, offset: int = 0):
        """Get system event logs"""
        try:
            from models.audit_models import SystemEventLog
            
            query = SystemEventLog.query
            
            if start_date:
                query = query.filter(SystemEventLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(SystemEventLog.timestamp <= end_date)
            
            logs = query.order_by(desc(SystemEventLog.timestamp)).offset(offset).limit(limit).all()
            total_count = query.count()
            
            return [log.to_dict() for log in logs], total_count
            
        except Exception as e:
            logger.error(f"❌ Error getting system event logs: {str(e)}")
            return [], 0
    
    def _get_security_event_logs(self, user_id: int = None, start_date: datetime = None,
                                end_date: datetime = None, limit: int = 100, offset: int = 0):
        """Get security event logs"""
        try:
            from models.audit_models import SecurityEventLog
            
            query = SecurityEventLog.query
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            if start_date:
                query = query.filter(SecurityEventLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(SecurityEventLog.timestamp <= end_date)
            
            logs = query.order_by(desc(SecurityEventLog.timestamp)).offset(offset).limit(limit).all()
            total_count = query.count()
            
            return [log.to_dict() for log in logs], total_count
            
        except Exception as e:
            logger.error(f"❌ Error getting security event logs: {str(e)}")
            return [], 0
    
    def _get_data_change_logs(self, user_id: int = None, start_date: datetime = None,
                             end_date: datetime = None, limit: int = 100, offset: int = 0):
        """Get data change logs"""
        try:
            from models.audit_models import DataChangeLog
            
            query = DataChangeLog.query
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            if start_date:
                query = query.filter(DataChangeLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(DataChangeLog.timestamp <= end_date)
            
            logs = query.order_by(desc(DataChangeLog.timestamp)).offset(offset).limit(limit).all()
            total_count = query.count()
            
            return [log.to_dict() for log in logs], total_count
            
        except Exception as e:
            logger.error(f"❌ Error getting data change logs: {str(e)}")
            return [], 0
    
    def _get_access_logs(self, user_id: int = None, start_date: datetime = None,
                        end_date: datetime = None, limit: int = 100, offset: int = 0):
        """Get access logs"""
        try:
            from models.audit_models import AccessLog
            
            query = AccessLog.query
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            if start_date:
                query = query.filter(AccessLog.timestamp >= start_date)
            
            if end_date:
                query = query.filter(AccessLog.timestamp <= end_date)
            
            logs = query.order_by(desc(AccessLog.timestamp)).offset(offset).limit(limit).all()
            total_count = query.count()
            
            return [log.to_dict() for log in logs], total_count
            
        except Exception as e:
            logger.error(f"❌ Error getting access logs: {str(e)}")
            return [], 0
    
    def generate_audit_report(self, report_type: str, start_date: datetime,
                            end_date: datetime, filters: Dict = None) -> Dict:
        """Generate audit report"""
        try:
            if report_type == 'user_activity':
                return self._generate_user_activity_report(start_date, end_date, filters)
            elif report_type == 'security_events':
                return self._generate_security_events_report(start_date, end_date, filters)
            elif report_type == 'data_changes':
                return self._generate_data_changes_report(start_date, end_date, filters)
            elif report_type == 'access_patterns':
                return self._generate_access_patterns_report(start_date, end_date, filters)
            else:
                raise Exception(f"Unknown report type: {report_type}")
                
        except Exception as e:
            logger.error(f"❌ Error generating audit report: {str(e)}")
            return {'error': str(e)}
    
    def _generate_user_activity_report(self, start_date: datetime, end_date: datetime, filters: Dict):
        """Generate user activity report"""
        try:
            from models.audit_models import UserActivityLog
            
            query = UserActivityLog.query.filter(
                UserActivityLog.timestamp >= start_date,
                UserActivityLog.timestamp <= end_date
            )
            
            if filters and filters.get('user_id'):
                query = query.filter_by(user_id=filters['user_id'])
            
            if filters and filters.get('activity_type'):
                query = query.filter_by(activity_type=filters['activity_type'])
            
            # Get summary statistics
            total_activities = query.count()
            unique_users = query.with_entities(UserActivityLog.user_id).distinct().count()
            activity_types = query.with_entities(
                UserActivityLog.activity_type,
                func.count(UserActivityLog.id).label('count')
            ).group_by(UserActivityLog.activity_type).all()
            
            return {
                'report_type': 'user_activity',
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_activities': total_activities,
                    'unique_users': unique_users,
                    'activity_types': [{'type': at.activity_type, 'count': at.count} for at in activity_types]
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating user activity report: {str(e)}")
            return {'error': str(e)}
    
    def _generate_security_events_report(self, start_date: datetime, end_date: datetime, filters: Dict):
        """Generate security events report"""
        try:
            from models.audit_models import SecurityEventLog
            
            query = SecurityEventLog.query.filter(
                SecurityEventLog.timestamp >= start_date,
                SecurityEventLog.timestamp <= end_date
            )
            
            if filters and filters.get('severity'):
                query = query.filter_by(severity=filters['severity'])
            
            if filters and filters.get('event_type'):
                query = query.filter_by(event_type=filters['event_type'])
            
            # Get summary statistics
            total_events = query.count()
            events_by_severity = query.with_entities(
                SecurityEventLog.severity,
                func.count(SecurityEventLog.id).label('count')
            ).group_by(SecurityEventLog.severity).all()
            
            events_by_type = query.with_entities(
                SecurityEventLog.event_type,
                func.count(SecurityEventLog.id).label('count')
            ).group_by(SecurityEventLog.event_type).all()
            
            return {
                'report_type': 'security_events',
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_events': total_events,
                    'events_by_severity': [{'severity': es.severity, 'count': es.count} for es in events_by_severity],
                    'events_by_type': [{'type': et.event_type, 'count': et.count} for et in events_by_type]
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating security events report: {str(e)}")
            return {'error': str(e)}
    
    def _generate_data_changes_report(self, start_date: datetime, end_date: datetime, filters: Dict):
        """Generate data changes report"""
        try:
            from models.audit_models import DataChangeLog
            
            query = DataChangeLog.query.filter(
                DataChangeLog.timestamp >= start_date,
                DataChangeLog.timestamp <= end_date
            )
            
            if filters and filters.get('table_name'):
                query = query.filter_by(table_name=filters['table_name'])
            
            if filters and filters.get('change_type'):
                query = query.filter_by(change_type=filters['change_type'])
            
            # Get summary statistics
            total_changes = query.count()
            changes_by_table = query.with_entities(
                DataChangeLog.table_name,
                func.count(DataChangeLog.id).label('count')
            ).group_by(DataChangeLog.table_name).all()
            
            changes_by_type = query.with_entities(
                DataChangeLog.change_type,
                func.count(DataChangeLog.id).label('count')
            ).group_by(DataChangeLog.change_type).all()
            
            return {
                'report_type': 'data_changes',
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_changes': total_changes,
                    'changes_by_table': [{'table': ct.table_name, 'count': ct.count} for ct in changes_by_table],
                    'changes_by_type': [{'type': cct.change_type, 'count': cct.count} for cct in changes_by_type]
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating data changes report: {str(e)}")
            return {'error': str(e)}
    
    def _generate_access_patterns_report(self, start_date: datetime, end_date: datetime, filters: Dict):
        """Generate access patterns report"""
        try:
            from models.audit_models import AccessLog
            
            query = AccessLog.query.filter(
                AccessLog.timestamp >= start_date,
                AccessLog.timestamp <= end_date
            )
            
            if filters and filters.get('success'):
                query = query.filter_by(success=filters['success'])
            
            if filters and filters.get('resource_type'):
                query = query.filter_by(resource_type=filters['resource_type'])
            
            # Get summary statistics
            total_access = query.count()
            successful_access = query.filter_by(success=True).count()
            failed_access = query.filter_by(success=False).count()
            
            access_by_type = query.with_entities(
                AccessLog.access_type,
                func.count(AccessLog.id).label('count')
            ).group_by(AccessLog.access_type).all()
            
            access_by_resource = query.with_entities(
                AccessLog.resource_type,
                func.count(AccessLog.id).label('count')
            ).group_by(AccessLog.resource_type).all()
            
            return {
                'report_type': 'access_patterns',
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_access': total_access,
                    'successful_access': successful_access,
                    'failed_access': failed_access,
                    'success_rate': (successful_access / total_access * 100) if total_access > 0 else 0,
                    'access_by_type': [{'type': at.access_type, 'count': at.count} for at in access_by_type],
                    'access_by_resource': [{'resource': ar.resource_type, 'count': ar.count} for ar in access_by_resource]
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating access patterns report: {str(e)}")
            return {'error': str(e)}
    
    def cleanup_old_logs(self):
        """Cleanup old logs berdasarkan retention policy"""
        try:
            from models.audit_models import (
                UserActivityLog, SystemEventLog, SecurityEventLog,
                DataChangeLog, AccessLog, db
            )
            
            cleanup_count = 0
            
            # Cleanup user activity logs
            retention_days = self.retention_policy.get('user_activities', 365)
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            deleted_count = UserActivityLog.query.filter(
                UserActivityLog.timestamp < cutoff_date
            ).delete()
            cleanup_count += deleted_count
            
            # Cleanup system event logs
            retention_days = self.retention_policy.get('system_events', 2555)
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            deleted_count = SystemEventLog.query.filter(
                SystemEventLog.timestamp < cutoff_date
            ).delete()
            cleanup_count += deleted_count
            
            # Cleanup security event logs
            retention_days = self.retention_policy.get('security_events', 2555)
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            deleted_count = SecurityEventLog.query.filter(
                SecurityEventLog.timestamp < cutoff_date
            ).delete()
            cleanup_count += deleted_count
            
            # Cleanup data change logs
            retention_days = self.retention_policy.get('data_changes', 1095)
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            deleted_count = DataChangeLog.query.filter(
                DataChangeLog.timestamp < cutoff_date
            ).delete()
            cleanup_count += deleted_count
            
            # Cleanup access logs
            retention_days = self.retention_policy.get('access_logs', 365)
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            deleted_count = AccessLog.query.filter(
                AccessLog.timestamp < cutoff_date
            ).delete()
            cleanup_count += deleted_count
            
            db.session.commit()
            
            logger.info(f"✅ Cleaned up {cleanup_count} old audit logs")
            
            return {
                'cleaned_logs': cleanup_count,
                'cleanup_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up old logs: {str(e)}")
            return {'error': str(e)}
