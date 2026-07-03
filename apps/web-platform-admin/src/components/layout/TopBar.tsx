import { Menu } from 'lucide-react';

export function TopBar({ title, subtitle, onToggleSidebar }: { title: string; subtitle?: string; onToggleSidebar: () => void }) {
  return (
    <header className="h-14 bg-white border-b border-slate-200/80 flex items-center gap-3 px-4 lg:px-6 shrink-0">
      <button
        onClick={onToggleSidebar}
        className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-500 transition-colors shrink-0"
        aria-label="Toggle navigation"
      >
        <Menu size={18} />
      </button>
      <div className="min-w-0">
        <h1 className="text-sm font-bold text-slate-900 truncate">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500 truncate">{subtitle}</p>}
      </div>
    </header>
  );
}
