// Centralized theme layer.
// Colors, radii, and shadows themselves live in src/styles.css as CSS variables
// (see :root) and are exposed to Tailwind via tailwind.config.js (colors.brand,
// colors.surface, boxShadow.card/float/auth). This file centralizes the
// *component-level* class combinations built on top of those tokens so
// spacing/typography/interaction patterns stay consistent across the app
// without being re-typed on every screen. Change brand look-and-feel by
// editing the CSS variables in styles.css; change component composition by
// editing the strings below.
export const ui = {
  focusRing: 'focus:outline-none focus:ring-2 focus:ring-slate-500/20 focus:border-slate-500',
  checkbox: 'w-4 h-4 rounded border-slate-300 text-slate-700 focus:ring-slate-500/30 cursor-pointer',
  appSurface: 'bg-[#F0F3FA]',
  card: 'bg-white rounded-2xl border border-slate-200 shadow-card',
  compactCard: 'bg-white rounded-xl border border-slate-200/80 shadow-sm',
  mutedPanel: 'bg-slate-50 rounded-xl border border-slate-100',
  selectedSidebarItem: 'bg-white/10 text-white',
  topBar: 'h-14 bg-white border-b border-slate-200/80',
  pageHeading: 'text-[20px] font-bold text-slate-900 leading-tight',
  pageSubheading: 'text-sm text-slate-500 mt-1',
} as const;

export const statusToneClasses: Record<string, string> = {
  active: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  trial: 'bg-blue-50 text-blue-700 border-blue-200',
  trialing: 'bg-blue-50 text-blue-700 border-blue-200',
  provisioning: 'bg-blue-50 text-blue-700 border-blue-200',
  pending: 'bg-blue-50 text-blue-700 border-blue-200',
  invited: 'bg-blue-50 text-blue-700 border-blue-200',
  running: 'bg-blue-50 text-blue-700 border-blue-200',
  open: 'bg-blue-50 text-blue-700 border-blue-200',
  acknowledged: 'bg-amber-50 text-amber-700 border-amber-200',
  in_progress: 'bg-amber-50 text-amber-700 border-amber-200',
  waiting_on_customer: 'bg-amber-50 text-amber-700 border-amber-200',
  warning: 'bg-amber-50 text-amber-700 border-amber-200',
  suspended: 'bg-red-50 text-red-700 border-red-200',
  locked: 'bg-red-50 text-red-700 border-red-200',
  failed: 'bg-red-50 text-red-700 border-red-200',
  partial_failure: 'bg-red-50 text-red-700 border-red-200',
  breached: 'bg-red-50 text-red-700 border-red-200',
  critical: 'bg-red-50 text-red-700 border-red-200',
  churned: 'bg-slate-100 text-slate-600 border-slate-200',
  deleted: 'bg-slate-100 text-slate-600 border-slate-200',
  pending_deletion: 'bg-slate-100 text-slate-600 border-slate-200',
  archived: 'bg-slate-100 text-slate-600 border-slate-200',
  retired: 'bg-slate-100 text-slate-600 border-slate-200',
  skipped: 'bg-slate-100 text-slate-600 border-slate-200',
  draft: 'bg-slate-100 text-slate-600 border-slate-200',
  closed: 'bg-slate-100 text-slate-600 border-slate-200',
  resolved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  completed: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  verified: 'bg-emerald-50 text-emerald-700 border-emerald-200',
};

export function toneForStatus(status: string | null | undefined): string {
  if (!status) return 'bg-slate-100 text-slate-600 border-slate-200';
  return statusToneClasses[status.toLowerCase()] ?? 'bg-slate-100 text-slate-600 border-slate-200';
}
