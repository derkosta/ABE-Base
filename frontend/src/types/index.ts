export interface User {
  id: string;
  username: string;
  email?: string;
  role: 'admin' | 'user';
  is_active: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Document {
  id: string;
  title: string;
  created: string;
  modified: string;
  content?: string;
  tags: string[];
  correspondent?: string;
  document_type?: string;
}

export interface SearchResult {
  doc_id: string;
  title: string;
  created: string;
  modified: string;
  snippet?: string;
  enumbers: string[];
  score?: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  enumbers_found: string[];
}

export interface AuditEntry {
  id: string;
  user: string;
  action: string;
  doc_id?: string;
  doc_title?: string;
  ip_address?: string;
  user_agent?: string;
  details?: string;
  created_at: string;
}

export interface UserCreate {
  username: string;
  email?: string;
  role: string;
}

export interface UserUpdate {
  email?: string;
  role?: string;
  is_active?: boolean;
}

export interface UserResponse {
  id: string;
  username: string;
  email?: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login_at?: string;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  total_documents: number;
  total_audits: number;
  recent_uploads: number;
  recent_downloads: number;
}

export interface HookSearchRequest {
  query?: string;
  model?: string;
  eNumber?: string;
  limit?: number;
}

export interface HookSearchResult {
  docId: string;
  title: string;
  snippet?: string;
  downloadUrl: string;
  enumbers: string[];
}
