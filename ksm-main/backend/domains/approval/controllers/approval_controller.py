#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Approval Routes - Best Practices Implementation
API routes untuk approval workflow system dengan escalation dan automation
"""

from flask import Blueprint, request, jsonify
from shared.middlewares.api_auth import jwt_required_custom, admin_required
from shared.utils.response_standardizer import APIResponse
import logging
from datetime import datetime, timedelta

# Create blueprint
approval_bp = Blueprint('approval', __name__, url_prefix='/api/approval')

# Initialize service (lazy initialization to avoid import errors)
approval_service = None

def get_approval_service():
    """Get approval service instance (lazy initialization)"""
    global approval_service
    if approval_service is None:
        try:
            from domains.approval.services.approval_workflow_service import ApprovalWorkflowService
            approval_service = ApprovalWorkflowService()
        except Exception as e:
            logging.error(f"Error initializing ApprovalWorkflowService: {e}")
            # Return a mock service that returns error responses
            class MockApprovalService:
                def create_approval_request(self, *args, **kwargs):
                    return {'success': False, 'error': 'ApprovalWorkflowService not available'}
                def approve_request(self, *args, **kwargs):
                    return {'success': False, 'error': 'ApprovalWorkflowService not available'}
                def reject_request(self, *args, **kwargs):
                    return {'success': False, 'error': 'ApprovalWorkflowService not available'}
                def escalate_request(self, *args, **kwargs):
                    return {'success': False, 'error': 'ApprovalWorkflowService not available'}
                def check_auto_approve_conditions(self, *args, **kwargs):
                    return {'success': False, 'error': 'ApprovalWorkflowService not available'}
                def test_workflow(self, *args, **kwargs):
                    return {'success': False, 'error': 'ApprovalWorkflowService not available'}
            approval_service = MockApprovalService()
    return approval_service

def get_models():
    """Helper function to get models"""
    from config.models_init import init_models
    return init_models()

@approval_bp.route('/workflows', methods=['GET'])
@jwt_required_custom
def get_workflows():
    """Get all approval workflows"""
    try:
        models = get_models()
        ApprovalWorkflow = models['approval']['ApprovalWorkflow']
        
        workflows = ApprovalWorkflow.query.filter_by(is_active=True).all()
        workflows_data = [workflow.to_dict() for workflow in workflows]
        
        return APIResponse.success(
            data=workflows_data,
            message="Approval workflows retrieved successfully"
        )
    except Exception as e:
        logging.error(f"Error getting workflows: {e}")
        return APIResponse.error("Failed to get approval workflows")

@approval_bp.route('/workflows', methods=['POST'])
@admin_required
def create_workflow():
    """Create new approval workflow"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Data tidak boleh kosong")
        
        # Validasi required fields
        required_fields = ['name', 'module', 'action_type', 'approval_steps']
        for field in required_fields:
            if field not in data or not data[field]:
                return APIResponse.error(f"Field {field} harus diisi")
        
        models = get_models()
        ApprovalWorkflow = models['approval']['ApprovalWorkflow']
        from config.database import db
        
        # Cek apakah workflow sudah ada
        existing_workflow = ApprovalWorkflow.query.filter_by(
            name=data['name'],
            module=data['module'],
            action_type=data['action_type']
        ).first()
        if existing_workflow:
            return APIResponse.error("Workflow sudah ada untuk module/action ini")
        
        # Create workflow
        new_workflow = ApprovalWorkflow(
            name=data['name'],
            description=data.get('description', ''),
            module=data['module'],
            action_type=data['action_type'],
            approval_steps=data['approval_steps'],
            escalation_policy=data.get('escalation_policy', {}),
            auto_approve_conditions=data.get('auto_approve_conditions', {}),
            notification_settings=data.get('notification_settings', {})
        )
        
        db.session.add(new_workflow)
        db.session.commit()
        
        return APIResponse.success(
            data=new_workflow.to_dict(),
            message="Approval workflow berhasil dibuat"
        )
    except Exception as e:
        logging.error(f"Error creating workflow: {e}")
        from config.database import db
        db.session.rollback()
        return APIResponse.error("Failed to create approval workflow")

