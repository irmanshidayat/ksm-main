#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notification Service - Best Practices Implementation
Sistem notification dengan batching, analytics, dan real-time delivery
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import current_app
from sqlalchemy import and_, or_, func
import json

# Fallback untuk flask_socketio
try:
    from flask_socketio import emit
    SOCKETIO_AVAILABLE = True
except ImportError:
    SOCKETIO_AVAILABLE = False
    # Fallback function untuk emit
    def emit(event, data, room=None):
        """Fallback emit function ketika flask_socketio tidak tersedia"""
        logging.warning(f"⚠️ WebSocket emit fallback: {event} to {room} - {data}")
        pass

logger = logging.getLogger(__name__)

class NotificationService:
    """Service untuk notification dengan best practices"""
    
    def __init__(self, socketio_app=None):
        self.sio = socketio_app
        self.batching_service = NotificationBatchingService()
        self.analytics_service = NotificationAnalyticsService()
    
    def send_notification(self, user_id: int, notification_type: str, 
                         title: str, message: str, data: Dict = None, 
                         priority: str = 'normal', action_required: bool = False) -> Dict:
        """Send notification dengan best practices"""
        try:
            # Create notification data
            notification_data = {
                'type': notification_type,
                'title': title,
                'message': message,
                'data': data or {},
                'priority': priority,
                'action_required': action_required,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Check if should batch
            if self.batching_service.should_batch_notification(user_id, notification_type, notification_data):
                # Add to batch
                batch_item = self.batching_service.add_to_batch(user_id, notification_type, notification_data)
                return {
                    'status': 'batched',
                    'batch_id': batch_item.batch_id,
                    'notification_id': None
                }
            else:
                # Send immediately
                return self._send_immediate_notification(user_id, notification_data)
                
        except Exception as e:
            logger.error(f"❌ Error sending notification: {str(e)}")
            raise
    
    def _send_immediate_notification(self, user_id: int, notification_data: Dict) -> Dict:
        """Send notification immediately"""
        try:
            from models.notification_models import Notification, db
            
            # Create notification record
            notification = Notification(
                user_id=user_id,
                type=notification_data['type'],
                title=notification_data['title'],
                message=notification_data['message'],
                data=notification_data['data'],
                priority=notification_data['priority'],
                action_required=notification_data['action_required'],
                is_sent=True,
                sent_at=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()
            
            # Send via WebSocket
            if self.sio and SOCKETIO_AVAILABLE:
                emit('notification', notification_data, room=f'user_{user_id}')
            elif not SOCKETIO_AVAILABLE:
                logger.warning("⚠️ WebSocket tidak tersedia, notification tidak dikirim via real-time")
            
            # Track analytics
            self.analytics_service.track_notification_sent(
                notification.id, user_id, notification_data['type']
            )
            
            logger.info(f"✅ Sent notification to user {user_id}")
            
            return {
                'status': 'sent',
                'notification_id': notification.id,
                'sent_at': notification.sent_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error sending immediate notification: {str(e)}")
            raise
    
    def send_approval_notification(self, approver_id: int, approval_request) -> Dict:
        """Send approval notification"""
        try:
            notification_data = {
                'type': 'approval_request',
                'title': 'Approval Request',
                'message': f'New approval request from {approval_request.requester.username}',
                'data': {
                    'request_id': approval_request.id,
                    'module': approval_request.module,
                    'action_type': approval_request.action_type,
                    'requester_name': approval_request.requester.username,
                    'department': approval_request.requester.department.name if approval_request.requester.department else None
                },
                'priority': 'high',
                'action_required': True
            }
            
            return self.send_notification(
                approver_id, 
                'approval_request',
                notification_data['title'],
                notification_data['message'],
                notification_data['data'],
                notification_data['priority'],
                notification_data['action_required']
            )
            
        except Exception as e:
            logger.error(f"❌ Error sending approval notification: {str(e)}")
            raise
    
    def send_escalation_notification(self, user_id: int, approval_request, escalation_log) -> Dict:
        """Send escalation notification"""
        try:
            notification_data = {
                'type': 'escalation',
                'title': 'Approval Escalated',
                'message': f'Approval request escalated to you',
                'data': {
                    'request_id': approval_request.id,
                    'escalation_level': escalation_log.escalation_level,
                    'original_requester': approval_request.requester.username,
                    'escalation_reason': escalation_log.escalation_reason
                },
                'priority': 'urgent',
                'action_required': True
            }
            
            return self.send_notification(
                user_id,
                'escalation',
                notification_data['title'],
                notification_data['message'],
                notification_data['data'],
                notification_data['priority'],
                notification_data['action_required']
            )
            
        except Exception as e:
            logger.error(f"❌ Error sending escalation notification: {str(e)}")
            raise
    
    def send_approval_status_notification(self, requester_id: int, approval_request, status: str) -> Dict:
        """Send approval status notification"""
        try:
            notification_data = {
                'type': 'approval_status',
                'title': f'Approval {status.title()}',
                'message': f'Your approval request has been {status}',
                'data': {
                    'request_id': approval_request.id,
                    'status': status,
                    'module': approval_request.module,
                    'action_type': approval_request.action_type
                },
                'priority': 'normal',
                'action_required': False
            }
            
            return self.send_notification(
                requester_id,
                'approval_status',
                notification_data['title'],
                notification_data['message'],
                notification_data['data'],
                notification_data['priority'],
                notification_data['action_required']
            )
            
        except Exception as e:
            logger.error(f"❌ Error sending approval status notification: {str(e)}")
            raise
    
    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        try:
            from models.notification_models import Notification, db
            
            notification = Notification.query.filter_by(
                id=notification_id,
                user_id=user_id
            ).first()
            
            if notification:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
                db.session.commit()
                
                # Track analytics
                self.analytics_service.track_notification_read(notification_id)
                
                logger.info(f"✅ Marked notification {notification_id} as read")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error marking notification as read: {str(e)}")
            return False
    
    def get_user_notifications(self, user_id: int, limit: int = 50, unread_only: bool = False) -> List[Dict]:
        """Get user notifications"""
        try:
            from models.notification_models import Notification
            
            query = Notification.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(is_read=False)
            
            notifications = query.order_by(
                Notification.created_at.desc()
            ).limit(limit).all()
            
            return [n.to_dict() for n in notifications]
            
        except Exception as e:
            logger.error(f"❌ Error getting user notifications: {str(e)}")
            return []
    
    def get_unread_count(self, user_id: int) -> int:
        """Get unread notification count"""
        try:
            from models.notification_models import Notification
            
            count = Notification.query.filter_by(
                user_id=user_id,
                is_read=False
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Error getting unread count: {str(e)}")
            return 0

class NotificationBatchingService:
    """Service untuk notification batching dengan best practices"""
    
    def __init__(self):
        self.batching_rules = self._load_batching_rules()
    
    def _load_batching_rules(self) -> Dict:
        """Load batching rules"""
        return {
            'approval_request': {
                'batch_window_minutes': 15,
                'max_items_per_batch': 10,
                'consolidation_method': 'count_summary',
                'batch_enabled': True,
                'priority_override': ['urgent', 'high'],
                'user_activity_override': True
            },
            'escalation': {
                'batch_window_minutes': 5,
                'max_items_per_batch': 5,
                'consolidation_method': 'priority_list',
                'batch_enabled': False,  # Escalation tidak di-batch
                'priority_override': ['urgent', 'high', 'normal'],
                'user_activity_override': False
            },
            'status_update': {
                'batch_window_minutes': 30,
                'max_items_per_batch': 20,
                'consolidation_method': 'category_summary',
                'batch_enabled': True,
                'priority_override': ['urgent'],
                'user_activity_override': True
            },
            'system_alert': {
                'batch_window_minutes': 60,
                'max_items_per_batch': 50,
                'consolidation_method': 'severity_grouping',
                'batch_enabled': True,
                'priority_override': ['critical'],
                'user_activity_override': False
            }
        }
    
    def should_batch_notification(self, user_id: int, notification_type: str, 
                                notification_data: Dict) -> bool:
        """Determine apakah notification harus di-batch"""
        try:
            # Get batching rules
            rules = self.batching_rules.get(notification_type, {})
            
            if not rules.get('batch_enabled', True):
                return False
            
            # Check priority override
            priority = notification_data.get('priority', 'normal')
            if priority in rules.get('priority_override', []):
                return False
            
            # Check user activity
            if rules.get('user_activity_override', True):
                if self._is_user_active(user_id):
                    return False
            
            # Check user preferences
            if self._user_prefers_immediate(user_id, notification_type):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error checking batching rules: {str(e)}")
            return False
    
    def _is_user_active(self, user_id: int) -> bool:
        """Check apakah user sedang aktif"""
        try:
            from models.notification_models import UserActivity
            
            last_activity = UserActivity.query.filter_by(
                user_id=user_id
            ).order_by(UserActivity.timestamp.desc()).first()
            
            if last_activity:
                time_diff = datetime.utcnow() - last_activity.timestamp
                return time_diff.total_seconds() < 300  # 5 menit
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking user activity: {str(e)}")
            return False
    
    def _user_prefers_immediate(self, user_id: int, notification_type: str) -> bool:
        """Check user preferences untuk immediate notification"""
        try:
            from models.notification_models import NotificationPreference
            
            preference = NotificationPreference.query.filter_by(
                user_id=user_id,
                notification_type=notification_type
            ).first()
            
            if preference:
                return not preference.batch_enabled
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking user preferences: {str(e)}")
            return False
    
    def add_to_batch(self, user_id: int, notification_type: str, notification_data: Dict):
        """Add notification ke batch"""
        try:
            from models.notification_models import NotificationBatch, NotificationBatchItem, db
            
            # Get or create batch
            batch = self._get_or_create_batch(user_id, notification_type)
            
            # Add notification to batch
            batch_item = NotificationBatchItem(
                batch_id=batch.id,
                notification_data=notification_data,
                created_at=datetime.utcnow()
            )
            db.session.add(batch_item)
            
            # Update batch item count
            batch.item_count += 1
            db.session.commit()
            
            logger.info(f"✅ Added notification to batch {batch.id}")
            
            return batch_item
            
        except Exception as e:
            logger.error(f"❌ Error adding to batch: {str(e)}")
            raise
    
    def _get_or_create_batch(self, user_id: int, notification_type: str):
        """Get or create notification batch"""
        try:
            from models.notification_models import NotificationBatch, db
            
            # Check for existing active batch
            batch = NotificationBatch.query.filter_by(
                user_id=user_id,
                notification_type=notification_type,
                status='collecting'
            ).first()
            
            if batch:
                return batch
            
            # Create new batch
            rules = self.batching_rules.get(notification_type, {})
            batch_window = rules.get('batch_window_minutes', 15)
            
            batch = NotificationBatch(
                user_id=user_id,
                notification_type=notification_type,
                batch_window_minutes=batch_window,
                status='collecting',
                item_count=0
            )
            db.session.add(batch)
            db.session.commit()
            
            return batch
            
        except Exception as e:
            logger.error(f"❌ Error creating batch: {str(e)}")
            raise
    
    def process_batches(self):
        """Process notification batches yang sudah selesai"""
        try:
            from models.notification_models import NotificationBatch, db
            
            current_time = datetime.utcnow()
            
            # Get batches yang sudah selesai collecting
            completed_batches = NotificationBatch.query.filter(
                NotificationBatch.status == 'collecting',
                NotificationBatch.created_at <= current_time - timedelta(
                    minutes=NotificationBatch.batch_window_minutes
                )
            ).all()
            
            for batch in completed_batches:
                self._send_batch_notification(batch)
            
            logger.info(f"✅ Processed {len(completed_batches)} notification batches")
            
        except Exception as e:
            logger.error(f"❌ Error processing batches: {str(e)}")
    
    def _send_batch_notification(self, batch):
        """Send batched notification"""
        try:
            from models.notification_models import NotificationBatchItem, Notification, db
            
            # Get all items in batch
            batch_items = NotificationBatchItem.query.filter_by(
                batch_id=batch.id
            ).all()
            
            if not batch_items:
                batch.status = 'completed'
                db.session.commit()
                return
            
            # Create consolidated notification
            consolidated_data = self._create_consolidated_notification(batch, batch_items)
            
            # Send consolidated notification
            if current_app.socketio and SOCKETIO_AVAILABLE:
                emit('notification', consolidated_data, room=f'user_{batch.user_id}')
            elif not SOCKETIO_AVAILABLE:
                logger.warning("⚠️ WebSocket tidak tersedia, batch notification tidak dikirim via real-time")
            
            # Create notification record
            notification = Notification(
                user_id=batch.user_id,
                type=f"{batch.notification_type}_batch",
                title=consolidated_data['title'],
                message=consolidated_data['message'],
                data=consolidated_data['data'],
                is_sent=True,
                sent_at=datetime.utcnow()
            )
            db.session.add(notification)
            
            # Mark batch as sent
            batch.status = 'sent'
            batch.sent_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"✅ Sent batch notification for batch {batch.id}")
            
        except Exception as e:
            logger.error(f"❌ Error sending batch notification: {str(e)}")
    
    def _create_consolidated_notification(self, batch, batch_items):
        """Create consolidated notification data"""
        try:
            rules = self.batching_rules.get(batch.notification_type, {})
            consolidation_method = rules.get('consolidation_method', 'count_summary')
            
            if consolidation_method == 'count_summary':
                return {
                    'type': f"{batch.notification_type}_batch",
                    'title': f"You have {len(batch_items)} {batch.notification_type} notifications",
                    'message': f"Click to view all {len(batch_items)} notifications",
                    'data': {
                        'batch_id': batch.id,
                        'item_count': len(batch_items),
                        'items': [item.notification_data for item in batch_items]
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
            elif consolidation_method == 'priority_list':
                # Group by priority
                priority_groups = {}
                for item in batch_items:
                    priority = item.notification_data.get('priority', 'normal')
                    if priority not in priority_groups:
                        priority_groups[priority] = []
                    priority_groups[priority].append(item.notification_data)
                
                return {
                    'type': f"{batch.notification_type}_batch",
                    'title': f"Priority notifications: {len(batch_items)} items",
                    'message': f"High priority: {len(priority_groups.get('high', []))}, Normal: {len(priority_groups.get('normal', []))}",
                    'data': {
                        'batch_id': batch.id,
                        'priority_groups': priority_groups,
                        'total_count': len(batch_items)
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                # Default consolidation
                return {
                    'type': f"{batch.notification_type}_batch",
                    'title': f"You have {len(batch_items)} notifications",
                    'message': f"Click to view all notifications",
                    'data': {
                        'batch_id': batch.id,
                        'items': [item.notification_data for item in batch_items]
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error creating consolidated notification: {str(e)}")
            raise

class NotificationAnalyticsService:
    """Service untuk notification analytics dengan best practices"""
    
    def track_notification_sent(self, notification_id: int, user_id: int, notification_type: str):
        """Track notification sent"""
        try:
            from models.notification_models import NotificationAnalytics, db
            
            analytics = NotificationAnalytics(
                notification_id=notification_id,
                user_id=user_id,
                notification_type=notification_type,
                sent_at=datetime.utcnow(),
                delivery_status='sent'
            )
            db.session.add(analytics)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"❌ Error tracking notification sent: {str(e)}")
    
    def track_notification_read(self, notification_id: int):
        """Track notification read"""
        try:
            from models.notification_models import NotificationAnalytics, db
            
            analytics = NotificationAnalytics.query.filter_by(
                notification_id=notification_id
            ).first()
            
            if analytics:
                analytics.read_at = datetime.utcnow()
                analytics.read_status = 'read'
                if analytics.sent_at:
                    analytics.read_time_seconds = int(
                        (analytics.read_at - analytics.sent_at).total_seconds()
                    )
                db.session.commit()
            
        except Exception as e:
            logger.error(f"❌ Error tracking notification read: {str(e)}")
    
    def track_notification_clicked(self, notification_id: int):
        """Track notification clicked"""
        try:
            from models.notification_models import NotificationAnalytics, db
            
            analytics = NotificationAnalytics.query.filter_by(
                notification_id=notification_id
            ).first()
            
            if analytics:
                analytics.clicked_at = datetime.utcnow()
                analytics.action_status = 'clicked'
                if analytics.sent_at:
                    analytics.response_time_seconds = int(
                        (analytics.clicked_at - analytics.sent_at).total_seconds()
                    )
                db.session.commit()
            
        except Exception as e:
            logger.error(f"❌ Error tracking notification clicked: {str(e)}")
    
    def get_notification_metrics(self, date_from: datetime, date_to: datetime, 
                               department_id: int = None) -> Dict:
        """Get notification metrics"""
        try:
            from models.notification_models import NotificationAnalytics
            
            query = NotificationAnalytics.query.filter(
                NotificationAnalytics.sent_at >= date_from,
                NotificationAnalytics.sent_at <= date_to
            )
            
            if department_id:
                query = query.filter_by(department_id=department_id)
            
            # Get aggregated metrics
            metrics = query.with_entities(
                NotificationAnalytics.notification_type,
                func.count(NotificationAnalytics.id).label('total_sent'),
                func.count(NotificationAnalytics.read_at).label('total_read'),
                func.count(NotificationAnalytics.clicked_at).label('total_clicked'),
                func.avg(NotificationAnalytics.read_time_seconds).label('avg_read_time'),
                func.avg(NotificationAnalytics.response_time_seconds).label('avg_response_time')
            ).group_by(NotificationAnalytics.notification_type).all()
            
            result = []
            for metric in metrics:
                result.append({
                    'notification_type': metric.notification_type,
                    'total_sent': metric.total_sent,
                    'total_read': metric.total_read,
                    'total_clicked': metric.total_clicked,
                    'read_rate': (metric.total_read / metric.total_sent * 100) if metric.total_sent > 0 else 0,
                    'click_rate': (metric.total_clicked / metric.total_sent * 100) if metric.total_sent > 0 else 0,
                    'avg_read_time': float(metric.avg_read_time) if metric.avg_read_time else 0,
                    'avg_response_time': float(metric.avg_response_time) if metric.avg_response_time else 0
                })
            
            return {
                'metrics': result,
                'summary': {
                    'total_notifications': sum(m['total_sent'] for m in result),
                    'avg_read_rate': sum(m['read_rate'] for m in result) / len(result) if result else 0,
                    'avg_click_rate': sum(m['click_rate'] for m in result) / len(result) if result else 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting notification metrics: {str(e)}")
            return {'metrics': [], 'summary': {}}
