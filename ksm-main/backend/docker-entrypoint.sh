#!/bin/sh
set -e

echo "🔧 Starting KSM Backend (with DB migration)"

echo "🚀 Running RAG documents migration..."
python scripts/migrate_rag_documents.py || echo "⚠️ RAG migration warning (non-fatal)"

echo "🚀 Running Stok Barang migration..."
python scripts/migrate_stok_barang.py || echo "⚠️ Stok Barang migration warning (non-fatal)"

echo "🚀 Running Request Pembelian migration..."
python scripts/migrate_request_pembelian.py || echo "⚠️ Request Pembelian migration warning (non-fatal)"

echo "✅ Starting app"
exec python app.py


