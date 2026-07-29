export interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  created_at: string;
}

export type EmbeddingStatus = 'pending' | 'processing' | 'done' | 'failed';

export interface Book {
  id: string;
  title: string;
  author?: string;
  language?: string;
  genre?: string;
  country?: string;
  cover_url?: string;
  file_url?: string;
  page_count: number;
  file_size_bytes: number;
  tags: string[];
  embedding_status: EmbeddingStatus;
  embedding_chunk_count: number;
  created_at: string;
}

export interface SourceCitation {
  book_title?: string;
  book_id?: string;
  chunk_index?: number;
  text_snippet?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: SourceCitation[];
  timestamp: string;
}

export interface ChatSession {
  session_id: string;
  title: string;
  book_ids: string[];
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

export interface BookRecommendation {
  title: string;
  author?: string;
  cover_url?: string;
  download_url?: string;
  source: 'open_library' | 'gutenberg';
  open_library_key?: string;
  gutenberg_id?: number;
}
