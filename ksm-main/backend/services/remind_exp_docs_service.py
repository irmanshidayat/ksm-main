from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, date, timedelta
from models.remind_exp_docs import RemindExpDocs, DocumentStatus
from utils.logger import get_logger
import pandas as pd
import io
from typing import List, Dict, Any, Optional
import re

logger = get_logger(__name__)

class RemindExpDocsService:
    def __init__(self):
        pass
    
    def get_all_documents(self, db: Session, page: int = 1, per_page: int = 10, 
                         search: str = '', status: str = '', document_type: str = '',
                         sort_by: str = 'expiry_date', sort_order: str = 'asc') -> Dict[str, Any]:
        """Mendapatkan semua dokumen dengan pagination dan filter"""
        try:
            # Query base
            query = db.query(RemindExpDocs)
            
            # Filter berdasarkan search
            if search:
                search_filter = or_(
                    RemindExpDocs.document_name.ilike(f'%{search}%'),
                    RemindExpDocs.document_number.ilike(f'%{search}%'),
                    RemindExpDocs.issuer.ilike(f'%{search}%'),
                    RemindExpDocs.description.ilike(f'%{search}%')
                )
                query = query.filter(search_filter)
            
            # Filter berdasarkan status
            if status:
                query = query.filter(RemindExpDocs.status == status)
            
            # Filter berdasarkan document_type
            if document_type:
                query = query.filter(RemindExpDocs.document_type == document_type)
            
            # Sorting
            if sort_by == 'expiry_date':
                sort_column = RemindExpDocs.expiry_date
            elif sort_by == 'document_name':
                sort_column = RemindExpDocs.document_name
            elif sort_by == 'created_at':
                sort_column = RemindExpDocs.created_at
            else:
                sort_column = RemindExpDocs.expiry_date
            
            if sort_order == 'desc':
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Hitung total records
            total = query.count()
            
            # Pagination
            offset = (page - 1) * per_page
            documents = query.offset(offset).limit(per_page).all()
            
            # Hitung pagination info
            total_pages = (total + per_page - 1) // per_page
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                'documents': [doc.to_dict() for doc in documents],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_prev': has_prev
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting all documents: {str(e)}")
            raise e
    
    def get_document_by_id(self, db: Session, document_id: int) -> Optional[RemindExpDocs]:
        """Mendapatkan dokumen berdasarkan ID"""
        try:
            return db.query(RemindExpDocs).filter(RemindExpDocs.id == document_id).first()
        except Exception as e:
            logger.error(f"Error getting document by ID: {str(e)}")
            raise e
    
    def create_document(self, db: Session, data: Dict[str, Any]) -> RemindExpDocs:
        """Membuat dokumen baru"""
        try:
            # Validasi data
            if not data.get('document_name'):
                raise ValueError("Nama dokumen harus diisi")
            
            if not data.get('expiry_date'):
                raise ValueError("Tanggal expired harus diisi")
            
            # Parse tanggal
            if isinstance(data['expiry_date'], str):
                expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
            else:
                expiry_date = data['expiry_date']
            
            # Buat objek dokumen
            document = RemindExpDocs(
                document_name=data['document_name'],
                document_number=data.get('document_number'),
                document_type=data.get('document_type'),
                issuer=data.get('issuer'),
                expiry_date=expiry_date,
                reminder_days_before=data.get('reminder_days_before', 30),
                status=DocumentStatus.ACTIVE,
                description=data.get('description'),
                file_path=data.get('file_path')
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            logger.info(f"Document created successfully: {document.id}")
            return document
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating document: {str(e)}")
            raise e
    
    def update_document(self, db: Session, document_id: int, data: Dict[str, Any]) -> Optional[RemindExpDocs]:
        """Update dokumen"""
        try:
            document = db.query(RemindExpDocs).filter(RemindExpDocs.id == document_id).first()
            
            if not document:
                return None
            
            # Update fields
            if 'document_name' in data:
                document.document_name = data['document_name']
            
            if 'document_number' in data:
                document.document_number = data['document_number']
            
            if 'document_type' in data:
                document.document_type = data['document_type']
            
            if 'issuer' in data:
                document.issuer = data['issuer']
            
            if 'expiry_date' in data:
                if isinstance(data['expiry_date'], str):
                    document.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
                else:
                    document.expiry_date = data['expiry_date']
            
            if 'reminder_days_before' in data:
                document.reminder_days_before = data['reminder_days_before']
            
            if 'status' in data:
                document.status = DocumentStatus(data['status'])
            
            if 'description' in data:
                document.description = data['description']
            
            if 'file_path' in data:
                document.file_path = data['file_path']
            
            db.commit()
            db.refresh(document)
            
            logger.info(f"Document updated successfully: {document.id}")
            return document
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating document: {str(e)}")
            raise e
    
    def delete_document(self, db: Session, document_id: int) -> bool:
        """Hapus dokumen"""
        try:
            document = db.query(RemindExpDocs).filter(RemindExpDocs.id == document_id).first()
            
            if not document:
                return False
            
            db.delete(document)
            db.commit()
            
            logger.info(f"Document deleted successfully: {document_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting document: {str(e)}")
            raise e
    
    def bulk_import_excel(self, db: Session, file) -> Dict[str, Any]:
        """Import dokumen dari file Excel"""
        try:
            # Baca file Excel
            df = pd.read_excel(file)
            
            # Validasi kolom yang diperlukan
            required_columns = ['document_name', 'expiry_date']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Kolom yang diperlukan tidak ditemukan: {', '.join(missing_columns)}")
            
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Validasi data
                    if pd.isna(row['document_name']) or not str(row['document_name']).strip():
                        raise ValueError("Nama dokumen tidak boleh kosong")
                    
                    if pd.isna(row['expiry_date']):
                        raise ValueError("Tanggal expired tidak boleh kosong")
                    
                    # Parse tanggal
                    if isinstance(row['expiry_date'], str):
                        expiry_date = datetime.strptime(row['expiry_date'], '%Y-%m-%d').date()
                    else:
                        expiry_date = row['expiry_date'].date()
                    
                    # Validasi tanggal
                    if expiry_date <= date.today():
                        raise ValueError("Tanggal expired harus lebih dari hari ini")
                    
                    # Buat dokumen
                    document_data = {
                        'document_name': str(row['document_name']).strip(),
                        'document_number': str(row.get('document_number', '')).strip() if not pd.isna(row.get('document_number')) else None,
                        'document_type': str(row.get('document_type', '')).strip() if not pd.isna(row.get('document_type')) else None,
                        'issuer': str(row.get('issuer', '')).strip() if not pd.isna(row.get('issuer')) else None,
                        'expiry_date': expiry_date,
                        'reminder_days_before': int(row.get('reminder_days_before', 30)) if not pd.isna(row.get('reminder_days_before')) else 30,
                        'description': str(row.get('description', '')).strip() if not pd.isna(row.get('description')) else None,
                        'file_path': str(row.get('file_path', '')).strip() if not pd.isna(row.get('file_path')) else None
                    }
                    
                    self.create_document(db, document_data)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Baris {index + 2}: {str(e)}")
                    logger.error(f"Error importing row {index + 2}: {str(e)}")
            
            return {
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error bulk import excel: {str(e)}")
            raise e
    
    def export_to_excel(self, db: Session) -> pd.DataFrame:
        """Export dokumen ke DataFrame untuk Excel"""
        try:
            # Ambil semua dokumen
            documents = db.query(RemindExpDocs).all()
            
            # Konversi ke DataFrame
            data = []
            for doc in documents:
                data.append({
                    'ID': doc.id,
                    'Nama Dokumen': doc.document_name,
                    'Nomor Dokumen': doc.document_number or '',
                    'Jenis Dokumen': doc.document_type or '',
                    'Penerbit': doc.issuer or '',
                    'Tanggal Expired': doc.expiry_date.strftime('%Y-%m-%d') if doc.expiry_date else '',
                    'Reminder (Hari)': doc.reminder_days_before,
                    'Status': doc.status.value if doc.status else '',
                    'Deskripsi': doc.description or '',
                    'File Path': doc.file_path or '',
                    'Dibuat': doc.created_at.strftime('%Y-%m-%d %H:%M:%S') if doc.created_at else '',
                    'Diupdate': doc.updated_at.strftime('%Y-%m-%d %H:%M:%S') if doc.updated_at else ''
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error export to excel: {str(e)}")
            raise e
    
    def get_expiring_documents(self, db: Session, days_ahead: int = 30) -> List[RemindExpDocs]:
        """Mendapatkan dokumen yang akan expired dalam X hari"""
        try:
            target_date = date.today() + timedelta(days=days_ahead)
            
            documents = db.query(RemindExpDocs).filter(
                and_(
                    RemindExpDocs.status == DocumentStatus.ACTIVE,
                    RemindExpDocs.expiry_date <= target_date,
                    RemindExpDocs.expiry_date > date.today()
                )
            ).order_by(RemindExpDocs.expiry_date).all()
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting expiring documents: {str(e)}")
            raise e
    
    def get_document_statistics(self, db: Session) -> Dict[str, Any]:
        """Mendapatkan statistik dokumen"""
        try:
            total_documents = db.query(RemindExpDocs).count()
            
            active_documents = db.query(RemindExpDocs).filter(
                RemindExpDocs.status == DocumentStatus.ACTIVE
            ).count()
            
            expired_documents = db.query(RemindExpDocs).filter(
                RemindExpDocs.status == DocumentStatus.EXPIRED
            ).count()
            
            inactive_documents = db.query(RemindExpDocs).filter(
                RemindExpDocs.status == DocumentStatus.INACTIVE
            ).count()
            
            # Dokumen yang akan expired dalam 30 hari
            expiring_30_days = len(self.get_expiring_documents(db, 30))
            
            # Dokumen yang akan expired dalam 7 hari
            expiring_7_days = len(self.get_expiring_documents(db, 7))
            
            # Dokumen yang sudah expired (status EXPIRED + dokumen ACTIVE yang lewat tanggal)
            already_expired = (
                db.query(RemindExpDocs).filter(
                    RemindExpDocs.status == DocumentStatus.EXPIRED
                ).count() +
                db.query(RemindExpDocs).filter(
                    and_(
                        RemindExpDocs.status == DocumentStatus.ACTIVE,
                        RemindExpDocs.expiry_date < date.today()
                    )
                ).count()
            )
            
            return {
                'total_documents': total_documents,
                'active_documents': active_documents,
                'expired_documents': expired_documents,
                'inactive_documents': inactive_documents,
                'expiring_30_days': expiring_30_days,
                'expiring_7_days': expiring_7_days,
                'already_expired': already_expired
            }
            
        except Exception as e:
            logger.error(f"Error getting document statistics: {str(e)}")
            raise e
    
    def update_expired_status(self, db: Session) -> int:
        """Update status dokumen yang sudah expired"""
        try:
            today = date.today()
            
            # Update dokumen yang sudah expired
            updated_count = db.query(RemindExpDocs).filter(
                and_(
                    RemindExpDocs.status == DocumentStatus.ACTIVE,
                    RemindExpDocs.expiry_date < today
                )
            ).update({
                'status': DocumentStatus.EXPIRED
            })
            
            db.commit()
            
            logger.info(f"Updated {updated_count} documents to expired status")
            return updated_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating expired status: {str(e)}")
            raise e
