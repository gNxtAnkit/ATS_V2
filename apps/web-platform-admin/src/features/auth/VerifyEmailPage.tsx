import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { platformAdminApi, toSafeUserMessage } from '../../api';

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const [status, setStatus] = useState<'checking' | 'success' | 'error'>('checking');
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setMessage('This verification link is invalid or missing a token.');
      return;
    }
    let active = true;
    platformAdminApi
      .verifyEmail(token)
      .then(() => {
        if (active) setStatus('success');
      })
      .catch((error) => {
        if (active) {
          setStatus('error');
          setMessage(toSafeUserMessage(error, 'verify'));
        }
      });
    return () => {
      active = false;
    };
  }, [token]);

  return (
    <AuthLayout>
      <div className="text-center">
        {status === 'checking' && (
          <>
            <Loader2 size={28} className="text-slate-400 animate-spin mx-auto mb-4" />
            <h1 className="text-xl font-bold text-slate-900">Verifying your email</h1>
            <p className="text-sm text-slate-500 mt-2">This will just take a moment.</p>
          </>
        )}
        {status === 'success' && (
          <>
            <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 size={22} className="text-emerald-600" />
            </div>
            <h1 className="text-xl font-bold text-slate-900">Email verified</h1>
            <p className="text-sm text-slate-500 mt-2 leading-relaxed">Your email address has been confirmed.</p>
            <Link
              to="/auth/login"
              className="inline-flex items-center justify-center h-10 px-4 rounded-lg bg-brand-primary text-white text-sm font-medium hover:bg-brand-hover transition-colors mt-6"
            >
              Continue to sign in
            </Link>
          </>
        )}
        {status === 'error' && (
          <>
            <div className="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center mx-auto mb-4">
              <XCircle size={22} className="text-red-600" />
            </div>
            <h1 className="text-xl font-bold text-slate-900">Verification failed</h1>
            <p className="text-sm text-slate-500 mt-2 leading-relaxed">{message}</p>
            <Link to="/auth/login" className="inline-flex text-sm font-medium text-slate-700 hover:text-slate-900 mt-6">
              Back to sign in
            </Link>
          </>
        )}
      </div>
    </AuthLayout>
  );
}
