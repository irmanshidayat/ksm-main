# 🚀 Docker Build Optimization - Solusi Alternatif

Dokumen ini menjelaskan berbagai solusi alternatif untuk mengoptimalkan proses build Docker yang lambat atau timeout.

## 📋 Masalah yang Sering Terjadi

1. **Build timeout** - apt-get update sangat lambat
2. **Network issues** - Koneksi ke Docker registry lambat
3. **Build terlalu lama** - `--no-cache` membuat build sangat lambat
4. **Resource constraints** - Server tidak memiliki cukup resource

## ✅ Solusi Alternatif 

### Solusi 1: Build dengan Cache (Paling Cepat)

**Keuntungan:**
- ⚡ Sangat cepat - hanya rebuild layer yang berubah
- 💾 Menghemat bandwidth
- 🔄 Build incremental

**Cara menggunakan:**

Edit `.github/workflows/deploy-dev.yml` baris 242-247, uncomment:

```bash
# Build dengan cache (lebih cepat)
docker-compose -f docker-compose.yml build || {
  echo "❌ Build failed! Showing logs..."
  docker-compose -f docker-compose.yml logs --tail=50
  exit 1
}
```

Dan comment solusi 2 (baris 249-287).

**Kapan menggunakan:**
- ✅ Untuk development yang sering deploy
- ✅ Ketika tidak ada perubahan besar di dependencies
- ✅ Ketika ingin build cepat

---

### Solusi 2: Build dengan Retry & Timeout (Sudah Diimplementasi)

**Keuntungan:**
- 🔄 Auto-retry jika build gagal
- ⏱️ Timeout protection (30 menit)
- 📊 Build parallel untuk mempercepat
- 📝 Logging yang lebih baik

**Fitur:**
- Retry otomatis hingga 3 kali
- Timeout 30 menit per build
- Build parallel dengan `--parallel`
- Progress logging ke file

**Kapan menggunakan:**
- ✅ Ketika network tidak stabil
- ✅ Ketika build sering timeout
- ✅ Untuk production deployment

---

### Solusi 3: Conditional Build (Hanya Build yang Berubah)

**Keuntungan:**
- 🎯 Hanya build service yang berubah
- ⚡ Lebih cepat
- 💰 Menghemat resource

**Cara menggunakan:**

Tambahkan script ini sebelum build:

```bash
# Deteksi perubahan
CHANGED_SERVICES=""

if git diff --name-only HEAD~1 HEAD | grep -q "backend/"; then
  CHANGED_SERVICES="$CHANGED_SERVICES ksm-backend-dev"
fi

if git diff --name-only HEAD~1 HEAD | grep -q "frontend-vite/"; then
  CHANGED_SERVICES="$CHANGED_SERVICES ksm-frontend-vite-dev"
fi

if git diff --name-only HEAD~1 HEAD | grep -q "Agent AI/"; then
  CHANGED_SERVICES="$CHANGED_SERVICES agent-ai-dev"
fi

# Build hanya service yang berubah
if [ -n "$CHANGED_SERVICES" ]; then
  echo "🔨 Building changed services: $CHANGED_SERVICES"
  docker-compose -f docker-compose.yml build $CHANGED_SERVICES
else
  echo "✅ No changes detected, skipping build"
fi
```

**Kapan menggunakan:**
- ✅ Ketika hanya 1-2 service yang berubah
- ✅ Untuk optimasi resource
- ✅ Ketika ingin deploy cepat

---

### Solusi 4: Build dengan Docker Buildx (Advanced)

**Keuntungan:**
- 🚀 Build lebih cepat dengan cache mounts
- 🔄 Multi-stage build optimization
- 💾 Better cache management

**Cara menggunakan:**

```bash
# Setup buildx
docker buildx create --use --name multiarch || docker buildx use multiarch

# Build dengan cache mounts
DOCKER_BUILDKIT=1 docker buildx build \
  --cache-from type=local,src=/tmp/.buildx-cache \
  --cache-to type=local,dest=/tmp/.buildx-cache \
  --load \
  -f backend/Dockerfile.production \
  -t ksm-backend-dev \
  ./backend
```

**Kapan menggunakan:**
- ✅ Untuk build yang sangat kompleks
- ✅ Ketika ingin optimasi maksimal
- ✅ Untuk CI/CD yang advanced

---

### Solusi 5: Pre-built Images (Paling Cepat)

**Keuntungan:**
- ⚡ Sangat cepat - tidak perlu build
- 💾 Menghemat resource server
- 🔄 Consistent builds

**Cara menggunakan:**

1. Build images di CI/CD (GitHub Actions)
2. Push ke Docker Registry (Docker Hub/GitHub Container Registry)
3. Pull images di server

**Workflow:**

```yaml
# Di GitHub Actions
- name: Build and push images
  run: |
    docker build -t ghcr.io/username/ksm-backend:dev ./backend
    docker push ghcr.io/username/ksm-backend:dev

# Di server deployment
- name: Pull images
  run: |
    docker pull ghcr.io/username/ksm-backend:dev
    docker-compose -f docker-compose.yml pull
```

**Kapan menggunakan:**
- ✅ Untuk production
- ✅ Ketika build time sangat penting
- ✅ Ketika server resource terbatas

---

### Solusi 6: Optimasi apt-get dengan Mirror

**Keuntungan:**
- 🌐 Menggunakan mirror lokal yang lebih cepat
- ⚡ apt-get update lebih cepat
- 🔄 Retry dengan mirror backup

**Cara menggunakan:**

