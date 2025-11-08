#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Attendance Controller untuk KSM Main Backend
REST API endpoints untuk sistem absensi karyawan
"""

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
from typing import Dict, List
import logging
import io

from services.attendance_service import attendance_service
from controllers.daily_task_controller import DailyTaskController
from middlewares.role_auth import require_admin, block_vendor
from config.database import db
from models.attendance_models import AttendanceRecord

logger = logging.getLogger(__name__)

attendance_bp = Blueprint('attendance', __name__, url_prefix='/api/attendance')

@attendance_bp.route('/clock-in', methods=['POST'])
@jwt_required()
@block_vendor()
def clock_in():
    """
    POST /api/attendance/clock-in
    Clock in dengan foto dan lokasi GPS
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data tidak boleh kosong'
            }), 400
        
        user_id = get_jwt_identity()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        address = data.get('address', '')
        photo_base64 = data.get('photo')
        notes = data.get('notes', '')
        
        # Validasi required fields
        if not latitude or not longitude:
            return jsonify({
                'success': False,
                'message': 'Koordinat GPS wajib diisi'
            }), 400
        
        result = attendance_service.clock_in(
            user_id=user_id,
            latitude=float(latitude),
            longitude=float(longitude),
            address=address,
            photo_base64=photo_base64,
            notes=notes
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error clock in endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/clock-out', methods=['POST'])
@jwt_required()
@block_vendor()
def clock_out():
    """
    POST /api/attendance/clock-out
    Clock out dengan foto dan lokasi GPS
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data tidak boleh kosong'
            }), 400
        
        user_id = get_jwt_identity()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        address = data.get('address', '')
        photo_base64 = data.get('photo')
        notes = data.get('notes', '')
        
        # Debug logging
        logger.info(f"Clock out request - User ID: {user_id}")
        logger.info(f"Clock out request - Latitude: {latitude}, Longitude: {longitude}")
        logger.info(f"Clock out request - Address: {address}")
        logger.info(f"Clock out request - Photo present: {bool(photo_base64)}")
        logger.info(f"Clock out request - Notes: {notes}")
        
        # Validasi required fields
        if not latitude or not longitude:
            logger.warning(f"Clock out validation failed - Missing coordinates: lat={latitude}, lng={longitude}")
            return jsonify({
                'success': False,
                'message': 'Koordinat GPS wajib diisi'
            }), 400
        
        result = attendance_service.clock_out(
            user_id=user_id,
            latitude=float(latitude),
            longitude=float(longitude),
            address=address,
            photo_base64=photo_base64,
            notes=notes
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error clock out endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/my-attendance', methods=['GET'])
@jwt_required()
@block_vendor()
def get_my_attendance():
    """
    GET /api/attendance/my-attendance
    History absensi user sendiri
    """
    try:
        user_id = get_jwt_identity()
        
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 30))
        
        # Convert string dates to date objects
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        records = attendance_service.get_user_attendance(
            user_id=user_id,
            start_date=start_date_obj,
            end_date=end_date_obj,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': records,
            'count': len(records)
        }), 200
        
    except Exception as e:
        logger.error(f"Error get my attendance: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/team', methods=['GET'])
@jwt_required()
@block_vendor()
def get_team_attendance():
    """
    GET /api/attendance/team
    Manager lihat absensi tim
    """
    try:
        manager_id = get_jwt_identity()
        
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Convert string dates to date objects
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        records = attendance_service.get_team_attendance(
            manager_user_id=manager_id,
            start_date=start_date_obj,
            end_date=end_date_obj
        )
        
        return jsonify({
            'success': True,
            'data': records,
            'count': len(records)
        }), 200
        
    except Exception as e:
        logger.error(f"Error get team attendance: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('', methods=['GET'])
@jwt_required()
@block_vendor()
def get_attendance():
    """
    GET /api/attendance
    Ambil daftar attendance dengan pagination
    """
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        search = request.args.get('search')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Convert string dates to date objects
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Convert user_id to int if provided
        user_id_int = None
        if user_id:
            try:
                user_id_int = int(user_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'User ID tidak valid'
                }), 400
        
        # Get current user ID
        current_user_id = get_jwt_identity()
        
        # Jika tidak ada user_id yang di-spesifikasi, default ke current user
        # Admin bisa lihat semua dengan tidak mengirim user_id
        if not user_id_int:
            # Untuk non-admin, hanya bisa lihat data sendiri
            # Admin bisa lihat semua dengan tidak mengirim user_id
            from models.knowledge_base import User
            current_user = User.query.get(current_user_id)
            if current_user and current_user.role != 'admin':
                user_id_int = current_user_id
        
        # Query dengan pagination
        query = AttendanceRecord.query
        
        if start_date_obj:
            query = query.filter(db.func.date(AttendanceRecord.clock_in) >= start_date_obj)
        if end_date_obj:
            query = query.filter(db.func.date(AttendanceRecord.clock_in) <= end_date_obj)
        if user_id_int:
            query = query.filter(AttendanceRecord.user_id == user_id_int)
        if status:
            query = query.filter(AttendanceRecord.status == status)
        
        # Tambahkan filter pencarian
        if search:
            from models.knowledge_base import User
            query = query.join(User, AttendanceRecord.user_id == User.id)
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    User.username.ilike(search_term),
                    AttendanceRecord.clock_in_address.ilike(search_term),
                    AttendanceRecord.clock_out_address.ilike(search_term)
                )
            )
        
        # Hitung total
        total = query.count()
        
        # Apply pagination
        records = query.order_by(AttendanceRecord.clock_in.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'success': True,
            'data': {
                'items': [record.to_dict() for record in records],
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page if total > 0 else 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error get attendance: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/all', methods=['GET'])
@jwt_required()
@require_admin()
def get_all_attendance():
    """
    GET /api/attendance/all
    Admin lihat semua absensi dengan filter
    """
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        search = request.args.get('search')  # Parameter pencarian baru
        
        # Convert string dates to date objects
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Convert user_id to int if provided
        user_id_int = None
        if user_id:
            try:
                user_id_int = int(user_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'User ID tidak valid'
                }), 400
        
        records = attendance_service.get_all_attendance(
            start_date=start_date_obj,
            end_date=end_date_obj,
            user_id=user_id_int,
            status=status,
            search=search  # Tambahkan parameter search
        )
        
        return jsonify({
            'success': True,
            'data': records,
            'count': len(records)
        }), 200
        
    except Exception as e:
        logger.error(f"Error get all attendance: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/today-status', methods=['GET'])
@jwt_required()
@block_vendor()
def get_today_status():
    """
    GET /api/attendance/today-status
    Status absensi hari ini
    """
    try:
        user_id = request.args.get('user_id')
        
        # Convert user_id to int if provided (for admin)
        user_id_int = None
        if user_id:
            try:
                user_id_int = int(user_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'User ID tidak valid'
                }), 400
        else:
            # Default to current user
            user_id_int = get_jwt_identity()
        
        status = attendance_service.get_today_status(user_id=user_id_int)
        
        return jsonify({
            'success': True,
            'data': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error get today status: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@block_vendor()
def get_dashboard():
    """
    GET /api/attendance/dashboard
    Dashboard data: stats dan today status
    """
    try:
        # Parse query parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        user_id = request.args.get('user_id')
        
        # Convert string dates to date objects
        start_date_obj = None
        end_date_obj = None
        
        if date_from:
            start_date_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        if date_to:
            end_date_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
        
        # Convert user_id to int if provided
        user_id_int = None
        if user_id:
            try:
                user_id_int = int(user_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'User ID tidak valid'
                }), 400
        else:
            # Default to current user
            user_id_int = get_jwt_identity()
        
        # Get dashboard stats
        stats = attendance_service.get_dashboard_stats(
            user_id=user_id_int,
            start_date=start_date_obj,
            end_date=end_date_obj
        )
        
        # Get today status
        today_status = attendance_service.get_today_status(user_id=user_id_int)
        
        return jsonify({
            'success': True,
            'data': {
                'stats': stats,
                'todayStatus': today_status if today_status else {}
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error get dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/leave-request', methods=['POST'])
@jwt_required()
@block_vendor()
def submit_leave_request():
    """
    POST /api/attendance/leave-request
    Ajukan izin/sakit
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data tidak boleh kosong'
            }), 400
        
        user_id = get_jwt_identity()
        leave_type = data.get('leave_type')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        reason = data.get('reason')
        medical_certificate = data.get('medical_certificate')
        emergency_contact = data.get('emergency_contact')
        emergency_phone = data.get('emergency_phone')
        
        # Validasi required fields
        if not all([leave_type, start_date, end_date, reason]):
            return jsonify({
                'success': False,
                'message': 'Semua field wajib diisi'
            }), 400
        
        # Convert string dates to date objects
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Format tanggal tidak valid (YYYY-MM-DD)'
            }), 400
        
        result = attendance_service.submit_leave_request(
            user_id=user_id,
            leave_type=leave_type,
            start_date=start_date_obj,
            end_date=end_date_obj,
            reason=reason,
            medical_certificate=medical_certificate,
            emergency_contact=emergency_contact,
            emergency_phone=emergency_phone
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error submit leave request: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/leave-request/<int:leave_id>/approve', methods=['PUT'])
@jwt_required()
@block_vendor()
def approve_leave_request(leave_id):
    """
    PUT /api/attendance/leave-request/<id>/approve
    Approve/reject izin
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data tidak boleh kosong'
            }), 400
        
        approver_id = get_jwt_identity()
        action = data.get('action')  # 'approve' or 'reject'
        rejection_reason = data.get('rejection_reason')
        
        if not action or action not in ['approve', 'reject']:
            return jsonify({
                'success': False,
                'message': 'Action harus approve atau reject'
            }), 400
        
        result = attendance_service.approve_leave_request(
            leave_id=leave_id,
            approver_id=approver_id,
            action=action,
            rejection_reason=rejection_reason
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error approve leave request: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/overtime-request', methods=['POST'])
@jwt_required()
@block_vendor()
def submit_overtime_request():
    """
    POST /api/attendance/overtime-request
    Ajukan overtime
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data tidak boleh kosong'
            }), 400
        
        user_id = get_jwt_identity()
        attendance_id = data.get('attendance_id')
        requested_hours = data.get('requested_hours')
        reason = data.get('reason')
        task_description = data.get('task_description')
        
        # Validasi required fields
        if not all([attendance_id, requested_hours, reason]):
            return jsonify({
                'success': False,
                'message': 'Attendance ID, jam overtime, dan alasan wajib diisi'
            }), 400
        
        try:
            requested_hours_float = float(requested_hours)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Jam overtime harus berupa angka'
            }), 400
        
        result = attendance_service.submit_overtime_request(
            user_id=user_id,
            attendance_id=int(attendance_id),
            requested_hours=requested_hours_float,
            reason=reason,
            task_description=task_description
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error submit overtime request: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/overtime-request/<int:overtime_id>/approve', methods=['PUT'])
@jwt_required()
@block_vendor()
def approve_overtime_request(overtime_id):
    """
    PUT /api/attendance/overtime-request/<id>/approve
    Approve/reject overtime
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Data tidak boleh kosong'
            }), 400
        
        approver_id = get_jwt_identity()
        action = data.get('action')  # 'approve' or 'reject'
        actual_hours = data.get('actual_hours')
        rejection_reason = data.get('rejection_reason')
        
        if not action or action not in ['approve', 'reject']:
            return jsonify({
                'success': False,
                'message': 'Action harus approve atau reject'
            }), 400
        
        # Convert actual_hours to float if provided
        actual_hours_float = None
        if actual_hours:
            try:
                actual_hours_float = float(actual_hours)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Jam actual harus berupa angka'
                }), 400
        
        result = attendance_service.approve_overtime_request(
            overtime_id=overtime_id,
            approver_id=approver_id,
            action=action,
            actual_hours=actual_hours_float,
            rejection_reason=rejection_reason
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error approve overtime request: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/report', methods=['GET'])
@jwt_required()
@block_vendor()
def generate_attendance_report():
    """
    GET /api/attendance/report
    Generate laporan absensi
    """
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        
        # Convert string dates to date objects
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Convert user_id to int if provided
        user_id_int = None
        if user_id:
            try:
                user_id_int = int(user_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'User ID tidak valid'
                }), 400
        
        records = attendance_service.get_all_attendance(
            start_date=start_date_obj,
            end_date=end_date_obj,
            user_id=user_id_int,
            status=status
        )
        
        return jsonify({
            'success': True,
            'data': records,
            'count': len(records),
            'period': {
                'start_date': start_date_obj.isoformat() if start_date_obj else None,
                'end_date': end_date_obj.isoformat() if end_date_obj else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error generate report: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/export/excel', methods=['GET'])
@jwt_required()
@block_vendor()
def export_excel():
    """
    GET /api/attendance/export/excel
    Export laporan ke Excel
    """
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        
        # Convert string dates to date objects
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Convert user_id to int if provided
        user_id_int = None
        if user_id:
            try:
                user_id_int = int(user_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'User ID tidak valid'
                }), 400
        
        records = attendance_service.get_all_attendance(
            start_date=start_date_obj,
            end_date=end_date_obj,
            user_id=user_id_int,
            status=status
        )
        
        # Generate Excel file
        excel_file = attendance_service.export_to_excel(records)
        
        # Generate filename
        filename = f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Error export Excel: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/export/pdf', methods=['GET'])
@jwt_required()
@block_vendor()
def export_pdf():
    """
    GET /api/attendance/export/pdf
    Export laporan ke PDF
    """
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        
        # Convert string dates to date objects
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Convert user_id to int if provided
        user_id_int = None
        if user_id:
            try:
                user_id_int = int(user_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'User ID tidak valid'
                }), 400
        
        records = attendance_service.get_all_attendance(
            start_date=start_date_obj,
            end_date=end_date_obj,
            user_id=user_id_int,
            status=status
        )
        
        # Generate PDF file
        pdf_file = attendance_service.export_to_pdf(records)
        
        # Generate filename
        filename = f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Error export PDF: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/dashboard-stats', methods=['GET'])
@jwt_required()
@block_vendor()
def get_dashboard_stats():
    """
    GET /api/attendance/dashboard-stats
    Stats untuk dashboard
    """
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id')
        
        # Convert string dates to date objects
        start_date_obj = None
        end_date_obj = None
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Convert user_id to int if provided
        user_id_int = None
        if user_id:
            try:
                user_id_int = int(user_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'User ID tidak valid'
                }), 400
        
        stats = attendance_service.get_dashboard_stats(
            user_id=user_id_int,
            start_date=start_date_obj,
            end_date=end_date_obj
        )
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error get dashboard stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

# ===== Daily Task Analytics Aliases (to ensure routes are available) =====
@attendance_bp.route('/tasks/statistics', methods=['GET'])
@jwt_required()
@block_vendor()
def tasks_statistics_alias():
    """
    GET /api/attendance/tasks/statistics
    Alias ke DailyTaskController.get_statistics untuk kompatibilitas frontend
    """
    controller = DailyTaskController()
    return controller.get_statistics()

@attendance_bp.route('/tasks/department-stats', methods=['GET'])
@jwt_required()
@block_vendor()
def tasks_department_stats_alias():
    """
    GET /api/attendance/tasks/department-stats
    Minimal endpoint agar tidak 404. Kembalikan array kosong jika tidak tersedia.
    """
    try:
        return jsonify({
            'success': True,
            'data': []
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/tasks/user-stats', methods=['GET'])
@jwt_required()
@block_vendor()
def tasks_user_stats_alias():
    """
    GET /api/attendance/tasks/user-stats
    Minimal endpoint agar tidak 404. Kembalikan array kosong jika tidak tersedia.
    """
    try:
        return jsonify({
            'success': True,
            'data': []
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/leave-requests', methods=['GET'])
@jwt_required()
@block_vendor()
def get_leave_requests():
    """
    GET /api/attendance/leave-requests
    Ambil daftar leave requests dengan pagination
    """
    try:
        from models.attendance_models import AttendanceLeave
        
        # Parse query parameters
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        leave_type = request.args.get('leave_type')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        query = AttendanceLeave.query
        
        # Get current user ID
        current_user_id = get_jwt_identity()
        
        # Jika tidak ada user_id yang di-spesifikasi, default ke current user
        if not user_id:
            from models.knowledge_base import User
            current_user = User.query.get(current_user_id)
            if current_user and current_user.role != 'admin':
                user_id = str(current_user_id)
        
        if user_id:
            try:
                query = query.filter(AttendanceLeave.user_id == int(user_id))
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'User ID tidak valid'
                }), 400
        
        if status:
            query = query.filter(AttendanceLeave.status == status)
        
        if leave_type:
            query = query.filter(AttendanceLeave.leave_type == leave_type)
        
        # Hitung total
        total = query.count()
        
        # Apply pagination
        leave_requests = query.order_by(AttendanceLeave.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        return jsonify({
            'success': True,
            'data': {
                'items': [request.to_dict() for request in leave_requests],
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page if total > 0 else 0
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error get leave requests: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500

@attendance_bp.route('/overtime-requests', methods=['GET'])
@jwt_required()
@block_vendor()
def get_overtime_requests():
    """
    GET /api/attendance/overtime-requests
    Ambil daftar overtime requests
    """
    try:
        from models.attendance_models import OvertimeRequest
        
        # Parse query parameters
        user_id = request.args.get('user_id')
        status = request.args.get('status')
        
        query = OvertimeRequest.query
        
        if user_id:
            try:
                query = query.filter(OvertimeRequest.user_id == int(user_id))
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'User ID tidak valid'
                }), 400
        
        if status:
            query = query.filter(OvertimeRequest.status == status)
        
        overtime_requests = query.order_by(OvertimeRequest.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [request.to_dict() for request in overtime_requests],
            'count': len(overtime_requests)
        }), 200
        
    except Exception as e:
        logger.error(f"Error get overtime requests: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }), 500



