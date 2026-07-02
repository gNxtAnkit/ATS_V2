import { Link } from 'react-router-dom';
import { AuthLayout } from '../../components/layout/AuthLayout';
import { Button } from '../../components/ui/Button';
import { ShieldOff } from 'lucide-react';

export function AccountLockedPage() {
  return (
    <AuthLayout footerText="If you believe this is an error, contact your workspace administrator.">
      <div className="hidden lg:flex items-center gap-2.5 mb-8">
        <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
          <span className="text-white font-bold text-xs leading-none">gN</span>
        </div>
        <span className="text-slate-900 font-bold text-base tracking-tight">gNxtHire</span>
      </div>

      <div className="text-center py-2">
        <div className="w-16 h-16 bg-red-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
          <ShieldOff size={28} className="text-red-600" />
        </div>

        <h1 className="text-[22px] font-bold text-slate-900 mb-2 leading-tight">Account access restricted</h1>
        <p className="text-sm text-slate-500 mb-6 leading-relaxed">
          For security reasons, this account cannot be accessed right now. This may be due to
          unusual activity or an administrative action.
        </p>

        <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 mb-6 text-left">
          <p className="text-xs font-semibold text-slate-600 mb-2.5">What you can do:</p>
          <ul className="space-y-2 text-sm text-slate-600">
            <li className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full mt-2 shrink-0" />
              Contact your workspace administrator to restore access.
            </li>
            <li className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full mt-2 shrink-0" />
              If this is urgent, reach out to your organisation's IT support.
            </li>
            <li className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full mt-2 shrink-0" />
              Do not attempt to log in repeatedly as this may extend the restriction.
            </li>
          </ul>
        </div>

        <div className="flex flex-col gap-3">
          <Link to="/auth/login">
            <Button variant="secondary" fullWidth size="lg">
              Back to sign in
            </Button>
          </Link>
          <a
            href="mailto:support@gnxthire.io"
            className="text-sm text-blue-600 hover:text-blue-700 font-medium transition-colors"
          >
            Contact support
          </a>
        </div>
      </div>
    </AuthLayout>
  );
}
