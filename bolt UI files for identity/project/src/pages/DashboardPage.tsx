import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { useAuthSession } from '../lib/auth/authSession';
import {
  Briefcase,
  Users,
  Calendar,
  TrendingUp,
  Sparkles,
  ArrowRight,
  Clock,
  CheckCircle2,
  GitBranch,
  ArrowUpRight,
  ShieldCheck,
  Inbox,
} from 'lucide-react';

/* ─── data ─── */
const stats = [
  { label: 'Open Roles', value: '12', delta: '+2', positive: true, icon: Briefcase, iconCls: 'bg-blue-500/10 text-blue-600' },
  { label: 'Active Candidates', value: '248', delta: '+34', positive: true, icon: Users, iconCls: 'bg-indigo-500/10 text-indigo-600' },
  { label: 'Interviews This Week', value: '18', delta: '3 today', positive: true, icon: Calendar, iconCls: 'bg-cyan-500/10 text-cyan-600' },
  { label: 'Avg. Time to Hire', value: '21d', delta: '↓ 2d', positive: true, icon: TrendingUp, iconCls: 'bg-emerald-500/10 text-emerald-600' },
];

const pipeline = [
  { stage: 'Applied', count: 124, pct: 100, color: 'bg-blue-500' },
  { stage: 'AI Screened', count: 89, pct: 72, color: 'bg-indigo-500' },
  { stage: 'Phone Screen', count: 45, pct: 36, color: 'bg-cyan-500' },
  { stage: 'Interview', count: 23, pct: 19, color: 'bg-violet-500' },
  { stage: 'Offer', count: 6, pct: 5, color: 'bg-emerald-500' },
];

const interviews = [
  { time: '9:00 AM', name: 'Sarah Kim', role: 'Senior Engineer', type: 'Technical', dot: 'bg-emerald-400' },
  { time: '11:30 AM', name: 'David L.', role: 'Backend Engineer', type: 'Culture Fit', dot: 'bg-blue-400' },
  { time: '2:30 PM', name: 'Marcus B.', role: 'Design Lead', type: 'Portfolio', dot: 'bg-amber-400' },
];

const activity = [
  { icon: GitBranch, bg: 'bg-blue-50', color: 'text-blue-500', text: 'Sarah Kim advanced to Interview stage for Senior Engineer', time: '5m ago' },
  { icon: CheckCircle2, bg: 'bg-emerald-50', color: 'text-emerald-500', text: 'Offer letter sent to Marcus B. for Design Lead position', time: '1h ago' },
  { icon: Briefcase, bg: 'bg-slate-50', color: 'text-slate-500', text: 'New requisition opened: Product Manager, Growth', time: '2h ago' },
  { icon: Calendar, bg: 'bg-indigo-50', color: 'text-indigo-500', text: 'Interview completed: David L. — Backend Engineer (5/5)', time: '3h ago' },
  { icon: Sparkles, bg: 'bg-violet-50', color: 'text-violet-500', text: 'AI screened 47 new applicants for Software Engineer role', time: '4h ago' },
  { icon: Inbox, bg: 'bg-amber-50', color: 'text-amber-500', text: 'Offer accepted: Priya R. — Product Designer', time: '6h ago' },
];

const aiInsights = [
  '7 candidates match Senior Engineer at 90%+ fit score',
  '3 in-progress offers pending response — follow-up recommended',
  'Interview-to-offer rate improved 12% vs last quarter',
];

/* ─── components ─── */
function Card({ className = '', children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={['bg-white rounded-xl border border-slate-200/80 shadow-sm', className].join(' ')}>
      {children}
    </div>
  );
}

function SectionHeader({
  title,
  sub,
  action,
  onAction,
}: {
  title: string;
  sub?: string;
  action?: string;
  onAction?: () => void;
}) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h3 className="text-[13px] font-bold text-slate-900 leading-none">{title}</h3>
        {sub && <p className="text-[11px] text-slate-500 mt-1">{sub}</p>}
      </div>
      {action && (
        <button
          onClick={onAction}
          className="flex items-center gap-0.5 text-[12px] text-blue-600 hover:text-blue-700 font-semibold transition-colors shrink-0 ml-4"
        >
          {action} <ArrowUpRight size={12} />
        </button>
      )}
    </div>
  );
}

