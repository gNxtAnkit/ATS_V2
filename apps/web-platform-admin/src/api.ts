import type {
  CursorPage,
  CurrentPlatformAdmin,
  LoginResponse,
  MessageResponse,
  PasswordPolicyResponse,
  PlatformEnvelope,
  PlatformListEnvelope,
  PlatformUser,
  RecoveryCodesResponse,
  TokenPair,
  TotpConfirmResponse,
  TotpSetupResponse,
} from './types';

// Base URLs come from environment config (see .env.example) — never hardcoded.
const IDENTITY_API_BASE_URL = (import.meta.env.VITE_IDENTITY_API_BASE_URL ?? 'http://localhost:8001').replace(/\/$/, '');
const PLATFORM_ADMIN_API_BASE_URL = (import.meta.env.VITE_PLATFORM_ADMIN_API_BASE_URL ?? 'http://localhost:8002').replace(/\/$/, '');

// Identity service, platform-admin realm (see services/identity/.../api/platform_routes.py)
const IDENTITY_PLATFORM_ADMIN_BASE = '/v1/identity/platform-admin';
// Identity service, platform-admin user management (see .../api/platform_user_routes.py)
const IDENTITY_PLATFORM_USERS_BASE = '/v1/identity/platform-users';

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

interface RequestOptions extends RequestInit {
  accessToken?: string | null;
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type') ?? '';
  const payload = contentType.includes('application/json') ? await response.json() : null;

  if (!response.ok) {
    const message =
      typeof payload?.detail === 'string'
        ? payload.detail
        : typeof payload?.error?.message === 'string'
          ? payload.error.message
          : typeof payload?.message === 'string'
            ? payload.message
            : 'The request could not be completed.';
    throw new ApiError(message, response.status);
  }

  return payload as T;
}

async function requestJson<T>(baseUrl: string, path: string, options: RequestOptions = {}): Promise<T> {
  const { accessToken, headers, body, ...requestOptions } = options;
  const requestHeaders = new Headers(headers);
  requestHeaders.set('Accept', 'application/json');
  if (body && !requestHeaders.has('Content-Type')) requestHeaders.set('Content-Type', 'application/json');
  if (accessToken) requestHeaders.set('Authorization', `Bearer ${accessToken}`);

  const response = await fetch(`${baseUrl}${path}`, { ...requestOptions, body, headers: requestHeaders });
  return parseJsonResponse<T>(response);
}

/** User-safe error copy, mirroring the pattern used by the identity Bolt UI. */
export function toSafeUserMessage(error: unknown, context?: 'login' | 'mfa' | 'reset' | 'verify'): string {
  if (!(error instanceof ApiError)) return 'We could not reach the server. Please check your connection and try again.';
  if (error.status === 429) return 'Too many attempts. Please wait a few minutes and try again.';
  if (context === 'reset' && error.status === 401) return 'This password reset link is invalid or has expired.';
  if (context === 'verify' && error.status === 401) return 'This verification link is invalid, expired, or already used.';
  if (context === 'mfa' && error.status === 401) return 'Invalid code. Please check your authenticator app and try again.';
  if (error.status === 401 && context === 'login') return 'The email or password you entered is incorrect. Please try again.';
  if (error.status === 401 || error.status === 403) return 'Access is restricted for this account. Contact your administrator.';
  if (error.status === 400) return error.message || 'Please check the form and try again.';
  if (error.status >= 500) return 'Something went wrong on our side. Please try again.';
  return error.message || 'We could not complete that request. Please try again.';
}

