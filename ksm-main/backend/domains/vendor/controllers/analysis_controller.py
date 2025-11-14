#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysis Controller - API Endpoints untuk Sistem Analisis Vendor
Controller untuk mengelola analisis vendor, scoring, dan recommendation
"""

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from config.database import db
from domains.vendor.services.vendor_analysis_service import VendorAnalysisService
from services.budget_integration_service import BudgetIntegrationService
from shared.utils.serialization import serialize_models

logger = logging.getLogger(__name__)

# Buat Blueprint untuk Flask
analysis_bp = Blueprint('analysis', __name__)

# ===== VENDOR ANALYSIS =====

@analysis_bp.route("/analyze/<int:request_id>", methods=["POST"])
def analyze_vendor_penawarans(request_id):
    """Analisis semua penawaran vendor untuk request tertentu"""
    try:
        data = request.get_json() or {}
        analysis_method = data.get('analysis_method', 'automated')
        
        # Validate analysis method
        valid_methods = ['automated', 'simplified', 'manual']
        if analysis_method not in valid_methods:
            return jsonify({
                'success': False,
                'message': f'Analysis method must be one of: {", ".join(valid_methods)}'
            }), 400
        
        service = VendorAnalysisService(db.session)
        result = service.analyze_vendor_penawarans(request_id, analysis_method)
        
        return jsonify({
            'success': True,
            'message': 'Analisis vendor berhasil dilakukan',
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error analyzing vendor penawarans: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@analysis_bp.route("/results/<int:request_id>", methods=["GET"])
def get_analysis_results(request_id):
    """Mendapatkan hasil analisis untuk request tertentu"""
    try:
        service = VendorAnalysisService(db.session)
        result = service.get_analysis_results(request_id)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Hasil analisis tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting analysis results: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@analysis_bp.route("/results/<int:request_id>/export", methods=["GET"])
def export_analysis_results(request_id):
    """Export hasil analisis ke format yang dapat didownload"""
    try:
        service = VendorAnalysisService(db.session)
        result = service.get_analysis_results(request_id)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Hasil analisis tidak ditemukan'
            }), 404
        
        # Generate export data
        export_data = {
            'request_info': result['request'],
            'analysis_date': result['analysis_date'],
            'total_vendors': result['total_vendors'],
            'vendor_results': []
        }
        
        for vendor_result in result['analysis_results']:
            export_data['vendor_results'].append({
                'vendor_info': vendor_result['vendor'],
                'penawaran_info': vendor_result['penawaran'],
                'analysis_scores': {
                    'price_score': vendor_result['analysis']['price_score'],
                    'quality_score': vendor_result['analysis']['quality_score'],
                    'delivery_score': vendor_result['analysis']['delivery_score'],
                    'reputation_score': vendor_result['analysis']['reputation_score'],
                    'payment_score': vendor_result['analysis']['payment_score'],
                    'total_score': vendor_result['analysis']['total_score'],
                    'recommendation_level': vendor_result['analysis']['recommendation_level']
                }
            })
        
        return jsonify({
            'success': True,
            'data': export_data,
            'export_format': 'json',
            'export_date': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error exporting analysis results: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== ANALYSIS CONFIGURATION =====

@analysis_bp.route("/config", methods=["GET"])
def get_analysis_config():
    """Mendapatkan konfigurasi analisis"""
    try:
        service = VendorAnalysisService(db.session)
        config = service.analysis_config
        
        return jsonify({
            'success': True,
            'data': config.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting analysis config: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@analysis_bp.route("/config", methods=["PUT"])
def update_analysis_config():
    """Update konfigurasi analisis"""
    try:
        update_data = request.get_json()
        
        service = VendorAnalysisService(db.session)
        config = service.analysis_config
        
        # Validate weights sum to 1.0
        if 'price_weight' in update_data or 'quality_weight' in update_data or \
           'delivery_weight' in update_data or 'reputation_weight' in update_data or \
           'payment_weight' in update_data:
            
            # Get current or new values
            price_weight = update_data.get('price_weight', config.price_weight)
            quality_weight = update_data.get('quality_weight', config.quality_weight)
            delivery_weight = update_data.get('delivery_weight', config.delivery_weight)
            reputation_weight = update_data.get('reputation_weight', config.reputation_weight)
            payment_weight = update_data.get('payment_weight', config.payment_weight)
            
            total_weight = price_weight + quality_weight + delivery_weight + reputation_weight + payment_weight
            
            if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
                return jsonify({
                    'success': False,
                    'message': 'Total weight harus sama dengan 1.0'
                }), 400
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(config, field):
                setattr(config, field, value)
        
        config.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Konfigurasi analisis berhasil diupdate',
            'data': config.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error updating analysis config: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== TIMELINE CONFIGURATION =====

@analysis_bp.route("/timeline-config", methods=["GET"])
def get_timeline_configs():
    """Mendapatkan semua konfigurasi timeline"""
    try:
        budget_service = BudgetIntegrationService(db.session)
        configs = budget_service.get_all_timeline_configs()
        
        return jsonify({
            'success': True,
            'data': [config.to_dict() for config in configs],
            'total': len(configs)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting timeline configs: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@analysis_bp.route("/timeline-config", methods=["POST"])
def create_timeline_config():
    """Buat konfigurasi timeline baru"""
    try:
        config_data = request.get_json()
        
        # Validate required fields
        required_fields = ['min_value', 'vendor_upload_days', 'analysis_days', 'approval_days']
        for field in required_fields:
            if field not in config_data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        budget_service = BudgetIntegrationService(db.session)
        result = budget_service.create_timeline_config(config_data)
        
        return jsonify({
            'success': True,
            'message': 'Konfigurasi timeline berhasil dibuat',
            'data': result.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Error creating timeline config: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@analysis_bp.route("/timeline-config/<float:value>", methods=["GET"])
def get_timeline_for_value(value):
    """Mendapatkan konfigurasi timeline untuk nilai tertentu"""
    try:
        budget_service = BudgetIntegrationService(db.session)
        config = budget_service.get_timeline_config(value)
        
        if not config:
            return jsonify({
                'success': False,
                'message': 'Konfigurasi timeline tidak ditemukan untuk nilai tersebut'
            }), 404
        
        return jsonify({
            'success': True,
            'data': config.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting timeline config for value: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== STATISTICS =====

@analysis_bp.route("/statistics", methods=["GET"])
def get_analysis_statistics():
    """Get analysis statistics"""
    try:
        # Get query parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Convert parameters
        if date_from:
            date_from = datetime.fromisoformat(date_from)
        
        if date_to:
            date_to = datetime.fromisoformat(date_to)
        
        service = VendorAnalysisService(db.session)
        stats = service.get_analysis_statistics(date_from, date_to)
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting analysis statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== BUDGET STATISTICS =====

@analysis_bp.route("/budget-statistics", methods=["GET"])
def get_budget_statistics():
    """Get budget statistics"""
    try:
        budget_year = request.args.get('budget_year')
        if budget_year:
            budget_year = int(budget_year)
        
        budget_service = BudgetIntegrationService(db.session)
        stats = budget_service.get_budget_statistics(budget_year)
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting budget statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== DEPARTMENT BUDGET SUMMARY =====

@analysis_bp.route("/budget-summary/<int:department_id>", methods=["GET"])
def get_department_budget_summary(department_id):
    """Get budget summary untuk departemen"""
    try:
        budget_year = request.args.get('budget_year')
        if budget_year:
            budget_year = int(budget_year)
        else:
            budget_year = datetime.now().year
        
        budget_service = BudgetIntegrationService(db.session)
        summary = budget_service.get_department_budget_summary(department_id, budget_year)
        
        return jsonify({
            'success': True,
            'data': summary
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting department budget summary: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== BUDGET TRANSACTIONS =====

@analysis_bp.route("/budget-transactions", methods=["GET"])
def get_budget_transactions():
    """Mendapatkan budget transactions dengan filter"""
    try:
        # Get query parameters
        filters = {}
        
        if request.args.get('department_id'):
            filters['department_id'] = int(request.args.get('department_id'))
        
        if request.args.get('request_id'):
            filters['request_id'] = int(request.args.get('request_id'))
        
        if request.args.get('transaction_type'):
            filters['transaction_type'] = request.args.get('transaction_type')
        
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        
        if request.args.get('date_from'):
            filters['date_from'] = datetime.fromisoformat(request.args.get('date_from'))
        
        if request.args.get('date_to'):
            filters['date_to'] = datetime.fromisoformat(request.args.get('date_to'))
        
        budget_service = BudgetIntegrationService(db.session)
        results = budget_service.get_budget_transactions(filters)
        
        return jsonify({
            'success': True,
            'data': [result.to_dict() for result in results],
            'total': len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting budget transactions: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@analysis_bp.route("/budget-transactions/<int:transaction_id>/approve", methods=["POST"])
def approve_budget_transaction(transaction_id):
    """Approve budget transaction"""
    try:
        data = request.get_json()
        approved_by = data.get('approved_by')
        notes = data.get('notes', '')
        
        if not approved_by:
            return jsonify({
                'success': False,
                'message': 'Field approved_by is required'
            }), 400
        
        budget_service = BudgetIntegrationService(db.session)
        result = budget_service.approve_budget_transaction(transaction_id, approved_by, notes)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Budget transaction tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Budget transaction berhasil diapprove'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error approving budget transaction: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@analysis_bp.route("/budget-transactions/<int:transaction_id>/reject", methods=["POST"])
def reject_budget_transaction(transaction_id):
    """Reject budget transaction"""
    try:
        data = request.get_json()
        rejected_by = data.get('rejected_by')
        reason = data.get('reason', '')
        
        if not rejected_by:
            return jsonify({
                'success': False,
                'message': 'Field rejected_by is required'
            }), 400
        
        if not reason:
            return jsonify({
                'success': False,
                'message': 'Field reason is required'
            }), 400
        
        budget_service = BudgetIntegrationService(db.session)
        result = budget_service.reject_budget_transaction(transaction_id, rejected_by, reason)
        
        if not result:
            return jsonify({
                'success': False,
                'message': 'Budget transaction tidak ditemukan'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Budget transaction berhasil direject'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error rejecting budget transaction: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== BUDGET VALIDATION =====

@analysis_bp.route("/validate-budget", methods=["POST"])
def validate_budget():
    """Validasi budget untuk request"""
    try:
        data = request.get_json()
        
        required_fields = ['department_id', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        budget_service = BudgetIntegrationService(db.session)
        budget_year = data.get('budget_year', datetime.now().year)
        
        validation = budget_service.validate_budget(
            department_id=data['department_id'],
            amount=float(data['amount']),
            budget_year=budget_year,
            budget_category=data.get('budget_category', 'purchase')
        )
        
        return jsonify({
            'success': True,
            'data': validation
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error validating budget: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ===== BUDGET ADJUSTMENT =====

@analysis_bp.route("/budget-adjustment", methods=["POST"])
def adjust_budget():
    """Adjust budget allocation"""
    try:
        data = request.get_json()
        
        required_fields = ['budget_id', 'adjustment_amount', 'reason', 'adjusted_by']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Field {field} is required'
                }), 400
        
        budget_service = BudgetIntegrationService(db.session)
        result = budget_service.adjust_budget(
            budget_id=data['budget_id'],
            adjustment_amount=float(data['adjustment_amount']),
            reason=data['reason'],
            adjusted_by=data['adjusted_by']
        )
        
        return jsonify({
            'success': True,
            'message': 'Budget berhasil diadjust'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error adjusting budget: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
