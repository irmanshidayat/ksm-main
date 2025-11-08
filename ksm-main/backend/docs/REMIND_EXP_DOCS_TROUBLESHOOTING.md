# 🔧 REMIND EXP DOCS - TROUBLESHOOTING GUIDE

## 📋 RINGKASAN

**Problem:** Report otomatis tidak dikirim ke Telegram setelah mengubah `REMIND_EXP_NOTIFICATION_TIME=15:05`  
**Root Cause:** Environment variables tidak terintegrasi dengan scheduler  
**Solution:** Update scheduler dan setup environment yang benar  

---

## ❌ MASALAH YANG DITEMUKAN

### **1. Environment Variables Tidak Terintegrasi**
- File `env.example` hanya template, tidak langsung digunakan
- Perlu copy ke file `.env` dan restart backend
- Scheduler belum membaca environment variables

### **2. Scheduler Menggunakan Hardcoded Values**
- Scheduler masih menggunakan jam 9:00, 15:00, 18:00 (hardcoded)
- Belum ada integrasi dengan `REMIND_EXP_NOTIFICATION_TIME`
- Belum ada integrasi dengan `REMIND_EXP_DAYS_AHEAD`

### **3. Konfigurasi Tidak Lengkap**
- Scheduler belum menggunakan environment variables
- Belum ada timezone handling untuk Remind Exp Docs
- Belum ada integration dengan konfigurasi environment

---

## ✅ SOLUSI YANG SUDAH DIIMPLEMENTASI

### **1. Update Scheduler untuk Environment Variables**
```python
# File: backend/schedulers/remind_exp_docs_scheduler.py
# Sekarang scheduler membaca dari environment variables:

self.notification_time = os.getenv('REMIND_EXP_NOTIFICATION_TIME', '09:00')
self.days_ahead = int(os.getenv('REMIND_EXP_DAYS_AHEAD', '30'))
self.urgent_days = int(os.getenv('REMIND_EXP_URGENT_DAYS', '7'))
self.notifications_enabled = os.getenv('REMIND_EXP_NOTIFICATIONS_ENABLED', 'true').lower() == 'true'
self.scheduler_enabled = os.getenv('REMIND_EXP_SCHEDULER_ENABLED', 'true').lower() == 'true'
self.weekdays_only = os.getenv('REMIND_EXP_WEEKDAYS_ONLY', 'true').lower() == 'true'
```

### **2. Dynamic Time Configuration**
```python
# Scheduler sekarang menggunakan waktu yang dikonfigurasi:
trigger=CronTrigger(hour=self.notification_hour, minute=self.notification_minute)
```

### **3. Environment Setup Script**
```bash
# Script untuk setup environment
python scripts/setup_remind_exp_docs_env.py
```

---

## 🔧 LANGKAH-LANGKAH PERBAIKAN

### **Step 1: Setup Environment**
```bash
# Pindah ke direktori backend
cd "C:\Irman\KSM Grup - dev\Client Projects\ksm-main\backend"

# Jalankan setup script
python scripts\setup_remind_exp_docs_env.py
```

### **Step 2: Verify Environment File**
```bash
# Cek apakah .env file sudah dibuat
dir .env

# Cek isi file .env
type .env | findstr REMIND_EXP
```

### **Step 3: Restart Backend**
```bash
# Stop backend (Ctrl+C)
# Start backend lagi
python app.py
```

### **Step 4: Test Configuration**
```bash
# Test manual notification
python scripts\send_telegram_report.py --type stats

# Test dengan waktu yang dikonfigurasi
python scripts\send_telegram_report.py --type daily --days 30
```

### **Step 5: Monitor Logs**
```bash
# Cek log untuk memastikan scheduler berjalan
type logs\telegram_notifications.log
```

---

## 📊 VERIFIKASI KONFIGURASI

