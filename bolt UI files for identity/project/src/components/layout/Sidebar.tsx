import { LayoutDashboard, Settings, ChevronLeft, ChevronRight, type LucideIcon } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuthSession } from '../../lib/auth/authSession';

interface NavItem {
  label: string;
  icon: LucideIcon;
  path: string;
}

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const tenantNav: NavItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { label: 'Security', icon: Settings, path: '/settings/security/mfa/setup' },
];

const platformNav: NavItem[] = [
  { label: 'Console', icon: LayoutDashboard, path: '/platform-admin/dashboard' },
  { label: 'Security', icon: Settings, path: '/platform-admin/security/mfa/setup' },
];

function NavItemRow({ item, collapsed, active }: { item: NavItem; collapsed: boolean; active: boolean }) {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate(item.path)}
      title={collapsed ? item.label : undefined}
      className={[
        'w-full flex items-center rounded-lg transition-all duration-150 relative group select-none',
        collapsed ? 'h-9 justify-center' : 'h-9 gap-3 px-3',
        active ? 'bg-white/10 text-white' : 'text-slate-400 hover:bg-white/[0.06] hover:text-slate-200',
      ].join(' ')}
    >
      {active && <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-[18px] bg-blue-400 rounded-r-full" />}
      <item.icon size={17} className={active ? 'text-blue-400' : 'text-slate-500 group-hover:text-slate-300'} />
      {!collapsed && <span className="text-[13px] font-medium flex-1 text-left truncate leading-none">{item.label}</span>}
    </button>
  );
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { realm } = useAuthSession();
  const visibleNav = realm === 'platform' ? platformNav : tenantNav;
  const homePath = realm === 'platform' ? '/platform-admin/dashboard' : '/dashboard';
  const shellLabel = realm === 'platform' ? 'Admin Console' : 'Identity';
  const isActive = (path: string) => location.pathname === path || location.pathname.startsWith(path + '/');

  return (
    <aside className={['hidden md:flex flex-col h-full bg-gray-900 shrink-0 relative sidebar-transition', collapsed ? 'w-[64px]' : 'w-[240px]'].join(' ')}>
      <div className={['flex items-center h-14 shrink-0 border-b border-white/[0.07]', collapsed ? 'justify-center' : 'gap-2.5 px-4'].join(' ')}>
        <button onClick={() => navigate(homePath)} className="flex items-center gap-2.5 min-w-0 group">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shrink-0 group-hover:bg-blue-500 transition-colors">
            <span className="text-white font-bold text-xs leading-none tracking-tight">gN</span>
          </div>
          {!collapsed && (
            <div className="min-w-0 overflow-hidden">
              <span className="text-white font-bold text-[15px] tracking-tight leading-none block truncate">gNxtHire</span>
              <span className="text-slate-500 text-[10px] font-medium tracking-widest uppercase leading-none">{shellLabel}</span>
            </div>
          )}
        </button>
      </div>

      <nav className={['flex-1 overflow-y-auto overflow-x-hidden py-3 space-y-0.5', collapsed ? 'px-[10px]' : 'px-3'].join(' ')}>
        {visibleNav.map((item) => (
          <NavItemRow key={item.path} item={item} collapsed={collapsed} active={isActive(item.path)} />
        ))}
      </nav>

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
  );
}
