import { ApiError } from './apiErrors';
import { clearStoredSession, getStoredSession, storeSession } from '../auth/authStorage';
import type { AuthRealm, TokenPair } from '../auth/authTypes';

const DEFAULT_IDENTITY_BASE_URL = 'http://localhost:8001';
const apiBaseUrl = (import.meta.env.VITE_IDENTITY_API_BASE_URL as string | undefined) ?? DEFAULT_IDENTITY_BASE_URL;

interface RequestOptions extends RequestInit {
  authRealm?: AuthRealm;
}

function resolvePath(path: string): string {
  return `${apiBaseUrl}${path}`;
}

async function parseResponse<T>(response: Response): Promise<T> {
  const text = await response.text();
  const body = text ? JSON.parse(text) as unknown : null;

  if (!response.ok) {
    const errorBody = typeof body === 'object' && body !== null && 'error' in body ? body as {
      error?: { code?: string; message?: string; field_errors?: Array<{ field: string; message: string }> };
    } : {};
    const fieldErrors = Object.fromEntries((errorBody.error?.field_errors ?? []).map((fieldError) => [fieldError.field, fieldError.message]));
    throw new ApiError(errorBody.error?.message ?? 'Request failed', {
      status: response.status,
      code: errorBody.error?.code ?? 'request_failed',
      fieldErrors,
    });
  }

  return body as T;
}

async function request<T>(path: string, options: RequestOptions = {}, retry = true): Promise<T> {
  const session = getStoredSession();
  const headers = new Headers(options.headers);
  headers.set('Accept', 'application/json');
  if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (options.authRealm && session?.realm === options.authRealm) {
    headers.set('Authorization', `Bearer ${session.tokens.access_token}`);
  }

  try {
    const response = await fetch(resolvePath(path), {
      ...options,
      headers,
      credentials: 'include',
    });

    if (response.status === 401 && retry && options.authRealm && session?.realm === options.authRealm) {
      const refreshed = await refreshTokens(options.authRealm, session.tokens.refresh_token);
      if (refreshed) return request<T>(path, options, false);
    }

    return parseResponse<T>(response);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw error;
  }
}

async function refreshTokens(realm: AuthRealm, refreshToken: string): Promise<TokenPair | null> {
  try {
    const basePath = realm === 'platform' ? '/v1/identity/platform-admin' : '/v1/identity';
    const tokens = await request<TokenPair>(`${basePath}/auth/refresh`, {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }, false);
    storeSession(realm, tokens);
    return tokens;
  } catch {
    clearStoredSession();
    return null;
  }
}

export const httpClient = {
  get: <T>(path: string, options?: RequestOptions) => request<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) => request<T>(path, {
    ...options,
    method: 'POST',
    body: body === undefined ? undefined : JSON.stringify(body),
  }),
};

export { apiBaseUrl };
