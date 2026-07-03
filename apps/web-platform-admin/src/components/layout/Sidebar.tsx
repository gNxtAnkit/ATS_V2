import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ShieldCheck, UsersRound, LogOut } from 'lucide-react';
import { PLATFORM_MODULES } from '../../features/modules/moduleConfig';
import { useAuth } from '../../lib/auth/AuthProvider';

const topLinks = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/platform-users', label: 'Platform Users', icon: UsersRound, end: false },
  { to: '/security', label: 'Security', icon: ShieldCheck, end: false },
];

export function Sidebar({ collapsed, onNavigate }: { collapsed: boolean; onNavigate?: () => void }) {
  const { admin, signOut } = useAuth();

  return (
    <aside
      className={[
        'sidebar-transition h-full bg-surface-sidebar flex flex-col',
        collapsed ? 'w-[72px]' : 'w-[248px]',
      ].join(' ')}
    >
      <div className="h-14 flex items-center gap-2.5 px-4 shrink-0">
        <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center shrink-0">
          <span className="text-slate-900 font-bold text-xs leading-none">gN</span>
        </div>
        {!collapsed && <span className="text-white font-bold text-[15px] tracking-tight truncate">gNxtHire</span>}
      </div>

      <nav className="flex-1 overflow-y-auto px-2.5 py-2 space-y-0.5">
        {topLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            onClick={onNavigate}
            className={({ isActive }) =>
              [
                'flex items-center gap-3 px-3 h-9 rounded-lg text-sm font-medium transition-colors',
                isActive ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white hover:bg-white/5',
              ].join(' ')
            }
            title={collapsed ? link.label : undefined}
          >
            <link.icon size={17} className="shrink-0" />
            {!collapsed && <span className="truncate">{link.label}</span>}
          </NavLink>
        ))}

        <div className={['pt-3 mt-3 border-t border-white/10', collapsed ? 'text-center' : ''].join(' ')}>
          {!collapsed && (
            <p className="px-3 pb-1.5 text-[11px] font-bold text-slate-500 uppercase tracking-wide">Platform</p>
          )}
          {PLATFORM_MODULES.map((module) => (
            <NavLink
              key={module.slug}
              to={`/platform/${module.slug}`}
              onClick={onNavigate}
              className={({ isActive }) =>
                [
                  'flex items-center gap-3 px-3 h-9 rounded-lg text-sm font-medium transition-colors',
                  isActive ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-white hover:bg-white/5',
                ].join(' ')
              }
              title={collapsed ? module.title : undefined}
            >
              <module.icon size={17} className="shrink-0" />
              {!collapsed && <span className="truncate">{module.title}</span>}
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="p-2.5 border-t border-white/10 shrink-0">
        <div className={['flex items-center gap-2.5 px-2 py-2', collapsed ? 'justify-center' : ''].join(' ')}>
          <div className="w-8 h-8 rounded-full bg-white/10 text-white flex items-center justify-center text-xs font-bold shrink-0">
            {(admin?.display_name || admin?.email || '?').charAt(0).toUpperCase()}
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="text-sm font-semibold text-white truncate">{admin?.display_name}</p>
              <p className="text-xs text-slate-500 truncate">{admin?.email}</p>
            </div>
          )}
        </div>
        <button
          onClick={() => void signOut()}
          className={[
            'flex items-center gap-3 px-3 h-9 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-white/5 transition-colors w-full mt-1',
            collapsed ? 'justify-center' : '',
          ].join(' ')}
          title="Sign out"
        >
          <LogOut size={17} className="shrink-0" />
          {!collapsed && <span>Sign out</span>}
        </button>
      </div>
    </aside>
  );
}
