import { LayoutDashboard, Settings, type LucideIcon } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuthSession } from '../../lib/auth/authSession';

interface Tab {
  label: string;
  icon: LucideIcon;
  path: string;
}

export function MobileBottomTabs() {
  const location = useLocation();
  const navigate = useNavigate();
  const { realm } = useAuthSession();
  const tabs: Tab[] = realm === 'platform'
    ? [
        { label: 'Console', icon: LayoutDashboard, path: '/platform-admin/dashboard' },
        { label: 'Security', icon: Settings, path: '/platform-admin/security/mfa/setup' },
      ]
    : [
        { label: 'Home', icon: LayoutDashboard, path: '/dashboard' },
        { label: 'Security', icon: Settings, path: '/settings/security/mfa/setup' },
      ];

  return (
    <nav
      className="md:hidden fixed bottom-0 inset-x-0 bg-white/95 backdrop-blur-sm border-t border-slate-200 z-30"
      style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
    >
      <div className="flex h-16">
        {tabs.map((tab) => {
          const active = location.pathname === tab.path || location.pathname.startsWith(tab.path + '/');
          return (
            <button
              key={tab.path}
              onClick={() => navigate(tab.path)}
              className={[
                'flex-1 flex flex-col items-center justify-center gap-[3px] relative transition-colors',
                active ? 'text-blue-600' : 'text-slate-500 active:text-slate-700',
              ].join(' ')}
            >
              {active && <span className="absolute top-0 inset-x-1/4 h-[2px] bg-blue-600 rounded-b-full" />}
              <tab.icon size={21} strokeWidth={active ? 2.5 : 2} />
              <span className="text-[10px] font-medium leading-none">{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
