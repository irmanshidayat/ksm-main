#### Via PowerShell:

```powershell
# Check system status
Invoke-WebRequest -Uri "http://localhost:8000/api/notification/test/public" -Method GET

# Test manual report
$body = @{ date = "2025-10-23"; dry_run = $false } | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8000/api/notification/test/manual-report" -Method POST -Body $body -ContentType "application/json"

# Force trigger
Invoke-WebRequest -Uri "http://localhost:8000/api/notification/test/force-trigger-now" -Method POST
```


# 📋 Daily Task Notification System - User Guide

## 🎯 Overview

Sistem Daily Task Notification adalah fitur otomatis yang mengirim laporan harian task ke Telegram setiap hari kerja pada jam yang ditentukan. Sistem ini terintegrasi dengan Agent AI untuk format report yang professional.

## 🏗️ Architecture

```
Database (MySQL) → Backend ksm-main → Agent AI → Telegram Bot
```

### Components:
- **Backend ksm-main** (Port 8000): Query data, scheduler, Telegram integration
- **Agent AI** (Port 5000): Format report ke JSON yang professional
- **Database**: MySQL dengan tabel `daily_tasks`
- **Telegram Bot**: Kirim report ke chat/grup

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Copy environment file
cp env.example .env

# Edit .env dengan konfigurasi yang benar
nano .env
```

### 2. Konfigurasi .env

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_DEFAULT_CHAT_ID=your_chat_id_here
ADMIN_ALERT_CHAT_ID=your_admin_chat_id_here

# Scheduler Configuration
TIMEZONE=Asia/Jakarta
SCHEDULER_ENABLED=true
DAILY_REPORT_TIME=17:00

# Agent AI Configuration
AGENT_AI_BASE_URL=http://localhost:5000
AGENT_AI_API_KEY=KSM_api_key_2ptybn
```

### 3. Start Services

```bash
# Terminal 1: Start Backend ksm-main
cd Client\ Projects/ksm-main/backend
ksm_venv\Scripts\activate
python app.py

# Terminal 2: Start Agent AI
cd Agent\ AI
agent_venv\Scripts\activate
python app.py
```

## 📱 Telegram Setup

### 1. Buat Bot Telegram

1. Buka Telegram, cari @BotFather
2. Kirim `/newbot`
3. Ikuti instruksi untuk membuat bot
4. Simpan Bot Token

### 2. Dapatkan Chat ID

#### Method 1: Via Bot
```bash
# 1. Kirim pesan ke bot
# 2. Buka: https://api.telegram.org/bot<BOT_TOKEN>/getUpdates
# 3. Lihat chat.id di response
```

#### Method 2: Via @userinfobot
1. Add @userinfobot ke grup
2. Bot akan kirim Chat ID

#### Method 3: Via @getidsbot
1. Forward pesan dari grup ke @getidsbot
2. Bot akan kirim Chat ID

### 3. Update .env

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_DEFAULT_CHAT_ID=2054126414
ADMIN_ALERT_CHAT_ID=2054126414
```

## 🧪 Testing

### 1. Test System Status

```bash
# Test semua koneksi
GET http://localhost:8000/api/notification/test/public
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Daily Task Notification System is working",
  "data": {
    "connections": {
      "agent_ai": {"success": true, "message": "Agent AI connection successful"},
      "database": {"success": true, "message": "Database connection successful"},
      "telegram": {"success": true, "message": "Bot connected: Finance Resport (@FinanceReportimn_bot)"}
    },
    "scheduler": {
      "enabled": true,
      "running": true,
      "report_time": "17:00",
      "timezone": "Asia/Jakarta"
    }
  }
}
```

### 2. Test Manual Report

#### Dry Run (Test tanpa kirim ke Telegram)
```bash
POST http://localhost:8000/api/notification/test/manual-report
{
  "date": "2025-10-23",
  "dry_run": true
}
```

#### Send to Telegram
```bash
POST http://localhost:8000/api/notification/test/manual-report
{
  "date": "2025-10-23",
  "dry_run": false
}
```

**Expected Result:**
- ✅ Response: Status 200 dengan success
- ✅ Telegram: Report terkirim ke chat yang dikonfigurasi

### 3. Test Scheduler (Tanpa Menunggu Waktu)

#### Force Trigger (Instant)
```bash
# Trigger sekarang juga - tidak perlu menunggu waktu
POST http://localhost:8000/api/notification/test/force-trigger-now
```

#### Simulate Scheduler
```bash
# Simulate dengan tanggal tertentu
POST http://localhost:8000/api/notification/test/simulate-scheduler
{
  "date": "2025-10-23"
}
```

**Expected Result:**
- ✅ Response: Status 200 dengan success
- ✅ Telegram: Report terkirim langsung

### 4. Test Scheduler (Real-time)

```bash
# Update waktu ke 1-2 menit dari sekarang
POST http://localhost:8000/api/notification/test/update-scheduler-time
{
  "time": "09:26"
}
```

**Expected Result:**
- ✅ Response: Status 200 dengan success
- ✅ Scheduler: Waktu berubah ke 09:26
- ✅ Next Run: Scheduler akan run pada 09:26

## 🧪 Manual Testing Tutorial

### Prerequisites untuk Testing Manual

**Yang Harus Sudah Running:**
1. ✅ **Backend ksm-main** - Port 8000
2. ✅ **Agent AI** - Port 5000  
3. ✅ **Database** - MySQL dengan data tasks
4. ✅ **Telegram Bot** - Sudah dikonfigurasi

**Tools yang Dibutuhkan:**
- **Postman** (recommended) atau **curl**
- **Browser** untuk GET requests
- **Telegram** untuk melihat hasil

### Step-by-Step Manual Testing

#### Step 1: Check System Status

**Via Browser:**
```
http://localhost:8000/api/notification/test/public
```

**Via Postman:**
- **Method**: GET
- **URL**: `http://localhost:8000/api/notification/test/public`

