import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Briefcase,
  Users,
  GitBranch,
  Inbox,
  MoreHorizontal,
  BarChart2,
  Settings,
  HelpCircle,
  type LucideIcon,
} from 'lucide-react';

interface Tab {
  label: string;
  icon: LucideIcon;
  path: string;
  badge?: number;
}

const primaryTabs: Tab[] = [
  { label: 'Home', icon: LayoutDashboard, path: '/dashboard' },
  { label: 'Jobs', icon: Briefcase, path: '/jobs' },
  { label: 'Candidates', icon: Users, path: '/candidates' },
  { label: 'Pipeline', icon: GitBranch, path: '/pipeline' },
  { label: 'Inbox', icon: Inbox, path: '/inbox', badge: 3 },
];

const moreTabs: Tab[] = [
  { label: 'Reports', icon: BarChart2, path: '/reports' },
  { label: 'Settings', icon: Settings, path: '/settings/security/mfa/setup' },
  { label: 'Help', icon: HelpCircle, path: '/help' },
];

export function MobileBottomTabs() {
  const location = useLocation();
  const navigate = useNavigate();
  const [moreOpen, setMoreOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  return (
    <>
      {/* Bottom nav bar */}
      <nav
        className="md:hidden fixed bottom-0 inset-x-0 bg-white/95 backdrop-blur-sm border-t border-slate-200 z-30"
        style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
      >
        <div className="flex h-16">
          {primaryTabs.map((tab) => {
            const active = isActive(tab.path);
            return (
              <button
                key={tab.path}
                onClick={() => { setMoreOpen(false); navigate(tab.path); }}
                className={[
                  'flex-1 flex flex-col items-center justify-center gap-[3px] relative transition-colors',
                  active ? 'text-blue-600' : 'text-slate-500 active:text-slate-700',
                ].join(' ')}
              >
                {active && (
                  <span className="absolute top-0 inset-x-1/4 h-[2px] bg-blue-600 rounded-b-full" />
                )}
                <div className="relative">
                  <tab.icon
                    size={21}
                    strokeWidth={active ? 2.5 : 2}
                    className="transition-transform active:scale-95"
                  />
                  {tab.badge ? (
                    <span className="absolute -top-1 -right-1.5 min-w-[16px] h-4 bg-blue-500 rounded-full text-[9px] font-bold text-white flex items-center justify-center px-0.5">
                      {tab.badge}
                    </span>
                  ) : null}
                </div>
                <span className="text-[10px] font-medium leading-none">{tab.label}</span>
              </button>
            );
          })}

          {/* More button */}
          <button
            onClick={() => setMoreOpen((v) => !v)}
            className={[
              'flex-1 flex flex-col items-center justify-center gap-[3px] transition-colors',
              moreOpen ? 'text-blue-600' : 'text-slate-500',
            ].join(' ')}
          >
            <MoreHorizontal size={21} strokeWidth={2} />
            <span className="text-[10px] font-medium leading-none">More</span>
          </button>
        </div>
      </nav>

      {/* More sheet */}
      {moreOpen && (
        <>
          <div
            className="md:hidden fixed inset-0 z-40 bg-black/25"
            onClick={() => setMoreOpen(false)}
          />
          <div
            className="md:hidden fixed inset-x-3 z-50 bg-white rounded-2xl shadow-float border border-slate-200 p-4"
            style={{ bottom: 'calc(4.5rem + env(safe-area-inset-bottom, 0px) + 8px)' }}
          >
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-widest mb-3 px-1">
              More
            </p>
            <div className="grid grid-cols-3 gap-2">
              {moreTabs.map((item) => {
                const active = isActive(item.path);
                return (
                  <button
                    key={item.path}
                    onClick={() => { navigate(item.path); setMoreOpen(false); }}
                    className={[
                      'flex flex-col items-center gap-2 p-3.5 rounded-xl transition-colors',
                      active
                        ? 'bg-blue-50 text-blue-700'
                        : 'bg-slate-50 text-slate-700 hover:bg-slate-100',
                    ].join(' ')}
                  >
                    <item.icon size={20} className={active ? 'text-blue-600' : 'text-slate-500'} />
                    <span className="text-xs font-medium leading-none">{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </>
  );
}
