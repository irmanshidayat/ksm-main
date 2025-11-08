#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Manager - Handles integrations with external systems
"""

import logging
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    NOTIFICATION = "notification"
    APPROVAL = "approval"
    VENDOR_ANALYSIS = "vendor_analysis"
    AUDIT_TRAIL = "audit_trail"
    FILE_STORAGE = "file_storage"
    AUTHENTICATION = "authentication"

class IntegrationManager:
    """Manages integrations with external systems"""
    
    def __init__(self):
        self.integrations = {
            IntegrationType.NOTIFICATION: NotificationIntegration(),
            IntegrationType.APPROVAL: ApprovalIntegration(),
            IntegrationType.VENDOR_ANALYSIS: VendorAnalysisIntegration(),
            IntegrationType.AUDIT_TRAIL: AuditTrailIntegration(),
            IntegrationType.FILE_STORAGE: FileStorageIntegration(),
            IntegrationType.AUTHENTICATION: AuthenticationIntegration(),
        }
    
    async def trigger_integration(self, integration_type: IntegrationType, event: str, data: Dict) -> Dict:
        """Trigger integration for specific event"""
        try:
            integration = self.integrations.get(integration_type)
            if not integration:
                return {'success': False, 'message': f'Integration {integration_type} not found'}
            
            result = await integration.handle_event(event, data)
            logger.info(f"✅ Integration {integration_type.value} triggered for event {event}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Integration {integration_type.value} failed: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    async def trigger_multiple(self, events: List[Dict]) -> Dict:
        """Trigger multiple integrations"""
        results = {}
        
        for event_data in events:
            integration_type = IntegrationType(event_data['type'])
            event = event_data['event']
            data = event_data['data']
            
            result = await self.trigger_integration(integration_type, event, data)
            results[f"{integration_type.value}_{event}"] = result
        
        return results

class NotificationIntegration:
    """Handles notification integrations (Email, SMS, Push)"""
    
    def __init__(self):
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': 'noreply@KSM.com',
            'password': 'your_password'
        }
        self.sms_config = {
            'api_url': 'https://api.twilio.com/2010-04-01/Accounts/',
            'account_sid': 'your_account_sid',
            'auth_token': 'your_auth_token'
        }
    
    async def handle_event(self, event: str, data: Dict) -> Dict:
        """Handle notification events"""
        try:
            if event == 'file_uploaded':
                return await self._notify_file_uploaded(data)
            elif event == 'deadline_approaching':
                return await self._notify_deadline_approaching(data)
            elif event == 'deadline_passed':
                return await self._notify_deadline_passed(data)
            elif event == 'penawaran_submitted':
                return await self._notify_penawaran_submitted(data)
            elif event == 'admin_upload':
                return await self._notify_admin_upload(data)
            else:
                return {'success': False, 'message': f'Unknown event: {event}'}
                
        except Exception as e:
            logger.error(f"❌ Notification error: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    async def _notify_file_uploaded(self, data: Dict) -> Dict:
        """Notify when file is uploaded"""
        vendor_email = data.get('vendor_email')
        file_name = data.get('file_name')
        request_title = data.get('request_title')
        
        subject = f"File Penawaran Diupload - {request_title}"
        body = f"""
        Halo,
        
        File penawaran "{file_name}" telah berhasil diupload untuk request "{request_title}".
        
        Terima kasih.
        """
        
        return await self._send_email(vendor_email, subject, body)
    
    async def _notify_deadline_approaching(self, data: Dict) -> Dict:
        """Notify when deadline is approaching"""
        vendor_email = data.get('vendor_email')
        request_title = data.get('request_title')
        deadline = data.get('deadline')
        hours_left = data.get('hours_left')
        
        subject = f"Deadline Mendekat - {request_title}"
        body = f"""
        Halo,
        
        Deadline upload penawaran untuk request "{request_title}" akan berakhir dalam {hours_left} jam.
        Deadline: {deadline}
        
        Silakan segera upload penawaran Anda.
        """
        
        return await self._send_email(vendor_email, subject, body)
    
    async def _notify_deadline_passed(self, data: Dict) -> Dict:
        """Notify when deadline has passed"""
        vendor_email = data.get('vendor_email')
        request_title = data.get('request_title')
        deadline = data.get('deadline')
        
        subject = f"Deadline Terlewat - {request_title}"
        body = f"""
        Halo,
        
        Deadline upload penawaran untuk request "{request_title}" telah terlewat.
        Deadline: {deadline}
        
        Silakan hubungi admin untuk informasi lebih lanjut.
        """
        
        return await self._send_email(vendor_email, subject, body)
    
    async def _notify_penawaran_submitted(self, data: Dict) -> Dict:
        """Notify when penawaran is submitted"""
        admin_emails = data.get('admin_emails', [])
        vendor_name = data.get('vendor_name')
        request_title = data.get('request_title')
        total_price = data.get('total_price')
        
        subject = f"Penawaran Baru - {request_title}"
        body = f"""
        Halo Admin,
        
        Vendor {vendor_name} telah mengirimkan penawaran untuk request "{request_title}".
        Total Harga: Rp {total_price:,}
        
        Silakan review penawaran tersebut.
        """
        
        results = []
        for admin_email in admin_emails:
            result = await self._send_email(admin_email, subject, body)
            results.append(result)
        
        return {'success': True, 'results': results}
    
    async def _notify_admin_upload(self, data: Dict) -> Dict:
        """Notify when admin uploads on behalf of vendor"""
        vendor_email = data.get('vendor_email')
        admin_name = data.get('admin_name')
        request_title = data.get('request_title')
        file_name = data.get('file_name')
        
        subject = f"File Diupload oleh Admin - {request_title}"
        body = f"""
        Halo,
        
        Admin {admin_name} telah mengupload file "{file_name}" untuk request "{request_title}" atas nama Anda.
        
        Silakan review file tersebut.
        """
        
        return await self._send_email(vendor_email, subject, body)
    
    async def _send_email(self, to_email: str, subject: str, body: str) -> Dict:
        """Send email notification"""
        try:
            # This is a placeholder for actual email sending
            # In production, use libraries like smtplib, sendgrid, or aws ses
            
            logger.info(f"📧 Email sent to {to_email}: {subject}")
            
            return {
                'success': True,
                'message': 'Email sent successfully',
                'to': to_email,
                'subject': subject
            }
            
        except Exception as e:
            logger.error(f"❌ Email sending failed: {str(e)}")
            return {'success': False, 'message': str(e)}

class ApprovalIntegration:
    """Handles approval system integration"""
    
    async def handle_event(self, event: str, data: Dict) -> Dict:
        """Handle approval events"""
        try:
            if event == 'penawaran_submitted':
                return await self._create_approval_request(data)
            elif event == 'approval_required':
                return await self._notify_approval_required(data)
            elif event == 'approval_completed':
                return await self._handle_approval_completed(data)
            else:
                return {'success': False, 'message': f'Unknown event: {event}'}
                
        except Exception as e:
            logger.error(f"❌ Approval integration error: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    async def _create_approval_request(self, data: Dict) -> Dict:
        """Create approval request"""
        try:
            approval_data = {
                'type': 'vendor_penawaran',
                'vendor_id': data.get('vendor_id'),
                'request_id': data.get('request_id'),
                'penawaran_id': data.get('penawaran_id'),
                'priority': 'normal',
                'due_date': data.get('due_date'),
                'metadata': {
                    'vendor_name': data.get('vendor_name'),
                    'request_title': data.get('request_title'),
                    'total_price': data.get('total_price'),
                    'delivery_time': data.get('delivery_time')
                }
            }
            
            # This would integrate with actual approval system
            logger.info(f"✅ Approval request created: {approval_data}")
            
            return {
                'success': True,
                'message': 'Approval request created',
                'approval_id': f"APP_{data.get('penawaran_id')}_{int(datetime.now().timestamp())}"
            }
            
        except Exception as e:
            logger.error(f"❌ Approval request creation failed: {str(e)}")
            return {'success': False, 'message': str(e)}

class VendorAnalysisIntegration:
    """Handles vendor analysis system integration"""
    
    async def handle_event(self, event: str, data: Dict) -> Dict:
        """Handle vendor analysis events"""
        try:
            if event == 'penawaran_submitted':
                return await self._analyze_penawaran(data)
            elif event == 'file_uploaded':
                return await self._analyze_file_quality(data)
            elif event == 'deadline_compliance':
                return await self._analyze_deadline_compliance(data)
            else:
                return {'success': False, 'message': f'Unknown event: {event}'}
                
        except Exception as e:
            logger.error(f"❌ Vendor analysis error: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    async def _analyze_penawaran(self, data: Dict) -> Dict:
        """Analyze penawaran data"""
        try:
            analysis_data = {
                'vendor_id': data.get('vendor_id'),
                'penawaran_id': data.get('penawaran_id'),
                'total_price': data.get('total_price'),
                'delivery_time': data.get('delivery_time'),
                'quality_rating': data.get('quality_rating'),
                'payment_terms': data.get('payment_terms'),
                'timestamp': datetime.now().isoformat()
            }
            
            # This would integrate with actual analysis system
            logger.info(f"✅ Penawaran analysis completed: {analysis_data}")
            
            return {
                'success': True,
                'message': 'Penawaran analyzed',
                'analysis_id': f"ANALYSIS_{data.get('penawaran_id')}_{int(datetime.now().timestamp())}"
            }
            
        except Exception as e:
            logger.error(f"❌ Penawaran analysis failed: {str(e)}")
            return {'success': False, 'message': str(e)}

class AuditTrailIntegration:
    """Handles audit trail system integration"""
    
    async def handle_event(self, event: str, data: Dict) -> Dict:
        """Handle audit trail events"""
        try:
            audit_data = {
                'event': event,
                'user_id': data.get('user_id'),
                'user_role': data.get('user_role'),
                'vendor_id': data.get('vendor_id'),
                'request_id': data.get('request_id'),
                'timestamp': datetime.now().isoformat(),
                'ip_address': data.get('ip_address'),
                'user_agent': data.get('user_agent'),
                'metadata': data.get('metadata', {})
            }
            
            # This would integrate with actual audit system
            logger.info(f"✅ Audit trail recorded: {audit_data}")
            
            return {
                'success': True,
                'message': 'Audit trail recorded',
                'audit_id': f"AUDIT_{int(datetime.now().timestamp())}"
            }
            
        except Exception as e:
            logger.error(f"❌ Audit trail error: {str(e)}")
            return {'success': False, 'message': str(e)}

class FileStorageIntegration:
    """Handles file storage system integration"""
    
    async def handle_event(self, event: str, data: Dict) -> Dict:
        """Handle file storage events"""
        try:
            if event == 'file_uploaded':
                return await self._backup_file(data)
            elif event == 'file_deleted':
                return await self._archive_file(data)
            elif event == 'file_downloaded':
                return await self._log_download(data)
            else:
                return {'success': False, 'message': f'Unknown event: {event}'}
                
        except Exception as e:
            logger.error(f"❌ File storage error: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    async def _backup_file(self, data: Dict) -> Dict:
        """Backup file to cloud storage"""
        try:
            # This would integrate with actual cloud storage (AWS S3, Google Cloud, etc.)
            logger.info(f"✅ File backed up: {data.get('file_name')}")
            
            return {
                'success': True,
                'message': 'File backed up',
                'backup_url': f"https://backup.example.com/{data.get('file_id')}"
            }
            
        except Exception as e:
            logger.error(f"❌ File backup failed: {str(e)}")
            return {'success': False, 'message': str(e)}

class AuthenticationIntegration:
    """Handles authentication system integration"""
    
    async def handle_event(self, event: str, data: Dict) -> Dict:
        """Handle authentication events"""
        try:
            if event == 'user_login':
                return await self._log_login(data)
            elif event == 'user_logout':
                return await self._log_logout(data)
            elif event == 'permission_check':
                return await self._check_permissions(data)
            else:
                return {'success': False, 'message': f'Unknown event: {event}'}
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    async def _check_permissions(self, data: Dict) -> Dict:
        """Check user permissions"""
        try:
            user_id = data.get('user_id')
            user_role = data.get('user_role')
            action = data.get('action')
            
            # This would integrate with actual permission system
            permissions = {
                'vendor': ['upload_file', 'view_own_files'],
                'admin': ['upload_file', 'view_all_files', 'delete_file', 'override_deadline'],
                'super_admin': ['upload_file', 'view_all_files', 'delete_file', 'override_deadline', 'manage_users']
            }
            
            user_permissions = permissions.get(user_role, [])
            has_permission = action in user_permissions
            
            return {
                'success': True,
                'has_permission': has_permission,
                'permissions': user_permissions
            }
            
        except Exception as e:
            logger.error(f"❌ Permission check failed: {str(e)}")
            return {'success': False, 'message': str(e)}

# Export singleton instance
integration_manager = IntegrationManager()
