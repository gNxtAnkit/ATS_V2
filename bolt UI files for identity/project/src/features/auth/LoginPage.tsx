import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';
import { identityApi } from '../../lib/api/identityApi';
import { toSafeError } from '../../lib/api/apiErrors';
import { useAuthSession } from '../../lib/auth/authSession';
import { storeMfaChallenge } from '../../lib/auth/authStorage';
import { ui } from '../../lib/theme';

type LoginState = 'idle' | 'loading' | 'error';

export function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { establishSession } = useAuthSession();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [state, setState] = useState<LoginState>('idle');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || state === 'loading') return;
    setState('loading');
    setError('');

    try {
      const response = await identityApi.login('tenant', email, password);
      const redirectTo = searchParams.get('redirect') || '/dashboard';

      const challengeToken = response.challenge_token ?? response.mfa_challenge_token;
      if ((response.mfa_required || response.status === 'mfa_required') && challengeToken) {
        storeMfaChallenge({
          realm: 'tenant',
          challengeToken,
          redirectTo,
          availableMethods: response.available_methods ?? ['totp'],
          expiresAt: Date.now() + (response.expires_in_seconds ?? 300) * 1000,
        });
        navigate('/auth/mfa/verify');
        return;
      }

      if (response.status === 'authenticated' && response.tokens) {
        await establishSession('tenant', response.tokens);
        navigate(redirectTo, { replace: true });
        return;
      }

      setState('error');
      setError('We could not complete sign in. Please try again.');
    } catch (err) {
      const safeError = toSafeError(err, 'login');
      if (safeError.kind === 'email_verification_required') {
        navigate(`/auth/verify-email-required?email=${encodeURIComponent(email)}`);
        return;
      }
      setState('error');
      setError(safeError.message);
    }
  };

  return (
    <AuthLayout>
      <div className="hidden lg:flex items-center gap-2.5 mb-8">
        <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
          <span className="text-white font-bold text-xs leading-none">gN</span>
        </div>
        <span className="text-slate-900 font-bold text-base tracking-tight">gNxtHire</span>
      </div>

      <div className="mb-6">
        <h1 className="text-[22px] font-bold text-slate-900 mb-1.5 leading-tight">Sign in to gNxtHire</h1>
        <p className="text-sm text-slate-500">Access your hiring workspace securely.</p>
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

        <div>
          <Input
            label="Password"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
          <div className="flex justify-end mt-1.5">
            <Link to="/auth/forgot-password" className="text-xs text-blue-600 hover:text-blue-700 font-medium">
              Forgot password?
            </Link>
          </div>
        </div>

        <label className="flex items-center gap-2.5 cursor-pointer select-none group">
          <input
            type="checkbox"
            checked={remember}
            onChange={(e) => setRemember(e.target.checked)}
            className={ui.checkbox}
          />
          <span className="text-sm text-slate-600 group-hover:text-slate-700">Remember this device</span>
        </label>

        <Button type="submit" fullWidth loading={state === 'loading'} size="lg">
          Sign in
        </Button>
      </form>
    </AuthLayout>
  );
}
