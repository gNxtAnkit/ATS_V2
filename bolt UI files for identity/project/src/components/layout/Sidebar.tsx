import { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Briefcase,
  Users,
  GitBranch,
  Calendar,
  Inbox,
  BarChart2,
  Settings,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  type LucideIcon,
} from 'lucide-react';
import { useAuthSession } from '../../lib/auth/authSession';

interface NavItem {
  label: string;
  icon: LucideIcon;
  path: string;
  badge?: number;
}

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const primaryNav: NavItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { label: 'Jobs', icon: Briefcase, path: '/jobs' },
  { label: 'Candidates', icon: Users, path: '/candidates' },
  { label: 'Pipeline', icon: GitBranch, path: '/pipeline' },
  { label: 'Interviews', icon: Calendar, path: '/interviews' },
  { label: 'Inbox', icon: Inbox, path: '/inbox', badge: 3 },
  { label: 'Reports', icon: BarChart2, path: '/reports' },
];

const bottomNav: NavItem[] = [
  { label: 'Settings', icon: Settings, path: '/settings/security/mfa/setup' },
  { label: 'Help', icon: HelpCircle, path: '/help' },
];

const platformPrimaryNav: NavItem[] = [
  { label: 'Console', icon: LayoutDashboard, path: '/platform-admin/dashboard' },
  { label: 'Platform users', icon: Users, path: '/platform-admin/users' },
  { label: 'Audit log', icon: Inbox, path: '/platform-admin/audit' },
  { label: 'Reports', icon: BarChart2, path: '/platform-admin/reports' },
];

const platformBottomNav: NavItem[] = [
  { label: 'Security', icon: Settings, path: '/platform-admin/security/mfa/setup' },
  { label: 'Help', icon: HelpCircle, path: '/platform-admin/help' },
];

/* ---------- Tooltip rendered via fixed positioning to avoid overflow issues ---------- */
interface TooltipState {
  label: string;
  top: number;
  left: number;
  badge?: number;
}

function FixedTooltip({ tooltip }: { tooltip: TooltipState | null }) {
  if (!tooltip) return null;
  return (
    <div
      className="fixed z-[9999] pointer-events-none"
      style={{ top: tooltip.top, left: tooltip.left }}
    >
      <div className="flex items-center gap-1.5 bg-gray-900 text-white text-xs font-medium px-2.5 py-1.5 rounded-lg shadow-float border border-white/10 whitespace-nowrap">
        {tooltip.label}
        {tooltip.badge ? (
          <span className="bg-blue-500/40 text-blue-200 rounded-full px-1.5 py-px text-[10px] font-semibold">
            {tooltip.badge}
          </span>
        ) : null}
      </div>
    </div>
  );
}

/* ---------- Single nav row ---------- */
function NavItemRow({
  item,
  collapsed,
  active,
  onTooltip,
}: {
  item: NavItem;
  collapsed: boolean;
  active: boolean;
  onTooltip: (t: TooltipState | null) => void;
}) {
  const navigate = useNavigate();
  const ref = useRef<HTMLButtonElement>(null);

  const handleMouseEnter = () => {
    if (!collapsed || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    onTooltip({
      label: item.label,
      badge: item.badge,
      top: rect.top + rect.height / 2 - 14,
      left: rect.right + 8,
    });
  };

  const handleMouseLeave = () => onTooltip(null);

  return (
    <button
      ref={ref}
      onClick={() => navigate(item.path)}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={[
        'w-full flex items-center rounded-lg transition-all duration-150 relative group select-none',
        collapsed ? 'h-9 justify-center' : 'h-9 gap-3 px-3',
        active
          ? 'bg-white/10 text-white'
          : 'text-slate-400 hover:bg-white/[0.06] hover:text-slate-200',
      ].join(' ')}
    >
      {/* Active left accent bar */}
      {active && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-[18px] bg-blue-400 rounded-r-full" />
      )}

      <item.icon
        size={17}
        className={[
          'shrink-0 transition-colors',
          active ? 'text-blue-400' : 'text-slate-500 group-hover:text-slate-300',
        ].join(' ')}
      />

      {!collapsed && (
        <span className="text-[13px] font-medium flex-1 text-left truncate leading-none">
          {item.label}
        </span>
      )}

      {/* Badge — expanded */}
      {!collapsed && item.badge ? (
        <span className="ml-auto text-[10px] font-bold bg-blue-500/25 text-blue-300 rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1 shrink-0">
          {item.badge}
        </span>
      ) : null}

      {/* Badge dot — collapsed */}
      {collapsed && item.badge ? (
        <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-blue-400 rounded-full" />
      ) : null}
    </button>
  );
}