export const platformAdminApi = {
  login(email: string, password: string) {
    return requestJson<LoginResponse>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/auth/login`, {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },
  passwordPolicy() {
    return requestJson<PasswordPolicyResponse>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/auth/password-policy`);
  },
  refresh(refreshToken: string) {
    return requestJson<TokenPair>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/auth/refresh`, {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  },
  logout(refreshToken: string | null, accessToken: string | null) {
    return requestJson<MessageResponse>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/auth/logout`, {
      method: 'POST',
      accessToken,
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  },
  me(accessToken: string) {
    return requestJson<CurrentPlatformAdmin>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/auth/me`, { accessToken });
  },
  forgotPassword(email: string) {
    return requestJson<MessageResponse>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/auth/forgot-password`, {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  },
  resetPassword(token: string, newPassword: string, confirmPassword: string) {
    return requestJson<MessageResponse>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/auth/reset-password`, {
      method: 'POST',
      body: JSON.stringify({ token, new_password: newPassword, confirm_password: confirmPassword }),
    });
  },
  requestEmailVerification(email: string) {
    return requestJson<MessageResponse>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/auth/request-email-verification`, {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  },
  verifyEmail(token: string) {
    return requestJson<MessageResponse>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/auth/verify-email`, {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  },
  changePassword(accessToken: string, currentPassword: string, newPassword: string, confirmPassword: string) {
    return requestJson<MessageResponse>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/auth/change-password`, {
      method: 'POST',
      accessToken,
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword, confirm_password: confirmPassword }),
    });
  },
  setupTotp(accessToken: string) {
    return requestJson<TotpSetupResponse>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/mfa/totp/setup`, { method: 'POST', accessToken });
  },
  confirmTotp(accessToken: string, code: string) {
    return requestJson<TotpConfirmResponse>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/mfa/totp/confirm`, {
      method: 'POST',
      accessToken,
      body: JSON.stringify({ code }),
    });
  },
  verifyTotp(challengeToken: string, code: string) {
    return requestJson<LoginResponse>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/mfa/totp/verify`, {
      method: 'POST',
      body: JSON.stringify({ mfa_challenge_token: challengeToken, code }),
    });
  },
  verifyRecoveryCode(challengeToken: string, recoveryCode: string) {
    return requestJson<LoginResponse>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/mfa/recovery-code/verify`, {
      method: 'POST',
      body: JSON.stringify({ mfa_challenge_token: challengeToken, recovery_code: recoveryCode }),
    });
  },
  regenerateRecoveryCodes(accessToken: string, password: string) {
    return requestJson<RecoveryCodesResponse>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/mfa/recovery-codes/regenerate`, {
      method: 'POST',
      accessToken,
      body: JSON.stringify({ password }),
    });
  },
  disableMfa(accessToken: string, password: string) {
    return requestJson<MessageResponse>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_ADMIN_BASE}/mfa/disable`, {
      method: 'POST',
      accessToken,
      body: JSON.stringify({ password }),
    });
  },
};

export const platformUsersApi = {
  list(accessToken: string, cursor: string | null = null) {
    const search = new URLSearchParams({ limit: '50' });
    if (cursor) search.set('cursor', cursor);
    return requestJson<CursorPage<PlatformUser>>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_USERS_BASE}?${search.toString()}`, { accessToken });
  },
  create(accessToken: string, email: string, displayName: string) {
    return requestJson<PlatformUser>(IDENTITY_API_BASE_URL, IDENTITY_PLATFORM_USERS_BASE, {
      method: 'POST',
      accessToken,
      body: JSON.stringify({ email, display_name: displayName }),
    });
  },
  update(accessToken: string, userId: string, displayName: string) {
    return requestJson<PlatformUser>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_USERS_BASE}/${userId}`, {
      method: 'PATCH',
      accessToken,
      body: JSON.stringify({ display_name: displayName }),
    });
  },
  action(accessToken: string, userId: string, action: 'activate' | 'deactivate' | 'lock' | 'unlock' | 'require-password-reset' | 'require-mfa') {
    return requestJson<PlatformUser>(IDENTITY_API_BASE_URL, `${IDENTITY_PLATFORM_USERS_BASE}/${userId}/${action}`, {
      method: 'POST',
      accessToken,
    });
  },
};

/** Generic client for the platform-admin control-plane service (tenants, plans, ...). */
export const platformControlApi = {
  list<T = Record<string, unknown>>(accessToken: string, path: string, query: Record<string, string> = {}) {
    const search = new URLSearchParams(query);
    const suffix = search.toString() ? `?${search.toString()}` : '';
    return requestJson<PlatformListEnvelope<T>>(PLATFORM_ADMIN_API_BASE_URL, `${path}${suffix}`, { accessToken });
  },
  get<T = Record<string, unknown>>(accessToken: string, path: string) {
    return requestJson<PlatformEnvelope<T>>(PLATFORM_ADMIN_API_BASE_URL, path, { accessToken });
  },
  post<T = Record<string, unknown>>(accessToken: string, path: string, body?: Record<string, unknown>) {
    return requestJson<PlatformEnvelope<T>>(PLATFORM_ADMIN_API_BASE_URL, path, {
      method: 'POST',
      accessToken,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  },
  patch<T = Record<string, unknown>>(accessToken: string, path: string, body: Record<string, unknown>) {
    return requestJson<PlatformEnvelope<T>>(PLATFORM_ADMIN_API_BASE_URL, path, { method: 'PATCH', accessToken, body: JSON.stringify(body) });
  },
  put<T = Record<string, unknown>>(accessToken: string, path: string, body: Record<string, unknown>) {
    return requestJson<PlatformEnvelope<T>>(PLATFORM_ADMIN_API_BASE_URL, path, { method: 'PUT', accessToken, body: JSON.stringify(body) });
  },
  delete<T = Record<string, unknown>>(accessToken: string, path: string) {
    return requestJson<PlatformEnvelope<T>>(PLATFORM_ADMIN_API_BASE_URL, path, { method: 'DELETE', accessToken });
  },
};
