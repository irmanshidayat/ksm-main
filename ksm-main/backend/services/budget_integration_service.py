#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Budget Integration Service - Business Logic untuk Sistem Budget Integration
Service untuk budget validation, tracking, dan integrasi dengan accounting system
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from models import (
    BudgetTracking, BudgetTransaction, AnalysisConfig, RequestTimelineConfig
)
from models import RequestPembelian
from models import Department

logger = logging.getLogger(__name__)


class BudgetIntegrationService:
    """Service untuk budget integration dan tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ===== BUDGET TRACKING =====
    
    def create_budget_tracking(self, budget_data: Dict[str, Any]) -> BudgetTracking:
        """Buat budget tracking baru"""
        try:
            # Check if budget already exists
            existing = self.db.query(BudgetTracking).filter(
                BudgetTracking.department_id == budget_data['department_id'],
                BudgetTracking.budget_year == budget_data['budget_year'],
                BudgetTracking.budget_category == budget_data['budget_category']
            ).first()
            
            if existing:
                raise Exception("Budget tracking sudah ada untuk departemen dan kategori ini")
            
            budget_tracking = BudgetTracking(
                department_id=budget_data['department_id'],
                budget_year=budget_data['budget_year'],
                budget_category=budget_data['budget_category'],
                allocated_budget=budget_data['allocated_budget'],
                used_budget=0,
                remaining_budget=budget_data['allocated_budget'],
                status='active',
                notes=budget_data.get('notes', '')
            )
            
            self.db.add(budget_tracking)
            self.db.commit()
            self.db.refresh(budget_tracking)
            
            # Create allocation transaction
            self._create_budget_transaction(
                budget_tracking_id=budget_tracking.id,
                department_id=budget_data['department_id'],
                transaction_type='allocation',
                amount=budget_data['allocated_budget'],
                description=f"Budget allocation untuk {budget_data['budget_category']} tahun {budget_data['budget_year']}",
                reference_type='budget_allocation'
            )
            
            logger.info(f"✅ Created budget tracking: {budget_tracking.id}")
            return budget_tracking
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating budget tracking: {str(e)}")
            raise Exception(f"Gagal membuat budget tracking: {str(e)}")
    
    def get_budget_tracking(self, department_id: int, budget_year: int, budget_category: str = None) -> Optional[BudgetTracking]:
        """Mendapatkan budget tracking"""
        query = self.db.query(BudgetTracking).filter(
            BudgetTracking.department_id == department_id,
            BudgetTracking.budget_year == budget_year
        )
        
        if budget_category:
            query = query.filter(BudgetTracking.budget_category == budget_category)
        
        return query.first()
    
    def get_all_budget_tracking(self, filters: Dict[str, Any] = None) -> List[BudgetTracking]:
        """Mendapatkan semua budget tracking dengan filter"""
        query = self.db.query(BudgetTracking)
        
        if filters:
            if 'department_id' in filters and filters['department_id']:
                query = query.filter(BudgetTracking.department_id == filters['department_id'])
            
            if 'budget_year' in filters and filters['budget_year']:
                query = query.filter(BudgetTracking.budget_year == filters['budget_year'])
            
            if 'budget_category' in filters and filters['budget_category']:
                query = query.filter(BudgetTracking.budget_category == filters['budget_category'])
            
            if 'status' in filters and filters['status']:
                query = query.filter(BudgetTracking.status == filters['status'])
        
        return query.order_by(desc(BudgetTracking.created_at)).all()
    
    def update_budget_tracking(self, budget_id: int, update_data: Dict[str, Any]) -> Optional[BudgetTracking]:
        """Update budget tracking"""
        try:
            budget_tracking = self.db.query(BudgetTracking).filter(BudgetTracking.id == budget_id).first()
            if not budget_tracking:
                return None
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(budget_tracking, field) and field not in ['id', 'created_at', 'used_budget', 'remaining_budget']:
                    setattr(budget_tracking, field, value)
            
            budget_tracking.updated_at = datetime.utcnow()
            budget_tracking.update_remaining_budget()
            
            self.db.commit()
            self.db.refresh(budget_tracking)
            
            logger.info(f"✅ Updated budget tracking: {budget_tracking.id}")
            return budget_tracking
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating budget tracking: {str(e)}")
            raise Exception(f"Gagal update budget tracking: {str(e)}")
    
    # ===== BUDGET VALIDATION =====
    
    def validate_budget(self, department_id: int, amount: float, budget_year: int, budget_category: str = 'purchase') -> Dict[str, Any]:
        """Validasi budget untuk request pembelian"""
        try:
            # Get budget tracking
            budget_tracking = self.get_budget_tracking(department_id, budget_year, budget_category)
            
            if not budget_tracking:
                return {
                    'valid': False,
                    'message': 'Budget tracking tidak ditemukan',
                    'available_budget': 0,
                    'requested_amount': amount,
                    'remaining_budget': 0
                }
            
            # Check if budget is active
            if budget_tracking.status != 'active':
                return {
                    'valid': False,
                    'message': 'Budget tracking tidak aktif',
                    'available_budget': float(budget_tracking.allocated_budget),
                    'requested_amount': amount,
                    'remaining_budget': float(budget_tracking.remaining_budget)
                }
            
            # Check if sufficient budget
            if budget_tracking.remaining_budget < amount:
                return {
                    'valid': False,
                    'message': 'Budget tidak mencukupi',
                    'available_budget': float(budget_tracking.allocated_budget),
                    'requested_amount': amount,
                    'remaining_budget': float(budget_tracking.remaining_budget),
                    'shortfall': float(amount - budget_tracking.remaining_budget)
                }
            
            return {
                'valid': True,
                'message': 'Budget valid',
                'available_budget': float(budget_tracking.allocated_budget),
                'requested_amount': amount,
                'remaining_budget': float(budget_tracking.remaining_budget)
            }
            
        except Exception as e:
            logger.error(f"❌ Error validating budget: {str(e)}")
            return {
                'valid': False,
                'message': f'Error validasi budget: {str(e)}',
                'available_budget': 0,
                'requested_amount': amount,
                'remaining_budget': 0
            }
    
    def reserve_budget(self, department_id: int, amount: float, request_id: int, budget_year: int, budget_category: str = 'purchase') -> bool:
        """Reserve budget untuk request pembelian"""
        try:
            # Validate budget first
            validation = self.validate_budget(department_id, amount, budget_year, budget_category)
            if not validation['valid']:
                raise Exception(validation['message'])
            
            # Get budget tracking
            budget_tracking = self.get_budget_tracking(department_id, budget_year, budget_category)
            
            # Update used budget
            budget_tracking.used_budget += amount
            budget_tracking.update_remaining_budget()
            
            # Create transaction record
            self._create_budget_transaction(
                budget_tracking_id=budget_tracking.id,
                department_id=department_id,
                request_id=request_id,
                transaction_type='usage',
                amount=amount,
                description=f"Budget reservation untuk request pembelian #{request_id}",
                reference_type='purchase_request',
                reference_number=f"REQ-{request_id}"
            )
            
            self.db.commit()
            
            logger.info(f"✅ Reserved budget: {amount} for request: {request_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error reserving budget: {str(e)}")
            raise Exception(f"Gagal reserve budget: {str(e)}")
    
    def release_budget(self, department_id: int, amount: float, request_id: int, budget_year: int, budget_category: str = 'purchase') -> bool:
        """Release budget reservation"""
        try:
            # Get budget tracking
            budget_tracking = self.get_budget_tracking(department_id, budget_year, budget_category)
            if not budget_tracking:
                raise Exception("Budget tracking tidak ditemukan")
            
            # Update used budget
            budget_tracking.used_budget -= amount
            budget_tracking.update_remaining_budget()
            
            # Create transaction record
            self._create_budget_transaction(
                budget_tracking_id=budget_tracking.id,
                department_id=department_id,
                request_id=request_id,
                transaction_type='refund',
                amount=amount,
                description=f"Budget release untuk request pembelian #{request_id}",
                reference_type='purchase_request',
                reference_number=f"REQ-{request_id}"
            )
            
            self.db.commit()
            
            logger.info(f"✅ Released budget: {amount} for request: {request_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error releasing budget: {str(e)}")
            raise Exception(f"Gagal release budget: {str(e)}")
    
    def adjust_budget(self, budget_id: int, adjustment_amount: float, reason: str, adjusted_by: int) -> bool:
        """Adjust budget allocation"""
        try:
            budget_tracking = self.db.query(BudgetTracking).filter(BudgetTracking.id == budget_id).first()
            if not budget_tracking:
                raise Exception("Budget tracking tidak ditemukan")
            
            # Update allocated budget
            old_amount = budget_tracking.allocated_budget
            budget_tracking.allocated_budget += adjustment_amount
            budget_tracking.update_remaining_budget()
            
            # Create transaction record
            self._create_budget_transaction(
                budget_tracking_id=budget_tracking.id,
                department_id=budget_tracking.department_id,
                transaction_type='adjustment',
                amount=adjustment_amount,
                description=f"Budget adjustment: {reason}",
                reference_type='budget_adjustment',
                approved_by=adjusted_by
            )
            
            self.db.commit()
            
            logger.info(f"✅ Adjusted budget: {adjustment_amount} for budget: {budget_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error adjusting budget: {str(e)}")
            raise Exception(f"Gagal adjust budget: {str(e)}")
    
    # ===== BUDGET TRANSACTIONS =====
    
    def _create_budget_transaction(self, budget_tracking_id: int, department_id: int, transaction_type: str, 
                                 amount: float, description: str, reference_type: str = None, 
                                 request_id: int = None, reference_number: str = None, approved_by: int = None) -> BudgetTransaction:
        """Create budget transaction record"""
        try:
            transaction = BudgetTransaction(
                budget_tracking_id=budget_tracking_id,
                department_id=department_id,
                request_id=request_id,
                transaction_type=transaction_type,
                amount=amount,
                description=description,
                reference_type=reference_type,
                reference_number=reference_number,
                status='approved' if approved_by else 'pending',
                approved_by=approved_by,
                approved_at=datetime.utcnow() if approved_by else None
            )
            
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            
            return transaction
            
        except Exception as e:
            logger.error(f"❌ Error creating budget transaction: {str(e)}")
            raise Exception(f"Gagal membuat budget transaction: {str(e)}")
    
    def get_budget_transactions(self, filters: Dict[str, Any] = None) -> List[BudgetTransaction]:
        """Mendapatkan budget transactions dengan filter"""
        query = self.db.query(BudgetTransaction)
        
        if filters:
            if 'department_id' in filters and filters['department_id']:
                query = query.filter(BudgetTransaction.department_id == filters['department_id'])
            
            if 'request_id' in filters and filters['request_id']:
                query = query.filter(BudgetTransaction.request_id == filters['request_id'])
            
            if 'transaction_type' in filters and filters['transaction_type']:
                query = query.filter(BudgetTransaction.transaction_type == filters['transaction_type'])
            
            if 'status' in filters and filters['status']:
                query = query.filter(BudgetTransaction.status == filters['status'])
            
            if 'date_from' in filters and filters['date_from']:
                query = query.filter(BudgetTransaction.transaction_date >= filters['date_from'])
            
            if 'date_to' in filters and filters['date_to']:
                query = query.filter(BudgetTransaction.transaction_date <= filters['date_to'])
        
        return query.order_by(desc(BudgetTransaction.transaction_date)).all()
    
    def approve_budget_transaction(self, transaction_id: int, approved_by: int, notes: str = None) -> bool:
        """Approve budget transaction"""
        try:
            transaction = self.db.query(BudgetTransaction).filter(BudgetTransaction.id == transaction_id).first()
            if not transaction:
                return False
            
            if transaction.status != 'pending':
                raise Exception("Transaction sudah diproses")
            
            transaction.status = 'approved'
            transaction.approved_by = approved_by
            transaction.approved_at = datetime.utcnow()
            
            if notes:
                transaction.description += f" | Notes: {notes}"
            
            self.db.commit()
            
            logger.info(f"✅ Approved budget transaction: {transaction_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error approving budget transaction: {str(e)}")
            raise Exception(f"Gagal approve budget transaction: {str(e)}")
    
    def reject_budget_transaction(self, transaction_id: int, rejected_by: int, reason: str) -> bool:
        """Reject budget transaction"""
        try:
            transaction = self.db.query(BudgetTransaction).filter(BudgetTransaction.id == transaction_id).first()
            if not transaction:
                return False
            
            if transaction.status != 'pending':
                raise Exception("Transaction sudah diproses")
            
            transaction.status = 'rejected'
            transaction.approved_by = rejected_by
            transaction.approved_at = datetime.utcnow()
            transaction.description += f" | Rejected: {reason}"
            
            self.db.commit()
            
            logger.info(f"✅ Rejected budget transaction: {transaction_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error rejecting budget transaction: {str(e)}")
            raise Exception(f"Gagal reject budget transaction: {str(e)}")
    
    # ===== INTEGRATION WITH REQUEST PEMBELIAN =====
    
    def process_request_budget(self, request_id: int, action: str) -> bool:
        """Process budget untuk request pembelian"""
        try:
            request = self.db.query(RequestPembelian).filter(RequestPembelian.id == request_id).first()
            if not request:
                raise Exception("Request tidak ditemukan")
            
            if not request.total_budget:
                return True  # No budget to process
            
            budget_year = request.created_at.year
            amount = float(request.total_budget)
            
            if action == 'reserve':
                return self.reserve_budget(
                    department_id=request.department_id,
                    amount=amount,
                    request_id=request_id,
                    budget_year=budget_year
                )
            elif action == 'release':
                return self.release_budget(
                    department_id=request.department_id,
                    amount=amount,
                    request_id=request_id,
                    budget_year=budget_year
                )
            else:
                raise Exception("Action tidak valid")
                
        except Exception as e:
            logger.error(f"❌ Error processing request budget: {str(e)}")
            raise Exception(f"Gagal process budget request: {str(e)}")
    
    def get_department_budget_summary(self, department_id: int, budget_year: int) -> Dict[str, Any]:
        """Get budget summary untuk departemen"""
        try:
            budget_trackings = self.db.query(BudgetTracking).filter(
                BudgetTracking.department_id == department_id,
                BudgetTracking.budget_year == budget_year
            ).all()
            
            if not budget_trackings:
                return {
                    'department_id': department_id,
                    'budget_year': budget_year,
                    'total_allocated': 0,
                    'total_used': 0,
                    'total_remaining': 0,
                    'categories': []
                }
            
            total_allocated = sum(float(bt.allocated_budget) for bt in budget_trackings)
            total_used = sum(float(bt.used_budget) for bt in budget_trackings)
            total_remaining = sum(float(bt.remaining_budget) for bt in budget_trackings)
            
            categories = []
            for bt in budget_trackings:
                categories.append({
                    'category': bt.budget_category,
                    'allocated': float(bt.allocated_budget),
                    'used': float(bt.used_budget),
                    'remaining': float(bt.remaining_budget),
                    'usage_percentage': bt.get_usage_percentage(),
                    'status': bt.status
                })
            
            return {
                'department_id': department_id,
                'budget_year': budget_year,
                'total_allocated': total_allocated,
                'total_used': total_used,
                'total_remaining': total_remaining,
                'overall_usage_percentage': round((total_used / total_allocated) * 100, 2) if total_allocated > 0 else 0,
                'categories': categories
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting department budget summary: {str(e)}")
            raise Exception(f"Gagal mendapatkan budget summary: {str(e)}")
    
    # ===== STATISTICS =====
    
    def get_budget_statistics(self, budget_year: int = None) -> Dict[str, Any]:
        """Get budget statistics"""
        try:
            if not budget_year:
                budget_year = datetime.now().year
            
            budget_trackings = self.db.query(BudgetTracking).filter(
                BudgetTracking.budget_year == budget_year
            ).all()
            
            if not budget_trackings:
                return {
                    'budget_year': budget_year,
                    'total_departments': 0,
                    'total_allocated': 0,
                    'total_used': 0,
                    'total_remaining': 0,
                    'by_department': {},
                    'by_category': {}
                }
            
            stats = {
                'budget_year': budget_year,
                'total_departments': len(set(bt.department_id for bt in budget_trackings)),
                'total_allocated': sum(float(bt.allocated_budget) for bt in budget_trackings),
                'total_used': sum(float(bt.used_budget) for bt in budget_trackings),
                'total_remaining': sum(float(bt.remaining_budget) for bt in budget_trackings),
                'by_department': {},
                'by_category': {}
            }
            
            # Calculate by department
            dept_totals = {}
            for bt in budget_trackings:
                dept_id = bt.department_id
                if dept_id not in dept_totals:
                    dept_totals[dept_id] = {
                        'allocated': 0,
                        'used': 0,
                        'remaining': 0
                    }
                
                dept_totals[dept_id]['allocated'] += float(bt.allocated_budget)
                dept_totals[dept_id]['used'] += float(bt.used_budget)
                dept_totals[dept_id]['remaining'] += float(bt.remaining_budget)
            
            stats['by_department'] = dept_totals
            
            # Calculate by category
            cat_totals = {}
            for bt in budget_trackings:
                category = bt.budget_category
                if category not in cat_totals:
                    cat_totals[category] = {
                        'allocated': 0,
                        'used': 0,
                        'remaining': 0
                    }
                
                cat_totals[category]['allocated'] += float(bt.allocated_budget)
                cat_totals[category]['used'] += float(bt.used_budget)
                cat_totals[category]['remaining'] += float(bt.remaining_budget)
            
            stats['by_category'] = cat_totals
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting budget statistics: {str(e)}")
            raise Exception(f"Gagal mendapatkan statistik budget: {str(e)}")
    
    # ===== TIMELINE CONFIGURATION =====
    
    def get_timeline_config(self, value: float) -> Optional[RequestTimelineConfig]:
        """Get timeline configuration for value"""
        return RequestTimelineConfig.get_timeline_for_value(value)
    
    def create_timeline_config(self, config_data: Dict[str, Any]) -> RequestTimelineConfig:
        """Create timeline configuration"""
        try:
            config = RequestTimelineConfig(
                min_value=config_data['min_value'],
                max_value=config_data.get('max_value'),
                vendor_upload_days=config_data['vendor_upload_days'],
                analysis_days=config_data['analysis_days'],
                approval_days=config_data['approval_days'],
                description=config_data.get('description', '')
            )
            
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            
            logger.info(f"✅ Created timeline config: {config.id}")
            return config
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating timeline config: {str(e)}")
            raise Exception(f"Gagal membuat timeline config: {str(e)}")
    
    def get_all_timeline_configs(self) -> List[RequestTimelineConfig]:
        """Get all timeline configurations"""
        return self.db.query(RequestTimelineConfig).filter(
            RequestTimelineConfig.is_active == True
        ).order_by(RequestTimelineConfig.min_value).all()
