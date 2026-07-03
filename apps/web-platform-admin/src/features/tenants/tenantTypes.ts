// Mirrors platform.tenants and related tables — see db/models/platform.py and
// services/platform-admin/src/gnxthire_platform_admin/routes.py (`/tenants*`).
export interface TenantRecord {
  id: string;
  name: string;
  legal_entity_name: string | null;
  tenant_type: string;
  primary_admin_email: string;
  plan_id: string | null;
  status: string;
  isolation_tier: string;
  region: string;
  data_residency_zone: string | null;
  infra_pool_id: string | null;
  activated_at: string | null;
  suspended_at: string | null;
  churned_at: string | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  lock_version: number;
}

export interface TenantDomain {
  id: string;
  tenant_id: string;
  domain: string;
  is_primary: boolean;
  verification_status: string;
  verified_at: string | null;
}

export interface TenantHealth {
  tenant: TenantRecord;
  failed_provisioning_jobs: { total: number };
  open_support_tickets: { total: number };
  active_support_sessions: { total: number };
}

export interface PlanRecord {
  id: string;
  code: string;
  name: string;
  status: string;
}

export interface QuotaLimit {
  quota_key: string;
  unit: string;
  soft_limit: number | null;
  hard_limit: number | null;
  overage_unit_price: number;
  source: string;
}

export interface EffectiveEntitlements {
  tenant_id: string;
  plan_id: string | null;
  quota_limits: QuotaLimit[];
  quota_deltas: unknown[];
  quota_overrides: unknown[];
}

export interface TenantLifecycleEvent {
  id: string;
  tenant_id: string;
  event_key: string;
  from_status: string | null;
  to_status: string | null;
  actor_platform_user_id: string | null;
  occurred_at: string;
  reason: string | null;
}

export interface SupportTicket {
  id: string;
  tenant_id: string;
  requester_email: string;
  subject: string;
  description: string;
  priority: string;
  status: string;
  assigned_platform_user_id: string | null;
  created_at: string;
  closed_at: string | null;
}

export interface DashboardSummary {
  tenants_by_status: Array<{ status: string; count: number }>;
}

// See GET /tenants/{id}/subscription-summary — subscription is the tenant's current
// billing.subscriptions row (null if none), active_addons are billing.tenant_addon_subscriptions.
export interface SubscriptionSummary {
  tenant: TenantRecord;
  subscription: {
    id: string;
    plan_id: string;
    status: string;
    billing_interval: string;
    current_period_start: string;
    current_period_end: string;
    trial_ends_at: string | null;
  } | null;
  active_addons: Array<{ id: string; addon_id: string }>;
}

export const TENANT_STATUSES = ['provisioning', 'trial', 'active', 'suspended', 'churned', 'pending_deletion', 'deleted'] as const;
export const TENANT_TYPES = ['corporate', 'staffing_agency', 'rpo', 'executive_search'] as const;
export const REGIONS = ['US', 'EU', 'IN', 'ME', 'APAC', 'UK', 'CA', 'AU'] as const;

// Mirrors TENANT_TRANSITIONS in services/platform-admin/.../routes.py — the set of
// statuses a tenant can move to from its current status, and the endpoint/reason
// requirement for each. Keeping this in sync with the backend means the UI never
// offers a transition the API would reject.
export const TENANT_TRANSITIONS: Record<string, string[]> = {
  provisioning: ['trial', 'active', 'suspended', 'pending_deletion'],
  trial: ['active', 'suspended', 'churned', 'pending_deletion'],
  active: ['suspended', 'churned', 'pending_deletion'],
  suspended: ['active', 'churned', 'pending_deletion'],
  churned: ['pending_deletion'],
  pending_deletion: ['deleted', 'active'],
  deleted: ['active'],
};

// `active` is reachable via two distinct real endpoints depending on where the
// tenant is coming from: /reactivate from `suspended`, /activate from anywhere
// else (provisioning, trial, pending_deletion, deleted) — see routes.py:433-445.
export function transitionEndpoint(fromStatus: string, toStatus: string): string {
  if (toStatus === 'active') return fromStatus === 'suspended' ? 'reactivate' : 'activate';
  if (toStatus === 'suspended') return 'suspend';
  if (toStatus === 'churned') return 'churn';
  return 'soft-delete';
}

export function transitionLabel(fromStatus: string, toStatus: string): string {
  if (toStatus === 'active') return fromStatus === 'suspended' ? 'Reactivate' : 'Activate';
  if (toStatus === 'suspended') return 'Suspend';
  if (toStatus === 'churned') return 'Mark churned';
  return 'Delete';
}

export const TRANSITION_REQUIRES_REASON = new Set(['suspended', 'churned', 'pending_deletion', 'deleted']);

export type TabKey = 'overview' | 'usage' | 'integrations' | 'support' | 'activity';

export const TABS: { key: TabKey; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'usage', label: 'Usage' },
  { key: 'integrations', label: 'Integrations' },
  { key: 'support', label: 'Support' },
  { key: 'activity', label: 'Activity' },
];

export const statusTone: Record<string, string> = {
  active: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  trial: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  provisioning: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
  suspended: 'bg-red-500/15 text-red-400 border-red-500/30',
  churned: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
  pending_deletion: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  deleted: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
};

export function initials(name: string): string {
  return (
    name
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join('') || '?'
  );
}
