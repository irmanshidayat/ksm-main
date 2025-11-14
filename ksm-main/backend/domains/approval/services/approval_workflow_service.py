#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Approval Workflow Service - Best Practices Implementation
Sistem approval workflow dengan escalation policy dan automation
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import current_app
from sqlalchemy import and_, or_, func
import json

logger = logging.getLogger(__name__)

class ApprovalWorkflowService:
    """Service untuk approval workflow dengan best practices"""
    
    def __init__(self):
        self.escalation_service = EscalationService()
        self.notification_service = None  # Will be injected
    
    def create_approval_request(self, requester_id: int, module: str, action_type: str,
                              resource_data: Dict, workflow_name: str = None) -> Dict:
        """Create approval request dengan best practices"""
        try:
            from domains.approval.models.approval_models import ApprovalRequest, ApprovalWorkflow
            from config.database import db
            
            # Get workflow
            if workflow_name:
                workflow = ApprovalWorkflow.query.filter_by(
                    name=workflow_name,
                    is_active=True
                ).first()
            else:
                workflow = ApprovalWorkflow.query.filter_by(
                    module=module,
                    action_type=action_type,
                    is_active=True
                ).first()
            
            if not workflow:
                raise Exception(f"No workflow found for {module}/{action_type}")
            
            # Create approval request
            approval_request = ApprovalRequest(
                workflow_id=workflow.id,
                requester_id=requester_id,
                module=module,
                action_type=action_type,
                resource_data=resource_data,
                status='pending',
                current_step=1
            )
            db.session.add(approval_request)
            db.session.commit()
            
            # Start approval process
            self._start_approval_process(approval_request)
            
            logger.info(f"✅ Created approval request {approval_request.id}")
            
            return {
                'request_id': approval_request.id,
                'workflow_id': workflow.id,
                'status': 'pending',
                'current_step': 1,
                'created_at': approval_request.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating approval request: {str(e)}")
            raise
    
    def _start_approval_process(self, approval_request):
        """Start approval process"""
        try:
            from domains.approval.models.approval_models import ApprovalStep
            from config.database import db
            
            # Get first step
            first_step = ApprovalStep.query.filter_by(
                workflow_id=approval_request.workflow_id,
                step_order=1
            ).first()
            
            if not first_step:
                raise Exception("No first step found in workflow")
            
            # Get approvers for first step
            approvers = self._get_approvers_for_step(first_step)
            
            if not approvers:
                raise Exception("No approvers found for first step")
            
            # Send notifications to approvers
            for approver in approvers:
                if self.notification_service:
                    self.notification_service.send_approval_notification(
                        approver.id, approval_request
                    )
            
            # Set timeout for first step
            if first_step.timeout_hours:
                approval_request.timeout_at = datetime.utcnow() + timedelta(
                    hours=first_step.timeout_hours
                )
                db.session.commit()
            
            logger.info(f"✅ Started approval process for request {approval_request.id}")
            
        except Exception as e:
            logger.error(f"❌ Error starting approval process: {str(e)}")
            raise
    
    def _get_approvers_for_step(self, step) -> List:
        """Get approvers for approval step"""
        try:
            from domains.auth.models.auth_models import User
            from domains.role.models.role_models import UserRole, Role, Department
            
            approvers = []
            
            if step.approver_role_id:
                # Get users with specific role
                role_users = User.query.join(UserRole).join(Role).filter(
                    Role.id == step.approver_role_id,
                    UserRole.is_active == True,
                    User.is_active == True
                ).all()
                approvers.extend(role_users)
            
            if step.approver_department_id:
                # Get users from specific department
                dept_users = User.query.filter(
                    User.department_id == step.approver_department_id,
                    User.is_active == True
                ).all()
                approvers.extend(dept_users)
            
            # Remove duplicates
            approvers = list(set(approvers))
            
            return approvers
            
        except Exception as e:
            logger.error(f"❌ Error getting approvers: {str(e)}")
            return []
    
    def process_approval(self, request_id: int, approver_id: int, action: str, 
                        comment: str = None) -> Dict:
        """Process approval action"""
        try:
            from domains.approval.models.approval_models import ApprovalRequest, ApprovalAction, ApprovalStep
            from config.database import db
            
            # Get approval request
            approval_request = ApprovalRequest.query.get(request_id)
            if not approval_request:
                raise Exception("Approval request not found")
            
            if approval_request.status != 'pending':
                raise Exception("Approval request is not pending")
            
            # Get current step
            current_step = ApprovalStep.query.filter_by(
                workflow_id=approval_request.workflow_id,
                step_order=approval_request.current_step
            ).first()
            
            if not current_step:
                raise Exception("Current step not found")
            
            # Check if user can approve this step
            if not self._can_user_approve_step(approver_id, current_step):
                raise Exception("User cannot approve this step")
            
            # Create approval action
            approval_action = ApprovalAction(
                request_id=request_id,
                step_id=current_step.id,
                approver_id=approver_id,
                action=action,
                comment=comment,
                timestamp=datetime.utcnow()
            )
            db.session.add(approval_action)
            
            # Process based on action
            if action == 'approve':
                result = self._process_approval(approval_request, current_step)
            elif action == 'reject':
                result = self._process_rejection(approval_request, comment)
            elif action == 'delegate':
                result = self._process_delegation(approval_request, current_step, approver_id, comment)
            else:
                raise Exception("Invalid action")
            
            db.session.commit()
            
            # Send notifications
            if self.notification_service:
                if action == 'approve':
                    self.notification_service.send_approval_status_notification(
                        approval_request.requester_id, approval_request, 'approved'
                    )
                elif action == 'reject':
                    self.notification_service.send_approval_status_notification(
                        approval_request.requester_id, approval_request, 'rejected'
                    )
            
            logger.info(f"✅ Processed approval action {action} for request {request_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing approval: {str(e)}")
            raise
    
    def _can_user_approve_step(self, user_id: int, step) -> bool:
        """Check if user can approve step"""
        try:
            from models import User
            from models import UserRole, Role
            
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return False
            
            # Check role-based approval
            if step.approver_role_id:
                user_roles = UserRole.query.filter_by(
                    user_id=user_id,
                    is_active=True
                ).all()
                
                for user_role in user_roles:
                    if user_role.role_id == step.approver_role_id:
                        return True
            
            # Check department-based approval
            if step.approver_department_id:
                if user.department_id == step.approver_department_id:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking user approval permission: {str(e)}")
            return False
    
    def _process_approval(self, approval_request, current_step) -> Dict:
        """Process approval action"""
        try:
            from domains.approval.models.approval_models import ApprovalStep
            from config.database import db
            
            # Check if this is the last step
            next_step = ApprovalStep.query.filter_by(
                workflow_id=approval_request.workflow_id,
                step_order=approval_request.current_step + 1
            ).first()
            
            if not next_step:
                # This is the last step, approve the request
                approval_request.status = 'approved'
                approval_request.completed_at = datetime.utcnow()
                
                # Execute the approved action
                self._execute_approved_action(approval_request)
                
                return {
                    'status': 'approved',
                    'message': 'Request approved and executed'
                }
            else:
                # Move to next step
                approval_request.current_step += 1
                
                # Get approvers for next step
                approvers = self._get_approvers_for_step(next_step)
                
                # Send notifications to next approvers
                for approver in approvers:
                    if self.notification_service:
                        self.notification_service.send_approval_notification(
                            approver.id, approval_request
                        )
                
                # Set timeout for next step
                if next_step.timeout_hours:
                    approval_request.timeout_at = datetime.utcnow() + timedelta(
                        hours=next_step.timeout_hours
                    )
                
                return {
                    'status': 'moved_to_next_step',
                    'current_step': approval_request.current_step,
                    'message': 'Moved to next approval step'
                }
                
        except Exception as e:
            logger.error(f"❌ Error processing approval: {str(e)}")
            raise
    
    def _process_rejection(self, approval_request, comment) -> Dict:
        """Process rejection action"""
        try:
            approval_request.status = 'rejected'
            approval_request.completed_at = datetime.utcnow()
            approval_request.rejection_reason = comment
            
            return {
                'status': 'rejected',
                'message': 'Request rejected'
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing rejection: {str(e)}")
            raise
    
    def _process_delegation(self, approval_request, current_step, approver_id, comment) -> Dict:
        """Process delegation action"""
        try:
            # For now, delegation is treated as rejection
            # In a more complex system, this would create a new approval request
            approval_request.status = 'delegated'
            approval_request.completed_at = datetime.utcnow()
            approval_request.delegation_reason = comment
            
            return {
                'status': 'delegated',
                'message': 'Request delegated'
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing delegation: {str(e)}")
            raise
    
    def _execute_approved_action(self, approval_request):
        """Execute the approved action"""
        try:
            # This is where the actual business logic would be executed
            # based on the module and action_type
            
            if approval_request.module == 'user_management':
                if approval_request.action_type == 'create_user':
                    self._execute_create_user(approval_request.resource_data)
                elif approval_request.action_type == 'update_user':
                    self._execute_update_user(approval_request.resource_data)
                elif approval_request.action_type == 'delete_user':
                    self._execute_delete_user(approval_request.resource_data)
            
            elif approval_request.module == 'finance':
                if approval_request.action_type == 'approve_expense':
                    self._execute_approve_expense(approval_request.resource_data)
                elif approval_request.action_type == 'approve_budget':
                    self._execute_approve_budget(approval_request.resource_data)
            
            # Add more modules and actions as needed
            
            logger.info(f"✅ Executed approved action for request {approval_request.id}")
            
        except Exception as e:
            logger.error(f"❌ Error executing approved action: {str(e)}")
            raise
    
    def _execute_create_user(self, resource_data):
        """Execute create user action"""
        # Implementation for creating user
        pass
    
    def _execute_update_user(self, resource_data):
        """Execute update user action"""
        # Implementation for updating user
        pass
    
    def _execute_delete_user(self, resource_data):
        """Execute delete user action"""
        # Implementation for deleting user
        pass
    
    def _execute_approve_expense(self, resource_data):
        """Execute approve expense action"""
        # Implementation for approving expense
        pass
    
    def _execute_approve_budget(self, resource_data):
        """Execute approve budget action"""
        # Implementation for approving budget
        pass
    
    def get_approval_requests(self, user_id: int = None, status: str = None, 
                            module: str = None) -> List[Dict]:
        """Get approval requests"""
        try:
            from domains.approval.models.approval_models import ApprovalRequest
            
            query = ApprovalRequest.query
            
            if user_id:
                query = query.filter_by(requester_id=user_id)
            
            if status:
                query = query.filter_by(status=status)
            
            if module:
                query = query.filter_by(module=module)
            
            requests = query.order_by(ApprovalRequest.created_at.desc()).all()
            
            return [r.to_dict() for r in requests]
            
        except Exception as e:
            logger.error(f"❌ Error getting approval requests: {str(e)}")
            return []
    
    def get_pending_approvals_for_user(self, user_id: int) -> List[Dict]:
        """Get pending approvals for user"""
        try:
            from domains.approval.models.approval_models import ApprovalRequest, ApprovalStep
            from models import User
            from models import UserRole, Role
            
            # Get user's roles and department
            user = User.query.get(user_id)
            if not user:
                return []
            
            user_roles = UserRole.query.filter_by(
                user_id=user_id,
                is_active=True
            ).all()
            
            role_ids = [ur.role_id for ur in user_roles]
            
            # Get pending requests where user can approve
            pending_requests = []
            
            for request in ApprovalRequest.query.filter_by(status='pending').all():
                current_step = ApprovalStep.query.filter_by(
                    workflow_id=request.workflow_id,
                    step_order=request.current_step
                ).first()
                
                if current_step and self._can_user_approve_step(user_id, current_step):
                    pending_requests.append(request.to_dict())
            
            return pending_requests
            
        except Exception as e:
            logger.error(f"❌ Error getting pending approvals: {str(e)}")
            return []

class EscalationService:
    """Service untuk escalation dengan best practices"""
    
    def __init__(self):
        self.escalation_rules = self._load_escalation_rules()
    
    def _load_escalation_rules(self) -> Dict:
        """Load escalation rules"""
        return {
            'timeout_escalation': {
                'level_1': {
                    'after_hours': 24,
                    'escalate_to': 'supervisor',
                    'notification_method': ['email', 'system']
                },
                'level_2': {
                    'after_hours': 48,
                    'escalate_to': 'department_manager',
                    'notification_method': ['email', 'sms', 'system']
                },
                'level_3': {
                    'after_hours': 72,
                    'escalate_to': 'admin',
                    'notification_method': ['email', 'sms', 'system', 'phone']
                }
            },
            'rejection_escalation': {
                'level_1': {
                    'escalate_to': 'department_manager',
                    'notification_method': ['email', 'system']
                },
                'level_2': {
                    'escalate_to': 'admin',
                    'notification_method': ['email', 'sms', 'system']
                }
            }
        }
    
    def check_timeout_escalations(self):
        """Check dan execute timeout escalations"""
        try:
            from domains.approval.models.approval_models import ApprovalRequest, EscalationLog
            from config.database import db
            
            current_time = datetime.utcnow()
            
            # Get pending approvals yang sudah timeout
            timeout_approvals = ApprovalRequest.query.filter(
                ApprovalRequest.status == 'pending',
                ApprovalRequest.timeout_at <= current_time
            ).all()
            
            for approval in timeout_approvals:
                self.escalate_approval(approval.id, 'timeout')
            
            logger.info(f"✅ Checked timeout escalations for {len(timeout_approvals)} requests")
            
        except Exception as e:
            logger.error(f"❌ Error checking timeout escalations: {str(e)}")
    
    def escalate_approval(self, approval_id: int, escalation_reason: str):
        """Escalate approval ke level berikutnya"""
        try:
            from domains.approval.models.approval_models import ApprovalRequest, EscalationLog, ApprovalStep
            from config.database import db
            from models import User
            from models import UserRole, Role
            
            # Get approval request
            approval_request = ApprovalRequest.query.get(approval_id)
            if not approval_request:
                raise Exception("Approval request not found")
            
            # Get current step
            current_step = ApprovalStep.query.filter_by(
                workflow_id=approval_request.workflow_id,
                step_order=approval_request.current_step
            ).first()
            
            if not current_step:
                raise Exception("Current step not found")
            
            # Get escalation policy
            escalation_policy = self._get_escalation_policy(current_step, escalation_reason)
            
            if not escalation_policy:
                logger.warning(f"No escalation policy found for step {current_step.id}")
                return
            
            # Get next approver
            next_approver = self._get_next_approver(approval_request, escalation_policy)
            
            if next_approver:
                # Create escalation log
                escalation_log = EscalationLog(
                    request_id=approval_request.id,
                    step_id=current_step.id,
                    escalated_from_user_id=approval_request.requester_id,
                    escalated_to_user_id=next_approver.id,
                    escalation_reason=escalation_reason,
                    escalation_level=escalation_policy.get('level', 1),
                    status='pending'
                )
                db.session.add(escalation_log)
                
                # Update approval request
                approval_request.current_step += 1
                approval_request.timeout_at = datetime.utcnow() + timedelta(hours=24)
                
                db.session.commit()
                
                # Send notification
                if hasattr(self, 'notification_service') and self.notification_service:
                    self.notification_service.send_escalation_notification(
                        next_approver.id, approval_request, escalation_log
                    )
                
                logger.info(f"✅ Escalated approval {approval_id} to user {next_approver.id}")
            else:
                logger.warning(f"No next approver found for escalation of approval {approval_id}")
                
        except Exception as e:
            logger.error(f"❌ Error escalating approval: {str(e)}")
    
    def _get_escalation_policy(self, step, escalation_reason: str) -> Dict:
        """Get escalation policy untuk step"""
        try:
            if escalation_reason == 'timeout':
                return self.escalation_rules['timeout_escalation']['level_1']
            elif escalation_reason == 'rejection':
                return self.escalation_rules['rejection_escalation']['level_1']
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting escalation policy: {str(e)}")
            return None
    
    def _get_next_approver(self, approval_request, escalation_policy) -> Optional:
        """Get next approver untuk escalation"""
        try:
            from models import User
            from models import UserRole, Role
            
            escalate_to = escalation_policy.get('escalate_to')
            
            if escalate_to == 'supervisor':
                # Get supervisor role users
                supervisor_role = Role.query.filter_by(name='supervisor').first()
                if supervisor_role:
                    return User.query.join(UserRole).filter(
                        UserRole.role_id == supervisor_role.id,
                        UserRole.is_active == True,
                        User.is_active == True
                    ).first()
            
            elif escalate_to == 'department_manager':
                # Get department manager
                dept_manager_role = Role.query.filter_by(name='department_manager').first()
                if dept_manager_role:
                    return User.query.join(UserRole).filter(
                        UserRole.role_id == dept_manager_role.id,
                        UserRole.is_active == True,
                        User.is_active == True
                    ).first()
            
            elif escalate_to == 'admin':
                # Get admin user
                admin_role = Role.query.filter_by(name='admin').first()
                if admin_role:
                    return User.query.join(UserRole).filter(
                        UserRole.role_id == admin_role.id,
                        UserRole.is_active == True,
                        User.is_active == True
                    ).first()
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting next approver: {str(e)}")
            return None
