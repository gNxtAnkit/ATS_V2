import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Alert } from '../components/ui/Alert';
import { PasswordStrength } from '../components/ui/PasswordStrength';
import { useAuthSession } from '../lib/auth/authSession';
import { identityApi, type PasswordPolicyResponse } from '../lib/api/identityApi';
import { toSafeError, ApiError } from '../lib/api/apiErrors';
import {
  Mail,
  Clock,
  MapPin,
  BadgeCheck,
  Building2,
  CalendarDays,
  CheckCircle2,
  Pencil,
  KeyRound,
  ShieldCheck,
  ArrowUpRight,
  LogIn,
  Settings2,
  UserPlus,
  FileClock,
  ShieldAlert,
} from 'lucide-react';

const defaultPasswordPolicy: PasswordPolicyResponse = {
  min_length: 12,
  max_length: 128,
  require_uppercase: true,
  require_lowercase: true,
  require_number: true,
  require_special: true,
  prevent_email_similarity: true,
};

const statusStyles: Record<string, string> = {
  active: 'text-emerald-600',
  invited: 'text-blue-600',
  locked: 'text-red-600',
  suspended: 'text-red-600',
  deleted: 'text-slate-400',
};

function formatDateTime(iso: string | null): string {
  if (!iso) return 'Never signed in';
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatStatus(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

const activity = [
  { icon: LogIn, bg: 'bg-emerald-50', color: 'text-emerald-600', text: 'Signed in to the platform console', time: '10m ago' },
  { icon: Settings2, bg: 'bg-blue-50', color: 'text-blue-600', text: 'Updated tenant subscription plan for Acme Corp', time: '1h ago' },
  { icon: UserPlus, bg: 'bg-violet-50', color: 'text-violet-600', text: 'Invited a new platform user', time: '3h ago' },
  { icon: ShieldAlert, bg: 'bg-amber-50', color: 'text-amber-600', text: 'Updated role permissions for Support Agent', time: '5h ago' },
  { icon: FileClock, bg: 'bg-slate-100', color: 'text-slate-500', text: 'Viewed platform audit logs', time: '1d ago' },
];

/* ─── components ─── */
function Card({ className = '', children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={['bg-white rounded-xl border border-slate-200/80 shadow-sm', className].join(' ')}>
      {children}
    </div>
  );
}

function SectionHeader({
  title,
  sub,
  action,
  onAction,
}: {
  title: string;
  sub?: string;
  action?: string;
  onAction?: () => void;
}) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h3 className="text-[13px] font-bold text-slate-900 leading-none">{title}</h3>
        {sub && <p className="text-[11px] text-slate-500 mt-1">{sub}</p>}
      </div>
      {action && (
        <button
          onClick={onAction}
          className="flex items-center gap-0.5 text-[12px] text-blue-600 hover:text-blue-700 font-semibold transition-colors shrink-0 ml-4"
        >
          {action} <ArrowUpRight size={12} />
        </button>
      )}
    </div>
  );
}

function Switch({
  checked,
  onChange,
  disabled,
}: {
  checked: boolean;
  onChange: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={onChange}
      className={[
        'relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors duration-200',
        'focus:outline-none focus:ring-2 focus:ring-blue-500/30',
        checked ? 'bg-blue-600' : 'bg-slate-300',
        disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
      ].join(' ')}
    >
      <span
        className={[
          'inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm transition-transform duration-200',
          checked ? 'translate-x-[18px]' : 'translate-x-[3px]',
        ].join(' ')}
      />
    </button>
  );
}

