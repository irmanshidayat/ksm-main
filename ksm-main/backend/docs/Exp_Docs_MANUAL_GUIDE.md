# 📱 TELEGRAM MANUAL NOTIFICATION GUIDE

## 📋 RINGKASAN

**Project:** Remind Exp Docs - Telegram Integration  
**Version:** 1.0  
**Date:** 23 Oktober 2025  
**Status:** ✅ Production Ready  

Dokumentasi lengkap untuk mengirim notifikasi manual dan mengubah konfigurasi sistem.

---

## 🚀 CARA KIRIM NOTIFIKASI MANUAL

### **1. Menggunakan Production Script (Recommended)**

#### **A. Kirim Laporan Statistik**
```bash
# Pindah ke direktori backend
cd "C:\Irman\KSM Grup - dev\Client Projects\ksm-main\backend"

# Kirim laporan statistik lengkap
python scripts\send_telegram_report.py --type stats
```

#### **B. Kirim Laporan Dokumen Expired**
```bash
# Laporan dokumen yang akan expired dalam 7 hari (URGENT)
python scripts\send_telegram_report.py --type daily --days 7

# Laporan dokumen yang akan expired dalam 14 hari
python scripts\send_telegram_report.py --type daily --days 14

# Laporan dokumen yang akan expired dalam 30 hari (DEFAULT)
python scripts\send_telegram_report.py --type daily --days 30

# Laporan dokumen yang akan expired dalam 45 hari
python scripts\send_telegram_report.py --type daily --days 45
```

#### **C. Contoh Output yang Diharapkan**
```
🚀 REMIND EXP DOCS - TELEGRAM REPORT
============================================================
Report Type: Daily Expiring Documents (7 days)
📊 Generating report for documents expiring in 7 days...
📤 Sending notification to Telegram...
✅ Notification sent successfully!
📱 Message delivered to Telegram bot
============================================================
✅ Report sent successfully!
```

---

### **2. Menggunakan API Endpoints**

#### **A. Test Koneksi Telegram**
```bash
curl -X POST http://localhost:8000/api/remind-exp-docs/test/telegram-notifications
```

#### **B. Buat Dokumen Test**
```bash
curl -X POST http://localhost:8000/api/remind-exp-docs/test/create-test-documents
```

#### **C. Bersihkan Dokumen Test**
```bash
curl -X DELETE http://localhost:8000/api/remind-exp-docs/test/cleanup-test-documents
```

---

### **3. Menggunakan Python Script Langsung**

#### **A. Buat File: `send_manual_notification.py`**
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script untuk mengirim notifikasi manual ke Telegram
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from controllers.telegram_controller import TelegramController
from services.remind_exp_docs_service import RemindExpDocsService
from datetime import datetime, date

def send_manual_notification():
    """Kirim notifikasi manual"""
    
    with app.app_context():
        telegram = TelegramController()
        service = RemindExpDocsService()
        
        # Ambil statistik
        stats = service.get_document_statistics(db.session)
        
        # Buat pesan manual
        message = f"""🔔 *NOTIFIKASI MANUAL*
📅 Tanggal: {datetime.now().strftime('%d/%m/%Y %H:%M')}

📊 *Statistik Sistem:*
• Total Dokumen: {stats['total_documents']}
• Aktif: {stats['active_documents']}
• Akan Expired (30 hari): {stats['expiring_30_days']}
• Akan Expired (7 hari): {stats['expiring_7_days']}
• Sudah Expired: {stats['already_expired']}

🔗 [Akses Sistem](http://localhost:3000/remind-exp-docs)"""
        
        # Kirim notifikasi
        result = telegram.send_message_to_admin(message)
        
        if result['success']:
            print("✅ Notifikasi manual berhasil dikirim!")
            print(f"📱 Message ID: {result.get('data', {}).get('result', {}).get('message_id', 'N/A')}")
        else:
            print(f"❌ Gagal mengirim notifikasi: {result['message']}")
        
        return result

if __name__ == '__main__':
    send_manual_notification()
```

#### **B. Jalankan Script**
```bash
python send_manual_notification.py
```

---

## ⚙️ CARA MENGUBAH KONFIGURASI HARI

### **1. File yang Perlu Diubah**

#### **A. Scheduler Configuration (PRIORITAS UTAMA)**
**File:** `backend/schedulers/remind_exp_docs_scheduler.py`

**Lokasi yang perlu diubah:**
```python
# Line ~50 - Method check_expiring_documents
def check_expiring_documents(self, days_ahead=30):  # UBAH 30 ke nilai yang diinginkan
    """Check dokumen yang akan expired"""
    # Contoh: ubah ke 45 hari
    def check_expiring_documents(self, days_ahead=45):

