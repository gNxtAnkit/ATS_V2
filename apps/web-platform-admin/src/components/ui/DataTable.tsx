import { ReactNode } from 'react';
import { StatusBadge } from './Badge';
import { TableSkeleton } from './Skeleton';
import { EmptyState } from './EmptyState';

export type JsonRecord = Record<string, unknown>;

export interface ColumnDef {
  key: string;
  label: string;
  render?: (value: unknown, row: JsonRecord) => ReactNode;
}

const STATUS_LIKE_KEYS = new Set(['status', 'verification_status']);

function defaultCellValue(value: unknown): ReactNode {
  if (value === null || value === undefined || value === '') return <span className="text-slate-300">—</span>;
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'object') return <span className="text-slate-400 font-mono text-xs">{JSON.stringify(value)}</span>;
  return String(value);
}

function humanizeHeader(key: string): string {
  return key.split('_').join(' ');
}

export function inferColumns(rows: JsonRecord[]): ColumnDef[] {
  const preferred = ['name', 'display_name', 'email', 'code', 'title', 'subject', 'framework', 'flag_key', 'version_label', 'policy_key', 'slo_key', 'quota_key', 'feature_key', 'role_key', 'permission_key', 'pool_key', 'status', 'priority', 'created_at'];
  const available = new Set(rows.flatMap((row) => Object.keys(row)));
  const selected = preferred.filter((key) => available.has(key));
  const keys = selected.length >= 3 ? selected.slice(0, 6) : Array.from(available).slice(0, 6);
  return keys.map((key) => ({
    key,
    label: humanizeHeader(key),
    render: STATUS_LIKE_KEYS.has(key) ? (value) => <StatusBadge status={typeof value === 'string' ? value : null} /> : undefined,
  }));
}

export function DataTable({
  rows,
  columns,
  selectedId,
  onSelect,
  loading,
  emptyTitle = 'No records found',
  emptyDescription = 'Try adjusting your search or filters.',
}: {
  rows: JsonRecord[];
  columns: ColumnDef[];
  selectedId: string | null;
  onSelect: (record: JsonRecord) => void;
  loading?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
}) {
  if (loading) return <TableSkeleton />;
  if (rows.length === 0) return <EmptyState title={emptyTitle} description={emptyDescription} />;

  return (
    <div className="overflow-auto max-h-[560px] rounded-xl border border-slate-200">
      <table className="min-w-full border-collapse">
        <thead className="sticky top-0 z-10">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className="bg-slate-50 text-left text-xs font-bold text-slate-500 uppercase tracking-wide px-3.5 py-2.5 border-b border-slate-200 whitespace-nowrap"
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => {
            const id = typeof row.id === 'string' ? row.id : `${index}`;
            const isSelected = selectedId === id;
            return (
              <tr
                key={id}
                onClick={() => onSelect(row)}
                className={[
                  'cursor-pointer transition-colors border-b border-slate-100 last:border-0',
                  isSelected ? 'bg-slate-100' : 'hover:bg-slate-50',
                ].join(' ')}
              >
                {columns.map((column) => (
                  <td key={column.key} className="px-3.5 py-2.5 text-sm text-slate-700 max-w-[220px] truncate">
                    {column.render ? column.render(row[column.key], row) : defaultCellValue(row[column.key])}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
