import { AlertTriangle } from 'lucide-react';
import { Button } from './Button';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  description?: string;
  confirmLabel?: string;
  destructive?: boolean;
  busy?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  destructive = false,
  busy = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-[1px]" onClick={busy ? undefined : onCancel} />
      <div className="relative bg-white rounded-2xl shadow-float border border-slate-200 w-full max-w-sm p-6">
        <div className="flex items-start gap-3 mb-4">
          <div
            className={[
              'w-10 h-10 rounded-xl flex items-center justify-center shrink-0',
              destructive ? 'bg-red-50' : 'bg-amber-50',
            ].join(' ')}
          >
            <AlertTriangle size={20} className={destructive ? 'text-red-600' : 'text-amber-600'} />
          </div>
          <div>
            <h3 className="text-[15px] font-bold text-slate-900 leading-tight">{title}</h3>
            {description && <p className="text-sm text-slate-500 mt-1 leading-relaxed">{description}</p>}
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <Button variant="secondary" size="sm" onClick={onCancel} disabled={busy}>
            Cancel
          </Button>
          <Button variant={destructive ? 'danger' : 'primary'} size="sm" onClick={onConfirm} loading={busy}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