**Expected Response:**
```json
{
  "success": true,
  "message": "Daily Task Notification System is working",
  "data": {
    "connections": {
      "agent_ai": {"success": true},
      "database": {"success": true},
      "telegram": {"success": true}
    },
    "scheduler": {
      "enabled": true,
      "running": true,
      "report_time": "17:00"
    }
  }
}
```

#### Step 2: Test Manual Report Generation

**Via Postman:**
- **Method**: POST
- **URL**: `http://localhost:8000/api/notification/test/manual-report`
- **Headers**: `Content-Type: application/json`
- **Body** (JSON):
```json
{
  "date": "2025-10-23",
  "dry_run": true
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Manual report generated successfully for 2025-10-23",
  "data": {
    "report": {
      "title": "📋 DAILY TASK REPORT - 23/10/2025",
      "summary": {
        "total": 3,
        "done": 0,
        "pending": 3,
        "progressPercent": 0
      },
      "sections": {
        "pendingTasks": [...],
        "doneToday": [...]
      }
    }
  }
}
```

#### Step 3: Test Send Report to Telegram

**Via Postman:**
- **Method**: POST
- **URL**: `http://localhost:8000/api/notification/test/manual-report`
- **Headers**: `Content-Type: application/json`
- **Body** (JSON):
```json
{
  "date": "2025-10-23",
  "dry_run": false
}
```

**Expected Result:**
- ✅ **Response**: Status 200 dengan success
- ✅ **Telegram**: Report terkirim ke chat yang dikonfigurasi

#### Step 4: Test Force Trigger (Instant)

**Via Postman:**
- **Method**: POST
- **URL**: `http://localhost:8000/api/notification/test/force-trigger-now`
- **Body**: Empty

**Expected Result:**
- ✅ **Response**: Status 200 dengan success
- ✅ **Telegram**: Report terkirim langsung

#### Step 5: Test Simulate Scheduler

**Via Postman:**
- **Method**: POST
- **URL**: `http://localhost:8000/api/notification/test/simulate-scheduler`
- **Headers**: `Content-Type: application/json`
- **Body** (JSON):
```json
{
  "date": "2025-10-23"
}
```

**Expected Result:**
- ✅ **Response**: Status 200 dengan success
- ✅ **Telegram**: Report terkirim dengan logic scheduler

#### Step 6: Test Update Scheduler Time

**Via Postman:**
- **Method**: POST
- **URL**: `http://localhost:8000/api/notification/test/update-scheduler-time`
- **Headers**: `Content-Type: application/json`
- **Body** (JSON):
```json
{
  "time": "09:30"
}
```

**Expected Result:**
- ✅ **Response**: Status 200 dengan success
- ✅ **Scheduler**: Waktu berubah ke 09:30

### Advanced Testing

#### Test 1: Different Dates

```json
// Test dengan tanggal kemarin
{
  "date": "2025-10-22",
  "dry_run": false
}

// Test dengan tanggal besok
{
  "date": "2025-10-24",
  "dry_run": false
}
```

#### Test 2: Multiple Triggers

```bash
# Test multiple force triggers
POST /api/notification/test/force-trigger-now
POST /api/notification/test/force-trigger-now
POST /api/notification/test/force-trigger-now
```

#### Test 3: Time Updates

```json
// Update ke waktu yang berbeda
{
  "time": "10:00"
}

{
  "time": "14:30"
}

{
  "time": "16:45"
}
```

### Quick Test Commands

#### Via curl (Command Line):

