import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, MailCheck } from 'lucide-react';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { platformAdminApi, toSafeUserMessage } from '../../api';

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [fieldError, setFieldError] = useState<string | undefined>();
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setFieldError('Enter a valid email address.');
      return;
    }
    setFieldError(undefined);
    setSubmitting(true);
    try {
      await platformAdminApi.forgotPassword(email.trim());
      // Generic outcome regardless of whether the account exists, so the
      // response never confirms or denies account existence.
      setSubmitted(true);
    } catch (error) {
      setFormError(toSafeUserMessage(error));
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <AuthLayout>
        <div className="text-center">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center mx-auto mb-4">
            <MailCheck size={22} className="text-emerald-600" />
          </div>
          <h1 className="text-xl font-bold text-slate-900">Check your email</h1>
          <p className="text-sm text-slate-500 mt-2 leading-relaxed">
            If an account exists for <span className="font-medium text-slate-700">{email}</span>, we've sent
            instructions to reset your password.
          </p>
          <Link
            to="/auth/login"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-700 hover:text-slate-900 transition-colors mt-6"
          >
            <ArrowLeft size={15} />
            Back to sign in
          </Link>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 leading-tight">Forgot password?</h1>
        <p className="text-sm text-slate-500 mt-1.5">Enter your email and we'll send you a link to reset it.</p>
      </div>

      {formError && (
        <div className="mb-4">
          <Alert variant="error">{formError}</Alert>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        <Input
          label="Email address"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          error={fieldError}
          disabled={submitting}
          placeholder="you@company.com"
        />
        <Button type="submit" fullWidth loading={submitting} disabled={submitting}>
          Send reset link
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
