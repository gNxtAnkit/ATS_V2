import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';
import { Mail } from 'lucide-react';
import { identityApi } from '../../lib/api/identityApi';
import { toSafeError } from '../../lib/api/apiErrors';
import { parseAuthRealm } from '../../lib/auth/authRealm';

type State = 'idle' | 'loading' | 'sent' | 'error';

export function ForgotPasswordPage() {
  const [searchParams] = useSearchParams();
  const realm = parseAuthRealm(searchParams.get('realm'));
  const [email, setEmail] = useState('');
  const [state, setState] = useState<State>('idle');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || state === 'loading') return;
    setState('loading');
    setError('');
    try {
      await identityApi.forgotPassword(realm, email);
      setState('sent');
    } catch (err) {
      setState('error');
      setError(toSafeError(err).message);
    }
  };

  return (
    <AuthLayout footerText="For security, we never reveal whether an email is registered.">
      <div className="hidden lg:flex items-center gap-2.5 mb-8">
        <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
          <span className="text-white font-bold text-xs leading-none">gN</span>
        </div>
        <span className="text-slate-900 font-bold text-base tracking-tight">gNxtHire</span>
      </div>

      {state === 'sent' ? (
        <div className="text-center py-4">
          <div className="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
            <Mail size={26} className="text-emerald-600" />
          </div>
          <h1 className="text-xl font-bold text-slate-900 mb-2">Check your inbox</h1>
          <p className="text-sm text-slate-500 mb-6 leading-relaxed">
            If an account exists for <span className="font-medium text-slate-700">{email}</span>,
            we've sent password reset instructions. Check your spam folder if you don't see it.
          </p>
          <Alert variant="info" className="text-left mb-6">
            Reset links expire after 1 hour. Request a new link if needed.
          </Alert>
          <Button variant="secondary" fullWidth onClick={() => setState('idle')}>
            Send another link
          </Button>
          <Link
            to={realm === 'platform' ? '/platform-admin/login' : '/auth/login'}
            className="block text-sm text-blue-600 hover:text-blue-700 font-medium mt-4 transition-colors"
          >
            Back to sign in
          </Link>
        </div>
      ) : (
        <>
          <div className="mb-6">
            <h1 className="text-[22px] font-bold text-slate-900 mb-1.5 leading-tight">Reset your password</h1>
            <p className="text-sm text-slate-500 leading-relaxed">
              Enter your email and we'll send reset instructions if an account exists.
            </p>
          </div>

          {state === 'error' && (
            <Alert variant="error" className="mb-5" onDismiss={() => setState('idle')}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Work email"
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
            <Button type="submit" fullWidth loading={state === 'loading'} size="lg">
              Send reset link
            </Button>
          </form>

          <div className="mt-5 text-center">
            <Link
              to={realm === 'platform' ? '/platform-admin/login' : '/auth/login'}
              className="text-sm text-slate-500 hover:text-slate-700 font-medium transition-colors"
            >
              ← Back to sign in
            </Link>
          </div>
        </>
      )}
    </AuthLayout>
  );
}