```bash
# Check system status
curl http://localhost:8000/api/notification/test/public

# Test manual report
curl -X POST http://localhost:8000/api/notification/test/manual-report \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-10-23", "dry_run": false}'

# Force trigger
curl -X POST http://localhost:8000/api/notification/test/force-trigger-now

# Update scheduler time
curl -X POST http://localhost:8000/api/notification/test/update-scheduler-time \
  -H "Content-Type: application/json" \
  -d '{"time": "09:30"}'
```

#### Via PowerShell:

```powershell
# Check system status
Invoke-WebRequest -Uri "http://localhost:8000/api/notification/test/public" -Method GET

# Test manual report
$body = @{ date = "2025-10-23"; dry_run = $false } | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8000/api/notification/test/manual-report" -Method POST -Body $body -ContentType "application/json"

# Force trigger
Invoke-WebRequest -Uri "http://localhost:8000/api/notification/test/force-trigger-now" -Method POST
```

### Testing Checklist

#### Basic Testing:
- [ ] System status check
- [ ] Manual report generation (dry run)
- [ ] Manual report generation (send to Telegram)
- [ ] Force trigger test
- [ ] Simulate scheduler test

#### Advanced Testing:
- [ ] Different dates testing
- [ ] Multiple triggers testing
- [ ] Time updates testing
- [ ] Error scenarios testing

#### Telegram Testing:
- [ ] Report format verification
- [ ] Content accuracy check
- [ ] Multiple recipients test
- [ ] Error notifications test

### Success Criteria

#### Testing Berhasil Jika:
1. ✅ **System Status**: Semua koneksi sukses
2. ✅ **Manual Report**: Report ter-generate dengan benar
3. ✅ **Telegram Send**: Report terkirim ke Telegram
4. ✅ **Force Trigger**: Instant trigger berfungsi
5. ✅ **Scheduler**: Time update berfungsi
6. ✅ **Format**: Report format sesuai ekspektasi

#### Production Ready Jika:
1. ✅ **All tests pass**
2. ✅ **No errors in logs**
3. ✅ **Telegram notifications working**
4. ✅ **Scheduler running correctly**
5. ✅ **Error handling working**

## 📊 Report Format

### Sample Report yang Dikirim ke Telegram:

```
📋 DAILY TASK REPORT - 23/10/2025

📊 SUMMARY:
• Total: 3 tasks
• Done: 0 tasks  
• Pending: 3 tasks
• Progress: 0%

📝 PENDING TASKS:
• testt (In Progress) - 6m
• testtt (To Do) - N/A
• test 23 (To Do) - N/A

✅ COMPLETED TODAY:
• No completed tasks

💡 RECOMMENDATIONS:
• Progress task masih rendah, pertimbangkan untuk memindahkan task ke hari berikutnya
```

## ⚙️ Configuration Options

### Scheduler Configuration

```env
# Timezone
TIMEZONE=Asia/Jakarta

# Enable/disable scheduler
SCHEDULER_ENABLED=true

# Waktu daily report (format: HH:MM, 24-hour)
DAILY_REPORT_TIME=17:00

# Hanya kirim pada hari kerja (Senin-Jumat)
REPORT_WEEKDAYS_ONLY=true
```

### Report Configuration

```env
# Enable/disable daily report
REPORT_ENABLED=true

# Frekuensi report (daily, weekly, custom)
REPORT_FREQUENCY=daily
```

### Error Handling

```env
# Enable/disable error notifications
ERROR_NOTIFICATION_ENABLED=true

# Method untuk error notifications (telegram, email, both)
ERROR_NOTIFICATION_METHOD=telegram
```

## 🔧 API Endpoints

### Public Endpoints (No Authentication)

#### 1. System Status
```bash
GET /api/notification/test/public
```
**Response:**
```json
{
  "success": true,
  "message": "Daily Task Notification System is working",
  "data": {
    "connections": {
      "agent_ai": {"success": true, "message": "Agent AI connection successful"},
      "database": {"success": true, "message": "Database connection successful"},
      "telegram": {"success": true, "message": "Bot connected: Finance Resport (@FinanceReportimn_bot)"}
    },
    "scheduler": {
      "enabled": true,
      "running": true,
      "report_time": "17:00",
      "timezone": "Asia/Jakarta",
      "next_run_time": "2025-10-23T17:00:00+07:00"
    }
  }
}
```

#### 2. Manual Report Generation
```bash
POST /api/notification/test/manual-report
{
  "date": "2025-10-23",
  "dry_run": false
}
```

#### 3. Force Trigger Scheduler
```bash
POST /api/notification/test/force-trigger-now
```

#### 4. Simulate Scheduler
```bash
POST /api/notification/test/simulate-scheduler
{
  "date": "2025-10-23"
}
```

#### 5. Update Scheduler Time
```bash
POST /api/notification/test/update-scheduler-time
{
  "time": "09:25"
}
```

