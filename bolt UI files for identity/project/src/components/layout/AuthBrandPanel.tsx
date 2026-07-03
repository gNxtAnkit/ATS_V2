import { KeyRound, Lock, MailCheck, Shield } from 'lucide-react';

interface AuthBrandPanelProps {
  variant?: 'tenant' | 'platform';
}

const tenantCapabilities = [
  { label: 'Password sign in', icon: KeyRound },
  { label: 'Email verification', icon: MailCheck },
  { label: 'Authenticator MFA', icon: Shield },
  { label: 'Recovery codes', icon: Lock },
];

const platformCapabilities = [
  { label: 'Separate admin realm', icon: Shield },
  { label: 'Admin password reset', icon: KeyRound },
  { label: 'Admin email verification', icon: MailCheck },
  { label: 'Admin authenticator MFA', icon: Lock },
];

export function AuthBrandPanel({ variant = 'tenant' }: AuthBrandPanelProps) {
  const capabilities = variant === 'platform' ? platformCapabilities : tenantCapabilities;
  const heading = variant === 'platform'
    ? 'Secure access for platform administrators.'
    : 'Secure access to your gNxtHire workspace.';
  const body = variant === 'platform'
    ? 'Platform administration uses a separate authentication realm with dedicated tokens, sessions, and MFA controls.'
    : 'Identity, password recovery, email verification, and authenticator-based MFA are handled by the gNxtHire Identity Service.';

  return (
    <div className="hidden lg:flex flex-col w-[45%] min-h-screen p-12 relative overflow-hidden bg-gradient-to-br from-blue-700 via-slate-800 to-slate-950">
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

      <div className="relative flex flex-col flex-1 justify-center">
        <h2 className="text-[28px] font-bold text-white leading-tight mb-3">{heading}</h2>
        <p className="text-blue-200 text-sm leading-relaxed max-w-md">{body}</p>

        <div className="mt-8 grid grid-cols-2 gap-3 max-w-md">
          {capabilities.map((item) => (
            <div key={item.label} className="bg-white/10 border border-white/10 rounded-xl p-4">
              <item.icon className="w-5 h-5 text-blue-200 mb-3" />
              <p className="text-sm font-semibold text-white">{item.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
