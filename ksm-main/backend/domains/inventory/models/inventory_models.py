#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Models untuk Stok Barang - KSM Main Backend
Model untuk mengelola data barang, stok, supplier, dan transaksi barang
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import db


class KategoriBarang(db.Model):
    """Model untuk kategori barang"""
    __tablename__ = 'kategori_barang'
    
    id = Column(Integer, primary_key=True, index=True)
    nama_kategori = Column(String(100), nullable=False)
    kode_kategori = Column(String(10), nullable=False, unique=True)
    deskripsi = Column(Text)
    parent_id = Column(Integer, ForeignKey('kategori_barang.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    barangs = relationship("Barang", back_populates="kategori")
    parent = relationship("KategoriBarang", remote_side=[id])


class Supplier(db.Model):
    """Model untuk supplier/vendor"""
    __tablename__ = 'supplier'
    
    id = Column(Integer, primary_key=True, index=True)
    nama_supplier = Column(String(200), nullable=False)
    alamat = Column(Text)
    telepon = Column(String(20))
    email = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    barang_masuk = relationship("BarangMasuk", back_populates="supplier")


class Barang(db.Model):
    """Model untuk data barang"""
    __tablename__ = 'barang'
    
    id = Column(Integer, primary_key=True, index=True)
    kode_barang = Column(String(20), nullable=False, unique=True)
    nama_barang = Column(String(200), nullable=False)
    deskripsi = Column(Text)
    kategori_id = Column(Integer, ForeignKey('kategori_barang.id'), nullable=False)
    satuan = Column(String(20), nullable=False, default='PCS')
    harga_per_unit = Column(Numeric(15, 2))
    merk = Column(String(100), nullable=True)  # Field merk (optional)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    kategori = relationship("KategoriBarang", back_populates="barangs")
    stok = relationship("StokBarang", back_populates="barang", uselist=False)
    barang_masuk = relationship("BarangMasuk", back_populates="barang")
    barang_keluar = relationship("BarangKeluar", back_populates="barang")


class StokBarang(db.Model):
    """Model untuk stok barang"""
    __tablename__ = 'stok_barang'
    
    id = Column(Integer, primary_key=True, index=True)
    barang_id = Column(Integer, ForeignKey('barang.id'), nullable=False, unique=True)
    jumlah_stok = Column(Integer, nullable=False, default=0)
    stok_minimum = Column(Integer, nullable=False, default=0)
    stok_maksimum = Column(Integer)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship
    barang = relationship("Barang", back_populates="stok")


class BarangMasuk(db.Model):
    """Model untuk transaksi barang masuk"""
    __tablename__ = 'barang_masuk'
    
    id = Column(Integer, primary_key=True, index=True)
    barang_id = Column(Integer, ForeignKey('barang.id'), nullable=False)
    supplier_id = Column(Integer, ForeignKey('supplier.id'))
    jumlah_masuk = Column(Integer, nullable=False)
    harga_per_unit = Column(Numeric(15, 2))
    tanggal_masuk = Column(DateTime(timezone=True), server_default=func.now())
    nomor_surat_jalan = Column(String(50))
    keterangan = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    barang = relationship("Barang", back_populates="barang_masuk")
    supplier = relationship("Supplier", back_populates="barang_masuk")


class BarangKeluar(db.Model):
    """Model untuk transaksi barang keluar"""
    __tablename__ = 'barang_keluar'
    
    id = Column(Integer, primary_key=True, index=True)
    barang_id = Column(Integer, ForeignKey('barang.id'), nullable=False)
    departemen_id = Column(Integer)
    jumlah_keluar = Column(Integer, nullable=False)
    tanggal_keluar = Column(DateTime(timezone=True), server_default=func.now())
    nomor_permintaan = Column(String(50))
    keterangan = Column(Text)
    status_approval = Column(String(20), default='PENDING')
    approved_by = Column(String(100))
    approved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    barang = relationship("Barang", back_populates="barang_keluar")