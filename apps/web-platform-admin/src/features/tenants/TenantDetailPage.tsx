import { useState } from 'react';
import { Navigate, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { TenantActions, TenantTabPanel, TenantTabs } from './TenantDetailContent';
import { useTenantDetail } from './useTenantDetail';
import { initials, statusTone, type TabKey } from './tenantTypes';

export function TenantDetailPage() {
  const { tenantId } = useParams<{ tenantId: string }>();
  const navigate = useNavigate();
  const [tab, setTab] = useState<TabKey>('overview');

  if (!tenantId) return <Navigate to="/tenants" replace />;

  return <TenantDetailPageBody tenantId={tenantId} tab={tab} setTab={setTab} onBack={() => navigate('/tenants')} />;
}

function TenantDetailPageBody({
  tenantId,
  tab,
  setTab,
  onBack,
}: {
  tenantId: string;
  tab: TabKey;
  setTab: (tab: TabKey) => void;
  onBack: () => void;
}) {
  const { data, loading, error, setTenant } = useTenantDetail(tenantId);

  return (
    <div className="h-screen flex flex-col bg-[#0B1220] text-slate-200 overflow-hidden">
      <header className="shrink-0 bg-[#0E1626] border-b border-white/10 px-4 lg:px-6">
        <div className="h-14 flex items-center gap-3">
          <button onClick={onBack} className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5 text-slate-400 transition-colors shrink-0" aria-label="Back to tenants">
            <ArrowLeft size={17} />
          </button>
          <div className="flex items-center gap-1.5 text-[13px] text-slate-500 min-w-0">
            <span className="truncate">Tenant Management</span>
            <span>/</span>
            <span className="text-white font-semibold truncate">{data?.tenant.name ?? 'Loading…'}</span>
          </div>
          {data && (
            <>
              <span className={['text-[11px] font-semibold px-2 py-0.5 rounded-full border capitalize shrink-0', statusTone[data.tenant.status] ?? statusTone.deleted].join(' ')}>
                {data.tenant.status.replace(/_/g, ' ')}
              </span>
              <div className="flex-1" />
              <div className="hidden sm:flex items-center gap-2.5 shrink-0">
                <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-[11px] font-bold text-white shrink-0">{initials(data.tenant.name)}</div>
              </div>
            </>
          )}
        </div>
        {data && <TenantTabs tab={tab} onChange={setTab} />}
      </header>

      <main className="flex-1 overflow-y-auto">
        {loading && !data ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 size={24} className="text-slate-500 animate-spin" />
          </div>
        ) : error && !data ? (
          <div className="max-w-lg mx-auto py-24 text-center">
            <p className="text-sm text-red-400">{error}</p>
            <button onClick={onBack} className="mt-4 h-9 px-4 rounded-lg bg-white/[0.06] hover:bg-white/10 text-slate-300 text-sm font-medium transition-colors">
              Back to tenants
            </button>
          </div>
        ) : data ? (
          <div className="max-w-[1400px] mx-auto px-6 py-8">
            {error && <p className="text-sm text-red-400 mb-4">{error}</p>}
            <div className={['grid grid-cols-1 gap-8 items-start', tab === 'overview' ? 'xl:grid-cols-[1fr_320px]' : ''].join(' ')}>
              <TenantTabPanel tab={tab} data={data} tenantId={tenantId} layout="page" />
              {tab === 'overview' && (
                <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-5 xl:sticky xl:top-6">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-3">Actions</h3>
                  <TenantActions tenant={data.tenant} onChanged={setTenant} />
                </div>
              )}
            </div>
          </div>
        ) : null}
      </main>
    </div>
  );
}
