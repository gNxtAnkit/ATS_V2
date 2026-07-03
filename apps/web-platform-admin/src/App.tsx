import { FormEvent, ReactNode, createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import QRCode from 'qrcode';
import {
  AlertCircle,
  CheckCircle2,
  KeyRound,
  Lock,
  LogOut,
  Mail,
  Network,
  Plus,
  ReceiptText,
  RefreshCw,
  Search,
  Shield,
  SlidersHorizontal,
  Sparkles,
  TicketCheck,
  UserCheck,
  Users,
} from 'lucide-react';
import { Link, Navigate, NavLink, Route, Routes, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { ApiError, platformAdminApi, platformControlApi, platformUsersApi } from './api';
import type {
  CurrentPlatformAdmin,
  LoginResponse,
  MfaChallenge,
  PasswordPolicyResponse,
  PlatformUser,
  TokenPair,
  TotpSetupResponse,
} from './types';

type JsonRecord = Record<string, unknown>;

interface PlatformModuleConfig {
  slug: string;
  title: string;
  description: string;
  icon: typeof Shield;
  readPermission: string;
  listPath: string;
  detailPath?: (record: JsonRecord) => string | null;
  actions?: PlatformActionConfig[];
}

interface PlatformActionConfig {
  label: string;
  permission: string;
  method: 'POST' | 'PATCH' | 'PUT' | 'DELETE';
  path: (record: JsonRecord | null) => string | null;
  body?: (record: JsonRecord | null) => JsonRecord | undefined;
  confirm?: string;
}

const SESSION_KEY = 'gnxthire.platformAdmin.session';
const MFA_CHALLENGE_KEY = 'gnxthire.platformAdmin.mfaChallenge';

const PLATFORM_MODULES: PlatformModuleConfig[] = [
  {
    slug: 'tenants',
    title: 'Tenants',
    description: 'Search tenants, inspect lifecycle state, domains, provisioning, entitlements, and support context.',
    icon: Network,
    readPermission: 'platform.tenant.read',
    listPath: '/v1/platform-admin/tenants',
    detailPath: (record) => idPath('/v1/platform-admin/tenants', record.id),
    actions: [
      {
        label: 'Suspend',
        permission: 'platform.tenant.lifecycle.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/tenants', record?.id, 'suspend'),
        body: () => ({ reason: 'Manual Platform Admin UI smoke action' }),
        confirm: 'Suspend this tenant?',
      },
      {
        label: 'Reactivate',
        permission: 'platform.tenant.lifecycle.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/tenants', record?.id, 'reactivate'),
        body: () => ({ reason: 'Manual Platform Admin UI smoke action' }),
        confirm: 'Reactivate this tenant?',
      },
    ],
  },
  {
    slug: 'provisioning',
    title: 'Provisioning',
    description: 'Review tenant provisioning jobs and retry or cancel failed work where supported.',
    icon: RefreshCw,
    readPermission: 'platform.provisioning.read',
    listPath: '/v1/platform-admin/provisioning-jobs',
    detailPath: (record) => idPath('/v1/platform-admin/provisioning-jobs', record.id),
    actions: [
      {
        label: 'Retry',
        permission: 'platform.provisioning.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/provisioning-jobs', record?.id, 'retry'),
        confirm: 'Retry this provisioning job?',
      },
      {
        label: 'Cancel',
        permission: 'platform.provisioning.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/provisioning-jobs', record?.id, 'cancel'),
        confirm: 'Cancel this provisioning job?',
      },
    ],
  },
  {
    slug: 'plans',
    title: 'Plans, Quotas, Features, Add-ons',
    description: 'Manage the catalogue that controls subscription capabilities and effective entitlements.',
    icon: ReceiptText,
    readPermission: 'platform.plan.read',
    listPath: '/v1/platform-admin/plans',
    detailPath: (record) => idPath('/v1/platform-admin/plans', record.id),
    actions: [
      {
        label: 'Activate',
        permission: 'platform.plan.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/plans', record?.id, 'activate'),
      },
      {
        label: 'Retire',
        permission: 'platform.plan.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/plans', record?.id, 'retire'),
        confirm: 'Retire this plan?',
      },
    ],
  },
  {
    slug: 'feature-flags',
    title: 'Feature Flags',
    description: 'Inspect rollout settings, tenant overrides, and kill switch state.',
    icon: SlidersHorizontal,
    readPermission: 'platform.feature_flag.read',
    listPath: '/v1/platform-admin/feature-flags',
    detailPath: (record) => idPath('/v1/platform-admin/feature-flags', record.id),
  },
  {
    slug: 'access-control',
    title: 'Users, Roles, Permissions',
    description: 'Review platform administrators, role assignment, and permission matrices.',
    icon: Users,
    readPermission: 'platform.user.read',
    listPath: '/v1/platform-admin/access-control/users',
    detailPath: (record) => idPath('/v1/platform-admin/access-control/users', record.id),
    actions: [
      {
        label: 'Lock',
        permission: 'platform.user.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/access-control/users', record?.id, 'lock'),
        confirm: 'Lock this platform admin?',
      },
      {
        label: 'Unlock',
        permission: 'platform.user.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/access-control/users', record?.id, 'unlock'),
      },
    ],
  },
  {
    slug: 'support',
    title: 'Support',
    description: 'Manage support sessions, support tickets, and SLA policy records.',
    icon: TicketCheck,
    readPermission: 'platform.support_ticket.read',
    listPath: '/v1/platform-admin/support-tickets',
    detailPath: (record) => idPath('/v1/platform-admin/support-tickets', record.id),
    actions: [
      {
        label: 'Close',
        permission: 'platform.support_ticket.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/support-tickets', record?.id, 'close'),
        body: () => ({ resolution_summary: 'Closed from Platform Admin UI smoke flow.' }),
        confirm: 'Close this ticket?',
      },
    ],
  },
  {
    slug: 'compliance',
    title: 'Compliance',
    description: 'Review frameworks, region mappings, and tenant compliance assignments.',
    icon: Shield,
    readPermission: 'platform.compliance.read',
    listPath: '/v1/platform-admin/compliance/frameworks',
    detailPath: (record) => idPath('/v1/platform-admin/compliance/frameworks', record.id),
  },
  {
    slug: 'ai-governance',
    title: 'AI Governance',
    description: 'Review AI models, quality metrics, region restrictions, and governance alerts.',
    icon: Sparkles,
    readPermission: 'platform.ai_governance.read',
    listPath: '/v1/platform-admin/ai/governance-alerts',
    detailPath: (record) => idPath('/v1/platform-admin/ai/governance-alerts', record.id),
    actions: [
      {
        label: 'Acknowledge',
        permission: 'platform.ai_governance.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/ai/governance-alerts', record?.id, 'acknowledge'),
      },
      {
        label: 'Resolve',
        permission: 'platform.ai_governance.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/ai/governance-alerts', record?.id, 'resolve'),
        confirm: 'Resolve this AI governance alert?',
      },
    ],
  },
  {
    slug: 'operations',
    title: 'Operations',
    description: 'Inspect API versions, deployments, SLO definitions, and error budget status.',
    icon: Search,
    readPermission: 'platform.operations.read',
    listPath: '/v1/platform-admin/api-versions',
    detailPath: (record) => idPath('/v1/platform-admin/api-versions', record.id),
  },
  {
    slug: 'audit-logs',
    title: 'Audit Logs',
    description: 'Search redacted platform audit records for security-sensitive changes.',
    icon: ReceiptText,
    readPermission: 'platform.audit_log.read',
    listPath: '/v1/platform-admin/audit-logs',
    detailPath: (record) => idPath('/v1/platform-admin/audit-logs', record.id),
  },
];

