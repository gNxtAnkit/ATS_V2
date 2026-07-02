import { CheckCircle2 } from 'lucide-react';

interface Rule {
  label: string;
  test: (password: string) => boolean;
}

interface PasswordPolicy {
  min_length: number;
  max_length: number;
  require_uppercase: boolean;
  require_lowercase: boolean;
  require_number: boolean;
  require_special: boolean;
}

const defaultPolicy: PasswordPolicy = {
  min_length: 12,
  max_length: 128,
  require_uppercase: true,
  require_lowercase: true,
  require_number: true,
  require_special: true,
};

function getPasswordRules(policy: PasswordPolicy = defaultPolicy): Rule[] {
  return [
    { label: `At least ${policy.min_length} characters`, test: (password) => password.length >= policy.min_length },
    { label: `No more than ${policy.max_length} characters`, test: (password) => password.length <= policy.max_length },
    ...(policy.require_uppercase ? [{ label: 'Uppercase letter (A-Z)', test: (password: string) => /[A-Z]/.test(password) }] : []),
    ...(policy.require_lowercase ? [{ label: 'Lowercase letter (a-z)', test: (password: string) => /[a-z]/.test(password) }] : []),
    ...(policy.require_number ? [{ label: 'Number (0-9)', test: (password: string) => /\d/.test(password) }] : []),
    ...(policy.require_special ? [{ label: 'Special character (!@#$)', test: (password: string) => /[^A-Za-z0-9]/.test(password) }] : []),
  ];
}

function getStrength(password: string, rules: Rule[]): number {
  if (!password) return 0;
  return Math.min(5, rules.filter((rule) => rule.test(password)).length);
}

const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong', 'Strong'];
const strengthColors = [
  '',
  'bg-red-500',
  'bg-amber-500',
  'bg-yellow-400',
  'bg-emerald-500',
  'bg-emerald-500',
];
const strengthTextColors = [
  '',
  'text-red-600',
  'text-amber-600',
  'text-yellow-600',
  'text-emerald-600',
  'text-emerald-600',
];

interface PasswordStrengthProps {
  password: string;
  confirmPassword?: string;
  policy?: PasswordPolicy;
}

export function PasswordStrength({ password, confirmPassword, policy = defaultPolicy }: PasswordStrengthProps) {
  const rules = getPasswordRules(policy);
  const strength = getStrength(password, rules);
  const showMatch = confirmPassword !== undefined;
  const passwordsMatch = Boolean(password && confirmPassword && password === confirmPassword);

  return (
    <div className="space-y-3">
      {password && (
        <div className="space-y-1.5">
          <div className="flex gap-1">
            {[1, 2, 3, 4].map((index) => (
              <div
                key={index}
                className={[
                  'h-1 flex-1 rounded-full transition-all duration-300',
                  strength > index ? strengthColors[strength] : 'bg-slate-200',
                ].join(' ')}
              />
            ))}
          </div>
          <p className="text-xs text-slate-500">
            Strength:{' '}
            <span className={['font-semibold', strengthTextColors[strength]].join(' ')}>
              {strengthLabels[strength]}
            </span>
          </p>
        </div>
      )}

      <ul className="space-y-1.5">
        {rules.map((rule) => {
          const passed = password ? rule.test(password) : false;
          return (
            <li key={rule.label} className="flex items-center gap-2">
              <span
                className={[
                  'w-4 h-4 rounded-full flex items-center justify-center shrink-0 transition-all duration-200',
                  passed ? 'bg-emerald-500' : 'bg-slate-100 border border-slate-200',
                ].join(' ')}
              >
                {passed && <CheckCircle2 size={10} className="text-white" strokeWidth={3} />}
              </span>
              <span className={['text-xs transition-colors', passed ? 'text-slate-700' : 'text-slate-500'].join(' ')}>
                {rule.label}
              </span>
            </li>
          );
        })}
        {showMatch && (
          <li className="flex items-center gap-2">
            <span
              className={[
                'w-4 h-4 rounded-full flex items-center justify-center shrink-0 transition-all duration-200',
                passwordsMatch ? 'bg-emerald-500' : 'bg-slate-100 border border-slate-200',
              ].join(' ')}
            >
              {passwordsMatch && <CheckCircle2 size={10} className="text-white" strokeWidth={3} />}
            </span>
            <span className={['text-xs transition-colors', passwordsMatch ? 'text-slate-700' : 'text-slate-500'].join(' ')}>
              Passwords match
            </span>
          </li>
        )}
      </ul>
    </div>
  );
}
