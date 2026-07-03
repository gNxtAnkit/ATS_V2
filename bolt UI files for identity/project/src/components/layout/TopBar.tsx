import { useEffect, useRef, useState } from 'react';
import { ChevronDown, LogOut, Settings } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthSession } from '../../lib/auth/authSession';

interface TopBarProps {
  pageTitle: string;
}

function ProfileMenu() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const { user, realm, logout } = useAuthSession();
  const menuRef = useRef<HTMLDivElement>(null);
  const displayName = user?.display_name || user?.email || 'Account';
  const initials = displayName
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('') || 'GN';
  const securityPath = realm === 'platform' ? '/platform-admin/security/mfa/setup' : '/settings/security/mfa/setup';
  const loginPath = realm === 'platform' ? '/platform-admin/login' : '/auth/login';

  useEffect(() => {
    if (!open) return;
    const handler = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen((value) => !value)}
        className="flex items-center gap-2 h-8 pl-1.5 pr-2 rounded-lg hover:bg-slate-100 transition-colors"
        aria-expanded={open}
        aria-haspopup="true"
      >
        <div className="w-[26px] h-[26px] bg-blue-600 rounded-full flex items-center justify-center shrink-0">
          <span className="text-white text-[10px] font-bold leading-none">{initials}</span>
        </div>
        <span className="text-[13px] font-medium text-slate-700 hidden sm:block leading-none">{displayName}</span>
        <ChevronDown size={12} className={['text-slate-400 hidden sm:block transition-transform duration-150', open ? 'rotate-180' : ''].join(' ')} />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1.5 w-52 bg-white rounded-xl shadow-float border border-slate-200/80 py-1.5 z-50">
          <div className="px-4 py-2.5 border-b border-slate-100">
            <p className="text-[13px] font-semibold text-slate-900 leading-none mb-1">{displayName}</p>
            <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          </div>
          <button
            onClick={() => { setOpen(false); navigate(securityPath); }}
            className="w-full flex items-center gap-2.5 px-4 py-2 text-[13px] text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <Settings size={13} className="text-slate-400 shrink-0" />
            Security settings
          </button>
          <div className="border-t border-slate-100 pt-1">
            <button
              onClick={() => {
                setOpen(false);
                void logout().then(() => navigate(loginPath, { replace: true }));
              }}
              className="w-full flex items-center gap-2.5 px-4 py-2 text-[13px] text-red-600 hover:bg-red-50 transition-colors"
            >
              <LogOut size={13} className="shrink-0" />
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export function TopBar({ pageTitle }: TopBarProps) {
  return (
    <header className="h-14 bg-white border-b border-slate-200/80 flex items-center gap-3 px-4 sm:px-5 shrink-0 z-10">
      <div className="flex-1 min-w-0">
        <h1 className="text-[15px] font-bold text-slate-900 truncate leading-none">{pageTitle}</h1>
      </div>
      <ProfileMenu />
    </header>
  );
}
