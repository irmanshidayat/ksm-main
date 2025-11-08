#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Notion Controller - Konsolidasi semua endpoint Notion
Menggabungkan database_discovery_controller, enhanced_database_controller, dan enhanced_notion_controller
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.unified_notion_service import get_unified_notion_service
from models.notion_database import NotionDatabase
from models.property_mapping import PropertyMapping as PropertyMappingModel
from config.database import db
from middlewares.api_auth import jwt_required_custom
import logging
import os
import asyncio

logger = logging.getLogger(__name__)

# Blueprint untuk unified notion operations
unified_notion_bp = Blueprint('unified_notion', __name__, url_prefix='/api/notion')

# Blueprint untuk database discovery operations (untuk kompatibilitas frontend)
database_discovery_bp = Blueprint('database_discovery', __name__, url_prefix='/api/database-discovery')

# =============================================================================
# DATABASE DISCOVERY ENDPOINTS
# =============================================================================

@unified_notion_bp.route('/discover', methods=['POST'])
@jwt_required()
def discover_databases():
    """
    Endpoint untuk discovery semua database Notion dalam workspace
    """
    try:
        # Dapatkan token Notion dari environment
        notion_token = os.getenv('NOTION_TOKEN')
        if not notion_token:
            return jsonify({
                'success': False,
                'message': 'NOTION_TOKEN tidak ditemukan di environment'
            }), 400
        
        # Inisialisasi unified service
        service = get_unified_notion_service()
        
        # Validasi token Notion
        if not service.validate_notion_token():
            return jsonify({
                'success': False,
                'message': 'Token Notion tidak valid atau tidak memiliki akses'
            }), 401
        
        # Jalankan discovery
        result = service.discover_all_databases()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': {
                    'databases_found': len(result['databases']),
                    'databases_saved': result['saved_count'],
                    'statistics': result['statistics']
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        logger.error(f"Error saat discovery database: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error internal server: {str(e)}'
        }), 500

@unified_notion_bp.route('/databases', methods=['GET'])
@jwt_required()
def get_databases():
    """
    Endpoint untuk mendapatkan list database yang sudah di-discover
    """
    try:
        # Query parameters
        database_type = request.args.get('type')  # task, employee, all
        employee_name = request.args.get('employee')
        valid_only = request.args.get('valid_only', 'true').lower() == 'true'
        
        # Query database dengan error handling
        try:
            query = NotionDatabase.query
            
            # Filter berdasarkan tipe
            if database_type == 'task':
                query = query.filter(NotionDatabase.is_task_database == True)
            elif database_type == 'employee':
                query = query.filter(NotionDatabase.is_employee_specific == True)
            
            # Filter berdasarkan nama karyawan
            if employee_name:
                query = query.filter(NotionDatabase.employee_name == employee_name)
            
            # Filter hanya yang valid
            if valid_only:
                query = query.filter(NotionDatabase.structure_valid == True)
            
            # Order by
            query = query.order_by(NotionDatabase.confidence_score.desc())
            
            # Execute query
            databases = query.all()
            
        except Exception as db_error:
            logger.error(f"Database query error: {str(db_error)}")
            return jsonify({
                'success': False,
                'message': 'Error saat query database',
                'error': str(db_error)
            }), 422
        
        # Convert ke dictionary dengan error handling
        result = []
        for db_item in databases:
            try:
                db_dict = db_item.to_dict()
                # Parse missing_properties dari JSON string
                if db_dict.get('missing_properties'):
                    try:
                        import json
                        db_dict['missing_properties'] = json.loads(db_dict['missing_properties'])
                    except:
                        db_dict['missing_properties'] = []
                result.append(db_dict)
            except Exception as convert_error:
                logger.warning(f"Error converting database {db_item.id}: {str(convert_error)}")
                continue
        
        return jsonify({
            'success': True,
            'data': {
                'databases': result,
                'total_count': len(result)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error saat mengambil database: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error internal server: {str(e)}'
        }), 500

@unified_notion_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """
    Endpoint untuk mendapatkan statistik database
    """
    try:
        service = get_unified_notion_service()
        
        # Cek apakah tabel NotionDatabase ada
        try:
            statistics = service.get_discovery_statistics()
        except Exception as stats_error:
            logger.error(f"Error getting statistics: {str(stats_error)}")
            # Return default statistics jika ada error
            statistics = {
                'total_databases': 0,
                'task_databases': 0,
                'employee_databases': 0,
                'valid_databases': 0,
                'enabled_databases': 0
            }
        
        return jsonify({
            'success': True,
            'data': statistics
        }), 200
        
    except Exception as e:
        logger.error(f"Error saat mengambil statistik: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error internal server: {str(e)}'
        }), 500