export function AdminProfilePage() {
  const navigate = useNavigate();
  const { user, realm, refreshCurrentSession } = useAuthSession();

  const displayName = user?.display_name || 'Admin User';
  const roleLabel = realm === 'platform' ? 'Platform Administrator' : 'Team Member';
  const initials = displayName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('') || 'AU';
  const mfaEnabled = user?.mfa_enabled ?? false;
  const mfaSetupPath = realm === 'platform' ? '/platform-admin/security/mfa/setup' : '/settings/security/mfa/setup';
  const auditPath = realm === 'platform' ? '/platform-admin/audit' : '/reports';

  /* ── Password policy (fetched from the identity service, same as reset-password) ── */
  const [passwordPolicy, setPasswordPolicy] = useState<PasswordPolicyResponse>(defaultPasswordPolicy);

  useEffect(() => {
    if (!realm) return;
    identityApi.passwordPolicy(realm).then(setPasswordPolicy).catch(() => undefined);
  }, [realm]);

  /* ── Change password ── */
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordState, setPasswordState] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [passwordError, setPasswordError] = useState('');

  const resetPasswordForm = () => {
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setPasswordState('idle');
    setPasswordError('');
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!realm || passwordState === 'loading') return;
    setPasswordError('');

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match.');
      return;
    }
    if (newPassword.length < passwordPolicy.min_length) {
      setPasswordError(`Password must be at least ${passwordPolicy.min_length} characters long.`);
      return;
    }
    if (newPassword.length > passwordPolicy.max_length) {
      setPasswordError(`Password must be no more than ${passwordPolicy.max_length} characters long.`);
      return;
    }
    if (passwordPolicy.require_uppercase && !/[A-Z]/.test(newPassword)) {
      setPasswordError('Password must contain an uppercase letter.');
      return;
    }
    if (passwordPolicy.require_lowercase && !/[a-z]/.test(newPassword)) {
      setPasswordError('Password must contain a lowercase letter.');
      return;
    }
    if (passwordPolicy.require_number && !/\d/.test(newPassword)) {
      setPasswordError('Password must contain a number.');
      return;
    }
    if (passwordPolicy.require_special && !/[^A-Za-z0-9]/.test(newPassword)) {
      setPasswordError('Password must contain a special character.');
      return;
    }

    setPasswordState('loading');
    try {
      await identityApi.changePassword(realm, currentPassword, newPassword, confirmPassword);
      setPasswordState('success');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => {
        setShowPasswordForm(false);
        setPasswordState('idle');
      }, 2000);
    } catch (err) {
      const safeError = toSafeError(err);
      setPasswordState('error');
      setPasswordError(
        err instanceof ApiError && err.fieldErrors.current_password
          ? err.fieldErrors.current_password
          : safeError.message
      );
    }
  };

  /* ── Two-factor authentication ── */
  const [showDisableMfa, setShowDisableMfa] = useState(false);
  const [mfaPassword, setMfaPassword] = useState('');
  const [mfaDisableState, setMfaDisableState] = useState<'idle' | 'loading' | 'error'>('idle');
  const [mfaDisableError, setMfaDisableError] = useState('');
  const [mfaSuccessMessage, setMfaSuccessMessage] = useState('');

  const profilePath = realm === 'platform' ? '/platform-admin/profile' : '/settings/profile';

  const handleToggleMfa = () => {
    if (!realm) return;
    if (mfaEnabled) {
      setMfaDisableError('');
      setShowDisableMfa((v) => !v);
    } else {
      navigate(mfaSetupPath, { state: { returnTo: profilePath } });
    }
  };

  const handleDisableMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!realm || mfaDisableState === 'loading') return;
    setMfaDisableState('loading');
    setMfaDisableError('');
    try {
      await identityApi.disableMfa(realm, mfaPassword);
      await refreshCurrentSession();
      setMfaPassword('');
      setShowDisableMfa(false);
      setMfaDisableState('idle');
      setMfaSuccessMessage('Two-factor authentication has been disabled.');
      setTimeout(() => setMfaSuccessMessage(''), 4000);
    } catch (err) {
      const safeError = toSafeError(err);
      setMfaDisableState('error');
      setMfaDisableError(safeError.message);
    }
  };

  return (
    <AppShell pageTitle="Admin Profile">
      {/* ── Page header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5">
        <div>
          <p className="text-[17px] font-bold text-slate-900 leading-tight">Admin Profile</p>
          <p className="text-sm text-slate-500 mt-0.5">Manage your account and security</p>
        </div>
        <Button size="md" variant="secondary" className="shrink-0">
          <Pencil size={14} />
          Edit Profile
        </Button>
      </div>

      {/* ── Profile summary ── */}
      <Card className="p-5 sm:p-6 mb-4">
        <div className="flex flex-col lg:flex-row lg:items-center gap-6">
          <div className="flex items-center gap-4 flex-1 min-w-0">
            <div className="relative shrink-0">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white text-lg font-bold leading-none">{initials}</span>
              </div>
              <span className="absolute bottom-0.5 right-0.5 w-3 h-3 bg-emerald-500 rounded-full border-2 border-white" />
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-base font-bold text-slate-900 leading-none">{displayName}</h2>
                <span className="text-[11px] font-semibold text-blue-700 bg-blue-50 border border-blue-100 rounded-full px-2 py-0.5">
                  {roleLabel}
                </span>
              </div>
              <div className="mt-2.5 space-y-1.5">
                <div className="flex items-center gap-2 text-[12px] text-slate-600">
                  <Mail size={13} className="text-slate-400 shrink-0" />
                  <span className="truncate">{user?.email || 'admin@gnxthire.io'}</span>
                </div>
                <div className="flex items-center gap-2 text-[12px] text-slate-600">
                  <Clock size={13} className="text-slate-400 shrink-0" />
                  <span>Last login: {formatDateTime(user?.last_login_at ?? null)}</span>
                </div>
                <div className="flex items-center gap-2 text-[12px] text-slate-600">
                  <MapPin size={13} className="text-slate-400 shrink-0" />
                  <span>IP address: {user?.last_login_ip ?? 'Not available'}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-1 gap-4 lg:gap-3 lg:w-[220px] lg:border-l lg:border-slate-100 lg:pl-6 shrink-0">
            <div className="flex items-start gap-2.5">
              <BadgeCheck size={15} className="text-blue-500 mt-0.5 shrink-0" />
              <div className="min-w-0">
                <p className="text-[10px] text-slate-500 leading-none mb-1">Role</p>
                <p className="text-[12px] font-semibold text-slate-800 truncate">{roleLabel}</p>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <Building2 size={15} className="text-indigo-500 mt-0.5 shrink-0" />
              <div className="min-w-0">
                <p className="text-[10px] text-slate-500 leading-none mb-1">Department</p>
                <p className="text-[12px] font-semibold text-slate-800 truncate">Platform Operations</p>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <CalendarDays size={15} className="text-cyan-500 mt-0.5 shrink-0" />
              <div className="min-w-0">
                <p className="text-[10px] text-slate-500 leading-none mb-1">Member Since</p>
                <p className="text-[12px] font-semibold text-slate-800 truncate">
                  {user?.created_at ? formatDate(user.created_at) : '—'}
                </p>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <CheckCircle2 size={15} className={['mt-0.5 shrink-0', user ? statusStyles[user.status] ?? 'text-slate-400' : 'text-slate-400'].join(' ')} />
              <div className="min-w-0">
                <p className="text-[10px] text-slate-500 leading-none mb-1">Status</p>
                <p
                  className={[
                    'text-[12px] font-semibold truncate',
                    user ? statusStyles[user.status] ?? 'text-slate-800' : 'text-slate-800',
                  ].join(' ')}
                >
                  {user ? formatStatus(user.status) : '—'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* ── Account Security + Recent Activity ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="p-5">
          <SectionHeader title="Account Security" sub="Password and two-factor authentication" />

          {mfaSuccessMessage && (
            <Alert variant="success" className="mb-4" onDismiss={() => setMfaSuccessMessage('')}>
              {mfaSuccessMessage}
            </Alert>
          )}

          <div className="divide-y divide-slate-100">
            {/* Password */}
            <div className="py-3 first:pt-0">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center shrink-0">
                  <KeyRound size={14} className="text-slate-500" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[12px] font-semibold text-slate-800 leading-none">Password</p>
                  <p className="text-[11px] text-slate-500 mt-1">Change your account password</p>
                </div>
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    setShowPasswordForm((v) => !v);
                    resetPasswordForm();
                  }}
                >
                  {showPasswordForm ? 'Cancel' : 'Change'}
                </Button>
              </div>

              {showPasswordForm && (
                <form onSubmit={handleChangePassword} className="mt-4 sm:pl-11 space-y-3">
                  {passwordState === 'error' && passwordError && (
                    <Alert variant="error" onDismiss={() => setPasswordError('')}>
                      {passwordError}
                    </Alert>
                  )}
                  {passwordState === 'success' && (
                    <Alert variant="success">Password updated successfully.</Alert>
                  )}
                  <Input
                    label="Current password"
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                  />
                  <Input
                    label="New password"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    required
                    autoComplete="new-password"
                  />
                  {newPassword && (
                    <PasswordStrength password={newPassword} confirmPassword={confirmPassword} policy={passwordPolicy} />
                  )}
                  <Input
                    label="Confirm new password"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    autoComplete="new-password"
                    error={confirmPassword && newPassword !== confirmPassword ? 'Passwords do not match' : undefined}
                  />
                  <div className="flex gap-2 pt-1">
                    <Button type="submit" size="sm" loading={passwordState === 'loading'}>
                      Update password
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setShowPasswordForm(false);
                        resetPasswordForm();
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </form>
              )}
            </div>

            {/* Two-Factor Auth */}
            <div className="py-3 last:pb-0">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center shrink-0">
                  <ShieldCheck size={14} className="text-slate-500" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-[12px] font-semibold text-slate-800 leading-none">Two-Factor Auth</p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    {mfaEnabled ? 'Enabled via authenticator app' : 'Add an extra layer of security to sign-in'}
                  </p>
                </div>
                <Switch checked={mfaEnabled} onChange={handleToggleMfa} />
              </div>

              {showDisableMfa && (
                <form onSubmit={handleDisableMfa} className="mt-4 sm:pl-11 space-y-3">
                  <Alert variant="warning">Enter your password to turn off two-factor authentication.</Alert>
                  {mfaDisableState === 'error' && mfaDisableError && (
                    <Alert variant="error" onDismiss={() => setMfaDisableError('')}>
                      {mfaDisableError}
                    </Alert>
                  )}
                  <Input
                    label="Current password"
                    type="password"
                    value={mfaPassword}
                    onChange={(e) => setMfaPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                  />
                  <div className="flex gap-2 pt-1">
                    <Button type="submit" size="sm" variant="danger" loading={mfaDisableState === 'loading'}>
                      Disable MFA
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setShowDisableMfa(false);
                        setMfaPassword('');
                        setMfaDisableError('');
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </Card>

        <Card className="lg:col-span-2 p-5">
          <SectionHeader title="Recent Activity" action="View all" onAction={() => navigate(auditPath)} />
          <div className="divide-y divide-slate-100">
            {activity.map((item, i) => (
              <div key={i} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
                <div
                  className={[
                    'w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5',
                    item.bg,
                  ].join(' ')}
                >
                  <item.icon size={13} className={item.color} />
                </div>
                <p className="flex-1 text-[12px] text-slate-700 leading-relaxed">{item.text}</p>
                <div className="flex items-center gap-1 shrink-0 mt-0.5 ml-2">
                  <Clock size={10} className="text-slate-300" />
                  <span className="text-[11px] text-slate-400 tabular-nums">{item.time}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
