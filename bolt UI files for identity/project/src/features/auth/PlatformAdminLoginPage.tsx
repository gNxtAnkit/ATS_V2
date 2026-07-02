import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';
import { ShieldCheck } from 'lucide-react';
import { identityApi } from '../../lib/api/identityApi';
import { toSafeError } from '../../lib/api/apiErrors';
import { useAuthSession } from '../../lib/auth/authSession';
import { storeMfaChallenge } from '../../lib/auth/authStorage';

type State = 'idle' | 'loading' | 'error';

export function PlatformAdminLoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { establishSession } = useAuthSession();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [state, setState] = useState<State>('idle');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || state === 'loading') return;
    setState('loading');
    setError('');

    try {
      const response = await identityApi.login('platform', email, password);
      const redirectTo = searchParams.get('redirect') || '/platform-admin/dashboard';

      if (response.status === 'mfa_required' && response.mfa_challenge_token) {
        storeMfaChallenge({ realm: 'platform', challengeToken: response.mfa_challenge_token, redirectTo });
        navigate('/auth/mfa/verify');
        return;
      }

      if (response.status === 'authenticated' && response.tokens) {
        await establishSession('platform', response.tokens);
        navigate(redirectTo, { replace: true });
        return;
      }

      setState('error');
      setError('We could not complete sign in. Please try again.');
    } catch (err) {
      const safeError = toSafeError(err, 'login');
      setState('error');
      setError(safeError.kind === 'invalid_credentials' ? 'Access denied. Please check your platform admin credentials.' : safeError.message);
    }
  };

  return (
    <AuthLayout variant="platform" footerText="Platform access is monitored and audited. Unauthorised access is strictly prohibited.">
      <div className="hidden lg:flex items-center gap-2.5 mb-8">
        <div className="w-8 h-8 bg-slate-800 rounded-xl flex items-center justify-center shadow-sm">
          <span className="text-white font-bold text-xs leading-none">gN</span>
        </div>
        <div className="flex flex-col">
          <span className="text-slate-900 font-bold text-base tracking-tight leading-none">gNxtHire</span>
          <span className="text-[10px] text-slate-500 font-medium tracking-wider uppercase">Platform Admin</span>
        </div>
      </div>

      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <ShieldCheck size={18} className="text-slate-600 shrink-0" />
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Restricted Access</span>
        </div>
        <h1 className="text-[22px] font-bold text-slate-900 mb-1.5 leading-tight">Platform Admin Sign In</h1>
        <p className="text-sm text-slate-500">Access gNxtHire platform operations.</p>
      </div>

      {state === 'error' && (
        <Alert variant="error" className="mb-5" onDismiss={() => setState('idle')}>
          {error}
        </Alert>
      )}

      <Alert variant="warning" className="mb-5">
        This login is for internal gNxtHire platform administrators only.
      </Alert>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Admin email"
          type="email"
          placeholder="admin@gnxthire.io"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
        />
        <Input
          label="Password"
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
        />
        <div className="flex justify-end -mt-2">
          <Link to="/auth/forgot-password?realm=platform" className="text-xs text-blue-600 hover:text-blue-700 font-medium">
            Forgot password?
          </Link>
        </div>

        <Button type="submit" fullWidth loading={state === 'loading'} size="lg">
          Sign in as platform admin
        </Button>
      </form>

      <div className="mt-6 pt-5 border-t border-slate-100">
        <p className="text-center text-xs text-slate-400">
          Tenant user?{' '}
          <Link to="/auth/login" className="text-blue-600 hover:text-blue-700 font-medium">
            Sign in to your workspace
          </Link>
        </p>
      </div>
    </AuthLayout>
  );
}