### Protected Endpoints (Require Authentication)

#### 1. Scheduler Status
```bash
GET /api/notification/scheduler/status
```

#### 2. Start/Stop Scheduler
```bash
POST /api/notification/scheduler/start
POST /api/notification/scheduler/stop
```

## 🐛 Troubleshooting

### 1. Telegram Bot Connection Failed

**Error:** `Bot connection failed`
**Solution:**
1. Pastikan Bot Token benar
2. Pastikan bot sudah di-start dengan @BotFather
3. Test koneksi: `https://api.telegram.org/bot<BOT_TOKEN>/getMe`

### 2. Chat ID Not Found

**Error:** `Bad Request: chat not found`
**Solution:**
1. Pastikan bot sudah ditambahkan ke chat/grup
2. Pastikan Chat ID format benar (tanpa minus untuk private chat)
3. Test kirim pesan manual ke bot

### 3. Agent AI Connection Failed

**Error:** `Agent AI health check failed`
**Solution:**
1. Pastikan Agent AI running di port 5000
2. Test: `GET http://localhost:5000/health`
3. Pastikan API key benar

### 4. Database Connection Failed

**Error:** `Database connection failed`
**Solution:**
1. Pastikan MySQL running
2. Pastikan database URL benar di .env
3. Test koneksi database

### 5. Scheduler Not Running

**Error:** `Scheduler is not running`
**Solution:**
1. Pastikan `SCHEDULER_ENABLED=true` di .env
2. Restart backend
3. Check logs untuk error

## 📝 Logs

### Backend Logs
```bash
# Check backend logs
tail -f logs/app.log

# Check scheduler logs
grep "Daily Task" logs/app.log
```

### Agent AI Logs
```bash
# Check Agent AI logs
tail -f agent_ai.log
```

## 🔄 Maintenance

### 1. Update Scheduler Time

```bash
# Update via API
POST /api/notification/test/update-scheduler-time
{
  "time": "09:00"
}

# Atau update .env dan restart
DAILY_REPORT_TIME=09:00
```

### 2. Disable Scheduler

```bash
# Via .env
SCHEDULER_ENABLED=false

# Atau via API (jika ada endpoint)
POST /api/notification/scheduler/stop
```

### 3. Change Report Recipients

```bash
# Update Chat ID di .env
TELEGRAM_DEFAULT_CHAT_ID=new_chat_id_here
ADMIN_ALERT_CHAT_ID=new_admin_chat_id_here

# Restart backend
```

## 📈 Monitoring

### 1. Health Check

```bash
# Check system health
GET http://localhost:8000/api/notification/test/public
```

### 2. Scheduler Status

```bash
# Check scheduler status
GET http://localhost:8000/api/notification/scheduler/status
```

### 3. Test Connections

```bash
# Test all connections
GET http://localhost:8000/api/notification/test/connections
```

## 🚀 Production Deployment

### 1. Environment Setup

```bash
# Production .env
FLASK_ENV=production
FLASK_DEBUG=False
SCHEDULER_ENABLED=true
DAILY_REPORT_TIME=17:00
```

### 2. Process Management

```bash
# Using PM2 (Node.js process manager)
pm2 start app.py --name "ksm-backend"
pm2 start app.py --name "agent-ai" --cwd "Agent AI"

# Using systemd (Linux)
sudo systemctl start ksm-backend
sudo systemctl start agent-ai
```

### 3. Monitoring

```bash
# Check processes
pm2 status
pm2 logs ksm-backend
pm2 logs agent-ai
```

## 📞 Support

### Common Issues:

1. **Report tidak terkirim**: Check Telegram bot token dan Chat ID
2. **Scheduler tidak jalan**: Check `SCHEDULER_ENABLED=true` dan restart backend
3. **Format report aneh**: Check Agent AI connection dan API key
4. **Database error**: Check MySQL connection dan database URL

### Debug Commands:

```bash
# Test semua koneksi
curl http://localhost:8000/api/notification/test/public

# Test manual report
curl -X POST http://localhost:8000/api/notification/test/force-trigger-now

# Check scheduler status
curl http://localhost:8000/api/notification/scheduler/status
```

---

## 📋 Summary

Sistem Daily Task Notification memberikan:

✅ **Automatic Reports**: Kirim laporan harian otomatis ke Telegram
✅ **Professional Format**: Report diformat oleh Agent AI
✅ **Flexible Scheduling**: Bisa set waktu kapan saja
✅ **Easy Testing**: Multiple testing methods tanpa menunggu waktu
✅ **Robust Error Handling**: Notifikasi error ke admin
✅ **Production Ready**: Siap deploy dengan monitoring

**Sistem siap digunakan untuk production!** 🚀
