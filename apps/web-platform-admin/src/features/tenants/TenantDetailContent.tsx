import { useEffect, useState } from 'react';
import { Copy, Check, ExternalLink, Crown, Globe2, CalendarDays, ShieldAlert, Gauge, Users2, FileClock, Headset, Puzzle, Loader2, ChevronDown, ReceiptText } from 'lucide-react';
import { platformControlApi, toSafeUserMessage } from '../../api';
import { useAuth } from '../../lib/auth/AuthProvider';
import {
  transitionEndpoint,
  transitionLabel,
  TABS,
  TENANT_TRANSITIONS,
  TRANSITION_REQUIRES_REASON,
  initials,
  statusTone,
  type SupportTicket,
  type TabKey,
  type TenantLifecycleEvent,
  type TenantRecord,
} from './tenantTypes';
import type { TenantDetailData } from './useTenantDetail';

export type { TabKey };

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        void navigator.clipboard.writeText(text).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1800);
        });
      }}
      className="text-slate-500 hover:text-slate-300 transition-colors shrink-0"
      aria-label="Copy"
    >
      {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
    </button>
  );
}

function InfoRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-white/[0.06] last:border-0 gap-3">
      <span className="text-xs text-slate-500 shrink-0">{label}</span>
      <div className="flex items-center gap-2 text-sm text-slate-200 min-w-0">{children}</div>
    </div>
  );
}

