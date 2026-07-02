/* eslint-disable react-refresh/only-export-components */
import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { identityApi } from '../api/identityApi';
import { clearStoredSession, getStoredSession, storeSession } from './authStorage';
import type { AuthRealm, CurrentUser, TokenPair } from './authTypes';

interface AuthSessionContextValue {
  status: 'loading' | 'authenticated' | 'anonymous';
  realm: AuthRealm | null;
  user: CurrentUser | null;
  establishSession: (realm: AuthRealm, tokens: TokenPair) => Promise<void>;
  refreshCurrentSession: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthSessionContext = createContext<AuthSessionContextValue | null>(null);

export function AuthSessionProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthSessionContextValue['status']>('loading');
  const [realm, setRealm] = useState<AuthRealm | null>(null);
  const [user, setUser] = useState<CurrentUser | null>(null);

  const loadSession = useCallback(async () => {
    const stored = getStoredSession();
    if (!stored) {
      setStatus('anonymous');
      setRealm(null);
      setUser(null);
      return;
    }

    try {
      const currentUser = await identityApi.me(stored.realm);
      setRealm(stored.realm);
      setUser(currentUser);
      setStatus('authenticated');
    } catch {
      clearStoredSession();
      setRealm(null);
      setUser(null);
      setStatus('anonymous');
    }
  }, []);

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  const establishSession = useCallback(async (nextRealm: AuthRealm, tokens: TokenPair) => {
    storeSession(nextRealm, tokens);
    const currentUser = await identityApi.me(nextRealm);
    setRealm(nextRealm);
    setUser(currentUser);
    setStatus('authenticated');
  }, []);

  const logout = useCallback(async () => {
    const stored = getStoredSession();
    clearStoredSession();
    setRealm(null);
    setUser(null);
    setStatus('anonymous');
    if (stored) {
      try {
        await identityApi.logout(stored.realm, stored.tokens.refresh_token);
      } catch {
        // Local session is already cleared; logout remains idempotent for the user.
      }
    }
  }, []);

  const value = useMemo<AuthSessionContextValue>(() => ({
    status,
    realm,
    user,
    establishSession,
    refreshCurrentSession: loadSession,
    logout,
  }), [establishSession, loadSession, logout, realm, status, user]);

  return <AuthSessionContext.Provider value={value}>{children}</AuthSessionContext.Provider>;
}

export function useAuthSession(): AuthSessionContextValue {
  const context = useContext(AuthSessionContext);
  if (!context) throw new Error('useAuthSession must be used inside AuthSessionProvider');
  return context;
}
