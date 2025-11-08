from flask import request, jsonify, send_file
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, date, timedelta
from config.database import db
from models.remind_exp_docs import RemindExpDocs, DocumentStatus
from services.remind_exp_docs_service import RemindExpDocsService
from controllers.telegram_controller import TelegramController
from utils.logger import get_logger
import io
import pandas as pd
from typing import List, Dict, Any

logger = get_logger(__name__)

class RemindExpDocsController:
    def __init__(self):
        self.service = RemindExpDocsService()
        self.telegram_controller = TelegramController()
    
    def get_all_documents(self):
        """Mendapatkan semua dokumen dengan pagination dan filter"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            search = request.args.get('search', '', type=str)
            status = request.args.get('status', '', type=str)
            document_type = request.args.get('document_type', '', type=str)
            sort_by = request.args.get('sort_by', 'expiry_date', type=str)
            sort_order = request.args.get('sort_order', 'asc', type=str)
            
            result = self.service.get_all_documents(
                db=db.session,
                page=page,
                per_page=per_page,
                search=search,
                status=status,
                document_type=document_type,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            return jsonify({
                'success': True,
                'data': result['documents'],
                'pagination': result['pagination'],
                'message': 'Data dokumen berhasil diambil'
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting all documents: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Gagal mengambil data dokumen: {str(e)}'
            }), 500
        finally:
            pass
    
    def get_document_by_id(self, document_id: int):
        """Mendapatkan dokumen berdasarkan ID"""
        try:
            document = self.service.get_document_by_id(db.session, document_id)
            
            if not document:
                return jsonify({
                    'success': False,
                    'message': 'Dokumen tidak ditemukan'
                }), 404
            
            return jsonify({
                'success': True,
                'data': document.to_dict(),
                'message': 'Data dokumen berhasil diambil'
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting document by ID: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Gagal mengambil data dokumen: {str(e)}'
            }), 500
        finally:
            pass
    
    def create_document(self):
        """Membuat dokumen baru"""
        try:
            data = request.get_json()
            
            # Validasi data yang diperlukan
            required_fields = ['document_name', 'expiry_date']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({
                        'success': False,
                        'message': f'Field {field} harus diisi'
                    }), 400
            
            # Validasi tanggal expired
            try:
                expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
                if expiry_date <= date.today():
                    return jsonify({
                        'success': False,
                        'message': 'Tanggal expired harus lebih dari hari ini'
                    }), 400
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Format tanggal tidak valid (YYYY-MM-DD)'
                }), 400
            
            document = self.service.create_document(db.session, data)
            
            # Kirim notifikasi Telegram untuk dokumen baru
            try:
                days_until_expiry = (expiry_date - date.today()).days
                
                # Kirim notifikasi jika dokumen akan expired dalam 30 hari
                if days_until_expiry <= 30:
                    message = f"""📋 *DOKUMEN BARU DITAMBAHKAN*

*{data.get('document_name')}*
📄 No: {data.get('document_number', '-')}
🏢 Penerbit: {data.get('issuer', '-')}
📅 Expired: {expiry_date.strftime('%d/%m/%Y')}
⏰ Sisa: *{days_until_expiry} hari*

{'🚨 *PERHATIAN: Dokumen akan segera expired!*' if days_until_expiry <= 7 else '⚠️ *Perlu perhatian*'}

