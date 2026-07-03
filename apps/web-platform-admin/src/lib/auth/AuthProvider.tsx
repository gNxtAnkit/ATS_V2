import { ReactNode, createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { ApiError, platformAdminApi } from '../../api';
import type { CurrentPlatformAdmin, LoginResponse, MfaChallenge, TokenPair } from '../../types';

const SESSION_KEY = 'gnxthire.platformAdmin.session';
const MFA_CHALLENGE_KEY = 'gnxthire.platformAdmin.mfaChallenge';

interface StoredSession {
  tokens: TokenPair;
  admin: CurrentPlatformAdmin;
}

export interface AuthContextValue {
  admin: CurrentPlatformAdmin | null;
  tokens: TokenPair | null;
  loading: boolean;
  signIn(email: string, password: string): Promise<'authenticated' | 'mfa_required'>;
  completeLogin(response: LoginResponse): Promise<void>;
  refreshCurrentAdmin(): Promise<CurrentPlatformAdmin>;
  withFreshToken<T>(operation: (accessToken: string) => Promise<T>): Promise<T>;
  signOut(): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredSession(): StoredSession | null {
  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredSession;
  } catch {
    window.localStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export function saveMfaChallenge(response: LoginResponse): void {
  const challengeToken = response.challenge_token ?? response.mfa_challenge_token;
  if (!challengeToken) throw new Error('MFA challenge token was not returned by the server.');
  const expiresAt = response.expires_in_seconds ? Date.now() + response.expires_in_seconds * 1000 : null;
  const challenge: MfaChallenge = { token: challengeToken, availableMethods: response.available_methods, expiresAt };
  window.localStorage.setItem(MFA_CHALLENGE_KEY, JSON.stringify(challenge));
}

export function readMfaChallenge(): MfaChallenge | null {
  const raw = window.localStorage.getItem(MFA_CHALLENGE_KEY);
  if (!raw) return null;
  try {
    const challenge = JSON.parse(raw) as MfaChallenge;
    if (challenge.expiresAt && challenge.expiresAt <= Date.now()) {
      window.localStorage.removeItem(MFA_CHALLENGE_KEY);
      return null;
    }
    return challenge;
  } catch {
    window.localStorage.removeItem(MFA_CHALLENGE_KEY);
    return null;
  }
}

export function clearMfaChallenge(): void {
  window.localStorage.removeItem(MFA_CHALLENGE_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [tokens, setTokens] = useState<TokenPair | null>(() => readStoredSession()?.tokens ?? null);
  const [admin, setAdmin] = useState<CurrentPlatformAdmin | null>(() => readStoredSession()?.admin ?? null);
  const [loading, setLoading] = useState(true);

  const persistSession = useCallback((nextTokens: TokenPair, nextAdmin: CurrentPlatformAdmin) => {
    setTokens(nextTokens);
    setAdmin(nextAdmin);
    window.localStorage.setItem(SESSION_KEY, JSON.stringify({ tokens: nextTokens, admin: nextAdmin }));
  }, []);

  const clearSession = useCallback(() => {
    setTokens(null);
    setAdmin(null);
    window.localStorage.removeItem(SESSION_KEY);
  }, []);

  const completeLogin = useCallback(
    async (response: LoginResponse) => {
      if (!response.tokens) throw new Error('The server did not return session tokens.');
      const nextAdmin = await platformAdminApi.me(response.tokens.access_token);
      persistSession(response.tokens, nextAdmin);
      clearMfaChallenge();
    },
    [persistSession],
  );

  const signIn = useCallback(
    async (email: string, password: string) => {
      const response = await platformAdminApi.login(email, password);
      if (response.mfa_required) {
        saveMfaChallenge(response);
        return 'mfa_required' as const;
      }
      await completeLogin(response);
      return 'authenticated' as const;
    },
    [completeLogin],
  );

  const refreshCurrentAdmin = useCallback(async () => {
    if (!tokens) throw new Error('Your admin session has expired.');
    const nextAdmin = await platformAdminApi.me(tokens.access_token);
    persistSession(tokens, nextAdmin);
    return nextAdmin;
  }, [persistSession, tokens]);

  const refreshTokens = useCallback(
    async (currentTokens: TokenPair) => {
      const nextTokens = await platformAdminApi.refresh(currentTokens.refresh_token);
      const nextAdmin = await platformAdminApi.me(nextTokens.access_token);
      persistSession(nextTokens, nextAdmin);
      return nextTokens;
    },
    [persistSession],
  );

  const withFreshToken = useCallback(
    async <T,>(operation: (accessToken: string) => Promise<T>) => {
      if (!tokens) throw new Error('Your admin session has expired.');
      try {
        return await operation(tokens.access_token);
      } catch (error) {
        if (!(error instanceof ApiError) || error.status !== 401) throw error;
        const nextTokens = await refreshTokens(tokens);
        return operation(nextTokens.access_token);
      }
    },
    [refreshTokens, tokens],
  );

  const signOut = useCallback(async () => {
    const currentTokens = tokens;
    clearSession();
    clearMfaChallenge();
    if (currentTokens) {
      try {
        await platformAdminApi.logout(currentTokens.refresh_token, currentTokens.access_token);
      } catch {
        // Local session is already cleared; logout stays idempotent for the user.
      }
    }
  }, [clearSession, tokens]);

  useEffect(() => {
    let active = true;
    const stored = readStoredSession();

    async function validateSession() {
      if (!stored) {
        setLoading(false);
        return;
      }
      try {
        const nextAdmin = await platformAdminApi.me(stored.tokens.access_token);
        if (active) persistSession(stored.tokens, nextAdmin);
      } catch {
        try {
          const nextTokens = await platformAdminApi.refresh(stored.tokens.refresh_token);
          const nextAdmin = await platformAdminApi.me(nextTokens.access_token);
          if (active) persistSession(nextTokens, nextAdmin);
        } catch {
          if (active) clearSession();
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void validateSession();
    return () => {
      active = false;
    };
  }, [clearSession, persistSession]);

  const value = useMemo<AuthContextValue>(
    () => ({ admin, tokens, loading, signIn, completeLogin, refreshCurrentAdmin, withFreshToken, signOut }),
    [admin, completeLogin, loading, refreshCurrentAdmin, signIn, signOut, tokens, withFreshToken],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('AuthContext is not available.');
  return value;
}