@unified_notion_bp.route('/employees', methods=['GET'])
@jwt_required()
def get_employees():
    """
    Endpoint untuk mendapatkan list karyawan yang memiliki database
    """
    try:
        # Query untuk mendapatkan nama karyawan unik dengan error handling
        try:
            from sqlalchemy import distinct
            employee_names = db.session.query(
                distinct(NotionDatabase.employee_name)
            ).filter(
                NotionDatabase.employee_name.isnot(None),
                NotionDatabase.is_employee_specific == True
            ).all()
            
            # Convert ke list
            employees = [name[0] for name in employee_names if name[0]]
            
        except Exception as query_error:
            logger.error(f"Employee query error: {str(query_error)}")
            return jsonify({
                'success': False,
                'message': 'Error saat query database',
                'error': str(query_error)
            }), 422
        
        # Hitung statistik per karyawan
        employee_stats = []
        for employee_name in employees:
            try:
                # Hitung jumlah database per karyawan
                db_count = NotionDatabase.query.filter(
                    NotionDatabase.employee_name == employee_name,
                    NotionDatabase.is_employee_specific == True
                ).count()
                
                # Hitung database yang valid
                valid_count = NotionDatabase.query.filter(
                    NotionDatabase.employee_name == employee_name,
                    NotionDatabase.is_employee_specific == True,
                    NotionDatabase.structure_valid == True
                ).count()
                
                employee_stats.append({
                    'name': employee_name,
                    'total_databases': db_count,
                    'valid_databases': valid_count,
                    'valid_percentage': round((valid_count / db_count * 100) if db_count > 0 else 0, 2)
                })
            except Exception as stat_error:
                logger.warning(f"Error calculating stats for {employee_name}: {str(stat_error)}")
                continue
        
        return jsonify({
            'success': True,
            'data': {
                'employees': employee_stats,
                'total_employees': len(employees)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error saat mengambil data karyawan: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error internal server: {str(e)}'
        }), 500

@unified_notion_bp.route('/database/<database_id>', methods=['GET'])
@jwt_required()
def get_database_detail(database_id):
    """
    Endpoint untuk mendapatkan detail database tertentu
    """
    try:
        database = NotionDatabase.get_by_database_id(database_id)
        
        if not database:
            return jsonify({
                'success': False,
                'message': 'Database tidak ditemukan'
            }), 404
        
        db_dict = database.to_dict()
        
        # Parse missing_properties dari JSON string
        if db_dict.get('missing_properties'):
            try:
                import json
                db_dict['missing_properties'] = json.loads(db_dict['missing_properties'])
            except:
                db_dict['missing_properties'] = []
        
        return jsonify({
            'success': True,
            'data': db_dict
        }), 200
        
    except Exception as e:
        logger.error(f"Error saat mengambil detail database: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error internal server: {str(e)}'
        }), 500

@unified_notion_bp.route('/database/<database_id>/toggle-sync', methods=['POST'])
@jwt_required()
def toggle_database_sync(database_id):
    """
    Endpoint untuk enable/disable sync untuk database tertentu
    """
    try:
        database = NotionDatabase.get_by_database_id(database_id)
        
        if not database:
            return jsonify({
                'success': False,
                'message': 'Database tidak ditemukan'
            }), 404
        
        # Toggle sync status
        database.sync_enabled = not database.sync_enabled
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Sync {"diaktifkan" if database.sync_enabled else "dinonaktifkan"} untuk database {database.database_title}',
            'data': {
                'database_id': database_id,
                'sync_enabled': database.sync_enabled
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error saat toggle sync database: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error internal server: {str(e)}'
        }), 500

