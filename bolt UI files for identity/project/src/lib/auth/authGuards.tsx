import { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthSession } from './authSession';
import type { AuthRealm } from './authTypes';

export function ProtectedRoute({ realm, children }: { realm: AuthRealm; children: ReactNode }) {
  const session = useAuthSession();
  const location = useLocation();
  const loginPath = realm === 'platform' ? '/platform-admin/login' : '/auth/login';

  if (session.status === 'loading') {
    return <div className="min-h-screen bg-[#F0F3FA]" />;
  }

  if (session.status !== 'authenticated' || session.realm !== realm) {
    return <Navigate to={`${loginPath}?redirect=${encodeURIComponent(location.pathname)}`} replace />;
  }

  return <>{children}</>;
}

export function PublicOnlyRoute({ realm, children }: { realm: AuthRealm; children: ReactNode }) {
  const session = useAuthSession();

  if (session.status === 'loading') {
    return <div className="min-h-screen bg-[#F0F3FA]" />;
  }

  if (session.status === 'authenticated' && session.realm === realm) {
    return <Navigate to={realm === 'platform' ? '/platform-admin/dashboard' : '/dashboard'} replace />;
  }

  return <>{children}</>;
}
