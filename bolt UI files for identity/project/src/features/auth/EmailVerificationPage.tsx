import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { Mail, CheckCircle2, AlertTriangle } from 'lucide-react';
import { useEffect } from 'react';
import { identityApi } from '../../lib/api/identityApi';
import { toSafeError } from '../../lib/api/apiErrors';
import { parseAuthRealm } from '../../lib/auth/authRealm';

type ResendState = 'idle' | 'sending' | 'sent' | 'rate_limited';

function maskEmail(email: string): string {
  const [user, domain] = email.split('@');
  if (!domain) return email;
  return user[0] + '•'.repeat(Math.max(1, user.length - 1)) + '@' + domain;
}

export function EmailVerificationRequiredPage() {
  const [searchParams] = useSearchParams();
  const realm = parseAuthRealm(searchParams.get('realm'));
  const [resendState, setResendState] = useState<ResendState>('idle');
  const email = searchParams.get('email') ?? '';

  const handleResend = async () => {
    if (!email || resendState === 'sending') return;
    setResendState('sending');
    try {
      await identityApi.requestEmailVerification(realm, email);
      setResendState('sent');
    } catch (err) {
      const safeError = toSafeError(err);
      setResendState(safeError.kind === 'rate_limited' ? 'rate_limited' : 'idle');
    }
  };

  return (
    <AuthLayout footerText="Check your spam or junk folder if you don't receive the email within a few minutes.">
      <div className="hidden lg:flex items-center gap-2.5 mb-8">
        <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
          <span className="text-white font-bold text-xs leading-none">gN</span>
        </div>
        <span className="text-slate-900 font-bold text-base tracking-tight">gNxtHire</span>
      </div>

      <div className="text-center mb-6">
        <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-5">
          <Mail size={26} className="text-blue-600" />
        </div>
        <h1 className="text-[22px] font-bold text-slate-900 mb-2 leading-tight">Verify your email</h1>
        <p className="text-sm text-slate-500 leading-relaxed">
          We need to verify your email before you can access your workspace.
        </p>
      </div>

      <div className="bg-slate-50 rounded-xl border border-slate-200 px-4 py-3 mb-5 text-center">
        <p className="text-xs text-slate-500 mb-0.5">Verification email sent to</p>
        <p className="text-sm font-semibold text-slate-800">{email ? maskEmail(email) : 'your email address'}</p>
      </div>

      {resendState === 'sent' && (
        <Alert variant="success" className="mb-4">
          A new verification email has been sent. Check your inbox and spam folder.
        </Alert>
      )}
      {resendState === 'rate_limited' && (
        <Alert variant="warning" className="mb-4">
          Too many requests. Please wait a few minutes before trying again.
        </Alert>
      )}

      <Alert variant="info" className="mb-5">
        Open the verification link in your email to continue. Links expire after 24 hours.
      </Alert>

      <Button
        fullWidth
        size="lg"
        loading={resendState === 'sending'}
        onClick={handleResend}
      >
        Resend verification email
      </Button>

      <div className="mt-5 flex flex-col items-center gap-3">
        <Link to={realm === 'platform' ? '/platform-admin/login' : '/auth/login'} className="text-sm text-slate-500 hover:text-slate-700 font-medium transition-colors">
          ← Back to sign in
        </Link>
      </div>
    </AuthLayout>
  );
}

export function EmailVerificationResultPage() {
  const [searchParams] = useSearchParams();
  const realm = parseAuthRealm(searchParams.get('realm'));
  const [displayState, setDisplayState] = useState<'verifying' | 'success' | 'expired'>('verifying');

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setDisplayState('expired');
      return;
    }
    identityApi.verifyEmail(realm, token)
      .then(() => setDisplayState('success'))
      .catch((err: unknown) => {
        const safeError = toSafeError(err, 'verify');
        setDisplayState(safeError.kind === 'invalid_verification_token' ? 'expired' : 'expired');
      });
  }, [realm, searchParams]);

  return (
    <AuthLayout footerText="Contact your administrator if you continue to have trouble verifying your email.">
      <div className="hidden lg:flex items-center gap-2.5 mb-8">
        <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
          <span className="text-white font-bold text-xs leading-none">gN</span>
        </div>
        <span className="text-slate-900 font-bold text-base tracking-tight">gNxtHire</span>
      </div>

      {displayState === 'verifying' ? (
        <div className="text-center py-2">
          <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mx-auto mb-5">
            <Mail size={30} className="text-blue-600" />
          </div>
          <h1 className="text-[22px] font-bold text-slate-900 mb-2 leading-tight">Verifying email</h1>
          <p className="text-sm text-slate-500 mb-6 leading-relaxed">Please wait while we verify your email address.</p>
        </div>
      ) : displayState === 'success' ? (
        <div className="text-center py-2">
          <div className="w-16 h-16 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
            <CheckCircle2 size={30} className="text-emerald-600" />
          </div>
          <h1 className="text-[22px] font-bold text-slate-900 mb-2 leading-tight">Email verified</h1>
          <p className="text-sm text-slate-500 mb-6 leading-relaxed">
            Your email address has been successfully verified. You can now access your workspace.
          </p>
          <Link to={realm === 'platform' ? '/platform-admin/login' : '/auth/login'}>
            <Button fullWidth size="lg">Continue to sign in</Button>
          </Link>
        </div>
      ) : (
        <div className="text-center py-2">
          <div className="w-16 h-16 bg-amber-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
            <AlertTriangle size={28} className="text-amber-600" />
          </div>
          <h1 className="text-[22px] font-bold text-slate-900 mb-2 leading-tight">Verification link expired</h1>
          <p className="text-sm text-slate-500 mb-6 leading-relaxed">
            This verification link has expired or has already been used. Request a new one below.
          </p>
          <Link to={realm === 'platform' ? '/auth/verify-email-required?realm=platform' : '/auth/verify-email-required'}>
            <Button fullWidth size="lg">Request a new link</Button>
          </Link>
          <Link to={realm === 'platform' ? '/platform-admin/login' : '/auth/login'} className="block text-sm text-slate-500 hover:text-slate-700 font-medium mt-3">
            Back to sign in
          </Link>
        </div>
      )}
    </AuthLayout>
  );
}
