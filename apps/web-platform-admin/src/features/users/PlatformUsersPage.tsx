import { FormEvent, useCallback, useEffect, useState } from 'react';
import { UsersRound, Plus, X } from 'lucide-react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, CardBody, CardHeader } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Alert } from '../../components/ui/Alert';
import { StatusBadge } from '../../components/ui/Badge';
import { EmptyState } from '../../components/ui/EmptyState';
import { TableSkeleton } from '../../components/ui/Skeleton';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { platformUsersApi, toSafeUserMessage } from '../../api';
import { useAuth } from '../../lib/auth/AuthProvider';
import type { PlatformUser } from '../../types';

export function PlatformUsersPage() {
  const { withFreshToken } = useAuth();
  const [users, setUsers] = useState<PlatformUser[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInvite, setShowInvite] = useState(false);
  const [pendingAction, setPendingAction] = useState<{ user: PlatformUser; action: 'activate' | 'deactivate' | 'lock' | 'unlock' } | null>(null);
  const [actionBusy, setActionBusy] = useState(false);

  const loadUsers = useCallback(
    async (cursorParam: string | null, replace: boolean) => {
      setLoading(true);
      setError(null);
      try {
        const page = await withFreshToken((accessToken) => platformUsersApi.list(accessToken, cursorParam));
        setUsers((current) => (replace ? page.data : [...current, ...page.data]));
        setCursor(page.next_cursor);
        setHasMore(page.has_more);
      } catch (err) {
        setError(toSafeUserMessage(err));
      } finally {
        setLoading(false);
      }
    },
    [withFreshToken],
  );

  useEffect(() => {
    void loadUsers(null, true);
  }, [loadUsers]);

  async function handleAction() {
    if (!pendingAction) return;
    setActionBusy(true);
    try {
      const updated = await withFreshToken((accessToken) => platformUsersApi.action(accessToken, pendingAction.user.id, pendingAction.action));
      setUsers((current) => current.map((user) => (user.id === updated.id ? updated : user)));
      setPendingAction(null);
    } catch (err) {
      setError(toSafeUserMessage(err));
    } finally {
      setActionBusy(false);
    }
  }

  return (
    <AppShell title="Platform Users" subtitle="Manage administrator accounts for the Platform Admin Portal">
      {error && (
        <div className="mb-4">
          <Alert variant="error" onDismiss={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      <Card>
        <CardHeader
          icon={UsersRound}
          title="Administrators"
          subtitle="Everyone with access to this portal"
          action={
            <Button size="sm" onClick={() => setShowInvite(true)}>
              <Plus size={15} />
              Invite user
            </Button>
          }
        />
        <CardBody className="p-0">
          {loading && users.length === 0 ? (
            <TableSkeleton />
          ) : users.length === 0 ? (
            <EmptyState icon={UsersRound} title="No platform users yet" description="Invite an administrator to get started." />
          ) : (
            <div className="overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="text-left text-xs font-bold text-slate-500 uppercase tracking-wide px-5 py-2.5">Name</th>
                    <th className="text-left text-xs font-bold text-slate-500 uppercase tracking-wide px-5 py-2.5">Email</th>
                    <th className="text-left text-xs font-bold text-slate-500 uppercase tracking-wide px-5 py-2.5">Status</th>
                    <th className="text-left text-xs font-bold text-slate-500 uppercase tracking-wide px-5 py-2.5">MFA</th>
                    <th className="text-left text-xs font-bold text-slate-500 uppercase tracking-wide px-5 py-2.5">Last login</th>
                    <th className="text-right text-xs font-bold text-slate-500 uppercase tracking-wide px-5 py-2.5">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/60">
                      <td className="px-5 py-3 text-sm font-medium text-slate-800">{user.display_name}</td>
                      <td className="px-5 py-3 text-sm text-slate-600">{user.email}</td>
                      <td className="px-5 py-3">
                        <StatusBadge status={user.status} />
                      </td>
                      <td className="px-5 py-3 text-sm text-slate-600">{user.mfa_enabled ? 'Enabled' : user.mfa_required ? 'Required' : '—'}</td>
                      <td className="px-5 py-3 text-sm text-slate-500">{user.last_login_at ? new Date(user.last_login_at).toLocaleString() : 'Never'}</td>
                      <td className="px-5 py-3 text-right">
                        {user.status === 'active' ? (
                          <button
                            className="text-xs font-semibold text-red-600 hover:text-red-700"
                            onClick={() => setPendingAction({ user, action: 'deactivate' })}
                          >
                            Deactivate
                          </button>
                        ) : user.status === 'locked' ? (
                          <button
                            className="text-xs font-semibold text-slate-700 hover:text-slate-900"
                            onClick={() => setPendingAction({ user, action: 'unlock' })}
                          >
                            Unlock
                          </button>
                        ) : (
                          <button
                            className="text-xs font-semibold text-slate-700 hover:text-slate-900"
                            onClick={() => setPendingAction({ user, action: 'activate' })}
                          >
                            Activate
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
        {hasMore && (
          <div className="p-4 border-t border-slate-100 flex justify-center">
            <Button variant="secondary" size="sm" loading={loading} onClick={() => void loadUsers(cursor, false)}>
              Load more
            </Button>
          </div>
        )}
      </Card>

      {showInvite && <InviteUserModal onClose={() => setShowInvite(false)} onCreated={(user) => setUsers((current) => [user, ...current])} />}

      <ConfirmDialog
        open={Boolean(pendingAction)}
        title={pendingAction ? `${pendingAction.action.charAt(0).toUpperCase()}${pendingAction.action.slice(1)} user` : ''}
        description={pendingAction ? `Are you sure you want to ${pendingAction.action} ${pendingAction.user.display_name}?` : ''}
        confirmLabel={pendingAction ? pendingAction.action.charAt(0).toUpperCase() + pendingAction.action.slice(1) : 'Confirm'}
        destructive={pendingAction?.action === 'deactivate' || pendingAction?.action === 'lock'}
        busy={actionBusy}
        onConfirm={handleAction}
        onCancel={() => setPendingAction(null)}
      />
    </AppShell>
  );
}

function InviteUserModal({ onClose, onCreated }: { onClose: () => void; onCreated: (user: PlatformUser) => void }) {
  const { withFreshToken } = useAuth();
  const [email, setEmail] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!email.trim() || !displayName.trim()) {
      setError('Enter a name and email address.');
      return;
    }
    setBusy(true);
    try {
      const user = await withFreshToken((accessToken) => platformUsersApi.create(accessToken, email.trim(), displayName.trim()));
      onCreated(user);
      onClose();
    } catch (err) {
      setError(toSafeUserMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-900/40" onClick={busy ? undefined : onClose} />
      <div className="relative bg-white rounded-2xl shadow-float border border-slate-200 w-full max-w-sm">
        <div className="flex items-center justify-between p-5 border-b border-slate-100">
          <h3 className="text-[15px] font-bold text-slate-900">Invite platform user</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={16} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && <Alert variant="error">{error}</Alert>}
          <Input label="Full name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} disabled={busy} />
          <Input label="Email address" type="email" value={email} onChange={(event) => setEmail(event.target.value)} disabled={busy} />
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="secondary" size="sm" onClick={onClose} disabled={busy}>
              Cancel
            </Button>
            <Button type="submit" size="sm" loading={busy}>
              Send invite
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