@approval_bp.route('/requests', methods=['GET'])
@jwt_required_custom
def get_approval_requests():
    """Get approval requests dengan filtering"""
    try:
        from flask_jwt_extended import get_jwt_identity
        models = get_models()
        ApprovalRequest = models['approval']['ApprovalRequest']
        
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.unauthorized("User not authenticated")
        
        # Parse query parameters
        status = request.args.get('status')
        module = request.args.get('module')
        limit = min(request.args.get('limit', 50, type=int), 100)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = ApprovalRequest.query
        
        # Filter by user role - show all requests for now
        # TODO: Implement proper role-based filtering
        # if not request.args.get('all_requests'):  # Only show user's requests by default
        #     query = query.filter(ApprovalRequest.requester_id == user_id)
        
        # Apply filters
        if status:
            query = query.filter_by(status=status)
        if module:
            query = query.filter_by(module=module)
        
        # Order by created date
        query = query.order_by(ApprovalRequest.created_at.desc())
        
        # Get total count before pagination
        total_count = query.count()
        
        # Pagination
        requests = query.offset(offset).limit(limit).all()
        requests_data = [req.to_dict() for req in requests]
        
        return APIResponse.success(
            data=requests_data,
            message="Approval requests retrieved successfully",
            total=total_count
        )
    except Exception as e:
        logging.error(f"Error getting approval requests: {e}")
        return APIResponse.error("Failed to get approval requests")

@approval_bp.route('/requests', methods=['POST'])
@jwt_required_custom
def create_approval_request():
    """Create new approval request"""
    try:
        from flask_jwt_extended import get_jwt_identity
        
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.unauthorized("User not authenticated")
        
        data = request.get_json()
        if not data:
            return APIResponse.error("Data tidak boleh kosong")
        
        # Validasi required fields
        required_fields = ['module', 'action_type', 'resource_data']
        for field in required_fields:
            if field not in data or not data[field]:
                return APIResponse.error(f"Field {field} harus diisi")
        
        # Create approval request
        result = get_approval_service().create_approval_request(
            requester_id=user_id,
            module=data['module'],
            action_type=data['action_type'],
            resource_data=data['resource_data'],
            workflow_name=data.get('workflow_name')
        )
        
        if result.get('success'):
            return APIResponse.success(
                data=result.get('data'),
                message="Approval request berhasil dibuat"
            )
        else:
            return APIResponse.error(result.get('error', 'Failed to create approval request'))
            
    except Exception as e:
        logging.error(f"Error creating approval request: {e}")
        return APIResponse.error("Failed to create approval request")

@approval_bp.route('/requests/<int:request_id>/approve', methods=['POST'])
@jwt_required_custom
def approve_request(request_id):
    """Approve approval request"""
    try:
        from flask_jwt_extended import get_jwt_identity
        
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.unauthorized("User not authenticated")
        data = request.get_json() or {}
        
        # Approve request
        result = get_approval_service().approve_request(
            request_id=request_id,
            approver_id=user_id,
            comments=data.get('comments', ''),
            additional_data=data.get('additional_data', {})
        )
        
        if result.get('success'):
            return APIResponse.success(
                data=result.get('data'),
                message="Request berhasil diapprove"
            )
        else:
            return APIResponse.error(result.get('error', 'Failed to approve request'))
            
    except Exception as e:
        logging.error(f"Error approving request: {e}")
        return APIResponse.error("Failed to approve request")

@approval_bp.route('/requests/<int:request_id>/reject', methods=['POST'])
@jwt_required_custom
def reject_request(request_id):
    """Reject approval request"""
    try:
        from flask_jwt_extended import get_jwt_identity
        
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.unauthorized("User not authenticated")
        data = request.get_json() or {}
        
        # Reject request
        result = get_approval_service().reject_request(
            request_id=request_id,
            approver_id=user_id,
            reason=data.get('reason', ''),
            comments=data.get('comments', '')
        )
        
        if result.get('success'):
            return APIResponse.success(
                data=result.get('data'),
                message="Request berhasil direject"
            )
        else:
            return APIResponse.error(result.get('error', 'Failed to reject request'))
            
    except Exception as e:
        logging.error(f"Error rejecting request: {e}")
        return APIResponse.error("Failed to reject request")

@approval_bp.route('/requests/<int:request_id>/escalate', methods=['POST'])
@admin_required
def escalate_request(request_id):
    """Escalate approval request"""
    try:
        data = request.get_json() or {}
        
        # Escalate request
        result = get_approval_service().escalate_request(
            request_id=request_id,
            escalation_reason=data.get('escalation_reason', ''),
            new_approver_id=data.get('new_approver_id')
        )
        
        if result.get('success'):
            return APIResponse.success(
                data=result.get('data'),
                message="Request berhasil di-escalate"
            )
        else:
            return APIResponse.error(result.get('error', 'Failed to escalate request'))
            
    except Exception as e:
        logging.error(f"Error escalating request: {e}")
        return APIResponse.error("Failed to escalate request")