Edit Dockerfile, tambahkan sebelum `apt-get update`:

```dockerfile
# Gunakan mirror yang lebih cepat
RUN echo "deb http://mirror.rackspace.com/debian/ trixie main" > /etc/apt/sources.list.d/rackspace.list || true
RUN echo "deb http://deb.debian.org/debian/ trixie main" >> /etc/apt/sources.list.d/debian.list || true
```

Atau gunakan script dengan retry:

```dockerfile
RUN set -e; \
    MAX_ATTEMPTS=5; \
    APT_TIMEOUT=180; \
    for i in $(seq 1 $MAX_ATTEMPTS); do \
        echo "Attempt $i/$MAX_ATTEMPTS: Updating package lists..."; \
        if timeout ${APT_TIMEOUT} apt-get update \
            -o Acquire::http::Timeout=${APT_TIMEOUT} \
            -o Acquire::Retries=3 \
            -o Acquire::http::No-Cache=True; then \
            echo "✅ Package lists updated successfully"; \
            break; \
        else \
            if [ $i -eq $MAX_ATTEMPTS ]; then \
                echo "❌ All attempts failed"; \
                exit 1; \
            fi; \
            echo "⚠️  Attempt $i failed, retrying..."; \
            sleep $((i * 10)); \
        fi; \
    done
```

---

### Solusi 7: Build Incremental (Layer by Layer)

**Keuntungan:**
- 🎯 Build hanya layer yang berubah
- ⚡ Lebih cepat dari full rebuild
- 💾 Efficient cache usage

**Cara menggunakan:**

```bash
# Build dengan cache
docker-compose -f docker-compose.yml build

# Atau build specific service
docker-compose -f docker-compose.yml build ksm-backend-dev
```

**Kapan menggunakan:**
- ✅ Ketika hanya beberapa file yang berubah
- ✅ Untuk development yang iteratif
- ✅ Ketika ingin balance antara speed dan freshness

---

## 🎯 Rekomendasi Berdasarkan Skenario

### Development (Sering Deploy)
1. **Solusi 1** (Build dengan Cache) - Paling cepat
2. **Solusi 3** (Conditional Build) - Hanya build yang berubah
3. **Solusi 7** (Build Incremental) - Balance

### Production (Stabil & Reliable)
1. **Solusi 2** (Retry & Timeout) - Sudah diimplementasi
2. **Solusi 5** (Pre-built Images) - Paling reliable
3. **Solusi 4** (Buildx) - Advanced optimization

### Network Issues
1. **Solusi 2** (Retry & Timeout) - Auto-retry
2. **Solusi 6** (apt-get Mirror) - Mirror lokal
3. **Solusi 5** (Pre-built Images) - Skip build

### Resource Constraints
1. **Solusi 3** (Conditional Build) - Hanya build yang perlu
2. **Solusi 5** (Pre-built Images) - No build di server
3. **Solusi 1** (Build dengan Cache) - Efficient

---

## 🔧 Implementasi Cepat

### Untuk Development (Build dengan Cache)

Edit `.github/workflows/deploy-dev.yml`:

```yaml
# Ganti baris 241-287 dengan:
echo "🔨 Building Docker images with cache..."
docker-compose -f docker-compose.yml build || {
  echo "❌ Build failed! Retrying without cache..."
  docker-compose -f docker-compose.yml build --no-cache || {
    echo "❌ Build failed after retry!"
    exit 1
  }
}
```

### Untuk Production (Pre-built Images)

1. Setup GitHub Container Registry di GitHub Actions
2. Build dan push images di CI
3. Pull images di deployment script

---

## 📊 Perbandingan Solusi

| Solusi | Speed | Reliability | Complexity | Resource Usage |
|--------|-------|-------------|------------|----------------|
| Build dengan Cache | ⚡⚡⚡ | ⭐⭐⭐ | ⭐ | 💾💾 |
| Retry & Timeout | ⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐ | 💾💾💾 |
| Conditional Build | ⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐ | 💾 |
| Buildx | ⚡⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 💾💾 |
| Pre-built Images | ⚡⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐ | 💾 |
| apt-get Mirror | ⚡⚡ | ⭐⭐⭐ | ⭐ | 💾💾 |
| Build Incremental | ⚡⚡⚡ | ⭐⭐⭐ | ⭐ | 💾💾 |

---

## 🚨 Troubleshooting

### Build Timeout
- ✅ Gunakan **Solusi 2** (Retry & Timeout)
- ✅ Atau **Solusi 6** (apt-get Mirror)

### Build Sangat Lambat
- ✅ Gunakan **Solusi 1** (Build dengan Cache)
- ✅ Atau **Solusi 3** (Conditional Build)

### Network Issues
- ✅ Gunakan **Solusi 2** (Retry & Timeout)
- ✅ Atau **Solusi 5** (Pre-built Images)

### Resource Exhausted
- ✅ Gunakan **Solusi 3** (Conditional Build)
- ✅ Atau **Solusi 5** (Pre-built Images)

---

## 📝 Catatan Penting

1. **Build dengan Cache** tidak selalu fresh - gunakan `--no-cache` jika perlu
2. **Pre-built Images** memerlukan setup registry
3. **Conditional Build** memerlukan git history
4. **Buildx** memerlukan Docker BuildKit

---

## 🔄 Migrasi ke Solusi Lain

Untuk beralih ke solusi lain, edit `.github/workflows/deploy-dev.yml` bagian build (baris 239-287) dan ganti dengan solusi yang diinginkan sesuai dokumentasi di atas.

