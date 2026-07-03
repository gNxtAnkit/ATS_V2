import { ReactNode } from 'react';

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={['bg-white rounded-2xl border border-slate-200 shadow-card', className].join(' ')}>{children}</div>;
}

export function CardHeader({
  icon: Icon,
  title,
  subtitle,
  action,
}: {
  icon?: React.ComponentType<{ size?: number; className?: string }>;
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 p-5 border-b border-slate-100">
      <div className="flex items-start gap-3 min-w-0">
        {Icon && (
          <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center shrink-0 mt-0.5">
            <Icon size={18} className="text-slate-600" />
          </div>
        )}
        <div className="min-w-0">
          <h2 className="text-[15px] font-bold text-slate-900 leading-tight truncate">{title}</h2>
          {subtitle && <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{subtitle}</p>}
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

export function CardBody({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={['p-5', className].join(' ')}>{children}</div>;
}
