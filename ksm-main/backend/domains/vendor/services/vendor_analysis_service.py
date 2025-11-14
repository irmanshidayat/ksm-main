#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Analysis Service - Business Logic untuk Sistem Analisis Vendor
Service untuk scoring algorithm, recommendation engine, dan analisis vendor
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging
import json
import statistics

from models import (
    RequestPembelian, VendorPenawaran, VendorAnalysis, Vendor, VendorPenawaranFile
)
from models import AnalysisConfig, RequestTimelineConfig

logger = logging.getLogger(__name__)


class VendorAnalysisService:
    """Service untuk analisis vendor dan recommendation"""
    
    def __init__(self, db: Session):
        self.db = db
        self.analysis_config = self._get_analysis_config()
    
    # ===== MAIN ANALYSIS METHODS =====
    
    def analyze_vendor_penawarans(self, request_id: int, analysis_method: str = 'automated') -> Dict[str, Any]:
        """Analisis semua penawaran vendor untuk request tertentu"""
        try:
            request = self.db.query(RequestPembelian).filter(RequestPembelian.id == request_id).first()
            if not request:
                raise Exception("Request tidak ditemukan")
            
            # Get all vendor penawarans
            penawarans = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.request_id == request_id,
                VendorPenawaran.status == 'submitted'
            ).all()
            
            if not penawarans:
                raise Exception("Belum ada penawaran vendor")
            
            # Perform analysis
            analysis_results = []
            for penawaran in penawarans:
                result = self._analyze_single_penawaran(penawaran, analysis_method)
                analysis_results.append(result)
            
            # Rank vendors
            ranked_results = self._rank_vendors(analysis_results)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(ranked_results, request)
            
            # Create analysis report
            report = self._create_analysis_report(request, ranked_results, recommendation)
            
            # Save analysis results to database
            self._save_analysis_results(request_id, analysis_results, analysis_method)
            
            logger.info(f"✅ Completed analysis for request: {request.reference_id}")
            
            return {
                'request_id': request_id,
                'analysis_method': analysis_method,
                'total_vendors': len(penawarans),
                'ranked_results': ranked_results,
                'recommendation': recommendation,
                'analysis_report': report,
                'analysis_date': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing vendor penawarans: {str(e)}")
            raise Exception(f"Gagal analisis vendor: {str(e)}")
    
    def get_analysis_results(self, request_id: int) -> Optional[Dict[str, Any]]:
        """Mendapatkan hasil analisis untuk request tertentu"""
        try:
            request = self.db.query(RequestPembelian).filter(RequestPembelian.id == request_id).first()
            if not request:
                return None
            
            # Get analysis results
            analyses = self.db.query(VendorAnalysis).filter(
                VendorAnalysis.request_id == request_id
            ).all()
            
            if not analyses:
                return None
            
            # Get vendor penawarans
            penawarans = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.request_id == request_id
            ).all()
            
            # Build results
            results = []
            for analysis in analyses:
                penawaran = next((p for p in penawarans if p.id == analysis.vendor_penawaran_id), None)
                if penawaran:
                    results.append({
                        'analysis': analysis.to_dict(),
                        'penawaran': penawaran.to_dict(),
                        'vendor': penawaran.vendor.to_dict() if penawaran.vendor else None
                    })
            
            # Sort by total score
            results.sort(key=lambda x: x['analysis']['total_score'] or 0, reverse=True)
            
            return {
                'request_id': request_id,
                'request': request.to_dict(),
                'analysis_results': results,
                'total_vendors': len(results),
                'analysis_date': analyses[0].analysis_date.isoformat() if analyses else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting analysis results: {str(e)}")
            raise Exception(f"Gagal mendapatkan hasil analisis: {str(e)}")
    
    # ===== SCORING ALGORITHMS =====
    
    def _analyze_single_penawaran(self, penawaran: VendorPenawaran, analysis_method: str) -> Dict[str, Any]:
        """Analisis single penawaran vendor"""
        try:
            if analysis_method == 'automated':
                return self._automated_analysis(penawaran)
            elif analysis_method == 'simplified':
                return self._simplified_analysis(penawaran)
            elif analysis_method == 'manual':
                return self._manual_analysis(penawaran)
            else:
                raise Exception("Metode analisis tidak valid")
                
        except Exception as e:
            logger.error(f"❌ Error analyzing single penawaran: {str(e)}")
            raise Exception(f"Gagal analisis penawaran: {str(e)}")
    
    def _automated_analysis(self, penawaran: VendorPenawaran) -> Dict[str, Any]:
        """Automated analysis dengan rule-based scoring"""
        try:
            # Price Score (40%)
            price_score = self._calculate_price_score(penawaran)
            
            # Quality Score (25%)
            quality_score = self._calculate_quality_score(penawaran)
            
            # Delivery Score (20%)
            delivery_score = self._calculate_delivery_score(penawaran)
            
            # Reputation Score (10%)
            reputation_score = self._calculate_reputation_score(penawaran)
            
            # Payment Score (5%)
            payment_score = self._calculate_payment_score(penawaran)
            
            # Calculate total score
            total_score = (
                price_score * self.analysis_config.price_weight +
                quality_score * self.analysis_config.quality_weight +
                delivery_score * self.analysis_config.delivery_weight +
                reputation_score * self.analysis_config.reputation_weight +
                payment_score * self.analysis_config.payment_weight
            )
            
            # Determine recommendation level
            recommendation_level = self._determine_recommendation_level(total_score)
            
            return {
                'penawaran_id': penawaran.id,
                'vendor_id': penawaran.vendor_id,
                'price_score': price_score,
                'quality_score': quality_score,
                'delivery_score': delivery_score,
                'reputation_score': reputation_score,
                'payment_score': payment_score,
                'total_score': total_score,
                'recommendation_level': recommendation_level,
                'analysis_method': 'automated'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in automated analysis: {str(e)}")
            raise Exception(f"Gagal automated analysis: {str(e)}")
    
    def _simplified_analysis(self, penawaran: VendorPenawaran) -> Dict[str, Any]:
        """Simplified analysis untuk fallback"""
        try:
            # Simple scoring based on basic criteria
            price_score = 50  # Default score
            quality_score = 50
            delivery_score = 50
            reputation_score = 50
            payment_score = 50
            
            # Adjust based on available data
            if penawaran.total_quoted_price:
                price_score = min(100, max(0, 100 - (float(penawaran.total_quoted_price) / 1000000) * 10))
            
            if penawaran.delivery_time_days:
                if penawaran.delivery_time_days <= 7:
                    delivery_score = 90
                elif penawaran.delivery_time_days <= 14:
                    delivery_score = 70
                elif penawaran.delivery_time_days <= 30:
                    delivery_score = 50
                else:
                    delivery_score = 30
            
            if penawaran.quality_rating:
                quality_score = penawaran.quality_rating * 20  # Convert 1-5 to 20-100
            
            # Calculate total score
            total_score = (
                price_score * 0.4 +
                quality_score * 0.25 +
                delivery_score * 0.2 +
                reputation_score * 0.1 +
                payment_score * 0.05
            )
            
            recommendation_level = self._determine_recommendation_level(total_score)
            
            return {
                'penawaran_id': penawaran.id,
                'vendor_id': penawaran.vendor_id,
                'price_score': price_score,
                'quality_score': quality_score,
                'delivery_score': delivery_score,
                'reputation_score': reputation_score,
                'payment_score': payment_score,
                'total_score': total_score,
                'recommendation_level': recommendation_level,
                'analysis_method': 'simplified'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in simplified analysis: {str(e)}")
            raise Exception(f"Gagal simplified analysis: {str(e)}")
    
    def _manual_analysis(self, penawaran: VendorPenawaran) -> Dict[str, Any]:
        """Manual analysis untuk admin input"""
        try:
            # Return default scores for manual input
            return {
                'penawaran_id': penawaran.id,
                'vendor_id': penawaran.vendor_id,
                'price_score': 0,  # To be filled manually
                'quality_score': 0,
                'delivery_score': 0,
                'reputation_score': 0,
                'payment_score': 0,
                'total_score': 0,
                'recommendation_level': 'not_recommend',
                'analysis_method': 'manual'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in manual analysis: {str(e)}")
            raise Exception(f"Gagal manual analysis: {str(e)}")
    
    # ===== SCORING COMPONENTS =====
    
    def _calculate_price_score(self, penawaran: VendorPenawaran) -> float:
        """Calculate price score (40% weight)"""
        try:
            if not penawaran.total_quoted_price:
                return 50  # Default score if no price
            
            # Get all prices for comparison
            all_prices = self.db.query(VendorPenawaran.total_quoted_price).filter(
                VendorPenawaran.request_id == penawaran.request_id,
                VendorPenawaran.status == 'submitted',
                VendorPenawaran.total_quoted_price.isnot(None)
            ).all()
            
            if len(all_prices) < 2:
                return 70  # Default if not enough data for comparison
            
            prices = [float(price[0]) for price in all_prices]
            min_price = min(prices)
            max_price = max(prices)
            current_price = float(penawaran.total_quoted_price)
            
            # Calculate score based on price position
            if max_price == min_price:
                return 80  # All prices are same
            
            # Lower price gets higher score
            price_ratio = (max_price - current_price) / (max_price - min_price)
            score = 60 + (price_ratio * 40)  # Score between 60-100
            
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating price score: {str(e)}")
            return 50
    
    def _calculate_quality_score(self, penawaran: VendorPenawaran) -> float:
        """Calculate quality score (25% weight)"""
        try:
            score = 50  # Base score
            
            # Check quality rating
            if penawaran.quality_rating:
                score += (penawaran.quality_rating - 3) * 15  # Adjust based on rating
            
            # Check if vendor has quality certifications (from files)
            quality_files = self.db.query(VendorPenawaranFile).filter(
                VendorPenawaranFile.vendor_penawaran_id == penawaran.id,
                or_(
                    VendorPenawaranFile.file_name.ilike('%sertifikat%'),
                    VendorPenawaranFile.file_name.ilike('%certificate%'),
                    VendorPenawaranFile.file_name.ilike('%iso%'),
                    VendorPenawaranFile.file_name.ilike('%quality%')
                )
            ).count()
            
            if quality_files > 0:
                score += 20
            
            # Check vendor category
            if penawaran.vendor.vendor_category == 'preferred':
                score += 15
            elif penawaran.vendor.vendor_category == 'specialized':
                score += 10
            
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating quality score: {str(e)}")
            return 50
    
    def _calculate_delivery_score(self, penawaran: VendorPenawaran) -> float:
        """Calculate delivery score (20% weight)"""
        try:
            if not penawaran.delivery_time_days:
                return 50  # Default score
            
            delivery_days = penawaran.delivery_time_days
            
            # Score based on delivery time
            if delivery_days <= 3:
                return 100
            elif delivery_days <= 7:
                return 90
            elif delivery_days <= 14:
                return 80
            elif delivery_days <= 21:
                return 70
            elif delivery_days <= 30:
                return 60
            elif delivery_days <= 45:
                return 50
            elif delivery_days <= 60:
                return 40
            else:
                return 30
                
        except Exception as e:
            logger.error(f"❌ Error calculating delivery score: {str(e)}")
            return 50
    
    def _calculate_reputation_score(self, penawaran: VendorPenawaran) -> float:
        """Calculate reputation score (10% weight)"""
        try:
            score = 50  # Base score
            
            # Check vendor status
            if penawaran.vendor.status == 'approved':
                score += 20
            
            # Check vendor category
            if penawaran.vendor.vendor_category == 'preferred':
                score += 25
            elif penawaran.vendor.vendor_category == 'specialized':
                score += 15
            elif penawaran.vendor.vendor_category == 'general':
                score += 5
            
            # Check historical performance (if available)
            historical_penawarans = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.vendor_id == penawaran.vendor_id,
                VendorPenawaran.status == 'selected'
            ).count()
            
            if historical_penawarans > 0:
                score += min(20, historical_penawarans * 2)
            
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating reputation score: {str(e)}")
            return 50
    
    def _calculate_payment_score(self, penawaran: VendorPenawaran) -> float:
        """Calculate payment terms score (5% weight)"""
        try:
            score = 50  # Base score
            
            if not penawaran.payment_terms:
                return score
            
            payment_terms = penawaran.payment_terms.lower()
            
            # Score based on payment terms
            if 'cash' in payment_terms or 'lunas' in payment_terms:
                score = 100
            elif 'net 30' in payment_terms or '30 hari' in payment_terms:
                score = 80
            elif 'net 15' in payment_terms or '15 hari' in payment_terms:
                score = 90
            elif 'net 7' in payment_terms or '7 hari' in payment_terms:
                score = 95
            elif 'net 60' in payment_terms or '60 hari' in payment_terms:
                score = 60
            elif 'net 90' in payment_terms or '90 hari' in payment_terms:
                score = 40
            elif 'advance' in payment_terms or 'uang muka' in payment_terms:
                score = 70
            
            return min(100, max(0, score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating payment score: {str(e)}")
            return 50
    
    def _determine_recommendation_level(self, total_score: float) -> str:
        """Determine recommendation level based on total score"""
        if total_score >= 90:
            return 'strongly_recommend'
        elif total_score >= 75:
            return 'recommend'
        elif total_score >= 60:
            return 'consider'
        else:
            return 'not_recommend'
    
    # ===== RANKING AND RECOMMENDATION =====
    
    def _rank_vendors(self, analysis_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank vendors berdasarkan total score"""
        try:
            # Sort by total score descending
            ranked = sorted(analysis_results, key=lambda x: x['total_score'], reverse=True)
            
            # Add rank
            for i, result in enumerate(ranked):
                result['rank'] = i + 1
            
            return ranked
            
        except Exception as e:
            logger.error(f"❌ Error ranking vendors: {str(e)}")
            return analysis_results
    
    def _generate_recommendation(self, ranked_results: List[Dict[str, Any]], request: RequestPembelian) -> Dict[str, Any]:
        """Generate recommendation untuk admin"""
        try:
            if not ranked_results:
                return {
                    'recommended_vendor': None,
                    'recommendation_reason': 'Tidak ada penawaran vendor',
                    'risk_level': 'high',
                    'alternative_vendors': []
                }
            
            # Get top vendor
            top_vendor = ranked_results[0]
            
            # Determine risk level
            risk_level = 'low'
            if top_vendor['total_score'] < 70:
                risk_level = 'high'
            elif top_vendor['total_score'] < 80:
                risk_level = 'medium'
            
            # Get alternative vendors
            alternative_vendors = []
            for result in ranked_results[1:3]:  # Top 2 alternatives
                if result['total_score'] >= 60:
                    alternative_vendors.append({
                        'vendor_id': result['vendor_id'],
                        'total_score': result['total_score'],
                        'recommendation_level': result['recommendation_level']
                    })
            
            # Generate recommendation reason
            recommendation_reason = self._generate_recommendation_reason(top_vendor, request)
            
            return {
                'recommended_vendor': {
                    'vendor_id': top_vendor['vendor_id'],
                    'total_score': top_vendor['total_score'],
                    'recommendation_level': top_vendor['recommendation_level'],
                    'price_score': top_vendor['price_score'],
                    'quality_score': top_vendor['quality_score'],
                    'delivery_score': top_vendor['delivery_score']
                },
                'recommendation_reason': recommendation_reason,
                'risk_level': risk_level,
                'alternative_vendors': alternative_vendors,
                'total_vendors_analyzed': len(ranked_results)
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating recommendation: {str(e)}")
            return {
                'recommended_vendor': None,
                'recommendation_reason': 'Error dalam analisis',
                'risk_level': 'high',
                'alternative_vendors': []
            }
    
    def _generate_recommendation_reason(self, top_vendor: Dict[str, Any], request: RequestPembelian) -> str:
        """Generate recommendation reason"""
        try:
            reasons = []
            
            # Price reason
            if top_vendor['price_score'] >= 80:
                reasons.append("Harga kompetitif")
            elif top_vendor['price_score'] >= 60:
                reasons.append("Harga wajar")
            
            # Quality reason
            if top_vendor['quality_score'] >= 80:
                reasons.append("Kualitas tinggi")
            elif top_vendor['quality_score'] >= 60:
                reasons.append("Kualitas memadai")
            
            # Delivery reason
            if top_vendor['delivery_score'] >= 80:
                reasons.append("Pengiriman cepat")
            elif top_vendor['delivery_score'] >= 60:
                reasons.append("Pengiriman tepat waktu")
            
            # Overall score reason
            if top_vendor['total_score'] >= 90:
                reasons.append("Skor keseluruhan sangat baik")
            elif top_vendor['total_score'] >= 75:
                reasons.append("Skor keseluruhan baik")
            
            if reasons:
                return f"Direkomendasikan karena: {', '.join(reasons)}"
            else:
                return "Direkomendasikan berdasarkan analisis komprehensif"
                
        except Exception as e:
            logger.error(f"❌ Error generating recommendation reason: {str(e)}")
            return "Direkomendasikan berdasarkan analisis sistem"
    
    # ===== REPORT GENERATION =====
    
    def _create_analysis_report(self, request: RequestPembelian, ranked_results: List[Dict[str, Any]], recommendation: Dict[str, Any]) -> str:
        """Create detailed analysis report"""
        try:
            report = f"""
# LAPORAN ANALISIS VENDOR
## Request: {request.title}
## Reference ID: {request.reference_id}
## Tanggal Analisis: {datetime.now().strftime('%d/%m/%Y %H:%M')}

## RINGKASAN
- Total Vendor: {len(ranked_results)}
- Vendor Terbaik: Vendor ID {recommendation['recommended_vendor']['vendor_id'] if recommendation['recommended_vendor'] else 'N/A'}
- Skor Terbaik: {recommendation['recommended_vendor']['total_score'] if recommendation['recommended_vendor'] else 'N/A'}
- Level Risiko: {recommendation['risk_level'].upper()}

## REKOMENDASI
{recommendation['recommendation_reason']}

## DETAIL ANALISIS
"""
            
            for i, result in enumerate(ranked_results[:5]):  # Top 5 vendors
                report += f"""
### Peringkat {i+1}: Vendor ID {result['vendor_id']}
- **Total Skor**: {result['total_score']:.2f}
- **Harga**: {result['price_score']:.2f}
- **Kualitas**: {result['quality_score']:.2f}
- **Pengiriman**: {result['delivery_score']:.2f}
- **Reputasi**: {result['reputation_score']:.2f}
- **Pembayaran**: {result['payment_score']:.2f}
- **Rekomendasi**: {result['recommendation_level'].replace('_', ' ').title()}
"""
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Error creating analysis report: {str(e)}")
            return "Error dalam pembuatan laporan analisis"
    
    # ===== DATABASE OPERATIONS =====
    
    def _save_analysis_results(self, request_id: int, analysis_results: List[Dict[str, Any]], analysis_method: str):
        """Save analysis results to database"""
        try:
            for result in analysis_results:
                # Check if analysis already exists
                existing = self.db.query(VendorAnalysis).filter(
                    VendorAnalysis.request_id == request_id,
                    VendorAnalysis.vendor_penawaran_id == result['penawaran_id']
                ).first()
                
                if existing:
                    # Update existing
                    existing.price_score = result['price_score']
                    existing.quality_score = result['quality_score']
                    existing.delivery_score = result['delivery_score']
                    existing.reputation_score = result['reputation_score']
                    existing.payment_score = result['payment_score']
                    existing.total_score = result['total_score']
                    existing.recommendation_level = result['recommendation_level']
                    existing.analysis_method = analysis_method
                    existing.analysis_date = datetime.utcnow()
                else:
                    # Create new
                    analysis = VendorAnalysis(
                        request_id=request_id,
                        vendor_penawaran_id=result['penawaran_id'],
                        price_score=result['price_score'],
                        quality_score=result['quality_score'],
                        delivery_score=result['delivery_score'],
                        reputation_score=result['reputation_score'],
                        payment_score=result['payment_score'],
                        total_score=result['total_score'],
                        recommendation_level=result['recommendation_level'],
                        analysis_method=analysis_method
                    )
                    self.db.add(analysis)
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error saving analysis results: {str(e)}")
            raise Exception(f"Gagal menyimpan hasil analisis: {str(e)}")
    
    def _get_analysis_config(self) -> AnalysisConfig:
        """Get analysis configuration"""
        config = self.db.query(AnalysisConfig).filter(AnalysisConfig.is_active == True).first()
        if not config:
            # Create default config
            config = AnalysisConfig(
                price_weight=0.40,
                quality_weight=0.25,
                delivery_weight=0.20,
                reputation_weight=0.10,
                payment_weight=0.05,
                ml_enabled=True,
                auto_analysis_enabled=True,
                min_vendor_count=2,
                max_analysis_days=3,
                min_score_threshold=50.00,
                price_variance_threshold=30.00,
                quality_threshold=70.00
            )
            self.db.add(config)
            self.db.commit()
        return config
    
    # ===== STATISTICS =====
    
    def get_analysis_statistics(self, date_from: datetime = None, date_to: datetime = None) -> Dict[str, Any]:
        """Get analysis statistics"""
        try:
            query = self.db.query(VendorAnalysis)
            
            if date_from:
                query = query.filter(VendorAnalysis.analysis_date >= date_from)
            
            if date_to:
                query = query.filter(VendorAnalysis.analysis_date <= date_to)
            
            analyses = query.all()
            
            if not analyses:
                return {
                    'total_analyses': 0,
                    'average_score': 0,
                    'by_recommendation': {},
                    'by_method': {}
                }
            
            stats = {
                'total_analyses': len(analyses),
                'average_score': statistics.mean([a.total_score for a in analyses if a.total_score]),
                'by_recommendation': {},
                'by_method': {}
            }
            
            for analysis in analyses:
                # Recommendation level count
                level = analysis.recommendation_level
                stats['by_recommendation'][level] = stats['by_recommendation'].get(level, 0) + 1
                
                # Method count
                method = analysis.analysis_method
                stats['by_method'][method] = stats['by_method'].get(method, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting analysis statistics: {str(e)}")
            raise Exception(f"Gagal mendapatkan statistik analisis: {str(e)}")
