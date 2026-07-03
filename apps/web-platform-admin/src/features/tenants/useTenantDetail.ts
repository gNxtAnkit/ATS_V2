import { useCallback, useEffect, useState } from 'react';
import { platformControlApi, toSafeUserMessage } from '../../api';
import { useAuth } from '../../lib/auth/AuthProvider';
import type { EffectiveEntitlements, PlanRecord, SubscriptionSummary, TenantDomain, TenantHealth, TenantRecord } from './tenantTypes';

export interface TenantDetailData {
  tenant: TenantRecord;
  domains: TenantDomain[];
  plan: PlanRecord | null;
  health: TenantHealth | null;
  entitlements: EffectiveEntitlements | null;
  subscription: SubscriptionSummary | null;
}

/** Shared data-fetching for both the popup and the full-page tenant detail views —
 * wires every real read endpoint available for a tenant on the platform-admin service. */
export function useTenantDetail(tenantId: string) {
  const { withFreshToken } = useAuth();
  const [data, setData] = useState<TenantDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [tenantEnvelope, domainsPage, healthEnvelope, subscriptionEnvelope] = await Promise.all([
        withFreshToken((token) => platformControlApi.get<TenantRecord>(token, `/v1/platform-admin/tenants/${tenantId}`)),
        withFreshToken((token) => platformControlApi.list<TenantDomain>(token, `/v1/platform-admin/tenants/${tenantId}/domains`)),
        withFreshToken((token) => platformControlApi.get<TenantHealth>(token, `/v1/platform-admin/tenants/${tenantId}/health`)).catch(() => null),
        withFreshToken((token) => platformControlApi.get<SubscriptionSummary>(token, `/v1/platform-admin/tenants/${tenantId}/subscription-summary`)).catch(() => null),
      ]);
      const tenant = tenantEnvelope.data;
      let plan: PlanRecord | null = null;
      let entitlements: EffectiveEntitlements | null = null;
      if (tenant.plan_id) {
        [plan, entitlements] = await Promise.all([
          withFreshToken((token) => platformControlApi.get<PlanRecord>(token, `/v1/platform-admin/plans/${tenant.plan_id}`)).then((r) => r.data).catch(() => null),
          withFreshToken((token) => platformControlApi.get<EffectiveEntitlements>(token, `/v1/platform-admin/tenants/${tenantId}/effective-entitlements`)).then((r) => r.data).catch(() => null),
        ]);
      }
      setData({ tenant, domains: domainsPage.data, plan, health: healthEnvelope?.data ?? null, entitlements, subscription: subscriptionEnvelope?.data ?? null });
    } catch (err) {
      setError(toSafeUserMessage(err));
    } finally {
      setLoading(false);
    }
  }, [tenantId, withFreshToken]);

  useEffect(() => {
    void load();
  }, [load]);

  const setTenant = useCallback((tenant: TenantRecord) => {
    setData((current) => (current ? { ...current, tenant } : current));
  }, []);

  return { data, loading, error, reload: load, setTenant };
}
