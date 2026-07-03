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
  mfa_required?: boolean;
  challenge_token?: string | null;
  available_methods?: string[];
  expires_in_seconds?: number | null;
}

export interface CurrentUser {
  actor_id: string;
  actor_type: 'tenant_user' | 'platform_admin' | string;
  tenant_id: string | null;
  email: string;
  display_name: string;
  email_verified: boolean;
  mfa_enabled: boolean;
  mfa_methods: string[];
  pending_mfa_setup: boolean;
  recovery_codes_remaining: number;
}

export interface StoredSession {
  realm: AuthRealm;
  tokens: TokenPair;
}

export interface PendingMfaChallenge {
  realm: AuthRealm;
  challengeToken: string;
  redirectTo: string;
  availableMethods: string[];
  expiresAt: number;
}
