# Tutorial Git & GitHub - KSM Main Project

Panduan ringkas untuk mengelola project KSM Main dengan Git dan GitHub.

## 📋 Daftar Isi

1. [Setup Repository](#setup-repository)
2. [Push ke GitHub](#push-ke-github)
3. [Merge Branch](#merge-branch)
4. [Resolve Merge Conflicts](#resolve-merge-conflicts)
5. [Troubleshooting](#troubleshooting)

---

## 🔧 Setup Repository

### Inisialisasi dan Remote

```bash
# Navigate ke project
cd "C:\Irman\Coding KSM Main\KSM Grup - dev"

# Inisialisasi Git (jika belum)
git init

# Setup config (jika belum)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Tambahkan remote origin
git remote add origin https://github.com/irmanshidayat/ksm-main.git
```

### File yang Di-Ignore

File berikut **TIDAK** ter-commit (sudah ada di `.gitignore`):
- `.env`, `env.example`, `env.dev.example`
- `*.log`, `venv/`, `node_modules/`, `*.db`

**Catatan**: File `env.example` dan `env.dev.example` di-ignore untuk keamanan, tetap bisa dibaca/edit lokal.

---

## 🚀 Push ke GitHub

### Push ke Branch Main

```bash
git checkout main
git add .
git commit -m "Initial commit"
git push -u origin main
```

### Push ke Branch Dev

```bash
# Buat atau switch ke dev
git checkout dev

# Commit dan push
git add .
git commit -m "Update development"
git push -u origin dev
```

### Push Feature Branch

```bash
# Buat feature branch
git checkout -b feature/nama-fitur

# Develop, commit, dan push
git add .
git commit -m "Add feature"
git push -u origin feature/nama-fitur
```

---

## 🔀 Merge Branch

### Merge Feature ke Dev

```bash
# Switch ke dev dan update
git checkout dev
git pull origin dev

# Merge feature branch
git merge feature/nama-fitur

# Push hasil merge
git push origin dev
```

### Merge Dev ke Main

```bash
# Switch ke main dan update
git checkout main
git pull origin main

# Merge dev ke main
git merge dev

# Push hasil merge
git push origin main
```

### Merge Strategies

```bash
# Fast-forward merge (default)
git merge feature/branch

# No-fast-forward (dengan merge commit)
git merge --no-ff feature/branch -m "Merge message"

# Squash merge (gabungkan semua commit jadi satu)
git merge --squash feature/branch
git commit -m "Squash merge feature/branch"
```

---

## ⚔️ Resolve Merge Conflicts

### Langkah Resolve

1. **Cek file yang conflict**
   ```bash
   git status
   ```

2. **Edit file yang conflict**
   - File akan memiliki marker:
     ```
     <<<<<<< HEAD
     Kode dari branch saat ini
     =======
     Kode dari branch yang di-merge
     >>>>>>> feature/branch
     ```
   - Pilih kode yang diinginkan atau gabungkan

3. **Stage file yang sudah di-resolve**
   ```bash
   git add file.txt
   ```

4. **Complete merge**
   ```bash
   git commit -m "Merge: resolve conflicts"
   ```

### Abort Merge

```bash
# Batalkan merge yang sedang berlangsung
git merge --abort
```

---

## 🔄 Pull Request Workflow

### Workflow Singkat

```bash
# 1. Buat feature branch dari dev
git checkout dev
git pull origin dev
git checkout -b feature/nama-fitur

# 2. Develop dan commit
git add .
git commit -m "Add feature"
git push -u origin feature/nama-fitur

# 3. Buat Pull Request di GitHub
# - Base: dev, Compare: feature/nama-fitur

# 4. Setelah PR merged, update local
git checkout dev
git pull origin dev
git branch -d feature/nama-fitur
```

---

## 🛠️ Troubleshooting

### Error: "Push cannot contain secrets"
- Pastikan `env.example` sudah di-ignore
- Hapus secrets dari file yang akan di-commit

### Error: "Repository not found"
```bash
git remote -v  # Cek remote URL
git remote set-url origin https://github.com/username/repository.git
```

### Error: "Branch has no upstream branch"
```bash
git push -u origin branch-name
```

### Error: "Your branch is behind"
```bash
git pull origin branch-name
```

### File `.env` Ter-Commit
```bash
git rm --cached .env
echo ".env" >> .gitignore
git commit -m "Remove .env from repository"
git push
```
**PENTING**: Jika sudah ter-push, segera rotate semua API keys!

### Undo Last Commit (Belum Push)
```bash
git reset --soft HEAD~1  # Keep changes
git reset --hard HEAD~1  # Discard changes
```

### Stash Changes
```bash
git stash              # Simpan perubahan
git stash pop          # Apply stash
git stash list         # List stash
```

---

## 📝 Best Practices

### Commit Message
```bash
# Format: type(scope): description
git commit -m "feat(auth): add login functionality"
git commit -m "fix(api): resolve timeout issue"
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### Review Sebelum Push
```bash
git status        # Cek status
git diff          # Lihat perubahan
git diff --staged # Lihat perubahan yang di-stage
```

### Keep Branch Updated
```bash
# Update feature branch dari dev sebelum merge
git checkout feature/nama-fitur
git pull origin dev
git merge dev
git push
```

---

## ✅ Quick Reference

### Workflow Umum
```bash
# Update dari remote
git checkout dev
git pull origin dev

# Buat feature branch
git checkout -b feature/nama-fitur

# Develop dan commit
git add .
git commit -m "Add feature"
git push -u origin feature/nama-fitur

# Merge ke dev
git checkout dev
git pull origin dev
git merge feature/nama-fitur
git push origin dev
```

### Merge Workflow
```bash
# Merge feature ke dev
git checkout dev
git pull origin dev
git merge feature/nama-fitur
git push origin dev

# Merge dev ke main
git checkout main
git pull origin main
git merge dev
git push origin main
```

---

## 🔐 Security Notes

**PENTING**: 
- File `env.example` dan `env.dev.example` **TIDAK** di-upload ke GitHub
- File tetap ada di lokal dan bisa dibaca/diedit oleh agent
- Jangan commit file dengan API keys atau credentials

---

**Selamat!** Project Anda sudah ter-upload ke GitHub dengan aman. 🎉

*Update terakhir: 2024 - Versi ringkas dengan merge workflow*
