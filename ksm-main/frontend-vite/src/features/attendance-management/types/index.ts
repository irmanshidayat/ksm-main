/**
 * Attendance Management Types
 */

export interface AttendanceRecord {
  id: number;
  user_id: number;
  user_name?: string;
  clock_in: string;
  clock_in_latitude?: number;
  clock_in_longitude?: number;
  clock_in_address?: string;
  clock_in_photo?: string;
  clock_out?: string;
  clock_out_latitude?: number;
  clock_out_longitude?: number;
  clock_out_address?: string;
  clock_out_photo?: string;
  work_duration_minutes?: number;
  work_duration_hours?: number;
  overtime_minutes?: number;
  overtime_hours?: number;
  status: AttendanceStatus;
  notes?: string;
  is_approved: boolean;
  approved_by?: number;
  approved_at?: string;
  created_at: string;
  updated_at: string;
  user?: {
    id: number;
    username: string;
    email?: string;
  };
}

export type AttendanceStatus = 'present' | 'late' | 'absent' | 'half_day';

export interface LeaveRequest {
  id: number;
  user_id: number;
  user_name?: string;
  leave_type: LeaveType;
  leave_type_display?: string;
  start_date: string;
  end_date: string;
  total_days: number;
  reason: string;
  medical_certificate?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  status: LeaveStatus;
  status_display?: string;
  approver_id?: number;
  approver_name?: string;
  approved_at?: string;
  rejection_reason?: string;
  created_at: string;
  updated_at: string;
}

export type LeaveType = 'sick' | 'personal' | 'vacation' | 'emergency';
export type LeaveStatus = 'pending' | 'approved' | 'rejected' | 'cancelled';

export interface DailyTask {
  id: number;
  user_id: number;
  title: string;
  description?: string;
  status: TaskStatus;
  priority?: TaskPriority;
  due_date?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  user?: {
    id: number;
    username: string;
  };
}

export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface AttendanceStats {
  period: {
    start_date: string;
    end_date: string;
    working_days: number;
  };
  attendance: {
    total_days: number;
    present_days: number;
    late_days: number;
    absent_days: number;
    half_day_days: number;
    attendance_rate: number;
  };
  work_hours: {
    total_work_hours: number;
    total_overtime_hours: number;
    average_daily_hours: number;
  };
}

export interface TodayStatus {
  user_id?: number;
  has_clocked_in: boolean;
  has_clocked_out: boolean;
  clock_in_time?: string;
  clock_out_time?: string;
  status: AttendanceStatus;
  work_duration_hours: number;
  total_users?: number;
  clocked_in_users?: number;
  clocked_out_users?: number;
  absent_users?: number;
  attendance_rate?: number;
}

export interface AttendanceQueryParams {
  page?: number;
  per_page?: number;
  start_date?: string;
  end_date?: string;
  user_id?: number;
  status?: AttendanceStatus;
  search?: string;
}

export interface LeaveRequestQueryParams {
  page?: number;
  per_page?: number;
  user_id?: number;
  status?: LeaveStatus;
  leave_type?: LeaveType;
  date_from?: string;
  date_to?: string;
}

export interface TaskQueryParams {
  page?: number;
  per_page?: number;
  user_id?: number;
  status?: TaskStatus;
  priority?: TaskPriority;
  search?: string;
}

export interface PaginatedAttendanceResponse {
  items: AttendanceRecord[];
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

export interface PaginatedLeaveRequestResponse {
  items: LeaveRequest[];
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

export interface PaginatedTaskResponse {
  items: DailyTask[];
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

export interface ClockInRequest {
  latitude: number;
  longitude: number;
  address?: string;
  photo?: string;
  notes?: string;
}

export interface ClockOutRequest {
  attendance_id: number;
  latitude: number;
  longitude: number;
  address?: string;
  photo?: string;
  notes?: string;
}

export interface LeaveRequestSubmit {
  leave_type: LeaveType;
  start_date: string;
  end_date: string;
  reason: string;
  medical_certificate?: string;
  emergency_contact?: string;
  emergency_phone?: string;
}

export const ATTENDANCE_STATUS_LABELS: Record<AttendanceStatus, string> = {
  present: 'Hadir',
  late: 'Terlambat',
  absent: 'Tidak Hadir',
  half_day: 'Setengah Hari'
};

export const ATTENDANCE_STATUS_COLORS: Record<AttendanceStatus, string> = {
  present: '#10B981',
  late: '#F59E0B',
  absent: '#EF4444',
  half_day: '#8B5CF6'
};

export const LEAVE_TYPE_LABELS: Record<LeaveType, string> = {
  sick: 'Sakit',
  personal: 'Izin Pribadi',
  vacation: 'Cuti',
  emergency: 'Izin Darurat'
};

export const LEAVE_STATUS_LABELS: Record<LeaveStatus, string> = {
  pending: 'Menunggu Persetujuan',
  approved: 'Disetujui',
  rejected: 'Ditolak',
  cancelled: 'Dibatalkan'
};

