import {
  Network,
  RefreshCw,
  ReceiptText,
  SlidersHorizontal,
  Users,
  TicketCheck,
  Shield,
  Sparkles,
  Search,
  type LucideIcon,
} from 'lucide-react';

export type JsonRecord = Record<string, unknown>;

export interface PlatformActionConfig {
  label: string;
  permission: string;
  method: 'POST' | 'PATCH' | 'PUT' | 'DELETE';
  path: (record: JsonRecord | null) => string | null;
  body?: (record: JsonRecord | null) => JsonRecord | undefined;
  confirm?: string;
  destructive?: boolean;
}

export interface PlatformModuleConfig {
  slug: string;
  title: string;
  description: string;
  icon: LucideIcon;
  readPermission: string;
  listPath: string;
  detailPath?: (record: JsonRecord) => string | null;
  actions?: PlatformActionConfig[];
}

export function idPath(basePath: string, id: unknown, suffix?: string): string | null {
  if (typeof id !== 'string' || id.length === 0) return null;
  return suffix ? `${basePath}/${id}/${suffix}` : `${basePath}/${id}`;
}

// Mirrors the real platform-admin control-plane API surface — see
// services/platform-admin/src/gnxthire_platform_admin/routes.py for the
// backing routes and services/platform-admin/.../routes.py `_route_permission`
// for the exact permission keys enforced server-side.
export const PLATFORM_MODULES: PlatformModuleConfig[] = [
  {
    slug: 'tenants',
    title: 'Tenants',
    description: 'Search tenants, inspect lifecycle state, domains, provisioning, entitlements, and support context.',
    icon: Network,
    readPermission: 'platform.tenant.read',
    listPath: '/v1/platform-admin/tenants',
    detailPath: (record) => idPath('/v1/platform-admin/tenants', record.id),
    actions: [
      {
        label: 'Suspend',
        permission: 'platform.tenant.lifecycle.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/tenants', record?.id, 'suspend'),
        body: () => ({ reason: 'Suspended from Platform Admin Portal' }),
        confirm: 'Suspend this tenant? They will lose access until reactivated.',
        destructive: true,
      },
      {
        label: 'Reactivate',
        permission: 'platform.tenant.lifecycle.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/tenants', record?.id, 'reactivate'),
        body: () => ({ reason: 'Reactivated from Platform Admin Portal' }),
        confirm: 'Reactivate this tenant?',
      },
    ],
  },
  {
    slug: 'provisioning',
    title: 'Provisioning',
    description: 'Review tenant provisioning jobs and retry or cancel failed work where supported.',
    icon: RefreshCw,
    readPermission: 'platform.provisioning.read',
    listPath: '/v1/platform-admin/provisioning-jobs',
    detailPath: (record) => idPath('/v1/platform-admin/provisioning-jobs', record.id),
    actions: [
      {
        label: 'Retry',
        permission: 'platform.provisioning.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/provisioning-jobs', record?.id, 'retry'),
        confirm: 'Retry this provisioning job?',
      },
      {
        label: 'Cancel',
        permission: 'platform.provisioning.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/provisioning-jobs', record?.id, 'cancel'),
        confirm: 'Cancel this provisioning job?',
        destructive: true,
      },
    ],
  },
  {
    slug: 'plans',
    title: 'Plans, Quotas & Features',
    description: 'Manage the catalogue that controls subscription capabilities and effective entitlements.',
    icon: ReceiptText,
    readPermission: 'platform.plan.read',
    listPath: '/v1/platform-admin/plans',
    detailPath: (record) => idPath('/v1/platform-admin/plans', record.id),
    actions: [
      {
        label: 'Activate',
        permission: 'platform.plan.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/plans', record?.id, 'activate'),
      },
      {
        label: 'Retire',
        permission: 'platform.plan.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/plans', record?.id, 'retire'),
        confirm: 'Retire this plan? Tenants cannot be assigned to it afterward.',
        destructive: true,
      },
    ],
  },
  {
    slug: 'feature-flags',
    title: 'Feature Flags',
    description: 'Inspect rollout settings, tenant overrides, and kill switch state.',
    icon: SlidersHorizontal,
    readPermission: 'platform.feature_flag.read',
    listPath: '/v1/platform-admin/feature-flags',
    detailPath: (record) => idPath('/v1/platform-admin/feature-flags', record.id),
  },
  {
    slug: 'access-control',
    title: 'Users, Roles & Permissions',
    description: 'Review platform administrators, role assignment, and permission matrices.',
    icon: Users,
    readPermission: 'platform.user.read',
    listPath: '/v1/platform-admin/access-control/users',
    detailPath: (record) => idPath('/v1/platform-admin/access-control/users', record.id),
    actions: [
      {
        label: 'Lock',
        permission: 'platform.user.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/access-control/users', record?.id, 'lock'),
        confirm: 'Lock this platform admin? They will be signed out immediately.',
        destructive: true,
      },
      {
        label: 'Unlock',
        permission: 'platform.user.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/access-control/users', record?.id, 'unlock'),
      },
    ],
  },
  {
    slug: 'support',
    title: 'Support',
    description: 'Manage support sessions, support tickets, and SLA policy records.',
    icon: TicketCheck,
    readPermission: 'platform.support_ticket.read',
    listPath: '/v1/platform-admin/support-tickets',
    detailPath: (record) => idPath('/v1/platform-admin/support-tickets', record.id),
    actions: [
      {
        label: 'Close',
        permission: 'platform.support_ticket.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/support-tickets', record?.id, 'close'),
        body: () => ({ resolution_summary: 'Closed from the Platform Admin Portal.' }),
        confirm: 'Close this ticket?',
      },
    ],
  },
  {
    slug: 'compliance',
    title: 'Compliance',
    description: 'Review frameworks, region mappings, and tenant compliance assignments.',
    icon: Shield,
    readPermission: 'platform.compliance.read',
    listPath: '/v1/platform-admin/compliance/frameworks',
    detailPath: (record) => idPath('/v1/platform-admin/compliance/frameworks', record.id),
  },
  {
    slug: 'ai-governance',
    title: 'AI Governance',
    description: 'Review AI models, quality metrics, region restrictions, and governance alerts.',
    icon: Sparkles,
    readPermission: 'platform.ai_governance.read',
    listPath: '/v1/platform-admin/ai/governance-alerts',
    detailPath: (record) => idPath('/v1/platform-admin/ai/governance-alerts', record.id),
    actions: [
      {
        label: 'Acknowledge',
        permission: 'platform.ai_governance.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/ai/governance-alerts', record?.id, 'acknowledge'),
      },
      {
        label: 'Resolve',
        permission: 'platform.ai_governance.manage',
        method: 'POST',
        path: (record) => idPath('/v1/platform-admin/ai/governance-alerts', record?.id, 'resolve'),
        confirm: 'Resolve this AI governance alert?',
      },
    ],
  },
  {
    slug: 'operations',
    title: 'Operations',
    description: 'Inspect API versions, deployments, SLO definitions, and error budget status.',
    icon: Search,
    readPermission: 'platform.operations.read',
    listPath: '/v1/platform-admin/api-versions',
    detailPath: (record) => idPath('/v1/platform-admin/api-versions', record.id),
  },
  {
    slug: 'audit-logs',
    title: 'Audit Logs',
    description: 'Search redacted platform audit records for security-sensitive changes.',
    icon: ReceiptText,
    readPermission: 'platform.audit_log.read',
    listPath: '/v1/platform-admin/audit-logs',
    detailPath: (record) => idPath('/v1/platform-admin/audit-logs', record.id),
  },
];
