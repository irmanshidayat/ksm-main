#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Production Script: Send Telegram Report
Kirim laporan dokumen expired ke Telegram
Usage: python scripts/send_telegram_report.py [days]
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from controllers.telegram_controller import TelegramController
from services.remind_exp_docs_service import RemindExpDocsService
from datetime import datetime, date
import argparse

def send_daily_report(days_ahead=30):
    """Kirim laporan harian ke Telegram"""
    
    with app.app_context():
        telegram_controller = TelegramController()
        service = RemindExpDocsService()
        
        print(f"📊 Generating report for documents expiring in {days_ahead} days...")
        
        # Ambil statistik
        stats = service.get_document_statistics(db.session)
        
        # Ambil dokumen yang akan expired
        expiring_docs = service.get_expiring_documents(db.session, days_ahead=days_ahead)
        
        if not expiring_docs:
            print(f"✅ No documents expiring in {days_ahead} days. No notification sent.")
            return
        
        # Buat pesan
        docs_list = "\n".join([
            f"{i+1}. *{doc.document_name}*\n   📄 No: {doc.document_number or '-'}\n   🏢 Penerbit: {doc.issuer or '-'}\n   📅 Expired: {doc.expiry_date.strftime('%d/%m/%Y')}\n   ⏰ Sisa: *{(doc.expiry_date - date.today()).days} hari*"
            for i, doc in enumerate(expiring_docs[:10])  # Max 10 dokumen
        ])
        
        urgency = "🚨 *URGENT*" if days_ahead <= 7 else "🔔 *REMINDER*"
        
        message = f"""{urgency}: DOKUMEN AKAN EXPIRED
📅 Tanggal: {datetime.now().strftime('%d/%m/%Y %H:%M')}

📋 *Ditemukan {len(expiring_docs)} dokumen yang akan expired dalam {days_ahead} hari:*

{docs_list}

📊 *Statistik Keseluruhan:*
• Total Dokumen: {stats['total_documents']}
• Akan Expired (30 hari): {stats['expiring_30_days']}
• Akan Expired (7 hari): {stats['expiring_7_days']}
• Sudah Expired: {stats['already_expired']}

⚠️ *Segera tindak lanjuti dokumen yang akan expired!*

🔗 [Lihat Detail di Sistem](http://localhost:3000/remind-exp-docs)"""
        
        # Kirim ke Telegram
        print("📤 Sending notification to Telegram...")
        result = telegram_controller.send_message_to_admin(message)
        
        if result['success']:
            print(f"✅ Notification sent successfully!")
            print(f"📱 Message delivered to Telegram bot")
            return True
        else:
            print(f"❌ Failed to send notification: {result['message']}")
            return False

def send_statistics_report():
    """Kirim laporan statistik ke Telegram"""
    
    with app.app_context():
        telegram_controller = TelegramController()
        service = RemindExpDocsService()
        
        print("📊 Generating statistics report...")
        
        # Ambil statistik
        stats = service.get_document_statistics(db.session)
        
        # Ambil dokumen yang perlu perhatian
        expiring_7 = service.get_expiring_documents(db.session, days_ahead=7)
        expiring_30 = service.get_expiring_documents(db.session, days_ahead=30)
        
        # Buat pesan
        message = f"""📊 *LAPORAN STATISTIK DOKUMEN*
📅 Periode: {datetime.now().strftime('%d/%m/%Y %H:%M')}

📈 *Statistik:*
• 📋 Total Dokumen: *{stats['total_documents']}*
• ✅ Aktif: *{stats['active_documents']}*
• ⚠️ Akan Expired (30 hari): *{stats['expiring_30_days']}*
• 🚨 Akan Expired (7 hari): *{stats['expiring_7_days']}*
• ❌ Sudah Expired: *{stats['already_expired']}*
• 🔒 Tidak Aktif: *{stats['inactive_documents']}*

{'📋 *Dokumen Perlu Perhatian:*' if expiring_7 else ''}
{chr(10).join([f'• {doc.document_name} ({(doc.expiry_date - date.today()).days} hari)' for doc in expiring_7[:5]]) if expiring_7 else ''}

💡 *Rekomendasi:*
• Prioritas perpanjang dokumen < 7 hari
• Review dokumen yang expired
• Update status dokumen

🔗 [Lihat Detail Lengkap](http://localhost:3000/remind-exp-docs)"""
        
        # Kirim ke Telegram
        print("📤 Sending statistics to Telegram...")
        result = telegram_controller.send_message_to_admin(message)
        
        if result['success']:
            print(f"✅ Statistics report sent successfully!")
            return True
        else:
            print(f"❌ Failed to send report: {result['message']}")
            return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Send Telegram Report for Remind Exp Docs')
    parser.add_argument('--type', choices=['daily', 'stats'], default='daily', 
                       help='Report type: daily (expiring docs) or stats (statistics)')
    parser.add_argument('--days', type=int, default=30,
                       help='Days ahead for daily report (default: 30)')
    
    args = parser.parse_args()
    
    print("🚀 REMIND EXP DOCS - TELEGRAM REPORT")
    print("="*60)
    
    if args.type == 'daily':
        print(f"Report Type: Daily Expiring Documents ({args.days} days)")
        success = send_daily_report(days_ahead=args.days)
    else:
        print("Report Type: Statistics Report")
        success = send_statistics_report()
    
    print("="*60)
    
    if success:
        print("✅ Report sent successfully!")
        sys.exit(0)
    else:
        print("❌ Report failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()

