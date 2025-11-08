#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Chunking Service untuk Gemini Embeddings

Memotong teks menjadi potongan yang dioptimalkan untuk Bahasa Indonesia dan semantic search.
Menggunakan strategi chunking yang lebih cerdas untuk hasil Gemini Embeddings yang lebih baik.
"""

from typing import List, Dict, Any, Optional
import hashlib
import re
import logging

logger = logging.getLogger(__name__)

# Konfigurasi optimal untuk Gemini Embeddings
DEFAULT_CHUNK_CHARS = 1200  # Naik dari 1600 ke 1200 untuk konteks lebih fokus
DEFAULT_OVERLAP_CHARS = 300  # Naik dari 200 ke 300 untuk overlap yang lebih baik
MIN_CHUNK_CHARS = 20  # Minimal 20 karakter untuk chunk yang meaningful
MAX_CHUNK_CHARS = 2000  # Maksimal 2000 karakter

# Stopwords Bahasa Indonesia untuk keyword extraction
INDONESIAN_STOPWORDS = [
    'yang', 'dan', 'di', 'ke', 'dari', 'dengan', 'untuk', 'pada', 'adalah', 'atau',
    'ini', 'itu', 'akan', 'telah', 'sudah', 'belum', 'tidak', 'bukan', 'jika', 'karena',
    'sehingga', 'namun', 'tetapi', 'oleh', 'dalam', 'atas', 'bawah', 'antara', 'sejak',
    'hingga', 'selama', 'ketika', 'sementara', 'meskipun', 'walaupun', 'agar', 'supaya',
    'maka', 'jadi', 'sebab', 'karena', 'sehingga', 'maka', 'jadi', 'sebab', 'karena'
]

# Pola untuk istilah legal dan bisnis yang penting
LEGAL_PATTERNS = [
    r'PT\.?\s+[A-Za-z\s]+',  # PT. Nama Perusahaan
    r'CV\.?\s+[A-Za-z\s]+',  # CV. Nama Perusahaan
    r'UD\.?\s+[A-Za-z\s]+',  # UD. Nama Perusahaan
    r'KBLI\s+\d{4}',         # KBLI 1234
    r'NIB\s+[A-Za-z0-9]+',  # NIB
    r'TDP\s+[A-Za-z0-9]+',   # TDP
    r'NPWP\s+[0-9\.\-]+',    # NPWP
    r'Akta\s+[A-Za-z0-9]+',  # Akta
    r'Notaris\s+[A-Za-z\s]+', # Notaris
    r'Modal\s+[A-Za-z0-9\s]+', # Modal
    r'Direktur\s+[A-Za-z\s]+', # Direktur
    r'Komisaris\s+[A-Za-z\s]+' # Komisaris
]

# Pola untuk alamat
ADDRESS_PATTERNS = [
    r'Jl\.?\s+[A-Za-z0-9\s]+',  # Jalan
    r'RT\s+\d+',                # RT
    r'RW\s+\d+',                # RW
    r'Kel\.?\s+[A-Za-z\s]+',    # Kelurahan
    r'Kec\.?\s+[A-Za-z\s]+',    # Kecamatan
    r'Kota\s+[A-Za-z\s]+',      # Kota
    r'Provinsi\s+[A-Za-z\s]+'   # Provinsi
]


def approximate_token_count(text: str) -> int:
    """Estimasi token count yang lebih akurat untuk Bahasa Indonesia"""
    # Bahasa Indonesia cenderung memiliki token yang lebih pendek
    return max(1, len(text) // 3)  # Ubah dari 4 ke 3 untuk estimasi yang lebih akurat


def preprocess_text(text: str) -> str:
    """Preprocess text untuk Bahasa Indonesia"""
    try:
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Normalize common variations
        text = re.sub(r'PT\.?\s*', 'PT ', text, flags=re.IGNORECASE)
        text = re.sub(r'CV\.?\s*', 'CV ', text, flags=re.IGNORECASE)
        text = re.sub(r'UD\.?\s*', 'UD ', text, flags=re.IGNORECASE)
        text = re.sub(r'Jl\.?\s*', 'Jalan ', text, flags=re.IGNORECASE)
        text = re.sub(r'RT\s*', 'RT ', text, flags=re.IGNORECASE)
        text = re.sub(r'RW\s*', 'RW ', text, flags=re.IGNORECASE)
        
        return text.strip()
    except Exception as e:
        logger.error(f"Error preprocessing text: {e}")
        return text


def extract_entities(text: str) -> List[str]:
    """Extract entities penting dari text"""
    try:
        entities = []
        
        # Extract legal entities
        for pattern in LEGAL_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        # Extract address entities
        for pattern in ADDRESS_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        # Remove duplicates
        entities = list(set(entities))
        return entities
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        return []


def extract_keywords(text: str) -> List[str]:
    """Extract keywords dari text"""
    try:
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter stopwords
        keywords = [word for word in words if word not in INDONESIAN_STOPWORDS]
        
        # Count frequency
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top keywords
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_keywords[:10]]
    except Exception as e:
        logger.error(f"Error extracting keywords: {e}")
        return []


def calculate_importance_score(text: str) -> float:
    """Hitung skor penting dari chunk"""
    try:
        score = 0.0
        
        # Boost untuk istilah legal
        legal_keywords = [
            'akta', 'notaris', 'siup', 'tdp', 'npwp', 'kbli', 'modal', 'direktur', 
            'komisaris', 'perusahaan', 'pendirian', 'perubahan', 'perpanjangan',
            'izin', 'lisensi', 'sertifikat', 'legalitas', 'dokumen', 'surat'
        ]
        
        for keyword in legal_keywords:
            if keyword.lower() in text.lower():
                score += 0.3
        
        # Boost untuk entities
        entities = extract_entities(text)
        score += len(entities) * 0.1
        
        # Boost untuk angka/nomor (biasanya penting)
        numbers = re.findall(r'\d+', text)
        score += len(numbers) * 0.05
        
        # Boost untuk kata kunci penting
        important_keywords = ['nama', 'alamat', 'direktur', 'komisaris', 'modal', 'akta', 'notaris']
        for keyword in important_keywords:
            if keyword.lower() in text.lower():
                score += 0.2
        
        # Normalize score
        score = min(score, 1.0)
        return score
    except Exception as e:
        logger.error(f"Error calculating importance score: {e}")
        return 0.0


def find_best_split_position(text: str, max_chars: int) -> int:
    """Temukan posisi terbaik untuk memotong text"""
    try:
        if len(text) <= max_chars:
            return len(text)
        
        # Cari posisi terakhir dari separator yang umum (prioritas tinggi ke rendah)
        separators = [
            '\n\n',  # Paragraf
            '. ',    # Akhir kalimat
            '! ',    # Akhir kalimat
            '? ',    # Akhir kalimat
            '\n',    # Baris baru
            ', ',    # Koma
            '; ',    # Titik koma
            ' '      # Spasi
        ]
        
        best_pos = max_chars
        
        for sep in separators:
            pos = text.rfind(sep, 0, max_chars)
            if pos > max_chars * 0.7:  # Minimal 70% dari max size
                best_pos = pos + len(sep)
                break
        
        return best_pos
    except Exception as e:
        logger.error(f"Error finding split position: {e}")
        return max_chars


def chunk_text(pages: List[Dict[str, Any]],
               chunk_chars: int = DEFAULT_CHUNK_CHARS,
               overlap_chars: int = DEFAULT_OVERLAP_CHARS) -> List[Dict[str, Any]]:
    """Enhanced chunking untuk Gemini Embeddings dengan optimasi Bahasa Indonesia.
    
    Args:
        pages: List halaman dengan text
        chunk_chars: Ukuran maksimal chunk (default: 1200)
        overlap_chars: Ukuran overlap (default: 300)
    
    Returns:
        List chunk dict dengan metadata lengkap untuk semantic search
    """
    chunks: List[Dict[str, Any]] = []

    # Gabungkan semua halaman dengan penanda halaman
    segments: List[Dict[str, Any]] = []
    for idx, p in enumerate(pages, start=1):
        t = p.get('text', '')
        if not t:
            continue
        
        # Preprocess text untuk Bahasa Indonesia
        processed_text = preprocess_text(t)
        segments.append({'page': idx, 'text': processed_text})

    if not segments:
        return chunks

    # Enhanced chunking dengan strategi yang lebih cerdas
    buffer_text = ''
    buffer_start_page = segments[0]['page']
    buffer_end_page = segments[0]['page']
    chunk_index = 0

    for seg in segments:
        page = seg['page']
        text = seg['text']
        start = 0
        
        while start < len(text):
            remaining = text[start:]
            space_left = max(0, chunk_chars - len(buffer_text))
            
            # Ambil teks yang tersisa
            to_take = remaining[:space_left]
            buffer_text += to_take
            buffer_end_page = page
            start += len(to_take)

            # Jika buffer sudah cukup besar, buat chunk
            if len(buffer_text) >= chunk_chars:
                # Cari posisi terbaik untuk memotong
                best_split_pos = find_best_split_position(buffer_text, chunk_chars)
                
                # Ambil chunk dengan posisi terbaik
                chunk_text = buffer_text[:best_split_pos]
                
                # Validasi chunk minimal
                if len(chunk_text.strip()) >= MIN_CHUNK_CHARS:
                    # Enrich chunk dengan metadata
                    enriched_chunk = create_enriched_chunk(
                        chunk_text, buffer_start_page, buffer_end_page, 
                        chunk_index, page
                    )
                    chunks.append(enriched_chunk)
                    chunk_index += 1

                # Overlap dengan strategi yang lebih baik
                overlap_text = get_smart_overlap(buffer_text, overlap_chars)
                buffer_text = overlap_text
                buffer_start_page = buffer_end_page

    # Sisa buffer
    if buffer_text.strip() and len(buffer_text.strip()) >= MIN_CHUNK_CHARS:
        enriched_chunk = create_enriched_chunk(
            buffer_text, buffer_start_page, buffer_end_page, 
            chunk_index, buffer_end_page
        )
        chunks.append(enriched_chunk)

    # Sort chunks berdasarkan importance score
    chunks.sort(key=lambda x: x.get('importance_score', 0), reverse=True)
    
    logger.info(f"Created {len(chunks)} enhanced chunks with average importance: {sum(c.get('importance_score', 0) for c in chunks) / len(chunks) if chunks else 0:.2f}")
    
    return chunks


def create_enriched_chunk(text: str, page_from: int, page_to: int, 
                         chunk_index: int, current_page: int) -> Dict[str, Any]:
    """Buat chunk dengan metadata yang diperkaya untuk semantic search"""
    try:
        # Basic chunk info
        tokens = approximate_token_count(text)
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        
        # Extract metadata
        entities = extract_entities(text)
        keywords = extract_keywords(text)
        importance_score = calculate_importance_score(text)
        
        # Calculate additional metrics
        word_count = len(text.split())
        sentence_count = len(re.split(r'[.!?]+', text))
        
        # Determine chunk type based on content
        chunk_type = determine_chunk_type(text)
        
        return {
            'text': text,
            'page_from': page_from,
            'page_to': page_to,
            'chunk_index': chunk_index,
            'tokens': tokens,
            'text_hash': text_hash,
            
            # Enhanced metadata untuk semantic search
            'entities': entities,
            'keywords': keywords,
            'importance_score': importance_score,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'chunk_type': chunk_type,
            
            # Metadata untuk Gemini Embeddings
            'is_legal_document': any(keyword in text.lower() for keyword in ['akta', 'notaris', 'siup', 'tdp']),
            'has_company_info': any(keyword in text.lower() for keyword in ['pt', 'cv', 'ud', 'perusahaan']),
            'has_address_info': any(keyword in text.lower() for keyword in ['jalan', 'rt', 'rw', 'kelurahan']),
            'has_financial_info': any(keyword in text.lower() for keyword in ['modal', 'rupiah', 'uang', 'biaya']),
            
            # Timestamp
            'created_at': get_timestamp()
        }
    except Exception as e:
        logger.error(f"Error creating enriched chunk: {e}")
        # Fallback ke chunk sederhana
        return {
            'text': text,
            'page_from': page_from,
            'page_to': page_to,
            'chunk_index': chunk_index,
            'tokens': approximate_token_count(text),
            'text_hash': hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'importance_score': 0.0,
            'entities': [],
            'keywords': [],
            'chunk_type': 'unknown'
        }


def get_smart_overlap(text: str, overlap_chars: int) -> str:
    """Ambil overlap text dengan strategi yang lebih cerdas"""
    try:
        if len(text) <= overlap_chars:
            return text
        
        # Ambil dari akhir teks
        overlap_text = text[-overlap_chars:]
        
        # Cari posisi yang tepat (akhir kalimat atau paragraf)
        separators = ['\n\n', '. ', '! ', '? ', '\n']
        best_pos = 0
        
        for sep in separators:
            pos = overlap_text.find(sep)
            if pos > best_pos:
                best_pos = pos + len(sep)
        
        if best_pos > 0:
            overlap_text = overlap_text[best_pos:]
        
        return overlap_text.strip()
    except Exception as e:
        logger.error(f"Error getting smart overlap: {e}")
        return text[-overlap_chars:] if len(text) > overlap_chars else text


def determine_chunk_type(text: str) -> str:
    """Tentukan tipe chunk berdasarkan konten"""
    try:
        text_lower = text.lower()
        
        # Legal document
        if any(keyword in text_lower for keyword in ['akta', 'notaris', 'siup', 'tdp', 'npwp']):
            return 'legal'
        
        # Company info
        if any(keyword in text_lower for keyword in ['pt', 'cv', 'ud', 'perusahaan', 'direktur', 'komisaris']):
            return 'company'
        
        # Address info
        if any(keyword in text_lower for keyword in ['jalan', 'rt', 'rw', 'kelurahan', 'kecamatan', 'kota']):
            return 'address'
        
        # Financial info
        if any(keyword in text_lower for keyword in ['modal', 'rupiah', 'uang', 'biaya', 'harga']):
            return 'financial'
        
        # General content
        return 'general'
    except Exception as e:
        logger.error(f"Error determining chunk type: {e}")
        return 'unknown'


def get_timestamp() -> str:
    """Get current timestamp"""
    from datetime import datetime
    return datetime.now().isoformat()


