// Identity service (platform-admin realm) contracts — see
// services/identity/src/gnxthire_identity/{schemas.py,platform_admin/schemas.py}
export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in_seconds: number;
}

export interface LoginResponse {
  status: string;
  tokens: TokenPair | null;
  mfa_challenge_token?: string | null;
  mfa_required: boolean;
  challenge_token?: string | null;
  available_methods: string[];
  expires_in_seconds?: number | null;
}

export interface CurrentPlatformAdmin {
  actor_id: string;
  actor_type: 'platform_admin';
  tenant_id: null;
  email: string;
  display_name: string;
  email_verified: boolean;
  mfa_enabled: boolean;
  mfa_methods: string[];
  pending_mfa_setup: boolean;
  recovery_codes_remaining: number;
}

export interface MessageResponse {
  message: string;
}

export interface PasswordPolicyResponse {
  min_length: number;
  max_length: number;
  require_uppercase: boolean;
  require_lowercase: boolean;
  require_number: boolean;
  require_special: boolean;
  prevent_email_similarity: boolean;
}

export interface TotpSetupResponse {
  provisioning_uri: string;
  manual_entry_secret: string;
}

export interface TotpConfirmResponse {
  recovery_codes: string[];
}

export interface RecoveryCodesResponse {
  recovery_codes: string[];
}

export interface PlatformUser {
  id: string;
  email: string;
  display_name: string;
  status: string;
  email_verified: boolean;
  mfa_enabled: boolean;
  mfa_required: boolean;
  last_login_at: string | null;
}

export interface CursorPage<T> {
  data: T[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface MfaChallenge {
  token: string;
  availableMethods: string[];
  expiresAt: number | null;
}

// platform-admin service envelopes — see services/platform-admin/.../schemas.py
export interface PlatformEnvelope<T = Record<string, unknown>> {
  data: T;
  meta: { request_id: string };
}

export interface PlatformListEnvelope<T = Record<string, unknown>> {
  data: T[];
  page: { limit: number; next_cursor: string | null; has_more: boolean };
  meta: { request_id: string };
}
