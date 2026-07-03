import { useNavigate } from 'react-router-dom';
import { ShieldCheck, ShieldAlert, ArrowRight } from 'lucide-react';
import { AppShell } from '../components/layout/AppShell';
import { Button } from '../components/ui/Button';
import { useAuthSession } from '../lib/auth/authSession';

export function DashboardPage() {
  const navigate = useNavigate();
  const { user, realm } = useAuthSession();
  const securityPath = realm === 'platform' ? '/platform-admin/security/mfa/setup' : '/settings/security/mfa/setup';
  const pageTitle = realm === 'platform' ? 'Platform console' : 'Account dashboard';
  const displayName = user?.display_name || user?.email || 'there';
  const mfaEnabled = user?.mfa_enabled ?? false;

  return (
    <AppShell pageTitle={pageTitle}>
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-card p-8 mb-5">
          <p className="text-sm text-slate-500 mb-1">Welcome</p>
          <h2 className="text-xl font-bold text-slate-900">{displayName}</h2>
          <p className="text-sm text-slate-600 mt-2">
            Manage your identity and security settings for gNxtHire.
          </p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-card p-8">
          <div className="flex items-start gap-5">
            <div className={['w-12 h-12 rounded-xl flex items-center justify-center shrink-0', mfaEnabled ? 'bg-emerald-50' : 'bg-amber-50'].join(' ')}>
              {mfaEnabled ? (
                <ShieldCheck size={24} className="text-emerald-600" />
              ) : (
                <ShieldAlert size={24} className="text-amber-600" />
              )}
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold text-slate-900 mb-1.5">
                {mfaEnabled ? 'MFA is enabled' : 'MFA is not enabled'}
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                {mfaEnabled
                  ? `Authenticator app sign-in is active. Recovery codes remaining: ${user?.recovery_codes_remaining ?? 0}.`
                  : 'Add an authenticator app before this account is used for production work.'}
              </p>
              <Button size="lg" onClick={() => navigate(securityPath)} className="mt-5">
                Open security settings
                <ArrowRight size={16} />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
