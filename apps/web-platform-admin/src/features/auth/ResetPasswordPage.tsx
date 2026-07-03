import { FormEvent, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowLeft, CheckCircle2 } from 'lucide-react';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { PasswordStrength } from '../../components/ui/PasswordStrength';
import { platformAdminApi, toSafeUserMessage } from '../../api';
import type { PasswordPolicyResponse } from '../../types';

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';

  const [policy, setPolicy] = useState<PasswordPolicyResponse | undefined>();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    let active = true;
    platformAdminApi
      .passwordPolicy()
      .then((result) => {
        if (active) setPolicy(result);
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);

    if (!token) {
      setFormError('This password reset link is invalid or has expired.');
      return;
    }
    if (password !== confirmPassword) {
      setFormError('Passwords do not match.');
      return;
    }

    setSubmitting(true);
    try {
      await platformAdminApi.resetPassword(token, password, confirmPassword);
      setSuccess(true);
    } catch (error) {
      setFormError(toSafeUserMessage(error, 'reset'));
    } finally {
      setSubmitting(false);
    }
  }

  if (!token) {
    return (
      <AuthLayout>
        <div className="text-center">
          <h1 className="text-xl font-bold text-slate-900">Invalid reset link</h1>
          <p className="text-sm text-slate-500 mt-2 leading-relaxed">
            This password reset link is invalid or has expired. Request a new one to continue.
          </p>
          <Link to="/auth/forgot-password" className="inline-flex text-sm font-medium text-slate-700 hover:text-slate-900 mt-6">
            Request a new link
          </Link>
        </div>
      </AuthLayout>
    );
  }

  if (success) {
    return (
      <AuthLayout>
        <div className="text-center">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 size={22} className="text-emerald-600" />
          </div>
          <h1 className="text-xl font-bold text-slate-900">Password updated</h1>
          <p className="text-sm text-slate-500 mt-2 leading-relaxed">Your password has been reset. You can now sign in.</p>
          <Link
            to="/auth/login"
            className="inline-flex items-center justify-center h-10 px-4 rounded-lg bg-brand-primary text-white text-sm font-medium hover:bg-brand-hover transition-colors mt-6"
          >
            Continue to sign in
          </Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 leading-tight">Set a new password</h1>
        <p className="text-sm text-slate-500 mt-1.5">Choose a strong password you haven't used before.</p>
      </div>

      {formError && (
        <div className="mb-4">
          <Alert variant="error">{formError}</Alert>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        <Input
          label="New password"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          disabled={submitting}
          placeholder="••••••••••"
        />
        <Input
          label="Confirm new password"
          type="password"
          autoComplete="new-password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          disabled={submitting}
          placeholder="••••••••••"
        />
        <PasswordStrength password={password} confirmPassword={confirmPassword} policy={policy} />
        <Button type="submit" fullWidth loading={submitting} disabled={submitting}>
          Reset password
        </Button>
      </form>

      <Link
        to="/auth/login"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors mt-5"
      >
        <ArrowLeft size={15} />
        Back to sign in
      </Link>
    </AuthLayout>
  );
}
