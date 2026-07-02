import { ReactNode } from 'react';
import { AlertCircle, CheckCircle2, AlertTriangle, Info, X, type LucideIcon } from 'lucide-react';

type AlertVariant = 'error' | 'success' | 'warning' | 'info';

interface AlertProps {
  variant: AlertVariant;
  title?: string;
  children: ReactNode;
  onDismiss?: () => void;
  className?: string;
}

const config: Record<AlertVariant, { bg: string; border: string; iconColor: string; textColor: string; Icon: LucideIcon }> = {
  error: { bg: 'bg-red-50', border: 'border-red-200', iconColor: 'text-red-500', textColor: 'text-red-800', Icon: AlertCircle },
  success: { bg: 'bg-emerald-50', border: 'border-emerald-200', iconColor: 'text-emerald-500', textColor: 'text-emerald-800', Icon: CheckCircle2 },
  warning: { bg: 'bg-amber-50', border: 'border-amber-200', iconColor: 'text-amber-500', textColor: 'text-amber-800', Icon: AlertTriangle },
  info: { bg: 'bg-blue-50', border: 'border-blue-200', iconColor: 'text-blue-500', textColor: 'text-blue-800', Icon: Info },
};

export function Alert({ variant, title, children, onDismiss, className = '' }: AlertProps) {
  const { bg, border, iconColor, textColor, Icon } = config[variant];
  return (
    <div
      className={['flex gap-3 p-3.5 rounded-lg border', bg, border, className].join(' ')}
      role="alert"
    >
      <Icon size={16} className={['shrink-0 mt-0.5', iconColor].join(' ')} />
      <div className="flex-1 min-w-0">
        {title && <p className={['text-sm font-semibold mb-0.5', textColor].join(' ')}>{title}</p>}
        <p className={['text-sm leading-relaxed', textColor].join(' ')}>{children}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className={['shrink-0 hover:opacity-60 transition-opacity mt-0.5', iconColor].join(' ')}
          aria-label="Dismiss alert"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}
