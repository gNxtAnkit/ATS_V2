import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AppShell } from '../../components/layout/AppShell';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { OtpInput } from '../../components/ui/OtpInput';
import { QrCode } from '../../components/ui/QrCode';
import { Copy, Check, Eye, EyeOff } from 'lucide-react';
import { identityApi, type TotpSetupResponse } from '../../lib/api/identityApi';
import { toSafeError } from '../../lib/api/apiErrors';
import { useAuthSession } from '../../lib/auth/authSession';

function QrCodePanel({ provisioningUri }: { provisioningUri: string }) {
  return (
    <div className="w-56 h-56 bg-white border-2 border-slate-200 rounded-xl flex items-center justify-center mx-auto overflow-hidden">
      <QrCode value={provisioningUri} className="w-48 h-48" />
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-700 font-medium transition-colors shrink-0"
    >
      {copied ? <Check size={13} className="text-emerald-500" /> : <Copy size={13} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  );
}

export function MfaSetupQrPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { realm } = useAuthSession();
  const setup = location.state as TotpSetupResponse | null;
  const [code, setCode] = useState('');
  const [state, setState] = useState<'idle' | 'loading' | 'error'>('idle');
  const [error, setError] = useState('Incorrect code. Please check your app and try again.');
  const [showSecret, setShowSecret] = useState(false);
  const provisioningUri = setup?.provisioning_uri ?? '';
  const manualSecret = setup?.manual_entry_secret ?? '';
  const setupPath = realm === 'platform' ? '/platform-admin/security/mfa/setup' : '/settings/security/mfa/setup';
  const recoveryCodesPath = realm === 'platform' ? '/platform-admin/security/mfa/recovery-codes' : '/settings/security/mfa/recovery-codes';

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (code.length < 6 || !realm || state === 'loading') return;
    setState('loading');
    try {
      const response = await identityApi.confirmMfaSetup(realm, code);
      navigate(recoveryCodesPath, { state: { recoveryCodes: response.recovery_codes } });
    } catch (err) {
      const safeError = toSafeError(err, 'mfa');
      setState('error');
      setError(safeError.message);
      setCode('');
    }
  };

  if (!provisioningUri || !manualSecret) {
    return (
      <AppShell pageTitle="Set up multi-factor authentication">
        <div className="max-w-lg mx-auto">
          <Alert variant="warning" className="mb-5">
            MFA setup has not been started. Return to the previous step to generate a new setup code.
          </Alert>
          <Button fullWidth size="lg" onClick={() => navigate(setupPath)}>
            Start setup again
          </Button>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell pageTitle="Set up multi-factor authentication">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-card overflow-hidden mb-5">
          <div className="border-b border-slate-100 px-8 py-5">
            <div className="flex items-center gap-3">
              {[1, 2, 3, 4].map((s) => (
                <div key={s} className="flex items-center gap-2">
                  <div
                    className={[
                      'w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-colors',
                      s === 2 ? 'bg-blue-600 text-white' : s < 2 ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-400',
                    ].join(' ')}
                  >
                    {s}
                  </div>
                  {s < 4 && <div className={['h-px w-8', s < 2 ? 'bg-emerald-300' : 'bg-slate-200'].join(' ')} />}
                </div>
              ))}
              <span className="text-sm font-medium text-slate-600 ml-2">Scan QR code</span>
            </div>
          </div>

          <div className="p-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="flex flex-col items-center">
                <p className="text-sm font-semibold text-slate-700 mb-4 self-start">
                  Scan with your authenticator app
                </p>
                <QrCodePanel provisioningUri={provisioningUri} />
                <p className="text-xs text-slate-500 text-center mt-3 leading-relaxed max-w-[200px]">
                  Open your authenticator app and scan this QR code to add gNxtHire.
                </p>

                <div className="mt-5 w-full">
                  <div className="flex items-center justify-between mb-1.5">
                    <p className="text-xs font-medium text-slate-600">Can't scan? Enter manually:</p>
                    <button
                      onClick={() => setShowSecret((v) => !v)}
                      className="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1"
                    >
                      {showSecret ? <EyeOff size={12} /> : <Eye size={12} />}
                      {showSecret ? 'Hide' : 'Show'}
                    </button>
                  </div>
                  <div className="bg-slate-50 rounded-lg border border-slate-200 px-3 py-2.5 flex items-center gap-2">
                    <code className={['flex-1 text-xs font-mono text-slate-700 break-all tracking-wide', !showSecret ? 'blur-sm select-none' : ''].join(' ')}>
                      {manualSecret}
                    </code>
                    {showSecret && <CopyButton text={manualSecret} />}
                  </div>
                  {!showSecret && (
                    <p className="text-[10px] text-slate-400 mt-1">Secret is hidden for security. Click show to reveal.</p>
                  )}
                </div>
              </div>

              <div className="flex flex-col">
                <p className="text-sm font-semibold text-slate-700 mb-2">Confirm your authenticator</p>
                <p className="text-xs text-slate-500 mb-6 leading-relaxed">
                  Enter the 6-digit code shown in your authenticator app to confirm the connection.
                </p>

                {state === 'error' && (
                  <Alert variant="error" className="mb-5" onDismiss={() => setState('idle')}>
                    {error}
                  </Alert>
                )}

                <form onSubmit={handleConfirm} className="space-y-5">
                  <OtpInput value={code} onChange={setCode} length={6} error={state === 'error'} />

                  <div className="flex flex-col gap-3 pt-2">
                    <Button
                      type="submit"
                      fullWidth
                      size="lg"
                      loading={state === 'loading'}
                      disabled={code.length < 6}
                    >
                      Confirm and enable MFA
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      fullWidth
                      onClick={() => navigate(setupPath)}
                    >
                      Cancel setup
                    </Button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
