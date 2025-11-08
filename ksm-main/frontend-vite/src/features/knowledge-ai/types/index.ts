/**
 * Knowledge AI Types
 */

export interface ChatMessage {
  id: string;
  type: 'user' | 'ai';
  message: string;
  timestamp: Date;
  confidence?: string;
  sourceFiles?: string[];
}

export interface SearchResult {
  file_id: number;
  filename: string;
  description: string;
  category: string;
  priority_level: string;
  relevance_score: number;
}

export interface KnowledgeAIStats {
  total_files: number;
  total_categories: number;
  high_priority_files: number;
  recent_files: number;
}

export interface ChatRequest {
  message: string;
  conversation_history?: Array<{
    role: 'user' | 'ai';
    content: string;
  }>;
  context?: Record<string, any>;
}

export interface ChatResponse {
  success: boolean;
  message: string;
  confidence?: string;
  source_files?: string[];
}

export interface SearchRequest {
  query: string;
}

export interface SearchResponse {
  success: boolean;
  data: {
    results: SearchResult[];
  };
}