function idPath(basePath: string, id: unknown, suffix?: string): string | null {
  if (typeof id !== 'string' || id.length === 0) {
    return null;
  }
  return suffix ? `${basePath}/${id}/${suffix}` : `${basePath}/${id}`;
}

function displayValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '-';
  }
  if (typeof value === 'object') {
    return JSON.stringify(value);
  }
  return String(value);
}

function firstColumns(rows: JsonRecord[]): string[] {
  const preferred = ['name', 'display_name', 'email', 'code', 'status', 'title', 'subject', 'framework', 'flag_key', 'created_at'];
  const available = new Set(rows.flatMap((row) => Object.keys(row)));
  const selected = preferred.filter((key) => available.has(key));
  if (selected.length >= 3) {
    return selected.slice(0, 5);
  }
  return Array.from(available).slice(0, 5);
}

interface StoredSession {
  tokens: TokenPair;
  admin: CurrentPlatformAdmin;
}

interface AuthContextValue {
  admin: CurrentPlatformAdmin | null;
  tokens: TokenPair | null;
  loading: boolean;
  signIn(email: string, password: string): Promise<'authenticated' | 'mfa_required'>;
  completeLogin(response: LoginResponse): Promise<void>;
  refreshCurrentAdmin(): Promise<CurrentPlatformAdmin>;
  withFreshToken<T>(operation: (accessToken: string) => Promise<T>): Promise<T>;
  signOut(): Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredSession(): StoredSession | null {
  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as StoredSession;
  } catch {
    window.localStorage.removeItem(SESSION_KEY);
    return null;
  }
}

function saveMfaChallenge(response: LoginResponse): void {
  const challengeToken = response.challenge_token ?? response.mfa_challenge_token;
  if (!challengeToken) {
    throw new Error('MFA challenge token was not returned by the server.');
  }

  const expiresAt = response.expires_in_seconds ? Date.now() + response.expires_in_seconds * 1000 : null;
  const challenge: MfaChallenge = {
    token: challengeToken,
    availableMethods: response.available_methods,
    expiresAt,
  };
  window.localStorage.setItem(MFA_CHALLENGE_KEY, JSON.stringify(challenge));
}

function readMfaChallenge(): MfaChallenge | null {
  const raw = window.localStorage.getItem(MFA_CHALLENGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const challenge = JSON.parse(raw) as MfaChallenge;
    if (challenge.expiresAt && challenge.expiresAt <= Date.now()) {
      window.localStorage.removeItem(MFA_CHALLENGE_KEY);
      return null;
    }
    return challenge;
  } catch {
    window.localStorage.removeItem(MFA_CHALLENGE_KEY);
    return null;
  }
}

function userMessage(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message;
  }
  return 'Something went wrong. Please try again.';
}

