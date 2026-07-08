import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Network,
  ReceiptText,
  Sparkles,
  Search as SearchIcon,
  Headset,
  ScrollText,
  ShieldCheck,
  Settings,
  Bell,
  HelpCircle,
  ChevronDown,
  Plus,
  Download,
  Users2,
  CheckCircle2,
  Clock3,
  CircleSlash,
  Trash2,
  Crown,
  Globe2,
  Loader2,
  X,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../../lib/auth/AuthProvider';
import { usePlatformPermissions } from '../../lib/auth/usePlatformPermissions';
import { platformControlApi, toSafeUserMessage } from '../../api';
import { TenantDetailPanel } from './TenantDetailPanel';
import { REGIONS, TENANT_STATUSES, initials, statusTone, type DashboardSummary, type PlanRecord, type TenantRecord } from './tenantTypes';

const PAGE_SIZE = 25;

const NAV_ITEMS: { label: string; icon: typeof LayoutDashboard; to: string | null }[] = [
  { label: 'Overview', icon: LayoutDashboard, to: '/' },
  { label: 'Tenants', icon: Network, to: '/tenants' },
  { label: 'Subscriptions', icon: ReceiptText, to: '/platform/plans' },
  { label: 'Usage & Billing', icon: ReceiptText, to: null },
  { label: 'AI Governance', icon: Sparkles, to: '/platform/ai-governance' },
  { label: 'Infrastructure', icon: Network, to: '/platform/operations' },
  { label: 'Integrations', icon: Network, to: null },
  { label: 'Support', icon: Headset, to: '/platform/support' },
  { label: 'Audit Logs', icon: ScrollText, to: '/platform/audit-logs' },
  { label: 'Security', icon: ShieldCheck, to: '/security' },
  { label: 'Settings', icon: Settings, to: null },
];

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

function shortId(id: string): string {
  return `TEN-${id.slice(0, 8).toUpperCase()}`;
}

// If the user pastes/types the short "TEN-XXXXXXXX" form shown in the table (derived
// from the first 8 hex chars of the tenant UUID), translate it back to the raw hex
// fragment the backend's `id::text ILIKE` search actually matches against.
function normalizeSearchTerm(raw: string): string {
  const trimmed = raw.trim();
  const match = /^TEN-([0-9a-f]{4,8})$/i.exec(trimmed);
  return match ? match[1].toLowerCase() : trimmed;
}

function statCount(summary: DashboardSummary | null, status: string): number {
  return summary?.tenants_by_status.find((row) => row.status === status)?.count ?? 0;
}

function statTotal(summary: DashboardSummary | null): number {
  return summary?.tenants_by_status.reduce((sum, row) => sum + row.count, 0) ?? 0;
}

function pct(count: number, total: number): string {
  if (total === 0) return '0%';
  return `${((count / total) * 100).toFixed(1)}%`;
}

function toCsv(rows: TenantRecord[], planNames: Map<string, string>): string {
  const header = ['Tenant ID', 'Name', 'Status', 'Plan', 'Region', 'Primary Admin Email', 'Created On'];
  const lines = rows.map((row) =>
    [row.id, row.name, row.status, row.plan_id ? planNames.get(row.plan_id) ?? row.plan_id : '', row.region, row.primary_admin_email, row.created_at]
      .map((value) => `"${String(value).replace(/"/g, '""')}"`)
      .join(','),
  );
  return [header.join(','), ...lines].join('\n');
}