export function DashboardPage() {
  const navigate = useNavigate();
  const { user, realm } = useAuthSession();
  const displayName = user?.display_name || user?.email || 'there';
  const mfaSetupPath = realm === 'platform' ? '/platform-admin/security/mfa/setup' : '/settings/security/mfa/setup';
  const pageTitle = realm === 'platform' ? 'Platform console' : 'Dashboard';

  return (
    <AppShell pageTitle={pageTitle}>
      {/* ── Welcome row ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5">
        <div>
          <p className="text-[17px] font-bold text-slate-900 leading-tight">Good morning, {displayName}</p>
          <p className="text-sm text-slate-500 mt-0.5">
            3 interviews scheduled today &nbsp;·&nbsp; 12 candidates pending review
          </p>
        </div>
        <button
          onClick={() => navigate(mfaSetupPath)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-[13px] font-semibold rounded-lg px-4 py-2.5 transition-colors shrink-0 shadow-sm"
        >
          <ShieldCheck size={14} />
          Enable MFA
          <ArrowRight size={13} />
        </button>
      </div>

      {/* ── Stats grid ── */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3 mb-5">
        {stats.map((s) => (
          <Card key={s.label} className="p-4 hover:shadow-md transition-shadow duration-200">
            <div className="flex items-center justify-between mb-3">
              <div className={['w-8 h-8 rounded-lg flex items-center justify-center', s.iconCls].join(' ')}>
                <s.icon size={15} />
              </div>
              <span
                className={[
                  'text-[11px] font-semibold px-1.5 py-0.5 rounded-full',
                  s.positive
                    ? 'text-emerald-700 bg-emerald-50'
                    : 'text-slate-500 bg-slate-100',
                ].join(' ')}
              >
                {s.delta}
              </span>
            </div>
            <p className="text-[22px] font-bold text-slate-900 tracking-tight leading-none mb-1">
              {s.value}
            </p>
            <p className="text-[11px] text-slate-500 font-medium leading-none">{s.label}</p>
          </Card>
        ))}
      </div>

      {/* ── Middle row: Pipeline + Interviews ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        {/* Pipeline */}
        <Card className="lg:col-span-2 p-5">
          <SectionHeader title="Hiring Pipeline" sub="All open roles combined" action="View all" />
          <div className="space-y-3">
            {pipeline.map((s) => (
              <div key={s.stage} className="flex items-center gap-3 group">
                <span className="text-[12px] text-slate-600 font-medium w-[90px] shrink-0 truncate">
                  {s.stage}
                </span>
                <div className="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={['h-full rounded-full transition-all duration-500', s.color].join(' ')}
                    style={{ width: `${s.pct}%` }}
                  />
                </div>
                <span className="text-[12px] font-bold text-slate-700 w-7 text-right tabular-nums shrink-0">
                  {s.count}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-3.5 border-t border-slate-100 flex items-center gap-2">
            <div className="w-5 h-5 bg-violet-100 rounded-md flex items-center justify-center shrink-0">
              <Sparkles size={11} className="text-violet-600" />
            </div>
            <p className="text-[12px] text-slate-600">
              <span className="font-semibold text-violet-700">AI insight:</span>{' '}
              7 candidates ready for offer stage across 3 roles
            </p>
          </div>
        </Card>

        {/* Interviews today */}
        <Card className="p-5">
          <SectionHeader title="Today's Interviews" sub="3 scheduled" action="Calendar" />
          <div className="space-y-2.5">
            {interviews.map((iv) => (
              <div
                key={iv.name}
                className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-100 hover:bg-slate-100/60 transition-colors cursor-pointer group"
              >
                <div className={['w-2 h-2 rounded-full shrink-0', iv.dot].join(' ')} />
                <div className="min-w-0 flex-1">
                  <p className="text-[12px] font-semibold text-slate-800 leading-none truncate">
                    {iv.name}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5 truncate">
                    {iv.role} · {iv.type}
                  </p>
                </div>
                <span className="text-[11px] text-slate-400 font-medium shrink-0 tabular-nums">
                  {iv.time}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* ── Bottom row: Activity + AI ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Recent Activity */}
        <Card className="lg:col-span-2 p-5">
          <SectionHeader title="Recent Activity" action="View all" />
          <div className="divide-y divide-slate-100">
            {activity.map((item, i) => (
              <div key={i} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
                <div
                  className={[
                    'w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5',
                    item.bg,
                  ].join(' ')}
                >
                  <item.icon size={13} className={item.color} />
                </div>
                <p className="flex-1 text-[12px] text-slate-700 leading-relaxed">{item.text}</p>
                <div className="flex items-center gap-1 shrink-0 mt-0.5 ml-2">
                  <Clock size={10} className="text-slate-300" />
                  <span className="text-[11px] text-slate-400 tabular-nums">{item.time}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* AI Insights */}
        <Card className="p-5 flex flex-col">
          <div className="flex items-center gap-2.5 mb-4">
            <div className="w-7 h-7 bg-violet-100 rounded-lg flex items-center justify-center shrink-0">
              <Sparkles size={13} className="text-violet-600" />
            </div>
            <div>
              <h3 className="text-[13px] font-bold text-slate-900 leading-none">AI Insights</h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Updated just now</p>
            </div>
          </div>

          <div className="space-y-2 flex-1">
            {aiInsights.map((insight, i) => (
              <div
                key={i}
                className="flex items-start gap-2.5 p-3 bg-violet-50/60 rounded-lg border border-violet-100/80"
              >
                <div className="w-1 h-1 bg-violet-400 rounded-full mt-[5px] shrink-0" />
                <p className="text-[12px] text-violet-900 leading-relaxed">{insight}</p>
              </div>
            ))}
          </div>

          <button className="w-full mt-4 text-[12px] text-violet-700 hover:text-violet-800 font-semibold flex items-center justify-center gap-1.5 py-2.5 bg-violet-50 hover:bg-violet-100 rounded-lg border border-violet-100 transition-colors">
            All AI recommendations <ArrowRight size={12} />
          </button>
        </Card>
      </div>
    </AppShell>
  );
}
