from config.database import db
from datetime import datetime
import enum

class DocumentStatus(enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    INACTIVE = "inactive"

class RemindExpDocs(db.Model):
    __tablename__ = "remind_exp_docs"
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    document_name = db.Column(db.String(255), nullable=False, comment="Nama dokumen/sertifikasi")
    document_number = db.Column(db.String(100), nullable=True, comment="Nomor dokumen")
    document_type = db.Column(db.String(100), nullable=True, comment="Jenis dokumen (Sertifikat, Izin, dll)")
    issuer = db.Column(db.String(255), nullable=True, comment="Penerbit dokumen")
    expiry_date = db.Column(db.Date, nullable=False, comment="Tanggal expired")
    reminder_days_before = db.Column(db.Integer, default=30, comment="Berapa hari sebelum expired untuk reminder")
    status = db.Column(db.Enum(DocumentStatus), default=DocumentStatus.ACTIVE, comment="Status dokumen")
    description = db.Column(db.Text, nullable=True, comment="Deskripsi tambahan")
    file_path = db.Column(db.String(500), nullable=True, comment="Path file dokumen jika ada")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment="Tanggal dibuat")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Tanggal diupdate")
    
    def __repr__(self):
        return f"<RemindExpDocs(id={self.id}, document_name='{self.document_name}', expiry_date='{self.expiry_date}')>"
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'document_name': self.document_name,
            'document_number': self.document_number,
            'document_type': self.document_type,
            'issuer': self.issuer,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'reminder_days_before': self.reminder_days_before,
            'status': self.status.value if self.status else None,
            'description': self.description,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
