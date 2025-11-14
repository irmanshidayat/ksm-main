#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Workflow Service - Best Practices Implementation
Service untuk mengelola approval workflow system
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from config.database import db
from models import (
    WorkflowTemplate, WorkflowInstance, Department, Role, UserRole
)

logger = logging.getLogger(__name__)

class WorkflowService:
    """Service untuk mengelola workflow system"""
    
    def __init__(self):
        # Don't initialize workflows automatically
        # This will be called manually within application context
        pass
    
    def initialize_default_workflows(self):
        """Initialize default workflow templates - must be called within app context"""
        try:
            # Check if workflows already exist
            if WorkflowTemplate.query.count() > 0:
                logger.info("[INFO] Default workflows already exist, skipping initialization")
                return
            
            logger.info("[INIT] Initializing default workflow templates...")
            
            # Default role assignment workflow
            role_assignment_workflow = {
                'name': 'Role Assignment Approval',
                'description': 'Default workflow for role assignments',
                'steps': [
                    {
                        'step': 1,
                        'name': 'Direct Supervisor Approval',
                        'approver_type': 'direct_supervisor',
                        'required': True,
                        'timeout_hours': 24
                    },
                    {
                        'step': 2,
                        'name': 'Department Head Approval',
                        'approver_type': 'department_head',
                        'required': True,
                        'timeout_hours': 48
                    }
                ]
            }
            
            # Default permission request workflow
            permission_request_workflow = {
                'name': 'Permission Request Approval',
                'description': 'Default workflow for permission requests',
                'steps': [
                    {
                        'step': 1,
                        'name': 'IT Manager Approval',
                        'approver_type': 'it_manager',
                        'required': True,
                        'timeout_hours': 24
                    },
                    {
                        'step': 2,
                        'name': 'Security Team Review',
                        'approver_type': 'security_team',
                        'required': False,
                        'timeout_hours': 72
                    }
                ]
            }
            
            # Create system workflows
            workflows = [
                {
                    'name': role_assignment_workflow['name'],
                    'description': role_assignment_workflow['description'],
                    'steps': role_assignment_workflow['steps'],
                    'is_system_template': True
                },
                {
                    'name': permission_request_workflow['name'],
                    'description': permission_request_workflow['description'],
                    'steps': permission_request_workflow['steps'],
                    'is_system_template': True
                }
            ]
            
            for workflow_data in workflows:
                workflow = WorkflowTemplate(
                    name=workflow_data['name'],
                    description=workflow_data['description'],
                    steps=workflow_data['steps'],
                    is_system_template=workflow_data['is_system_template']
                )
                db.session.add(workflow)
            
            db.session.commit()
            logger.info("[SUCCESS] Default workflow templates initialized successfully")
            
        except Exception as e:
            logger.error(f"[ERROR] Error initializing default workflows: {e}")
            db.session.rollback()
            raise
    
    def create_workflow_template(self, name: str, description: str, 
                               steps: List[Dict], department_id: int = None,
                               created_by: int = None) -> Optional[WorkflowTemplate]:
        """Create new workflow template"""
        try:
            workflow = WorkflowTemplate(
                name=name,
                description=description,
                steps=steps,
                department_id=department_id,
                created_by=created_by,
                is_system_template=False
            )
            
            db.session.add(workflow)
            db.session.commit()
            
            return workflow
            
        except Exception as e:
            logger.error(f"[ERROR] Error creating workflow template: {e}")
            db.session.rollback()
            return None
    
    def start_workflow(self, template_id: int, requester_id: int, 
                      resource_type: str, resource_id: int = None,
                      data: Dict = None) -> Optional[WorkflowInstance]:
        """Start new workflow instance"""
        try:
            template = WorkflowTemplate.query.get(template_id)
            if not template:
                return None
            
            # Determine approvers for each step
            approvers = self.determine_approvers(template, requester_id, data)
            
            workflow_instance = WorkflowInstance(
                workflow_template_id=template_id,
                requester_id=requester_id,
                resource_type=resource_type,
                resource_id=resource_id,
                data=data or {},
                approvers=approvers,
                approvals=[]
            )
            
            db.session.add(workflow_instance)
            db.session.commit()
            
            # Send notifications to first approver
            self.send_approval_notification(workflow_instance, 0)
            
            return workflow_instance
            
        except Exception as e:
            logger.error(f"[ERROR] Error starting workflow: {e}")
            db.session.rollback()
            return None
    
    def determine_approvers(self, template: WorkflowTemplate, 
                          requester_id: int, data: Dict = None) -> List[Dict]:
        """Determine approvers for workflow steps"""
        try:
            approvers = []
            
            for step in template.steps:
                approver_type = step.get('approver_type')
                approver_users = self.get_approvers_by_type(
                    approver_type, requester_id, data
                )
                
                approvers.append({
                    'step': step['step'],
                    'approver_type': approver_type,
                    'user_ids': approver_users,
                    'required': step.get('required', True),
                    'timeout_hours': step.get('timeout_hours', 24)
                })
            
            return approvers
            
        except Exception as e:
            logger.error(f"❌ Error determining approvers: {e}")
            return []
    
    def get_approvers_by_type(self, approver_type: str, requester_id: int, 
                            data: Dict = None) -> List[int]:
        """Get approver user IDs by type"""
        try:
            # Get requester's department
            requester_roles = UserRole.query.filter_by(
                user_id=requester_id, 
                is_active=True
            ).join(Role).first()
            
            if not requester_roles:
                return []
            
            department_id = requester_roles.role.department_id
            
            if approver_type == 'direct_supervisor':
                return self.get_direct_supervisors(requester_id, department_id)
            elif approver_type == 'department_head':
                return self.get_department_heads(department_id)
            elif approver_type == 'it_manager':
                return self.get_it_managers()
            elif approver_type == 'security_team':
                return self.get_security_team()
            elif approver_type == 'hr_manager':
                return self.get_hr_managers()
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting approvers by type: {e}")
            return []
    
    def get_direct_supervisors(self, user_id: int, department_id: int) -> List[int]:
        """Get direct supervisors for user"""
        try:
            # Find users with management roles in same department
            management_roles = Role.query.filter_by(
                department_id=department_id,
                is_management=True,
                is_active=True
            ).all()
            
            supervisor_ids = []
            for role in management_roles:
                user_roles = UserRole.query.filter_by(
                    role_id=role.id,
                    is_active=True
                ).all()
                supervisor_ids.extend([ur.user_id for ur in user_roles])
            
            return supervisor_ids
            
        except Exception as e:
            logger.error(f"❌ Error getting direct supervisors: {e}")
            return []
    
    def get_department_heads(self, department_id: int) -> List[int]:
        """Get department heads"""
        try:
            # Find users with highest level management role in department
            highest_level = db.session.query(db.func.max(Role.level)).filter_by(
                department_id=department_id,
                is_management=True,
                is_active=True
            ).scalar()
            
            if not highest_level:
                return []
            
            head_roles = Role.query.filter_by(
                department_id=department_id,
                level=highest_level,
                is_management=True,
                is_active=True
            ).all()
            
            head_ids = []
            for role in head_roles:
                user_roles = UserRole.query.filter_by(
                    role_id=role.id,
                    is_active=True
                ).all()
                head_ids.extend([ur.user_id for ur in user_roles])
            
            return head_ids
            
        except Exception as e:
            logger.error(f"❌ Error getting department heads: {e}")
            return []
    
    def get_it_managers(self) -> List[int]:
        """Get IT managers"""
        try:
            it_department = Department.query.filter_by(code='IT').first()
            if not it_department:
                return []
            
            return self.get_department_heads(it_department.id)
            
        except Exception as e:
            logger.error(f"❌ Error getting IT managers: {e}")
            return []
    
    def get_security_team(self) -> List[int]:
        """Get security team members"""
        try:
            # Find users with security-related roles
            security_roles = Role.query.filter(
                Role.name.ilike('%security%'),
                Role.is_active == True
            ).all()
            
            security_ids = []
            for role in security_roles:
                user_roles = UserRole.query.filter_by(
                    role_id=role.id,
                    is_active=True
                ).all()
                security_ids.extend([ur.user_id for ur in user_roles])
            
            return security_ids
            
        except Exception as e:
            logger.error(f"❌ Error getting security team: {e}")
            return []
    
    def get_hr_managers(self) -> List[int]:
        """Get HR managers"""
        try:
            hr_department = Department.query.filter_by(code='HR').first()
            if not hr_department:
                return []
            
            return self.get_department_heads(hr_department.id)
            
        except Exception as e:
            logger.error(f"❌ Error getting HR managers: {e}")
            return []
    
    def approve_workflow_step(self, workflow_id: int, approver_id: int, 
                            comments: str = None) -> bool:
        """Approve current workflow step"""
        try:
            workflow = WorkflowInstance.query.get(workflow_id)
            if not workflow:
                return False
            
            # Check if user is authorized to approve this step
            if not self.is_authorized_approver(workflow, approver_id):
                return False
            
            # Approve the step
            success = workflow.approve_step(approver_id, comments)
            
            if success:
                # Send notification to next approver or complete workflow
                if workflow.status == 'pending':
                    self.send_approval_notification(workflow, workflow.current_step)
                else:
                    self.send_completion_notification(workflow)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error approving workflow step: {e}")
            return False
    
    def reject_workflow_step(self, workflow_id: int, approver_id: int, 
                           reason: str) -> bool:
        """Reject workflow step"""
        try:
            workflow = WorkflowInstance.query.get(workflow_id)
            if not workflow:
                return False
            
            # Check if user is authorized to reject this step
            if not self.is_authorized_approver(workflow, approver_id):
                return False
            
            # Reject the step
            success = workflow.reject_step(approver_id, reason)
            
            if success:
                self.send_rejection_notification(workflow)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error rejecting workflow step: {e}")
            return False
    
    def is_authorized_approver(self, workflow: WorkflowInstance, approver_id: int) -> bool:
        """Check if user is authorized to approve current step"""
        try:
            if workflow.current_step >= len(workflow.approvers):
                return False
            
            current_step_approvers = workflow.approvers[workflow.current_step]
            return approver_id in current_step_approvers.get('user_ids', [])
            
        except Exception as e:
            logger.error(f"❌ Error checking authorization: {e}")
            return False
    
    def send_approval_notification(self, workflow: WorkflowInstance, step: int):
        """Send notification to approvers"""
        try:
            # This would integrate with notification service
            logger.info(f"📧 Sending approval notification for workflow {workflow.id}, step {step}")
            # Implementation would depend on notification system
            pass
            
        except Exception as e:
            logger.error(f"❌ Error sending approval notification: {e}")
    
    def send_completion_notification(self, workflow: WorkflowInstance):
        """Send workflow completion notification"""
        try:
            logger.info(f"✅ Workflow {workflow.id} completed")
            # Implementation would depend on notification system
            pass
            
        except Exception as e:
            logger.error(f"❌ Error sending completion notification: {e}")
    
    def send_rejection_notification(self, workflow: WorkflowInstance):
        """Send workflow rejection notification"""
        try:
            logger.info(f"❌ Workflow {workflow.id} rejected")
            # Implementation would depend on notification system
            pass
            
        except Exception as e:
            logger.error(f"❌ Error sending rejection notification: {e}")
    
    def get_user_pending_approvals(self, user_id: int) -> List[Dict]:
        """Get pending approvals for user"""
        try:
            pending_workflows = []
            
            # Find workflows where user is current approver
            all_workflows = WorkflowInstance.query.filter_by(
                status='pending'
            ).all()
            
            for workflow in all_workflows:
                if self.is_authorized_approver(workflow, user_id):
                    pending_workflows.append(workflow.to_dict())
            
            return pending_workflows
            
        except Exception as e:
            logger.error(f"❌ Error getting pending approvals: {e}")
            return []
    
    def get_user_workflow_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's workflow history"""
        try:
            workflows = WorkflowInstance.query.filter_by(
                requester_id=user_id
            ).order_by(WorkflowInstance.created_at.desc()).limit(limit).all()
            
            return [workflow.to_dict() for workflow in workflows]
            
        except Exception as e:
            logger.error(f"❌ Error getting workflow history: {e}")
            return []
    
    def get_workflow_statistics(self, department_id: int = None) -> Dict:
        """Get workflow statistics"""
        try:
            query = WorkflowInstance.query
            
            if department_id:
                # Filter by department if specified
                query = query.join(WorkflowTemplate).filter(
                    WorkflowTemplate.department_id == department_id
                )
            
            total_workflows = query.count()
            pending_workflows = query.filter_by(status='pending').count()
            approved_workflows = query.filter_by(status='approved').count()
            rejected_workflows = query.filter_by(status='rejected').count()
            
            return {
                'total': total_workflows,
                'pending': pending_workflows,
                'approved': approved_workflows,
                'rejected': rejected_workflows,
                'approval_rate': (approved_workflows / total_workflows * 100) if total_workflows > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting workflow statistics: {e}")
            return {}
    
    def cleanup_expired_workflows(self):
        """Clean up expired workflows"""
        try:
            expired_workflows = WorkflowInstance.query.filter(
                WorkflowInstance.status == 'pending',
                WorkflowInstance.created_at < datetime.utcnow() - timedelta(days=30)
            ).all()
            
            for workflow in expired_workflows:
                workflow.status = 'expired'
                workflow.completed_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"🧹 Cleaned up {len(expired_workflows)} expired workflows")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired workflows: {e}")
            db.session.rollback()

# Export singleton instance
workflow_service = WorkflowService()
