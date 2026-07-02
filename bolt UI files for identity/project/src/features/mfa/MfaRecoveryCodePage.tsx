import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';
import { identityApi } from '../../lib/api/identityApi';
import { toSafeError } from '../../lib/api/apiErrors';
import { useAuthSession } from '../../lib/auth/authSession';
import { clearMfaChallenge, getMfaChallenge } from '../../lib/auth/authStorage';

export function MfaRecoveryCodePage() {
  const navigate = useNavigate();
  const { establishSession } = useAuthSession();
  const [code, setCode] = useState('');
  const [state, setState] = useState<'idle' | 'loading' | 'error'>('idle');
  const [error, setError] = useState('Invalid recovery code. Please check your saved codes and try again.');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim() || state === 'loading') return;
    const challenge = getMfaChallenge();
    if (!challenge) {
      setState('error');
      setError('Your verification session expired. Please sign in again.');
      return;
    }
    setState('loading');
    try {
      const response = await identityApi.verifyMfaRecoveryCode(challenge.realm, challenge.challengeToken, code.trim());
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
    }
  };

  return (
    <AuthLayout footerText="Each recovery code can only be used once. Contact your admin if you've lost all codes.">
      <div className="hidden lg:flex items-center gap-2.5 mb-8">
        <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
          <span className="text-white font-bold text-xs leading-none">gN</span>
        </div>
        <span className="text-slate-900 font-bold text-base tracking-tight">gNxtHire</span>
      </div>

      <div className="mb-6">
        <h1 className="text-[22px] font-bold text-slate-900 mb-1.5 leading-tight">Use a recovery code</h1>
        <p className="text-sm text-slate-500 leading-relaxed">
          Enter one of the recovery codes you saved when MFA was enabled.
        </p>
      </div>

      {state === 'error' && (
        <Alert variant="error" className="mb-5" onDismiss={() => setState('idle')}>
          {error}
        </Alert>
      )}

      <Alert variant="warning" className="mb-5">
        Each recovery code can only be used once. Using a code will invalidate it permanently.
      </Alert>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Recovery code"
          type="text"
          placeholder="XXXX-XXXX-XXXX"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          required
          autoComplete="off"
          autoFocus
          helper="Recovery codes are case-insensitive and formatted as groups separated by dashes."
        />

        <Button
          type="submit"
          fullWidth
          size="lg"
          loading={state === 'loading'}
          disabled={!code.trim()}
        >
          Verify recovery code
        </Button>
      </form>

      <div className="mt-5 flex flex-col items-center gap-3">
        <Link
          to="/auth/mfa/verify"
          className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
        >
          Use authenticator code instead
        </Link>
        <Link
          to="/auth/login"
          className="text-sm text-slate-500 hover:text-slate-700 font-medium transition-colors"
        >
          ← Back to sign in
        </Link>
      </div>
    </AuthLayout>
  );
}
