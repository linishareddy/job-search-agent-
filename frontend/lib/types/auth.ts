export interface User {
  id: string;
  email: string;
  name?: string | null;
  is_active: boolean;
  email_enabled: boolean;
  auto_apply_enabled: boolean;
  auto_apply_min_score: number;
  auto_apply_resume_id?: string | null;
  auto_apply_max_per_run: number;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface UserPreferencesUpdate {
  name?: string;
  email_enabled?: boolean;
  auto_apply_enabled?: boolean;
  auto_apply_min_score?: number;
  auto_apply_resume_id?: string | null;
  auto_apply_max_per_run?: number;
}
