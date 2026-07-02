import { useState, useRef, useEffect } from 'react';
import { Bell, Search, X, ChevronDown, LogOut, Settings, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthSession } from '../../lib/auth/authSession';

interface TopBarProps {
  pageTitle: string;
}

function SearchBar() {
  const [focused, setFocused] = useState(false);
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="relative hidden sm:block">
      <div
        className={[
          'flex items-center gap-2 h-[34px] rounded-lg border transition-all duration-200 overflow-hidden',
          focused
            ? 'border-blue-400/70 bg-white ring-2 ring-blue-500/10 w-64'
            : 'border-slate-200 bg-slate-50 w-52 hover:border-slate-300 hover:bg-white/80',
        ].join(' ')}
      >
        <Search size={13} className="text-slate-400 ml-3 shrink-0" />
        <input
          ref={inputRef}
          type="search"
          placeholder="Search candidates, jobs…"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className="flex-1 text-[13px] text-slate-700 bg-transparent outline-none placeholder:text-slate-400 min-w-0 pr-2"
        />
        {value && (
          <button
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => { setValue(''); inputRef.current?.focus(); }}
            className="pr-2 text-slate-400 hover:text-slate-600 shrink-0"
          >
            <X size={12} />
          </button>
        )}
      </div>
    </div>
  );
}

function NotificationButton() {
  return (
    <button
      className="relative w-8 h-8 flex items-center justify-center rounded-lg hover:bg-slate-100 transition-colors text-slate-500 hover:text-slate-700"
      aria-label="Notifications"
    >
      <Bell size={16} />
      <span className="absolute top-1.5 right-1.5 w-[7px] h-[7px] bg-blue-500 rounded-full border-[1.5px] border-white" />
    </button>
  );
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

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 h-8 pl-1.5 pr-2 rounded-lg hover:bg-slate-100 transition-colors"
        aria-expanded={open}
        aria-haspopup="true"
      >
        <div className="w-[26px] h-[26px] bg-blue-600 rounded-full flex items-center justify-center shrink-0">
          <span className="text-white text-[10px] font-bold leading-none">{initials}</span>
        </div>
        <span className="text-[13px] font-medium text-slate-700 hidden sm:block leading-none">
          {displayName}
        </span>
        <ChevronDown
          size={12}
          className={[
            'text-slate-400 hidden sm:block transition-transform duration-150',
            open ? 'rotate-180' : '',
          ].join(' ')}
        />
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1.5 w-52 bg-white rounded-xl shadow-float border border-slate-200/80 py-1.5 z-50">
          <div className="px-4 py-2.5 border-b border-slate-100">
            <p className="text-[13px] font-semibold text-slate-900 leading-none mb-1">{displayName}</p>
            <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          </div>
          <div className="py-1">
            <button
              onClick={() => setOpen(false)}
              className="w-full flex items-center gap-2.5 px-4 py-2 text-[13px] text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <User size={13} className="text-slate-400 shrink-0" />
              Your profile
            </button>
            <button
              onClick={() => { setOpen(false); navigate(realm === 'platform' ? '/platform-admin/security/mfa/setup' : '/settings/security/mfa/setup'); }}
              className="w-full flex items-center gap-2.5 px-4 py-2 text-[13px] text-slate-700 hover:bg-slate-50 transition-colors"
            >
              <Settings size={13} className="text-slate-400 shrink-0" />
              Security settings
            </button>
          </div>
          <div className="border-t border-slate-100 pt-1">
            <button
              onClick={() => {
                setOpen(false);
                void logout().then(() => navigate(realm === 'platform' ? '/platform-admin/login' : '/auth/login', { replace: true }));
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
      <div className="flex items-center gap-1">
        <SearchBar />
        <NotificationButton />
        <div className="w-px h-4 bg-slate-200 mx-1 hidden sm:block" />
        <ProfileMenu />
      </div>
    </header>
  );
}