/* ---------- Sidebar ---------- */
export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { realm } = useAuthSession();
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);
  const visiblePrimaryNav = realm === 'platform' ? platformPrimaryNav : primaryNav;
  const visibleBottomNav = realm === 'platform' ? platformBottomNav : bottomNav;
  const homePath = realm === 'platform' ? '/platform-admin/dashboard' : '/dashboard';
  const shellLabel = realm === 'platform' ? 'Admin Console' : 'ATS Platform';

  /* Dismiss tooltip when sidebar expands */
  useEffect(() => { if (!collapsed) setTooltip(null); }, [collapsed]);

  const isActive = (path: string) =>
    location.pathname === path || location.pathname.startsWith(path + '/');

  return (
    <>
      <FixedTooltip tooltip={collapsed ? tooltip : null} />

      <aside
        className={[
          /* NO overflow-hidden here — that was causing:
             1. The collapse toggle (-right-3) to be clipped
             2. Horizontal scroll artifacts during transition
             The outer AppShell div (overflow-hidden) contains everything */
          'hidden md:flex flex-col h-full bg-gray-900 shrink-0 relative sidebar-transition',
          collapsed ? 'w-[64px]' : 'w-[240px]',
        ].join(' ')}
      >
        {/* ── Logo / brand ── */}
        <div
          className={[
            'flex items-center h-14 shrink-0 border-b border-white/[0.07]',
            collapsed ? 'justify-center' : 'gap-2.5 px-4',
          ].join(' ')}
        >
          <button
            onClick={() => navigate(homePath)}
            className="flex items-center gap-2.5 min-w-0 group"
          >
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shrink-0 group-hover:bg-blue-500 transition-colors">
              <span className="text-white font-bold text-xs leading-none tracking-tight">gN</span>
            </div>
            {!collapsed && (
              <div className="min-w-0 overflow-hidden">
                <span className="text-white font-bold text-[15px] tracking-tight leading-none block truncate">
                  gNxtHire
                </span>
                <span className="text-slate-500 text-[10px] font-medium tracking-widest uppercase leading-none">
                  {shellLabel}
                </span>
              </div>
            )}
          </button>
        </div>

        {/* ── AI Copilot badge ── */}
        <div className={['shrink-0 pt-3 pb-1', collapsed ? 'px-[10px]' : 'px-3'].join(' ')}>
          {!collapsed ? (
            <div className="flex items-center gap-2 px-3 py-2 bg-violet-500/10 rounded-lg border border-violet-500/15">
              <Sparkles size={11} className="text-violet-400 shrink-0" />
              <span className="text-[11px] font-medium text-violet-300 truncate">AI Copilot active</span>
              <span className="ml-auto w-1.5 h-1.5 bg-violet-400 rounded-full animate-pulse shrink-0" />
            </div>
          ) : (
            <div
              title="AI Copilot active"
              className="w-full flex justify-center"
            >
              <div className="w-10 h-9 rounded-lg bg-violet-500/10 border border-violet-500/15 flex items-center justify-center">
                <Sparkles size={13} className="text-violet-400" />
              </div>
            </div>
          )}
        </div>

        {/* ── Primary navigation — scrollable ── */}
        <nav
          className={[
            'flex-1 overflow-y-auto overflow-x-hidden py-1 space-y-0.5',
            collapsed ? 'px-[10px]' : 'px-3',
          ].join(' ')}
        >
            {visiblePrimaryNav.map((item) => (
            <NavItemRow
              key={item.path}
              item={item}
              collapsed={collapsed}
              active={isActive(item.path)}
              onTooltip={setTooltip}
            />
          ))}
        </nav>

        {/* ── Bottom nav ── */}
        <div
          className={[
            'shrink-0 border-t border-white/[0.07] py-3 space-y-0.5',
            collapsed ? 'px-[10px]' : 'px-3',
          ].join(' ')}
        >
            {visibleBottomNav.map((item) => (
            <NavItemRow
              key={item.path}
              item={item}
              collapsed={collapsed}
              active={isActive(item.path)}
              onTooltip={setTooltip}
            />
          ))}

          {/* Workspace pill */}
          {!collapsed ? (
            <div className="mt-3 flex items-center gap-2.5 px-3 py-2.5 bg-white/[0.05] rounded-lg border border-white/[0.06]">
              <div className="w-6 h-6 bg-blue-600/30 border border-blue-500/20 rounded-md flex items-center justify-center shrink-0">
                <span className="text-blue-300 text-[9px] font-bold">AC</span>
              </div>
              <div className="min-w-0">
                <p className="text-[12px] font-semibold text-slate-200 truncate leading-none mb-0.5">
                  Acme Corp
                </p>
                <p className="text-[10px] text-slate-500">Enterprise plan</p>
              </div>
            </div>
          ) : (
            <div className="flex justify-center mt-3">
              <div
                title="Acme Corp — Enterprise"
                className="w-8 h-8 bg-blue-600/20 border border-blue-500/20 rounded-lg flex items-center justify-center"
              >
                <span className="text-blue-300 text-[9px] font-bold">AC</span>
              </div>
            </div>
          )}
        </div>

        {/* ── Collapse toggle — sits on the right edge ── */}
        <button
          onClick={onToggle}
          className="absolute -right-[11px] top-[70px] w-[22px] h-[22px] bg-gray-800 border border-gray-700 rounded-full flex items-center justify-center shadow-md hover:bg-gray-700 transition-colors z-20"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronRight size={10} className="text-slate-400 translate-x-px" />
          ) : (
            <ChevronLeft size={10} className="text-slate-400 -translate-x-px" />
          )}
        </button>
      </aside>
    </>
  );
}
