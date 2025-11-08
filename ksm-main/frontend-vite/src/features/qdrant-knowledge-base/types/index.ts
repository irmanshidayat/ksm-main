/**
 * Qdrant Knowledge Base Types
 */

export interface Document {
  id: number;
  company_id: string;
  original_name: string;
  title: string;
  description: string;
  status: 'uploaded' | 'processing' | 'ready' | 'failed';
  total_pages: number;
  vector_count: number;
  chunks_count: number;
  size_bytes: number;
  created_at: string;
  updated_at: string;
  collection: string;
}

export interface Collection {
  name: string;
  status: string;
  vectors_count: number;
  indexed_vectors_count: number;
  points_count: number;
  config?: {
    vector_size: number;
    distance: string;
  };
}

export interface SearchResult {
  id: string;
  score: number;
  payload: {
    document_id: number;
    chunk_id: number;
    chunk_index: number;
    text: string;
    company_id: string;
    created_at: string;
  };
}

export interface Statistics {
  total_documents: number;
  total_collections: number;
  total_vectors: number;
  total_storage_mb: number;
  documents_by_status: {
    uploaded: number;
    processing: number;
    ready: number;
    failed: number;
  };
}

export interface DocumentsQueryParams {
  company_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

export interface CreateCollectionRequest {
  collection_name: string;
  vector_size?: number;
  distance?: string;
}

export interface UploadDocumentRequest {
  filename: string;
  base64_content: string;
  company_id: string;
  title: string;
  description?: string;
  collection: string;
}

export interface SearchRequest {
  query: string;
  collection_name: string;
  limit?: number;
  score_threshold?: number;
}

