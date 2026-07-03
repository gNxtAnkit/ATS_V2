import { FormEvent, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, KeyRound, ShieldCheck } from 'lucide-react';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { OtpInput } from '../../components/ui/OtpInput';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { platformAdminApi, toSafeUserMessage } from '../../api';
import { useAuth } from '../../lib/auth/AuthProvider';
import { readMfaChallenge, clearMfaChallenge } from '../../lib/auth/AuthProvider';

export function MfaVerifyPage() {
  const { completeLogin } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<'totp' | 'recovery'>('totp');
  const [code, setCode] = useState('');
  const [recoveryCode, setRecoveryCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const challenge = readMfaChallenge();

  useEffect(() => {
    if (!challenge) navigate('/auth/login', { replace: true });
  }, [challenge, navigate]);

  if (!challenge) return null;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (mode === 'totp' && code.length !== 6) {
      setError('Enter the 6-digit code from your authenticator app.');
      return;
    }
    if (mode === 'recovery' && !recoveryCode.trim()) {
      setError('Enter a recovery code.');
      return;
    }

    setSubmitting(true);
    try {
      const response =
        mode === 'totp'
          ? await platformAdminApi.verifyTotp(challenge!.token, code)
          : await platformAdminApi.verifyRecoveryCode(challenge!.token, recoveryCode.trim());
      await completeLogin(response);
      navigate('/', { replace: true });
    } catch (err) {
      setError(toSafeUserMessage(err, 'mfa'));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <div className="mb-6 text-center">
        <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mx-auto mb-4">
          <ShieldCheck size={22} className="text-slate-700" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900 leading-tight">Two-step verification</h1>
        <p className="text-sm text-slate-500 mt-1.5">
          {mode === 'totp' ? 'Enter the 6-digit code from your authenticator app.' : 'Enter one of your recovery codes.'}
        </p>
      </div>

      {error && (
        <div className="mb-4">
          <Alert variant="error">{error}</Alert>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="space-y-5">
        {mode === 'totp' ? (
          <OtpInput value={code} onChange={setCode} autoFocus />
        ) : (
          <Input
            label="Recovery code"
            value={recoveryCode}
            onChange={(event) => setRecoveryCode(event.target.value)}
            placeholder="XXXX-XXXX-XXXX"
            autoFocus
          />
        )}

        <Button type="submit" fullWidth loading={submitting} disabled={submitting}>
          Verify and continue
        </Button>
      </form>

      <button
        onClick={() => {
          setError(null);
          setMode((current) => (current === 'totp' ? 'recovery' : 'totp'));
        }}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors mt-5"
      >
        <KeyRound size={15} />
        {mode === 'totp' ? 'Use a recovery code instead' : 'Use authenticator app instead'}
      </button>

      <div className="mt-4 pt-4 border-t border-slate-100">
        <Link
          to="/auth/login"
          onClick={() => clearMfaChallenge()}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-slate-600 transition-colors"
        >
          <ArrowLeft size={13} />
          Back to sign in
        </Link>
      </div>
    </AuthLayout>
  );
}
