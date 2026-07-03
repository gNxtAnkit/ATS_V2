import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { OtpInput } from '../../components/ui/OtpInput';
import { RefreshCw } from 'lucide-react';
import { identityApi } from '../../lib/api/identityApi';
import { toSafeError } from '../../lib/api/apiErrors';
import { useAuthSession } from '../../lib/auth/authSession';
import { clearMfaChallenge, getMfaChallenge } from '../../lib/auth/authStorage';

export function MfaVerifyPage() {
  const navigate = useNavigate();
  const { establishSession } = useAuthSession();
  const [code, setCode] = useState('');
  const [state, setState] = useState<'idle' | 'loading' | 'error'>('idle');
  const [error, setError] = useState('Invalid code. Please check your authenticator app and try again.');
  const [countdown, setCountdown] = useState(30);
  const challenge = getMfaChallenge();
  const loginPath = challenge?.realm === 'platform' ? '/platform-admin/login' : '/auth/login';
  const recoveryCodeAvailable = challenge?.availableMethods.includes('recovery_code') ?? false;

  useEffect(() => {
    const interval = setInterval(() => {
      setCountdown((c) => (c <= 1 ? 30 : c - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (code.length < 6 || state === 'loading') return;
    if (!challenge) {
      setState('error');
      setError('Your verification session expired. Please sign in again.');
      return;
    }
    if (challenge.expiresAt <= Date.now()) {
      clearMfaChallenge();
      navigate(loginPath, { replace: true });
      return;
    }
    setState('loading');
    try {
      const response = await identityApi.verifyMfa(challenge.realm, challenge.challengeToken, code);
      if (response.tokens) {
        clearMfaChallenge();
        await establishSession(challenge.realm, response.tokens);
        navigate(challenge.redirectTo, { replace: true });
        return;
      }
      setState('error');
      setError('We could not complete verification. Please try again.');
    } catch (err) {
      const safeError = toSafeError(err, 'mfa');
      setState('error');
      setError(safeError.message);
      setCode('');
    }
  };

  return (
    <AuthLayout footerText="Keep your authenticator app secure. Never share your verification codes.">
      <div className="hidden lg:flex items-center gap-2.5 mb-8">
        <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
          <span className="text-white font-bold text-xs leading-none">gN</span>
        </div>
        <span className="text-slate-900 font-bold text-base tracking-tight">gNxtHire</span>
      </div>

      <div className="text-center mb-7">
        <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg viewBox="0 0 24 24" fill="none" className="w-7 h-7 text-blue-600" stroke="currentColor" strokeWidth="1.8">
            <rect x="5" y="11" width="14" height="10" rx="2" />
            <path d="M8 11V7a4 4 0 118 0v4" />
            <circle cx="12" cy="16" r="1.5" fill="currentColor" stroke="none" />
          </svg>
        </div>
        <h1 className="text-[22px] font-bold text-slate-900 mb-1.5 leading-tight">Enter your verification code</h1>
        <p className="text-sm text-slate-500 leading-relaxed">
          Open your authenticator app and enter the 6-digit code.
        </p>
      </div>

      {state === 'error' && (
        <Alert variant="error" className="mb-5" onDismiss={() => setState('idle')}>
          {error}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <OtpInput value={code} onChange={setCode} length={6} error={state === 'error'} autoFocus />

        <div className="flex items-center justify-center gap-2 mt-3 mb-6">
          <RefreshCw size={12} className="text-slate-400" />
          <span className="text-xs text-slate-500">
            Code refreshes in <span className="font-semibold text-slate-700 tabular-nums">{countdown}s</span>
          </span>
        </div>

        <Button
          type="submit"
          fullWidth
          size="lg"
          loading={state === 'loading'}
          disabled={code.length < 6}
        >
          Verify and continue
        </Button>
      </form>

      <div className="mt-5 flex flex-col items-center gap-3">
        {recoveryCodeAvailable && (
          <Link
            to="/auth/mfa/recovery-code"
            className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
          >
            Use a recovery code instead
          </Link>
        )}
        <Link
          to={loginPath}
          className="text-sm text-slate-500 hover:text-slate-700 font-medium transition-colors"
        >
          ← Back to sign in
        </Link>
      </div>
    </AuthLayout>
  );
}
