#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Domain Routes - Blueprint registration for task domain
"""

from flask import Blueprint, send_file
from domains.task.controllers.daily_task_controller import DailyTaskController
from domains.task.controllers.remind_exp_docs_controller import RemindExpDocsController
from shared.middlewares.api_auth import require_auth
from shared.middlewares.role_auth import require_role
import io
import pandas as pd
from datetime import datetime

# Create blueprints
daily_task_bp = Blueprint('daily_task', __name__, url_prefix='/api/attendance')
remind_exp_docs_bp = Blueprint('remind_exp_docs', __name__, url_prefix='/api/remind-exp-docs')

# Initialize controllers
daily_task_controller = DailyTaskController()
remind_exp_docs_controller = RemindExpDocsController()

# ===== Daily Task Routes =====
@daily_task_bp.route('/tasks', methods=['POST'])
def create_task():
    """POST /api/attendance/tasks - Create new task"""
    return daily_task_controller.create_task()

@daily_task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    """GET /api/attendance/tasks - List tasks dengan filter"""
    return daily_task_controller.get_tasks()

@daily_task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """GET /api/attendance/tasks/{task_id} - Get single task"""
    return daily_task_controller.get_task(task_id)

@daily_task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """PUT /api/attendance/tasks/{task_id} - Update task (full update)"""
    return daily_task_controller.update_task(task_id)

@daily_task_bp.route('/tasks/<int:task_id>', methods=['PATCH'])
def partial_update_task(task_id):
    """PATCH /api/attendance/tasks/{task_id} - Partial update task"""
    return daily_task_controller.partial_update_task(task_id)

@daily_task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """DELETE /api/attendance/tasks/{task_id} - Soft delete task"""
    return daily_task_controller.delete_task(task_id)

@daily_task_bp.route('/tasks/<int:task_id>/status', methods=['PATCH'])
def update_task_status(task_id):
    """PATCH /api/attendance/tasks/{task_id}/status - Update task status"""
    return daily_task_controller.update_task_status(task_id)

@daily_task_bp.route('/tasks/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """POST /api/attendance/tasks/{task_id}/start - Start task"""
    return daily_task_controller.start_task(task_id)

@daily_task_bp.route('/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """POST /api/attendance/tasks/{task_id}/complete - Complete task"""
    return daily_task_controller.complete_task(task_id)

@daily_task_bp.route('/tasks/<int:task_id>/assign', methods=['POST'])
def assign_task(task_id):
    """POST /api/attendance/tasks/{task_id}/assign - Assign task"""
    return daily_task_controller.assign_task(task_id)

@daily_task_bp.route('/tasks/<int:task_id>/assign', methods=['DELETE'])
def unassign_task(task_id):
    """DELETE /api/attendance/tasks/{task_id}/assign - Unassign task"""
    return daily_task_controller.unassign_task(task_id)

@daily_task_bp.route('/tasks/<int:task_id>/attachments', methods=['POST'])
def upload_attachment(task_id):
    """POST /api/attendance/tasks/{task_id}/attachments - Upload attachment"""
    return daily_task_controller.upload_attachment(task_id)

@daily_task_bp.route('/tasks/<int:task_id>/attachments', methods=['GET'])
def get_attachments(task_id):
    """GET /api/attendance/tasks/{task_id}/attachments - List attachments"""
    return daily_task_controller.get_attachments(task_id)

@daily_task_bp.route('/tasks/<int:task_id>/comments', methods=['POST'])
def add_comment(task_id):
    """POST /api/attendance/tasks/{task_id}/comments - Add comment"""
    return daily_task_controller.add_comment(task_id)

@daily_task_bp.route('/tasks/<int:task_id>/comments', methods=['GET'])
def get_comments(task_id):
    """GET /api/attendance/tasks/{task_id}/comments - List comments"""
    return daily_task_controller.get_comments(task_id)

@daily_task_bp.route('/tasks/statistics', methods=['GET'])
def get_statistics():
    """GET /api/attendance/tasks/statistics - Get task statistics"""
    return daily_task_controller.get_statistics()

@daily_task_bp.route('/tasks/summary', methods=['GET'])
def get_summary():
    """GET /api/attendance/tasks/summary - Get daily summary"""
    return daily_task_controller.get_summary()

@daily_task_bp.route('/tasks/validate-clockout', methods=['GET'])
def validate_clockout():
    """GET /api/attendance/tasks/validate-clockout - Validate tasks before clock-out"""
    return daily_task_controller.validate_clockout()

# ===== Remind Exp Docs Routes =====
@remind_exp_docs_bp.route('/', methods=['GET'])
@require_auth
def get_all_documents():
    """Mendapatkan semua dokumen dengan pagination dan filter"""
    return remind_exp_docs_controller.get_all_documents()

@remind_exp_docs_bp.route('/<int:document_id>', methods=['GET'])
@require_auth
def get_document_by_id(document_id):
    """Mendapatkan dokumen berdasarkan ID"""
    return remind_exp_docs_controller.get_document_by_id(document_id)

@remind_exp_docs_bp.route('/', methods=['POST'])
@require_auth
@require_role(['admin', 'manager'])
def create_document():
    """Membuat dokumen baru (hanya admin/manager)"""
    return remind_exp_docs_controller.create_document()

@remind_exp_docs_bp.route('/<int:document_id>', methods=['PUT'])
@require_auth
@require_role(['admin', 'manager'])
def update_document(document_id):
    """Update dokumen (hanya admin/manager)"""
    return remind_exp_docs_controller.update_document(document_id)

@remind_exp_docs_bp.route('/<int:document_id>', methods=['DELETE'])
@require_auth
@require_role(['admin'])
def delete_document(document_id):
    """Hapus dokumen (hanya admin)"""
    return remind_exp_docs_controller.delete_document(document_id)

@remind_exp_docs_bp.route('/bulk-import', methods=['POST'])
@require_auth
@require_role(['admin', 'manager'])
def bulk_import():
    """Import dokumen dari file Excel (hanya admin/manager)"""
    return remind_exp_docs_controller.bulk_import()

@remind_exp_docs_bp.route('/export', methods=['GET'])
@require_auth
@require_role(['admin', 'manager'])
def export_excel():
    """Export dokumen ke file Excel (hanya admin/manager)"""
    return remind_exp_docs_controller.export_excel()

@remind_exp_docs_bp.route('/expiring', methods=['GET'])
@require_auth
def get_expiring_documents():
    """Mendapatkan dokumen yang akan expired (untuk notifikasi)"""
    return remind_exp_docs_controller.get_expiring_documents()

@remind_exp_docs_bp.route('/statistics', methods=['GET'])
@require_auth
def get_document_statistics():
    """Mendapatkan statistik dokumen"""
    return remind_exp_docs_controller.get_document_statistics()

@remind_exp_docs_bp.route('/test/telegram-notifications', methods=['POST'])
@require_auth
@require_role(['admin'])
def test_telegram_notifications():
    """Test notifikasi Telegram (hanya admin)"""
    return remind_exp_docs_controller.test_telegram_notifications()

@remind_exp_docs_bp.route('/test/create-test-documents', methods=['POST'])
@require_auth
@require_role(['admin'])
def create_test_documents():
    """Buat dokumen test untuk testing (hanya admin)"""
    return remind_exp_docs_controller.create_test_documents()

@remind_exp_docs_bp.route('/test/cleanup-test-documents', methods=['DELETE'])
@require_auth
@require_role(['admin'])
def cleanup_test_documents():
    """Bersihkan dokumen test (hanya admin)"""
    return remind_exp_docs_controller.cleanup_test_documents()

@remind_exp_docs_bp.route('/template', methods=['GET'])
@require_auth
@require_role(['admin', 'manager'])
def download_template():
    """Download template Excel untuk import"""
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


def register_task_routes(app):
    """Register all task domain blueprints"""
    app.register_blueprint(daily_task_bp)
    app.register_blueprint(remind_exp_docs_bp)
