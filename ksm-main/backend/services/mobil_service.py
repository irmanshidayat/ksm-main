#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mobil Service untuk KSM Main Backend
Service layer untuk business logic mobil management
"""

from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, or_, func
from config.database import db
from models.mobil_models import Mobil, MobilRequest, WaitingList, MobilBackup, MobilUsageLog
from models.mobil_models import MobilStatus, RequestStatus, RecurringPattern, WaitingListStatus
from models.knowledge_base import User
from datetime import datetime, date, timedelta
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class MobilService:
    def __init__(self):
        self.db = db
    
    def get_all_mobils(self, page: int = 1, per_page: int = 100, search: str = None, status: str = None) -> Dict[str, Any]:
        """Get all mobil data with pagination"""
        try:
            query = Mobil.query
            
            # Filter by status
            if status:
                try:
                    status_enum = MobilStatus(status)
                    query = query.filter_by(status=status_enum)
                except ValueError:
                    pass
            else:
                # Default: show active mobils
                query = query.filter_by(status=MobilStatus.ACTIVE)
            
            # Search filter
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Mobil.nama.ilike(search_term),
                        Mobil.plat_nomor.ilike(search_term)
                    )
                )
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            mobils = query.order_by(Mobil.created_at.desc()).offset(offset).limit(per_page).all()
            
            # Calculate pages
            pages = (total + per_page - 1) // per_page if per_page > 0 else 1
            
            return {
                'items': [self._mobil_to_dict(mobil) for mobil in mobils],
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting all mobils: {e}")
            raise
    
    def get_mobil_by_id(self, mobil_id: int) -> Optional[Dict[str, Any]]:
        """Get mobil by ID"""
        try:
            mobil = Mobil.query.get(mobil_id)
            return self._mobil_to_dict(mobil) if mobil else None
        except Exception as e:
            logger.error(f"Error getting mobil by ID {mobil_id}: {e}")
            raise
    
    def get_mobil_by_plat_nomor(self, plat_nomor: str) -> Optional[Dict[str, Any]]:
        """Get mobil by plat nomor"""
        try:
            mobil = Mobil.query.filter_by(plat_nomor=plat_nomor).first()
            return self._mobil_to_dict(mobil) if mobil else None
        except Exception as e:
            logger.error(f"Error getting mobil by plat nomor {plat_nomor}: {e}")
            raise
    
    def create_mobil(self, mobil_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new mobil"""
        try:
            # Create new mobil
            mobil = Mobil(
                nama=mobil_data['nama'],
                plat_nomor=mobil_data['plat_nomor'],
                status=MobilStatus(mobil_data.get('status', 'active')),
                is_backup=mobil_data.get('is_backup', False),
                backup_for_mobil_id=mobil_data.get('backup_for_mobil_id'),
                priority_score=mobil_data.get('priority_score', 0)
            )
            
            self.db.session.add(mobil)
            self.db.session.commit()
            
            logger.info(f"✅ Mobil created: {mobil.nama} ({mobil.plat_nomor})")
            
            return {
                'success': True,
                'message': 'Mobil berhasil ditambahkan',
                'mobil': self._mobil_to_dict(mobil)
            }
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error creating mobil: {e}")
            raise
    
    def delete_mobil(self, mobil_id: int) -> Dict[str, Any]:
        """Delete mobil by ID"""
        try:
            # Check if mobil exists
            mobil = Mobil.query.get(mobil_id)
            if not mobil:
                return {'success': False, 'message': 'Mobil tidak ditemukan'}
            
            # Check if mobil has active requests
            active_requests = MobilRequest.query.filter(
                and_(
                    MobilRequest.mobil_id == mobil_id,
                    MobilRequest.status == RequestStatus.ACTIVE
                )
            ).count()
            
            if active_requests > 0:
                return {
                    'success': False, 
                    'message': f'Tidak dapat menghapus mobil karena masih ada {active_requests} request aktif. Batalkan semua request terlebih dahulu.'
                }
            
            # Check if mobil is used as backup for other mobils
            backup_relations = MobilBackup.query.filter_by(mobil_backup_id=mobil_id).count()
            if backup_relations > 0:
                return {
                    'success': False,
                    'message': 'Tidak dapat menghapus mobil karena masih digunakan sebagai backup mobil lain'
                }
            
            # Soft delete by changing status to inactive
            mobil.status = MobilStatus.INACTIVE
            mobil.updated_at = datetime.utcnow()
            
            self.db.session.commit()
            
            logger.info(f"✅ Mobil deleted (soft): {mobil.nama} ({mobil.plat_nomor})")
            
            return {
                'success': True,
                'message': 'Mobil berhasil dihapus',
                'mobil': self._mobil_to_dict(mobil)
            }
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error deleting mobil {mobil_id}: {e}")
            raise
    
    def get_calendar_data(self, month: str = None, view: str = 'month') -> Dict[str, Any]:
        """Get calendar data for mobil availability"""
        try:
            if not month:
                month = datetime.now().strftime('%Y-%m')
            
            # Parse month - validate format
            try:
                parts = month.split('-')
                if len(parts) != 2:
                    raise ValueError(f"Invalid month format: {month}. Expected YYYY-MM")
                year, month_num = map(int, parts)
                
                # Validate month range
                if month_num < 1 or month_num > 12:
                    raise ValueError(f"Invalid month number: {month_num}. Must be between 1-12")
                
                # Validate year range (reasonable range)
                if year < 2000 or year > 2100:
                    raise ValueError(f"Invalid year: {year}. Must be between 2000-2100")
                    
            except ValueError as e:
                logger.error(f"❌ Error parsing month '{month}': {e}")
                raise ValueError(f"Invalid month format: {month}. Use YYYY-MM format (e.g., 2025-11)")
            
            start_date = date(year, month_num, 1)
            
            if month_num == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month_num + 1, 1) - timedelta(days=1)
            
            # Get all mobils
            mobils = Mobil.query.filter_by(status=MobilStatus.ACTIVE).all()
            
            # Get all requests for the month (semua status untuk ditampilkan di calendar)
            # Filter berdasarkan tanggal overlap dengan bulan yang diminta
            requests = MobilRequest.query.filter(
                or_(
                    and_(MobilRequest.tanggal_mulai <= end_date, MobilRequest.tanggal_selesai >= start_date)
                )
            ).order_by(MobilRequest.tanggal_mulai.asc(), MobilRequest.created_at.asc()).all()
            
            # Build calendar data
            calendar_data = {
                'month': month,
                'view': view,
                'mobils': [],
                'requests': []
            }
            
            for mobil in mobils:
                mobil_data = self._mobil_to_dict(mobil)
                mobil_data['availability'] = self._get_mobil_availability(mobil.id, start_date, end_date, requests)
                calendar_data['mobils'].append(mobil_data)
            
            for request in requests:
                calendar_data['requests'].append(self._request_to_dict(request))
            
            return calendar_data
            
        except Exception as e:
            logger.error(f"Error getting calendar data: {e}")
            raise
    
    def create_request(self, user_id: int, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new mobil request"""
        try:
            logger.info(f"🚀 Creating request: user_id={user_id}, request_data={request_data}")
            
            # Validate request data
            mobil_id = request_data.get('mobil_id')
            tanggal_mulai = datetime.strptime(request_data.get('tanggal_mulai'), '%Y-%m-%d').date()
            tanggal_selesai = datetime.strptime(request_data.get('tanggal_selesai'), '%Y-%m-%d').date()
            jam_mulai = request_data.get('jam_mulai', '08:00')
            jam_selesai = request_data.get('jam_selesai', '17:00')
            keperluan = request_data.get('keperluan', '')
            is_recurring = request_data.get('is_recurring', False)
            recurring_pattern = request_data.get('recurring_pattern')
            recurring_end_date = request_data.get('recurring_end_date')
            
            logger.info(f"📋 Request details: mobil_id={mobil_id}, tanggal_mulai={tanggal_mulai}, tanggal_selesai={tanggal_selesai}, is_recurring={is_recurring}")
            
            if recurring_end_date:
                recurring_end_date = datetime.strptime(recurring_end_date, '%Y-%m-%d').date()
            
            # Check availability
            logger.info(f"🔍 Checking availability before creating request...")
            if not self._check_availability(mobil_id, tanggal_mulai, tanggal_selesai, jam_mulai, jam_selesai):
                logger.warning(f"⚠️ Mobil {mobil_id} not available, looking for backup...")
                # Try to find backup mobil
                backup_mobil = self._find_backup_mobil(mobil_id, tanggal_mulai, tanggal_selesai)
                if backup_mobil:
                    logger.info(f"🔄 Found backup mobil: {backup_mobil['id']}")
                    mobil_id = backup_mobil['id']
                else:
                    logger.warning(f"❌ No backup available, adding to waiting list")
                    # Add to waiting list
                    self._add_to_waiting_list(user_id, mobil_id, tanggal_mulai, tanggal_selesai)
                    return {
                        'success': False,
                        'message': 'Mobil tidak tersedia, telah ditambahkan ke waiting list',
                        'waiting_list': True
                    }
            
            # Create request
            if is_recurring and recurring_pattern and recurring_end_date:
                logger.info(f"🔄 Creating recurring request...")
                return self._create_recurring_request(
                    user_id, mobil_id, tanggal_mulai, tanggal_selesai, 
                    keperluan, recurring_pattern, recurring_end_date
                )
            else:
                logger.info(f"📝 Creating single request...")
                return self._create_single_request(
                    user_id, mobil_id, tanggal_mulai, tanggal_selesai, jam_mulai, jam_selesai, keperluan
                )
                
        except Exception as e:
            logger.error(f"❌ Error creating request: {e}")
            raise
    
    def get_user_requests(self, user_id: int, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Get user's mobil requests with pagination"""
        try:
            query = MobilRequest.query.filter_by(user_id=user_id)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            requests = query.order_by(MobilRequest.created_at.desc()).offset(offset).limit(per_page).all()
            
            # Calculate pages
            pages = (total + per_page - 1) // per_page if per_page > 0 else 1
            
            return {
                'items': [self._request_to_dict(request) for request in requests],
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting user requests: {e}")
            raise
    
    def get_all_requests(self, page: int = 1, per_page: int = 10, mobil_id: int = None, status: str = None, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get all mobil requests with pagination"""
        try:
            query = MobilRequest.query
            
            # Filter by mobil_id
            if mobil_id:
                query = query.filter_by(mobil_id=mobil_id)
            
            # Filter by status
            if status:
                try:
                    status_enum = RequestStatus(status)
                    query = query.filter_by(status=status_enum)
                except ValueError:
                    pass
            
            # Filter by date range
            if start_date:
                try:
                    start = datetime.strptime(start_date, '%Y-%m-%d').date()
                    query = query.filter(MobilRequest.tanggal_mulai >= start)
                except ValueError:
                    pass
            
            if end_date:
                try:
                    end = datetime.strptime(end_date, '%Y-%m-%d').date()
                    query = query.filter(MobilRequest.tanggal_selesai <= end)
                except ValueError:
                    pass
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            requests = query.order_by(MobilRequest.created_at.desc()).offset(offset).limit(per_page).all()
            
            # Calculate pages
            pages = (total + per_page - 1) // per_page if per_page > 0 else 1
            
            # Include mobil and user info
            requests_data = []
            for request in requests:
                request_dict = self._request_to_dict(request)
                # Get mobil info
                mobil = Mobil.query.get(request.mobil_id)
                if mobil:
                    request_dict['mobil'] = self._mobil_to_dict(mobil)
                requests_data.append(request_dict)
            
            return {
                'items': requests_data,
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages
            }
        except Exception as e:
            logger.error(f"Error getting all requests: {e}")
            raise
    
    def cancel_request(self, request_id: int, user_id: int) -> Dict[str, Any]:
        """Cancel mobil request"""
        try:
            request = MobilRequest.query.filter_by(id=request_id, user_id=user_id).first()
            if not request:
                return {'success': False, 'message': 'Request tidak ditemukan'}
            
            request.status = RequestStatus.CANCELLED
            request.updated_at = datetime.utcnow()
            
            # Log the action
            self._log_usage(request.mobil_id, user_id, request_id, 'cancel')
            
            # Check waiting list for this mobil
            self._check_waiting_list(request.mobil_id, request.tanggal_mulai, request.tanggal_selesai)
            
            self.db.session.commit()
            
            return {'success': True, 'message': 'Request berhasil dibatalkan'}
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error cancelling request: {e}")
            raise
    
    def get_backup_options(self, mobil_id: int, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Get backup mobil options"""
        try:
            backup_mobils = MobilBackup.query.filter_by(mobil_utama_id=mobil_id).all()
            available_backups = []
            
            for backup in backup_mobils:
                if self._check_availability(backup.mobil_backup_id, start_date, end_date):
                    mobil = Mobil.query.get(backup.mobil_backup_id)
                    if mobil and mobil.status == MobilStatus.ACTIVE:
                        available_backups.append({
                            'id': mobil.id,
                            'nama': mobil.nama,
                            'plat_nomor': mobil.plat_nomor,
                            'priority': backup.priority,
                            'is_backup': True
                        })
            
            # Sort by priority
            available_backups.sort(key=lambda x: x['priority'], reverse=True)
            return available_backups
            
        except Exception as e:
            logger.error(f"Error getting backup options: {e}")
            raise
    
    def _check_availability(self, mobil_id: int, start_date: date, end_date: date, jam_mulai: str = None, jam_selesai: str = None) -> bool:
        """Check if mobil is available for given date range"""
        try:
            logger.info(f"🔍 Checking availability: mobil_id={mobil_id}, start_date={start_date}, end_date={end_date}, jam_mulai={jam_mulai}, jam_selesai={jam_selesai}")
            
            # Get all conflicting requests for the same date
            conflicting_requests = MobilRequest.query.filter(
                and_(
                    MobilRequest.mobil_id == mobil_id,
                    MobilRequest.status == RequestStatus.ACTIVE,
                    or_(
                        and_(MobilRequest.tanggal_mulai <= end_date, MobilRequest.tanggal_selesai >= start_date)
                    )
                )
            ).all()
            
            logger.info(f"📊 Found {len(conflicting_requests)} conflicting requests for mobil {mobil_id}")
            
            # Log details of conflicting requests
            for req in conflicting_requests:
                logger.info(f"🚫 Conflicting request: ID={req.id}, jam_mulai={req.jam_mulai}, jam_selesai={req.jam_selesai}")
            
            # If no time specified, use old logic (full day conflict)
            if not jam_mulai or not jam_selesai:
                is_available = len(conflicting_requests) == 0
                logger.info(f"✅ Availability result (no time specified): mobil_id={mobil_id}, available={is_available}")
                return is_available
            
            # Check time conflicts for same date requests
            is_available = True
            for req in conflicting_requests:
                logger.info(f"🚫 Checking time conflict with request: ID={req.id}, jam_mulai={req.jam_mulai}, jam_selesai={req.jam_selesai}")
                
                # Check if time ranges overlap
                if self._time_ranges_overlap(jam_mulai, jam_selesai, str(req.jam_mulai), str(req.jam_selesai)):
                    logger.info(f"❌ Time conflict found with request {req.id}")
                    is_available = False
                    break
            
            logger.info(f"✅ Availability result (with time): mobil_id={mobil_id}, available={is_available}")
            logger.info(f"✅ Availability result: mobil_id={mobil_id}, available={is_available}")
            
            return is_available
            
        except Exception as e:
            logger.error(f"❌ Error checking availability: {e}")
            return False
    
    def _time_ranges_overlap(self, start1: str, end1: str, start2: str, end2: str) -> bool:
        """Check if two time ranges overlap"""
        try:
            # Convert time strings to datetime objects for comparison
            from datetime import datetime, time
            
            def time_to_minutes(time_str: str) -> int:
                """Convert time string (HH:MM) to minutes since midnight"""
                if not time_str:
                    return 0
                # Handle both 'HH:MM' and 'HH:MM:SS' formats
                time_str = time_str.split(':')[0] + ':' + time_str.split(':')[1]
                t = datetime.strptime(time_str, '%H:%M').time()
                return t.hour * 60 + t.minute
            
            start1_min = time_to_minutes(start1)
            end1_min = time_to_minutes(end1)
            start2_min = time_to_minutes(start2)
            end2_min = time_to_minutes(end2)
            
            # Check if ranges overlap
            # Two ranges overlap if: start1 < end2 AND start2 < end1
            overlap = start1_min < end2_min and start2_min < end1_min
            
            logger.info(f"🕐 Time overlap check: {start1}-{end1} vs {start2}-{end2} = {overlap}")
            return overlap
            
        except Exception as e:
            logger.error(f"❌ Error checking time overlap: {e}")
            return True  # Assume conflict if error
    
    def _find_backup_mobil(self, original_mobil_id: int, start_date: date, end_date: date) -> Optional[Dict[str, Any]]:
        """Find available backup mobil"""
        try:
            backup_options = self.get_backup_options(original_mobil_id, start_date, end_date)
            return backup_options[0] if backup_options else None
        except Exception as e:
            logger.error(f"Error finding backup mobil: {e}")
            return None
    
    def _add_to_waiting_list(self, user_id: int, mobil_id: int, start_date: date, end_date: date):
        """Add request to waiting list"""
        try:
            waiting_list = WaitingList(
                user_id=user_id,
                mobil_id=mobil_id,
                tanggal_mulai=start_date,
                tanggal_selesai=end_date,
                status=WaitingListStatus.WAITING
            )
            
            self.db.session.add(waiting_list)
            self.db.session.commit()
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error adding to waiting list: {e}")
            raise
    
    def _create_single_request(self, user_id: int, mobil_id: int, start_date: date, end_date: date, jam_mulai: str, jam_selesai: str, keperluan: str) -> Dict[str, Any]:
        """Create single mobil request"""
        try:
            logger.info(f"📝 Creating single request: user_id={user_id}, mobil_id={mobil_id}, start_date={start_date}, end_date={end_date}")
            
            request = MobilRequest(
                user_id=user_id,
                mobil_id=mobil_id,
                tanggal_mulai=start_date,
                tanggal_selesai=end_date,
                jam_mulai=jam_mulai,
                jam_selesai=jam_selesai,
                keperluan=keperluan,
                status=RequestStatus.ACTIVE
            )
            
            self.db.session.add(request)
            self.db.session.commit()
            
            logger.info(f"✅ Request created successfully: ID={request.id}, user_id={user_id}, mobil_id={mobil_id}, tanggal_mulai={start_date}, tanggal_selesai={end_date}")
            
            # Log the action
            self._log_usage(mobil_id, user_id, request.id, 'request')
            
            return {
                'success': True,
                'message': 'Request berhasil dibuat',
                'request': self._request_to_dict(request),
                'id': request.id
            }
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"❌ Error creating single request: {e}")
            raise
    
    def _create_recurring_request(self, user_id: int, mobil_id: int, start_date: date, end_date: date, 
                                keperluan: str, pattern: str, recurring_end_date: date) -> Dict[str, Any]:
        """Create recurring mobil request"""
        try:
            # Create parent request
            parent_request = MobilRequest(
                user_id=user_id,
                mobil_id=mobil_id,
                tanggal_mulai=start_date,
                tanggal_selesai=end_date,
                keperluan=keperluan,
                status=RequestStatus.ACTIVE,
                is_recurring=True,
                recurring_pattern=RecurringPattern(pattern),
                recurring_end_date=recurring_end_date
            )
            
            self.db.session.add(parent_request)
            self.db.session.flush()  # Get the ID
            
            # Generate recurring dates
            recurring_dates = self._generate_recurring_dates(start_date, end_date, pattern, recurring_end_date)
            
            created_requests = []
            for date_range in recurring_dates:
                if self._check_availability(mobil_id, date_range['start'], date_range['end']):
                    request = MobilRequest(
                        user_id=user_id,
                        mobil_id=mobil_id,
                        tanggal_mulai=date_range['start'],
                        tanggal_selesai=date_range['end'],
                        keperluan=keperluan,
                        status=RequestStatus.ACTIVE,
                        parent_request_id=parent_request.id
                    )
                    
                    self.db.session.add(request)
                    created_requests.append(request)
                    
                    # Log the action
                    self._log_usage(mobil_id, user_id, request.id, 'request')
            
            self.db.session.commit()
            
            return {
                'success': True,
                'message': f'Recurring request berhasil dibuat dengan {len(created_requests)} occurrences',
                'parent_request': self._request_to_dict(parent_request),
                'created_requests': [self._request_to_dict(req) for req in created_requests]
            }
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error creating recurring request: {e}")
            raise
    
    def _generate_recurring_dates(self, start_date: date, end_date: date, pattern: str, recurring_end_date: date) -> List[Dict[str, date]]:
        """Generate recurring dates based on pattern"""
        dates = []
        current_start = start_date
        current_end = end_date
        
        while current_start <= recurring_end_date:
            dates.append({
                'start': current_start,
                'end': current_end
            })
            
            if pattern == 'daily':
                current_start += timedelta(days=1)
                current_end += timedelta(days=1)
            elif pattern == 'weekly':
                current_start += timedelta(weeks=1)
                current_end += timedelta(weeks=1)
            elif pattern == 'monthly':
                # Add one month
                if current_start.month == 12:
                    current_start = current_start.replace(year=current_start.year + 1, month=1)
                else:
                    current_start = current_start.replace(month=current_start.month + 1)
                
                if current_end.month == 12:
                    current_end = current_end.replace(year=current_end.year + 1, month=1)
                else:
                    current_end = current_end.replace(month=current_end.month + 1)
        
        return dates
    
    def _get_mobil_availability(self, mobil_id: int, start_date: date, end_date: date, requests: List[MobilRequest]) -> List[Dict[str, Any]]:
        """Get mobil availability for date range"""
        availability = []
        current_date = start_date
        
        while current_date <= end_date:
            is_available = True
            conflicting_requests = []
            
            # Find all requests for this mobil and date (semua status)
            for request in requests:
                if (request.mobil_id == mobil_id and
                    request.tanggal_mulai <= current_date <= request.tanggal_selesai):
                    # Jika status ACTIVE, mobil tidak available
                    if request.status == RequestStatus.ACTIVE:
                        is_available = False
                    conflicting_requests.append(request)
            
            # If there are multiple requests, we'll show the first one in the main request field
            # and include all requests in a separate field
            main_request = conflicting_requests[0] if conflicting_requests else None
            all_requests = [self._request_to_dict(req) for req in conflicting_requests] if conflicting_requests else []
            
            availability.append({
                'date': current_date.isoformat(),
                'available': is_available,
                'request': self._request_to_dict(main_request) if main_request else None,
                'all_requests': all_requests,
                'request_count': len(conflicting_requests)
            })
            
            current_date += timedelta(days=1)
        
        return availability
    
    def _check_waiting_list(self, mobil_id: int, start_date: date, end_date: date):
        """Check waiting list when a request is cancelled"""
        try:
            waiting_items = WaitingList.query.filter(
                and_(
                    WaitingList.mobil_id == mobil_id,
                    WaitingList.status == WaitingListStatus.WAITING,
                    or_(
                        and_(WaitingList.tanggal_mulai <= end_date, WaitingList.tanggal_selesai >= start_date)
                    )
                )
            ).order_by(WaitingList.created_at.asc()).all()
            
            for item in waiting_items:
                if self._check_availability(mobil_id, item.tanggal_mulai, item.tanggal_selesai):
                    # Create request for waiting list item
                    request = MobilRequest(
                        user_id=item.user_id,
                        mobil_id=mobil_id,
                        tanggal_mulai=item.tanggal_mulai,
                        tanggal_selesai=item.tanggal_selesai,
                        keperluan='Auto-approved from waiting list',
                        status=RequestStatus.ACTIVE
                    )
                    
                    self.db.session.add(request)
                    self.db.session.flush()
                    
                    # Update waiting list status
                    item.status = WaitingListStatus.NOTIFIED
                    
                    # Log the action
                    self._log_usage(mobil_id, item.user_id, request.id, 'request')
                    
                    self.db.session.commit()
                    break  # Only process first available item
                    
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error checking waiting list: {e}")
    
    def _log_usage(self, mobil_id: int, user_id: int, request_id: int, action: str):
        """Log mobil usage"""
        try:
            log = MobilUsageLog(
                mobil_id=mobil_id,
                user_id=user_id,
                request_id=request_id,
                action=action
            )
            
            self.db.session.add(log)
            
        except Exception as e:
            logger.error(f"Error logging usage: {e}")
    
    def _mobil_to_dict(self, mobil: Mobil) -> Dict[str, Any]:
        """Convert Mobil model to dictionary"""
        if not mobil:
            return None
            
        return {
            'id': mobil.id,
            'nama': mobil.nama,
            'nama_mobil': mobil.nama,  # Alias for frontend compatibility
            'plat_nomor': mobil.plat_nomor,
            'status': mobil.status.value if mobil.status else None,
            'is_backup': mobil.is_backup,
            'backup_for_mobil_id': mobil.backup_for_mobil_id,
            'priority_score': mobil.priority_score,
            'created_at': mobil.created_at.isoformat() if mobil.created_at else None,
            'updated_at': mobil.updated_at.isoformat() if mobil.updated_at else None
        }
    
    def _request_to_dict(self, request: MobilRequest) -> Dict[str, Any]:
        """Convert MobilRequest model to dictionary"""
        if not request:
            return None
        
        # Get user information
        user_info = None
        if request.user_id:
            try:
                user = User.query.get(request.user_id)
                if user:
                    user_info = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role
                    }
            except Exception as e:
                logger.warning(f"Error getting user info for user_id {request.user_id}: {e}")
        
        # Get mobil information
        mobil_info = None
        if request.mobil_id:
            try:
                mobil = Mobil.query.get(request.mobil_id)
                if mobil:
                    mobil_info = self._mobil_to_dict(mobil)
            except Exception as e:
                logger.warning(f"Error getting mobil info for mobil_id {request.mobil_id}: {e}")
            
        return {
            'id': request.id,
            'user_id': request.user_id,
            'user': user_info,
            'mobil_id': request.mobil_id,
            'mobil': mobil_info,
            'tanggal_mulai': request.tanggal_mulai.isoformat() if request.tanggal_mulai else None,
            'tanggal_selesai': request.tanggal_selesai.isoformat() if request.tanggal_selesai else None,
            'start_date': request.tanggal_mulai.isoformat() if request.tanggal_mulai else None,  # Alias for frontend compatibility
            'end_date': request.tanggal_selesai.isoformat() if request.tanggal_selesai else None,  # Alias for frontend compatibility
            'jam_mulai': str(request.jam_mulai) if request.jam_mulai else None,
            'jam_selesai': str(request.jam_selesai) if request.jam_selesai else None,
            'keperluan': request.keperluan,
            'purpose': request.keperluan,  # Alias for frontend compatibility
            'status': request.status.value if request.status else None,
            'is_recurring': request.is_recurring,
            'recurring_pattern': request.recurring_pattern.value if request.recurring_pattern else None,
            'recurring_end_date': request.recurring_end_date.isoformat() if request.recurring_end_date else None,
            'parent_request_id': request.parent_request_id,
            'is_backup_mobil': request.is_backup_mobil,
            'original_mobil_id': request.original_mobil_id,
            'created_at': request.created_at.isoformat() if request.created_at else None,
            'updated_at': request.updated_at.isoformat() if request.updated_at else None
        }
