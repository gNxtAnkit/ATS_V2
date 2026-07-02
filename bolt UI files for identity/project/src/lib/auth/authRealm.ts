import type { AuthRealm } from './authTypes';

export function getDefaultAuthRealm(): AuthRealm {
  const configuredRealm = import.meta.env.VITE_DEFAULT_AUTH_REALM as AuthRealm | undefined;
  if (configuredRealm === 'platform' || configuredRealm === 'tenant') return configuredRealm;
  return window.location.port === '5174' ? 'platform' : 'tenant';
}

export function parseAuthRealm(value: string | null): AuthRealm {
  if (value === 'platform') return 'platform';
  return getDefaultAuthRealm();
}
