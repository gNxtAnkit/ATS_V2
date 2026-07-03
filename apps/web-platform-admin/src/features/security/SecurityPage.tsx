import { FormEvent, useState } from 'react';
import { ShieldCheck, KeyRound, ShieldOff } from 'lucide-react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, CardBody, CardHeader } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';
import { PasswordStrength } from '../../components/ui/PasswordStrength';
import { MfaSetupPanel, MfaDangerZone } from '../mfa/MfaSetupPanel';
import { platformAdminApi, toSafeUserMessage } from '../../api';
import { useAuth } from '../../lib/auth/AuthProvider';

function ChangePasswordCard() {
  const { withFreshToken } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSuccess(false);
    if (newPassword !== confirmPassword) {
      setError('New passwords do not match.');
      return;
    }
    setBusy(true);
    try {
      await withFreshToken((accessToken) => platformAdminApi.changePassword(accessToken, currentPassword, newPassword, confirmPassword));
      setSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setError(toSafeUserMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader icon={KeyRound} title="Change password" subtitle="Update the password used to sign in." />
      <CardBody>
        {error && (
          <div className="mb-4">
            <Alert variant="error">{error}</Alert>
          </div>
        )}
        {success && (
          <div className="mb-4">
            <Alert variant="success">Your password has been updated.</Alert>
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4 max-w-sm">
          <Input
            label="Current password"
            type="password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            disabled={busy}
          />
          <Input label="New password" type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} disabled={busy} />
          <Input
            label="Confirm new password"
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            disabled={busy}
          />
          <PasswordStrength password={newPassword} confirmPassword={confirmPassword} />
          <Button type="submit" loading={busy}>
            Update password
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}

export function SecurityPage() {
  const { admin } = useAuth();
  const [showSetup, setShowSetup] = useState(false);

  return (
    <AppShell title="Security" subtitle="Manage your sign-in credentials and two-step verification">
      <div className="space-y-6 max-w-2xl">
        <ChangePasswordCard />

        {admin?.mfa_enabled ? (
          <MfaDangerZone />
        ) : showSetup ? (
          <MfaSetupPanel onClose={() => setShowSetup(false)} />
        ) : (
          <Card>
            <CardHeader icon={ShieldCheck} title="Two-step verification" subtitle="Not currently enabled for your account." />
            <CardBody>
              <div className="flex items-start gap-3 mb-4">
                <ShieldOff size={18} className="text-slate-400 mt-0.5" />
                <p className="text-sm text-slate-600 leading-relaxed">
                  Add an authenticator app as a second factor to protect your account, even if your password is
                  compromised.
                </p>
              </div>
              <Button onClick={() => setShowSetup(true)}>Set up two-step verification</Button>
            </CardBody>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
