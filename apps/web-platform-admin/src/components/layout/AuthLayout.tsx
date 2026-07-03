import { ReactNode } from 'react';
import { ShieldCheck, KeyRound, MailCheck, Lock } from 'lucide-react';

interface AuthLayoutProps {
  children: ReactNode;
  footerText?: string;
}

const capabilities = [
  { label: 'Password sign in', icon: KeyRound },
  { label: 'Email verification', icon: MailCheck },
  { label: 'Authenticator MFA', icon: ShieldCheck },
  { label: 'Recovery codes', icon: Lock },
];

/**
 * Shared auth-screen frame (brand panel + centered card). Deliberately uses
 * ordinary, non-privileged product language — see BrandPanel copy below —
 * per the requirement that the public sign-in screen not reveal that this is
 * an internal/admin surface.
 */
export function AuthLayout({ children, footerText }: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50 flex">
      <div className="hidden lg:flex flex-col w-[45%] min-h-screen p-12 relative overflow-hidden bg-gradient-to-br from-slate-700 via-slate-800 to-slate-950">
        <div className="relative flex items-center gap-2.5 mb-10">
          <div className="w-9 h-9 bg-white rounded-xl flex items-center justify-center shadow-sm">
            <span className="text-slate-800 font-bold text-sm leading-none">gN</span>
          </div>
          <span className="text-white font-bold text-lg tracking-tight">gNxtHire</span>
        </div>

        <div className="relative flex flex-col flex-1 justify-center">
          <h2 className="text-[28px] font-bold text-white leading-tight mb-3">Welcome back.</h2>
          <p className="text-slate-300 text-sm leading-relaxed max-w-md">
            Sign in to continue to gNxtHire. Your connection is protected with modern authentication and audit
            logging.
          </p>

          <div className="mt-8 grid grid-cols-2 gap-3 max-w-md">
            {capabilities.map((item) => (
              <div key={item.label} className="bg-white/10 border border-white/10 rounded-xl p-4">
                <item.icon className="w-5 h-5 text-slate-300 mb-3" />
                <p className="text-sm font-semibold text-white">{item.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center min-h-screen px-5 py-12 relative">
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute -top-48 right-0 w-[500px] h-[500px] bg-slate-100/60 rounded-full blur-3xl" />
        </div>

        <div className="flex lg:hidden items-center gap-2.5 mb-8">
          <div className="w-9 h-9 bg-slate-800 rounded-xl flex items-center justify-center shadow-sm">
            <span className="text-white font-bold text-sm leading-none">gN</span>
          </div>
          <span className="text-slate-900 font-bold text-lg tracking-tight">gNxtHire</span>
        </div>

        <div className="relative w-full max-w-md bg-white rounded-2xl shadow-auth border border-slate-200 p-8">
          {children}
        </div>

        <p className="relative mt-5 text-xs text-slate-400 text-center max-w-sm leading-relaxed">
          {footerText || 'Your connection is protected.'}
        </p>
      </div>
    </div>
  );
}
