import { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from './AuthProvider';
import { readMfaChallenge } from './AuthProvider';

function FullScreenLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
    </div>
  );
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { admin, loading } = useAuth();
  const location = useLocation();

  if (loading) return <FullScreenLoader />;
  if (!admin) return <Navigate to="/auth/login" replace state={{ from: location.pathname }} />;
  return <>{children}</>;
}

export function RedirectIfAuthenticated({ children }: { children: ReactNode }) {
  const { admin, loading } = useAuth();
  if (loading) return <FullScreenLoader />;
  if (admin) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export function RequireMfaChallenge({ children }: { children: ReactNode }) {
  const challenge = readMfaChallenge();
  if (!challenge) return <Navigate to="/auth/login" replace />;
  return <>{children}</>;
}
