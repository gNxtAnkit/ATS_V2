import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';
import { PasswordStrength } from '../../components/ui/PasswordStrength';
import { CheckCircle2, AlertTriangle } from 'lucide-react';
import { identityApi } from '../../lib/api/identityApi';
import { toSafeError } from '../../lib/api/apiErrors';
import { parseAuthRealm } from '../../lib/auth/authRealm';
import type { PasswordPolicyResponse } from '../../lib/api/identityApi';

type State = 'idle' | 'loading' | 'success' | 'expired';

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const realm = parseAuthRealm(searchParams.get('realm'));
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [state, setState] = useState<State>('idle');
  const [formError, setFormError] = useState('');
  const [passwordPolicy, setPasswordPolicy] = useState<PasswordPolicyResponse>({
    min_length: 12,
    max_length: 128,
    require_uppercase: true,
    require_lowercase: true,
    require_number: true,
    require_special: true,
    prevent_email_similarity: true,
  });

  const token = searchParams.get('token') ?? '';

  useEffect(() => {
    identityApi.passwordPolicy(realm)
      .then(setPasswordPolicy)
      .catch(() => undefined);
  }, [realm]);

  if (!token || state === 'expired') {
    return (
      <AuthLayout footerText="Password reset links expire after 1 hour for security.">
        <div className="hidden lg:flex items-center gap-2.5 mb-8">
          <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
            <span className="text-white font-bold text-xs leading-none">gN</span>
          </div>
          <span className="text-slate-900 font-bold text-base tracking-tight">gNxtHire</span>
        </div>
        <div className="text-center py-4">
          <div className="w-14 h-14 bg-amber-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
            <AlertTriangle size={26} className="text-amber-600" />
          </div>
          <h1 className="text-xl font-bold text-slate-900 mb-2">Reset link expired</h1>
          <p className="text-sm text-slate-500 mb-6 leading-relaxed">
            This password reset link is invalid or has expired. Please request a new one.
          </p>
          <Link to={realm === 'platform' ? '/auth/forgot-password?realm=platform' : '/auth/forgot-password'}>
            <Button fullWidth size="lg">Request a new link</Button>
          </Link>
          <Link to={realm === 'platform' ? '/platform-admin/login' : '/auth/login'} className="block text-sm text-slate-500 hover:text-slate-700 font-medium mt-4">
            Back to sign in
          </Link>
        </div>
      </AuthLayout>
    );
  }

  if (state === 'success') {
    return (
      <AuthLayout>
        <div className="hidden lg:flex items-center gap-2.5 mb-8">
          <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
            <span className="text-white font-bold text-xs leading-none">gN</span>
          </div>
          <span className="text-slate-900 font-bold text-base tracking-tight">gNxtHire</span>
        </div>
        <div className="text-center py-4">
          <div className="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
            <CheckCircle2 size={26} className="text-emerald-600" />
          </div>
          <h1 className="text-xl font-bold text-slate-900 mb-2">Password updated</h1>
          <p className="text-sm text-slate-500 mb-6 leading-relaxed">
            Your password has been changed successfully. Sign in with your new credentials.
          </p>
          <Button fullWidth size="lg" onClick={() => navigate(realm === 'platform' ? '/platform-admin/login' : '/auth/login')}>
            Back to sign in
          </Button>
        </div>
      </AuthLayout>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    if (password !== confirm) {
      setFormError('Passwords do not match.');
      return;
    }
    if (password.length < passwordPolicy.min_length) {
      setFormError(`Password must be at least ${passwordPolicy.min_length} characters long.`);
      return;
    }
    if (password.length > passwordPolicy.max_length) {
      setFormError(`Password must be no more than ${passwordPolicy.max_length} characters long.`);
      return;
    }
    if (passwordPolicy.require_uppercase && !/[A-Z]/.test(password)) {
      setFormError('Password must contain an uppercase letter.');
      return;
    }
    if (passwordPolicy.require_lowercase && !/[a-z]/.test(password)) {
      setFormError('Password must contain a lowercase letter.');
      return;
    }
    if (passwordPolicy.require_number && !/\d/.test(password)) {
      setFormError('Password must contain a number.');
      return;
    }
    if (passwordPolicy.require_special && !/[^A-Za-z0-9]/.test(password)) {
      setFormError('Password must contain a special character.');
      return;
    }
    setState('loading');
    try {
      await identityApi.resetPassword(realm, token, password, confirm);
      setState('success');
    } catch (err) {
      const safeError = toSafeError(err, 'reset');
      if (safeError.kind === 'invalid_reset_token') {
        setState('expired');
        return;
      }
      setState('idle');
      setFormError(safeError.message);
    }
  };

  return (
    <AuthLayout footerText="Your new password will take effect immediately upon saving.">
      <div className="hidden lg:flex items-center gap-2.5 mb-8">
        <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
          <span className="text-white font-bold text-xs leading-none">gN</span>
        </div>
        <span className="text-slate-900 font-bold text-base tracking-tight">gNxtHire</span>
      </div>

      <div className="mb-6">
        <h1 className="text-[22px] font-bold text-slate-900 mb-1.5 leading-tight">Create a new password</h1>
        <p className="text-sm text-slate-500 leading-relaxed">
          Choose a strong password for your account.
        </p>
      </div>

      {formError && (
        <Alert variant="error" className="mb-5" onDismiss={() => setFormError('')}>
          {formError}
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="New password"
          type="password"
          placeholder="Create a strong password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="new-password"
        />

        {password && (
          <div className="px-1">
            <PasswordStrength password={password} policy={passwordPolicy} />
          </div>
        )}

        <Input
          label="Confirm new password"
          type="password"
          placeholder="Re-enter your password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          required
          autoComplete="new-password"
          error={confirm && password !== confirm ? 'Passwords do not match' : undefined}
        />

        <Button type="submit" fullWidth loading={state === 'loading'} size="lg">
          Update password
        </Button>
      </form>

      <div className="mt-5 text-center">
        <Link to={realm === 'platform' ? '/platform-admin/login' : '/auth/login'} className="text-sm text-slate-500 hover:text-slate-700 font-medium transition-colors">
          ← Back to sign in
        </Link>
      </div>
    </AuthLayout>
  );
}
