import { FormEvent, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { toSafeUserMessage } from '../../api';
import { useAuth } from '../../lib/auth/AuthProvider';

interface LocationState {
  from?: string;
}

export function LoginPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function validate(): boolean {
    const errors: { email?: string; password?: string } = {};
    if (!email.trim()) errors.email = 'Email address is required.';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = 'Enter a valid email address.';
    if (!password) errors.password = 'Password is required.';
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    if (!validate()) return;

    setSubmitting(true);
    try {
      const outcome = await signIn(email.trim(), password);
      if (outcome === 'mfa_required') {
        navigate('/auth/mfa/verify');
        return;
      }
      const from = (location.state as LocationState | null)?.from;
      navigate(from && from !== '/auth/login' ? from : '/', { replace: true });
    } catch (error) {
      setFormError(toSafeUserMessage(error, 'login'));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900 leading-tight">Welcome back</h1>
        <p className="text-sm text-slate-500 mt-1.5">Sign in to continue to gNxtHire.</p>
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
          error={fieldErrors.email}
          disabled={submitting}
          placeholder="you@company.com"
        />

        <div>
          <Input
            label="Password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            error={fieldErrors.password}
            disabled={submitting}
            placeholder="••••••••••"
          />
          <div className="flex justify-end mt-2">
            <Link to="/auth/forgot-password" className="text-xs font-medium text-slate-600 hover:text-slate-900 transition-colors">
              Forgot password?
            </Link>
          </div>
        </div>

        <Button type="submit" fullWidth loading={submitting} disabled={submitting}>
          Sign in
        </Button>
      </form>
    </AuthLayout>
  );
}
