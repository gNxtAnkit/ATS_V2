export type AuthRealm = 'tenant' | 'platform';

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  expires_in_seconds: number;
}

export interface LoginResponse {
  status: 'authenticated' | 'mfa_required' | string;
  tokens: TokenPair | null;
  mfa_challenge_token: string | null;
}

export interface CurrentUser {
  actor_id: string;
  actor_type: 'tenant_user' | 'platform_admin' | string;
  tenant_id: string | null;
  email: string;
  display_name: string;
  email_verified: boolean;
  mfa_enabled: boolean;
  status: string;
  created_at: string;
  last_login_at: string | null;
  last_login_ip: string | null;
}

export interface StoredSession {
  realm: AuthRealm;
  tokens: TokenPair;
}

export interface PendingMfaChallenge {
  realm: AuthRealm;
  challengeToken: string;
  redirectTo: string;
}
