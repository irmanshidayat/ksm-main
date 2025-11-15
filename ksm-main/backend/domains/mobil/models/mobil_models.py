#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mobil Models untuk KSM Main Backend
Models untuk sistem request penggunaan mobil
"""

from sqlalchemy import Column, Integer, String, Date, Boolean, Text, ForeignKey, DateTime, Enum, JSON, Time
from sqlalchemy.orm import relationship
from config.database import db
from datetime import datetime
import enum

class MobilStatus(enum.Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"

class RequestStatus(enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class RecurringPattern(enum.Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class WaitingListStatus(enum.Enum):
    WAITING = "waiting"
    NOTIFIED = "notified"
    EXPIRED = "expired"

class Mobil(db.Model):
    __tablename__ = 'mobil'
    
    id = Column(Integer, primary_key=True)
    nama = Column(String(50), nullable=False)
    plat_nomor = Column(String(20), unique=True, nullable=False)
    status = Column(Enum(MobilStatus), default=MobilStatus.ACTIVE)
    is_backup = Column(Boolean, default=False)
    backup_for_mobil_id = Column(Integer, ForeignKey('mobil.id'), nullable=True)
    priority_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    backup_for = relationship("Mobil", remote_side=[id])
    requests = relationship("MobilRequest", back_populates="mobil", foreign_keys="MobilRequest.mobil_id")
    waiting_lists = relationship("WaitingList", back_populates="mobil")

class MobilRequest(db.Model):
    __tablename__ = 'mobil_request'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    mobil_id = Column(Integer, ForeignKey('mobil.id'), nullable=False)
    tanggal_mulai = Column(Date, nullable=False)
    tanggal_selesai = Column(Date, nullable=False)
    jam_mulai = Column(Time, default='08:00:00')
    jam_selesai = Column(Time, default='17:00:00')
    keperluan = Column(Text)
    status = Column(Enum(RequestStatus), default=RequestStatus.ACTIVE)
    is_recurring = Column(Boolean, default=False)
    recurring_pattern = Column(Enum(RecurringPattern), nullable=True)
    recurring_end_date = Column(Date, nullable=True)
    parent_request_id = Column(Integer, ForeignKey('mobil_request.id'), nullable=True)
    is_backup_mobil = Column(Boolean, default=False)
    original_mobil_id = Column(Integer, ForeignKey('mobil.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # user = relationship("User", back_populates="mobil_requests")
    mobil = relationship("Mobil", back_populates="requests", foreign_keys=[mobil_id])
    parent_request = relationship("MobilRequest", remote_side=[id])
    original_mobil = relationship("Mobil", foreign_keys=[original_mobil_id])

class WaitingList(db.Model):
    __tablename__ = 'waiting_list'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    mobil_id = Column(Integer, ForeignKey('mobil.id'), nullable=False)
    tanggal_mulai = Column(Date, nullable=False)
    tanggal_selesai = Column(Date, nullable=False)
    priority = Column(Integer, default=0)
    status = Column(Enum(WaitingListStatus), default=WaitingListStatus.WAITING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # user = relationship("User", back_populates="waiting_lists")
    mobil = relationship("Mobil", back_populates="waiting_lists")

class MobilBackup(db.Model):
    __tablename__ = 'mobil_backup'
    
    id = Column(Integer, primary_key=True)
    mobil_utama_id = Column(Integer, ForeignKey('mobil.id'), nullable=False)
    mobil_backup_id = Column(Integer, ForeignKey('mobil.id'), nullable=False)
    priority = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    mobil_utama = relationship("Mobil", foreign_keys=[mobil_utama_id])
    mobil_backup = relationship("Mobil", foreign_keys=[mobil_backup_id])

class MobilUsageLog(db.Model):
    __tablename__ = 'mobil_usage_log'
    
    id = Column(Integer, primary_key=True)
    mobil_id = Column(Integer, ForeignKey('mobil.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    request_id = Column(Integer, ForeignKey('mobil_request.id'), nullable=True)
    action = Column(String(50), nullable=False)  # 'request', 'cancel', 'complete'
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    mobil = relationship("Mobil")
    # user = relationship("User")
    request = relationship("MobilRequest")

