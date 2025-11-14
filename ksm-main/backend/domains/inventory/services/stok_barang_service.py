#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service untuk Stok Barang - KSM Main Backend
Service untuk mengelola logika bisnis stok barang
"""

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from domains.inventory.models.inventory_models import (
    Barang, KategoriBarang, Supplier, StokBarang, 
    BarangMasuk, BarangKeluar
)


class StokBarangService:
    def __init__(self, db_session):
        self.db = db_session

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Mengambil data untuk dashboard stok barang"""
        try:
            # Total barang
            total_barang = self.db.query(Barang).count()
            
            # Total kategori
            total_kategori = self.db.query(KategoriBarang).count()
            
            # Barang masuk hari ini
            today = datetime.now().date()
            barang_masuk_hari_ini = self.db.query(BarangMasuk).filter(
                func.date(BarangMasuk.tanggal_masuk) == today
            ).count()
            
            # Barang keluar hari ini
            barang_keluar_hari_ini = self.db.query(BarangKeluar).filter(
                func.date(BarangKeluar.tanggal_keluar) == today
            ).count()
            
            # Total nilai stok
            total_nilai_stok = self.db.query(
                func.sum(StokBarang.jumlah_stok * Barang.harga_per_unit)
            ).join(Barang).scalar() or 0
            
            # Stok menipis (stok <= stok_minimum dan > 0)
            stok_menipis = self.db.query(StokBarang).join(Barang).filter(
                and_(
                    StokBarang.jumlah_stok <= StokBarang.stok_minimum,
                    StokBarang.jumlah_stok > 0
                )
            ).options(joinedload(StokBarang.barang)).all()
            
            # Stok habis (stok = 0)
            stok_habis = self.db.query(StokBarang).join(Barang).filter(
                StokBarang.jumlah_stok == 0
            ).options(joinedload(StokBarang.barang)).all()
            
            return {
                "total_barang": total_barang,
                "total_kategori": total_kategori,
                "barang_masuk_hari_ini": barang_masuk_hari_ini,
                "barang_keluar_hari_ini": barang_keluar_hari_ini,
                "total_nilai_stok": float(total_nilai_stok),
                "stok_menipis": [
                    {
                        "id": item.id,
                        "jumlah_stok": item.jumlah_stok,
                        "stok_minimum": item.stok_minimum,
                        "barang": {
                            "id": item.barang.id,
                            "nama_barang": item.barang.nama_barang,
                            "satuan": item.barang.satuan
                        }
                    } for item in stok_menipis
                ],
                "stok_habis": [
                    {
                        "id": item.id,
                        "jumlah_stok": item.jumlah_stok,
                        "barang": {
                            "id": item.barang.id,
                            "nama_barang": item.barang.nama_barang,
                            "satuan": item.barang.satuan
                        }
                    } for item in stok_habis
                ]
            }
        except Exception as e:
            raise Exception(f"Error mengambil data dashboard: {str(e)}")

    def get_all_barang(self, page: int = 1, per_page: int = 10, search: str = None, 
                       kategori_id: int = None, stok_min: int = None, stok_max: int = None,
                       harga_min: float = None, harga_max: float = None,
                       sort_by: str = 'nama_barang', sort_order: str = 'asc') -> Dict[str, Any]:
        """Mengambil daftar barang dengan pagination, filter, dan search"""
        try:
            # Base query dengan join
            query = self.db.query(Barang).options(
                joinedload(Barang.kategori),
                joinedload(Barang.stok)
            )
            
            # Apply filters
            if search:
                search_filter = or_(
                    Barang.kode_barang.ilike(f'%{search}%'),
                    Barang.nama_barang.ilike(f'%{search}%'),
                    Barang.deskripsi.ilike(f'%{search}%'),
                    Barang.merk.ilike(f'%{search}%'),  # Include merk in search
                    KategoriBarang.nama_kategori.ilike(f'%{search}%')
                )
                query = query.join(KategoriBarang).filter(search_filter)
            else:
                query = query.join(KategoriBarang)
            
            if kategori_id:
                query = query.filter(Barang.kategori_id == kategori_id)
            
            # Filter by stock range
            if stok_min is not None or stok_max is not None:
                query = query.join(StokBarang)
                if stok_min is not None:
                    query = query.filter(StokBarang.jumlah_stok >= stok_min)
                if stok_max is not None:
                    query = query.filter(StokBarang.jumlah_stok <= stok_max)
            
            # Filter by price range
            if harga_min is not None:
                query = query.filter(Barang.harga_per_unit >= harga_min)
            if harga_max is not None:
                query = query.filter(Barang.harga_per_unit <= harga_max)
            
            # Apply sorting
            sort_column = getattr(Barang, sort_by, Barang.nama_barang)
            if sort_by == 'stok':
                sort_column = StokBarang.jumlah_stok
                query = query.join(StokBarang)
            elif sort_by == 'kategori':
                sort_column = KategoriBarang.nama_kategori
                query = query.join(KategoriBarang)
            elif sort_by == 'merk':
                sort_column = Barang.merk
            
            if sort_order.lower() == 'desc':
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
            
            total = query.count()
            items = query.offset((page - 1) * per_page).limit(per_page).all()
            
            return {
                "items": [
                    {
                        "id": item.id,
                        "kode_barang": item.kode_barang,
                        "nama_barang": item.nama_barang,
                        "deskripsi": item.deskripsi,
                        "satuan": item.satuan,
                        "merk": item.merk,
                        "harga_per_unit": float(item.harga_per_unit) if item.harga_per_unit else 0,
                        "kategori": {
                            "id": item.kategori.id,
                            "nama_kategori": item.kategori.nama_kategori
                        } if item.kategori else None,
                        "stok": {
                            "jumlah_stok": item.stok.jumlah_stok if item.stok else 0,
                            "stok_minimum": item.stok.stok_minimum if item.stok else 0,
                            "stok_maksimum": item.stok.stok_maksimum if item.stok else 0
                        } if item.stok else {"jumlah_stok": 0, "stok_minimum": 0, "stok_maksimum": 0}
                    } for item in items
                ],
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            }
        except Exception as e:
            raise Exception(f"Error mengambil daftar barang: {str(e)}")

    def get_barang_by_id(self, barang_id: int) -> Optional[Dict[str, Any]]:
        """Mengambil detail barang berdasarkan ID"""
        try:
            item = self.db.query(Barang).filter(
                Barang.id == barang_id
            ).options(
                joinedload(Barang.kategori),
                joinedload(Barang.stok)
            ).first()
            
            if not item:
                return None
                
            return {
                "id": item.id,
                "kode_barang": item.kode_barang,
                "nama_barang": item.nama_barang,
                "deskripsi": item.deskripsi,
                "satuan": item.satuan,
                "merk": item.merk,
                "harga_per_unit": float(item.harga_per_unit) if item.harga_per_unit else 0,
                "kategori": {
                    "id": item.kategori.id,
                    "nama_kategori": item.kategori.nama_kategori
                } if item.kategori else None,
                "stok": {
                    "jumlah_stok": item.stok.jumlah_stok if item.stok else 0,
                    "stok_minimum": item.stok.stok_minimum if item.stok else 0,
                    "stok_maksimum": item.stok.stok_maksimum if item.stok else 0
                } if item.stok else {"jumlah_stok": 0, "stok_minimum": 0, "stok_maksimum": 0}
            }
        except Exception as e:
            raise Exception(f"Error mengambil detail barang: {str(e)}")

    def get_barang_by_code(self, kode_barang: str) -> Optional[Dict[str, Any]]:
        """Mengambil detail barang berdasarkan kode barang"""
        try:
            item = self.db.query(Barang).filter(
                Barang.kode_barang == kode_barang
            ).options(
                joinedload(Barang.kategori),
                joinedload(Barang.stok)
            ).first()
            
            if not item:
                return None
                
            return {
                "id": item.id,
                "kode_barang": item.kode_barang,
                "nama_barang": item.nama_barang,
                "deskripsi": item.deskripsi,
                "satuan": item.satuan,
                "harga_per_unit": float(item.harga_per_unit) if item.harga_per_unit else 0,
                "merk": item.merk,
                "kategori": {
                    "id": item.kategori.id,
                    "nama_kategori": item.kategori.nama_kategori
                } if item.kategori else None,
                "stok": {
                    "jumlah_stok": item.stok.jumlah_stok if item.stok else 0,
                    "stok_minimum": item.stok.stok_minimum if item.stok else 0,
                    "stok_maksimum": item.stok.stok_maksimum if item.stok else 0
                } if item.stok else {"jumlah_stok": 0, "stok_minimum": 0, "stok_maksimum": 0}
            }
        except Exception as e:
            raise Exception(f"Error mengambil detail barang: {str(e)}")

    def create_barang(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Membuat barang baru"""
        try:
            # Cek apakah kode barang sudah ada
            existing = self.db.query(Barang).filter(Barang.kode_barang == data['kode_barang']).first()
            if existing:
                raise Exception("Kode barang sudah ada")
            
            barang = Barang(
                kode_barang=data['kode_barang'],
                nama_barang=data['nama_barang'],
                deskripsi=data.get('deskripsi'),
                kategori_id=data.get('kategori_id'),
                satuan=data['satuan'],
                harga_per_unit=data.get('harga_per_unit', 0),
                merk=data.get('merk')  # Field merk (optional)
            )
            
            self.db.add(barang)
            self.db.flush()  # Untuk mendapatkan ID
            
            # Buat stok awal
            stok = StokBarang(
                barang_id=barang.id,
                jumlah_stok=data.get('jumlah_stok_awal', 0),
                stok_minimum=data.get('stok_minimum', 0),
                stok_maksimum=data.get('stok_maksimum', 0)
            )
            
            self.db.add(stok)
            self.db.commit()
            
            return self.get_barang_by_id(barang.id)
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error membuat barang: {str(e)}")

    def update_barang(self, barang_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update data barang"""
        try:
            barang = self.db.query(Barang).filter(
                Barang.id == barang_id
            ).first()
            
            if not barang:
                raise Exception("Barang tidak ditemukan")
            
            # Update data barang
            for key, value in data.items():
                if hasattr(barang, key) and key != 'id':
                    setattr(barang, key, value)
            
            # Update stok jika ada
            if 'stok' in data:
                stok = self.db.query(StokBarang).filter(StokBarang.barang_id == barang_id).first()
                if stok:
                    for key, value in data['stok'].items():
                        if hasattr(stok, key):
                            setattr(stok, key, value)
            
            self.db.commit()
            return self.get_barang_by_id(barang_id)
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error update barang: {str(e)}")

    def delete_barang(self, barang_id: int) -> bool:
        """Hard delete barang"""
        try:
            barang = self.db.query(Barang).filter(
                Barang.id == barang_id
            ).first()
            
            if not barang:
                raise Exception("Barang tidak ditemukan")
            
            # Hapus stok terlebih dahulu
            stok = self.db.query(StokBarang).filter(StokBarang.barang_id == barang_id).first()
            if stok:
                self.db.delete(stok)
            
            # Hapus barang
            self.db.delete(barang)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error menghapus barang: {str(e)}")

    def get_kategori_list(self) -> List[Dict[str, Any]]:
        """Mengambil daftar kategori barang"""
        try:
            kategoris = self.db.query(KategoriBarang).all()
            return [
                {
                    "id": item.id,
                    "nama_kategori": item.nama_kategori,
                    "kode_kategori": item.kode_kategori,
                    "deskripsi": item.deskripsi,
                    "parent_id": item.parent_id,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None
                } for item in kategoris
            ]
        except Exception as e:
            raise Exception(f"Error mengambil daftar kategori: {str(e)}")

    def get_merk_list(self) -> List[str]:
        """Mengambil daftar merk yang ada (unik)"""
        try:
            # Query untuk mendapatkan merk yang tidak null dan tidak kosong
            merks = self.db.query(Barang.merk).filter(
                Barang.merk.isnot(None),
                Barang.merk != '',
                Barang.merk != 'null'  # Filter out 'null' strings
            ).distinct().all()
            
            # Extract merk values and filter out None/empty values
            merk_list = []
            for merk_tuple in merks:
                if merk_tuple and merk_tuple[0] and merk_tuple[0].strip():
                    merk_list.append(merk_tuple[0].strip())
            
            return merk_list
        except Exception as e:
            print(f"Error in get_merk_list: {str(e)}")
            # Return empty list instead of raising exception to prevent 500 error
            return []

    def get_supplier_list(self) -> List[Dict[str, Any]]:
        """Mengambil daftar supplier"""
        try:
            suppliers = self.db.query(Supplier).all()
            return [
                {
                    "id": item.id,
                    "nama_supplier": item.nama_supplier,
                    "alamat": item.alamat,
                    "telepon": item.telepon,
                    "email": item.email
                } for item in suppliers
            ]
        except Exception as e:
            raise Exception(f"Error mengambil daftar supplier: {str(e)}")

    def get_barang_masuk_list(self) -> List[Dict[str, Any]]:
        """Mengambil daftar barang masuk"""
        try:
            barang_masuk_list = self.db.query(BarangMasuk).options(
                joinedload(BarangMasuk.barang).joinedload(Barang.kategori),
                joinedload(BarangMasuk.supplier)
            ).order_by(BarangMasuk.tanggal_masuk.desc()).all()
            
            return [
                {
                    "id": item.id,
                    "barang_id": item.barang_id,
                    "supplier_id": item.supplier_id,
                    "jumlah_masuk": item.jumlah_masuk,
                    "harga_per_unit": float(item.harga_per_unit) if item.harga_per_unit else None,
                    "tanggal_masuk": item.tanggal_masuk.isoformat() if item.tanggal_masuk else None,
                    "nomor_surat_jalan": item.nomor_surat_jalan,
                    "keterangan": item.keterangan,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "barang": {
                        "id": item.barang.id,
                        "kode_barang": item.barang.kode_barang,
                        "nama_barang": item.barang.nama_barang,
                        "satuan": item.barang.satuan,
                        "kategori": {
                            "id": item.barang.kategori.id if item.barang.kategori else None,
                            "nama_kategori": item.barang.kategori.nama_kategori if item.barang.kategori else None
                        } if item.barang.kategori else None
                    } if item.barang else None,
                    "supplier": {
                        "id": item.supplier.id,
                        "nama_supplier": item.supplier.nama_supplier
                    } if item.supplier else None,
                    "total_harga": float(item.jumlah_masuk * item.harga_per_unit) if item.harga_per_unit else None
                } for item in barang_masuk_list
            ]
        except Exception as e:
            raise Exception(f"Error mengambil daftar barang masuk: {str(e)}")

    def create_barang_masuk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Membuat transaksi barang masuk baru"""
        try:
            # Validasi barang_id
            barang = self.db.query(Barang).filter(Barang.id == data['barang_id']).first()
            if not barang:
                raise Exception("Barang tidak ditemukan")
            
            # Validasi supplier_id jika ada
            if data.get('supplier_id'):
                supplier = self.db.query(Supplier).filter(Supplier.id == data['supplier_id']).first()
                if not supplier:
                    raise Exception("Supplier tidak ditemukan")
            
            # Parse tanggal_masuk
            tanggal_masuk = None
            if data.get('tanggal_masuk'):
                if isinstance(data['tanggal_masuk'], str):
                    try:
                        # Handle format YYYY-MM-DD
                        if len(data['tanggal_masuk']) == 10:
                            tanggal_masuk = datetime.strptime(data['tanggal_masuk'], '%Y-%m-%d')
                        else:
                            # Handle ISO format
                            tanggal_masuk_str = data['tanggal_masuk'].replace('Z', '+00:00')
                            tanggal_masuk = datetime.fromisoformat(tanggal_masuk_str)
                    except Exception:
                        tanggal_masuk = None
                else:
                    tanggal_masuk = data['tanggal_masuk']
            
            # Buat transaksi barang masuk
            barang_masuk = BarangMasuk(
                barang_id=data['barang_id'],
                supplier_id=data.get('supplier_id'),
                jumlah_masuk=data['jumlah_masuk'],
                harga_per_unit=data.get('harga_per_unit'),
                tanggal_masuk=tanggal_masuk,
                nomor_surat_jalan=data.get('nomor_surat_jalan'),
                keterangan=data.get('keterangan')
            )
            
            self.db.add(barang_masuk)
            self.db.flush()
            
            # Update stok barang
            stok = self.db.query(StokBarang).filter(StokBarang.barang_id == data['barang_id']).first()
            if stok:
                stok.jumlah_stok += data['jumlah_masuk']
            else:
                # Buat stok baru jika belum ada
                stok = StokBarang(
                    barang_id=data['barang_id'],
                    jumlah_stok=data['jumlah_masuk'],
                    stok_minimum=0,
                    stok_maksimum=0
                )
                self.db.add(stok)
            
            self.db.commit()
            
            # Ambil data barang masuk yang baru dibuat dengan relasi
            barang_masuk_result = self.db.query(BarangMasuk).options(
                joinedload(BarangMasuk.barang).joinedload(Barang.kategori),
                joinedload(BarangMasuk.supplier)
            ).filter(BarangMasuk.id == barang_masuk.id).first()
            
            return {
                "id": barang_masuk_result.id,
                "barang_id": barang_masuk_result.barang_id,
                "supplier_id": barang_masuk_result.supplier_id,
                "jumlah_masuk": barang_masuk_result.jumlah_masuk,
                "harga_per_unit": float(barang_masuk_result.harga_per_unit) if barang_masuk_result.harga_per_unit else None,
                "tanggal_masuk": barang_masuk_result.tanggal_masuk.isoformat() if barang_masuk_result.tanggal_masuk else None,
                "nomor_surat_jalan": barang_masuk_result.nomor_surat_jalan,
                "keterangan": barang_masuk_result.keterangan,
                "created_at": barang_masuk_result.created_at.isoformat() if barang_masuk_result.created_at else None,
                "barang": {
                    "id": barang_masuk_result.barang.id,
                    "kode_barang": barang_masuk_result.barang.kode_barang,
                    "nama_barang": barang_masuk_result.barang.nama_barang,
                    "satuan": barang_masuk_result.barang.satuan
                } if barang_masuk_result.barang else None,
                "supplier": {
                    "id": barang_masuk_result.supplier.id,
                    "nama_supplier": barang_masuk_result.supplier.nama_supplier
                } if barang_masuk_result.supplier else None
            }
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error membuat barang masuk: {str(e)}")