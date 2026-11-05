export interface HistoryItem {
  id?: number;
  from_status?: string | null;
  to_status: string;
  changed_at: string;
}

export interface RequestItem {
  public_id: string;
  title: string;
  description?: string | null;
  status: string;
  allowed_transitions: string[];
  version: number;
  created_at: string;
  updated_at: string;
  history?: HistoryItem[];
}

export interface RequestCreateInput {
  title: string;
  description?: string;
}

export interface RequestUpdateInput {
  title?: string;
  description?: string;
}

export interface AllowedTransitionsResponse {
  public_id: string;
  current_status: string;
  allowed: string[];
}

export interface SummaryResult {
  source: 'llm' | 'fallback';
  headline: string;
  highlights: string[];
  risks: string[];
  next_actions: string[];
  generated_at: string;
  cached?: boolean;
}

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}