function AuthProvider({ children }: { children: ReactNode }) {
  const [tokens, setTokens] = useState<TokenPair | null>(() => readStoredSession()?.tokens ?? null);
  const [admin, setAdmin] = useState<CurrentPlatformAdmin | null>(() => readStoredSession()?.admin ?? null);
  const [loading, setLoading] = useState(true);

  const persistSession = useCallback((nextTokens: TokenPair, nextAdmin: CurrentPlatformAdmin) => {
    setTokens(nextTokens);
    setAdmin(nextAdmin);
    window.localStorage.setItem(SESSION_KEY, JSON.stringify({ tokens: nextTokens, admin: nextAdmin }));
  }, []);

  const clearSession = useCallback(() => {
    setTokens(null);
    setAdmin(null);
    window.localStorage.removeItem(SESSION_KEY);
  }, []);

  const completeLogin = useCallback(async (response: LoginResponse) => {
    if (!response.tokens) {
      throw new Error('The server did not return session tokens.');
    }
    const nextAdmin = await platformAdminApi.me(response.tokens.access_token);
    persistSession(response.tokens, nextAdmin);
    window.localStorage.removeItem(MFA_CHALLENGE_KEY);
  }, [persistSession]);

  const signIn = useCallback(async (email: string, password: string) => {
    const response = await platformAdminApi.login(email, password);
    if (response.mfa_required) {
      saveMfaChallenge(response);
      return 'mfa_required';
    }
    await completeLogin(response);
    return 'authenticated';
  }, [completeLogin]);

  const refreshCurrentAdmin = useCallback(async () => {
    if (!tokens) {
      throw new Error('Your admin session has expired.');
    }
    const nextAdmin = await platformAdminApi.me(tokens.access_token);
    persistSession(tokens, nextAdmin);
    return nextAdmin;
  }, [persistSession, tokens]);

  const refreshTokens = useCallback(async (currentTokens: TokenPair) => {
    const nextTokens = await platformAdminApi.refresh(currentTokens.refresh_token);
    const nextAdmin = await platformAdminApi.me(nextTokens.access_token);
    persistSession(nextTokens, nextAdmin);
    return nextTokens;
  }, [persistSession]);

  const withFreshToken = useCallback(async <T,>(operation: (accessToken: string) => Promise<T>) => {
    if (!tokens) {
      throw new Error('Your admin session has expired.');
    }

    try {
      return await operation(tokens.access_token);
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 401) {
        throw error;
      }
      const nextTokens = await refreshTokens(tokens);
      return operation(nextTokens.access_token);
    }
  }, [refreshTokens, tokens]);

  const signOut = useCallback(async () => {
    const currentTokens = tokens;
    clearSession();
    window.localStorage.removeItem(MFA_CHALLENGE_KEY);
    if (currentTokens) {
      try {
        await platformAdminApi.logout(currentTokens.refresh_token, currentTokens.access_token);
      } catch {
        return;
      }
    }
  }, [clearSession, tokens]);

  useEffect(() => {
    let active = true;
    const stored = readStoredSession();

    async function validateSession() {
      if (!stored) {
        setLoading(false);
        return;
      }

      try {
        const nextAdmin = await platformAdminApi.me(stored.tokens.access_token);
        if (active) {
          persistSession(stored.tokens, nextAdmin);
        }
      } catch {
        try {
          const nextTokens = await platformAdminApi.refresh(stored.tokens.refresh_token);
          const nextAdmin = await platformAdminApi.me(nextTokens.access_token);
          if (active) {
            persistSession(nextTokens, nextAdmin);
          }
        } catch {
          if (active) {
            clearSession();
          }
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void validateSession();
    return () => {
      active = false;
    };
  }, [clearSession, persistSession]);

  const value = useMemo<AuthContextValue>(() => ({
    admin,
    tokens,
    loading,
    signIn,
    completeLogin,
    refreshCurrentAdmin,
    withFreshToken,
    signOut,
  }), [admin, completeLogin, loading, refreshCurrentAdmin, signIn, signOut, tokens, withFreshToken]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error('AuthContext is not available.');
  }
  return value;
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}

function Notice({ kind, children }: { kind: 'success' | 'error' | 'info'; children: ReactNode }) {
  const Icon = kind === 'success' ? CheckCircle2 : kind === 'error' ? AlertCircle : Shield;
  return (
    <div className={`notice ${kind}`}>
      <Icon size={18} />
      <span>{children}</span>
    </div>
  );
}

function SubmitButton({ loading, children }: { loading: boolean; children: ReactNode }) {
  return (
    <button className="primary-button" disabled={loading} type="submit">
      {loading ? <RefreshCw className="spin" size={18} /> : null}
      {children}
    </button>
  );
}

function AuthShell({ children, title, subtitle }: { children: ReactNode; title: string; subtitle: string }) {
  return (
    <main className="auth-page">
      <section className="auth-panel">
        <div className="brand-lockup">
          <div className="brand-mark"><Shield size={24} /></div>
          <div>
            <p>Gnxthire</p>
            <strong>Platform Admin</strong>
          </div>
        </div>
        <div className="auth-heading">
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        {children}
      </section>
    </main>
  );
}

function LoginPage() {
  const { admin, loading, signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!loading && admin) {
    return <Navigate to="/" replace />;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const outcome = await signIn(email, password);
      if (outcome === 'mfa_required') {
        navigate('/mfa/verify', { replace: true });
      } else {
        const redirectTo = typeof location.state === 'object' && location.state && 'from' in location.state
          ? String(location.state.from)
          : '/';
        navigate(redirectTo, { replace: true });
      }
    } catch (err) {
      setError(userMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell title="Admin sign in" subtitle="Use your platform administrator credentials.">
      <form className="stack" onSubmit={onSubmit}>
        {error ? <Notice kind="error">{error}</Notice> : null}
        <Field label="Work email">
          <input autoComplete="email" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
        </Field>
        <Field label="Password">
          <input autoComplete="current-password" onChange={(event) => setPassword(event.target.value)} required type="password" value={password} />
        </Field>
        <SubmitButton loading={submitting}>Sign in</SubmitButton>
      </form>
      <div className="auth-links">
        <Link to="/forgot-password">Forgot password?</Link>
        <Link to="/request-email-verification">Verify email</Link>
      </div>
    </AuthShell>
  );
}

function MfaVerifyPage() {
  const { completeLogin } = useAuth();
  const navigate = useNavigate();
  const [challenge] = useState<MfaChallenge | null>(() => readMfaChallenge());
  const [mode, setMode] = useState<'totp' | 'recovery'>('totp');
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const recoveryAllowed = challenge?.availableMethods.includes('recovery_code') ?? false;

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!challenge) {
      setError('Your MFA challenge has expired. Please sign in again.');
      return;
    }

    setError(null);
    setSubmitting(true);
    try {
      const response = mode === 'recovery'
        ? await platformAdminApi.verifyRecoveryCode(challenge.token, code)
        : await platformAdminApi.verifyTotp(challenge.token, code);
      await completeLogin(response);
      navigate('/', { replace: true });
    } catch (err) {
      setError(userMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (!challenge) {
    return (
      <AuthShell title="MFA required" subtitle="The verification challenge has expired.">
        <Notice kind="error">Please sign in again to start a fresh MFA challenge.</Notice>
        <Link className="secondary-button" to="/login">Back to sign in</Link>
      </AuthShell>
    );
  }

  return (
    <AuthShell title="Verify MFA" subtitle="Enter the code from your authenticator app.">
      <form className="stack" onSubmit={onSubmit}>
        {error ? <Notice kind="error">{error}</Notice> : null}
        <div className="segmented">
          <button className={mode === 'totp' ? 'active' : ''} onClick={() => setMode('totp')} type="button">Authenticator</button>
          <button className={mode === 'recovery' ? 'active' : ''} disabled={!recoveryAllowed} onClick={() => setMode('recovery')} type="button">Recovery code</button>
        </div>
        <Field label={mode === 'recovery' ? 'Recovery code' : 'Authenticator code'}>
          <input autoComplete="one-time-code" inputMode="numeric" onChange={(event) => setCode(event.target.value)} required value={code} />
        </Field>
        <SubmitButton loading={submitting}>Verify and continue</SubmitButton>
      </form>
    </AuthShell>
  );
}

function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setSubmitting(true);
    try {
      const response = await platformAdminApi.forgotPassword(email);
      setMessage(response.message);
    } catch (err) {
      setError(userMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell title="Reset password" subtitle="Request a secure password reset email.">
      <form className="stack" onSubmit={onSubmit}>
        {message ? <Notice kind="success">{message}</Notice> : null}
        {error ? <Notice kind="error">{error}</Notice> : null}
        <Field label="Work email">
          <input autoComplete="email" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
        </Field>
        <SubmitButton loading={submitting}>Send reset email</SubmitButton>
      </form>
      <div className="auth-links"><Link to="/login">Back to sign in</Link></div>
    </AuthShell>
  );
}

function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [policy, setPolicy] = useState<PasswordPolicyResponse | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(token ? null : 'The reset token is missing from the URL.');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    platformAdminApi.passwordPolicy().then(setPolicy).catch(() => setPolicy(null));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setSubmitting(true);
    try {
      const response = await platformAdminApi.resetPassword(token, password, confirmPassword);
      setMessage(response.message);
    } catch (err) {
      setError(userMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell title="Choose a new password" subtitle="Complete the password reset from your email link.">
      <form className="stack" onSubmit={onSubmit}>
        {message ? <Notice kind="success">{message}</Notice> : null}
        {error ? <Notice kind="error">{error}</Notice> : null}
        {policy ? <p className="hint">Minimum {policy.min_length} characters. Use the mix required by platform policy.</p> : null}
        <Field label="New password">
          <input autoComplete="new-password" disabled={!token} onChange={(event) => setPassword(event.target.value)} required type="password" value={password} />
        </Field>
        <Field label="Confirm password">
          <input autoComplete="new-password" disabled={!token} onChange={(event) => setConfirmPassword(event.target.value)} required type="password" value={confirmPassword} />
        </Field>
        <SubmitButton loading={submitting}>Update password</SubmitButton>
      </form>
      <div className="auth-links"><Link to="/login">Back to sign in</Link></div>
    </AuthShell>
  );
}

function RequestEmailVerificationPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setSubmitting(true);
    try {
      const response = await platformAdminApi.requestEmailVerification(email);
      setMessage(response.message);
    } catch (err) {
      setError(userMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell title="Verify email" subtitle="Send a platform-admin email verification link.">
      <form className="stack" onSubmit={onSubmit}>
        {message ? <Notice kind="success">{message}</Notice> : null}
        {error ? <Notice kind="error">{error}</Notice> : null}
        <Field label="Work email">
          <input autoComplete="email" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
        </Field>
        <SubmitButton loading={submitting}>Send verification email</SubmitButton>
      </form>
      <div className="auth-links"><Link to="/login">Back to sign in</Link></div>
    </AuthShell>
  );
}

function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(token ? null : 'The verification token is missing from the URL.');

  useEffect(() => {
    if (!token) {
      return;
    }

    platformAdminApi.verifyEmail(token).then((response) => {
      setMessage(response.message);
    }).catch((err: unknown) => {
      setError(userMessage(err));
    });
  }, [token]);

  return (
    <AuthShell title="Email verification" subtitle="Completing your platform-admin verification.">
      <div className="stack">
        {message ? <Notice kind="success">{message}</Notice> : null}
        {error ? <Notice kind="error">{error}</Notice> : null}
        {!message && !error ? <Notice kind="info">Verifying your email link...</Notice> : null}
        <Link className="secondary-button" to="/login">Back to sign in</Link>
      </div>
    </AuthShell>
  );
}

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { admin, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <main className="loading-page">Loading platform admin...</main>;
  }

  if (!admin) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <>{children}</>;
}

function usePlatformPermissions() {
  const { admin, withFreshToken } = useAuth();
  const [permissions, setPermissions] = useState<Set<string>>(new Set());
  const [loadingPermissions, setLoadingPermissions] = useState(true);

  useEffect(() => {
    let active = true;
    async function loadPermissions() {
      if (!admin) {
        setLoadingPermissions(false);
        return;
      }
      setLoadingPermissions(true);
      try {
        const rolePage = await withFreshToken((accessToken) => platformControlApi.list<JsonRecord>(
          accessToken,
          `/v1/platform-admin/access-control/users/${admin.actor_id}/roles`,
        ));
        const loaded = new Set<string>();
        await Promise.all(rolePage.data.map(async (role) => {
          const roleId = role.id;
          if (typeof roleId !== 'string') {
            return;
          }
          const permissionPage = await withFreshToken((accessToken) => platformControlApi.list<JsonRecord>(
            accessToken,
            `/v1/platform-admin/access-control/roles/${roleId}/permissions`,
          ));
          permissionPage.data.forEach((permission) => {
            const permissionKey = permission.permission_key;
            if (typeof permissionKey === 'string') {
              loaded.add(permissionKey);
            }
          });
        }));
        if (active) {
          setPermissions(loaded);
        }
      } catch {
        if (active) {
          setPermissions(new Set());
        }
      } finally {
        if (active) {
          setLoadingPermissions(false);
        }
      }
    }

    void loadPermissions();
    return () => {
      active = false;
    };
  }, [admin, withFreshToken]);

  return { permissions, loadingPermissions };
}

function useCan(permissions: Set<string>) {
  return useCallback((permission: string) => permissions.has(permission), [permissions]);
}

function AdminLayout() {
  const { admin, signOut } = useAuth();
  const { permissions, loadingPermissions } = usePlatformPermissions();
  const can = useCan(permissions);
  const navigate = useNavigate();
  const visibleModules = PLATFORM_MODULES.filter((module) => can(module.readPermission));

  async function onSignOut() {
    await signOut();
    navigate('/login', { replace: true });
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup compact">
          <div className="brand-mark"><Shield size={22} /></div>
          <div>
            <p>Gnxthire</p>
            <strong>Platform Admin</strong>
          </div>
        </div>
        <nav>
          <NavLink to="/" end><Shield size={18} /> Overview</NavLink>
          {visibleModules.map((module) => (
            <NavLink key={module.slug} to={`/platform/${module.slug}`}>
              <module.icon size={18} /> {module.title}
            </NavLink>
          ))}
          <NavLink to="/users"><Users size={18} /> Identity users</NavLink>
          <NavLink to="/security"><KeyRound size={18} /> Security</NavLink>
        </nav>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div>
            <p>Signed in as</p>
            <strong>{admin?.display_name}</strong>
          </div>
          <button className="ghost-button" onClick={onSignOut} type="button"><LogOut size={18} /> Sign out</button>
        </header>
        <Routes>
          <Route element={<OverviewPage />} path="/" />
          <Route element={<UsersPage />} path="/users" />
          <Route element={<SecurityPage />} path="/security" />
          {PLATFORM_MODULES.map((module) => (
            <Route
              key={module.slug}
              element={(
                <PlatformModulePage
                  can={can}
                  loadingPermissions={loadingPermissions}
                  module={module}
                />
              )}
              path={`/platform/${module.slug}`}
            />
          ))}
        </Routes>
      </div>
    </div>
  );
}

function OverviewPage() {
  const { admin, withFreshToken } = useAuth();
  const [summary, setSummary] = useState<JsonRecord | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    withFreshToken((accessToken) => platformControlApi.get<JsonRecord>(accessToken, '/v1/platform-admin/dashboard/summary'))
      .then((response) => {
        if (active) {
          setSummary(response.data);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(userMessage(err));
        }
      });
    return () => {
      active = false;
    };
  }, [withFreshToken]);

  return (
    <main className="content">
      <section className="page-heading">
        <div>
          <h1>Platform administration</h1>
          <p>Operate tenants, catalogue, support, governance, operations, audit, and access control.</p>
        </div>
      </section>
      {error ? <Notice kind="error">{error}</Notice> : null}
      <div className="metric-grid">
        <article className="metric-card">
          <Mail size={22} />
          <span>Email status</span>
          <strong>{admin?.email_verified ? 'Verified' : 'Not verified'}</strong>
        </article>
        <article className="metric-card">
          <Shield size={22} />
          <span>MFA status</span>
          <strong>{admin?.mfa_enabled ? 'Enabled' : 'Not enabled'}</strong>
        </article>
        <article className="metric-card">
          <KeyRound size={22} />
          <span>Recovery codes</span>
          <strong>{admin?.recovery_codes_remaining ?? 0} available</strong>
        </article>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <Shield size={22} />
          <div>
            <h2>Control-plane summary</h2>
            <p>Live dashboard payload from the Platform Admin API.</p>
          </div>
        </div>
        {summary ? <JsonViewer value={summary} /> : <p className="empty-state">Loading dashboard summary...</p>}
      </section>
    </main>
  );
}

