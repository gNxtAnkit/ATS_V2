import { StatusBadge } from './Badge';

type JsonRecord = Record<string, unknown>;

const STATUS_LIKE_KEYS = new Set(['status', 'verification_status']);
const HIDDEN_KEYS = new Set(['password_hash']);

function humanizeLabel(key: string): string {
  return key
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatValue(key: string, value: unknown): string {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (key.endsWith('_at') && typeof value === 'string') {
    const parsed = new Date(value);
    if (!Number.isNaN(parsed.getTime())) return parsed.toLocaleString();
  }
  if (typeof value === 'object') return JSON.stringify(value, null, 2);
  return String(value);
}

/**
 * Renders an arbitrary record (tenant, plan, ticket, audit log, ...) as a
 * readable key/value grid instead of a raw JSON dump. Nested objects/arrays
 * are shown as formatted JSON blocks (still readable, still bounded) rather
 * than a wall of unindented text.
 */
export function RecordDetail({ record }: { record: JsonRecord | null }) {
  if (!record) return null;
  const entries = Object.entries(record).filter(([key]) => !HIDDEN_KEYS.has(key));

  return (
    <dl className="divide-y divide-slate-100">
      {entries.map(([key, value]) => {
        const isComplex = value !== null && typeof value === 'object';
        return (
          <div key={key} className="py-2.5 grid grid-cols-[minmax(120px,0.9fr)_1.4fr] gap-3 items-start">
            <dt className="text-xs font-semibold text-slate-500 uppercase tracking-wide pt-0.5">{humanizeLabel(key)}</dt>
            <dd className="text-sm text-slate-800 min-w-0">
              {STATUS_LIKE_KEYS.has(key) && typeof value === 'string' ? (
                <StatusBadge status={value} />
              ) : isComplex ? (
                <pre className="text-xs bg-slate-50 border border-slate-100 rounded-lg p-2.5 overflow-auto whitespace-pre-wrap break-words">
                  {formatValue(key, value)}
                </pre>
              ) : (
                <span className="break-words">{formatValue(key, value)}</span>
              )}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}