🔗 [Lihat Detail](http://localhost:3000/remind-exp-docs)"""
                    
                    self.telegram_controller.send_message_to_admin(message)
                    logger.info(f"Telegram notification sent for new document: {document.id}")
            except Exception as e:
                logger.error(f"Failed to send Telegram notification: {str(e)}")
                # Don't fail the request if notification fails
            
            return jsonify({
                'success': True,
                'data': document.to_dict(),
                'message': 'Dokumen berhasil dibuat'
            }), 201
            
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Gagal membuat dokumen: {str(e)}'
            }), 500
        finally:
            pass
    
    def update_document(self, document_id: int):
        """Update dokumen"""
        try:
            data = request.get_json()
            
            # Validasi tanggal expired jika ada
            if 'expiry_date' in data and data['expiry_date']:
                try:
                    expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
                    if expiry_date <= date.today():
                        return jsonify({
                            'success': False,
                            'message': 'Tanggal expired harus lebih dari hari ini'
                        }), 400
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': 'Format tanggal tidak valid (YYYY-MM-DD)'
                    }), 400
            
            document = self.service.update_document(db.session, document_id, data)
            
            if not document:
                return jsonify({
                    'success': False,
                    'message': 'Dokumen tidak ditemukan'
                }), 404
            
            return jsonify({
                'success': True,
                'data': document.to_dict(),
                'message': 'Dokumen berhasil diupdate'
            }), 200
            
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Gagal mengupdate dokumen: {str(e)}'
            }), 500
        finally:
            pass
    
    def delete_document(self, document_id: int):
        """Hapus dokumen"""
        try:
            success = self.service.delete_document(db.session, document_id)
            
            if not success:
                return jsonify({
                    'success': False,
                    'message': 'Dokumen tidak ditemukan'
                }), 404
            
            return jsonify({
                'success': True,
                'message': 'Dokumen berhasil dihapus'
            }), 200
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Gagal menghapus dokumen: {str(e)}'
            }), 500
        finally:
            pass
    
    def bulk_import(self):
        """Import dokumen dari file Excel"""
        try:
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'message': 'File Excel harus diupload'
                }), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'message': 'File tidak dipilih'
                }), 400
            
            if not file.filename.endswith(('.xlsx', '.xls')):
                return jsonify({
                    'success': False,
                    'message': 'File harus berformat Excel (.xlsx atau .xls)'
                }), 400
            
            result = self.service.bulk_import_excel(db.session, file)
            
            # Kirim notifikasi Telegram untuk bulk import
            try:
                if result['success_count'] > 0:
                    message = f"""✅ *BULK IMPORT BERHASIL*
📊 Tanggal: {datetime.now().strftime('%d/%m/%Y %H:%M')}

📈 *Hasil Import:*
• ✅ Berhasil: {result['success_count']} dokumen
• ❌ Gagal: {result['error_count']} dokumen
• 📁 File: {file.filename}

🔗 [Lihat Detail di Sistem](http://localhost:3000/remind-exp-docs)"""
                    
                    self.telegram_controller.send_message_to_admin(message)
                    logger.info(f"Telegram notification sent for bulk import: {result['success_count']} documents")
            except Exception as e:
                logger.error(f"Failed to send Telegram notification: {str(e)}")
                # Don't fail the request if notification fails
            
            return jsonify({
                'success': True,
                'data': result,
                'message': f'Import berhasil: {result["success_count"]} dokumen berhasil, {result["error_count"]} gagal'
            }), 200
            
        except Exception as e:
            logger.error(f"Error bulk import: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Gagal import dokumen: {str(e)}'
            }), 500
        finally:
            pass
    
    def export_excel(self):
        """Export dokumen ke file Excel"""
        try:
            excel_data = self.service.export_to_excel(db.session)
            
            # Buat file Excel di memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                excel_data.to_excel(writer, sheet_name='Remind Exp Docs', index=False)
            
            output.seek(0)
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'remind_exp_docs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
            
        except Exception as e:
            logger.error(f"Error export excel: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Gagal export dokumen: {str(e)}'
            }), 500
        finally:
            pass
    
    def get_expiring_documents(self):
        """Mendapatkan dokumen yang akan expired (untuk notifikasi)"""
        try:
            days_ahead = request.args.get('days_ahead', 30, type=int)
            
            documents = self.service.get_expiring_documents(db.session, days_ahead)
            
            return jsonify({
                'success': True,
                'data': [doc.to_dict() for doc in documents],
                'message': f'Ditemukan {len(documents)} dokumen yang akan expired dalam {days_ahead} hari'
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting expiring documents: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Gagal mengambil dokumen yang akan expired: {str(e)}'
            }), 500
        finally:
            pass
    
    def get_document_statistics(self):
        """Mendapatkan statistik dokumen"""
        try:
            stats = self.service.get_document_statistics(db.session)
            
            return jsonify({
                'success': True,
                'data': stats,
                'message': 'Statistik dokumen berhasil diambil'
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting document statistics: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Gagal mengambil statistik dokumen: {str(e)}'
            }), 500
        finally:
            pass
    
    def test_telegram_notifications(self):
        """Test endpoint untuk notifikasi Telegram"""
        try:
            from schedulers.remind_exp_docs_scheduler import remind_exp_docs_scheduler
            
            # Test koneksi Telegram
            connection_result = remind_exp_docs_scheduler.test_telegram_connection()
            
            # Test manual trigger
            manual_result_30 = remind_exp_docs_scheduler.manual_check_expiring_documents(30)
            manual_result_7 = remind_exp_docs_scheduler.manual_check_expiring_documents(7)
            
            return jsonify({
                'success': True,
                'data': {
                    'telegram_connection': connection_result,
                    'manual_trigger_30_days': manual_result_30,
                    'manual_trigger_7_days': manual_result_7
                },
                'message': 'Test notifikasi Telegram berhasil dijalankan'
            }), 200
            
        except Exception as e:
            logger.error(f"Error testing telegram notifications: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Gagal test notifikasi Telegram: {str(e)}'
            }), 500
        finally:
            pass
    
    def create_test_documents(self):
        """Buat dokumen test untuk testing"""
        try:
            from tests.test_data_generator import test_data_generator
            
            # Buat dokumen test
            test_documents = test_data_generator.create_test_documents_with_different_expiry_dates()
            
            return jsonify({
                'success': True,
                'data': {
                    'created_documents': len(test_documents),
                    'documents': [doc.to_dict() for doc in test_documents]
                },
                'message': f'Berhasil membuat {len(test_documents)} dokumen test'
            }), 200
            
        except Exception as e:
            logger.error(f"Error creating test documents: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Gagal membuat dokumen test: {str(e)}'
            }), 500
        finally:
            pass
    
    def cleanup_test_documents(self):
        """Bersihkan dokumen test"""
        try:
            from tests.test_data_generator import test_data_generator
            
            # Bersihkan dokumen test
            test_data_generator.cleanup_test_documents()
            
            return jsonify({
                'success': True,
                'message': 'Dokumen test berhasil dibersihkan'
            }), 200
            
        except Exception as e:
            logger.error(f"Error cleaning up test documents: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Gagal membersihkan dokumen test: {str(e)}'
            }), 500
        finally:
            pass