export function TenantManagementPage() {
  const navigate = useNavigate();
  const { admin, withFreshToken, signOut } = useAuth();
  const { can, loadingPermissions } = usePlatformPermissions();

  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [rows, setRows] = useState<TenantRecord[]>([]);
  const [plans, setPlans] = useState<PlanRecord[]>([]);
  const [cursorStack, setCursorStack] = useState<(string | null)[]>([null]);
  const [pageIndex, setPageIndex] = useState(0);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [totalKnown, setTotalKnown] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [planFilter, setPlanFilter] = useState('');
  const [regionFilter, setRegionFilter] = useState('');

  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);

  const planNames = useMemo(() => new Map(plans.map((plan) => [plan.id, plan.name])), [plans]);

  const loadPage = useCallback(
    async (cursor: string | null) => {
      setLoading(true);
      setError(null);
      try {
        const query: Record<string, string> = { limit: String(PAGE_SIZE) };
        if (cursor) query.cursor = cursor;
        if (search.trim()) query.search = search.trim();
        if (statusFilter) query.status = statusFilter;
        if (planFilter) query.plan_id = planFilter;
        if (regionFilter) query.region = regionFilter;
        const page = await withFreshToken((token) => platformControlApi.list<TenantRecord>(token, '/v1/platform-admin/tenants', query));
        setRows(page.data);
        setNextCursor(page.page.next_cursor);
        setHasMore(page.page.has_more);
      } catch (err) {
        setError(toSafeUserMessage(err));
      } finally {
        setLoading(false);
      }
    },
    [planFilter, regionFilter, search, statusFilter, withFreshToken],
  );

  const loadSummary = useCallback(async () => {
    try {
      const envelope = await withFreshToken((token) => platformControlApi.get<DashboardSummary>(token, '/v1/platform-admin/dashboard/summary'));
      setSummary(envelope.data);
      setTotalKnown(statTotal(envelope.data));
    } catch {
      // Stat cards are a convenience; a failed summary fetch shouldn't block the table.
    }
  }, [withFreshToken]);

  const loadPlans = useCallback(async () => {
    try {
      const page = await withFreshToken((token) => platformControlApi.list<PlanRecord>(token, '/v1/platform-admin/plans', { limit: '200' }));
      setPlans(page.data);
    } catch {
      // Plan names are a display convenience; fall back to showing the raw plan_id.
    }
  }, [withFreshToken]);

  useEffect(() => {
    void loadSummary();
    void loadPlans();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    setCursorStack([null]);
    setPageIndex(0);
    void loadPage(null);
  }, [loadPage]);

  function goNext() {
    if (!hasMore || !nextCursor) return;
    setCursorStack((stack) => [...stack.slice(0, pageIndex + 1), nextCursor]);
    setPageIndex((i) => i + 1);
    void loadPage(nextCursor);
  }

  function goPrevious() {
    if (pageIndex === 0) return;
    const previousCursor = cursorStack[pageIndex - 1];
    setPageIndex((i) => i - 1);
    void loadPage(previousCursor);
  }

  function handleSearchSubmit(event: FormEvent) {
    event.preventDefault();
    setSearch(normalizeSearchTerm(searchInput));
  }

  function filterByStatus(status: string) {
    setStatusFilter((current) => (current === status ? '' : status));
  }

  function resetFilters() {
    setSearchInput('');
    setSearch('');
    setStatusFilter('');
    setPlanFilter('');
    setRegionFilter('');
  }

  function handleTenantChanged(updated: TenantRecord) {
    setRows((current) => current.map((row) => (row.id === updated.id ? updated : row)));
    void loadSummary();
  }

  function exportCsv() {
    const csv = toCsv(rows, planNames);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'tenants.csv';
    anchor.click();
    URL.revokeObjectURL(url);
  }

  const canRead = loadingPermissions || can('platform.tenant.read');
  const canCreate = can('platform.tenant.create');
  const rangeStart = pageIndex * PAGE_SIZE + (rows.length > 0 ? 1 : 0);
  const rangeEnd = pageIndex * PAGE_SIZE + rows.length;

  return (
    <div className="h-screen flex bg-[#0B1220] overflow-hidden text-slate-200">
      <aside className="hidden md:flex flex-col w-[248px] shrink-0 bg-[#0E1626] border-r border-white/10">
        <div className="h-14 flex items-center gap-2.5 px-4 shrink-0 border-b border-white/10">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center shrink-0">
            <span className="text-white font-bold text-xs leading-none">gN</span>
          </div>
          <span className="text-white font-bold text-[15px] tracking-tight truncate">GNXTHIRE</span>
        </div>

        <div className="px-3 pt-3 pb-1">
          <div className="flex items-center gap-2 px-3 h-9 rounded-lg bg-white/[0.04] border border-white/10">
            <ShieldCheck size={14} className="text-blue-400 shrink-0" />
            <span className="text-xs font-semibold text-slate-300 truncate">Platform Admin</span>
            <ChevronDown size={12} className="text-slate-500 ml-auto shrink-0" />
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-0.5">
          {NAV_ITEMS.map((item) =>
            item.to ? (
              <NavLink
                key={item.label}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  [
                    'flex items-center gap-3 px-3 h-9 rounded-lg text-sm font-medium transition-colors',
                    isActive ? 'bg-blue-500/15 text-blue-400' : 'text-slate-400 hover:text-white hover:bg-white/5',
                  ].join(' ')
                }
              >
                <item.icon size={16} className="shrink-0" />
                <span className="truncate">{item.label}</span>
              </NavLink>
            ) : (
              <div
                key={item.label}
                title="Not available yet"
                className="flex items-center gap-3 px-3 h-9 rounded-lg text-sm font-medium text-slate-600 cursor-default"
              >
                <item.icon size={16} className="shrink-0" />
                <span className="truncate">{item.label}</span>
              </div>
            ),
          )}
        </nav>

        <div className="p-3 border-t border-white/10 shrink-0">
          <div className="rounded-xl bg-white/[0.04] border border-white/10 p-3">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">System Health</p>
            <div className="flex items-center gap-1.5 text-emerald-400">
              <CheckCircle2 size={13} />
              <span className="text-xs font-semibold">All Systems Operational</span>
            </div>
          </div>
          <p className="text-[10px] text-slate-600 mt-2 px-1">Version 1.0.0</p>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 h-full">
        <header className="h-14 bg-[#0E1626] border-b border-white/10 flex items-center gap-3 px-4 lg:px-6 shrink-0">
          <div className="flex items-center gap-1.5 text-[13px] text-slate-500 min-w-0">
            <span className="truncate">System Admin</span>
            <span>/</span>
            <span className="text-white font-semibold truncate">Tenant Management</span>
          </div>
          <div className="flex-1" />
          <div className="hidden sm:flex items-center gap-2 h-9 px-3 rounded-lg bg-white/[0.04] border border-white/10 w-64 text-slate-500">
            <SearchIcon size={14} className="shrink-0" />
            <span className="text-xs truncate">Search anything...</span>
            <span className="ml-auto text-[10px] font-mono text-slate-600 border border-white/10 rounded px-1">⌘K</span>
          </div>
          <button className="relative w-9 h-9 flex items-center justify-center rounded-lg hover:bg-white/5 text-slate-400 transition-colors shrink-0" aria-label="Notifications">
            <Bell size={16} />
          </button>
          <button className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-white/5 text-slate-400 transition-colors shrink-0" aria-label="Help">
            <HelpCircle size={16} />
          </button>
          <div className="relative shrink-0">
            <button onClick={() => setProfileMenuOpen((v) => !v)} className="flex items-center gap-2 h-9 pl-1.5 pr-2 rounded-lg hover:bg-white/5 transition-colors">
              <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-[10px] font-bold text-white shrink-0">
                {initials(admin?.display_name ?? admin?.email ?? '?')}
              </div>
              <div className="hidden sm:block text-left leading-none">
                <p className="text-xs font-semibold text-white">{admin?.display_name ?? admin?.email}</p>
                <p className="text-[10px] text-slate-500 mt-0.5">Platform Admin</p>
              </div>
              <ChevronDown size={12} className="text-slate-500" />
            </button>
            {profileMenuOpen && (
              <div className="absolute right-0 top-full mt-1.5 w-44 bg-[#1a2333] border border-white/10 rounded-lg shadow-xl py-1 z-30">
                <button
                  onClick={() => void signOut().then(() => navigate('/auth/login', { replace: true }))}
                  className="w-full flex items-center gap-2.5 px-3.5 py-2 text-[13px] text-red-400 hover:bg-white/[0.06] transition-colors"
                >
                  <LogOut size={13} />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="max-w-[1500px] mx-auto px-4 lg:px-6 py-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5">
              <div>
                <h1 className="text-xl font-bold text-white leading-tight">Tenant Management</h1>
                <p className="text-sm text-slate-500 mt-0.5">View and manage all tenants in the platform.</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {canCreate && (
                  <button
                    onClick={() => setShowCreate(true)}
                    className="flex items-center gap-1.5 h-9 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-[13px] font-semibold transition-colors"
                  >
                    <Plus size={15} />
                    Provision New Tenant
                  </button>
                )}
                <button onClick={exportCsv} className="w-9 h-9 flex items-center justify-center rounded-lg bg-white/[0.04] border border-white/10 hover:bg-white/10 text-slate-300 transition-colors" aria-label="Export CSV">
                  <Download size={15} />
                </button>
              </div>
            </div>

            {!canRead ? (
              <div className="bg-[#111827] border border-white/10 rounded-2xl py-16 text-center">
                <p className="text-sm font-semibold text-slate-300">You don't have access to this area</p>
                <p className="text-xs text-slate-500 mt-1">This section requires the platform.tenant.read permission.</p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-5">
                  <StatCard icon={Users2} label="Total Tenants" value={statTotal(summary)} tone="text-violet-400 bg-violet-500/10" active={statusFilter === ''} onClick={() => setStatusFilter('')} />
                  <StatCard
                    icon={CheckCircle2}
                    label="Active Tenants"
                    value={statCount(summary, 'active')}
                    sub={pct(statCount(summary, 'active'), statTotal(summary)) + ' of total'}
                    tone="text-emerald-400 bg-emerald-500/10"
                    active={statusFilter === 'active'}
                    onClick={() => filterByStatus('active')}
                  />
                  <StatCard
                    icon={Clock3}
                    label="Trial Tenants"
                    value={statCount(summary, 'trial')}
                    sub={pct(statCount(summary, 'trial'), statTotal(summary)) + ' of total'}
                    tone="text-blue-400 bg-blue-500/10"
                    active={statusFilter === 'trial'}
                    onClick={() => filterByStatus('trial')}
                  />
                  <StatCard
                    icon={CircleSlash}
                    label="Suspended Tenants"
                    value={statCount(summary, 'suspended')}
                    sub={pct(statCount(summary, 'suspended'), statTotal(summary)) + ' of total'}
                    tone="text-red-400 bg-red-500/10"
                    active={statusFilter === 'suspended'}
                    onClick={() => filterByStatus('suspended')}
                  />
                  <StatCard
                    icon={Trash2}
                    label="Pending Deletion"
                    value={statCount(summary, 'pending_deletion')}
                    sub={pct(statCount(summary, 'pending_deletion'), statTotal(summary)) + ' of total'}
                    tone="text-amber-400 bg-amber-500/10"
                    active={statusFilter === 'pending_deletion'}
                    onClick={() => filterByStatus('pending_deletion')}
                  />
                </div>

                <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-2 mb-4">
                  <div className="relative flex-1 min-w-[220px] max-w-sm">
                    <SearchIcon size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input
                      value={searchInput}
                      onChange={(e) => setSearchInput(e.target.value)}
                      placeholder="Search by name, tenant ID, domain, admin email, or legal entity..."
                      className="w-full h-9 pl-9 pr-3 text-sm rounded-lg bg-[#111827] border border-white/10 text-slate-200 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                    />
                  </div>
                  <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="h-9 px-3 text-sm rounded-lg bg-[#111827] border border-white/10 text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500/50">
                    <option value="">Status: All</option>
                    {TENANT_STATUSES.map((s) => (
                      <option key={s} value={s} className="capitalize">
                        {s.replace(/_/g, ' ')}
                      </option>
                    ))}
                  </select>
                  <select value={planFilter} onChange={(e) => setPlanFilter(e.target.value)} className="h-9 px-3 text-sm rounded-lg bg-[#111827] border border-white/10 text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500/50">
                    <option value="">Plan: All</option>
                    {plans.map((plan) => (
                      <option key={plan.id} value={plan.id}>
                        {plan.name}
                      </option>
                    ))}
                  </select>
                  <select value={regionFilter} onChange={(e) => setRegionFilter(e.target.value)} className="h-9 px-3 text-sm rounded-lg bg-[#111827] border border-white/10 text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500/50">
                    <option value="">Region: All</option>
                    {REGIONS.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                  <button type="submit" className="h-9 px-3 rounded-lg bg-white/[0.04] border border-white/10 hover:bg-white/10 text-slate-300 text-sm font-medium transition-colors">
                    Apply
                  </button>
                  <button type="button" onClick={resetFilters} className="text-sm text-blue-400 hover:text-blue-300 font-medium">
                    Reset
                  </button>
                </form>

                {error && <p className="text-sm text-red-400 mb-3">{error}</p>}

                <div>
                  <div className="bg-[#111827] border border-white/10 rounded-2xl overflow-hidden shadow-sm">
                    {loading && rows.length === 0 ? (
                      <div className="flex items-center justify-center py-20">
                        <Loader2 size={22} className="text-slate-500 animate-spin" />
                      </div>
                    ) : rows.length === 0 ? (
                      <div className="text-center py-20">
                        <p className="text-sm font-semibold text-slate-300">No tenants found</p>
                        <p className="text-xs text-slate-500 mt-1">Try adjusting your search or filters.</p>
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="min-w-full border-collapse">
                          <thead>
                            <tr className="border-b border-white/10">
                              <th className="text-left text-[11px] font-bold text-slate-500 uppercase tracking-wide px-4 py-3">Tenant Name</th>
                              <th className="text-left text-[11px] font-bold text-slate-500 uppercase tracking-wide px-4 py-3">Status</th>
                              <th className="text-left text-[11px] font-bold text-slate-500 uppercase tracking-wide px-4 py-3">Plan</th>
                              <th className="text-left text-[11px] font-bold text-slate-500 uppercase tracking-wide px-4 py-3">Region</th>
                              <th className="text-left text-[11px] font-bold text-slate-500 uppercase tracking-wide px-4 py-3">Created On</th>
                              <th className="text-right text-[11px] font-bold text-slate-500 uppercase tracking-wide px-4 py-3">Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {rows.map((tenant) => (
                              <tr
                                key={tenant.id}
                                className={['border-b border-white/[0.06] last:border-0 transition-colors', selectedTenantId === tenant.id ? 'bg-blue-500/[0.06]' : 'hover:bg-white/[0.02]'].join(' ')}
                              >
                                <td className="px-4 py-3">
                                  <div className="flex items-center gap-2.5 min-w-0">
                                    <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-[11px] font-bold text-white shrink-0">{initials(tenant.name)}</div>
                                    <div className="min-w-0">
                                      <p className="text-[13px] font-semibold text-slate-100 truncate">{tenant.name}</p>
                                      <p className="text-[11px] text-slate-500 font-mono truncate">{shortId(tenant.id)}</p>
                                    </div>
                                  </div>
                                </td>
                                <td className="px-4 py-3">
                                  <span className={['text-[11px] font-semibold px-2 py-0.5 rounded-full border capitalize', statusTone[tenant.status] ?? statusTone.deleted].join(' ')}>
                                    {tenant.status.replace(/_/g, ' ')}
                                  </span>
                                </td>
                                <td className="px-4 py-3">
                                  <div className="flex items-center gap-1.5 text-[13px] text-slate-300">
                                    <Crown size={12} className="text-violet-400 shrink-0" />
                                    {tenant.plan_id ? planNames.get(tenant.plan_id) ?? '—' : '—'}
                                  </div>
                                </td>
                                <td className="px-4 py-3">
                                  <div className="flex items-center gap-1.5 text-[13px] text-slate-300">
                                    <Globe2 size={12} className="text-blue-400 shrink-0" />
                                    {tenant.region}
                                  </div>
                                </td>
                                <td className="px-4 py-3 text-[13px] text-slate-400 whitespace-nowrap">{formatDate(tenant.created_at)}</td>
                                <td className="px-4 py-3 text-right">
                                  <button
                                    onClick={() => setSelectedTenantId(tenant.id)}
                                    className="h-7 px-3 rounded-md bg-white/[0.06] hover:bg-white/10 text-[12px] font-medium text-slate-200 transition-colors"
                                  >
                                    Details
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    <div className="flex items-center justify-between px-4 py-3 border-t border-white/10 text-[12px] text-slate-500">
                      <span>
                        Showing {rangeStart}-{rangeEnd}
                        {totalKnown !== null ? ` of ${totalKnown} tenants.` : '.'}
                      </span>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={goPrevious}
                          disabled={pageIndex === 0 || loading}
                          className="h-7 px-3 rounded-md bg-white/[0.04] border border-white/10 hover:bg-white/10 disabled:opacity-30 text-slate-300 text-[12px] font-medium transition-colors"
                        >
                          Previous
                        </button>
                        <button
                          onClick={goNext}
                          disabled={!hasMore || loading}
                          className="h-7 px-3 rounded-md bg-white/[0.04] border border-white/10 hover:bg-white/10 disabled:opacity-30 text-slate-300 text-[12px] font-medium transition-colors"
                        >
                          Next
                        </button>
                      </div>
                    </div>
                  </div>

                  {selectedTenantId && (
                    <TenantDetailPanel tenantId={selectedTenantId} onClose={() => setSelectedTenantId(null)} onTenantChanged={handleTenantChanged} />
                  )}
                </div>
              </>
            )}
          </div>
        </main>
      </div>

      {showCreate && <CreateTenantModal onClose={() => setShowCreate(false)} onCreated={() => { setShowCreate(false); void loadPage(cursorStack[pageIndex]); void loadSummary(); }} />}
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  tone,
  active,
  onClick,
}: {
  icon: typeof Users2;
  label: string;
  value: number;
  sub?: string;
  tone: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={[
        'text-left bg-[#111827] border rounded-2xl p-4 transition-colors',
        active ? 'border-blue-500/60 ring-1 ring-blue-500/30' : 'border-white/10 hover:border-white/20',
      ].join(' ')}
    >
      <div className="flex items-center justify-between mb-3">
        <div className={['w-8 h-8 rounded-lg flex items-center justify-center', tone].join(' ')}>
          <Icon size={15} />
        </div>
      </div>
      <p className="text-2xl font-bold text-white tracking-tight leading-none mb-1">{value.toLocaleString()}</p>
      <p className="text-[11px] text-slate-500 font-medium leading-none">{label}</p>
      {sub && <p className="text-[10px] text-slate-600 mt-1.5">{sub}</p>}
    </button>
  );
}

function CreateTenantModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const { withFreshToken } = useAuth();
  const [name, setName] = useState('');
  const [tenantType, setTenantType] = useState('corporate');
  const [primaryAdminEmail, setPrimaryAdminEmail] = useState('');
  const [region, setRegion] = useState('US');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim() || !primaryAdminEmail.trim()) {
      setError('Enter a tenant name and admin email.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await withFreshToken((token) =>
        platformControlApi.post(token, '/v1/platform-admin/tenants', {
          name: name.trim(),
          tenant_type: tenantType,
          primary_admin_email: primaryAdminEmail.trim(),
          isolation_tier: 'shared',
          region,
          idempotency_key: crypto.randomUUID(),
        }),
      );
      onCreated();
    } catch (err) {
      setError(toSafeUserMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60" onClick={busy ? undefined : onClose} />
      <div className="relative bg-[#111827] border border-white/10 rounded-2xl w-full max-w-md">
        <div className="flex items-center justify-between p-5 border-b border-white/10">
          <h3 className="text-[15px] font-bold text-white">Provision new tenant</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-300">
            <X size={16} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {error && <p className="text-xs text-red-400">{error}</p>}
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Tenant name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={busy}
              className="w-full h-9 px-3 text-sm rounded-lg bg-white/[0.04] border border-white/10 text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Tenant type</label>
            <select
              value={tenantType}
              onChange={(e) => setTenantType(e.target.value)}
              disabled={busy}
              className="w-full h-9 px-3 text-sm rounded-lg bg-white/[0.04] border border-white/10 text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
            >
              <option value="corporate">Corporate</option>
              <option value="staffing_agency">Staffing agency</option>
              <option value="rpo">RPO</option>
              <option value="executive_search">Executive search</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Primary admin email</label>
            <input
              type="email"
              value={primaryAdminEmail}
              onChange={(e) => setPrimaryAdminEmail(e.target.value)}
              disabled={busy}
              className="w-full h-9 px-3 text-sm rounded-lg bg-white/[0.04] border border-white/10 text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Region</label>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              disabled={busy}
              className="w-full h-9 px-3 text-sm rounded-lg bg-white/[0.04] border border-white/10 text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
            >
              {REGIONS.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={onClose} disabled={busy} className="h-9 px-4 rounded-lg bg-white/[0.04] border border-white/10 text-slate-300 text-sm font-medium hover:bg-white/10 transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={busy} className="h-9 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-semibold transition-colors">
              {busy ? 'Provisioning…' : 'Provision tenant'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