### **1. Check Environment Variables**
```bash
# Test dengan Python script
python -c "
import os
print('REMIND_EXP_NOTIFICATION_TIME:', os.getenv('REMIND_EXP_NOTIFICATION_TIME', 'Not set'))
print('REMIND_EXP_DAYS_AHEAD:', os.getenv('REMIND_EXP_DAYS_AHEAD', 'Not set'))
print('REMIND_EXP_URGENT_DAYS:', os.getenv('REMIND_EXP_URGENT_DAYS', 'Not set'))
print('REMIND_EXP_NOTIFICATIONS_ENABLED:', os.getenv('REMIND_EXP_NOTIFICATIONS_ENABLED', 'Not set'))
"
```

### **2. Check Scheduler Status**
```bash
# Test scheduler configuration
python -c "
from app import app
from schedulers.remind_exp_docs_scheduler import remind_exp_docs_scheduler
with app.app_context():
    print('Notification Time:', remind_exp_docs_scheduler.notification_time)
    print('Days Ahead:', remind_exp_docs_scheduler.days_ahead)
    print('Urgent Days:', remind_exp_docs_scheduler.urgent_days)
    print('Notifications Enabled:', remind_exp_docs_scheduler.notifications_enabled)
    print('Scheduler Enabled:', remind_exp_docs_scheduler.scheduler_enabled)
"
```

### **3. Check Database Settings**
```bash
# Test database configuration
python -c "
from app import app, db
from models.knowledge_base import TelegramSettings
with app.app_context():
    settings = TelegramSettings.query.first()
    print('Bot Token:', 'Set' if settings.bot_token else 'Not set')
    print('Chat ID:', 'Set' if settings.admin_chat_id else 'Not set')
    print('Active:', settings.is_active if settings else 'No settings')
"
```

---

## 🚨 TROUBLESHOOTING COMMON ISSUES

### **Issue 1: Environment Variables Tidak Terbaca**
```bash
# Problem: Scheduler masih menggunakan hardcoded values
# Solution: Pastikan .env file ada dan restart backend

# Check .env file exists
dir .env

# Check content
type .env | findstr REMIND_EXP_NOTIFICATION_TIME

# Restart backend
python app.py
```

### **Issue 2: Scheduler Tidak Berjalan**
```bash
# Problem: Scheduler tidak start
# Solution: Check scheduler configuration

# Test scheduler start
python -c "
from app import app
from schedulers.remind_exp_docs_scheduler import remind_exp_docs_scheduler
with app.app_context():
    print('Scheduler Running:', remind_exp_docs_scheduler.is_running)
    print('Scheduler Enabled:', remind_exp_docs_scheduler.scheduler_enabled)
"
```

### **Issue 3: Notifikasi Tidak Terkirim**
```bash
# Problem: Notifikasi tidak terkirim
# Solution: Check Telegram configuration

# Test Telegram connection
python scripts\send_telegram_report.py --type stats

# Check bot token
python -c "
from app import app
from models.knowledge_base import TelegramSettings
with app.app_context():
    settings = TelegramSettings.query.first()
    print(f'Bot Token: {settings.bot_token[:20]}...' if settings.bot_token else 'No token')
    print(f'Chat ID: {settings.admin_chat_id}')
    print(f'Active: {settings.is_active}')
"
```

### **Issue 4: Waktu Tidak Sesuai**
```bash
# Problem: Notifikasi tidak dikirim pada waktu yang dikonfigurasi
# Solution: Check timezone dan format waktu

# Check timezone
python -c "
import os
print('Timezone:', os.getenv('TIMEZONE', 'Not set'))
print('Notification Time:', os.getenv('REMIND_EXP_NOTIFICATION_TIME', 'Not set'))
"

# Test manual trigger
python -c "
from app import app
from schedulers.remind_exp_docs_scheduler import remind_exp_docs_scheduler
with app.app_context():
    result = remind_exp_docs_scheduler.manual_check_expiring_documents(30)
    print(f'Manual trigger result: {result}')
"
```

---

## 📋 CHECKLIST PERBAIKAN