# Line ~100 - Method start_daily_checks  
def start_daily_checks(self):
    """Start daily checks untuk dokumen expired"""
    # Cari baris yang memanggil check_expiring_documents(30)
    # Ubah menjadi:
    self.check_expiring_documents(45)  # UBAH 30 ke 45
```

#### **B. Controller Configuration**
**File:** `backend/controllers/remind_exp_docs_controller.py`

**Lokasi yang perlu diubah:**
```python
# Line ~290 - Method get_expiring_documents
def get_expiring_documents(self):
    days_ahead = request.args.get('days_ahead', 30, type=int)  # UBAH 30 ke 45
    # Ubah menjadi:
    days_ahead = request.args.get('days_ahead', 45, type=int)
```

#### **C. Environment Configuration**
**File:** `backend/.env`

**Tambahkan konfigurasi:**
```bash
# Konfigurasi hari untuk reminder
REMIND_EXP_DAYS_AHEAD=45  # UBAH dari 30 ke 45
```

---

### **2. Langkah-langkah Implementasi**

#### **Step 1: Backup File Sebelum Diubah**
```bash
# Backup scheduler
copy "backend\schedulers\remind_exp_docs_scheduler.py" "backend\schedulers\remind_exp_docs_scheduler.py.backup"

# Backup controller  
copy "backend\controllers\remind_exp_docs_controller.py" "backend\controllers\remind_exp_docs_controller.py.backup"
```

#### **Step 2: Update Scheduler**
```python
# Di file: backend/schedulers/remind_exp_docs_scheduler.py
# Cari dan ubah semua nilai 30 menjadi 45

# Line ~50
def check_expiring_documents(self, days_ahead=45):  # UBAH

# Line ~100  
def start_daily_checks(self):
    # Cari dan ubah
    self.check_expiring_documents(45)  # UBAH
```

#### **Step 3: Update Controller**
```python
# Di file: backend/controllers/remind_exp_docs_controller.py
# Line ~290
days_ahead = request.args.get('days_ahead', 45, type=int)  # UBAH
```

#### **Step 4: Update Environment**
```bash
# Di file: backend/.env
REMIND_EXP_DAYS_AHEAD=45
```

#### **Step 5: Restart Backend**
```bash
# Stop backend (Ctrl+C)
# Start backend lagi
python app.py
```

---

### **3. Verifikasi Perubahan**

#### **A. Test dengan Script Manual**
```bash
# Test dengan nilai baru
python scripts\send_telegram_report.py --type daily --days 45
```

#### **B. Test dengan API**
```bash
# Test endpoint dengan parameter baru
curl "http://localhost:8000/api/remind-exp-docs/expiring?days_ahead=45"
```

#### **C. Check Log**
```bash
# Cek log untuk memastikan tidak ada error
tail -f backend\logs\telegram_notifications.log
```

---

## 📊 REKOMENDASI NILAI HARI

### **Untuk Perusahaan Besar:**
- **60 hari** - Sangat aman, banyak waktu untuk perpanjang
- **45 hari** - Aman, waktu cukup untuk perpanjang
- **30 hari** - Standard (current default)

### **Untuk Perusahaan Kecil:**
- **21 hari** - Cukup untuk perpanjang
- **14 hari** - Minimal untuk perpanjang
- **7 hari** - Urgent only

### **Untuk Testing:**
- **7 hari** - Test urgent notification
- **3 hari** - Test critical notification
- **1 hari** - Test immediate notification

---

## 🔧 TROUBLESHOOTING

### **1. Notifikasi Tidak Terkirim**

#### **A. Check Bot Token**
```bash
# Cek di database
python -c "
from app import app, db
from models.knowledge_base import TelegramSettings
with app.app_context():
    settings = TelegramSettings.query.first()
    print(f'Bot Token: {settings.bot_token[:20]}...' if settings.bot_token else 'No token')
    print(f'Chat ID: {settings.admin_chat_id}')
    print(f'Active: {settings.is_active}')
