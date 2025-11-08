#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property Mapping Model - Model untuk menyimpan property mapping Notion database
"""

from datetime import datetime
from config.database import db
import json

class PropertyMapping(db.Model):
    """Model untuk menyimpan property mapping Notion database"""
    
    __tablename__ = 'property_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    database_id = db.Column(db.String(255), nullable=False, index=True)
    notion_property_name = db.Column(db.String(255), nullable=False)
    property_type = db.Column(db.String(50), nullable=False)
    mapped_field = db.Column(db.String(100), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False, default=0.0)
    alternative_names = db.Column(db.Text, nullable=True)  # JSON array
    is_required = db.Column(db.Boolean, nullable=False, default=False)
    validation_rules = db.Column(db.Text, nullable=True)  # JSON object
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('database_id', 'notion_property_name', name='uq_database_property'),
    )
    
    def __repr__(self):
        return f'<PropertyMapping {self.database_id}:{self.notion_property_name} -> {self.mapped_field}>'
    
    def to_dict(self):
        """Convert model ke dictionary"""
        return {
            'id': self.id,
            'database_id': self.database_id,
            'notion_property_name': self.notion_property_name,
            'property_type': self.property_type,
            'mapped_field': self.mapped_field,
            'confidence_score': self.confidence_score,
            'alternative_names': json.loads(self.alternative_names) if self.alternative_names else [],
            'is_required': self.is_required,
            'validation_rules': json.loads(self.validation_rules) if self.validation_rules else {},
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_or_update_mapping(cls, database_id: str, mapping_data: dict):
        """Create atau update property mapping"""
        try:
            existing_mapping = cls.query.filter_by(
                database_id=database_id,
                notion_property_name=mapping_data['notion_property_name']
            ).first()
            
            if existing_mapping:
                # Update existing mapping
                existing_mapping.property_type = mapping_data['property_type']
                existing_mapping.mapped_field = mapping_data['mapped_field']
                existing_mapping.confidence_score = mapping_data['confidence_score']
                existing_mapping.alternative_names = json.dumps(mapping_data.get('alternative_names', []))
                existing_mapping.is_required = mapping_data.get('is_required', False)
                existing_mapping.validation_rules = json.dumps(mapping_data.get('validation_rules', {}))
                existing_mapping.is_active = mapping_data.get('is_active', True)
                existing_mapping.updated_at = datetime.utcnow()
                
                db.session.commit()
                return existing_mapping
            else:
                # Create new mapping
                new_mapping = cls(
                    database_id=database_id,
                    notion_property_name=mapping_data['notion_property_name'],
                    property_type=mapping_data['property_type'],
                    mapped_field=mapping_data['mapped_field'],
                    confidence_score=mapping_data['confidence_score'],
                    alternative_names=json.dumps(mapping_data.get('alternative_names', [])),
                    is_required=mapping_data.get('is_required', False),
                    validation_rules=json.dumps(mapping_data.get('validation_rules', {})),
                    is_active=mapping_data.get('is_active', True)
                )
                
                db.session.add(new_mapping)
                db.session.commit()
                return new_mapping
                
        except Exception as e:
            db.session.rollback()
            raise e
    
    @classmethod
    def get_database_mappings(cls, database_id: str, active_only: bool = True):
        """Get semua mapping untuk database tertentu"""
        query = cls.query.filter_by(database_id=database_id)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.all()
    
    @classmethod
    def get_mapping_by_field(cls, database_id: str, mapped_field: str):
        """Get mapping berdasarkan mapped field"""
        return cls.query.filter_by(
            database_id=database_id,
            mapped_field=mapped_field,
            is_active=True
        ).first()
    
    @classmethod
    def delete_database_mappings(cls, database_id: str):
        """Delete semua mapping untuk database tertentu"""
        try:
            mappings = cls.query.filter_by(database_id=database_id).all()
            for mapping in mappings:
                db.session.delete(mapping)
            db.session.commit()
            return len(mappings)
        except Exception as e:
            db.session.rollback()
            raise e
    
    @classmethod
    def toggle_mapping_status(cls, mapping_id: int, is_active: bool):
        """Toggle status mapping (active/inactive)"""
        try:
            mapping = cls.query.get(mapping_id)
            if mapping:
                mapping.is_active = is_active
                mapping.updated_at = datetime.utcnow()
                db.session.commit()
                return mapping
            return None
        except Exception as e:
            db.session.rollback()
            raise e
    
    @classmethod
    def get_mapping_statistics(cls, database_id: str):
        """Get statistics mapping untuk database tertentu"""
        try:
            total_mappings = cls.query.filter_by(database_id=database_id).count()
            active_mappings = cls.query.filter_by(database_id=database_id, is_active=True).count()
            required_mappings = cls.query.filter_by(database_id=database_id, is_required=True, is_active=True).count()
            high_confidence_mappings = cls.query.filter(
                cls.database_id == database_id,
                cls.is_active == True,
                cls.confidence_score >= 0.8
            ).count()
            
            return {
                'total_mappings': total_mappings,
                'active_mappings': active_mappings,
                'required_mappings': required_mappings,
                'high_confidence_mappings': high_confidence_mappings,
                'mapping_quality_score': (high_confidence_mappings / active_mappings * 100) if active_mappings > 0 else 0
            }
        except Exception as e:
            return {
                'total_mappings': 0,
                'active_mappings': 0,
                'required_mappings': 0,
                'high_confidence_mappings': 0,
                'mapping_quality_score': 0
            }
    
    @classmethod
    def get_all_database_ids(cls):
        """Get semua database ID yang memiliki mapping"""
        return [row[0] for row in db.session.query(cls.database_id).distinct().all()]
