#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Catalog Service - Business Logic untuk Sistem Vendor Catalog Management
Service untuk mengelola katalog barang vendor dan perbandingan penawaran
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import csv
import io

from models import (
    VendorPenawaran, VendorPenawaranItem, VendorPenawaranFile,
    Vendor, VendorCategory, RequestPembelian, RequestPembelianItem
)

logger = logging.getLogger(__name__)


class VendorCatalogService:
    """Service untuk mengelola katalog barang vendor"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_vendor_catalog_by_reference(self, reference_id: str) -> Dict[str, Any]:
        """Mendapatkan semua barang vendor untuk reference ID tertentu"""
        try:
            # Get request by reference_id
            request = self.db.query(RequestPembelian).filter(
                RequestPembelian.reference_id == reference_id
            ).first()
            
            if not request:
                return {
                    'success': False,
                    'message': f'Request dengan reference ID {reference_id} tidak ditemukan'
                }
            
            # Get all penawaran for this request
            penawarans = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.request_id == request.id
            ).all()
            
            if not penawarans:
                return {
                    'success': True,
                    'data': {
                        'request': request.to_dict(),
                        'penawarans': [],
                        'summary': {
                            'total_vendors': 0,
                            'total_items': 0,
                            'total_value': 0
                        }
                    }
                }
            
            # Get penawaran items with vendor info
            formatted_penawarans = []
            total_items = 0
            total_value = 0
            
            for penawaran in penawarans:
                # Get vendor info
                vendor = self.db.query(Vendor).filter(Vendor.id == penawaran.vendor_id).first()
                
                # Get penawaran items
                items = self.db.query(VendorPenawaranItem).filter(
                    VendorPenawaranItem.vendor_penawaran_id == penawaran.id
                ).all()
                
                # Format items with request item info
                formatted_items = []
                for item in items:
                    # Get request item info
                    request_item = self.db.query(RequestPembelianItem).filter(
                        RequestPembelianItem.id == item.request_item_id
                    ).first()
                    
                    item_data = item.to_dict()
                    if request_item:
                        # Get request item data using to_dict() method to get nama_barang
                        request_item_data = request_item.to_dict()
                        item_data.update({
                            'request_item_name': request_item_data.get('nama_barang', 'Nama Barang Tidak Diketahui'),
                            'request_item_specifications': request_item.specifications,
                            'request_item_quantity': request_item.quantity,
                            'request_item_unit': request_item_data.get('satuan', 'pcs')
                        })
                    
                    formatted_items.append(item_data)
                    total_items += 1
                    total_value += float(item.vendor_total_price or 0)
                
                penawaran_data = penawaran.to_dict()
                penawaran_data.update({
                    'vendor': vendor.to_dict() if vendor else None,
                    'items': formatted_items,
                    'items_count': len(formatted_items)
                })
                
                formatted_penawarans.append(penawaran_data)
            
            return {
                'success': True,
                'data': {
                    'request': request.to_dict(),
                    'penawarans': formatted_penawarans,
                    'summary': {
                        'total_vendors': len(penawarans),
                        'total_items': total_items,
                        'total_value': total_value
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting vendor catalog by reference: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_all_vendor_catalog_items(self, page: int = 1, per_page: int = 10, 
                                   filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Mendapatkan semua barang vendor dengan pagination dan filter"""
        try:
            if filters is None:
                filters = {}
            
            # Debug logging
            logger.info(f"🔍 get_all_vendor_catalog_items - Input filters: {filters}")
            logger.info(f"🔍 get_all_vendor_catalog_items - Search term: {filters.get('search')}")
            
            # Base query with joins
            query = self.db.query(
                VendorPenawaranItem,
                VendorPenawaran,
                Vendor,
                RequestPembelian,
                RequestPembelianItem
            ).join(
                VendorPenawaran, VendorPenawaranItem.vendor_penawaran_id == VendorPenawaran.id
            ).join(
                Vendor, VendorPenawaran.vendor_id == Vendor.id
            ).join(
                RequestPembelian, VendorPenawaran.request_id == RequestPembelian.id
            ).outerjoin(
                RequestPembelianItem, VendorPenawaranItem.request_item_id == RequestPembelianItem.id
            )
            
            # Apply filters
            if filters.get('vendor_id'):
                query = query.filter(Vendor.id == filters['vendor_id'])
            
            if filters.get('reference_id'):
                query = query.filter(RequestPembelian.reference_id.like(f"%{filters['reference_id']}%"))
            
            if filters.get('status'):
                query = query.filter(VendorPenawaran.status == filters['status'])
            
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                logger.info(f"🔍 Applying search filter with term: {search_term}")
                
                # Enhanced search implementation with all requested fields
                search_conditions = [
                    # Search in vendor company name
                    Vendor.company_name.like(search_term),
                    # Search in vendor email
                    Vendor.email.like(search_term),
                    # Search in request reference ID
                    RequestPembelian.reference_id.like(search_term),
                    # Search in request title
                    RequestPembelian.title.like(search_term),
                    # Search in vendor specifications
                    VendorPenawaranItem.vendor_specifications.like(search_term),
                    # Search in request item specifications
                    RequestPembelianItem.specifications.like(search_term),
                    # Search in vendor merk field
                    VendorPenawaranItem.vendor_merk.like(search_term),
                    # Search in kategori field
                    VendorPenawaranItem.kategori.like(search_term)
                ]
                
                # Add search in barang table if available
                try:
                    from models import Barang, KategoriBarang
                    
                    # Search in barang nama_barang
                    barang_search_exists = self.db.query(Barang.id).join(
                        RequestPembelianItem, RequestPembelianItem.barang_id == Barang.id
                    ).filter(
                        and_(
                            RequestPembelianItem.id == VendorPenawaranItem.request_item_id,
                            Barang.nama_barang.like(search_term)
                        )
                    ).exists()
                    search_conditions.append(barang_search_exists)
                    
                    # Search in kategori barang
                    kategori_search_exists = self.db.query(Barang.id).join(
                        RequestPembelianItem, RequestPembelianItem.barang_id == Barang.id
                    ).join(
                        KategoriBarang, KategoriBarang.id == Barang.kategori_id
                    ).filter(
                        and_(
                            RequestPembelianItem.id == VendorPenawaranItem.request_item_id,
                            KategoriBarang.nama_kategori.like(search_term)
                        )
                    ).exists()
                    search_conditions.append(kategori_search_exists)
                    
                    # Search in barang kode_barang (merek)
                    merek_search_exists = self.db.query(Barang.id).join(
                        RequestPembelianItem, RequestPembelianItem.barang_id == Barang.id
                    ).filter(
                        and_(
                            RequestPembelianItem.id == VendorPenawaranItem.request_item_id,
                            Barang.kode_barang.like(search_term)
                        )
                    ).exists()
                    search_conditions.append(merek_search_exists)
                    
                    logger.info(f"🔍 Added barang, kategori, and merek search conditions")
                except ImportError:
                    # If Barang model is not available, skip this search
                    logger.info(f"🔍 Barang model not available, skipping barang search")
                    pass
                
                logger.info(f"🔍 Applying {len(search_conditions)} search conditions")
                query = query.filter(or_(*search_conditions))
            
            if filters.get('date_from'):
                try:
                    date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d')
                    query = query.filter(VendorPenawaran.created_at >= date_from)
                except ValueError:
                    pass
            
            if filters.get('date_to'):
                try:
                    date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d')
                    query = query.filter(VendorPenawaran.created_at <= date_to)
                except ValueError:
                    pass
            
            # Additional filters
            if filters.get('kategori'):
                from models import Barang, KategoriBarang
                kategori_subquery = self.db.query(RequestPembelianItem.id).join(
                    Barang, Barang.id == RequestPembelianItem.barang_id
                ).join(
                    KategoriBarang, KategoriBarang.id == Barang.kategori_id
                ).filter(KategoriBarang.nama_kategori == filters['kategori']).subquery()
                
                query = query.filter(
                    VendorPenawaranItem.request_item_id.in_(
                        self.db.query(kategori_subquery.c.id)
                    )
                )
            
            if filters.get('merek'):
                from models import Barang
                merek_subquery = self.db.query(RequestPembelianItem.id).join(
                    Barang, Barang.id == RequestPembelianItem.barang_id
                ).filter(Barang.kode_barang == filters['merek']).subquery()
                
                query = query.filter(
                    VendorPenawaranItem.request_item_id.in_(
                        self.db.query(merek_subquery.c.id)
                    )
                )
            
            # Vendor type and business model filters
            if filters.get('vendor_type'):
                query = query.filter(Vendor.vendor_type == filters['vendor_type'])
            
            if filters.get('business_model'):
                query = query.filter(Vendor.business_model == filters['business_model'])
            
            if filters.get('min_harga'):
                query = query.filter(VendorPenawaranItem.vendor_unit_price >= filters['min_harga'])
            
            if filters.get('max_harga'):
                query = query.filter(VendorPenawaranItem.vendor_unit_price <= filters['max_harga'])
            
            if filters.get('request_id'):
                query = query.filter(VendorPenawaran.request_id == filters['request_id'])
            
            # Get total count
            total_count = query.count()
            
            # Calculate pagination
            total_pages = (total_count + per_page - 1) // per_page
            offset = (page - 1) * per_page
            
            # Apply sorting
            sort_by = filters.get('sort_by', 'created_at')
            sort_order = filters.get('sort_order', 'desc')
            
            if sort_by == 'created_at':
                order_column = VendorPenawaran.created_at
            elif sort_by == 'nama_barang':
                order_column = RequestPembelianItem.nama_barang
            elif sort_by == 'harga_satuan':
                order_column = VendorPenawaranItem.vendor_unit_price
            elif sort_by == 'kategori':
                # For kategori sorting, we need to join with Barang and KategoriBarang
                from models import Barang, KategoriBarang
                query = query.join(Barang, Barang.id == RequestPembelianItem.barang_id).join(
                    KategoriBarang, KategoriBarang.id == Barang.kategori_id
                )
                order_column = KategoriBarang.nama_kategori
            elif sort_by == 'merek':
                # For merek sorting, we need to join with Barang
                from models import Barang
                query = query.join(Barang, Barang.id == RequestPembelianItem.barang_id)
                order_column = Barang.kode_barang
            elif sort_by == 'vendor':
                order_column = Vendor.company_name
            else:
                order_column = VendorPenawaran.created_at
            
            # Apply order
            if sort_order == 'asc':
                query = query.order_by(order_column.asc())
            else:
                query = query.order_by(order_column.desc())
            
            # Get paginated results
            results = query.offset(offset).limit(per_page).all()
            
            # Format results
            formatted_items = []
            for result in results:
                item, penawaran, vendor, request, request_item = result
                
                item_data = item.to_dict()
                if request_item:
                    request_item_data = request_item.to_dict()
                    
                    # Extract nama_barang from specifications if it contains the pattern
                    nama_barang = 'Nama Barang Tidak Diketahui'
                    if request_item.specifications and ' | ' in request_item.specifications:
                        nama_barang = request_item.specifications.split(' | ')[0]
                        logger.info(f"🔍 Extracted nama_barang: {nama_barang} from specs: {request_item.specifications}")
                    elif request_item.specifications:
                        nama_barang = request_item.specifications
                        logger.info(f"🔍 Using full specs as nama_barang: {nama_barang}")
                    else:
                        logger.warning(f"⚠️ No specifications found for request_item {request_item.id}")
                    
                    # Get merek from barang if available
                    merek = None
                    if request_item.barang_id:
                        try:
                            from models import Barang
                            barang = self.db.query(Barang).filter(Barang.id == request_item.barang_id).first()
                            if barang:
                                merek = barang.merk
                        except Exception as e:
                            logger.warning(f"Error getting merek for barang {request_item.barang_id}: {e}")
                    
                    item_data.update({
                        'vendor': vendor.to_dict(),
                        'penawaran': penawaran.to_dict(),
                        'request': request.to_dict(),
                        'request_item': request_item_data,
                        'nama_barang': nama_barang,
                        'kategori': item.kategori or request_item_data.get('kategori', None),
                        'satuan': request_item_data.get('satuan', 'pcs'),
                        'merek': item.vendor_merk or merek,
                        # Add aliases for frontend compatibility
                        'quantity': item.vendor_quantity,
                        'harga_satuan': float(item.vendor_unit_price) if item.vendor_unit_price else 0,
                        'harga_total': float(item.vendor_total_price) if item.vendor_total_price else (float(item.vendor_unit_price) * item.vendor_quantity if item.vendor_unit_price and item.vendor_quantity else 0),
                        'spesifikasi': item.vendor_specifications
                    })
                else:
                    item_data.update({
                        'vendor': vendor.to_dict(),
                        'penawaran': penawaran.to_dict(),
                        'request': request.to_dict(),
                        'request_item': None,
                        'nama_barang': 'Nama Barang Tidak Diketahui',
                        'kategori': item.kategori,
                        'satuan': 'pcs',
                        'merek': item.vendor_merk,
                        # Add aliases for frontend compatibility
                        'quantity': item.vendor_quantity,
                        'harga_satuan': float(item.vendor_unit_price) if item.vendor_unit_price else 0,
                        'harga_total': float(item.vendor_total_price) if item.vendor_total_price else (float(item.vendor_unit_price) * item.vendor_quantity if item.vendor_unit_price and item.vendor_quantity else 0),
                        'spesifikasi': item.vendor_specifications
                    })
                
                formatted_items.append(item_data)
            
            return {
                'success': True,
                'data': formatted_items,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting all vendor catalog items: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }
    
    def get_reference_ids_with_penawaran(self, page: int = 1, per_page: int = 10,
                                       filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Mendapatkan daftar reference ID yang memiliki penawaran vendor"""
        try:
            if filters is None:
                filters = {}
            
            # Query untuk mendapatkan reference ID yang memiliki penawaran
            query = self.db.query(
                RequestPembelian.reference_id,
                RequestPembelian.title,
                RequestPembelian.id,
                RequestPembelian.vendor_upload_deadline,
                RequestPembelian.status,
                func.count(VendorPenawaran.id).label('vendor_count'),
                func.count(VendorPenawaranItem.id).label('total_items'),
                func.sum(VendorPenawaran.total_quoted_price).label('total_value')
            ).join(
                VendorPenawaran, RequestPembelian.id == VendorPenawaran.request_id
            ).outerjoin(
                VendorPenawaranItem, VendorPenawaran.id == VendorPenawaranItem.vendor_penawaran_id
            ).group_by(
                RequestPembelian.id
            )
            
            # Apply filters
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        RequestPembelian.reference_id.like(search_term),
                        RequestPembelian.title.like(search_term)
                    )
                )
            
            if filters.get('status'):
                query = query.filter(RequestPembelian.status == filters['status'])
            
            # Get total count
            total_count = query.count()
            
            # Calculate pagination
            total_pages = (total_count + per_page - 1) // per_page
            offset = (page - 1) * per_page
            
            # Get paginated results
            results = query.order_by(
                desc(RequestPembelian.created_at)
            ).offset(offset).limit(per_page).all()
            
            # Format results
            formatted_references = []
            for result in results:
                formatted_references.append({
                    'reference_id': result.reference_id,
                    'title': result.title,
                    'request_id': result.id,
                    'vendor_upload_deadline': result.vendor_upload_deadline.isoformat() if result.vendor_upload_deadline else None,
                    'status': result.status,
                    'vendor_count': result.vendor_count,
                    'total_items': result.total_items,
                    'total_value': float(result.total_value or 0)
                })
            
            return {
                'success': True,
                'data': formatted_references,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting reference IDs with penawaran: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'data': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': 0,
                    'pages': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }
    
    def create_vendor_catalog_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Membuat item katalog vendor baru"""
        try:
            # Validate required fields
            required_fields = ['vendor_id', 'request_item_id', 'vendor_unit_price', 'vendor_quantity']
            for field in required_fields:
                if field not in item_data or not item_data[field]:
                    return {
                        'success': False,
                        'message': f'Field {field} is required'
                    }
            
            # Check if vendor exists
            vendor = self.db.query(Vendor).filter(Vendor.id == item_data['vendor_id']).first()
            if not vendor:
                return {
                    'success': False,
                    'message': 'Vendor tidak ditemukan'
                }
            
            # Check if request item exists
            request_item = self.db.query(RequestPembelianItem).filter(
                RequestPembelianItem.id == item_data['request_item_id']
            ).first()
            if not request_item:
                return {
                    'success': False,
                    'message': 'Request item tidak ditemukan'
                }
            
            # Get or create penawaran for this vendor and request
            penawaran = self.db.query(VendorPenawaran).filter(
                and_(
                    VendorPenawaran.vendor_id == item_data['vendor_id'],
                    VendorPenawaran.request_id == request_item.request_id
                )
            ).first()
            
            if not penawaran:
                # Create new penawaran
                reference_id = f"PEN-{datetime.utcnow().strftime('%Y%m%d')}-{item_data['vendor_id']:04d}-{request_item.request_id:04d}"
                penawaran = VendorPenawaran(
                    request_id=request_item.request_id,
                    vendor_id=item_data['vendor_id'],
                    reference_id=reference_id,
                    status='submitted',
                    total_quoted_price=0,  # Will be calculated
                    delivery_time_days=item_data.get('delivery_time_days', 0),
                    payment_terms=item_data.get('payment_terms', ''),
                    quality_rating=item_data.get('quality_rating', 3),
                    notes=item_data.get('notes', '')
                )
                self.db.add(penawaran)
                self.db.flush()
            
            # Calculate total price
            vendor_unit_price = float(item_data['vendor_unit_price'])
            vendor_quantity = int(item_data['vendor_quantity'])
            vendor_total_price = vendor_unit_price * vendor_quantity
            
            # Create penawaran item
            penawaran_item = VendorPenawaranItem(
                vendor_penawaran_id=penawaran.id,
                request_item_id=item_data['request_item_id'],
                vendor_unit_price=vendor_unit_price,
                vendor_total_price=vendor_total_price,
                vendor_quantity=vendor_quantity,
                vendor_specifications=item_data.get('vendor_specifications', ''),
                vendor_notes=item_data.get('vendor_notes', '')
            )
            
            self.db.add(penawaran_item)
            
            # Update penawaran total
            self._update_penawaran_total(penawaran.id)
            
            self.db.commit()
            
            logger.info(f"✅ Created vendor catalog item for vendor {item_data['vendor_id']}")
            
            return {
                'success': True,
                'message': 'Item katalog vendor berhasil dibuat',
                'data': penawaran_item.to_dict()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating vendor catalog item: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def update_vendor_catalog_item(self, item_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update item katalog vendor"""
        try:
            # Get existing item
            item = self.db.query(VendorPenawaranItem).filter(
                VendorPenawaranItem.id == item_id
            ).first()
            
            if not item:
                return {
                    'success': False,
                    'message': 'Item katalog vendor tidak ditemukan'
                }
            
            # Update fields
            if 'vendor_unit_price' in update_data:
                item.vendor_unit_price = float(update_data['vendor_unit_price'])
            
            if 'vendor_quantity' in update_data:
                item.vendor_quantity = int(update_data['vendor_quantity'])
            
            if 'vendor_specifications' in update_data:
                item.vendor_specifications = update_data['vendor_specifications']
            
            if 'vendor_notes' in update_data:
                item.vendor_notes = update_data['vendor_notes']
            
            # Recalculate total price
            if 'vendor_unit_price' in update_data or 'vendor_quantity' in update_data:
                item.vendor_total_price = item.vendor_unit_price * item.vendor_quantity
            
            item.updated_at = datetime.utcnow()
            
            # Update penawaran total
            self._update_penawaran_total(item.vendor_penawaran_id)
            
            self.db.commit()
            
            logger.info(f"✅ Updated vendor catalog item {item_id}")
            
            return {
                'success': True,
                'message': 'Item katalog vendor berhasil diupdate',
                'data': item.to_dict()
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating vendor catalog item: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def delete_vendor_catalog_item(self, item_id: int) -> Dict[str, Any]:
        """Hapus item katalog vendor"""
        try:
            # Get existing item
            item = self.db.query(VendorPenawaranItem).filter(
                VendorPenawaranItem.id == item_id
            ).first()
            
            if not item:
                return {
                    'success': False,
                    'message': 'Item katalog vendor tidak ditemukan'
                }
            
            penawaran_id = item.vendor_penawaran_id
            
            # Delete item
            self.db.delete(item)
            
            # Update penawaran total
            self._update_penawaran_total(penawaran_id)
            
            # Check if penawaran has no more items, delete penawaran if empty
            remaining_items = self.db.query(VendorPenawaranItem).filter(
                VendorPenawaranItem.vendor_penawaran_id == penawaran_id
            ).count()
            
            if remaining_items == 0:
                penawaran = self.db.query(VendorPenawaran).filter(
                    VendorPenawaran.id == penawaran_id
                ).first()
                if penawaran:
                    self.db.delete(penawaran)
            
            self.db.commit()
            
            logger.info(f"✅ Deleted vendor catalog item {item_id}")
            
            return {
                'success': True,
                'message': 'Item katalog vendor berhasil dihapus'
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error deleting vendor catalog item: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def export_vendor_catalog(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Export data katalog vendor ke CSV"""
        try:
            if filters is None:
                filters = {}
            
            # Get all data (no pagination for export)
            result = self.get_all_vendor_catalog_items(page=1, per_page=10000, filters=filters)
            
            if not result['success']:
                return result
            
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Reference ID', 'Request Title', 'Vendor', 'Nama Barang',
                'Quantity', 'Harga Satuan', 'Harga Total', 'Spesifikasi',
                'Status Penawaran', 'Tanggal Submit', 'Catatan'
            ])
            
            # Write data
            for item in result['data']:
                writer.writerow([
                    item.get('request', {}).get('reference_id', ''),
                    item.get('request', {}).get('title', ''),
                    item.get('vendor', {}).get('company_name', ''),
                    item.get('nama_barang', ''),
                    item.get('vendor_quantity', 0),
                    item.get('vendor_unit_price', 0),
                    item.get('vendor_total_price', 0),
                    item.get('vendor_specifications', ''),
                    item.get('penawaran', {}).get('status', ''),
                    item.get('penawaran', {}).get('created_at', ''),
                    item.get('vendor_notes', '')
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            return {
                'success': True,
                'data': csv_content,
                'filename': f'vendor_catalog_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
            
        except Exception as e:
            logger.error(f"❌ Error exporting vendor catalog: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_vendors_list(self) -> List[Dict[str, Any]]:
        """Mendapatkan daftar vendor untuk dropdown - vendor yang sudah submit penawaran"""
        try:
            # Get vendors that have submitted penawaran (vendor_penawaran)
            from models import VendorPenawaran
            
            vendors_with_penawaran = self.db.query(Vendor).join(
                VendorPenawaran, Vendor.id == VendorPenawaran.vendor_id
            ).filter(
                Vendor.status.in_(['approved', 'active']) | (Vendor.status.is_(None))
            ).distinct().all()
            
            # If no vendors with penawaran, get all approved vendors
            if not vendors_with_penawaran:
                vendors_with_penawaran = self.db.query(Vendor).filter(
                    Vendor.status.in_(['approved', 'active']) | (Vendor.status.is_(None))
                ).all()
            
            return [vendor.to_dict() for vendor in vendors_with_penawaran]
        except Exception as e:
            logger.error(f"❌ Error getting vendors list: {str(e)}")
            return []
    
    def get_request_items_list(self, request_id: int = None) -> List[Dict[str, Any]]:
        """Mendapatkan daftar request items untuk dropdown"""
        try:
            query = self.db.query(RequestPembelianItem)
            
            if request_id:
                query = query.filter(RequestPembelianItem.request_id == request_id)
            
            items = query.all()
            return [item.to_dict() for item in items]
        except Exception as e:
            logger.error(f"❌ Error getting request items list: {str(e)}")
            return []
    
    def get_categories_list(self) -> List[Dict[str, Any]]:
        """Mendapatkan daftar kategori untuk dropdown dari VendorPenawaranItem"""
        try:
            from sqlalchemy import distinct
            # Get unique categories from VendorPenawaranItem
            categories = self.db.query(distinct(VendorPenawaranItem.kategori)).filter(
                VendorPenawaranItem.kategori.isnot(None),
                VendorPenawaranItem.kategori != ''
            ).all()
            
            result = []
            for i, cat in enumerate(categories):
                if cat[0] and cat[0].strip():  # Only add non-empty categories
                    result.append({
                        'id': i + 1,
                        'name': cat[0].strip(),
                        'code': cat[0].strip().upper()[:3],
                        'description': f"Kategori {cat[0].strip()}"
                    })
            
            return result
        except Exception as e:
            logger.error(f"❌ Error getting categories list: {str(e)}")
            return []
    
    def get_requests_list(self) -> List[Dict[str, Any]]:
        """Mendapatkan daftar requests untuk dropdown"""
        try:
            requests = self.db.query(RequestPembelian).filter(
                RequestPembelian.status.in_(['submitted', 'vendor_uploading', 'under_analysis'])
            ).all()
            return [request.to_dict() for request in requests]
        except Exception as e:
            logger.error(f"❌ Error getting requests list: {str(e)}")
            return []
    
    def get_mereks_list(self) -> List[Dict[str, Any]]:
        """Mendapatkan daftar merek untuk dropdown dari VendorPenawaranItem"""
        try:
            from sqlalchemy import distinct
            # Get unique mereks from VendorPenawaranItem
            mereks = self.db.query(distinct(VendorPenawaranItem.vendor_merk)).filter(
                VendorPenawaranItem.vendor_merk.isnot(None),
                VendorPenawaranItem.vendor_merk != ''
            ).all()
            
            result = []
            for i, merek in enumerate(mereks):
                if merek[0] and merek[0].strip():  # Only add non-empty mereks
                    result.append({
                        'id': i + 1,
                        'name': merek[0].strip()
                    })
            
            return result
        except Exception as e:
            logger.error(f"❌ Error getting mereks list: {str(e)}")
            return []
    
    def get_penawarans_list(self) -> List[Dict[str, Any]]:
        """Mendapatkan daftar penawaran untuk dropdown"""
        try:
            penawarans = self.db.query(VendorPenawaran).join(
                RequestPembelian, VendorPenawaran.request_id == RequestPembelian.id
            ).join(
                Vendor, VendorPenawaran.vendor_id == Vendor.id
            ).all()
            
            result = []
            for penawaran in penawarans:
                # Get request info
                request = self.db.query(RequestPembelian).filter(
                    RequestPembelian.id == penawaran.request_id
                ).first()
                
                # Get vendor info
                vendor = self.db.query(Vendor).filter(
                    Vendor.id == penawaran.vendor_id
                ).first()
                
                result.append({
                    'id': penawaran.id,
                    'reference_id': request.reference_id if request else 'N/A',
                    'display_name': f"{request.reference_id if request else 'N/A'} - {request.title if request else 'N/A'} ({vendor.company_name if vendor else 'N/A'})",
                    'request': {
                        'id': request.id if request else None,
                        'reference_id': request.reference_id if request else None,
                        'title': request.title if request else None
                    },
                    'vendor': {
                        'id': vendor.id if vendor else None,
                        'company_name': vendor.company_name if vendor else None
                    },
                    'status': penawaran.status,
                    'total_quoted_price': penawaran.total_quoted_price,
                    'created_at': penawaran.created_at.isoformat() if penawaran.created_at else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting penawarans list: {str(e)}")
            return []
    
    def debug_penawarans_list(self) -> Dict[str, Any]:
        """Debug method untuk penawaran list"""
        try:
            # Get total count
            total_penawarans = self.db.query(VendorPenawaran).count()
            
            # Get sample data
            sample_penawarans = self.db.query(VendorPenawaran).limit(5).all()
            
            sample_data = []
            for penawaran in sample_penawarans:
                # Get related data
                request = self.db.query(RequestPembelian).filter(
                    RequestPembelian.id == penawaran.request_id
                ).first()
                
                vendor = self.db.query(Vendor).filter(
                    Vendor.id == penawaran.vendor_id
                ).first()
                
                sample_data.append({
                    'penawaran_id': penawaran.id,
                    'request_id': penawaran.request_id,
                    'vendor_id': penawaran.vendor_id,
                    'request_reference': request.reference_id if request else None,
                    'request_title': request.title if request else None,
                    'vendor_name': vendor.company_name if vendor else None,
                    'status': penawaran.status
                })
            
            return {
                'total_penawarans': total_penawarans,
                'sample_data': sample_data,
                'message': 'Debug info retrieved successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Error debugging penawarans list: {str(e)}")
            return {
                'error': str(e),
                'message': 'Failed to retrieve debug info'
            }

    def _update_penawaran_total(self, penawaran_id: int):
        """Update total harga penawaran berdasarkan items"""
        try:
            # Calculate total from all items
            total = self.db.query(func.sum(VendorPenawaranItem.vendor_total_price)).filter(
                VendorPenawaranItem.vendor_penawaran_id == penawaran_id
            ).scalar() or 0
            
            # Update penawaran
            penawaran = self.db.query(VendorPenawaran).filter(
                VendorPenawaran.id == penawaran_id
            ).first()
            
            if penawaran:
                penawaran.total_quoted_price = total
                penawaran.updated_at = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"❌ Error updating penawaran total: {str(e)}")
    
    def bulk_import_vendor_catalog_items(self, items_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk import vendor catalog items"""
        try:
            successful_imports = 0
            failed_imports = 0
            errors = []
            imported_items = []
            
            # Buat request pembelian khusus untuk proses bulk import ini
            import uuid
            now = datetime.utcnow()
            reference_id = f"BULK_IMPORT_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6].upper()}"

            # Ambil user dan department default (gunakan record pertama yang tersedia)
            from models import User
            from models import Department
            default_user = self.db.query(User).first()
            default_dept = self.db.query(Department).first()

            if not default_user or not default_dept:
                return {
                    'success': False,
                    'message': 'Tidak dapat membuat request: User atau Department tidak ditemukan di database'
                }

            bulk_request_number = f"PR-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
            bulk_request = RequestPembelian(
                request_number=bulk_request_number,
                reference_id=reference_id,
                user_id=default_user.id,
                department_id=default_dept.id,
                title='Bulk Import Request',
                description='Request otomatis untuk bulk import vendor catalog',
                status='draft',
                priority='medium',
                vendor_upload_deadline=now + timedelta(days=30),
                analysis_deadline=now + timedelta(days=35),
                approval_deadline=now + timedelta(days=36)
            )
            self.db.add(bulk_request)
            self.db.flush()  # Pastikan parent tersimpan sebelum insert child
            logger.info(f"✅ Created bulk import request: {bulk_request.id} - {reference_id}")

            bulk_request_id = bulk_request.id
            
            for index, item_data in enumerate(items_data):
                try:
                    # Validate vendor exists by name
                    vendor = self.db.query(Vendor).filter(Vendor.company_name == item_data['vendor_name']).first()
                    if not vendor:
                        # Try to create vendor if not exists
                        vendor = Vendor(
                            company_name=item_data['vendor_name'],
                            contact_person='Auto-created from bulk import',
                            email=item_data.get('email', f'auto_{item_data["vendor_name"].replace(" ", "_").lower()}@vendor.com'),
                            phone='-',
                            address='-',
                            status='approved'  # Set status to approved for auto-created vendors
                        )
                        self.db.add(vendor)
                        self.db.flush()  # Get the ID
                        logger.info(f"Created new vendor: {item_data['vendor_name']}")
                    
                    vendor_id = vendor.id
                    
                    # Create vendor penawaran item (simulate as standalone catalog item)
                    # For now, we'll create a mock penawaran item
                    # In real implementation, you might need to create a separate catalog table
                    
                    # Create a mock request item first
                    request_item = RequestPembelianItem(
                        request_id=bulk_request_id,  # Use the bulk request ID
                        specifications=item_data['spesifikasi'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['harga_satuan'],
                        total_price=item_data['harga_total']
                    )
                    # Add nama_barang to specifications for now
                    request_item.specifications = f"{item_data['nama_barang']} | {item_data['spesifikasi']}"
                    self.db.add(request_item)
                    self.db.flush()  # Get the ID
                    
                    # Create vendor penawaran
                    reference_id = f"BULK_IMPORT_{uuid.uuid4().hex[:8].upper()}"
                    
                    penawaran = VendorPenawaran(
                        request_id=bulk_request_id,  # Use the bulk request ID
                        vendor_id=vendor_id,
                        reference_id=reference_id,
                        status=item_data['status'],
                        total_quoted_price=item_data['harga_total']
                    )
                    self.db.add(penawaran)
                    self.db.flush()  # Get the ID
                    
                    # Create vendor penawaran item
                    penawaran_item = VendorPenawaranItem(
                        vendor_penawaran_id=penawaran.id,
                        request_item_id=request_item.id,
                        vendor_quantity=item_data['quantity'],
                        vendor_unit_price=item_data['harga_satuan'],
                        vendor_total_price=item_data['harga_total'],
                        vendor_specifications=item_data['spesifikasi'],
                        vendor_notes=f"Tanggal Input: {item_data['tanggal']}" if item_data['tanggal'] else None,
                        vendor_merk=item_data['merek'],
                        kategori=item_data['kategori'],
                        created_at=datetime.utcnow()
                    )
                    self.db.add(penawaran_item)
                    
                    # Commit the transaction
                    self.db.commit()
                    
                    imported_items.append({
                        'id': penawaran_item.id,
                        'nama_barang': item_data['nama_barang'],
                        'vendor_name': item_data['vendor_name'],
                        'quantity': item_data['quantity'],
                        'harga_satuan': item_data['harga_satuan'],
                        'harga_total': item_data['harga_total'],
                        'kategori': item_data['kategori'],
                        'merek': item_data['merek'],
                        'spesifikasi': item_data['spesifikasi'],
                        'status': item_data['status'],
                        'tanggal': item_data['tanggal']
                    })
                    
                    successful_imports += 1
                    
                except Exception as e:
                    self.db.rollback()
                    errors.append({
                        'row': index + 1,
                        'field': 'General',
                        'message': f'Error processing item: {str(e)}'
                    })
                    failed_imports += 1
            
            return {
                'success': True,
                'successful_imports': successful_imports,
                'failed_imports': failed_imports,
                'errors': errors,
                'imported_items': imported_items
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error in bulk import: {str(e)}")
            return {
                'success': False,
                'message': f'Terjadi kesalahan saat mengimport data: {str(e)}'
            }