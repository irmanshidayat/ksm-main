#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mobil Routes untuk KSM Main Backend
API routes untuk mobil management system
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.mobil_service import MobilService
from utils.response_standardizer import APIResponse
import logging
from datetime import datetime, date
from typing import Dict, Any

# Create blueprint
mobil_bp = Blueprint('mobil', __name__, url_prefix='/api/mobil')

# Initialize service
mobil_service = MobilService()

# Setup logging
logger = logging.getLogger(__name__)

@mobil_bp.route('/mobils', methods=['GET'])
@jwt_required()
def get_all_mobils():
    """Get all mobil data with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        search = request.args.get('search')
        status = request.args.get('status')
        
        result = mobil_service.get_all_mobils(page=page, per_page=per_page, search=search, status=status)
        return APIResponse.success(result, "Mobil data retrieved successfully")
    except Exception as e:
        logger.error(f"Error getting all mobils: {e}")
        return APIResponse.error(f"Failed to get mobil data: {str(e)}")

@mobil_bp.route('/mobils/<int:mobil_id>', methods=['GET'])
@jwt_required()
def get_mobil_by_id(mobil_id):
    """Get mobil by ID"""
    try:
        mobil = mobil_service.get_mobil_by_id(mobil_id)
        if not mobil:
            return APIResponse.error("Mobil not found", status_code=404)
        
        return APIResponse.success(mobil, "Mobil data retrieved successfully")
    except Exception as e:
        logger.error(f"Error getting mobil by ID {mobil_id}: {e}")
        return APIResponse.error(f"Failed to get mobil data: {str(e)}")

@mobil_bp.route('/mobils/<int:mobil_id>', methods=['DELETE'])
@jwt_required()
def delete_mobil(mobil_id):
    """Delete mobil by ID"""
    try:
        result = mobil_service.delete_mobil(mobil_id)
        
        if result['success']:
            return APIResponse.success(result, "Mobil berhasil dihapus")
        else:
            return APIResponse.error(result['message'], status_code=400)
            
    except Exception as e:
        logger.error(f"Error deleting mobil {mobil_id}: {e}")
        return APIResponse.error(f"Failed to delete mobil: {str(e)}")

@mobil_bp.route('/mobils', methods=['POST'])
@jwt_required()
def create_mobil():
    """Create new mobil"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['nama', 'plat_nomor']
        for field in required_fields:
            if field not in data or not data[field]:
                return APIResponse.error(f"Field '{field}' is required", status_code=400)
        
        # Check if plat_nomor already exists
        existing_mobil = mobil_service.get_mobil_by_plat_nomor(data['plat_nomor'])
        if existing_mobil:
            return APIResponse.error("Plat nomor sudah digunakan", status_code=400)
        
        result = mobil_service.create_mobil(data)
        return APIResponse.success(result, "Mobil berhasil ditambahkan")
        
    except Exception as e:
        logger.error(f"Error creating mobil: {e}")
        return APIResponse.error(f"Failed to create mobil: {str(e)}")

