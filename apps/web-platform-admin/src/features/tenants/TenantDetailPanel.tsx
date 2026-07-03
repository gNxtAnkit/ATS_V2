import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Maximize2, Loader2 } from 'lucide-react';
import { TenantActions, TenantTabPanel, TenantTabs } from './TenantDetailContent';
import { useTenantDetail } from './useTenantDetail';
import { initials, statusTone, type TabKey, type TenantRecord } from './tenantTypes';

export function TenantDetailPanel({ tenantId, onClose, onTenantChanged }: { tenantId: string; onClose: () => void; onTenantChanged: (tenant: TenantRecord) => void }) {
  const navigate = useNavigate();
  const { data, loading, error, setTenant } = useTenantDetail(tenantId);
  const [tab, setTab] = useState<TabKey>('overview');

  useEffect(() => {
    setTab('overview');
  }, [tenantId]);

  useEffect(() => {
    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onClose]);

  function handleTenantChanged(updated: TenantRecord) {
    setTenant(updated);
    onTenantChanged(updated);
  }

  return (
    <div className="fixed inset-0 z-40 flex items-start sm:items-center justify-center p-0 sm:p-6">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-[1px]" onClick={onClose} />
      <div className="relative bg-[#111827] border border-white/10 sm:rounded-2xl w-full sm:max-w-2xl h-full sm:h-auto sm:max-h-[88vh] flex flex-col overflow-hidden shadow-2xl">
        {loading && !data ? (
          <div className="flex items-center justify-center py-24">
            <Loader2 size={22} className="text-slate-500 animate-spin" />
          </div>
        ) : error && !data ? (
          <div className="p-6">
            <p className="text-sm text-red-400">{error}</p>
            <button onClick={onClose} className="mt-4 h-9 px-4 rounded-lg bg-white/[0.06] hover:bg-white/10 text-slate-300 text-sm font-medium transition-colors">
              Close
            </button>
          </div>
        ) : data ? (
          <>
            <div className="flex items-center gap-3 px-5 pt-5 pb-4 shrink-0">
              <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center shrink-0">
                <span className="text-white text-xs font-bold">{initials(data.tenant.name)}</span>
              </div>
              <h2 className="text-[15px] font-bold text-white truncate flex-1 min-w-0">{data.tenant.name}</h2>
              <span className={['text-[11px] font-semibold px-2 py-0.5 rounded-full border capitalize shrink-0', statusTone[data.tenant.status] ?? statusTone.deleted].join(' ')}>
                {data.tenant.status.replace(/_/g, ' ')}
              </span>
              <button
                onClick={() => navigate(`/tenants/${tenantId}`)}
                className="text-slate-500 hover:text-white transition-colors shrink-0"
                aria-label="Open in full page"
                title="Open in full page"
              >
                <Maximize2 size={15} />
              </button>
              <button onClick={onClose} className="text-slate-500 hover:text-white transition-colors shrink-0" aria-label="Close">
                <X size={16} />
              </button>
            </div>

            <div className="shrink-0">
              <TenantTabs tab={tab} onChange={setTab} />
            </div>

            <div className="p-5 flex-1 overflow-y-auto">
              {error && <p className="text-xs text-red-400 mb-3">{error}</p>}
              <TenantTabPanel tab={tab} data={data} tenantId={tenantId} layout="popup" />
            </div>

            {tab === 'overview' && (
              <div className="px-5 pb-5 shrink-0">
                <TenantActions tenant={data.tenant} onChanged={handleTenantChanged} />
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}
