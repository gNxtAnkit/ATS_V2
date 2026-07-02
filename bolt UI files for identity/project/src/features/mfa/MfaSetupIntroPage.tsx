import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../../components/layout/AppShell';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { Shield, Smartphone, QrCode, KeyRound, CheckCircle2, ArrowRight } from 'lucide-react';
import { identityApi } from '../../lib/api/identityApi';
import { toSafeError } from '../../lib/api/apiErrors';
import { useAuthSession } from '../../lib/auth/authSession';

const steps = [
  {
    icon: Smartphone,
    title: 'Install an authenticator app',
    description: 'Download Google Authenticator, Microsoft Authenticator, Authy, or any TOTP-compatible app.',
  },
  {
    icon: QrCode,
    title: 'Scan the QR code',
    description: "We'll show you a QR code to add gNxtHire to your authenticator app.",
  },
  {
    icon: CheckCircle2,
    title: 'Enter the verification code',
    description: 'Confirm setup by entering the 6-digit code from your authenticator app.',
  },
  {
    icon: KeyRound,
    title: 'Save your recovery codes',
    description: "We'll give you backup codes to access your account if you lose your device.",
  },
];

export function MfaSetupIntroPage() {
  const navigate = useNavigate();
  const { realm } = useAuthSession();
  const [state, setState] = useState<'idle' | 'loading' | 'error'>('idle');
  const [error, setError] = useState('');
  const setupQrPath = realm === 'platform' ? '/platform-admin/security/mfa/setup/qr' : '/settings/security/mfa/setup/qr';
  const dashboardPath = realm === 'platform' ? '/platform-admin/dashboard' : '/dashboard';

  const handleStartSetup = async () => {
    if (!realm || state === 'loading') return;
    setState('loading');
    setError('');
    try {
      const setup = await identityApi.startMfaSetup(realm);
      navigate(setupQrPath, { state: setup });
    } catch (err) {
      setState('error');
      setError(toSafeError(err).message);
    }
  };

  return (
    <AppShell pageTitle="Set up multi-factor authentication">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-card p-8 mb-5">
          <div className="flex items-start gap-5">
            <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center shrink-0">
              <Shield size={24} className="text-blue-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 mb-1.5">Add extra security to your account</h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                Multi-factor authentication (MFA) adds a second layer of protection by requiring a
                verification code in addition to your password when you sign in.
              </p>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              { label: 'Protects against', value: 'Stolen passwords' },
              { label: 'Works with', value: 'Any TOTP app' },
              { label: 'Recovery via', value: 'Backup codes' },
            ].map((stat) => (
              <div key={stat.label} className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                <p className="text-xs text-slate-500 mb-1">{stat.label}</p>
                <p className="text-sm font-semibold text-slate-800">{stat.value}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-card p-8 mb-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-5">How it works</h3>
          <div className="space-y-5">
            {steps.map((step, i) => (
              <div key={step.title} className="flex items-start gap-4">
                <div className="flex items-center justify-center w-8 h-8 bg-blue-600 rounded-full text-white text-sm font-bold shrink-0">
                  {i + 1}
                </div>
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  <div className="w-9 h-9 bg-slate-50 rounded-xl flex items-center justify-center shrink-0 border border-slate-100">
                    <step.icon size={17} className="text-slate-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-800 mb-0.5">{step.title}</p>
                    <p className="text-xs text-slate-500 leading-relaxed">{step.description}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {state === 'error' && (
          <Alert variant="error" className="mb-5" onDismiss={() => setState('idle')}>
            {error}
          </Alert>
        )}

        <div className="flex flex-col sm:flex-row gap-3">
          <Button size="lg" loading={state === 'loading'} onClick={handleStartSetup} className="flex-1">
            Start setup
            <ArrowRight size={16} />
          </Button>
          <Button variant="secondary" size="lg" onClick={() => navigate(dashboardPath)}>
            Maybe later
          </Button>
        </div>
      </div>
    </AppShell>
  );
}