function JsonViewer({ value }: { value: unknown }) {
  return <pre className="json-viewer">{JSON.stringify(value, null, 2)}</pre>;
}

function DataTable({
  rows,
  selectedId,
  onSelect,
}: {
  rows: JsonRecord[];
  selectedId: string | null;
  onSelect(record: JsonRecord): void;
}) {
  if (rows.length === 0) {
    return <p className="empty-state">No records returned by the API.</p>;
  }

  const columns = firstColumns(rows);
  return (
    <div className="table-shell">
      <table>
        <thead>
          <tr>
            {columns.map((column) => <th key={column}>{column.split('_').join(' ')}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => {
            const id = typeof row.id === 'string' ? row.id : `${index}`;
            return (
              <tr className={selectedId === id ? 'selected' : ''} key={id} onClick={() => onSelect(row)}>
                {columns.map((column) => <td key={column}>{displayValue(row[column])}</td>)}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function PlatformModulePage({
  module,
  can,
  loadingPermissions,
}: {
  module: PlatformModuleConfig;
  can(permission: string): boolean;
  loadingPermissions: boolean;
}) {
  const { withFreshToken } = useAuth();
  const [records, setRecords] = useState<JsonRecord[]>([]);
  const [selected, setSelected] = useState<JsonRecord | null>(null);
  const [detail, setDetail] = useState<JsonRecord | null>(null);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  const loadRecords = useCallback(async () => {
    setLoading(true);
    setError(null);
    const query: Record<string, string> = { limit: '50' };
    if (search) {
      query.search = search;
    }
    if (status) {
      query.status = status;
    }
    try {
      const response = await withFreshToken((accessToken) => platformControlApi.list<JsonRecord>(
        accessToken,
        module.listPath,
        query,
      ));
      setRecords(response.data);
      setSelected(response.data[0] ?? null);
      setDetail(null);
    } catch (err) {
      setError(userMessage(err));
    } finally {
      setLoading(false);
    }
  }, [module.listPath, search, status, withFreshToken]);

  useEffect(() => {
    if (loadingPermissions || !can(module.readPermission)) {
      setLoading(false);
      return;
    }
    void loadRecords();
  }, [can, loadRecords, loadingPermissions, module.readPermission]);

  useEffect(() => {
    let active = true;
    const detailPath = selected && module.detailPath ? module.detailPath(selected) : null;
    if (!detailPath) {
      setDetail(null);
      return;
    }
    withFreshToken((accessToken) => platformControlApi.get<JsonRecord>(accessToken, detailPath))
      .then((response) => {
        if (active) {
          setDetail(response.data);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(userMessage(err));
        }
      });
    return () => {
      active = false;
    };
  }, [module, selected, withFreshToken]);

  async function runAction(action: PlatformActionConfig) {
    if (!can(action.permission)) {
      setError('You do not have permission to perform this action.');
      return;
    }
    if (action.confirm && !window.confirm(action.confirm)) {
      return;
    }
    const path = action.path(selected);
    if (!path) {
      setError('Select a record before running this action.');
      return;
    }

    setBusy(action.label);
    setError(null);
    setMessage(null);
    try {
      await withFreshToken((accessToken) => {
        const body = action.body ? action.body(selected) : undefined;
        if (action.method === 'PATCH') {
          return platformControlApi.patch(accessToken, path, body ?? {});
        }
        if (action.method === 'PUT') {
          return platformControlApi.put(accessToken, path, body ?? {});
        }
        if (action.method === 'DELETE') {
          return platformControlApi.delete(accessToken, path);
        }
        return platformControlApi.post(accessToken, path, body);
      });
      setMessage(`${action.label} completed.`);
      await loadRecords();
    } catch (err) {
      setError(userMessage(err));
    } finally {
      setBusy(null);
    }
  }

  if (loadingPermissions) {
    return <main className="content"><p className="empty-state">Checking permissions...</p></main>;
  }

  if (!can(module.readPermission)) {
    return (
      <main className="content">
        <Notice kind="error">Your current role does not include {module.readPermission}.</Notice>
      </main>
    );
  }

  return (
    <main className="content">
      <section className="page-heading">
        <div>
          <h1>{module.title}</h1>
          <p>{module.description}</p>
        </div>
        <button className="secondary-button" disabled={loading} onClick={loadRecords} type="button">
          {loading ? <RefreshCw className="spin" size={18} /> : <RefreshCw size={18} />}
          Refresh
        </button>
      </section>
      {message ? <Notice kind="success">{message}</Notice> : null}
      {error ? <Notice kind="error">{error}</Notice> : null}
      <section className="panel">
        <div className="filters">
          <Field label="Search">
            <input onChange={(event) => setSearch(event.target.value)} placeholder="Search API-supported fields" value={search} />
          </Field>
          <Field label="Status">
            <input onChange={(event) => setStatus(event.target.value)} placeholder="active, open, failed..." value={status} />
          </Field>
          <button className="primary-button" disabled={loading} onClick={loadRecords} type="button">Apply filters</button>
        </div>
      </section>
      <div className="two-column module-layout">
        <section className="panel">
          <div className="panel-heading">
            <module.icon size={22} />
            <div>
              <h2>Records</h2>
              <p>{loading ? 'Loading from API...' : `${records.length} records loaded`}</p>
            </div>
          </div>
          {loading ? <p className="empty-state">Loading...</p> : (
            <DataTable
              rows={records}
              selectedId={selected && typeof selected.id === 'string' ? selected.id : null}
              onSelect={setSelected}
            />
          )}
        </section>
        <section className="panel">
          <div className="panel-heading">
            <Shield size={22} />
            <div>
              <h2>Detail and actions</h2>
              <p>All actions call the real Platform Admin API.</p>
            </div>
          </div>
          {module.actions?.length ? (
            <div className="row-actions module-actions">
              {module.actions.map((action) => (
                <button
                  disabled={!selected || !can(action.permission) || busy === action.label}
                  key={action.label}
                  onClick={() => void runAction(action)}
                  type="button"
                >
                  {busy === action.label ? 'Working...' : action.label}
                </button>
              ))}
            </div>
          ) : null}
          {detail ? <JsonViewer value={detail} /> : <p className="empty-state">Select a record to inspect details.</p>}
        </section>
      </div>
    </main>
  );
}

function RecoveryCodesPanel({ codes }: { codes: string[] }) {
  if (codes.length === 0) {
    return null;
  }
  return (
    <div className="recovery-codes">
      <Notice kind="info">Store these recovery codes now. They are shown once.</Notice>
      <div className="code-grid">
        {codes.map((code) => <code key={code}>{code}</code>)}
      </div>
    </div>
  );
}

function SecurityPage() {
  const { admin, refreshCurrentAdmin, withFreshToken } = useAuth();
  const [setup, setSetup] = useState<TotpSetupResponse | null>(null);
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [totpCode, setTotpCode] = useState('');
  const [password, setPassword] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    if (!setup) {
      setQrCode(null);
      return;
    }

    QRCode.toDataURL(setup.provisioning_uri, { errorCorrectionLevel: 'M', margin: 2, width: 220 })
      .then((dataUrl) => {
        if (active) {
          setQrCode(dataUrl);
        }
      })
      .catch(() => {
        if (active) {
          setQrCode(null);
        }
      });

    return () => {
      active = false;
    };
  }, [setup]);

  async function runSecurityAction(name: string, action: () => Promise<void>) {
    setBusy(name);
    setError(null);
    setMessage(null);
    try {
      await action();
    } catch (err) {
      setError(userMessage(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="content">
      <section className="page-heading">
        <div>
          <h1>Security</h1>
          <p>Configure your platform-admin password and multi-factor authentication.</p>
        </div>
      </section>
      <div className="two-column security-grid">
        <section className="panel">
          <div className="panel-heading">
            <Shield size={22} />
            <div>
              <h2>Authenticator app</h2>
              <p>{admin?.mfa_enabled ? 'TOTP is enabled for your admin account.' : 'Set up TOTP before managing production accounts.'}</p>
            </div>
          </div>
          <div className="stack">
            {message ? <Notice kind="success">{message}</Notice> : null}
            {error ? <Notice kind="error">{error}</Notice> : null}
            {!admin?.mfa_enabled && !setup ? (
              <button className="primary-button" disabled={busy === 'setup'} onClick={() => runSecurityAction('setup', async () => {
                const response = await withFreshToken((accessToken) => platformAdminApi.setupTotp(accessToken));
                setSetup(response);
              })} type="button">
                {busy === 'setup' ? <RefreshCw className="spin" size={18} /> : <Shield size={18} />}
                Start MFA setup
              </button>
            ) : null}
            {setup ? (
              <div className="mfa-setup">
                {qrCode ? <img alt="Authenticator QR code" src={qrCode} /> : <div className="qr-placeholder">Generating QR code...</div>}
                <div className="manual-secret">
                  <span>Manual entry secret</span>
                  <code>{setup.manual_entry_secret}</code>
                </div>
                <Field label="Authenticator code">
                  <input autoComplete="one-time-code" inputMode="numeric" onChange={(event) => setTotpCode(event.target.value)} value={totpCode} />
                </Field>
                <button className="primary-button" disabled={busy === 'confirm'} onClick={() => runSecurityAction('confirm', async () => {
                  const response = await withFreshToken((accessToken) => platformAdminApi.confirmTotp(accessToken, totpCode));
                  setRecoveryCodes(response.recovery_codes);
                  setSetup(null);
                  setTotpCode('');
                  await refreshCurrentAdmin();
                  setMessage('MFA is now enabled.');
                })} type="button">
                  {busy === 'confirm' ? <RefreshCw className="spin" size={18} /> : <CheckCircle2 size={18} />}
                  Confirm MFA
                </button>
              </div>
            ) : null}
            <RecoveryCodesPanel codes={recoveryCodes} />
          </div>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <KeyRound size={22} />
            <div>
              <h2>Password</h2>
              <p>Change the password for your signed-in platform-admin account.</p>
            </div>
          </div>
          <form className="stack" onSubmit={(event) => {
            event.preventDefault();
            void runSecurityAction('change-password', async () => {
              const response = await withFreshToken((accessToken) => platformAdminApi.changePassword(
                accessToken,
                currentPassword,
                newPassword,
                confirmPassword,
              ));
              setCurrentPassword('');
              setNewPassword('');
              setConfirmPassword('');
              setMessage(response.message);
            });
          }}>
            <Field label="Current password">
              <input autoComplete="current-password" onChange={(event) => setCurrentPassword(event.target.value)} required type="password" value={currentPassword} />
            </Field>
            <Field label="New password">
              <input autoComplete="new-password" onChange={(event) => setNewPassword(event.target.value)} required type="password" value={newPassword} />
            </Field>
            <Field label="Confirm new password">
              <input autoComplete="new-password" onChange={(event) => setConfirmPassword(event.target.value)} required type="password" value={confirmPassword} />
            </Field>
            <SubmitButton loading={busy === 'change-password'}>Change password</SubmitButton>
          </form>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <Lock size={22} />
            <div>
              <h2>Recovery and disable</h2>
              <p>{admin?.recovery_codes_remaining ?? 0} recovery codes are available.</p>
            </div>
          </div>
          <div className="stack">
            <Field label="Current password">
              <input autoComplete="current-password" onChange={(event) => setPassword(event.target.value)} type="password" value={password} />
            </Field>
            <button className="secondary-button" disabled={!admin?.mfa_enabled || !password || busy === 'regenerate'} onClick={() => runSecurityAction('regenerate', async () => {
              const response = await withFreshToken((accessToken) => platformAdminApi.regenerateRecoveryCodes(accessToken, password));
              setRecoveryCodes(response.recovery_codes);
              setPassword('');
              await refreshCurrentAdmin();
              setMessage('Recovery codes regenerated.');
            })} type="button">
              {busy === 'regenerate' ? <RefreshCw className="spin" size={18} /> : <RefreshCw size={18} />}
              Regenerate recovery codes
            </button>
            <button className="danger-button" disabled={!admin?.mfa_enabled || !password || busy === 'disable'} onClick={() => runSecurityAction('disable', async () => {
              await withFreshToken((accessToken) => platformAdminApi.disableMfa(accessToken, password));
              setPassword('');
              setRecoveryCodes([]);
              await refreshCurrentAdmin();
              setMessage('MFA has been disabled.');
            })} type="button">
              Disable MFA
            </button>
          </div>
        </section>
      </div>
    </main>
  );
}

function UsersPage() {
  const { withFreshToken } = useAuth();
  const [users, setUsers] = useState<PlatformUser[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [editingUserId, setEditingUserId] = useState<string | null>(null);
  const [editingDisplayName, setEditingDisplayName] = useState('');

  const loadUsers = useCallback(async (cursor: string | null = null) => {
    setLoading(true);
    setError(null);
    try {
      const page = await withFreshToken((accessToken) => platformUsersApi.list(accessToken, cursor));
      setUsers((current) => cursor ? [...current, ...page.data] : page.data);
      setNextCursor(page.next_cursor);
    } catch (err) {
      setError(userMessage(err));
    } finally {
      setLoading(false);
    }
  }, [withFreshToken]);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  async function createUser(event: FormEvent) {
    event.preventDefault();
    setBusy('create');
    setError(null);
    setMessage(null);
    try {
      const created = await withFreshToken((accessToken) => platformUsersApi.create(accessToken, email, displayName));
      setUsers((current) => [created, ...current]);
      setEmail('');
      setDisplayName('');
      setMessage('Platform admin user created.');
    } catch (err) {
      setError(userMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function runUserAction(user: PlatformUser, action: Parameters<typeof platformUsersApi.action>[2]) {
    setBusy(`${action}:${user.id}`);
    setError(null);
    setMessage(null);
    try {
      const updated = await withFreshToken((accessToken) => platformUsersApi.action(accessToken, user.id, action));
      setUsers((current) => current.map((item) => item.id === updated.id ? updated : item));
      setMessage('User updated.');
    } catch (err) {
      setError(userMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function updateDisplayName(event: FormEvent, user: PlatformUser) {
    event.preventDefault();
    setBusy(`update:${user.id}`);
    setError(null);
    setMessage(null);
    try {
      const updated = await withFreshToken((accessToken) => platformUsersApi.update(accessToken, user.id, editingDisplayName));
      setUsers((current) => current.map((item) => item.id === updated.id ? updated : item));
      setEditingUserId(null);
      setEditingDisplayName('');
      setMessage('User display name updated.');
    } catch (err) {
      setError(userMessage(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="content">
      <section className="page-heading">
        <div>
          <h1>Admin users</h1>
          <p>Create and govern platform administrators.</p>
        </div>
      </section>
      <div className="two-column users-layout">
        <section className="panel">
          <div className="panel-heading">
            <Plus size={22} />
            <div>
              <h2>Create admin user</h2>
              <p>The backend records this as a platform-admin audit event.</p>
            </div>
          </div>
          <form className="stack" onSubmit={createUser}>
            {message ? <Notice kind="success">{message}</Notice> : null}
            {error ? <Notice kind="error">{error}</Notice> : null}
            <Field label="Display name">
              <input onChange={(event) => setDisplayName(event.target.value)} required value={displayName} />
            </Field>
            <Field label="Work email">
              <input autoComplete="email" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
            </Field>
            <SubmitButton loading={busy === 'create'}>Create user</SubmitButton>
          </form>
        </section>
        <section className="panel user-list-panel">
          <div className="panel-heading">
            <Users size={22} />
            <div>
              <h2>Platform administrators</h2>
              <p>{loading ? 'Loading users...' : `${users.length} loaded`}</p>
            </div>
          </div>
          <div className="user-list">
            {users.map((user) => (
              <article className="user-row" key={user.id}>
                <div className="user-main">
                  <UserCheck size={20} />
                  <div>
                    {editingUserId === user.id ? (
                      <form className="inline-edit" onSubmit={(event) => updateDisplayName(event, user)}>
                        <input aria-label="Display name" onChange={(event) => setEditingDisplayName(event.target.value)} required value={editingDisplayName} />
                        <button disabled={busy === `update:${user.id}`} type="submit">Save</button>
                        <button onClick={() => {
                          setEditingUserId(null);
                          setEditingDisplayName('');
                        }} type="button">Cancel</button>
                      </form>
                    ) : (
                      <strong>{user.display_name}</strong>
                    )}
                    <span>{user.email}</span>
                  </div>
                </div>
                <div className="status-strip">
                  <span className={`pill ${user.status}`}>{user.status}</span>
                  <span className="pill">{user.email_verified ? 'email verified' : 'email pending'}</span>
                  <span className="pill">{user.mfa_enabled ? 'mfa enabled' : user.mfa_required ? 'mfa required' : 'mfa optional'}</span>
                </div>
                <div className="row-actions">
                  <button onClick={() => {
                    setEditingUserId(user.id);
                    setEditingDisplayName(user.display_name);
                  }} type="button">Edit name</button>
                  <button onClick={() => runUserAction(user, user.status === 'active' ? 'deactivate' : 'activate')} type="button">
                    {user.status === 'active' ? 'Deactivate' : 'Activate'}
                  </button>
                  <button onClick={() => runUserAction(user, user.status === 'locked' ? 'unlock' : 'lock')} type="button">
                    {user.status === 'locked' ? 'Unlock' : 'Lock'}
                  </button>
                  <button onClick={() => runUserAction(user, 'require-password-reset')} type="button">Require reset</button>
                  <button onClick={() => runUserAction(user, 'require-mfa')} type="button">Require MFA</button>
                </div>
              </article>
            ))}
            {!loading && users.length === 0 ? <p className="empty-state">No platform administrators were returned.</p> : null}
            {nextCursor ? (
              <button className="secondary-button" disabled={Boolean(busy)} onClick={() => loadUsers(nextCursor)} type="button">
                Load more
              </button>
            ) : null}
          </div>
        </section>
      </div>
    </main>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<LoginPage />} path="/login" />
        <Route element={<MfaVerifyPage />} path="/mfa/verify" />
        <Route element={<ForgotPasswordPage />} path="/forgot-password" />
        <Route element={<ResetPasswordPage />} path="/reset-password" />
        <Route element={<RequestEmailVerificationPage />} path="/request-email-verification" />
        <Route element={<VerifyEmailPage />} path="/verify-email" />
        <Route element={<ProtectedRoute><AdminLayout /></ProtectedRoute>} path="/*" />
      </Routes>
    </AuthProvider>
  );
}