@mobil_bp.route('/calendar', methods=['GET'])
@jwt_required()
def get_calendar():
    """Get mobil calendar data"""
    try:
        month = request.args.get('month')
        year = request.args.get('year', type=int)
        view = request.args.get('view', 'month')
        
        # Parse month and year parameters
        from datetime import datetime
        now = datetime.now()
        
        # If year is provided, construct month string
        if year and month:
            # Convert month to int if it's a string
            try:
                month_int = int(month) if month else now.month
                month_str = f"{year}-{month_int:02d}"
            except (ValueError, TypeError):
                # If month is already in YYYY-MM format, use it directly
                if month and '-' in str(month):
                    month_str = month
                else:
                    # Default to current month
                    month_str = f"{now.year}-{now.month:02d}"
        elif month:
            # Check if month is in YYYY-MM format
            if '-' in str(month):
                month_str = month
            else:
                # Assume it's just month number, use current year
                try:
                    month_int = int(month)
                    month_str = f"{now.year}-{month_int:02d}"
                except (ValueError, TypeError):
                    month_str = f"{now.year}-{now.month:02d}"
        else:
            # Default to current month
            month_str = f"{now.year}-{now.month:02d}"
        
        logger.info(f"📅 Calendar request: month={month}, year={year}, month_str={month_str}, view={view}")
        
        calendar_data = mobil_service.get_calendar_data(month_str, view)
        
        # Transform calendar data to match frontend expectations
        # Frontend expects: { mobil_id: { date: [reservations] } }
        transformed_data = {}
        
        for mobil in calendar_data.get('mobils', []):
            mobil_id = mobil['id']
            transformed_data[mobil_id] = {}
            
            for availability in mobil.get('availability', []):
                date_str = availability['date']
                # Gunakan all_requests jika ada (berisi semua reservasi untuk tanggal ini)
                reservations = availability.get('all_requests', [])
                if not reservations and availability.get('request'):
                    reservations = [availability['request']]
                
                # Tambahkan semua reservasi (semua status) untuk tanggal ini
                if reservations:
                    if date_str not in transformed_data[mobil_id]:
                        transformed_data[mobil_id][date_str] = []
                    # Tambahkan semua reservasi untuk tanggal ini
                    for reservation in reservations:
                        # Pastikan reservasi memiliki informasi lengkap (user, status, dll)
                        # Cek duplikasi berdasarkan ID reservasi
                        existing_ids = [r.get('id') for r in transformed_data[mobil_id][date_str] if r.get('id')]
                        if reservation.get('id') not in existing_ids:
                            transformed_data[mobil_id][date_str].append(reservation)
        
        logger.info(f"✅ Calendar data retrieved: {len(transformed_data)} mobils, month={month_str}")
        return APIResponse.success(transformed_data, "Calendar data retrieved successfully")
    except ValueError as e:
        logger.error(f"❌ ValueError getting calendar data: {e}")
        return APIResponse.error(f"Invalid date format: {str(e)}", status_code=400)
    except Exception as e:
        logger.error(f"❌ Error getting calendar data: {e}", exc_info=True)
        return APIResponse.error(f"Failed to get calendar data: {str(e)}", status_code=500)

