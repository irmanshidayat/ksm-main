import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseNamingConvention:
    """
    Service untuk mendeteksi dan memproses konvensi penamaan database Notion
    yang fleksibel untuk mengidentifikasi database karyawan
    """
    
    def __init__(self):
        # Pattern untuk mendeteksi nama karyawan dari judul database
        self.employee_patterns = [
            # Pattern 1: "Tasks - [Nama]"
            r'tasks?\s*[-–—]\s*([a-zA-Z\s]+)',
            # Pattern 2: "[Nama]'s Tasks"
            r"([a-zA-Z\s]+)'s?\s*tasks?",
            # Pattern 3: "[Nama] Tasks"
            r'([a-zA-Z\s]+)\s+tasks?',
            # Pattern 4: "Task [Nama]"
            r'task\s+([a-zA-Z\s]+)',
            # Pattern 5: "[Nama] - Task"
            r'([a-zA-Z\s]+)\s*[-–—]\s*task',
            # Pattern 6: "Daily Task [Nama]"
            r'daily\s+task\s+([a-zA-Z\s]+)',
            # Pattern 7: "[Nama] Daily Task"
            r'([a-zA-Z\s]+)\s+daily\s+task',
            # Pattern 8: "Work [Nama]"
            r'work\s+([a-zA-Z\s]+)',
            # Pattern 9: "[Nama] Work"
            r'([a-zA-Z\s]+)\s+work',
            # Pattern 10: "Pekerjaan [Nama]"
            r'pekerjaan\s+([a-zA-Z\s]+)',
            # Pattern 11: "[Nama] Pekerjaan"
            r'([a-zA-Z\s]+)\s+pekerjaan',
            # Pattern 12: "Tugas [Nama]"
            r'tugas\s+([a-zA-Z\s]+)',
            # Pattern 13: "[Nama] Tugas"
            r'([a-zA-Z\s]+)\s+tugas',
        ]
        
        # Kata-kata yang harus diabaikan (stop words)
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'dan', 'atau', 'dengan',
            'untuk', 'dari', 'ke', 'di', 'pada', 'oleh', 'adalah', 'akan',
            'bisa', 'dapat', 'harus', 'perlu', 'mungkin', 'sebaiknya'
        }
        
        # Mapping nama umum ke nama lengkap
        self.name_mapping = {
            'irman': 'Irman',
            'john': 'John Doe',
            'jane': 'Jane Smith',
            # Tambahkan mapping lain sesuai kebutuhan
        }
    
    def extract_employee_name(self, database_title: str) -> Optional[str]:
        """
        Mengekstrak nama karyawan dari judul database Notion
        
        Args:
            database_title (str): Judul database dari Notion
            
        Returns:
            Optional[str]: Nama karyawan yang terdeteksi atau None
        """
        if not database_title:
            return None
            
        # Normalisasi judul
        normalized_title = database_title.lower().strip()
        
        # Coba setiap pattern
        for pattern in self.employee_patterns:
            match = re.search(pattern, normalized_title, re.IGNORECASE)
            if match:
                employee_name = match.group(1).strip()
                if employee_name and len(employee_name) > 1:
                    # Bersihkan nama dari karakter yang tidak diinginkan
                    cleaned_name = self._clean_employee_name(employee_name)
                    if cleaned_name:
                        return self._normalize_employee_name(cleaned_name)
        
        return None
    
    def _clean_employee_name(self, name: str) -> Optional[str]:
        """
        Membersihkan nama karyawan dari karakter yang tidak diinginkan
        
        Args:
            name (str): Nama mentah
            
        Returns:
            Optional[str]: Nama yang sudah dibersihkan
        """
        # Hapus karakter khusus kecuali spasi dan huruf
        cleaned = re.sub(r'[^a-zA-Z\s]', '', name)
        
        # Hapus spasi berlebih
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Hapus kata-kata yang terlalu pendek atau stop words
        words = cleaned.split()
        filtered_words = []
        
        for word in words:
            if len(word) > 1 and word.lower() not in self.stop_words:
                filtered_words.append(word)
        
        if filtered_words:
            return ' '.join(filtered_words)
        
        return None
    
    def _normalize_employee_name(self, name: str) -> str:
        """
        Normalisasi nama karyawan (capitalize, mapping, dll)
        
        Args:
            name (str): Nama karyawan
            
        Returns:
            str: Nama yang sudah dinormalisasi
        """
        # Cek mapping nama
        if name.lower() in self.name_mapping:
            return self.name_mapping[name.lower()]
        
        # Capitalize setiap kata
        words = name.split()
        normalized_words = []
        
        for word in words:
            if len(word) > 1:
                # Handle nama dengan prefix/suffix khusus
                if word.lower() in ['van', 'von', 'de', 'da', 'di', 'del', 'della']:
                    normalized_words.append(word.lower())
                else:
                    normalized_words.append(word.capitalize())
        
        return ' '.join(normalized_words)
    
    def detect_database_type(self, database_title: str) -> Dict[str, any]:
        """
        Mendeteksi tipe database berdasarkan judul
        
        Args:
            database_title (str): Judul database
            
        Returns:
            Dict[str, any]: Informasi tipe database
        """
        title_lower = database_title.lower()
        
        # Deteksi tipe database
        database_type = {
            'is_task_database': False,
            'is_employee_specific': False,
            'employee_name': None,
            'database_category': 'unknown',
            'confidence_score': 0.0
        }
        
        # Cek apakah ini database task
        task_keywords = ['task', 'tugas', 'pekerjaan', 'work', 'daily', 'todo', 'to-do']
        is_task_db = any(keyword in title_lower for keyword in task_keywords)
        
        if is_task_db:
            database_type['is_task_database'] = True
            database_type['confidence_score'] += 0.3
            
            # Cek apakah spesifik untuk karyawan
            employee_name = self.extract_employee_name(database_title)
            if employee_name:
                database_type['is_employee_specific'] = True
                database_type['employee_name'] = employee_name
                database_type['confidence_score'] += 0.5
                database_type['database_category'] = 'employee_task'
            else:
                database_type['database_category'] = 'general_task'
        
        # Deteksi kategori lain
        if 'project' in title_lower or 'proyek' in title_lower:
            database_type['database_category'] = 'project'
        elif 'meeting' in title_lower or 'rapat' in title_lower:
            database_type['database_category'] = 'meeting'
        elif 'document' in title_lower or 'dokumen' in title_lower:
            database_type['database_category'] = 'document'
        
        return database_type
    
    def validate_database_structure(self, database_properties: Dict) -> Dict[str, any]:
        """
        Validasi struktur database untuk memastikan ini adalah database task
        
        Args:
            database_properties (Dict): Properties database dari Notion API
            
        Returns:
            Dict[str, any]: Hasil validasi struktur
        """
        validation_result = {
            'is_valid_task_database': False,
            'has_title_property': False,
            'has_status_property': False,
            'has_date_property': False,
            'has_assignee_property': False,
            'missing_properties': [],
            'confidence_score': 0.0
        }
        
        if not database_properties:
            return validation_result
        
        # Property yang diharapkan untuk database task (lebih fleksibel)
        expected_properties = {
            'title': ['title', 'name', 'task', 'tugas', 'pekerjaan', 'uraian', 'judul', 'nama'],
            'status': ['status', 'state', 'progress', 'kondisi', 'status pekerjaan', 'keadaan', 'progres'],
            'date': ['date', 'tanggal', 'due date', 'deadline', 'waktu', 'tgl', 'jatuh tempo'],
            'assignee': ['assignee', 'pic', 'responsible', 'penanggung jawab', 'pemilik', 'karyawan', 'staff']
        }
        
        property_names = [prop.lower() for prop in database_properties.keys()]
        
        # Cek setiap property yang diharapkan
        for prop_type, possible_names in expected_properties.items():
            found = any(name in property_names for name in possible_names)
            
            if found:
                validation_result[f'has_{prop_type}_property'] = True
                validation_result['confidence_score'] += 0.25
            else:
                validation_result['missing_properties'].append(prop_type)
        
        # Database dianggap valid jika memiliki minimal title ATAU status
        # Lebih fleksibel - tidak harus memiliki keduanya
        if (validation_result['has_title_property'] or 
            validation_result['has_status_property'] or
            len(property_names) >= 2):  # Minimal 2 properties apapun
            validation_result['is_valid_task_database'] = True
            # Tambahkan confidence score jika memiliki lebih banyak properties
            if validation_result['has_title_property'] and validation_result['has_status_property']:
                validation_result['confidence_score'] += 0.2  # Bonus untuk memiliki keduanya
        
        # Jika tidak ada missing properties, set confidence tinggi
        if not validation_result['missing_properties']:
            validation_result['confidence_score'] = 1.0
        
        return validation_result
    
    def generate_database_metadata(self, database_id: str, database_title: str, 
                                 database_properties: Dict) -> Dict[str, any]:
        """
        Generate metadata lengkap untuk database
        
        Args:
            database_id (str): ID database Notion
            database_title (str): Judul database
            database_properties (Dict): Properties database
            
        Returns:
            Dict[str, any]: Metadata database
        """
        # Deteksi tipe database
        type_info = self.detect_database_type(database_title)
        
        # Validasi struktur
        structure_info = self.validate_database_structure(database_properties)
        
        # Generate metadata
        metadata = {
            'database_id': database_id,
            'database_title': database_title,
            'employee_name': type_info['employee_name'],
            'database_type': type_info['database_category'],
            'is_task_database': type_info['is_task_database'],
            'is_employee_specific': type_info['is_employee_specific'],
            'structure_valid': structure_info['is_valid_task_database'],
            'confidence_score': (type_info['confidence_score'] + 
                               structure_info['confidence_score']) / 2,
            'missing_properties': structure_info['missing_properties'],
            'detected_at': datetime.utcnow().isoformat(),
            'last_synced': None,
            'sync_enabled': True
        }
        
        return metadata
    
    def suggest_naming_convention(self, existing_databases: List[Dict]) -> Dict[str, any]:
        """
        Memberikan saran konvensi penamaan berdasarkan database yang ada
        
        Args:
            existing_databases (List[Dict]): List database yang sudah ada
            
        Returns:
            Dict[str, any]: Saran konvensi penamaan
        """
        suggestions = {
            'recommended_pattern': None,
            'pattern_frequency': {},
            'examples': [],
            'best_practices': []
        }
        
        if not existing_databases:
            return suggestions
        
        # Analisis pattern yang ada
        patterns = []
        for db in existing_databases:
            title = db.get('title', '')
            employee_name = self.extract_employee_name(title)
            
            if employee_name:
                # Ekstrak pattern dari judul
                pattern = self._extract_pattern_from_title(title, employee_name)
                patterns.append(pattern)
        
        # Hitung frekuensi pattern
        pattern_count = {}
        for pattern in patterns:
            pattern_count[pattern] = pattern_count.get(pattern, 0) + 1
        
        suggestions['pattern_frequency'] = pattern_count
        
        # Tentukan pattern yang paling sering digunakan
        if pattern_count:
            most_common_pattern = max(pattern_count, key=pattern_count.get)
            suggestions['recommended_pattern'] = most_common_pattern
        
        # Generate contoh
        suggestions['examples'] = [
            "Tasks - [Nama Karyawan]",
            "[Nama Karyawan]'s Tasks", 
            "[Nama Karyawan] Daily Task",
            "Daily Task [Nama Karyawan]"
        ]
        
        # Best practices
        suggestions['best_practices'] = [
            "Gunakan format yang konsisten untuk semua database karyawan",
            "Sertakan nama karyawan yang jelas dan mudah dikenali",
            "Hindari karakter khusus yang sulit diproses",
            "Gunakan bahasa yang konsisten (Indonesia atau Inggris)",
            "Sertakan kata kunci 'Task', 'Tugas', atau 'Pekerjaan'"
        ]
        
        return suggestions
    
    def _extract_pattern_from_title(self, title: str, employee_name: str) -> str:
        """
        Ekstrak pattern dari judul database
        
        Args:
            title (str): Judul database
            employee_name (str): Nama karyawan yang terdeteksi
            
        Returns:
            str: Pattern yang terdeteksi
        """
        # Ganti nama karyawan dengan placeholder
        pattern = title.replace(employee_name, '[Nama]')
        
        # Normalisasi pattern
        pattern = re.sub(r'\s+', ' ', pattern).strip()
        
        return pattern
