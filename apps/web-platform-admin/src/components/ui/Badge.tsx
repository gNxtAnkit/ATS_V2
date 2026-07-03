import { toneForStatus } from '../../theme';

export function StatusBadge({ status }: { status: string | null | undefined }) {
  if (!status) return <span className="text-slate-400 text-xs">—</span>;
  return (
    <span
      className={[
        'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border capitalize',
        toneForStatus(status),
      ].join(' ')}
    >
      {status.replace(/_/g, ' ')}
    </span>
  );
}

export function Badge({ children, tone = 'neutral' }: { children: React.ReactNode; tone?: 'neutral' | 'brand' }) {
  return (
    <span
      className={[
        'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border',
        tone === 'brand' ? 'bg-slate-800 text-white border-slate-800' : 'bg-slate-100 text-slate-600 border-slate-200',
      ].join(' ')}
    >
      {children}
    </span>
  );
}