@mobil_bp.route('/request', methods=['POST'])
@jwt_required()
def create_request():
    """Create new mobil request"""
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Debug logging
        logger.info(f"🚀 Create request received: user_id={user_id}, data={data}")
        
        # Validate required fields
        required_fields = ['mobil_id', 'tanggal_mulai', 'tanggal_selesai']
        for field in required_fields:
            if field not in data:
                logger.warning(f"❌ Missing required field: {field}")
                return APIResponse.error(f"Field '{field}' is required", status_code=400)
        
        # Validate date format
        try:
            start_date = datetime.strptime(data['tanggal_mulai'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['tanggal_selesai'], '%Y-%m-%d').date()
            logger.info(f"📅 Parsed request dates: start_date={start_date}, end_date={end_date}")
        except ValueError as e:
            logger.error(f"❌ Date parsing error: {e}")
            return APIResponse.error("Invalid date format. Use YYYY-MM-DD", status_code=400)
        
        # Validate date range
        if start_date > end_date:
            logger.warning(f"❌ Invalid date range: start_date={start_date} > end_date={end_date}")
            return APIResponse.error("Start date cannot be after end date", status_code=400)
        
        if start_date < date.today():
            logger.warning(f"❌ Past date request: start_date={start_date} < today={date.today()}")
            return APIResponse.error("Cannot request for past dates", status_code=400)
        
        result = mobil_service.create_request(user_id, data)
        logger.info(f"✅ Request created successfully: result={result}")
        return APIResponse.success(result, "Request processed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error creating request: {e}")
        return APIResponse.error(f"Failed to create request: {str(e)}")

@mobil_bp.route('/requests', methods=['POST'])
@jwt_required()
def create_request_plural():
    """Create new mobil request - alias untuk kompatibilitas frontend"""
    # Redirect ke endpoint yang sudah ada
    return create_request()

@mobil_bp.route('/requests', methods=['GET'])
@jwt_required()
def get_all_requests():
    """Get all mobil requests with pagination and filters"""
    try:
        # TODO: Add admin check here if needed
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        mobil_id = request.args.get('mobil_id', type=int)
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        result = mobil_service.get_all_requests(
            page=page, 
            per_page=per_page, 
            mobil_id=mobil_id,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        return APIResponse.success(result, "All requests retrieved successfully")
    except Exception as e:
        logger.error(f"Error getting all requests: {e}")
        return APIResponse.error(f"Failed to get all requests: {str(e)}")

@mobil_bp.route('/requests/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_requests(user_id):
    """Get user's mobil requests with pagination"""
    try:
        # Check if user is requesting their own data or is admin
        current_user_id = get_jwt_identity()
        if current_user_id != user_id:
            # TODO: Add admin check here if needed
            pass
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        result = mobil_service.get_user_requests(user_id, page=page, per_page=per_page)
        return APIResponse.success(result, "User requests retrieved successfully")
    except Exception as e:
        logger.error(f"Error getting user requests: {e}")
        return APIResponse.error(f"Failed to get user requests: {str(e)}")

@mobil_bp.route('/requests/my', methods=['GET'])
@jwt_required()
def get_my_requests():
    """Get current user's mobil requests with pagination"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        result = mobil_service.get_user_requests(user_id, page=page, per_page=per_page)
        return APIResponse.success(result, "My requests retrieved successfully")
    except Exception as e:
        logger.error(f"Error getting my requests: {e}")
        return APIResponse.error(f"Failed to get my requests: {str(e)}")

@mobil_bp.route('/request/<int:request_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_request(request_id):
    """Cancel mobil request"""
    try:
        user_id = get_jwt_identity()
        result = mobil_service.cancel_request(request_id, user_id)
        
        if result['success']:
            return APIResponse.success(result, "Request cancelled successfully")
        else:
            return APIResponse.error(result['message'], status_code=400)
            
    except Exception as e:
        logger.error(f"Error cancelling request: {e}")
        return APIResponse.error(f"Failed to cancel request: {str(e)}")

@mobil_bp.route('/backup-options', methods=['GET'])
@jwt_required()
def get_backup_options():
    """Get backup mobil options"""
    try:
        mobil_id = request.args.get('mobil_id', type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not all([mobil_id, start_date_str, end_date_str]):
            return APIResponse.error("mobil_id, start_date, and end_date are required", status_code=400)
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return APIResponse.error("Invalid date format. Use YYYY-MM-DD", status_code=400)
        
        backup_options = mobil_service.get_backup_options(mobil_id, start_date, end_date)
        return APIResponse.success(backup_options, "Backup options retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting backup options: {e}")
        return APIResponse.error(f"Failed to get backup options: {str(e)}")

@mobil_bp.route('/availability', methods=['GET'])
@jwt_required()
def check_availability():
    """Check mobil availability for date range"""
    try:
        mobil_id = request.args.get('mobil_id', type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        jam_mulai = request.args.get('jam_mulai')
        jam_selesai = request.args.get('jam_selesai')
        
        # Debug logging
        logger.info(f"🔍 Availability check request: mobil_id={mobil_id}, start_date={start_date_str}, end_date={end_date_str}, jam_mulai={jam_mulai}, jam_selesai={jam_selesai}")
        
        if not all([mobil_id, start_date_str, end_date_str]):
            logger.warning(f"❌ Missing required parameters: mobil_id={mobil_id}, start_date={start_date_str}, end_date={end_date_str}")
            return APIResponse.error("mobil_id, start_date, and end_date are required", status_code=400)
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            logger.info(f"📅 Parsed dates: start_date={start_date}, end_date={end_date}")
        except ValueError as e:
            logger.error(f"❌ Date parsing error: {e}")
            return APIResponse.error("Invalid date format. Use YYYY-MM-DD", status_code=400)
        
        is_available = mobil_service._check_availability(mobil_id, start_date, end_date, jam_mulai, jam_selesai)
        
        # Get conflicting reservations if not available
        conflicting_reservations = []
        if not is_available:
            from models.mobil_models import MobilRequest, RequestStatus
            conflicting_requests = MobilRequest.query.filter(
                and_(
                    MobilRequest.mobil_id == mobil_id,
                    MobilRequest.status == RequestStatus.ACTIVE,
                    or_(
                        and_(MobilRequest.tanggal_mulai <= end_date, MobilRequest.tanggal_selesai >= start_date)
                    )
                )
            ).all()
            conflicting_reservations = [mobil_service._request_to_dict(req) for req in conflicting_requests]
        
        logger.info(f"✅ Availability result: mobil_id={mobil_id}, available={is_available}")
        
        return APIResponse.success({
            'available': is_available,
            'mobil_id': mobil_id,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'jam_mulai': jam_mulai,
            'jam_selesai': jam_selesai,
            'conflicting_reservations': conflicting_reservations
        }, "Availability checked successfully")
        
    except Exception as e:
        logger.error(f"❌ Error checking availability: {e}")
        return APIResponse.error(f"Failed to check availability: {str(e)}")

@mobil_bp.route('/conflicts', methods=['GET'])
@jwt_required()
def get_conflicts():
    """Get conflicting requests for mobil and date range"""
    try:
        mobil_id = request.args.get('mobil_id', type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not all([mobil_id, start_date_str, end_date_str]):
            return APIResponse.error("mobil_id, start_date, and end_date are required", status_code=400)
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return APIResponse.error("Invalid date format. Use YYYY-MM-DD", status_code=400)
        
        # Get calendar data to find conflicts
        calendar_data = mobil_service.get_calendar_data()
        conflicts = []
        
        for mobil in calendar_data['mobils']:
            if mobil['id'] == mobil_id:
                for availability in mobil['availability']:
                    if not availability['available'] and availability['request']:
                        conflicts.append(availability['request'])
                break
        
        return APIResponse.success(conflicts, "Conflicts retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting conflicts: {e}")
        return APIResponse.error(f"Failed to get conflicts: {str(e)}")

@mobil_bp.route('/debug/requests', methods=['GET'])
@jwt_required()
def debug_requests():
    """Debug endpoint to see all requests"""
    try:
        from models.mobil_models import MobilRequest, RequestStatus
        
        # Get all active requests
        requests = MobilRequest.query.filter_by(status=RequestStatus.ACTIVE).all()
        
        debug_data = []
        for req in requests:
            debug_data.append({
                'id': req.id,
                'user_id': req.user_id,
                'mobil_id': req.mobil_id,
                'tanggal_mulai': req.tanggal_mulai.isoformat(),
                'tanggal_selesai': req.tanggal_selesai.isoformat(),
                'status': req.status.value,
                'created_at': req.created_at.isoformat() if req.created_at else None
            })
        
        logger.info(f"🔍 Debug requests: Found {len(debug_data)} active requests")
        
        return APIResponse.success({
            'total_requests': len(debug_data),
            'requests': debug_data
        }, "Debug requests retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting debug requests: {e}")
        return APIResponse.error(f"Failed to get debug requests: {str(e)}")

@mobil_bp.route('/debug/calendar', methods=['GET'])
@jwt_required()
def debug_calendar():
    """Debug endpoint to see calendar data and compare with requests"""
    try:
        from models.mobil_models import MobilRequest, RequestStatus, Mobil, MobilStatus
        from datetime import datetime, date, timedelta
        from sqlalchemy import and_, or_
        
        month = request.args.get('month', datetime.now().strftime('%Y-%m'))
        mobil_id = request.args.get('mobil_id', type=int)
        
        # Parse month
        year, month_num = map(int, month.split('-'))
        start_date = date(year, month_num, 1)
        
        if month_num == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month_num + 1, 1) - timedelta(days=1)
        
        # Get all active requests
        requests_query = MobilRequest.query.filter(
            and_(
                MobilRequest.status == RequestStatus.ACTIVE,
                or_(
                    and_(MobilRequest.tanggal_mulai <= end_date, MobilRequest.tanggal_selesai >= start_date)
                )
            )
        )
        
        if mobil_id:
            requests_query = requests_query.filter(MobilRequest.mobil_id == mobil_id)
        
        requests = requests_query.all()
        
        # Get mobils
        mobils_query = Mobil.query.filter_by(status=MobilStatus.ACTIVE)
        if mobil_id:
            mobils_query = mobils_query.filter(Mobil.id == mobil_id)
        
        mobils = mobils_query.all()
        
        debug_data = {
            'month': month,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'mobil_id_filter': mobil_id,
            'requests': [],
            'mobils': [],
            'availability': {}
        }
        
        # Process requests
        for req in requests:
            debug_data['requests'].append({
                'id': req.id,
                'user_id': req.user_id,
                'mobil_id': req.mobil_id,
                'tanggal_mulai': req.tanggal_mulai.isoformat(),
                'tanggal_selesai': req.tanggal_selesai.isoformat(),
                'status': req.status.value,
                'created_at': req.created_at.isoformat() if req.created_at else None
            })
        
        # Process mobils and availability
        for mobil in mobils:
            mobil_data = {
                'id': mobil.id,
                'nama': mobil.nama,
                'plat_nomor': mobil.plat_nomor,
                'availability': []
            }
            
            # Generate availability for each day
            current_date = start_date
            while current_date <= end_date:
                is_available = True
                conflicting_request = None
                
                for req in requests:
                    if (req.mobil_id == mobil.id and 
                        req.status == RequestStatus.ACTIVE and
                        req.tanggal_mulai <= current_date <= req.tanggal_selesai):
                        is_available = False
                        conflicting_request = req
                        break
                
                mobil_data['availability'].append({
                    'date': current_date.isoformat(),
                    'available': is_available,
                    'request_id': conflicting_request.id if conflicting_request else None,
                    'request_dates': {
                        'tanggal_mulai': conflicting_request.tanggal_mulai.isoformat() if conflicting_request else None,
                        'tanggal_selesai': conflicting_request.tanggal_selesai.isoformat() if conflicting_request else None
                    } if conflicting_request else None
                })
                
                current_date += timedelta(days=1)
            
            debug_data['mobils'].append(mobil_data)
        
        logger.info(f"🔍 Debug calendar: month={month}, mobil_id={mobil_id}, requests={len(requests)}, mobils={len(mobils)}")
        
        return APIResponse.success(debug_data, "Debug calendar data retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting debug calendar: {e}")
        return APIResponse.error(f"Failed to get debug calendar: {str(e)}")

@mobil_bp.route('/recurring-preview', methods=['POST'])
@jwt_required()
def preview_recurring():
    """Preview recurring request dates"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['start_date', 'end_date', 'pattern', 'recurring_end_date']
        for field in required_fields:
            if field not in data:
                return APIResponse.error(f"Field '{field}' is required", status_code=400)
        
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            recurring_end_date = datetime.strptime(data['recurring_end_date'], '%Y-%m-%d').date()
        except ValueError:
            return APIResponse.error("Invalid date format. Use YYYY-MM-DD", status_code=400)
        
        # Generate recurring dates
        recurring_dates = mobil_service._generate_recurring_dates(
            start_date, end_date, data['pattern'], recurring_end_date
        )
        
        return APIResponse.success({
            'dates': recurring_dates,
            'total_occurrences': len(recurring_dates)
        }, "Recurring preview generated successfully")
        
    except Exception as e:
        logger.error(f"Error generating recurring preview: {e}")
        return APIResponse.error(f"Failed to generate recurring preview: {str(e)}")

@mobil_bp.route('/waiting-list', methods=['GET'])
@jwt_required()
def get_waiting_list():
    """Get waiting list for current user"""
    try:
        user_id = get_jwt_identity()
        
        # Get waiting list from service
        from models.mobil_models import WaitingList, WaitingListStatus
        from config.database import db
        
        waiting_items = db.session.query(WaitingList).filter(
            WaitingList.user_id == user_id,
            WaitingList.status == WaitingListStatus.WAITING
        ).order_by(WaitingList.created_at.desc()).all()
        
        waiting_list = []
        for item in waiting_items:
            waiting_list.append({
                'id': item.id,
                'mobil_id': item.mobil_id,
                'tanggal_mulai': item.tanggal_mulai.isoformat(),
                'tanggal_selesai': item.tanggal_selesai.isoformat(),
                'priority': item.priority,
                'status': item.status.value,
                'created_at': item.created_at.isoformat()
            })
        
        return APIResponse.success(waiting_list, "Waiting list retrieved successfully")
        
    except Exception as e:
        logger.error(f"Error getting waiting list: {e}")
        return APIResponse.error(f"Failed to get waiting list: {str(e)}")

@mobil_bp.route('/waiting-list/<int:waiting_id>/remove', methods=['DELETE'])
@jwt_required()
def remove_from_waiting_list(waiting_id):
    """Remove item from waiting list"""
    try:
        user_id = get_jwt_identity()
        
        from models.mobil_models import WaitingList
        from config.database import db
        
        waiting_item = db.session.query(WaitingList).filter(
            WaitingList.id == waiting_id,
            WaitingList.user_id == user_id
        ).first()
        
        if not waiting_item:
            return APIResponse.error("Waiting list item not found", status_code=404)
        
        db.session.delete(waiting_item)
        db.session.commit()
        
        return APIResponse.success({}, "Item removed from waiting list successfully")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing from waiting list: {e}")
        return APIResponse.error(f"Failed to remove from waiting list: {str(e)}")

# Health check endpoint dihapus - sekarang menggunakan unified_health_controller
