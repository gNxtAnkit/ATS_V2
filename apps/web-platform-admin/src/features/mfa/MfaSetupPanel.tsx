import { FormEvent, useEffect, useState } from 'react';
import { Copy, Check, ShieldCheck, AlertTriangle } from 'lucide-react';
import { Card, CardBody, CardHeader } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { OtpInput } from '../../components/ui/OtpInput';
import { QrCode } from '../../components/ui/QrCode';
import { platformAdminApi, toSafeUserMessage } from '../../api';
import { useAuth } from '../../lib/auth/AuthProvider';

type Step = 'intro' | 'scan' | 'confirm' | 'recovery-codes';

export function MfaSetupPanel({ onClose }: { onClose: () => void }) {
  const { withFreshToken, refreshCurrentAdmin } = useAuth();
  const [step, setStep] = useState<Step>('intro');
  const [provisioningUri, setProvisioningUri] = useState('');
  const [manualSecret, setManualSecret] = useState('');
  const [code, setCode] = useState('');
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function startSetup() {
    setError(null);
    setBusy(true);
    try {
      const result = await withFreshToken((accessToken) => platformAdminApi.setupTotp(accessToken));
      setProvisioningUri(result.provisioning_uri);
      setManualSecret(result.manual_entry_secret);
      setStep('scan');
    } catch (err) {
      setError(toSafeUserMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleConfirm(event: FormEvent) {
    event.preventDefault();
    if (code.length !== 6) {
      setError('Enter the 6-digit code from your authenticator app.');
      return;
    }
    setError(null);
    setBusy(true);
    try {
      const result = await withFreshToken((accessToken) => platformAdminApi.confirmTotp(accessToken, code));
      setRecoveryCodes(result.recovery_codes);
      setStep('recovery-codes');
      await refreshCurrentAdmin();
    } catch (err) {
      setError(toSafeUserMessage(err, 'mfa'));
    } finally {
      setBusy(false);
    }
  }

  function copyRecoveryCodes() {
    void navigator.clipboard.writeText(recoveryCodes.join('\n'));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Card>
      <CardHeader icon={ShieldCheck} title="Set up authenticator app" subtitle="Add a second factor to your sign-in." />
      <CardBody>
        {error && (
          <div className="mb-4">
            <Alert variant="error">{error}</Alert>
          </div>
        )}

        {step === 'intro' && (
          <div className="space-y-4">
            <p className="text-sm text-slate-600 leading-relaxed">
              You'll need an authenticator app such as Google Authenticator, 1Password, or Authy. We'll show a QR
              code to scan, then ask you to confirm with a 6-digit code.
            </p>
            <div className="flex gap-2">
              <Button onClick={startSetup} loading={busy}>
                Get started
              </Button>
              <Button variant="secondary" onClick={onClose}>
                Cancel
              </Button>
            </div>
          </div>
        )}

        {step === 'scan' && (
          <div className="space-y-4">
            <div className="flex justify-center bg-slate-50 rounded-xl p-5 border border-slate-100">
              <QrCode value={provisioningUri} className="w-44 h-44" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Can't scan? Enter manually</p>
              <code className="block text-xs bg-slate-50 border border-slate-100 rounded-lg p-2.5 font-mono break-all text-slate-700">
                {manualSecret}
              </code>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => setStep('confirm')}>I've added the account</Button>
              <Button variant="secondary" onClick={onClose}>
                Cancel
              </Button>
            </div>
          </div>
        )}

        {step === 'confirm' && (
          <form onSubmit={handleConfirm} className="space-y-5">
            <p className="text-sm text-slate-600">Enter the 6-digit code shown in your authenticator app.</p>
            <OtpInput value={code} onChange={setCode} autoFocus />
            <div className="flex gap-2">
              <Button type="submit" loading={busy}>
                Confirm and enable
              </Button>
              <Button type="button" variant="secondary" onClick={() => setStep('scan')}>
                Back
              </Button>
            </div>
          </form>
        )}

        {step === 'recovery-codes' && (
          <div className="space-y-4">
            <Alert variant="warning" title="Save your recovery codes">
              Store these somewhere safe. Each code can be used once if you lose access to your authenticator app.
            </Alert>
            <div className="grid grid-cols-2 gap-2 bg-slate-50 border border-slate-100 rounded-xl p-4">
              {recoveryCodes.map((rc) => (
                <code key={rc} className="text-sm font-mono text-slate-800">
                  {rc}
                </code>
              ))}
            </div>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={copyRecoveryCodes}>
                {copied ? <Check size={15} /> : <Copy size={15} />}
                {copied ? 'Copied' : 'Copy codes'}
              </Button>
              <Button onClick={onClose}>Done</Button>
            </div>
          </div>
        )}
      </CardBody>
    </Card>
  );
}

export function MfaDangerZone() {
  const { admin, withFreshToken, refreshCurrentAdmin } = useAuth();
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [busy, setBusy] = useState<'disable' | 'regenerate' | null>(null);
  const [newCodes, setNewCodes] = useState<string[] | null>(null);

  async function handleRegenerate() {
    setError(null);
    setInfo(null);
    if (!password) {
      setError('Enter your password to continue.');
      return;
    }
    setBusy('regenerate');
    try {
      const result = await withFreshToken((accessToken) => platformAdminApi.regenerateRecoveryCodes(accessToken, password));
      setNewCodes(result.recovery_codes);
      setPassword('');
    } catch (err) {
      setError(toSafeUserMessage(err));
    } finally {
      setBusy(null);
    }
  }

  async function handleDisable() {
    setError(null);
    setInfo(null);
    if (!password) {
      setError('Enter your password to continue.');
      return;
    }
    setBusy('disable');
    try {
      await withFreshToken((accessToken) => platformAdminApi.disableMfa(accessToken, password));
      await refreshCurrentAdmin();
      setInfo('Two-step verification has been disabled for your account.');
      setPassword('');
    } catch (err) {
      setError(toSafeUserMessage(err));
    } finally {
      setBusy(null);
    }
  }

  if (!admin?.mfa_enabled) return null;

  return (
    <Card>
      <CardHeader icon={AlertTriangle} title="Manage two-step verification" subtitle="Regenerate recovery codes or disable MFA for this account." />
      <CardBody className="space-y-5">
        {error && <Alert variant="error">{error}</Alert>}
        {info && <Alert variant="success">{info}</Alert>}
        {newCodes && (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">New recovery codes</p>
            <div className="grid grid-cols-2 gap-2 bg-slate-50 border border-slate-100 rounded-xl p-4">
              {newCodes.map((rc) => (
                <code key={rc} className="text-sm font-mono text-slate-800">
                  {rc}
                </code>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-3">
          <input
            type="password"
            placeholder="Confirm your password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full h-10 px-3.5 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-500/20 focus:border-slate-500"
          />
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" size="sm" onClick={handleRegenerate} loading={busy === 'regenerate'} disabled={busy !== null}>
              Regenerate recovery codes
            </Button>
            <Button variant="danger" size="sm" onClick={handleDisable} loading={busy === 'disable'} disabled={busy !== null}>
              Disable MFA
            </Button>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
