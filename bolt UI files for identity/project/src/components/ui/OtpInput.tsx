import { useRef, useEffect, ClipboardEvent, KeyboardEvent, ChangeEvent } from 'react';

interface OtpInputProps {
  value: string;
  onChange: (value: string) => void;
  length?: number;
  error?: boolean;
  autoFocus?: boolean;
}

export function OtpInput({ value, onChange, length = 6, error = false, autoFocus = false }: OtpInputProps) {
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (autoFocus) inputRefs.current[0]?.focus();
  }, [autoFocus]);

  const getDigits = () => value.padEnd(length, ' ').slice(0, length);

  const handleChange = (index: number, e: ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/\D/g, '');
    if (!raw) {
      const digits = getDigits().split('');
      digits[index] = ' ';
      onChange(digits.join('').trimEnd());
      return;
    }
    const char = raw[raw.length - 1];
    const digits = getDigits().split('');
    digits[index] = char;
    const next = digits.join('').trimEnd();
    onChange(next);
    if (index < length - 1) inputRefs.current[index + 1]?.focus();
  };

  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace') {
      e.preventDefault();
      const digits = getDigits().split('');
      if (digits[index] !== ' ') {
        digits[index] = ' ';
        onChange(digits.join('').trimEnd());
      } else if (index > 0) {
        digits[index - 1] = ' ';
        onChange(digits.join('').trimEnd());
        inputRefs.current[index - 1]?.focus();
      }
    } else if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus();
    } else if (e.key === 'ArrowRight' && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e: ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, length);
    onChange(pasted);
    const focusIndex = Math.min(pasted.length, length - 1);
    inputRefs.current[focusIndex]?.focus();
  };

  const digits = getDigits();

  return (
    <div className="flex gap-2.5 justify-center" role="group" aria-label="Verification code input">
      {Array.from({ length }).map((_, i) => (
        <input
          key={i}
          ref={(el) => { inputRefs.current[i] = el; }}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={digits[i] === ' ' ? '' : digits[i]}
          onChange={(e) => handleChange(i, e)}
          onKeyDown={(e) => handleKeyDown(i, e)}
          onPaste={handlePaste}
          aria-label={`Digit ${i + 1} of ${length}`}
          className={[
            'w-11 h-14 text-center text-xl font-semibold rounded-xl border-2 outline-none',
            'bg-white transition-all duration-150 text-slate-900',
            'focus:ring-4',
            error
              ? 'border-red-400 focus:border-red-500 focus:ring-red-100'
              : 'border-slate-200 focus:border-blue-500 focus:ring-blue-100',
          ].join(' ')}
        />
      ))}
    </div>
  );
}
