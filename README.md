# KSM Main

Sistem manajemen terintegrasi untuk PT. Kian Santang Muliatama dengan fitur AI-powered chatbot dan RAG (Retrieval-Augmented Generation).

## 📋 Deskripsi

KSM Main adalah aplikasi web full-stack yang terdiri dari:
- **Backend**: Flask REST API dengan integrasi AI/ML
- **Frontend**: React + Vite + TypeScript dengan Tailwind CSS
- **Agent AI**: Service terpisah untuk LLM dan RAG processing
- **Database**: MySQL dengan SQLAlchemy ORM
- **Cache**: Redis untuk caching dan session management

## 🏗️ Struktur Project

```
.
├── Agent AI/              # AI Service (Flask) - LLM & RAG Processing
│   ├── app.py
│   ├── controllers/      # API endpoints
│   ├── services/         # Business logic (LLM, RAG)
│   ├── models/           # Data models
│   └── requirements.txt
│
├── ksm-main/             # Main Application
│   ├── backend/          # Flask Backend API
│   │   ├── app.py
│   │   ├── controllers/  # API controllers
│   │   ├── services/     # Business logic
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routes/       # API routes
│   │   ├── migrations/   # Database migrations
│   │   └── requirements.txt
│   │
│   ├── frontend-vite/    # React Frontend (Vite)
│   │   ├── src/
│   │   │   ├── app/      # App config (store, router)
│   │   │   ├── core/     # Core abstractions
│   │   │   ├── features/ # Feature modules
│   │   │   └── shared/   # Shared components
│   │   └── package.json
│   │
│   ├── infrastructure/   # Docker & Infrastructure configs
│   │   ├── mysql-init/
│   │   ├── nginx/
│   │   └── redis/
│   │
│   └── docker-compose.yml # Docker Compose untuk Production
│
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** dan npm
- **MySQL 8.0+** (XAMPP atau standalone)
- **Redis** (optional, untuk caching)
- **Git**

### Development Setup

#### 1. Clone Repository

```bash
git clone https://github.com/irmanshidayat/ksm-main.git
cd ksm-main
```

#### 2. Backend Setup

```bash
cd ksm-main/backend

# Create virtual environment
python -m venv ksm_venv

# Activate virtual environment
# Windows:
ksm_venv\Scripts\activate
# Linux/Mac:
source ksm_venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env dengan konfigurasi database lokal

# Run migrations (jika ada)
# flask db upgrade

# Run backend
python app.py
```

Backend akan berjalan di `http://localhost:8000`

#### 3. Agent AI Setup

```bash
cd ../../Agent AI

# Create virtual environment
python -m venv agent_venv

# Activate virtual environment
# Windows:
agent_venv\Scripts\activate
# Linux/Mac:
source agent_venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env dengan konfigurasi OpenAI API key

# Run Agent AI
python app.py
```

Agent AI akan berjalan di `http://localhost:5000`

#### 4. Frontend Setup

```bash
cd ../ksm-main/frontend-vite

# Install dependencies
npm install

# Setup environment
cp .env.example .env
# Edit .env dengan API URL

# Run development server
npm run dev
```

Frontend akan berjalan di `http://localhost:3004`

## 🐳 Docker Production Setup

Untuk deployment production menggunakan Docker:

```bash
cd ksm-main

# Setup environment
cp env.example .env
# Edit .env dengan konfigurasi production

# Build and run
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

Services akan tersedia di:
- **Frontend**: `http://localhost:3005`
- **Backend API**: `http://localhost:8001`
- **Agent AI**: `http://localhost:5001`
- **MySQL**: `localhost:3308`
- **Redis**: `localhost:6380`
- **Adminer**: `http://localhost:8083`

## 📚 Dokumentasi

### Backend
- API Documentation: Lihat `ksm-main/backend/docs/`
- Database Migrations: `ksm-main/backend/migrations/`

### Frontend
- Frontend Guide: `ksm-main/frontend-vite/README.md`
- Migration Guide: `ksm-main/frontend-vite/MIGRATION_GUIDE.md`

### Agent AI
- Agent AI Guide: `Agent AI/README.md`

## 🔧 Konfigurasi

### Environment Variables

Setiap service memiliki file `env.example` yang harus di-copy ke `.env`:

- `ksm-main/backend/env.example` → `.env`
- `ksm-main/frontend-vite/.env.example` → `.env`
- `Agent AI/env.example` → `.env`

**PENTING**: Jangan commit file `.env` ke repository! File ini berisi informasi sensitif.

### Database Configuration

#### Development (XAMPP)
```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=KSM_main
DB_USER=root
DB_PASSWORD=
```

#### Production (Docker)
```env
DB_HOST=mysql-prod
DB_PORT=3306
DB_NAME=KSM_main
DB_USER=root
DB_PASSWORD=your_password
```

## 🧪 Testing

### Backend Tests
```bash
cd ksm-main/backend
pytest
```

### Frontend Tests
```bash
cd ksm-main/frontend-vite
npm test
```

## 📦 Tech Stack

### Backend
- **Flask 3.0** - Web framework
- **SQLAlchemy 2.0** - ORM
- **Flask-JWT-Extended** - Authentication
- **PyMySQL** - MySQL driver
- **Redis** - Caching
- **OpenAI API** - AI integration
- **Qdrant** - Vector database untuk RAG

### Frontend
- **React 18** - UI library
- **Vite** - Build tool
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Redux Toolkit** - State management
- **React Router v6** - Routing
- **Axios** - HTTP client

### Agent AI
- **Flask 2.3** - Web framework
- **OpenAI API** - LLM integration
- **SQLAlchemy** - Database ORM

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy
- **MySQL 8.0** - Database
- **Redis** - Cache & session store

## 🔐 Security

- JWT-based authentication
- Environment-based configuration
- API key validation
- CORS protection
- Input validation & sanitization
- Rate limiting

## 📝 License

Internal use only - PT. Kian Santang Muliatama

## 👥 Contributors

- Development Team - KSM Group

## 📞 Support

Untuk pertanyaan atau issue, silakan buat issue di repository atau hubungi development team.

---

**Catatan**: Pastikan untuk tidak commit file `.env`, `*.log`, atau file sensitif lainnya ke repository.

