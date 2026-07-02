import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AppShell } from '../../components/layout/AppShell';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { Download, Copy, Check, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useAuthSession } from '../../lib/auth/authSession';

export function MfaRecoveryCodesPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { realm, refreshCurrentSession } = useAuthSession();
  const locationState = location.state as { recoveryCodes?: string[]; returnTo?: string } | null;
  const recoveryCodes = locationState?.recoveryCodes ?? [];
  const returnTo = locationState?.returnTo;
  const [copied, setCopied] = useState(false);
  const [downloaded, setDownloaded] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(recoveryCodes.join('\n')).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  };

  const handleDownload = () => {
    const content = [
      'gNxtHire - MFA Recovery Codes',
      'Generated: ' + new Date().toLocaleDateString(),
      'Keep these codes safe. Each code can only be used once.',
      '',
      ...recoveryCodes.map((code, i) => `${i + 1}. ${code}`),
    ].join('\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'gnxthire-recovery-codes.txt';
    anchor.click();
    URL.revokeObjectURL(url);
    setDownloaded(true);
  };

  const actionsTaken = copied || downloaded;
  const setupPath = realm === 'platform' ? '/platform-admin/security/mfa/setup' : '/settings/security/mfa/setup';
  const dashboardPath = realm === 'platform' ? '/platform-admin/dashboard' : '/dashboard';

  if (recoveryCodes.length === 0) {
    return (
      <AppShell pageTitle="Save recovery codes">
        <div className="max-w-lg mx-auto">
          <Alert variant="warning" className="mb-5">
            Recovery codes are only shown immediately after MFA setup. Start MFA setup again if you need new codes.
          </Alert>
          <Button fullWidth size="lg" onClick={() => navigate(setupPath)}>
            Start setup again
          </Button>
        </div>
      </AppShell>
    );
  }

  if (confirmed) {
    return (
      <AppShell pageTitle="Set up multi-factor authentication">
        <div className="max-w-lg mx-auto">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-card p-8 text-center">
            <div className="w-16 h-16 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
              <CheckCircle2 size={30} className="text-emerald-600" />
            </div>
            <h2 className="text-xl font-bold text-slate-900 mb-2">MFA enabled successfully</h2>
            <p className="text-sm text-slate-500 mb-6 leading-relaxed">
              Your account is now protected with multi-factor authentication. You'll need your authenticator
              app every time you sign in.
            </p>
            <Button fullWidth size="lg" onClick={() => navigate(returnTo ?? dashboardPath, { replace: true })}>
              {returnTo ? 'Back to profile' : 'Go to dashboard'}
            </Button>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell pageTitle="Save recovery codes">
      <div className="max-w-xl mx-auto">
        <Alert variant="warning" className="mb-5">
          <strong>These codes will only be shown once.</strong> Save them somewhere secure before continuing.
          If you lose your authenticator device, these codes are the only way to recover access to your account.
        </Alert>

        <div className="bg-white rounded-2xl border border-slate-200 shadow-card p-6 mb-5">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-base font-bold text-slate-900">Your recovery codes</h2>
              <p className="text-xs text-slate-500 mt-0.5">{recoveryCodes.length} codes - each can be used once</p>
            </div>
            <div className="flex items-center gap-1.5 bg-amber-50 border border-amber-200 rounded-full px-3 py-1.5">
              <AlertTriangle size={12} className="text-amber-600" />
              <span className="text-xs font-semibold text-amber-700">Save now</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 mb-5">
            {recoveryCodes.map((code, i) => (
              <div
                key={code}
                className="flex items-center gap-2.5 bg-slate-50 rounded-xl px-3 py-2.5 border border-slate-100 font-mono text-sm text-slate-800"
              >
                <span className="text-xs text-slate-400 w-4 shrink-0 tabular-nums">{i + 1}</span>
                <span className="font-medium tracking-wider">{code}</span>
              </div>
            ))}
          </div>

          <div className="flex gap-2.5">
            <Button variant="secondary" size="md" onClick={handleDownload} className="flex-1">
              {downloaded ? (
                <>
                  <Check size={14} className="text-emerald-500" />
                  Downloaded
                </>
              ) : (
                <>
                  <Download size={14} />
                  Download codes
                </>
              )}
            </Button>
            <Button variant="secondary" size="md" onClick={handleCopy} className="flex-1">
              {copied ? (
                <>
                  <Check size={14} className="text-emerald-500" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy size={14} />
                  Copy codes
                </>
              )}
            </Button>
          </div>
        </div>

        {!actionsTaken && (
          <Alert variant="info" className="mb-5">
            Download or copy your codes above before confirming you've saved them.
          </Alert>
        )}

        <Button
          fullWidth
          size="lg"
          disabled={!actionsTaken}
          loading={refreshing}
          onClick={async () => {
            setRefreshing(true);
            try {
              await refreshCurrentSession();
            } finally {
              setRefreshing(false);
              setConfirmed(true);
            }
          }}
        >
          <CheckCircle2 size={16} />
          I have saved my recovery codes
        </Button>

        <p className="text-xs text-slate-400 text-center mt-3 leading-relaxed">
          You won't be able to view these codes again. Store them in a password manager or secure location.
        </p>
      </div>
    </AppShell>
  );
}
