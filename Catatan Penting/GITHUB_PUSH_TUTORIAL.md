# Tutorial Push Project ke GitHub

Panduan lengkap untuk mengupload project KSM Main ke GitHub dengan aman dan benar.

## 📋 Daftar Isi

1. [Persiapan](#persiapan)
2. [Setup Repository](#setup-repository)
3. [Menghapus Secrets](#menghapus-secrets)
4. [Membuat Fresh Repository](#membuat-fresh-repository)
5. [Push ke GitHub](#push-ke-github)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Persiapan

### 1. Pastikan File Penting Sudah Ada

Sebelum push ke GitHub, pastikan file-file berikut sudah ada:

- ✅ `.gitignore` (root level) - untuk mengabaikan file sensitif
- ✅ `README.md` (root level) - dokumentasi project
- ✅ `env.example` - template environment variables (tanpa secrets)

### 2. Periksa File yang Akan Di-Ignore

Pastikan file berikut **TIDAK** akan ter-commit:
- `.env` files
- `*.log` files
- `venv/`, `agent_venv/`, `ksm_venv/`
- `node_modules/`
- `*.db`, `*.sqlite`
- `cache/`, `uploads/`, `temp/`
- File dengan secrets/API keys

---

## 🔧 Setup Repository

### Langkah 1: Inisialisasi Git Repository

```bash
# Navigate ke root project
cd "C:\Irman\Coding KSM Main\KSM Grup - dev"

# Inisialisasi repository (jika belum ada)
git init
```

### Langkah 2: Buat Repository di GitHub

1. Login ke GitHub: https://github.com
2. Klik **New Repository** atau **+** → **New repository**
3. Isi informasi:
   - **Repository name**: `ksm-main`
   - **Description**: (opsional) Deskripsi project
   - **Visibility**: Private atau Public (sesuai kebutuhan)
   - **JANGAN** centang "Initialize with README" (karena kita sudah punya)
4. Klik **Create repository**

### Langkah 3: Tambahkan Remote Origin

```bash
# Tambahkan remote origin
git remote add origin https://github.com/irmanshidayat/ksm-main.git

# Verifikasi remote
git remote -v
```

---

## 🔒 Menghapus Secrets dari File

**PENTING**: GitHub Push Protection akan memblokir push jika mendeteksi secrets di repository.

### File yang Perlu Diperiksa dan Diperbaiki:

1. **Agent AI/env.example**
   - Ganti `OPENAI_API_KEY` dengan `your_openai_api_key_here`
   - Ganti `OPENROUTER_API_KEY` dengan `your_openrouter_api_key_here`
   - Ganti `TELEGRAM_BOT_TOKEN` dengan `your_telegram_bot_token_here`

2. **Agent AI/README.md**
   - Ganti contoh API key di dokumentasi dengan placeholder

3. **ksm-main/env.example**
   - Ganti semua API keys dengan placeholder
   - Ganti `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `TELEGRAM_BOT_TOKEN`, dll.

4. **ksm-main/backend/env.example**
   - Ganti `GMAIL_CLIENT_ID` dengan `your_google_client_id_here`
   - Ganti `GMAIL_CLIENT_SECRET` dengan `your_google_client_secret_here`
   - Ganti `QDRANT_API_KEY` dengan `your_qdrant_api_key_here`

### Contoh Perubahan:

**Sebelum:**
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Sesudah:**
```env
OPENAI_API_KEY=your_openai_api_key_here
```

---

## 🆕 Membuat Fresh Repository

Jika repository sudah ada dan mengandung secrets di commit history, kita perlu membuat fresh repository:

### Langkah 1: Hapus Git History

```bash
# Hapus folder .git (menghapus semua history)
Remove-Item -Recurse -Force .git

# Atau di Linux/Mac:
rm -rf .git
```

### Langkah 2: Inisialisasi Repository Baru

```bash
# Inisialisasi repository baru
git init

# Tambahkan semua file
git add .
```

### Langkah 3: Buat Commit Pertama

```bash
# Buat commit pertama
git commit -m "first commit"

# Set branch ke main
git branch -M main
```

---

## 🚀 Push ke GitHub

### Langkah 1: Tambahkan Remote Origin

```bash
# Tambahkan remote origin
git remote add origin https://github.com/irmanshidayat/ksm-main.git
```

### Langkah 2: Push ke GitHub

```bash
# Push ke GitHub dengan set upstream
git push -u origin main
```

### Output yang Diharapkan:

```
Enumerating objects: 521, done.
Counting objects: 100% (521/521), done.
Delta compression using up to 8 threads
Compressing objects: 100% (500/500), done.
Writing objects: 100% (521/521), 2.5 MiB | 1.2 MiB/s, done.
Total 521 (delta 50), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (50/50), done.
To https://github.com/irmanshidayat/ksm-main.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```

---

## ✅ Verifikasi

### 1. Cek di GitHub

1. Buka: https://github.com/irmanshidayat/ksm-main
2. Pastikan semua file sudah ter-upload
3. Pastikan `.env` files **TIDAK** ada di repository

### 2. Cek File yang Ter-Ignore

```bash
# Cek file yang di-ignore
git status --ignored
```

Pastikan file berikut muncul sebagai ignored:
- `.env`
- `*.log`
- `venv/`, `agent_venv/`, `ksm_venv/`
- `node_modules/`
- `*.db`

---

## 🔄 Update Repository (Setelah Perubahan)

### Menambahkan Perubahan Baru

```bash
# Tambahkan file yang diubah
git add .

# Atau tambahkan file spesifik
git add path/to/file

# Commit perubahan
git commit -m "Deskripsi perubahan"

# Push ke GitHub
git push
```

### Menghapus File dari Repository

```bash
# Hapus file dari repository (tapi tetap di local)
git rm --cached file.txt

# Commit perubahan
git commit -m "Remove file from repository"

# Push ke GitHub
git push
```

---

## 🛠️ Troubleshooting

### Error: "Push cannot contain secrets"

**Masalah**: GitHub Push Protection mendeteksi secrets di commit history.

**Solusi**:
1. Hapus secrets dari file `env.example` dan `README.md`
2. Buat fresh repository (hapus `.git` dan buat ulang)
3. Atau gunakan `git filter-branch` untuk menghapus secrets dari history (advanced)

### Error: "Repository not found"

**Masalah**: Remote URL salah atau repository belum dibuat di GitHub.

**Solusi**:
```bash
# Cek remote URL
git remote -v

# Ubah remote URL jika salah
git remote set-url origin https://github.com/username/repository.git
```

### Error: "Permission denied"

**Masalah**: Tidak memiliki akses ke repository atau belum login.

**Solusi**:
1. Login ke GitHub di browser
2. Gunakan Personal Access Token (PAT) untuk authentication
3. Atau setup SSH key untuk GitHub

### Error: "Branch 'main' has no upstream branch"

**Masalah**: Branch belum di-set untuk tracking remote branch.

**Solusi**:
```bash
# Set upstream branch
git push -u origin main
```

### File `.env` Ter-Commit

**Masalah**: File `.env` ter-commit ke repository.

**Solusi**:
```bash
# Hapus dari repository (tapi tetap di local)
git rm --cached .env

# Tambahkan ke .gitignore (jika belum)
echo ".env" >> .gitignore

# Commit perubahan
git commit -m "Remove .env from repository"

# Push ke GitHub
git push
```

**PENTING**: Jika `.env` sudah ter-push, secrets sudah terekspos. Segera:
1. Rotate semua API keys dan secrets
2. Hapus file dari repository
3. Hapus dari commit history (gunakan `git filter-branch` atau buat fresh repository)

---

## 📝 Best Practices

### 1. Jangan Commit Secrets

- ✅ Gunakan `env.example` dengan placeholder
- ✅ Pastikan `.env` ada di `.gitignore`
- ✅ Jangan hardcode secrets di kode

### 2. Gunakan .gitignore yang Komprehensif

Pastikan `.gitignore` mencakup:
- Environment files (`.env`, `.env.local`)
- Logs (`*.log`, `logs/`)
- Virtual environments (`venv/`, `env/`)
- Dependencies (`node_modules/`, `__pycache__/`)
- Database files (`*.db`, `*.sqlite`)
- Cache dan temporary files

### 3. Commit Message yang Jelas

Gunakan commit message yang deskriptif:
```bash
# ❌ Buruk
git commit -m "fix"

# ✅ Baik
git commit -m "Fix authentication bug in login controller"
```

### 4. Review Sebelum Push

Selalu review perubahan sebelum push:
```bash
# Lihat perubahan yang akan di-commit
git diff

# Lihat status
git status
```

### 5. Gunakan Branch untuk Development

Jangan langsung commit ke `main`:
```bash
# Buat branch baru
git checkout -b feature/nama-fitur

# Commit perubahan
git commit -m "Add new feature"

# Push branch
git push -u origin feature/nama-fitur

# Buat Pull Request di GitHub
```

---

## 🔐 Security Checklist

Sebelum push ke GitHub, pastikan:

- [ ] Semua secrets sudah dihapus dari `env.example`
- [ ] File `.env` ada di `.gitignore`
- [ ] Tidak ada API keys di kode source
- [ ] Tidak ada credentials di commit history
- [ ] Repository visibility sudah sesuai (Private/Public)
- [ ] README.md sudah diupdate dengan instruksi setup

---

## 📚 Referensi

- [GitHub Documentation](https://docs.github.com)
- [Git Documentation](https://git-scm.com/doc)
- [GitHub Secret Scanning](https://docs.github.com/code-security/secret-scanning)
- [Git Ignore Patterns](https://git-scm.com/docs/gitignore)

---

## 💡 Tips Tambahan

### Setup Git Credentials (Windows)

```bash
# Setup username dan email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Setup credential helper (untuk Windows)
git config --global credential.helper wincred
```

### Clone Repository (untuk Developer Lain)

```bash
# Clone repository
git clone https://github.com/irmanshidayat/ksm-main.git

# Masuk ke folder
cd ksm-main

# Copy env.example ke .env
cp env.example .env

# Edit .env dengan credentials yang sesuai
```

### Menghapus File dari History (Advanced)

Jika secrets sudah ter-commit di history lama:

```bash
# Install git-filter-repo (recommended)
pip install git-filter-repo

# Hapus file dari semua commit
git filter-repo --path file-with-secret.txt --invert-paths

# Force push (HATI-HATI!)
git push origin --force --all
```

**PENTING**: Force push akan mengubah history. Pastikan semua developer sudah diinformasikan!

---

## ✅ Checklist Final

Sebelum push, pastikan:

- [ ] `.gitignore` sudah lengkap
- [ ] `README.md` sudah dibuat
- [ ] Semua secrets sudah dihapus dari `env.example`
- [ ] File `.env` tidak ter-commit
- [ ] Repository sudah dibuat di GitHub
- [ ] Remote origin sudah di-set
- [ ] Commit message sudah jelas
- [ ] Sudah review perubahan (`git status`, `git diff`)

---

**Selamat!** Project Anda sudah ter-upload ke GitHub dengan aman. 🎉

---

*Tutorial ini dibuat untuk project KSM Main. Update terakhir: 2024*

