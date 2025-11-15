from datetime import datetime
from config.database import db

class NotionDatabase(db.Model):
    """
    Model untuk menyimpan metadata database Notion yang terdeteksi
    """
    __tablename__ = 'notion_databases'
    
    id = db.Column(db.Integer, primary_key=True)
    database_id = db.Column(db.String(255), unique=True, nullable=False)
    database_title = db.Column(db.String(500), nullable=False)
    employee_name = db.Column(db.String(255), nullable=True)
    database_type = db.Column(db.String(100), nullable=True)
    is_task_database = db.Column(db.Boolean, default=False)
    is_employee_specific = db.Column(db.Boolean, default=False)
    structure_valid = db.Column(db.Boolean, default=False)
    confidence_score = db.Column(db.Float, default=0.0)
    missing_properties = db.Column(db.Text, nullable=True)  # JSON string
    sync_enabled = db.Column(db.Boolean, default=True)
    last_synced = db.Column(db.DateTime, nullable=True)
    # Property mapping metadata
    mapping_quality_score = db.Column(db.Float, default=0.0)
    mapped_properties_count = db.Column(db.Integer, default=0)
    last_mapping_analysis = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<NotionDatabase {self.database_title} ({self.employee_name})>'
    
    def to_dict(self):
        """
        Convert model ke dictionary
        """
        return {
            'id': self.id,
            'database_id': self.database_id,
            'database_title': self.database_title,
            'employee_name': self.employee_name,
            'database_type': self.database_type,
            'is_task_database': self.is_task_database,
            'is_employee_specific': self.is_employee_specific,
            'structure_valid': self.structure_valid,
            'confidence_score': self.confidence_score,
            'missing_properties': self.missing_properties,
            'sync_enabled': self.sync_enabled,
            'last_synced': self.last_synced.isoformat() if self.last_synced else None,
            'mapping_quality_score': self.mapping_quality_score,
            'mapped_properties_count': self.mapped_properties_count,
            'last_mapping_analysis': self.last_mapping_analysis.isoformat() if self.last_mapping_analysis else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def get_employee_databases(cls, employee_name: str = None):
        """
        Mendapatkan database untuk karyawan tertentu atau semua database karyawan
        """
        query = cls.query.filter(cls.is_employee_specific == True)
        
        if employee_name:
            query = query.filter(cls.employee_name == employee_name)
        
        return query.all()
    
    @classmethod
    def get_task_databases(cls):
        """
        Mendapatkan semua database task yang valid
        """
        return cls.query.filter(
            cls.is_task_database == True,
            cls.structure_valid == True,
            cls.sync_enabled == True
        ).all()
    
    @classmethod
    def get_by_database_id(cls, database_id: str):
        """
        Mendapatkan database berdasarkan ID Notion
        """
        return cls.query.filter(cls.database_id == database_id).first()
    
    @classmethod
    def update_sync_time(cls, database_id: str):
        """
        Update waktu sync terakhir
        """
        database = cls.get_by_database_id(database_id)
        if database:
            database.last_synced = datetime.utcnow()
            db.session.commit()
    
    @classmethod
    def get_sync_statistics(cls):
        """
        Mendapatkan statistik sync database
        """
        total_databases = cls.query.count()
        task_databases = cls.query.filter(cls.is_task_database == True).count()
        employee_databases = cls.query.filter(cls.is_employee_specific == True).count()
        valid_databases = cls.query.filter(cls.structure_valid == True).count()
        enabled_databases = cls.query.filter(cls.sync_enabled == True).count()
        
        return {
            'total_databases': total_databases,
            'task_databases': task_databases,
            'employee_databases': employee_databases,
            'valid_databases': valid_databases,
            'enabled_databases': enabled_databases
        }