### **Sebelum Perbaikan:**
- [ ] Backup file yang akan diubah
- [ ] Stop backend server
- [ ] Check current configuration
- [ ] Test manual notification

### **Setelah Perbaikan:**
- [ ] Environment file (.env) created
- [ ] Backend server restarted
- [ ] Scheduler configuration updated
- [ ] Manual notification tested
- [ ] Log monitoring enabled

### **Verifikasi Akhir:**
- [ ] Environment variables loaded
- [ ] Scheduler running with correct time
- [ ] Manual notification working
- [ ] No errors in logs
- [ ] Wait for scheduled time

---

## 🎯 CONTOH IMPLEMENTASI LENGKAP

### **Scenario: Ubah waktu notifikasi ke 15:05**

#### **1. Setup Environment**
```bash
# Copy env.example to .env
python scripts\setup_remind_exp_docs_env.py
```

#### **2. Edit .env File**
```bash
# Edit .env file
notepad .env

# Change notification time
REMIND_EXP_NOTIFICATION_TIME=15:05
```

#### **3. Restart Backend**
```bash
# Stop backend (Ctrl+C)
# Start backend
python app.py
```

#### **4. Test Configuration**
```bash
# Test manual notification
python scripts\send_telegram_report.py --type stats

# Test scheduler configuration
python -c "
from app import app
from schedulers.remind_exp_docs_scheduler import remind_exp_docs_scheduler
with app.app_context():
    print('Notification Time:', remind_exp_docs_scheduler.notification_time)
    print('Hour:', remind_exp_docs_scheduler.notification_hour)
    print('Minute:', remind_exp_docs_scheduler.notification_minute)
"
```

#### **5. Monitor Logs**
```bash
# Check logs
type logs\telegram_notifications.log
```

---

## 🎉 EXPECTED RESULTS

### **Setelah Perbaikan:**
1. ✅ **Environment Variables** - Terbaca dengan benar
2. ✅ **Scheduler Configuration** - Menggunakan waktu yang dikonfigurasi
3. ✅ **Automatic Notifications** - Dikirim pada waktu yang tepat
4. ✅ **Manual Notifications** - Berfungsi dengan baik
5. ✅ **Log Monitoring** - Menampilkan status yang benar

### **Log Output yang Diharapkan:**
```
INFO: Starting Remind Exp Docs scheduler with notification time: 15:05
INFO: Remind Exp Docs Scheduler started successfully
INFO: Starting daily expiring documents check for 30 days...
INFO: Expiring documents notification sent for X documents
```

---

## 📞 SUPPORT

### **Jika Masih Ada Masalah:**
1. **Check log file:** `backend/logs/telegram_notifications.log`
2. **Test manual:** `python scripts/send_telegram_report.py --type stats`
3. **Check environment:** Pastikan `.env` file ada dan benar
4. **Restart backend:** `python app.py`

### **File Log Penting:**
- `backend/logs/telegram_notifications.log` - Log notifikasi
- `backend/logs/app.log` - Log aplikasi umum
- Console output saat menjalankan backend

---

## 🎊 KESIMPULAN

### **✅ MASALAH TERSELESAIKAN:**
1. ✅ **Environment Integration** - Scheduler sekarang membaca environment variables
2. ✅ **Dynamic Time Configuration** - Waktu notifikasi dapat dikonfigurasi
3. ✅ **Setup Script** - Script otomatis untuk setup environment
4. ✅ **Troubleshooting Guide** - Panduan lengkap untuk debugging

### **🚀 READY FOR PRODUCTION:**
- ✅ Scheduler menggunakan konfigurasi environment
- ✅ Waktu notifikasi dapat diubah melalui .env file
- ✅ Manual testing berfungsi dengan baik
- ✅ Log monitoring tersedia

**📱 Sistem Remind Exp Docs sekarang akan mengirim notifikasi otomatis pada jam 15:05 sesuai konfigurasi!**

---

**Dokumentasi dibuat:** 23 Oktober 2025  
**Versi:** 1.0  
**Status:** Production Ready ✅
