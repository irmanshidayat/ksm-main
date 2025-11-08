#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Attendance Models untuk KSM Main Backend
Sistem absensi karyawan dengan lokasi GPS dan foto kamera
"""

from config.database import db
from datetime import datetime, time, date
from sqlalchemy import Index, UniqueConstraint
import json
from utils.timezone_utils import get_jakarta_utc_time, utc_to_jakarta

class AttendanceRecord(db.Model):
    """Model untuk record absensi karyawan"""
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Clock in data
    clock_in = db.Column(db.DateTime, nullable=False)
    clock_in_latitude = db.Column(db.Float)
    clock_in_longitude = db.Column(db.Float)
    clock_in_address = db.Column(db.Text)  # Alamat dari reverse geocoding
    clock_in_photo = db.Column(db.Text)  # Base64 encoded image
    
    # Clock out data
    clock_out = db.Column(db.DateTime)
    clock_out_latitude = db.Column(db.Float)
    clock_out_longitude = db.Column(db.Float)
    clock_out_address = db.Column(db.Text)
    clock_out_photo = db.Column(db.Text)
    
    # Work duration calculation
    work_duration_minutes = db.Column(db.Integer)  # Durasi kerja dalam menit
    overtime_minutes = db.Column(db.Integer, default=0)  # Overtime dalam menit
    
    # Status dan notes
    status = db.Column(db.String(20), default='present')  # present, late, absent, half_day
    notes = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=get_jakarta_utc_time)
    updated_at = db.Column(db.DateTime, default=get_jakarta_utc_time, onupdate=get_jakarta_utc_time)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='attendance_records')
    approver = db.relationship('User', foreign_keys=[approved_by])
    overtime_requests = db.relationship('OvertimeRequest', backref='attendance_record', lazy=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_attendance_user_date', 'user_id', 'clock_in'),
        Index('idx_attendance_date', 'clock_in'),
        Index('idx_attendance_status', 'status'),
        Index('idx_attendance_approved', 'is_approved'),
        UniqueConstraint('user_id', 'clock_in', name='unique_user_clock_in_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'clock_in': self.clock_in.isoformat() if self.clock_in else None,
            'clock_in_latitude': self.clock_in_latitude,
            'clock_in_longitude': self.clock_in_longitude,
            'clock_in_address': self.clock_in_address,
            'clock_in_photo': self.clock_in_photo,
            'clock_out': self.clock_out.isoformat() if self.clock_out else None,
            'clock_out_latitude': self.clock_out_latitude,
            'clock_out_longitude': self.clock_out_longitude,
            'clock_out_address': self.clock_out_address,
            'clock_out_photo': self.clock_out_photo,
            'work_duration_minutes': self.work_duration_minutes,
            'work_duration_hours': round(self.work_duration_minutes / 60, 2) if self.work_duration_minutes else 0,
            'overtime_minutes': self.overtime_minutes,
            'overtime_hours': round(self.overtime_minutes / 60, 2) if self.overtime_minutes else 0,
            'status': self.status,
            'notes': self.notes,
            'is_approved': self.is_approved,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def calculate_work_duration(self):
        """Hitung durasi kerja jika clock out sudah ada"""
        if self.clock_in and self.clock_out:
            duration = self.clock_out - self.clock_in
            self.work_duration_minutes = int(duration.total_seconds() / 60)
            
            # Hitung overtime (jika lebih dari 8 jam)
            if self.work_duration_minutes > 480:  # 8 jam = 480 menit
                self.overtime_minutes = self.work_duration_minutes - 480
            else:
                self.overtime_minutes = 0
                
            return self.work_duration_minutes
        return 0
    
    def is_late(self, work_start_time=None, grace_period_minutes=0):
        """Cek apakah terlambat dengan grace period"""
        if not self.clock_in:
            return False
            
        clock_in_time = self.clock_in.time()
        
        if work_start_time:
            # Hitung batas waktu dengan grace period
            from datetime import timedelta
            grace_time = (datetime.combine(date.today(), work_start_time) + 
                         timedelta(minutes=grace_period_minutes)).time()
            return clock_in_time > grace_time
        else:
            # Default: terlambat jika lebih dari jam 8:00 (08:00 + 0 menit grace period)
            return clock_in_time > time(8, 0)
    
    def get_status(self):
        """Tentukan status berdasarkan data"""
        if not self.clock_in:
            return 'absent'
        elif not self.clock_out:
            return 'present'  # Belum clock out
        elif self.is_late():
            return 'late'
        elif self.work_duration_minutes and self.work_duration_minutes < 240:  # Kurang dari 4 jam
            return 'half_day'
        else:
            return 'present'

class AttendanceLeave(db.Model):
    """Model untuk izin/sakit/cuti karyawan"""
    __tablename__ = 'attendance_leaves'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Leave details
    leave_type = db.Column(db.String(20), nullable=False)  # sick, personal, vacation, emergency
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Integer, nullable=False)
    
    # Request details
    reason = db.Column(db.Text, nullable=False)
    medical_certificate = db.Column(db.Text)  # Base64 encoded file
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    
    # Approval workflow
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, cancelled
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=get_jakarta_utc_time)
    updated_at = db.Column(db.DateTime, default=get_jakarta_utc_time, onupdate=get_jakarta_utc_time)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='leave_requests')
    approver = db.relationship('User', foreign_keys=[approver_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_leave_user', 'user_id'),
        Index('idx_leave_dates', 'start_date', 'end_date'),
        Index('idx_leave_status', 'status'),
        Index('idx_leave_type', 'leave_type'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'leave_type': self.leave_type,
            'leave_type_display': self.get_leave_type_display(),
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'total_days': self.total_days,
            'reason': self.reason,
            'medical_certificate': self.medical_certificate,
            'emergency_contact': self.emergency_contact,
            'emergency_phone': self.emergency_phone,
            'status': self.status,
            'status_display': self.get_status_display(),
            'approver_id': self.approver_id,
            'approver_name': self.approver.username if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_leave_type_display(self):
        """Get display name for leave type"""
        types = {
            'sick': 'Sakit',
            'personal': 'Izin Pribadi',
            'vacation': 'Cuti',
            'emergency': 'Izin Darurat'
        }
        return types.get(self.leave_type, self.leave_type)
    
    def get_status_display(self):
        """Get display name for status"""
        statuses = {
            'pending': 'Menunggu Persetujuan',
            'approved': 'Disetujui',
            'rejected': 'Ditolak',
            'cancelled': 'Dibatalkan'
        }
        return statuses.get(self.status, self.status)
    
    def approve(self, approver_id):
        """Approve leave request"""
        self.status = 'approved'
        self.approver_id = approver_id
        self.approved_at = datetime.utcnow()
        db.session.commit()
    
    def reject(self, approver_id, rejection_reason):
        """Reject leave request"""
        self.status = 'rejected'
        self.approver_id = approver_id
        self.approved_at = datetime.utcnow()
        self.rejection_reason = rejection_reason
        db.session.commit()

class OvertimeRequest(db.Model):
    """Model untuk request overtime"""
    __tablename__ = 'overtime_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    attendance_id = db.Column(db.Integer, db.ForeignKey('attendance_records.id'), nullable=False)
    
    # Overtime details
    requested_hours = db.Column(db.Float, nullable=False)
    actual_hours = db.Column(db.Float)  # Setelah approval
    reason = db.Column(db.Text, nullable=False)
    task_description = db.Column(db.Text)
    
    # Approval workflow
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=get_jakarta_utc_time)
    updated_at = db.Column(db.DateTime, default=get_jakarta_utc_time, onupdate=get_jakarta_utc_time)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='overtime_requests')
    approver = db.relationship('User', foreign_keys=[approver_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_overtime_user', 'user_id'),
        Index('idx_overtime_attendance', 'attendance_id'),
        Index('idx_overtime_status', 'status'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'attendance_id': self.attendance_id,
            'attendance_date': self.attendance_record.clock_in.date().isoformat() if self.attendance_record and self.attendance_record.clock_in else None,
            'requested_hours': self.requested_hours,
            'actual_hours': self.actual_hours,
            'reason': self.reason,
            'task_description': self.task_description,
            'status': self.status,
            'status_display': self.get_status_display(),
            'approver_id': self.approver_id,
            'approver_name': self.approver.username if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_status_display(self):
        """Get display name for status"""
        statuses = {
            'pending': 'Menunggu Persetujuan',
            'approved': 'Disetujui',
            'rejected': 'Ditolak'
        }
        return statuses.get(self.status, self.status)
    
    def approve(self, approver_id, actual_hours=None):
        """Approve overtime request"""
        self.status = 'approved'
        self.approver_id = approver_id
        self.approved_at = datetime.utcnow()
        if actual_hours:
            self.actual_hours = actual_hours
        db.session.commit()
    
    def reject(self, approver_id, rejection_reason):
        """Reject overtime request"""
        self.status = 'rejected'
        self.approver_id = approver_id
        self.approved_at = datetime.utcnow()
        self.rejection_reason = rejection_reason
        db.session.commit()

class AttendanceSettings(db.Model):
    """Model untuk konfigurasi absensi"""
    __tablename__ = 'attendance_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.String(100), default='PT. Kian Santang Muliatama')
    
    # Work schedule
    work_start_time = db.Column(db.Time, default=time(8, 0))  # 08:00
    work_end_time = db.Column(db.Time, default=time(17, 0))   # 17:00
    grace_period_minutes = db.Column(db.Integer, default=0)  # Toleransi keterlambatan
    
    # Overtime settings
    overtime_enabled = db.Column(db.Boolean, default=True)
    overtime_rate_multiplier = db.Column(db.Float, default=1.5)  # 1.5x untuk overtime
    
    # Location settings
    location_validation_enabled = db.Column(db.Boolean, default=False)
    allowed_locations = db.Column(db.Text)  # JSON array of allowed locations
    
    # Photo settings
    photo_required = db.Column(db.Boolean, default=True)
    max_photo_size_mb = db.Column(db.Integer, default=5)
    
    # Notification settings
    reminder_enabled = db.Column(db.Boolean, default=True)
    reminder_time = db.Column(db.Time, default=time(7, 30))  # Reminder jam 7:30
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=get_jakarta_utc_time)
    updated_at = db.Column(db.DateTime, default=get_jakarta_utc_time, onupdate=get_jakarta_utc_time)
    
    # Indexes
    __table_args__ = (
        Index('idx_attendance_settings_company', 'company_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'work_start_time': self.work_start_time.isoformat() if self.work_start_time else None,
            'work_end_time': self.work_end_time.isoformat() if self.work_end_time else None,
            'grace_period_minutes': self.grace_period_minutes,
            'overtime_enabled': self.overtime_enabled,
            'overtime_rate_multiplier': self.overtime_rate_multiplier,
            'location_validation_enabled': self.location_validation_enabled,
            'allowed_locations': json.loads(self.allowed_locations) if self.allowed_locations else [],
            'photo_required': self.photo_required,
            'max_photo_size_mb': self.max_photo_size_mb,
            'reminder_enabled': self.reminder_enabled,
            'reminder_time': self.reminder_time.isoformat() if self.reminder_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_allowed_locations(self):
        """Get allowed locations as list"""
        if self.allowed_locations:
            try:
                return json.loads(self.allowed_locations)
            except:
                return []
        return []
    
    def set_allowed_locations(self, locations):
        """Set allowed locations from list"""
        self.allowed_locations = json.dumps(locations) if locations else None


class DailyTask(db.Model):
    """Model untuk task harian karyawan"""
    __tablename__ = 'daily_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Task details
    task_date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(20), default='regular')  # regular, urgent, project
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), default='todo')  # todo, in_progress, done, cancelled
    
    # Assignment fields
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # NULL = self-created
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_self_created = db.Column(db.Boolean, default=True)
    
    # Time tracking
    estimated_minutes = db.Column(db.Integer)
    actual_minutes = db.Column(db.Integer)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Integration with attendance
    attendance_id = db.Column(db.Integer, db.ForeignKey('attendance_records.id'))
    
    # Approval workflow
    requires_approval = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    
    # Additional fields
    tags = db.Column(db.Text)  # JSON array of tags
    completion_note = db.Column(db.Text)
    
    # Soft delete
    deleted_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=get_jakarta_utc_time)
    updated_at = db.Column(db.DateTime, default=get_jakarta_utc_time, onupdate=get_jakarta_utc_time)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='daily_tasks')
    assigned_by_user = db.relationship('User', foreign_keys=[assigned_by], backref='assigned_tasks')
    assigned_to_user = db.relationship('User', foreign_keys=[assigned_to])
    approver = db.relationship('User', foreign_keys=[approved_by])
    attendance_record = db.relationship('AttendanceRecord', backref='daily_tasks')
    attachments = db.relationship('TaskAttachment', backref='task', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('TaskComment', backref='task', lazy=True, cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('idx_daily_task_user_date', 'user_id', 'task_date'),
        Index('idx_daily_task_status', 'status'),
        Index('idx_daily_task_category', 'category'),
        Index('idx_daily_task_assigned_to', 'assigned_to'),
        Index('idx_daily_task_attendance', 'attendance_id'),
        Index('idx_daily_task_deleted', 'deleted_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'task_date': self.task_date.isoformat() if self.task_date else None,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'category_display': self.get_category_display(),
            'priority': self.priority,
            'priority_display': self.get_priority_display(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'assigned_by': self.assigned_by,
            'assigned_by_name': self.assigned_by_user.username if self.assigned_by_user else None,
            'assigned_to': self.assigned_to,
            'assigned_to_name': self.assigned_to_user.username if self.assigned_to_user else None,
            'is_self_created': self.is_self_created,
            'estimated_minutes': self.estimated_minutes,
            'estimated_hours': round(self.estimated_minutes / 60, 2) if self.estimated_minutes else 0,
            'actual_minutes': self.actual_minutes,
            'actual_hours': round(self.actual_minutes / 60, 2) if self.actual_minutes else 0,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'attendance_id': self.attendance_id,
            'requires_approval': self.requires_approval,
            'is_approved': self.is_approved,
            'approved_by': self.approved_by,
            'approved_by_name': self.approver.username if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'tags': json.loads(self.tags) if self.tags else [],
            'completion_note': self.completion_note,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'created_at': utc_to_jakarta(self.created_at).isoformat() if self.created_at else None,
            'updated_at': utc_to_jakarta(self.updated_at).isoformat() if self.updated_at else None,
            'attachments_count': len(self.attachments) if self.attachments else 0,
            'comments_count': len(self.comments) if self.comments else 0
        }
    
    def get_category_display(self):
        """Get display name for category"""
        categories = {
            'regular': 'Regular',
            'urgent': 'Urgent',
            'project': 'Project'
        }
        return categories.get(self.category, self.category)
    
    def get_priority_display(self):
        """Get display name for priority"""
        priorities = {
            'low': 'Low',
            'medium': 'Medium',
            'high': 'High',
            'critical': 'Critical'
        }
        return priorities.get(self.priority, self.priority)
    
    def get_status_display(self):
        """Get display name for status"""
        statuses = {
            'todo': 'To Do',
            'in_progress': 'In Progress',
            'done': 'Done',
            'cancelled': 'Cancelled'
        }
        return statuses.get(self.status, self.status)
    
    def start_task(self):
        """Start task - set status to in_progress and started_at"""
        self.status = 'in_progress'
        self.started_at = datetime.utcnow()
        db.session.commit()
    
    def complete_task(self, actual_minutes=None, completion_note=None):
        """Complete task - set status to done and completed_at"""
        self.status = 'done'
        self.completed_at = datetime.utcnow()
        if actual_minutes:
            self.actual_minutes = actual_minutes
        if completion_note:
            self.completion_note = completion_note
        db.session.commit()
    
    def cancel_task(self, reason=None):
        """Cancel task"""
        self.status = 'cancelled'
        if reason:
            self.completion_note = reason
        db.session.commit()
    
    def soft_delete(self):
        """Soft delete task"""
        self.deleted_at = datetime.utcnow()
        db.session.commit()


class TaskAttachment(db.Model):
    """Model untuk attachment task"""
    __tablename__ = 'task_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('daily_tasks.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    base64_content = db.Column(db.Text, nullable=False)  # Longtext untuk base64
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship('User', backref='task_attachments')
    
    # Indexes
    __table_args__ = (
        Index('idx_task_attachment_task', 'task_id'),
        Index('idx_task_attachment_uploader', 'uploaded_by'),
        Index('idx_task_attachment_uploaded', 'uploaded_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'file_size_mb': round(self.file_size / (1024 * 1024), 2),
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.username if self.uploader else None,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }
    
    def get_base64_content(self):
        """Get base64 content"""
        return self.base64_content


class TaskComment(db.Model):
    """Model untuk komentar task"""
    __tablename__ = 'task_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('daily_tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    is_system_comment = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_jakarta_utc_time)
    updated_at = db.Column(db.DateTime, default=get_jakarta_utc_time, onupdate=get_jakarta_utc_time)
    
    # Relationships
    user = db.relationship('User', backref='task_comments')
    
    # Indexes
    __table_args__ = (
        Index('idx_task_comment_task', 'task_id'),
        Index('idx_task_comment_user', 'user_id'),
        Index('idx_task_comment_created', 'created_at'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'comment_text': self.comment_text,
            'is_system_comment': self.is_system_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TaskSettings(db.Model):
    """Model untuk konfigurasi task"""
    __tablename__ = 'task_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.String(100), default='PT. Kian Santang Muliatama')
    
    # Task validation settings
    require_task_before_clockout = db.Column(db.Boolean, default=True)
    minimum_tasks_required = db.Column(db.Integer, default=1)
    allow_self_task_creation = db.Column(db.Boolean, default=True)
    
    # File upload settings
    max_attachment_size_mb = db.Column(db.Integer, default=5)
    allowed_file_types = db.Column(db.Text)  # JSON array
    
    # Notification settings
    notification_enabled = db.Column(db.Boolean, default=True)
    email_notification_enabled = db.Column(db.Boolean, default=True)
    
    # Task settings
    default_task_category = db.Column(db.String(20), default='regular')
    default_task_priority = db.Column(db.String(20), default='medium')
    auto_approve_self_tasks = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=get_jakarta_utc_time)
    updated_at = db.Column(db.DateTime, default=get_jakarta_utc_time, onupdate=get_jakarta_utc_time)
    
    # Indexes
    __table_args__ = (
        Index('idx_task_settings_company', 'company_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'require_task_before_clockout': self.require_task_before_clockout,
            'minimum_tasks_required': self.minimum_tasks_required,
            'allow_self_task_creation': self.allow_self_task_creation,
            'max_attachment_size_mb': self.max_attachment_size_mb,
            'allowed_file_types': json.loads(self.allowed_file_types) if self.allowed_file_types else ['jpg', 'jpeg', 'png', 'pdf', 'docx', 'xlsx'],
            'notification_enabled': self.notification_enabled,
            'email_notification_enabled': self.email_notification_enabled,
            'default_task_category': self.default_task_category,
            'default_task_priority': self.default_task_priority,
            'auto_approve_self_tasks': self.auto_approve_self_tasks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_allowed_file_types(self):
        """Get allowed file types as list"""
        if self.allowed_file_types:
            try:
                return json.loads(self.allowed_file_types)
            except:
                return ['jpg', 'jpeg', 'png', 'pdf', 'docx', 'xlsx']
        return ['jpg', 'jpeg', 'png', 'pdf', 'docx', 'xlsx']
    
    def set_allowed_file_types(self, file_types):
        """Set allowed file types from list"""
        self.allowed_file_types = json.dumps(file_types) if file_types else None
