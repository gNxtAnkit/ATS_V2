import { ReactNode } from 'react';
import { AuthBrandPanel } from './AuthBrandPanel';

interface AuthLayoutProps {
  children: ReactNode;
  variant?: 'tenant' | 'platform';
  footerText?: string;
}

export function AuthLayout({ children, variant = 'tenant', footerText }: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50 flex">
      <AuthBrandPanel variant={variant} />

      {/* Form side */}
      <div className="flex-1 flex flex-col items-center justify-center min-h-screen px-5 py-12 relative">
        {/* Subtle background glow on right side */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute -top-48 right-0 w-[500px] h-[500px] bg-blue-100/50 rounded-full blur-3xl" />
        </div>

        {/* Mobile-only logo */}
        <div className="flex lg:hidden items-center gap-2.5 mb-8">
          <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
            <span className="text-white font-bold text-sm leading-none">gN</span>
          </div>
          <span className="text-slate-900 font-bold text-lg tracking-tight">gNxtHire</span>
        </div>

        {/* Form card */}
        <div className="relative w-full max-w-md bg-white rounded-2xl shadow-auth border border-slate-200 p-8">
          {children}
        </div>

        {/* Footer */}
        <p className="relative mt-5 text-xs text-slate-400 text-center max-w-sm leading-relaxed">
          {footerText || 'Protected with enterprise-grade authentication and audit logging.'}
        </p>
      </div>
    </div>
  );
}
