import { Sparkles, Calendar, Shield, Zap, GitBranch, Brain, Users, Activity, Server, Lock } from 'lucide-react';

interface AuthBrandPanelProps {
  variant?: 'tenant' | 'platform';
}

function TenantPanel() {
  return (
    <>
      <div className="mb-10">
        <h2 className="text-[28px] font-bold text-white leading-tight mb-3">
          AI-native hiring operations for modern teams.
        </h2>
        <p className="text-blue-200 text-sm leading-relaxed">
          Screen candidates faster, coordinate interviews, automate follow-ups, and keep every
          hiring workflow governed.
        </p>
      </div>

      {/* Pipeline Preview Card */}
      <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-5 mb-3 border border-white/15">
        <div className="flex items-center justify-between mb-4">
          <span className="text-white text-sm font-semibold">Hiring Pipeline</span>
          <div className="flex items-center gap-1.5 bg-violet-600/40 border border-violet-400/30 rounded-full px-2.5 py-1">
            <Sparkles className="w-3 h-3 text-violet-200" />
            <span className="text-violet-100 text-xs font-medium">AI Active</span>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-2.5">
          {[
            { stage: 'Applied', count: 124, fill: 100, barColor: 'bg-blue-400' },
            { stage: 'Screening', count: 67, fill: 54, barColor: 'bg-indigo-400' },
            { stage: 'Interview', count: 23, fill: 19, barColor: 'bg-violet-400' },
          ].map((s) => (
            <div key={s.stage} className="bg-white/10 rounded-xl p-3">
              <p className="text-blue-200 text-[11px] mb-0.5">{s.stage}</p>
              <p className="text-white text-xl font-bold">{s.count}</p>
              <div className="mt-2 h-1 bg-white/10 rounded-full overflow-hidden">
                <div className={['h-full rounded-full', s.barColor].join(' ')} style={{ width: `${s.fill}%` }} />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-3 flex items-center gap-2 bg-violet-600/20 rounded-xl px-3 py-2 border border-violet-400/20">
          <Brain className="w-3.5 h-3.5 text-violet-300 shrink-0" />
          <span className="text-xs text-violet-200">7 candidates ready for offer — AI recommendation</span>
        </div>
      </div>

      {/* Interview Mini Card */}
      <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 mb-6 border border-white/15">
        <div className="flex items-center gap-2 mb-3">
          <Calendar className="w-3.5 h-3.5 text-blue-300" />
          <span className="text-white text-sm font-semibold">Today's Interviews</span>
          <span className="ml-auto text-xs text-blue-300 bg-blue-500/20 rounded-full px-2 py-0.5">2 scheduled</span>
        </div>
        <div className="space-y-2.5">
          {[
            { time: '9:00 AM', name: 'Sarah Kim', role: 'Senior Engineer', dot: 'bg-emerald-400' },
            { time: '2:30 PM', name: 'Marcus B.', role: 'Design Lead', dot: 'bg-blue-400' },
          ].map((item) => (
            <div key={item.name} className="flex items-center gap-2.5">
              <div className={['w-2 h-2 rounded-full shrink-0', item.dot].join(' ')} />
              <span className="text-blue-300 text-xs w-16 shrink-0 font-medium">{item.time}</span>
              <span className="text-white text-xs font-medium flex-1 truncate">{item.name}</span>
              <span className="text-blue-300 text-xs shrink-0">{item.role}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Feature chips */}
      <div className="mt-auto flex flex-wrap gap-2">
        {[
          { label: 'AI Screening', icon: Brain },
          { label: 'Smart Scheduling', icon: Calendar },
          { label: 'Pipeline Automation', icon: GitBranch },
          { label: 'Enterprise Security', icon: Shield },
          { label: 'Workflow Approvals', icon: Zap },
          { label: 'Candidate Insights', icon: Users },
        ].map((chip) => (
          <div
            key={chip.label}
            className="flex items-center gap-1.5 bg-white/10 border border-white/10 rounded-full px-3 py-1.5"
          >
            <chip.icon className="w-3 h-3 text-blue-300" />
            <span className="text-blue-100 text-xs">{chip.label}</span>
          </div>
        ))}
      </div>
    </>
  );
}

function PlatformPanel() {
  return (
    <>
      <div className="mb-10">
        <h2 className="text-[28px] font-bold text-white leading-tight mb-3">
          Platform operations centre for gNxtHire.
        </h2>
        <p className="text-blue-200 text-sm leading-relaxed">
          Manage tenants, monitor system health, govern AI usage, and oversee security events from
          one centralised admin console.
        </p>
      </div>

      {/* Tenant Health Card */}
      <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-5 mb-3 border border-white/15">
        <div className="flex items-center justify-between mb-4">
          <span className="text-white text-sm font-semibold">Tenant Console</span>
          <span className="text-xs text-emerald-300 bg-emerald-500/20 border border-emerald-400/20 rounded-full px-2.5 py-1">
            All systems nominal
          </span>
        </div>
        <div className="grid grid-cols-3 gap-2.5">
          {[
            { label: 'Active Tenants', value: '142', barColor: 'bg-blue-400', fill: 85 },
            { label: 'Platform Users', value: '6.2k', barColor: 'bg-indigo-400', fill: 62 },
            { label: 'Uptime', value: '99.9%', barColor: 'bg-emerald-400', fill: 100 },
          ].map((s) => (
            <div key={s.label} className="bg-white/10 rounded-xl p-3">
              <p className="text-blue-200 text-[11px] mb-0.5">{s.label}</p>
              <p className="text-white text-xl font-bold">{s.value}</p>
              <div className="mt-2 h-1 bg-white/10 rounded-full overflow-hidden">
                <div className={['h-full rounded-full', s.barColor].join(' ')} style={{ width: `${s.fill}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Security Events mini card */}
      <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 mb-6 border border-white/15">
        <div className="flex items-center gap-2 mb-3">
          <Shield className="w-3.5 h-3.5 text-blue-300" />
          <span className="text-white text-sm font-semibold">Security Events</span>
          <span className="ml-auto text-xs text-amber-300 bg-amber-500/20 rounded-full px-2 py-0.5">3 flagged</span>
        </div>
        <div className="space-y-2.5">
          {[
            { icon: Lock, label: 'Failed MFA attempts', value: '12 today', color: 'text-amber-300' },
            { icon: Activity, label: 'API rate limit warnings', value: '2 tenants', color: 'text-blue-300' },
            { icon: Server, label: 'Infra health', value: 'All green', color: 'text-emerald-300' },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-2.5">
              <item.icon className={['w-3 h-3 shrink-0', item.color].join(' ')} />
              <span className="text-blue-200 text-xs flex-1">{item.label}</span>
              <span className={['text-xs font-medium shrink-0', item.color].join(' ')}>{item.value}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-auto flex flex-wrap gap-2">
        {[
          { label: 'Tenant Management', icon: Users },
          { label: 'AI Governance', icon: Brain },
          { label: 'Security Events', icon: Shield },
          { label: 'Feature Flags', icon: Zap },
          { label: 'System Health', icon: Activity },
          { label: 'Compliance', icon: Lock },
        ].map((chip) => (
          <div
            key={chip.label}
            className="flex items-center gap-1.5 bg-white/10 border border-white/10 rounded-full px-3 py-1.5"
          >
            <chip.icon className="w-3 h-3 text-blue-300" />
            <span className="text-blue-100 text-xs">{chip.label}</span>
          </div>
        ))}
      </div>
    </>
  );
}

export function AuthBrandPanel({ variant = 'tenant' }: AuthBrandPanelProps) {
  const gradientClass =
    variant === 'platform'
      ? 'from-slate-800 via-blue-900 to-slate-900'
      : 'from-blue-600 via-blue-700 to-slate-800';

  return (
    <div
      className={[
        'hidden lg:flex flex-col w-[45%] min-h-screen p-12 relative overflow-hidden',
        'bg-gradient-to-br',
        gradientClass,
      ].join(' ')}
    >
      {/* Dot pattern */}
      <div className="absolute inset-0 opacity-[0.04]">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="brandDots" width="24" height="24" patternUnits="userSpaceOnUse">
              <circle cx="3" cy="3" r="1.5" fill="white" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#brandDots)" />
        </svg>
      </div>

      {/* Glow accents */}
      <div className="absolute -top-32 -right-32 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-32 -left-16 w-80 h-80 bg-violet-600/15 rounded-full blur-3xl pointer-events-none" />

      {/* Logo */}
      <div className="relative flex items-center gap-2.5 mb-10">
        <div className="w-9 h-9 bg-white rounded-xl flex items-center justify-center shadow-sm">
          <span className="text-blue-700 font-bold text-sm leading-none">gN</span>
        </div>
        <span className="text-white font-bold text-lg tracking-tight">gNxtHire</span>
        {variant === 'platform' && (
          <span className="text-[10px] font-semibold text-blue-300 bg-blue-500/20 border border-blue-400/20 rounded-full px-2 py-0.5 ml-1">
            PLATFORM
          </span>
        )}
      </div>

      <div className="relative flex flex-col flex-1">
        {variant === 'tenant' ? <TenantPanel /> : <PlatformPanel />}
      </div>
    </div>
  );
}
