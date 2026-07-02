import type { AuthRealm, PendingMfaChallenge, StoredSession, TokenPair } from './authTypes';

const SESSION_KEY = 'gnxthire.identity.session';
const MFA_CHALLENGE_KEY = 'gnxthire.identity.mfaChallenge';

function parseJson<T>(value: string | null): T | null {
  if (!value) return null;
  try {
    return JSON.parse(value) as T;
  } catch {
    return null;
  }
}

export function getStoredSession(): StoredSession | null {
  return parseJson<StoredSession>(localStorage.getItem(SESSION_KEY));
}

export function storeSession(realm: AuthRealm, tokens: TokenPair): void {
  localStorage.setItem(SESSION_KEY, JSON.stringify({ realm, tokens }));
}

export function clearStoredSession(): void {
  localStorage.removeItem(SESSION_KEY);
  sessionStorage.removeItem(MFA_CHALLENGE_KEY);
}

export function storeMfaChallenge(challenge: PendingMfaChallenge): void {
  sessionStorage.setItem(MFA_CHALLENGE_KEY, JSON.stringify(challenge));
}

export function getMfaChallenge(): PendingMfaChallenge | null {
  return parseJson<PendingMfaChallenge>(sessionStorage.getItem(MFA_CHALLENGE_KEY));
}

export function clearMfaChallenge(): void {
  sessionStorage.removeItem(MFA_CHALLENGE_KEY);
}