"
```

#### **B. Test Koneksi Telegram**
```bash
# Test koneksi langsung
python scripts\send_telegram_report.py --type stats
```

#### **C. Check Log Error**
```bash
# Cek log error
type backend\logs\telegram_notifications.log
```

### **2. Scheduler Tidak Berjalan**

#### **A. Check Scheduler Status**
```bash
# Cek di app.py line 1300-1308
# Pastikan scheduler di-start
```

#### **B. Manual Trigger**
```bash
# Trigger manual
python -c "
from app import app
from schedulers.remind_exp_docs_scheduler import remind_exp_docs_scheduler
with app.app_context():
    result = remind_exp_docs_scheduler.manual_check_expiring_documents(30)
    print(f'Result: {result}')
"
```

### **3. Database Error**

#### **A. Check Migration**
```bash
# Jalankan migration ulang
python migrations\add_admin_chat_id_to_telegram_settings.py up
```

#### **B. Check Database Connection**
```bash
# Test koneksi database
python -c "
from app import app, db
from models.remind_exp_docs import RemindExpDocs
with app.app_context():
    count = RemindExpDocs.query.count()
    print(f'Total documents: {count}')
"
```

---

## 📋 CHECKLIST IMPLEMENTASI

### **Sebelum Mengubah Konfigurasi:**
- [ ] Backup file yang akan diubah
- [ ] Stop backend server
- [ ] Test dengan nilai kecil dulu (7 hari)
- [ ] Pastikan notifikasi berfungsi

### **Setelah Mengubah Konfigurasi:**
- [ ] Update semua file yang menggunakan nilai lama
- [ ] Restart backend server
- [ ] Test dengan script manual
- [ ] Monitor log untuk error
- [ ] Test dengan data real

### **Verifikasi Akhir:**
- [ ] Notifikasi manual berfungsi
- [ ] Scheduler otomatis berfungsi
- [ ] Tidak ada error di log
- [ ] Database ter-update dengan benar

---

## 🎯 CONTOH IMPLEMENTASI LENGKAP

### **Scenario: Ubah dari 30 hari ke 45 hari**

#### **1. Backup Files**
```bash
copy "backend\schedulers\remind_exp_docs_scheduler.py" "backend\schedulers\remind_exp_docs_scheduler.py.backup"
copy "backend\controllers\remind_exp_docs_controller.py" "backend\controllers\remind_exp_docs_controller.py.backup"
```

#### **2. Update Scheduler**
```python
# File: backend/schedulers/remind_exp_docs_scheduler.py
# Line 50: Ubah
def check_expiring_documents(self, days_ahead=45):  # UBAH 30 ke 45

# Line 100: Ubah  
def start_daily_checks(self):
    self.check_expiring_documents(45)  # UBAH 30 ke 45
```

#### **3. Update Controller**
```python
# File: backend/controllers/remind_exp_docs_controller.py
# Line 290: Ubah
days_ahead = request.args.get('days_ahead', 45, type=int)  # UBAH 30 ke 45
```

#### **4. Update Environment**
```bash
# File: backend/.env
REMIND_EXP_DAYS_AHEAD=45
```

#### **5. Restart & Test**
```bash
# Restart backend
python app.py

# Test dengan nilai baru
python scripts\send_telegram_report.py --type daily --days 45
```

---

## 📞 SUPPORT

### **Jika Ada Masalah:**
1. **Check log file:** `backend/logs/telegram_notifications.log`
2. **Test koneksi:** `python scripts/send_telegram_report.py --type stats`
3. **Check database:** Pastikan `telegram_settings` table ada
4. **Check bot token:** Pastikan token valid di Telegram

### **File Log Penting:**
- `backend/logs/telegram_notifications.log` - Log notifikasi
- `backend/logs/app.log` - Log aplikasi umum
- Console output saat menjalankan script

---

## 🎉 KESIMPULAN

Dengan panduan ini, Anda dapat:
1. ✅ **Mengirim notifikasi manual** dengan berbagai cara
2. ✅ **Mengubah konfigurasi hari** sesuai kebutuhan
3. ✅ **Troubleshoot masalah** yang mungkin terjadi
4. ✅ **Memverifikasi perubahan** berfungsi dengan benar

**🚀 Sistem Telegram Integration siap digunakan untuk production!**

---

**Dokumentasi dibuat:** 23 Oktober 2025  
**Versi:** 1.0  
**Status:** Production Ready ✅