export function TenantTabs({ tab, onChange }: { tab: TabKey; onChange: (tab: TabKey) => void }) {
  return (
    <div className="flex items-center gap-4 px-5 border-b border-white/10 overflow-x-auto">
      {TABS.map((t) => (
        <button
          key={t.key}
          onClick={() => onChange(t.key)}
          className={[
            'text-[13px] font-medium pb-2.5 pt-1 border-b-2 whitespace-nowrap transition-colors',
            tab === t.key ? 'text-blue-400 border-blue-500' : 'text-slate-500 border-transparent hover:text-slate-300',
          ].join(' ')}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function TenantTabPanel({ tab, data, tenantId, layout = 'popup' }: { tab: TabKey; data: TenantDetailData; tenantId: string; layout?: 'popup' | 'page' }) {
  if (tab === 'overview') return <OverviewTab data={data} layout={layout} />;
  if (tab === 'usage') return <UsageTab data={data} layout={layout} />;
  if (tab === 'integrations') return <IntegrationsTab />;
  if (tab === 'support') return <SupportTab tenantId={tenantId} layout={layout} />;
  return <ActivityTab tenantId={tenantId} />;
}

function OverviewTab({ data, layout }: { data: TenantDetailData; layout: 'popup' | 'page' }) {
  const primaryDomain = data.domains.find((d) => d.is_primary) ?? data.domains[0] ?? null;

  const info = (
    <div>
      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-3">Tenant Information</h3>
      <div>
        <InfoRow label="Tenant ID">
          <span className="font-mono text-xs truncate">{data.tenant.id}</span>
          <CopyButton text={data.tenant.id} />
        </InfoRow>
        <InfoRow label="Domain">
          {primaryDomain ? (
            <>
              <span className="truncate">{primaryDomain.domain}</span>
              <a href={`https://${primaryDomain.domain}`} target="_blank" rel="noreferrer" className="text-slate-500 hover:text-slate-300 shrink-0">
                <ExternalLink size={12} />
              </a>
            </>
          ) : (
            <span className="text-slate-500">No domain configured</span>
          )}
        </InfoRow>
        <InfoRow label="Plan">
          <Crown size={13} className="text-violet-400 shrink-0" />
          <span className="truncate">{data.plan?.name ?? 'No plan assigned'}</span>
        </InfoRow>
        <InfoRow label="Region">
          <Globe2 size={13} className="text-blue-400 shrink-0" />
          <span className="truncate">
            {data.tenant.region}
            {data.tenant.data_residency_zone ? ` · ${data.tenant.data_residency_zone}` : ''}
          </span>
        </InfoRow>
        <InfoRow label="Status">
          <span className={['text-[11px] font-semibold px-2 py-0.5 rounded-full border capitalize', statusTone[data.tenant.status] ?? statusTone.deleted].join(' ')}>
            {data.tenant.status.replace(/_/g, ' ')}
          </span>
        </InfoRow>
        <InfoRow label="Created On">
          <CalendarDays size={13} className="text-cyan-400 shrink-0" />
          {formatDate(data.tenant.created_at)}
        </InfoRow>
        <InfoRow label="Tenant Admin">
          <div className="w-5 h-5 rounded-full bg-slate-700 flex items-center justify-center text-[9px] font-bold text-slate-300 shrink-0">
            {initials(data.tenant.primary_admin_email.split('@')[0].replace(/[._]/g, ' '))}
          </div>
          <span className="truncate">{data.tenant.primary_admin_email}</span>
        </InfoRow>
      </div>
    </div>
  );

  const health = (
    <div>
      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-3">Health</h3>
      {data.health ? (
        <div className="grid grid-cols-3 gap-2">
          <HealthStat label="Failed jobs" value={data.health.failed_provisioning_jobs.total} bad={data.health.failed_provisioning_jobs.total > 0} />
          <HealthStat label="Open tickets" value={data.health.open_support_tickets.total} bad={data.health.open_support_tickets.total > 0} />
          <HealthStat label="Support sessions" value={data.health.active_support_sessions.total} bad={false} />
        </div>
      ) : (
        <p className="text-xs text-slate-500">Health data unavailable.</p>
      )}
    </div>
  );

  const billing = (
    <div>
      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-3 flex items-center gap-1.5">
        <ReceiptText size={13} />
        Billing Subscription
      </h3>
      {data.subscription?.subscription ? (
        <div>
          <InfoRow label="Status">
            <span className="capitalize">{data.subscription.subscription.status.replace(/_/g, ' ')}</span>
          </InfoRow>
          <InfoRow label="Billing interval">
            <span className="capitalize">{data.subscription.subscription.billing_interval}</span>
          </InfoRow>
          <InfoRow label="Current period">
            {formatDate(data.subscription.subscription.current_period_start)} – {formatDate(data.subscription.subscription.current_period_end)}
          </InfoRow>
          {data.subscription.subscription.trial_ends_at && (
            <InfoRow label="Trial ends">{formatDate(data.subscription.subscription.trial_ends_at)}</InfoRow>
          )}
          <InfoRow label="Active add-ons">{data.subscription.active_addons.length}</InfoRow>
        </div>
      ) : (
        <p className="text-xs text-slate-500">No active billing subscription found for this tenant.</p>
      )}
    </div>
  );

  if (layout === 'page') {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {info}
        {billing}
        {health}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {info}
      {billing}
      {health}
    </div>
  );
}

function HealthStat({ label, value, bad }: { label: string; value: number; bad: boolean }) {
  return (
    <div className="bg-white/[0.03] border border-white/10 rounded-lg p-3">
      <p className={['text-lg font-bold leading-none', bad ? 'text-amber-400' : 'text-emerald-400'].join(' ')}>{value}</p>
      <p className="text-[10px] text-slate-500 mt-1 leading-tight">{label}</p>
    </div>
  );
}

function UsageTab({ data, layout }: { data: TenantDetailData; layout: 'popup' | 'page' }) {
  const hasPlan = Boolean(data.tenant.plan_id);
  const entitlements = data.entitlements;
  if (!hasPlan) {
    return <p className="text-sm text-slate-500">No plan assigned — quota limits are not available.</p>;
  }
  if (!entitlements || entitlements.quota_limits.length === 0) {
    return <p className="text-sm text-slate-500">No quota limits configured for this plan.</p>;
  }
  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <Gauge size={14} className="text-blue-400" />
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Plan Quotas & Limits</h3>
      </div>
      <div className={['grid grid-cols-1 sm:grid-cols-2 gap-3', layout === 'page' ? 'lg:grid-cols-3 xl:grid-cols-4' : ''].join(' ')}>
        {entitlements.quota_limits.map((quota) => (
          <div key={quota.quota_key} className="bg-white/[0.03] border border-white/10 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-slate-200 capitalize">{quota.quota_key.replace(/_/g, ' ')}</span>
              <span className="text-[11px] text-slate-500">{quota.unit}</span>
            </div>
            <p className="text-[11px] text-slate-500">
              Soft limit: <span className="text-slate-300">{quota.soft_limit ?? '—'}</span> · Hard limit: <span className="text-slate-300">{quota.hard_limit ?? 'Unlimited'}</span>
            </p>
          </div>
        ))}
      </div>
      <p className="text-[11px] text-slate-600 mt-3">Live consumption metering is not yet available — these are the plan's configured limits.</p>
    </div>
  );
}

function IntegrationsTab() {
  return (
    <div className="flex flex-col items-center text-center py-10">
      <div className="w-11 h-11 rounded-xl bg-white/[0.04] border border-white/10 flex items-center justify-center mb-3">
        <Puzzle size={19} className="text-slate-500" />
      </div>
      <p className="text-sm font-semibold text-slate-300">No integration data available</p>
      <p className="text-xs text-slate-500 mt-1 max-w-[240px]">Connector status for this tenant isn't tracked by the platform-admin service yet.</p>
    </div>
  );
}

function SupportTab({ tenantId, layout }: { tenantId: string; layout: 'popup' | 'page' }) {
  const { withFreshToken } = useAuth();
  const [tickets, setTickets] = useState<SupportTicket[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    withFreshToken((token) => platformControlApi.list<SupportTicket>(token, '/v1/platform-admin/support-tickets', { tenant_id: tenantId }))
      .then((page) => {
        if (active) setTickets(page.data);
      })
      .catch((err) => {
        if (active) setError(toSafeUserMessage(err));
      });
    return () => {
      active = false;
    };
  }, [tenantId, withFreshToken]);

  if (error) return <p className="text-sm text-red-400">{error}</p>;
  if (!tickets) return <Loader2 size={16} className="text-slate-500 animate-spin" />;
  if (tickets.length === 0) {
    return (
      <div className="flex flex-col items-center text-center py-10">
        <Headset size={19} className="text-slate-500 mb-3" />
        <p className="text-sm font-semibold text-slate-300">No support tickets</p>
      </div>
    );
  }
  return (
    <div className={['grid grid-cols-1 sm:grid-cols-2 gap-2.5', layout === 'page' ? 'lg:grid-cols-3 xl:grid-cols-4' : ''].join(' ')}>
      {tickets.map((ticket) => (
        <div key={ticket.id} className="bg-white/[0.03] border border-white/10 rounded-lg p-3">
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="text-xs font-semibold text-slate-200 truncate">{ticket.subject}</span>
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-700 text-slate-300 shrink-0">{ticket.priority}</span>
          </div>
          <p className="text-[11px] text-slate-500 capitalize">
            {ticket.status.replace(/_/g, ' ')} · {formatDate(ticket.created_at)}
          </p>
        </div>
      ))}
    </div>
  );
}

function ActivityTab({ tenantId }: { tenantId: string }) {
  const { withFreshToken } = useAuth();
  const [events, setEvents] = useState<TenantLifecycleEvent[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    withFreshToken((token) => platformControlApi.list<TenantLifecycleEvent>(token, `/v1/platform-admin/tenants/${tenantId}/lifecycle-events`))
      .then((page) => {
        if (active) setEvents(page.data);
      })
      .catch((err) => {
        if (active) setError(toSafeUserMessage(err));
      });
    return () => {
      active = false;
    };
  }, [tenantId, withFreshToken]);

  if (error) return <p className="text-sm text-red-400">{error}</p>;
  if (!events) return <Loader2 size={16} className="text-slate-500 animate-spin" />;
  if (events.length === 0) {
    return (
      <div className="flex flex-col items-center text-center py-10">
        <FileClock size={19} className="text-slate-500 mb-3" />
        <p className="text-sm font-semibold text-slate-300">No activity recorded yet</p>
      </div>
    );
  }
  return (
    <div className="space-y-0 divide-y divide-white/[0.06]">
      {events.map((event) => (
        <div key={event.id} className="py-2.5 first:pt-0">
          <p className="text-xs text-slate-300">
            {event.from_status ? (
              <>
                <span className="capitalize">{event.from_status.replace(/_/g, ' ')}</span> → <span className="capitalize">{event.to_status?.replace(/_/g, ' ')}</span>
              </>
            ) : (
              <span className="capitalize">{event.event_key.replace(/\./g, ' ').replace(/_/g, ' ')}</span>
            )}
          </p>
          {event.reason && <p className="text-[11px] text-slate-500 mt-0.5">{event.reason}</p>}
          <p className="text-[10px] text-slate-600 mt-0.5">{formatDate(event.occurred_at)}</p>
        </div>
      ))}
    </div>
  );
}

export function TenantActions({ tenant, onChanged }: { tenant: TenantRecord; onChanged: (tenant: TenantRecord) => void }) {
  const { withFreshToken } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [pendingTarget, setPendingTarget] = useState<string | null>(null);
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [supportPromptOpen, setSupportPromptOpen] = useState(false);
  const [supportReason, setSupportReason] = useState('');
  const [supportBusy, setSupportBusy] = useState(false);
  const [supportMessage, setSupportMessage] = useState<string | null>(null);

  const targets = TENANT_TRANSITIONS[tenant.status] ?? [];

  async function runTransition(target: string) {
    setBusy(true);
    setError(null);
    try {
      const endpoint = transitionEndpoint(tenant.status, target);
      const needsReason = TRANSITION_REQUIRES_REASON.has(target);
      const result = await withFreshToken((token) =>
        platformControlApi.post<TenantRecord>(token, `/v1/platform-admin/tenants/${tenant.id}/${endpoint}`, needsReason ? { reason } : undefined),
      );
      onChanged(result.data);
      setPendingTarget(null);
      setReason('');
      setMenuOpen(false);
    } catch (err) {
      setError(toSafeUserMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function startSupportSession() {
    setSupportBusy(true);
    setError(null);
    try {
      const expiresAt = new Date(Date.now() + 60 * 60 * 1000).toISOString();
      await withFreshToken((token) =>
        platformControlApi.post(token, '/v1/platform-admin/support-sessions', { tenant_id: tenant.id, reason: supportReason, expires_at: expiresAt }),
      );
      setSupportMessage('Support session started — access is audited and expires in 1 hour.');
      setSupportPromptOpen(false);
      setSupportReason('');
    } catch (err) {
      setError(toSafeUserMessage(err));
    } finally {
      setSupportBusy(false);
    }
  }

  return (
    <div>
      {error && <p className="text-xs text-red-400 mb-2">{error}</p>}
      {supportMessage && <p className="text-xs text-emerald-400 mb-2">{supportMessage}</p>}

      {!pendingTarget && !supportPromptOpen && (
        <div className="flex gap-2">
          <button
            onClick={() => setSupportPromptOpen(true)}
            className="flex-1 flex items-center justify-center gap-2 h-9 rounded-lg bg-white/[0.06] hover:bg-white/10 border border-white/10 text-[13px] font-medium text-slate-200 transition-colors"
          >
            <Users2 size={14} />
            Impersonate User
          </button>
          <div className="relative">
            <button
              onClick={() => setMenuOpen((v) => !v)}
              disabled={targets.length === 0}
              className="flex items-center gap-1.5 h-9 px-3 rounded-lg bg-white/[0.06] hover:bg-white/10 border border-white/10 text-[13px] font-medium text-slate-200 transition-colors disabled:opacity-40"
            >
              More Actions
              <ChevronDown size={13} className={menuOpen ? 'rotate-180 transition-transform' : 'transition-transform'} />
            </button>
            {menuOpen && (
              <div className="absolute right-0 bottom-full mb-1.5 w-44 bg-[#1a2333] border border-white/10 rounded-lg shadow-xl py-1 z-10">
                {targets.map((target) => (
                  <button key={target} onClick={() => setPendingTarget(target)} className="w-full text-left px-3 py-2 text-[13px] text-slate-200 hover:bg-white/[0.06] transition-colors">
                    {transitionLabel(tenant.status, target)}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {pendingTarget && (
        <div className="bg-white/[0.03] border border-white/10 rounded-lg p-3.5">
          <p className="text-[13px] font-semibold text-slate-200 mb-2">{transitionLabel(tenant.status, pendingTarget)} this tenant?</p>
          {TRANSITION_REQUIRES_REASON.has(pendingTarget) && (
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Reason (required)"
              rows={2}
              className="w-full text-xs bg-white/[0.04] border border-white/10 rounded-md p-2 text-slate-200 placeholder:text-slate-600 mb-2 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
            />
          )}
          <div className="flex gap-2">
            <button
              onClick={() => void runTransition(pendingTarget)}
              disabled={busy || (TRANSITION_REQUIRES_REASON.has(pendingTarget) && !reason.trim())}
              className="h-8 px-3 rounded-md bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-xs font-semibold transition-colors"
            >
              {busy ? 'Working…' : 'Confirm'}
            </button>
            <button
              onClick={() => {
                setPendingTarget(null);
                setReason('');
              }}
              disabled={busy}
              className="h-8 px-3 rounded-md bg-white/[0.06] hover:bg-white/10 text-slate-300 text-xs font-medium transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {supportPromptOpen && (
        <div className="bg-white/[0.03] border border-white/10 rounded-lg p-3.5">
          <p className="text-[13px] font-semibold text-slate-200 mb-2">Start an audited support session</p>
          <textarea
            value={supportReason}
            onChange={(e) => setSupportReason(e.target.value)}
            placeholder="Reason for accessing this tenant (required)"
            rows={2}
            className="w-full text-xs bg-white/[0.04] border border-white/10 rounded-md p-2 text-slate-200 placeholder:text-slate-600 mb-2 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
          />
          <div className="flex gap-2">
            <button
              onClick={() => void startSupportSession()}
              disabled={supportBusy || !supportReason.trim()}
              className="h-8 px-3 rounded-md bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-xs font-semibold transition-colors"
            >
              {supportBusy ? 'Starting…' : 'Start session'}
            </button>
            <button
              onClick={() => {
                setSupportPromptOpen(false);
                setSupportReason('');
              }}
              disabled={supportBusy}
              className="h-8 px-3 rounded-md bg-white/[0.06] hover:bg-white/10 text-slate-300 text-xs font-medium transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="flex items-start gap-2.5 mt-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
        <ShieldAlert size={14} className="text-amber-400 shrink-0 mt-0.5" />
        <p className="text-[11px] text-amber-200/90 leading-relaxed">All admin actions are audited and tenant admins are notified.</p>
      </div>
    </div>
  );
}
