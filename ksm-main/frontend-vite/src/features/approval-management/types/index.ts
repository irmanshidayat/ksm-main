/**
 * Approval Management Types
 */

export interface ApprovalRequest {
  id: number;
  workflow_id: number;
  workflow_name: string;
  requester_id: number;
  requester_name: string;
  module: string;
  action_type: string;
  resource_id?: number;
  resource_data: any;
  status: 'pending' | 'approved' | 'rejected' | 'expired' | 'cancelled';
  current_step: number;
  timeout_at?: string;
  completed_at?: string;
  rejection_reason?: string;
  delegation_reason?: string;
  created_at: string;
  updated_at: string;
  actions_count: number;
  escalation_count: number;
  is_timeout: boolean;
  days_since_created: number;
}

export interface ApprovalStats {
  pending_approvals: number;
  my_requests: number;
  approved_requests: number;
  rejected_requests: number;
}

export interface ApprovalAction {
  id: number;
  request_id: number;
  approver_id: number;
  approver_name: string;
  action: 'approve' | 'reject' | 'delegate';
  comment?: string;
  created_at: string;
}

export interface ApprovalQueryParams {
  status?: string;
  module?: string;
  search?: string;
  page?: number;
  per_page?: number;
}

