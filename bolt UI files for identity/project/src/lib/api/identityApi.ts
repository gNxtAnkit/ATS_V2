import { httpClient } from './httpClient';
import type { AuthRealm, CurrentUser, LoginResponse } from '../auth/authTypes';

const basePathByRealm: Record<AuthRealm, string> = {
  tenant: '/v1/identity',
  platform: '/v1/identity/platform-admin',
};

export interface MessageResponse {
  message: string;
}

export interface TotpSetupResponse {
  provisioning_uri: string;
  manual_entry_secret: string;
}

export interface TotpConfirmResponse {
  recovery_codes: string[];
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

function basePath(realm: AuthRealm): string {
  return basePathByRealm[realm];
}

export const identityApi = {
  login: (realm: AuthRealm, email: string, password: string) =>
    httpClient.post<LoginResponse>(`${basePath(realm)}/auth/login`, { email, password }),
  forgotPassword: (realm: AuthRealm, email: string) =>
    httpClient.post<MessageResponse>(`${basePath(realm)}/auth/forgot-password`, { email }),
  resetPassword: (realm: AuthRealm, token: string, newPassword: string, confirmPassword: string) =>
    httpClient.post<MessageResponse>(`${basePath(realm)}/auth/reset-password`, {
      token,
      new_password: newPassword,
      confirm_password: confirmPassword,
    }),
  requestEmailVerification: (realm: AuthRealm, email: string) =>
    httpClient.post<MessageResponse>(`${basePath(realm)}/auth/request-email-verification`, { email }),
  verifyEmail: (realm: AuthRealm, token: string) =>
    httpClient.post<MessageResponse>(`${basePath(realm)}/auth/verify-email`, { token }),
  verifyMfa: (realm: AuthRealm, challengeToken: string, code: string) =>
    httpClient.post<LoginResponse>(`${basePath(realm)}/mfa/totp/verify`, {
      mfa_challenge_token: challengeToken,
      code,
    }),
  verifyMfaRecoveryCode: (realm: AuthRealm, challengeToken: string, recoveryCode: string) =>
    httpClient.post<LoginResponse>(`${basePath(realm)}/mfa/recovery-code/verify`, {
      mfa_challenge_token: challengeToken,
      recovery_code: recoveryCode,
    }),
  passwordPolicy: (realm: AuthRealm) =>
    httpClient.get<PasswordPolicyResponse>(`${basePath(realm)}/auth/password-policy`),
  me: (realm: AuthRealm) =>
    httpClient.get<CurrentUser>(`${basePath(realm)}/auth/me`, { authRealm: realm }),
  logout: (realm: AuthRealm, refreshToken?: string) =>
    httpClient.post<MessageResponse>(`${basePath(realm)}/auth/logout`, { refresh_token: refreshToken ?? null }),
  startMfaSetup: (realm: AuthRealm) =>
    httpClient.post<TotpSetupResponse>(`${basePath(realm)}/mfa/totp/setup`, undefined, { authRealm: realm }),
  confirmMfaSetup: (realm: AuthRealm, code: string) =>
    httpClient.post<TotpConfirmResponse>(`${basePath(realm)}/mfa/totp/confirm`, { code }, { authRealm: realm }),
  changePassword: (realm: AuthRealm, currentPassword: string, newPassword: string, confirmPassword: string) =>
    httpClient.post<MessageResponse>(`${basePath(realm)}/auth/change-password`, {
      current_password: currentPassword,
      new_password: newPassword,
      confirm_password: confirmPassword,
    }, { authRealm: realm }),
  disableMfa: (realm: AuthRealm, password: string) =>
    httpClient.post<MessageResponse>(`${basePath(realm)}/mfa/disable`, { password }, { authRealm: realm }),
};
