from flask import Blueprint
from controllers.remind_exp_docs_controller import RemindExpDocsController
from middlewares.api_auth import require_auth
from middlewares.role_auth import require_role

# Buat blueprint untuk remind_exp_docs
remind_exp_docs_bp = Blueprint('remind_exp_docs', __name__, url_prefix='/api/remind-exp-docs')

# Inisialisasi controller
controller = RemindExpDocsController()

@remind_exp_docs_bp.route('/', methods=['GET'])
@require_auth
def get_all_documents():
    """Mendapatkan semua dokumen dengan pagination dan filter"""
    return controller.get_all_documents()

@remind_exp_docs_bp.route('/<int:document_id>', methods=['GET'])
@require_auth
def get_document_by_id(document_id):
    """Mendapatkan dokumen berdasarkan ID"""
    return controller.get_document_by_id(document_id)

@remind_exp_docs_bp.route('/', methods=['POST'])
@require_auth
@require_role(['admin', 'manager'])
def create_document():
    """Membuat dokumen baru (hanya admin/manager)"""
    return controller.create_document()

@remind_exp_docs_bp.route('/<int:document_id>', methods=['PUT'])
@require_auth
@require_role(['admin', 'manager'])
def update_document(document_id):
    """Update dokumen (hanya admin/manager)"""
    return controller.update_document(document_id)

@remind_exp_docs_bp.route('/<int:document_id>', methods=['DELETE'])
@require_auth
@require_role(['admin'])
def delete_document(document_id):
    """Hapus dokumen (hanya admin)"""
    return controller.delete_document(document_id)

@remind_exp_docs_bp.route('/bulk-import', methods=['POST'])
@require_auth
@require_role(['admin', 'manager'])
def bulk_import():
    """Import dokumen dari file Excel (hanya admin/manager)"""
    return controller.bulk_import()

@remind_exp_docs_bp.route('/export', methods=['GET'])
@require_auth
@require_role(['admin', 'manager'])
def export_excel():
    """Export dokumen ke file Excel (hanya admin/manager)"""
    return controller.export_excel()

@remind_exp_docs_bp.route('/expiring', methods=['GET'])
@require_auth
def get_expiring_documents():
    """Mendapatkan dokumen yang akan expired (untuk notifikasi)"""
    return controller.get_expiring_documents()

@remind_exp_docs_bp.route('/statistics', methods=['GET'])
@require_auth
def get_document_statistics():
    """Mendapatkan statistik dokumen"""
    return controller.get_document_statistics()

# Test endpoints untuk Telegram notifications
@remind_exp_docs_bp.route('/test/telegram-notifications', methods=['POST'])
@require_auth
@require_role(['admin'])
def test_telegram_notifications():
    """Test notifikasi Telegram (hanya admin)"""
    return controller.test_telegram_notifications()

@remind_exp_docs_bp.route('/test/create-test-documents', methods=['POST'])
@require_auth
@require_role(['admin'])
def create_test_documents():
    """Buat dokumen test untuk testing (hanya admin)"""
    return controller.create_test_documents()

@remind_exp_docs_bp.route('/test/cleanup-test-documents', methods=['DELETE'])
@require_auth
@require_role(['admin'])
def cleanup_test_documents():
    """Bersihkan dokumen test (hanya admin)"""
    return controller.cleanup_test_documents()

# Route untuk template Excel
@remind_exp_docs_bp.route('/template', methods=['GET'])
@require_auth
@require_role(['admin', 'manager'])
def download_template():
    """Download template Excel untuk import"""
    from flask import send_file
    import io
    import pandas as pd
    from datetime import datetime
    
    try:
        # Buat template Excel
        template_data = {
            'document_name': ['Contoh Sertifikat ISO 9001', 'Contoh Izin Usaha'],
            'document_number': ['ISO-2024-001', 'IU-2024-001'],
            'document_type': ['Sertifikat ISO', 'Izin Usaha'],
            'issuer': ['Bureau Veritas', 'Dinas Perindustrian'],
            'expiry_date': ['2024-12-31', '2024-06-30'],
            'reminder_days_before': [30, 30],
            'description': ['Sertifikat ISO 9001:2015', 'Izin usaha untuk operasional'],
            'file_path': ['', '']
        }
        
        df = pd.DataFrame(template_data)
        
        # Buat file Excel di memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Template', index=False)
            
            # Tambah sheet dengan instruksi
            instructions = pd.DataFrame({
                'Kolom': ['document_name', 'document_number', 'document_type', 'issuer', 'expiry_date', 'reminder_days_before', 'description', 'file_path'],
                'Deskripsi': [
                    'Nama dokumen (WAJIB)',
                    'Nomor dokumen (opsional)',
                    'Jenis dokumen (opsional)',
                    'Penerbit dokumen (opsional)',
                    'Tanggal expired format YYYY-MM-DD (WAJIB)',
                    'Hari sebelum expired untuk reminder (opsional, default 30)',
                    'Deskripsi tambahan (opsional)',
                    'Path file dokumen (opsional)'
                ],
                'Contoh': [
                    'Sertifikat ISO 9001:2015',
                    'ISO-2024-001',
                    'Sertifikat ISO',
                    'Bureau Veritas',
                    '2024-12-31',
                    '30',
                    'Sertifikat ISO 9001:2015 untuk sistem manajemen mutu',
                    '/files/certificates/iso9001.pdf'
                ]
            })
            instructions.to_excel(writer, sheet_name='Instruksi', index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'remind_exp_docs_template_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
        
    except Exception as e:
        from flask import jsonify
        return jsonify({
            'success': False,
            'message': f'Gagal membuat template: {str(e)}'
        }), 500