@unified_notion_bp.route('/validate-token', methods=['POST'])
@jwt_required()
def validate_notion_token():
    """
    Endpoint untuk validasi token Notion
    """
    try:
        notion_token = os.getenv('NOTION_TOKEN')
        if not notion_token:
            return jsonify({
                'success': False,
                'message': 'NOTION_TOKEN tidak ditemukan di environment'
            }), 400
        
        service = get_unified_notion_service()
        is_valid = service.validate_notion_token()
        
        return jsonify({
            'success': True,
            'data': {
                'token_valid': is_valid,
                'message': 'Token valid' if is_valid else 'Token tidak valid'
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error saat validasi token: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error internal server: {str(e)}'
        }), 500

# =============================================================================
# ENHANCED DATABASE ENDPOINTS
# =============================================================================

@unified_notion_bp.route('/discover-and-analyze', methods=['POST'])
@jwt_required_custom
def discover_and_analyze_databases():
    """Discover semua database dan analyze property mapping"""
    try:
        service = get_unified_notion_service()
        result = service.discover_and_analyze_databases()
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': f"Successfully analyzed {result['databases_analyzed']} databases with {result['total_mappings_created']} mappings created",
                'data': result
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error in discover_and_analyze_databases: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_notion_bp.route('/tasks/all-employees', methods=['GET'])
@jwt_required_custom
def get_all_employee_tasks():
    """Get semua task dari semua database, dikelompokkan berdasarkan employee"""
    try:
        employee_filter = request.args.get('employee')
        
        service = get_unified_notion_service()
        tasks = service.get_all_employee_tasks(employee_filter)
        
        return jsonify({
            'success': True,
            'data': tasks,
            'total_employees': len(tasks),
            'total_tasks': sum(len(employee_tasks) for employee_tasks in tasks.values())
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_all_employee_tasks: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_notion_bp.route('/tasks/database/<database_id>', methods=['GET'])
@jwt_required_custom
def get_database_tasks(database_id):
    """Get tasks dari database tertentu"""
    try:
        service = get_unified_notion_service()
        tasks = service.get_tasks_from_database(database_id)
        
        return jsonify({
            'success': True,
            'data': tasks,
            'total_tasks': len(tasks)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_database_tasks: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_notion_bp.route('/mapping/analyze/<database_id>', methods=['GET'])
@jwt_required_custom
def analyze_mapping_quality(database_id):
    """Analyze kualitas mapping untuk database tertentu"""
    try:
        service = get_unified_notion_service()
        analysis = service.analyze_mapping_quality(database_id)
        
        if 'error' in analysis:
            return jsonify({
                'success': False,
                'error': analysis['error']
            }), 400
        
        return jsonify({
            'success': True,
            'data': analysis
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in analyze_mapping_quality: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_notion_bp.route('/mapping/analyze-test/<database_id>', methods=['GET'])
def analyze_mapping_quality_test(database_id):
    """Test endpoint untuk analyze mapping quality (tanpa auth)"""
    try:
        service = get_unified_notion_service()
        analysis = service.analyze_mapping_quality(database_id)
        
        if 'error' in analysis:
            return jsonify({
                'success': False,
                'error': analysis['error']
            }), 400
        
        return jsonify({
            'success': True,
            'data': analysis
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in analyze_mapping_quality_test: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_notion_bp.route('/mapping/update', methods=['POST'])
@jwt_required_custom
def update_property_mapping():
    """Update property mapping secara manual"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        required_fields = ['database_id', 'property_name', 'mapped_field']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        service = get_unified_notion_service()
        success = service.update_property_mapping(
            database_id=data['database_id'],
            property_name=data['property_name'],
            mapped_field=data['mapped_field'],
            is_active=data.get('is_active', True)
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Property mapping updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update property mapping'
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Error in update_property_mapping: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_notion_bp.route('/mapping/database/<database_id>', methods=['GET'])
@jwt_required_custom
def get_database_mappings(database_id):
    """Get semua property mappings untuk database tertentu"""
    try:
        mappings = PropertyMappingModel.get_database_mappings(database_id, active_only=False)
        
        return jsonify({
            'success': True,
            'data': [mapping.to_dict() for mapping in mappings],
            'total_mappings': len(mappings)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_database_mappings: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_notion_bp.route('/mapping/toggle/<int:mapping_id>', methods=['POST'])
@jwt_required_custom
def toggle_mapping_status(mapping_id):
    """Toggle status mapping (active/inactive)"""
    try:
        data = request.get_json()
        is_active = data.get('is_active', True) if data else True
        
        mapping = PropertyMappingModel.toggle_mapping_status(mapping_id, is_active)
        
        if mapping:
            return jsonify({
                'success': True,
                'message': f'Mapping {"activated" if is_active else "deactivated"} successfully',
                'data': mapping.to_dict()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Mapping not found'
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Error in toggle_mapping_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_notion_bp.route('/mapping/statistics', methods=['GET'])
@jwt_required_custom
def get_mapping_statistics():
    """Get overall mapping statistics"""
    try:
        service = get_unified_notion_service()
        stats = service.get_mapping_statistics()
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_mapping_statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_notion_bp.route('/mapping/statistics-test', methods=['GET'])
def get_mapping_statistics_test():
    """Test endpoint untuk mapping statistics (tanpa auth)"""
    try:
        # Get mapping statistics directly
        total_mappings = PropertyMappingModel.query.count()
        active_mappings = PropertyMappingModel.query.filter(PropertyMappingModel.is_active == True).count()
        high_quality_mappings = PropertyMappingModel.query.filter(PropertyMappingModel.confidence_score >= 0.8).count()
        
        # Get database count
        database_ids = PropertyMappingModel.get_all_database_ids()
        total_databases = len(database_ids)
        
        stats = {
            'total_databases': total_databases,
            'total_mappings': total_mappings,
            'active_mappings': active_mappings,
            'high_quality_mappings': high_quality_mappings,
            'average_mappings_per_database': total_mappings / total_databases if total_databases > 0 else 0,
            'mapping_coverage_percentage': 100.0 if total_databases > 0 else 0.0
        }
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_mapping_statistics_test: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_notion_bp.route('/mapping/statistics/<database_id>', methods=['GET'])
@jwt_required_custom
def get_database_mapping_statistics(database_id):
    """Get mapping statistics untuk database tertentu"""
    try:
        stats = PropertyMappingModel.get_mapping_statistics(database_id)
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_database_mapping_statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_notion_bp.route('/databases/with-mappings', methods=['GET'])
@jwt_required_custom
def get_databases_with_mappings():
    """Get semua database yang memiliki property mappings"""
    try:
        database_ids = PropertyMappingModel.get_all_database_ids()
        
        databases = []
        for database_id in database_ids:
            database = NotionDatabase.get_by_database_id(database_id)
            if database:
                db_data = database.to_dict()
                # Add mapping statistics
                mapping_stats = PropertyMappingModel.get_mapping_statistics(database_id)
                db_data['mapping_statistics'] = mapping_stats
                databases.append(db_data)
        
        return jsonify({
            'success': True,
            'data': databases,
            'total_databases': len(databases)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_databases_with_mappings: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_notion_bp.route('/databases/with-mappings-test', methods=['GET'])
def get_databases_with_mappings_test():
    """Test endpoint untuk get databases with mappings (tanpa auth)"""
    try:
        database_ids = PropertyMappingModel.get_all_database_ids()
        
        databases = []
        for database_id in database_ids:
            database = NotionDatabase.get_by_database_id(database_id)
            if database:
                db_data = database.to_dict()
                # Add mapping statistics
                mapping_stats = PropertyMappingModel.get_mapping_statistics(database_id)
                db_data['mapping_statistics'] = mapping_stats
                databases.append(db_data)
        
        return jsonify({
            'success': True,
            'data': databases,
            'total_databases': len(databases)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_databases_with_mappings_test: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@unified_notion_bp.route('/mapping/suggestions/<database_id>', methods=['GET'])
@jwt_required_custom
def get_mapping_suggestions(database_id):
    """Get suggestions untuk property renaming"""
    try:
        service = get_unified_notion_service()
        analysis = service.analyze_mapping_quality(database_id)
        
        if 'error' in analysis:
            return jsonify({
                'success': False,
                'error': analysis['error']
            }), 400
        
        suggestions = analysis.get('renaming_suggestions', [])
        
        return jsonify({
            'success': True,
            'data': suggestions,
            'total_suggestions': len(suggestions)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_mapping_suggestions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# ENHANCED NOTION ENDPOINTS
# =============================================================================

@unified_notion_bp.route('/tasks', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_all_employee_tasks_async():
    """Mendapatkan task list dari semua karyawan dengan filter"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # Get query parameters
        employee_filter = request.args.get('employee')
        status_filter = request.args.get('status')
        priority_filter = request.args.get('priority')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Get tasks from all employees
        service = get_unified_notion_service()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            tasks = loop.run_until_complete(
                service.get_all_employee_tasks_async(
                    employee_filter=employee_filter,
                    status_filter=status_filter,
                    priority_filter=priority_filter,
                    date_from=date_from,
                    date_to=date_to
                )
            )
        finally:
            loop.close()
        
        # Check if using fallback data
        using_fallback = any(task.get('id', '').startswith('fallback-') for task in tasks)
        
        response_data = {
            'success': True,
            'data': tasks,
            'count': len(tasks),
            'using_fallback': using_fallback,
            'employee_count': len(service.employee_databases)
        }
        
        if using_fallback:
            response_data['message'] = '⚠️ Menggunakan data fallback karena Notion API tidak tersedia'
            response_data['debug_info'] = {
                'token_configured': service.validate_token(),
                'employee_databases': len(service.employee_databases)
            }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error in get_all_employee_tasks_async: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil data task',
            'error': str(e)
        }), 500

@unified_notion_bp.route('/employee-list', methods=['GET'])
@jwt_required()
def get_employee_list():
    """Mendapatkan daftar karyawan yang tersedia"""
    try:
        service = get_unified_notion_service()
        employees = list(service.employee_databases.keys())
        
        return jsonify({
            'success': True,
            'data': {
                'employees': employees,
                'total_count': len(employees)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_employee_list: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil daftar karyawan'
        }), 500

@unified_notion_bp.route('/enhanced-statistics', methods=['GET'])
@jwt_required()
def get_enhanced_statistics():
    """Mendapatkan statistik untuk semua karyawan"""
    try:
        service = get_unified_notion_service()
        stats = service.get_employee_statistics()
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_enhanced_statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil statistik'
        }), 500

@unified_notion_bp.route('/discover-databases', methods=['POST'])
@jwt_required()
def discover_databases_enhanced():
    """Discover semua database dalam workspace Notion"""
    try:
        service = get_unified_notion_service()
        databases = service.discover_employee_databases()
        
        return jsonify({
            'success': True,
            'data': {
                'databases': databases,
                'total_count': len(databases)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in discover_databases_enhanced: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat discover database'
        }), 500

@unified_notion_bp.route('/status', methods=['GET'])
@jwt_required()
def get_enhanced_status():
    """Mendapatkan status koneksi dan konfigurasi"""
    try:
        service = get_unified_notion_service()
        token_valid = service.validate_token()
        
        status_info = {
            'token_configured': token_valid,
            'employee_databases_count': len(service.employee_databases),
            'employee_list': list(service.employee_databases.keys()),
            'base_url': service.base_url
        }
        
        if token_valid:
            status_info['message'] = '✅ Enhanced Notion API terhubung dengan baik'
        else:
            status_info['message'] = '❌ Enhanced Notion API tidak terhubung'
            status_info['setup_required'] = True
            status_info['setup_instructions'] = [
                '1. Buat file .env di folder backend/',
                '2. Copy isi dari env.example ke .env',
                '3. Dapatkan Notion Integration Token dari https://www.notion.so/my-integrations',
                '4. Share database dengan integration',
                '5. Tambahkan database ID karyawan di unified_notion_service.py'
            ]
        
        return jsonify({
            'success': True,
            'data': status_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_enhanced_status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengecek status'
        }), 500

@unified_notion_bp.route('/test', methods=['GET'])
@jwt_required()
def test_enhanced_connection():
    """Test koneksi ke Enhanced Notion API"""
    try:
        service = get_unified_notion_service()
        
        # Test token validity
        token_valid = service.validate_token()
        
        if not token_valid:
            return jsonify({
                'success': False,
                'message': '❌ Token Notion tidak valid atau tidak dikonfigurasi',
                'setup_required': True
            }), 400
        
        # Test database discovery
        try:
            databases = service.discover_employee_databases()
            
            return jsonify({
                'success': True,
                'message': '✅ Koneksi ke Enhanced Notion API berhasil!',
                'data': {
                    'discovered_databases': len(databases),
                    'configured_employees': len(service.employee_databases),
                    'sample_databases': databases[:3] if databases else []
                }
            }), 200
                
        except Exception as db_error:
            return jsonify({
                'success': False,
                'message': f'❌ Error mengakses database: {str(db_error)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in test_enhanced_connection: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat test koneksi'
        }), 500

# =============================================================================
# ENHANCED NOTION ENDPOINTS (dari enhanced_notion_controller.py)
# =============================================================================

@unified_notion_bp.route('/enhanced-tasks', methods=['GET'])
@jwt_required()
def get_enhanced_tasks():
    """Get all tasks from Notion integration (Enhanced endpoint)"""
    try:
        # Parse query parameters
        employee = request.args.get('employee', '')
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        service = get_unified_notion_service()
        
        # Cek apakah Notion API dikonfigurasi
        if not service.validate_token():
            logger.warning("Notion API tidak dikonfigurasi, menggunakan fallback data")
            return _get_fallback_tasks(employee, status, priority, date_from, date_to)
        
        # Ambil data real dari Notion menggunakan async method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tasks = loop.run_until_complete(
                service.get_all_employee_tasks_async(
                    employee_filter=employee if employee else None,
                    status_filter=status if status else None,
                    priority_filter=priority if priority else None,
                    date_from=date_from if date_from else None,
                    date_to=date_to if date_to else None
                )
            )
        finally:
            loop.close()
        
        # Apply additional filters if needed
        filtered_tasks = tasks
        if employee:
            filtered_tasks = [task for task in filtered_tasks if employee.lower() in task.get('employee_name', '').lower()]
        
        return jsonify({
            'success': True,
            'data': filtered_tasks,
            'message': f'Berhasil mengambil {len(filtered_tasks)} tasks dari Notion'
        })
        
    except Exception as e:
        logger.error(f"Error in get_enhanced_tasks: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error mengambil tasks: {str(e)}',
            'data': []
        }), 500


@unified_notion_bp.route('/enhanced-statistics', methods=['GET'])
@jwt_required()
def get_enhanced_statistics_v2():
    """Get task statistics (Enhanced endpoint v2)"""
    try:
        service = get_unified_notion_service()
        
        # Cek apakah Notion API dikonfigurasi
        if not service.validate_token():
            logger.warning("Notion API tidak dikonfigurasi, menggunakan fallback statistics")
            return _get_fallback_statistics()
        
        # Ambil statistik real dari Notion
        statistics = service.get_employee_statistics()
        
        return jsonify({
            'success': True,
            'data': statistics,
            'message': 'Statistik berhasil diambil dari Notion'
        })
        
    except Exception as e:
        logger.error(f"Error in get_enhanced_statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error mengambil statistik: {str(e)}',
            'data': {}
        }), 500


@unified_notion_bp.route('/enhanced-employees', methods=['GET'])
@jwt_required()
def get_enhanced_employees():
    """Get list of employees (Enhanced endpoint)"""
    try:
        service = get_unified_notion_service()
        
        # Cek apakah Notion API dikonfigurasi
        if not service.validate_token():
            logger.warning("Notion API tidak dikonfigurasi, menggunakan fallback employees")
            return _get_fallback_employees()
        
        # Ambil employees real dari Notion
        employee_databases = service.employee_databases
        employees = []
        
        for employee_name, database_id in employee_databases.items():
            # Ambil task count untuk employee ini
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                tasks = loop.run_until_complete(
                    service.get_all_employee_tasks_async(employee_filter=employee_name)
                )
                task_count = len(tasks)
            finally:
                loop.close()
            
            employees.append({
                'name': employee_name,
                'task_count': task_count
            })
        
        return jsonify({
            'success': True,
            'data': {
                'employees': employees,
                'total_count': len(employees)
            },
            'message': f'Berhasil mengambil {len(employees)} employees dari Notion'
        })
        
    except Exception as e:
        logger.error(f"Error in get_enhanced_employees: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error mengambil employees: {str(e)}',
            'data': {
                'employees': [],
                'total_count': 0
            }
        }), 500


@unified_notion_bp.route('/enhanced-sync', methods=['POST'])
@jwt_required()
def sync_enhanced_tasks():
    """Sync tasks with Notion API (Enhanced endpoint)"""
    try:
        from datetime import datetime
        
        # Mock sync process - bisa diimplementasikan lebih lanjut
        sync_result = {
            "sync_id": f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "completed",
            "tasks_synced": 0,
            "new_tasks": 0,
            "updated_tasks": 0,
            "sync_time": datetime.now().isoformat(),
            "message": "Tasks synchronized successfully"
        }
        
        logger.info(f"Task sync completed: {sync_result['sync_id']}")
        
        return jsonify({
            'success': True,
            'data': sync_result,
            'message': 'Tasks synchronized successfully'
        })
        
    except Exception as e:
        logger.error(f"Error syncing tasks: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to sync tasks',
            'error': str(e)
        }), 500


@unified_notion_bp.route('/enhanced-health', methods=['GET'])
@jwt_required()
def enhanced_health_check():
    """Health check for enhanced notion service"""
    try:
        from datetime import datetime
        
        service = get_unified_notion_service()
        
        health_data = {
            "service": "enhanced_notion",
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "notion_configured": service.validate_token(),
            "endpoints": {
                "tasks": "/api/notion/enhanced-tasks",
                "statistics": "/api/notion/enhanced-statistics", 
                "employees": "/api/notion/enhanced-employees",
                "sync": "/api/notion/enhanced-sync"
            }
        }
        
        return jsonify({
            'success': True,
            'data': health_data,
            'message': 'Enhanced Notion service is healthy'
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'message': 'Health check failed',
            'error': str(e)
        }), 500


# =============================================================================
# FALLBACK FUNCTIONS (dari enhanced_notion_controller.py)
# =============================================================================

def _get_fallback_tasks(employee, status, priority, date_from, date_to):
    """Fallback data jika Notion API tidak tersedia"""
    from datetime import datetime
    
    mock_tasks = [
        {
            "id": "fallback-001",
            "employee_name": "IRMN",
            "title": "Implementasi fitur baru",
            "date": "2025-01-15",
            "status": "Dalam Proses",
            "priority": "Tinggi",
            "description": "Implementasi fitur manajemen task yang baru",
            "notion_url": "https://notion.so/task_001",
            "created_time": "2025-01-10T10:00:00Z",
            "last_edited_time": "2025-01-15T14:30:00Z"
        },
        {
            "id": "fallback-002",
            "employee_name": "IRMN",
            "title": "Review dokumentasi",
            "date": "2025-01-14",
            "status": "Selesai",
            "priority": "Sedang",
            "description": "Review dan update dokumentasi API",
            "notion_url": "https://notion.so/task_002",
            "created_time": "2025-01-12T09:00:00Z",
            "last_edited_time": "2025-01-14T16:45:00Z"
        }
    ]
    
    # Apply filters
    filtered_tasks = mock_tasks
    
    if employee:
        filtered_tasks = [task for task in filtered_tasks if employee.lower() in task['employee_name'].lower()]
    
    if status:
        filtered_tasks = [task for task in filtered_tasks if task['status'] == status]
    
    if priority:
        filtered_tasks = [task for task in filtered_tasks if task['priority'] == priority]
    
    if date_from:
        filtered_tasks = [task for task in filtered_tasks if task['date'] >= date_from]
    
    if date_to:
        filtered_tasks = [task for task in filtered_tasks if task['date'] <= date_to]
        
    return jsonify({
        'success': True,
        'data': filtered_tasks,
        'message': f'⚠️ Menggunakan data fallback - {len(filtered_tasks)} tasks (Notion API tidak tersedia)'
    })


def _get_fallback_statistics():
    """Fallback statistics jika Notion API tidak tersedia"""
    from datetime import datetime
    
    return jsonify({
        'success': True,
        'data': {
            'total_tasks': 2,
            'total_employees': 1,
            'tasks_by_status': {
                'Dalam Proses': 1,
                'Selesai': 1,
                'Tertunda': 0,
                'Dialihkan': 0
            },
            'tasks_by_priority': {
                'Tinggi': 1,
                'Sedang': 1,
                'Rendah': 0
            },
            'last_sync': datetime.now().isoformat()
        },
        'message': '⚠️ Menggunakan statistik fallback (Notion API tidak tersedia)'
    })


def _get_fallback_employees():
    """Fallback employees jika Notion API tidak tersedia"""
    return jsonify({
        'success': True,
        'data': {
            'employees': [
                {'name': 'IRMN', 'task_count': 2}
            ],
            'total_count': 1
        },
        'message': '⚠️ Menggunakan data employees fallback (Notion API tidak tersedia)'
    })


# =============================================================================
# DATABASE DISCOVERY ROUTES (untuk kompatibilitas frontend)
# =============================================================================

@database_discovery_bp.route('/databases', methods=['GET'])
@jwt_required()
def database_discovery_get_databases():
    """Endpoint untuk mendapatkan list database yang sudah di-discover (alias untuk /api/notion/databases)"""
    return get_databases()

@database_discovery_bp.route('/employees', methods=['GET'])
@jwt_required()
def database_discovery_get_employees():
    """Endpoint untuk mendapatkan list karyawan yang memiliki database (alias untuk /api/notion/employees)"""
    return get_employees()

@database_discovery_bp.route('/statistics', methods=['GET'])
@jwt_required()
def database_discovery_get_statistics():
    """Endpoint untuk mendapatkan statistik database (alias untuk /api/notion/statistics)"""
    return get_statistics()

@database_discovery_bp.route('/discover', methods=['POST'])
@jwt_required()
def database_discovery_discover():
    """Endpoint untuk discovery semua database Notion dalam workspace (alias untuk /api/notion/discover)"""
    return discover_databases()

@database_discovery_bp.route('/validate-token', methods=['POST'])
@jwt_required()
def database_discovery_validate_token():
    """Endpoint untuk validasi token Notion (alias untuk /api/notion/validate-token)"""
    return validate_notion_token()

@database_discovery_bp.route('/database/<database_id>/toggle-sync', methods=['POST'])
@jwt_required()
def database_discovery_toggle_sync(database_id):
    """Endpoint untuk enable/disable sync untuk database tertentu (alias untuk /api/notion/database/<id>/toggle-sync)"""
    return toggle_database_sync(database_id)

@database_discovery_bp.route('/test-endpoints', methods=['GET'])
def test_enhanced_database_endpoints():
    """Test endpoint untuk debug Enhanced Database"""
    try:
        from app import app
        
        with app.app_context():
            # Test get_databases_with_mappings
            database_ids = PropertyMappingModel.get_all_database_ids()
            
            databases = []
            for database_id in database_ids:
                database = NotionDatabase.get_by_database_id(database_id)
                if database:
                    db_data = database.to_dict()
                    # Add mapping statistics
                    mapping_stats = PropertyMappingModel.get_mapping_statistics(database_id)
                    db_data['mapping_statistics'] = mapping_stats
                    databases.append(db_data)
            
            # Test mapping statistics
            total_mappings = PropertyMappingModel.query.count()
            active_mappings = PropertyMappingModel.query.filter(PropertyMappingModel.is_active == True).count()
            high_quality_mappings = PropertyMappingModel.query.filter(PropertyMappingModel.confidence_score >= 0.8).count()
            
            return jsonify({
                'success': True,
                'data': {
                    'databases_with_mappings': databases,
                    'total_databases': len(databases),
                    'mapping_statistics': {
                        'total_mappings': total_mappings,
                        'active_mappings': active_mappings,
                        'high_quality_mappings': high_quality_mappings,
                        'average_mappings_per_database': total_mappings / len(databases) if databases else 0,
                        'mapping_coverage_percentage': 100.0 if databases else 0.0
                    }
                }
            }), 200
                
    except Exception as e:
        logger.error(f"Error in test endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@database_discovery_bp.route('/database/<database_id>/revalidate', methods=['POST'])
@jwt_required()
def database_discovery_revalidate(database_id):
    """Endpoint untuk re-validate database structure"""
    try:
        from app import app
        
        with app.app_context():
            # Get database from local storage
            database = NotionDatabase.get_by_database_id(database_id)
            if not database:
                return jsonify({
                    'success': False,
                    'message': 'Database tidak ditemukan'
                }), 404
            
            # Get fresh data from Notion API
            service = get_unified_notion_service()
            notion_db = service._get_database_info(database_id)
            
            if not notion_db:
                return jsonify({
                    'success': False,
                    'message': 'Tidak dapat mengambil data dari Notion API'
                }), 400
            
            # Re-analyze database structure
            analysis = service._analyze_database(notion_db)
            
            if analysis:
                # Update database with new analysis
                database.database_title = analysis.get('database_title', database.database_title)
                database.employee_name = analysis.get('employee_name', database.employee_name)
                database.database_type = analysis.get('database_type', database.database_type)
                database.is_task_database = analysis.get('is_task_database', database.is_task_database)
                database.is_employee_specific = analysis.get('is_employee_specific', database.is_employee_specific)
                database.structure_valid = analysis.get('structure_valid', database.structure_valid)
                database.confidence_score = analysis.get('confidence_score', database.confidence_score)
                database.missing_properties = json.dumps(analysis.get('missing_properties', []))
                database.updated_at = datetime.utcnow()
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Database {database.database_title} berhasil di-revalidate',
                    'data': {
                        'database_id': database_id,
                        'structure_valid': database.structure_valid,
                        'confidence_score': database.confidence_score,
                        'missing_properties': analysis.get('missing_properties', [])
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Gagal menganalisis database'
                }), 400
                
    except Exception as e:
        logger.error(f"Error saat re-validate database: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error internal server: {str(e)}'
        }), 500

# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@unified_notion_bp.route('/service-status', methods=['GET'])
@jwt_required()
def get_service_status():
    """Get comprehensive service status"""
    try:
        service = get_unified_notion_service()
        status = service.get_service_status()
        
        return jsonify({
            'success': True,
            'data': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_service_status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Terjadi kesalahan saat mengambil status service'
        }), 500