@approval_bp.route('/requests/<int:request_id>', methods=['GET'])
@jwt_required_custom
def get_approval_request(request_id):
    """Get specific approval request details"""
    try:
        models = get_models()
        ApprovalRequest = models['approval']['ApprovalRequest']
        
        approval_request = ApprovalRequest.query.get(request_id)
        if not approval_request:
            return APIResponse.error("Approval request tidak ditemukan")
        
        request_data = approval_request.to_dict()
        
        # Add workflow details
        if approval_request.workflow:
            request_data['workflow'] = approval_request.workflow.to_dict()
        
        # Add approval history
        if approval_request.approval_history:
            request_data['approval_history'] = [
                history.to_dict() for history in approval_request.approval_history
            ]
        
        return APIResponse.success(
            data=request_data,
            message="Approval request retrieved successfully"
        )
    except Exception as e:
        logging.error(f"Error getting approval request: {e}")
        return APIResponse.error("Failed to get approval request")

@approval_bp.route('/requests/<int:request_id>/history', methods=['GET'])
@jwt_required_custom
def get_approval_history(request_id):
    """Get approval request history"""
    try:
        models = get_models()
        ApprovalAction = models['approval']['ApprovalAction']
        
        history = ApprovalAction.query.filter_by(
            approval_request_id=request_id
        ).order_by(ApprovalAction.created_at.desc()).all()
        
        history_data = [h.to_dict() for h in history]
        
        return APIResponse.success(
            data=history_data,
            message="Approval history retrieved successfully"
        )
    except Exception as e:
        logging.error(f"Error getting approval history: {e}")
        return APIResponse.error("Failed to get approval history")

@approval_bp.route('/stats', methods=['GET'])
@jwt_required_custom
def get_approval_stats():
    """Get approval statistics"""
    try:
        from flask_jwt_extended import get_jwt_identity
        models = get_models()
        ApprovalRequest = models['approval']['ApprovalRequest']
        from sqlalchemy import func
        
        user_id = get_jwt_identity()
        if not user_id:
            return APIResponse.unauthorized("User not authenticated")
        
        # Get stats for user
        stats = {
            'pending_approvals': ApprovalRequest.query.filter_by(
                status='pending'
            ).count(),
            'my_requests': ApprovalRequest.query.filter_by(
                requester_id=user_id
            ).count(),
            'approved_requests': ApprovalRequest.query.filter_by(
                requester_id=user_id,
                status='approved'
            ).count(),
            'rejected_requests': ApprovalRequest.query.filter_by(
                requester_id=user_id,
                status='rejected'
            ).count()
        }
        
        return APIResponse.success(
            data=stats,
            message="Approval statistics retrieved successfully"
        )
    except Exception as e:
        logging.error(f"Error getting approval stats: {e}")
        return APIResponse.error("Failed to get approval statistics")

@approval_bp.route('/auto-approve/check', methods=['POST'])
@jwt_required_custom
def check_auto_approve():
    """Check if request can be auto-approved"""
    try:
        data = request.get_json()
        if not data:
            return APIResponse.error("Data tidak boleh kosong")
        
        # Check auto-approve conditions
        result = get_approval_service().check_auto_approve_conditions(
            module=data.get('module'),
            action_type=data.get('action_type'),
            resource_data=data.get('resource_data', {}),
            requester_id=data.get('requester_id')
        )
        
        return APIResponse.success(
            data=result,
            message="Auto-approve check completed"
        )
    except Exception as e:
        logging.error(f"Error checking auto-approve: {e}")
        return APIResponse.error("Failed to check auto-approve conditions")

@approval_bp.route('/workflows/<int:workflow_id>/test', methods=['POST'])
@admin_required
def test_workflow():
    """Test approval workflow"""
    try:
        workflow_id = request.view_args['workflow_id']
        data = request.get_json() or {}
        
        # Test workflow
        result = get_approval_service().test_workflow(
            workflow_id=workflow_id,
            test_data=data.get('test_data', {})
        )
        
        return APIResponse.success(
            data=result,
            message="Workflow test completed"
        )
    except Exception as e:
        logging.error(f"Error testing workflow: {e}")
        return APIResponse.error("Failed to test workflow")
