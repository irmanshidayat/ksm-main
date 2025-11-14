#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Notion Service - Konsolidasi semua service Notion
Menggabungkan DatabaseDiscoveryService, DatabaseNamingConvention, 
EnhancedDatabaseService, dan EnhancedNotionService
"""

import os
import requests
import logging
import json
import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Import dependencies
from services.database_naming_service import DatabaseNamingConvention
from models.notion_database import NotionDatabase
from models.property_mapping import PropertyMapping as PropertyMappingModel
from config.database import db

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class PropertyType(Enum):
    """Enum untuk tipe property Notion"""
    TITLE = "title"
    RICH_TEXT = "rich_text"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    PEOPLE = "people"
    FILES = "files"
    CHECKBOX = "checkbox"
    URL = "url"
    EMAIL = "email"
    PHONE_NUMBER = "phone_number"
    NUMBER = "number"
    FORMULA = "formula"
    RELATION = "relation"
    ROLLUP = "rollup"
    CREATED_TIME = "created_time"
    CREATED_BY = "created_by"
    LAST_EDIT_TIME = "last_edited_time"
    LAST_EDITED_BY = "last_edited_by"

@dataclass
class PropertyMapping:
    """Data class untuk mapping property"""
    notion_property_name: str
    property_type: PropertyType
    mapped_field: str
    confidence_score: float
    alternative_names: List[str]
    is_required: bool
    validation_rules: Dict[str, Any]

class UnifiedNotionService:
    """
    Unified service untuk semua operasi Notion database
    Menggabungkan discovery, naming convention, property mapping, dan task management
    """
    
    def __init__(self):
        self.base_url = "https://api.notion.com/v1"
        self.notion_token = os.getenv('NOTION_TOKEN')
        
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}" if self.notion_token else "Bearer invalid_token",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        # Initialize sub-services
        self.naming_convention = DatabaseNamingConvention()
        
        # Initialize property mapping components
        self.property_patterns = self._initialize_property_patterns()
        self.field_mappings = self._initialize_field_mappings()
        self.validation_rules = self._initialize_validation_rules()
        
        # Employee database mapping (dari EnhancedNotionService)
        self.employee_databases = self._load_employee_databases()
        
        # Thread pool untuk async operations
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="notion-worker")
        
        logger.info("✅ UnifiedNotionService initialized successfully")
    
    def _load_employee_databases(self) -> Dict[str, str]:
        """Load mapping database ID untuk setiap karyawan"""
        return {
            "IRMN": os.getenv('NOTION_DATABASE_ID', "2543ea57-2713-8080-820c-000b3e400a46"),
            # Tambahkan database ID untuk karyawan lain sesuai kebutuhan
        }
    
    # =============================================================================
    # PROPERTY MAPPING METHODS (dari PropertyMappingService)
    # =============================================================================
    
    def _initialize_property_patterns(self) -> Dict[str, List[str]]:
        """Initialize pola nama property untuk setiap field"""
        return {
            # Title/Name patterns
            "title": [
                r"title", r"name", r"task", r"pekerjaan", r"uraian", r"deskripsi",
                r"judul", r"nama", r"kegiatan", r"aktivitas", r"item", r"hal"
            ],
            
            # Status patterns
            "status": [
                r"status", r"state", r"progress", r"progres", r"keadaan", r"kondisi",
                r"status pekerjaan", r"status task", r"status kegiatan", r"progress pekerjaan"
            ],
            
            # Priority patterns
            "priority": [
                r"priority", r"prioritas", r"urgensi", r"kepentingan", r"level",
                r"tingkat", r"grade", r"rank", r"importance", r"urgent"
            ],
            
            # Date patterns
            "date": [
                r"date", r"tanggal", r"waktu", r"time", r"deadline", r"due",
                r"jatuh tempo", r"target", r"schedule", r"jadwal", r"timeline"
            ],
            
            # Assignee patterns
            "assignee": [
                r"assignee", r"pic", r"responsible", r"penanggung jawab", r"pemilik",
                r"owner", r"assigned", r"diberikan kepada", r"ditugaskan", r"handler"
            ],
            
            # Description patterns
            "description": [
                r"description", r"deskripsi", r"detail", r"keterangan", r"catatan",
                r"notes", r"remark", r"penjelasan", r"informasi", r"content"
            ],
            
            # Difficulty patterns
            "difficulty": [
                r"difficulty", r"kesulitan", r"complexity", r"kompleksitas", r"level",
                r"tingkat kesulitan", r"challenge", r"tantangan", r"hardness"
            ],
            
            # Duration patterns
            "duration": [
                r"duration", r"durasi", r"time", r"waktu", r"estimate", r"estimasi",
                r"estimated time", r"waktu perkiraan", r"time estimate", r"effort"
            ],
            
            # Problems patterns
            "problems": [
                r"problem", r"masalah", r"issue", r"kendala", r"obstacle", r"hambatan",
                r"challenge", r"tantangan", r"difficulty", r"kesulitan", r"blocker"
            ],
            
            # Plan patterns
            "plan": [
                r"plan", r"rencana", r"tomorrow", r"besok", r"next", r"selanjutnya",
                r"future", r"mendatang", r"upcoming", r"planned", r"target"
            ],
            
            # Notes patterns
            "notes": [
                r"notes", r"catatan", r"remark", r"komentar", r"comment", r"memo",
                r"annotation", r"penjelasan", r"detail", r"keterangan tambahan"
            ],
            
            # URL patterns
            "url": [
                r"url", r"link", r"reference", r"referensi", r"source", r"sumber",
                r"attachment", r"lampiran", r"file", r"document", r"resource"
            ]
        }
    
    def _initialize_field_mappings(self) -> Dict[str, str]:
        """Initialize mapping field ke database column"""
        return {
            "title": "title",
            "status": "status", 
            "priority": "priority",
            "date": "task_date",
            "assignee": "assignee",
            "description": "description",
            "difficulty": "difficulty",
            "duration": "duration",
            "problems": "problems",
            "plan": "tomorrow_plan",
            "notes": "notes",
            "url": "notion_url"
        }
    
    def _initialize_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize aturan validasi untuk setiap field"""
        return {
            "title": {
                "required": True,
                "min_length": 1,
                "max_length": 500,
                "type": "string"
            },
            "status": {
                "required": False,
                "type": "select",
                "allowed_values": ["Tertunda", "Dalam Proses", "Selesai", "Dialihkan", "Pending", "In Progress", "Done", "Cancelled"]
            },
            "priority": {
                "required": False,
                "type": "select",
                "allowed_values": ["Rendah", "Sedang", "Tinggi", "Low", "Medium", "High", "Urgent"]
            },
            "date": {
                "required": False,
                "type": "date",
                "format": "ISO"
            },
            "assignee": {
                "required": False,
                "type": "people",
                "max_count": 10
            },
            "description": {
                "required": False,
                "type": "rich_text",
                "max_length": 2000
            },
            "difficulty": {
                "required": False,
                "type": "select",
                "allowed_values": ["Mudah", "Sedang", "Sulit", "Easy", "Medium", "Hard"]
            },
            "duration": {
                "required": False,
                "type": "number",
                "min_value": 0,
                "max_value": 1000
            },
            "problems": {
                "required": False,
                "type": "rich_text",
                "max_length": 1000
            },
            "plan": {
                "required": False,
                "type": "rich_text",
                "max_length": 1000
            },
            "notes": {
                "required": False,
                "type": "rich_text",
                "max_length": 2000
            },
            "url": {
                "required": False,
                "type": "url",
                "format": "url"
            }
        }
    
    def analyze_database_properties(self, database_properties: Dict[str, Any]) -> Dict[str, PropertyMapping]:
        """
        Analyze properties database Notion dan buat mapping
        
        Args:
            database_properties: Properties dari Notion database
            
        Returns:
            Dictionary dengan mapping property
        """
        try:
            logger.info(f"🔍 Analyzing {len(database_properties)} database properties...")
            
            mappings = {}
            
            for property_name, property_info in database_properties.items():
                property_type = property_info.get("type")
                
                if not property_type:
                    continue
                
                # Detect field berdasarkan nama property
                detected_field = self._detect_field_by_name(property_name)
                
                if detected_field:
                    # Validate property type compatibility
                    if self._validate_property_type_compatibility(detected_field, property_type):
                        confidence_score = self._calculate_confidence_score(property_name, detected_field, property_type)
                        
                        mapping = PropertyMapping(
                            notion_property_name=property_name,
                            property_type=PropertyType(property_type),
                            mapped_field=self.field_mappings[detected_field],
                            confidence_score=confidence_score,
                            alternative_names=self._get_alternative_names(property_name, detected_field),
                            is_required=self.validation_rules[detected_field].get("required", False),
                            validation_rules=self.validation_rules[detected_field]
                        )
                        
                        mappings[detected_field] = mapping
                        logger.info(f"✅ Mapped '{property_name}' ({property_type}) -> '{detected_field}' (confidence: {confidence_score:.2f})")
                    else:
                        logger.warning(f"⚠️ Property type mismatch: '{property_name}' ({property_type}) tidak kompatibel dengan field '{detected_field}'")
                else:
                    logger.debug(f"🔍 Property '{property_name}' ({property_type}) tidak terdeteksi sebagai field yang dikenal")
            
            # Check required fields
            missing_required = self._check_missing_required_fields(mappings)
            if missing_required:
                logger.warning(f"⚠️ Missing required fields: {missing_required}")
            
            logger.info(f"✅ Property mapping analysis complete. Mapped {len(mappings)} properties.")
            return mappings
            
        except Exception as e:
            logger.error(f"❌ Error analyzing database properties: {str(e)}")
            return {}
    
    def _detect_field_by_name(self, property_name: str) -> Optional[str]:
        """Detect field berdasarkan nama property menggunakan pattern matching"""
        property_name_lower = property_name.lower()
        
        for field, patterns in self.property_patterns.items():
            for pattern in patterns:
                if re.search(pattern, property_name_lower, re.IGNORECASE):
                    return field
        
        return None
    
    def _validate_property_type_compatibility(self, field: str, property_type: str) -> bool:
        """Validate apakah property type kompatibel dengan field"""
        validation_rule = self.validation_rules.get(field, {})
        expected_type = validation_rule.get("type")
        
        if not expected_type:
            return True
        
        # Mapping Notion property types ke expected types
        type_mapping = {
            "title": "string",
            "rich_text": "rich_text",
            "select": "select",
            "multi_select": "select",
            "date": "date",
            "people": "people",
            "url": "url",
            "number": "number",
            "checkbox": "boolean"
        }
        
        notion_type = type_mapping.get(property_type, property_type)
        return notion_type == expected_type or expected_type == "string"
    
    def _calculate_confidence_score(self, property_name: str, field: str, property_type: str) -> float:
        """Calculate confidence score untuk mapping (0.0 - 1.0)"""
        score = 0.0
        
        # Base score dari pattern matching
        property_name_lower = property_name.lower()
        patterns = self.property_patterns[field]
        
        for pattern in patterns:
            if re.search(pattern, property_name_lower, re.IGNORECASE):
                # Exact match gets higher score
                if pattern.lower() == property_name_lower:
                    score += 0.8
                else:
                    score += 0.4
                break
        
        # Bonus untuk property type compatibility
        if self._validate_property_type_compatibility(field, property_type):
            score += 0.2
        
        # Bonus untuk required fields
        if self.validation_rules[field].get("required", False):
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_alternative_names(self, property_name: str, field: str) -> List[str]:
        """Get alternative names untuk property"""
        alternatives = []
        patterns = self.property_patterns[field]
        
        for pattern in patterns:
            if pattern.lower() != property_name.lower():
                alternatives.append(pattern)
        
        return alternatives[:5]  # Limit to 5 alternatives
    
    def _check_missing_required_fields(self, mappings: Dict[str, PropertyMapping]) -> List[str]:
        """Check missing required fields"""
        missing = []
        
        for field, rule in self.validation_rules.items():
            if rule.get("required", False) and field not in mappings:
                missing.append(field)
        
        return missing
    
    def parse_task_with_mapping(self, page: Dict, mappings: Dict[str, PropertyMapping]) -> Dict[str, Any]:
        """
        Parse Notion page menggunakan property mapping
        
        Args:
            page: Notion page data
            mappings: Property mappings dari analyze_database_properties
            
        Returns:
            Parsed task data
        """
        try:
            properties = page.get('properties', {})
            parsed_data = {
                "id": page.get("id", ""),
                "url": page.get("url", ""),
                "created_time": page.get("created_time", ""),
                "last_edited_time": page.get("last_edited_time", "")
            }
            
            for field, mapping in mappings.items():
                property_name = mapping.notion_property_name
                property_info = properties.get(property_name, {})
                
                parsed_value = self._extract_property_value(property_info, mapping.property_type)
                
                if parsed_value is not None:
                    parsed_data[mapping.mapped_field] = parsed_value
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing task with mapping: {str(e)}")
            return {}
    
    def _extract_property_value(self, property_info: Dict, property_type: PropertyType) -> Any:
        """Extract value dari property berdasarkan type"""
        try:
            if property_type == PropertyType.TITLE:
                if property_info.get("title"):
                    return property_info["title"][0].get("text", {}).get("content", "")
                return ""
            
            elif property_type == PropertyType.RICH_TEXT:
                if property_info.get("rich_text"):
                    return property_info["rich_text"][0].get("text", {}).get("content", "")
                return ""
            
            elif property_type == PropertyType.SELECT:
                if property_info.get("select"):
                    return property_info["select"].get("name", "")
                return ""
            
            elif property_type == PropertyType.MULTI_SELECT:
                if property_info.get("multi_select"):
                    return [item.get("name", "") for item in property_info["multi_select"]]
                return []
            
            elif property_type == PropertyType.DATE:
                if property_info.get("date"):
                    return property_info["date"].get("start", "")
                return ""
            
            elif property_type == PropertyType.PEOPLE:
                if property_info.get("people"):
                    return [person.get("name", "") for person in property_info["people"] if person.get("name")]
                return []
            
            elif property_type == PropertyType.URL:
                return property_info.get("url", "")
            
            elif property_type == PropertyType.NUMBER:
                return property_info.get("number", 0)
            
            elif property_type == PropertyType.CHECKBOX:
                return property_info.get("checkbox", False)
            
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ Error extracting property value: {str(e)}")
            return None
    
    def validate_mapping_quality(self, mappings: Dict[str, PropertyMapping]) -> Dict[str, Any]:
        """
        Validate kualitas mapping dan berikan rekomendasi
        
        Args:
            mappings: Property mappings
            
        Returns:
            Validation results dan rekomendasi
        """
        try:
            results = {
                "total_properties": len(mappings),
                "required_fields_mapped": 0,
                "optional_fields_mapped": 0,
                "missing_required": [],
                "low_confidence_mappings": [],
                "recommendations": []
            }
            
            # Check required fields
            for field, rule in self.validation_rules.items():
                if rule.get("required", False):
                    if field in mappings:
                        results["required_fields_mapped"] += 1
                    else:
                        results["missing_required"].append(field)
                else:
                    if field in mappings:
                        results["optional_fields_mapped"] += 1
            
            # Check confidence scores
            for field, mapping in mappings.items():
                if mapping.confidence_score < 0.5:
                    results["low_confidence_mappings"].append({
                        "field": field,
                        "property": mapping.notion_property_name,
                        "confidence": mapping.confidence_score
                    })
            
            # Generate recommendations
            if results["missing_required"]:
                results["recommendations"].append(
                    f"Missing required fields: {', '.join(results['missing_required'])}"
                )
            
            if results["low_confidence_mappings"]:
                results["recommendations"].append(
                    f"Low confidence mappings detected: {len(results['low_confidence_mappings'])} properties"
                )
            
            if results["total_properties"] < 3:
                results["recommendations"].append(
                    "Very few properties mapped. Consider reviewing database structure."
                )
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error validating mapping quality: {str(e)}")
            return {}
    
    def suggest_property_renaming(self, mappings: Dict[str, PropertyMapping], database_properties: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Suggest renaming properties untuk meningkatkan mapping quality
        
        Args:
            mappings: Current property mappings
            database_properties: Original database properties
            
        Returns:
            List of renaming suggestions
        """
        try:
            suggestions = []
            
            # Find unmapped properties that could be useful
            mapped_property_names = {mapping.notion_property_name for mapping in mappings.values()}
            
            for property_name, property_info in database_properties.items():
                if property_name in mapped_property_names:
                    continue
                
                property_type = property_info.get("type")
                if not property_type:
                    continue
                
                # Check if this property could be mapped to a missing field
                for field, rule in self.validation_rules.items():
                    if field not in mappings and self._validate_property_type_compatibility(field, property_type):
                        # Suggest renaming
                        suggested_name = self._suggest_better_name(field, property_name)
                        
                        if suggested_name != property_name:
                            suggestions.append({
                                "current_name": property_name,
                                "suggested_name": suggested_name,
                                "target_field": field,
                                "reason": f"Could map to missing field '{field}'"
                            })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"❌ Error suggesting property renaming: {str(e)}")
            return []
    
    def _suggest_better_name(self, field: str, current_name: str) -> str:
        """Suggest better name untuk property"""
        patterns = self.property_patterns[field]
        
        # Return the most common pattern for this field
        if patterns:
            return patterns[0].title()
        
        return current_name
    
    # =============================================================================
    # DATABASE DISCOVERY METHODS (dari DatabaseDiscoveryService)
    # =============================================================================
    
    def discover_all_databases(self) -> Dict[str, any]:
        """
        Discovery semua database dalam workspace Notion
        
        Returns:
            Dict[str, any]: Hasil discovery dengan metadata database
        """
        try:
            logger.info("Memulai discovery database Notion...")
            
            # Dapatkan semua database
            databases = self._get_all_databases()
            
            if not databases:
                logger.warning("Tidak ada database yang ditemukan")
                return {
                    'success': False,
                    'message': 'Tidak ada database yang ditemukan',
                    'databases': [],
                    'statistics': {}
                }
            
            # Analisis setiap database
            analyzed_databases = []
            for db_info in databases:
                analysis = self._analyze_database(db_info)
                if analysis:
                    analyzed_databases.append(analysis)
            
            # Simpan ke database lokal
            saved_count = self._save_databases_to_local(analyzed_databases)
            
            # Generate statistik
            statistics = self._generate_discovery_statistics(analyzed_databases)
            
            logger.info(f"Discovery selesai. {len(analyzed_databases)} database dianalisis, {saved_count} disimpan")
            
            return {
                'success': True,
                'message': f'Berhasil discover {len(analyzed_databases)} database',
                'databases': analyzed_databases,
                'statistics': statistics,
                'saved_count': saved_count
            }
            
        except Exception as e:
            logger.error(f"Error saat discovery database: {str(e)}")
            return {
                'success': False,
                'message': f'Error saat discovery: {str(e)}',
                'databases': [],
                'statistics': {}
            }
    
    def _get_all_databases(self) -> List[Dict]:
        """Mendapatkan semua database dari Notion API"""
        databases = []
        start_cursor = None
        
        try:
            while True:
                url = f"{self.base_url}/search"
                
                payload = {
                    "filter": {
                        "value": "database",
                        "property": "object"
                    },
                    "sort": {
                        "direction": "ascending",
                        "timestamp": "last_edited_time"
                    }
                }
                
                if start_cursor:
                    payload["start_cursor"] = start_cursor
                
                response = requests.post(url, headers=self.headers, json=payload)
                
                if response.status_code != 200:
                    logger.error(f"Error API Notion: {response.status_code} - {response.text}")
                    break
                
                data = response.json()
                databases.extend(data.get('results', []))
                
                if not data.get('has_more'):
                    break
                
                start_cursor = data.get('next_cursor')
                
                if len(databases) > 1000:
                    logger.warning("Mencapai limit 1000 database, berhenti discovery")
                    break
            
            logger.info(f"Berhasil mendapatkan {len(databases)} database dari Notion")
            return databases
            
        except Exception as e:
            logger.error(f"Error saat mengambil database dari Notion: {str(e)}")
            return []
    
    def _get_database_info(self, database_id: str) -> Optional[Dict]:
        """Mendapatkan informasi database berdasarkan ID dari Notion API"""
        try:
            url = f"{self.base_url}/databases/{database_id}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error API Notion untuk database {database_id}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error saat mengambil database info {database_id}: {str(e)}")
            return None
    
    def _analyze_database(self, db_info: Dict) -> Optional[Dict]:
        """Analisis database untuk menentukan tipe dan metadata"""
        try:
            database_id = db_info.get('id')
            database_title = self._extract_database_title(db_info)
            database_properties = db_info.get('properties', {})
            
            # Generate metadata menggunakan naming convention service
            metadata = self.naming_convention.generate_database_metadata(
                database_id, database_title, database_properties
            )
            
            # Tambahkan informasi tambahan
            analysis = {
                **metadata,
                'notion_url': db_info.get('url'),
                'created_time': db_info.get('created_time'),
                'last_edited_time': db_info.get('last_edited_time'),
                'archived': db_info.get('archived', False),
                'raw_properties': list(database_properties.keys())
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error saat analisis database {db_info.get('id', 'unknown')}: {str(e)}")
            return None
    
    def _extract_database_title(self, db_info: Dict) -> str:
        """Ekstrak judul database dari response Notion API"""
        try:
            title_property = db_info.get('title', [])
            if title_property and len(title_property) > 0:
                title_content = title_property[0].get('plain_text', '')
                if title_content:
                    return title_content
            
            return f"Database {db_info.get('id', 'Unknown')}"
            
        except Exception as e:
            logger.error(f"Error saat ekstrak judul database: {str(e)}")
            return "Unknown Database"
    
    def _save_databases_to_local(self, databases: List[Dict]) -> int:
        """Simpan database ke database lokal"""
        saved_count = 0
        
        try:
            from app import app
            
            with app.app_context():
                for db_data in databases:
                    database_id = db_data.get('database_id')
                    
                    # Cek apakah sudah ada
                    existing_db = NotionDatabase.get_by_database_id(database_id)
                    
                    if existing_db:
                        # Update existing database
                        existing_db.database_title = db_data.get('database_title')
                        existing_db.employee_name = db_data.get('employee_name')
                        existing_db.database_type = db_data.get('database_type')
                        existing_db.is_task_database = db_data.get('is_task_database')
                        existing_db.is_employee_specific = db_data.get('is_employee_specific')
                        existing_db.structure_valid = db_data.get('structure_valid')
                        existing_db.confidence_score = db_data.get('confidence_score')
                        existing_db.missing_properties = json.dumps(db_data.get('missing_properties', []))
                        existing_db.updated_at = datetime.utcnow()
                    else:
                        # Buat database baru
                        new_db = NotionDatabase(
                            database_id=database_id,
                            database_title=db_data.get('database_title'),
                            employee_name=db_data.get('employee_name'),
                            database_type=db_data.get('database_type'),
                            is_task_database=db_data.get('is_task_database'),
                            is_employee_specific=db_data.get('is_employee_specific'),
                            structure_valid=db_data.get('structure_valid'),
                            confidence_score=db_data.get('confidence_score'),
                            missing_properties=json.dumps(db_data.get('missing_properties', [])),
                            sync_enabled=True
                        )
                        db.session.add(new_db)
                    
                    saved_count += 1
                
                db.session.commit()
                logger.info(f"Berhasil menyimpan {saved_count} database ke database lokal")
            
        except Exception as e:
            logger.error(f"Error saat menyimpan database ke lokal: {str(e)}")
            saved_count = 0
        
        return saved_count
    
    def _generate_discovery_statistics(self, databases: List[Dict]) -> Dict[str, any]:
        """Generate statistik dari hasil discovery"""
        total_databases = len(databases)
        task_databases = sum(1 for db in databases if db.get('is_task_database'))
        employee_databases = sum(1 for db in databases if db.get('is_employee_specific'))
        valid_databases = sum(1 for db in databases if db.get('structure_valid'))
        
        # Hitung confidence score rata-rata
        confidence_scores = [db.get('confidence_score', 0) for db in databases]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Kategori database
        categories = {}
        for db in databases:
            category = db.get('database_type', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        
        return {
            'total_databases': total_databases,
            'task_databases': task_databases,
            'employee_databases': employee_databases,
            'valid_databases': valid_databases,
            'average_confidence': round(avg_confidence, 2),
            'categories': categories,
            'discovery_time': datetime.utcnow().isoformat()
        }
    
    def get_employee_databases(self, employee_name: str = None) -> List[Dict]:
        """Mendapatkan database untuk karyawan tertentu"""
        try:
            from app import app
            with app.app_context():
                databases = NotionDatabase.get_employee_databases(employee_name)
                return [db.to_dict() for db in databases]
        except Exception as e:
            logger.error(f"Error saat mengambil database karyawan: {str(e)}")
            return []
    
    def get_task_databases(self) -> List[Dict]:
        """Mendapatkan semua database task yang valid"""
        try:
            from app import app
            with app.app_context():
                databases = NotionDatabase.get_task_databases()
                return [db.to_dict() for db in databases]
        except Exception as e:
            logger.error(f"Error saat mengambil database task: {str(e)}")
            return []
    
    def get_discovery_statistics(self) -> Dict[str, any]:
        """Mendapatkan statistik discovery database"""
        try:
            from app import app
            with app.app_context():
                return NotionDatabase.get_sync_statistics()
        except Exception as e:
            logger.error(f"Error saat mengambil statistik: {str(e)}")
            return {}
    
    def validate_notion_token(self) -> bool:
        """Validasi token Notion"""
        try:
            url = f"{self.base_url}/users/me"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                logger.info("Token Notion valid")
                return True
            else:
                logger.error(f"Token Notion tidak valid: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error saat validasi token: {str(e)}")
            return False
    
    # =============================================================================
    # ENHANCED DATABASE METHODS (dari EnhancedDatabaseService)
    # =============================================================================
    
    def discover_and_analyze_databases(self) -> Dict[str, Any]:
        """Discover semua database dan analyze property mapping"""
        try:
            logger.info("🔍 Starting comprehensive database discovery and analysis...")
            
            # Step 1: Discover databases
            discovery_result = self.discover_all_databases()
            
            if not discovery_result.get('success'):
                return {
                    'success': False,
                    'error': discovery_result.get('error', 'Database discovery failed'),
                    'databases_analyzed': 0,
                    'total_mappings_created': 0
                }
            
            # Step 2: Analyze each database for property mapping
            databases_analyzed = 0
            total_mappings_created = 0
            
            databases = discovery_result.get('databases', [])
            
            for database in databases:
                try:
                    database_id = database.get('database_id')
                    if not database_id:
                        continue
                    
                    # Get database properties from Notion API
                    properties = self._get_database_properties(database_id)
                    if not properties:
                        continue
                    
                    # Analyze properties and create mappings
                    mappings = self.analyze_database_properties(properties)
                    
                    # Save mappings to database
                    mappings_saved = self._save_property_mappings(database_id, mappings)
                    
                    # Update database metadata with mapping info
                    self._update_database_mapping_metadata(database_id, mappings)
                    
                    databases_analyzed += 1
                    total_mappings_created += mappings_saved
                    
                    logger.info(f"✅ Analyzed database {database_id}: {len(mappings)} mappings created")
                    
                except Exception as e:
                    logger.error(f"❌ Error analyzing database {database.get('database_id', 'unknown')}: {str(e)}")
                    continue
            
            return {
                'success': True,
                'databases_analyzed': databases_analyzed,
                'total_mappings_created': total_mappings_created,
                'discovery_result': discovery_result
            }
            
        except Exception as e:
            logger.error(f"❌ Error in discover_and_analyze_databases: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'databases_analyzed': 0,
                'total_mappings_created': 0
            }
    
    def _get_database_properties(self, database_id: str) -> Optional[Dict[str, Any]]:
        """Get database properties dari Notion API"""
        try:
            response = requests.get(
                f"{self.base_url}/databases/{database_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('properties', {})
            else:
                logger.error(f"❌ Error getting database properties: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Exception getting database properties: {str(e)}")
            return None
    
    def _save_property_mappings(self, database_id: str, mappings: Dict[str, PropertyMapping]) -> int:
        """Save property mappings ke database"""
        try:
            mappings_saved = 0
            
            for field, mapping in mappings.items():
                mapping_data = {
                    'notion_property_name': mapping.notion_property_name,
                    'property_type': mapping.property_type.value,
                    'mapped_field': mapping.mapped_field,
                    'confidence_score': mapping.confidence_score,
                    'alternative_names': mapping.alternative_names,
                    'is_required': mapping.is_required,
                    'validation_rules': mapping.validation_rules,
                    'is_active': True
                }
                
                PropertyMappingModel.create_or_update_mapping(database_id, mapping_data)
                mappings_saved += 1
            
            return mappings_saved
            
        except Exception as e:
            logger.error(f"❌ Error saving property mappings: {str(e)}")
            return 0
    
    def _update_database_mapping_metadata(self, database_id: str, mappings: Dict[str, PropertyMapping]):
        """Update database metadata dengan mapping information"""
        try:
            from app import app
            
            with app.app_context():
                database = NotionDatabase.get_by_database_id(database_id)
                if database:
                    # Calculate mapping quality
                    quality_validation = self.validate_mapping_quality(mappings)
                    
                    # Update database metadata
                    database.mapping_quality_score = quality_validation.get('mapping_quality_score', 0)
                    database.mapped_properties_count = len(mappings)
                    database.last_mapping_analysis = datetime.utcnow()
                    
                    db.session.commit()
                    
        except Exception as e:
            logger.error(f"❌ Error updating database mapping metadata: {str(e)}")
    
    def get_tasks_from_database(self, database_id: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Get tasks dari database tertentu menggunakan property mapping"""
        try:
            # Get property mappings for this database
            mappings = self._get_database_mappings(database_id)
            if not mappings:
                logger.warning(f"⚠️ No property mappings found for database {database_id}")
                return []
            
            # Query Notion database
            tasks_data = self._query_notion_database(database_id, filters)
            if not tasks_data:
                return []
            
            # Parse tasks using mappings
            parsed_tasks = []
            for page in tasks_data:
                parsed_task = self.parse_task_with_mapping(page, mappings)
                if parsed_task:
                    parsed_tasks.append(parsed_task)
            
            logger.info(f"✅ Retrieved {len(parsed_tasks)} tasks from database {database_id}")
            return parsed_tasks
            
        except Exception as e:
            logger.error(f"❌ Error getting tasks from database {database_id}: {str(e)}")
            return []
    
    def _get_database_mappings(self, database_id: str) -> Dict[str, PropertyMapping]:
        """Get property mappings dari database"""
        try:
            from app import app
            
            with app.app_context():
                db_mappings = PropertyMappingModel.get_database_mappings(database_id)
                
                mappings = {}
                for db_mapping in db_mappings:
                    mapping = PropertyMapping(
                        notion_property_name=db_mapping.notion_property_name,
                        property_type=PropertyType(db_mapping.property_type),
                        mapped_field=db_mapping.mapped_field,
                        confidence_score=db_mapping.confidence_score,
                        alternative_names=db_mapping.alternative_names,
                        is_required=db_mapping.is_required,
                        validation_rules=db_mapping.validation_rules
                    )
                    
                    # Get field name from mapped_field
                    field_name = self._get_field_name_from_mapped_field(db_mapping.mapped_field)
                    if field_name:
                        mappings[field_name] = mapping
                
                return mappings
                
        except Exception as e:
            logger.error(f"❌ Error getting database mappings: {str(e)}")
            return {}
    
    def _get_field_name_from_mapped_field(self, mapped_field: str) -> Optional[str]:
        """Get field name dari mapped field"""
        reverse_mapping = {v: k for k, v in self.field_mappings.items()}
        return reverse_mapping.get(mapped_field)
    
    def _query_notion_database(self, database_id: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Query Notion database"""
        try:
            payload = {
                "page_size": 100,
                "sorts": [
                    {
                        "property": "created_time",
                        "direction": "descending"
                    }
                ]
            }
            
            if filters:
                payload["filter"] = filters
            
            response = requests.post(
                f"{self.base_url}/databases/{database_id}/query",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            else:
                logger.error(f"❌ Error querying Notion database: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Exception querying Notion database: {str(e)}")
            return []
    
    def get_all_employee_tasks(self, employee_filter: Optional[str] = None) -> Dict[str, List[Dict]]:
        """Get semua task dari semua database, dikelompokkan berdasarkan employee"""
        try:
            from app import app
            
            with app.app_context():
                # Get all employee databases
                employee_databases = NotionDatabase.get_employee_databases()
                
                all_tasks = {}
                
                for database in employee_databases:
                    employee_name = database.employee_name
                    
                    # Apply employee filter if specified
                    if employee_filter and employee_name != employee_filter:
                        continue
                    
                    # Get tasks from this database
                    tasks = self.get_tasks_from_database(database.database_id)
                    
                    if tasks:
                        if employee_name not in all_tasks:
                            all_tasks[employee_name] = []
                        
                        all_tasks[employee_name].extend(tasks)
                
                logger.info(f"✅ Retrieved tasks for {len(all_tasks)} employees")
                return all_tasks
                
        except Exception as e:
            logger.error(f"❌ Error getting all employee tasks: {str(e)}")
            return {}
    
    def analyze_mapping_quality(self, database_id: str) -> Dict[str, Any]:
        """Analyze kualitas mapping untuk database tertentu"""
        try:
            # Get database properties
            properties = self._get_database_properties(database_id)
            if not properties:
                return {'error': 'Could not retrieve database properties'}
            
            # Analyze properties
            mappings = self.analyze_database_properties(properties)
            
            # Validate mapping quality
            quality_validation = self.validate_mapping_quality(mappings)
            
            # Get renaming suggestions
            renaming_suggestions = self.suggest_property_renaming(mappings, properties)
            
            # Convert mappings to JSON-serializable format
            serializable_mappings = {}
            for k, v in mappings.items():
                mapping_dict = {
                    'notion_property_name': v.notion_property_name,
                    'property_type': v.property_type.value if hasattr(v.property_type, 'value') else str(v.property_type),
                    'mapped_field': v.mapped_field,
                    'confidence_score': v.confidence_score,
                    'alternative_names': v.alternative_names,
                    'is_required': v.is_required,
                    'validation_rules': v.validation_rules
                }
                serializable_mappings[k] = mapping_dict
            
            return {
                'database_id': database_id,
                'total_properties': len(properties),
                'mapped_properties': len(mappings),
                'mapping_quality': quality_validation,
                'renaming_suggestions': renaming_suggestions,
                'mappings': serializable_mappings
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing mapping quality: {str(e)}")
            return {'error': str(e)}
    
    def update_property_mapping(self, database_id: str, property_name: str, 
                               mapped_field: str, is_active: bool = True) -> bool:
        """Update property mapping secara manual"""
        try:
            from app import app
            
            with app.app_context():
                # Get property info from Notion
                properties = self._get_database_properties(database_id)
                if not properties or property_name not in properties:
                    return False
                
                property_info = properties[property_name]
                property_type = property_info.get('type', 'unknown')
                
                # Create mapping data
                mapping_data = {
                    'notion_property_name': property_name,
                    'property_type': property_type,
                    'mapped_field': mapped_field,
                    'confidence_score': 1.0,  # Manual mapping gets full confidence
                    'alternative_names': [],
                    'is_required': False,
                    'validation_rules': {},
                    'is_active': is_active
                }
                
                # Save mapping
                PropertyMappingModel.create_or_update_mapping(database_id, mapping_data)
                
                logger.info(f"✅ Updated property mapping: {database_id}:{property_name} -> {mapped_field}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error updating property mapping: {str(e)}")
            return False
    
    def get_mapping_statistics(self) -> Dict[str, Any]:
        """Get overall mapping statistics"""
        try:
            from app import app
            
            with app.app_context():
                # Get all databases with mappings
                database_ids = PropertyMappingModel.get_all_database_ids()
                
                total_databases = len(database_ids)
                total_mappings = 0
                active_mappings = 0
                high_quality_mappings = 0
                
                for database_id in database_ids:
                    stats = PropertyMappingModel.get_mapping_statistics(database_id)
                    total_mappings += stats['total_mappings']
                    active_mappings += stats['active_mappings']
                    high_quality_mappings += stats['high_confidence_mappings']
                
                return {
                    'total_databases': total_databases,
                    'total_mappings': total_mappings,
                    'active_mappings': active_mappings,
                    'high_quality_mappings': high_quality_mappings,
                    'average_mappings_per_database': total_mappings / total_databases if total_databases > 0 else 0,
                    'mapping_coverage_percentage': (active_mappings / total_mappings * 100) if total_mappings > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting mapping statistics: {str(e)}")
            return {}
    
    # =============================================================================
    # ENHANCED NOTION METHODS (dari EnhancedNotionService)
    # =============================================================================
    
    def get_all_employee_tasks_sync(self, 
                                   employee_filter: Optional[str] = None,
                                   status_filter: Optional[str] = None,
                                   priority_filter: Optional[str] = None,
                                   date_from: Optional[str] = None,
                                   date_to: Optional[str] = None) -> List[Dict]:
        """Mengambil task dari semua database karyawan secara parallel"""
        try:
            logger.info("🔍 Mengambil data task dari semua database karyawan...")
            
            # Filter karyawan yang akan diambil datanya
            target_employees = self.employee_databases
            if employee_filter:
                target_employees = {k: v for k, v in target_employees.items() 
                                  if employee_filter.lower() in k.lower()}
            
            # Ambil data secara parallel menggunakan ThreadPoolExecutor
            all_tasks = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for employee_name, database_id in target_employees.items():
                    future = executor.submit(
                        self._fetch_employee_tasks_sync, 
                        employee_name, database_id,
                        status_filter, priority_filter, date_from, date_to
                    )
                    futures.append(future)
                
                # Collect results
                for future in futures:
                    try:
                        result = future.result(timeout=30)
                        all_tasks.extend(result)
                    except Exception as e:
                        logger.error(f"Error fetching employee tasks: {e}")
            
            logger.info(f"✅ Berhasil mengambil {len(all_tasks)} task dari {len(target_employees)} karyawan")
            return all_tasks
            
        except Exception as e:
            logger.error(f"❌ Error mengambil semua task: {str(e)}")
            return self._get_fallback_tasks()
    
    def get_all_employees_sync(self) -> List[Dict]:
        """Mengambil daftar semua karyawan"""
        try:
            employees = []
            for employee_name, database_id in self.employee_databases.items():
                employees.append({
                    "name": employee_name,
                    "database_id": database_id,
                    "status": "active"
                })
            return employees
        except Exception as e:
            logger.error(f"❌ Error getting employees: {str(e)}")
            return []
    
    def _fetch_employee_tasks_sync(self, 
                                  employee_name: str,
                                  database_id: str,
                                  status_filter: Optional[str] = None,
                                  priority_filter: Optional[str] = None,
                                  date_from: Optional[str] = None,
                                  date_to: Optional[str] = None) -> List[Dict]:
        """Fetch tasks untuk satu karyawan secara async"""
        try:
            # Build filter
            filters = []
            
            if status_filter:
                filters.append({
                    "property": "Status Pekerjaan",
                    "select": {"equals": status_filter}
                })
                
            if priority_filter:
                filters.append({
                    "property": "Prioritas",
                    "select": {"equals": priority_filter}
                })
                
            if date_from or date_to:
                date_filter = {"property": "Tanggal", "date": {}}
                if date_from:
                    date_filter["date"]["on_or_after"] = date_from
                if date_to:
                    date_filter["date"]["on_or_before"] = date_to
                filters.append(date_filter)
            
            # Build payload
            payload = {
                "page_size": 100,
                "sorts": [{"property": "Tanggal", "direction": "descending"}]
            }
            
            if filters:
                payload["filter"] = {"and": filters}
            
            # Make sync request
            response = requests.post(
                f"{self.base_url}/databases/{database_id}/query",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                tasks = []
                
                for page in data.get("results", []):
                    task = self._parse_task_page(page, employee_name)
                    if task:
                        tasks.append(task)
                
                return tasks
            else:
                logger.error(f"Error fetching tasks for {employee_name}: {response.status_code}")
                return []
                    
        except Exception as e:
            logger.error(f"Error fetching tasks for {employee_name}: {str(e)}")
            return []
    
    def _parse_task_page(self, page: Dict, employee_name: str) -> Optional[Dict]:
        """Parse Notion page menjadi task dictionary dengan employee info"""
        try:
            properties = page.get('properties', {})
            
            # Extract title
            title_prop = properties.get("Uraian Pekerjaan", {})
            title = ""
            if title_prop.get("title"):
                title = title_prop["title"][0].get("text", {}).get("content", "")
            
            # Extract status
            status_prop = properties.get("Status Pekerjaan", {})
            status = status_prop.get("select", {}).get("name", "") if status_prop.get("select") else ""
            
            # Extract priority
            priority_prop = properties.get("Prioritas", {})
            priority = priority_prop.get("select", {}).get("name", "") if priority_prop.get("select") else ""
            
            # Extract date
            date_prop = properties.get("Tanggal", {})
            date = date_prop.get("date", {}).get("start", "") if date_prop.get("date") else ""
            
            # Extract description
            desc_prop = properties.get("Deskripsi", {})
            description = ""
            if desc_prop.get("rich_text"):
                description = desc_prop["rich_text"][0].get("text", {}).get("content", "")
            
            return {
                "id": page.get("id", ""),
                "employee_name": employee_name,
                "title": title,
                "status": status,
                "priority": priority,
                "date": date,
                "description": description,
                "url": page.get("url", ""),
                "created_time": page.get("created_time", ""),
                "last_edited_time": page.get("last_edited_time", "")
            }
            
        except Exception as e:
            logger.error(f"Error parsing task page: {str(e)}")
            return None
    
    def get_employee_statistics(self) -> Dict[str, Any]:
        """Get statistics untuk semua karyawan"""
        try:
            return {
                "total_employees": len(self.employee_databases),
                "total_tasks": 0,
                "tasks_by_status": {
                    "Tertunda": 0,
                    "Dalam Proses": 0,
                    "Selesai": 0
                },
                "tasks_by_priority": {
                    "Tinggi": 0,
                    "Sedang": 0,
                    "Rendah": 0
                },
                "last_sync": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {}
    
    def discover_employee_databases(self) -> List[Dict]:
        """Discover semua database karyawan dalam workspace"""
        try:
            # Search semua database dalam workspace
            response = requests.post(
                f"{self.base_url}/search",
                headers=self.headers,
                json={
                    "filter": {"property": "object", "value": "database"},
                    "page_size": 100
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                databases = []
                
                for db in data.get("results", []):
                    db_info = {
                        "id": db.get("id"),
                        "title": self._extract_database_title(db),
                        "url": db.get("url"),
                        "created_time": db.get("created_time")
                    }
                    databases.append(db_info)
                
                logger.info(f"✅ Discovered {len(databases)} databases")
                return databases
            else:
                logger.error(f"Error discovering databases: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error discovering databases: {str(e)}")
            return []
    
    def _get_fallback_tasks(self) -> List[Dict]:
        """Return fallback sample data"""
        logger.warning("⚠️ Menggunakan fallback data")
        
        return [
            {
                "id": "fallback-1",
                "employee_name": "IRMN",
                "title": "Sample Task 1",
                "status": "Dalam Proses",
                "priority": "Tinggi",
                "date": "2024-01-15",
                "description": "Sample task description",
                "url": "",
                "created_time": "2024-01-15T10:00:00Z",
                "last_edited_time": "2024-01-15T10:00:00Z"
            }
        ]
    
    def validate_token(self) -> bool:
        """Validate Notion API token"""
        if not self.notion_token or self.notion_token == 'your_notion_integration_token_here':
            return False
        
        try:
            response = requests.get(
                "https://api.notion.com/v1/users/me",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        return {
            'service_name': 'UnifiedNotionService',
            'version': '1.0.0',
            'token_configured': self.validate_token(),
            'employee_databases_count': len(self.employee_databases),
            'employee_list': list(self.employee_databases.keys()),
            'base_url': self.base_url,
            'last_updated': datetime.now().isoformat()
        }
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
        logger.info("✅ UnifiedNotionService cleanup completed")
    
    # =============================================================================
    # ASYNC METHODS (untuk compatibility dengan controller)
    # =============================================================================
    
    async def get_all_employee_tasks_async(self, 
                                         employee_filter: Optional[str] = None,
                                         status_filter: Optional[str] = None,
                                         priority_filter: Optional[str] = None,
                                         date_from: Optional[str] = None,
                                         date_to: Optional[str] = None) -> List[Dict]:
        """Async wrapper untuk get_all_employee_tasks_sync"""
        try:
            # Run sync method in thread pool untuk async compatibility
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self.get_all_employee_tasks_sync,
                employee_filter,
                status_filter,
                priority_filter,
                date_from,
                date_to
            )
            return result
        except Exception as e:
            logger.error(f"❌ Error in get_all_employee_tasks_async: {str(e)}")
            return self._get_fallback_tasks()
    
    async def get_all_employees_async(self) -> List[Dict]:
        """Async wrapper untuk get_all_employees_sync"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self.get_all_employees_sync
            )
            return result
        except Exception as e:
            logger.error(f"❌ Error in get_all_employees_async: {str(e)}")
            return []


# Global instance untuk singleton pattern
_unified_notion_service = None

def get_unified_notion_service() -> UnifiedNotionService:
    """Get singleton instance of UnifiedNotionService"""
    global _unified_notion_service
    if _unified_notion_service is None:
        _unified_notion_service = UnifiedNotionService()
    return _unified_notion_service
