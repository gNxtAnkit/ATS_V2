import { FormEvent, useState } from 'react';
import { X } from 'lucide-react';
import { Button } from './Button';
import { Alert } from './Alert';
import { Input } from './Input';

export interface FieldDef {
  key: string;
  label: string;
  type: 'text' | 'textarea' | 'number' | 'decimal' | 'boolean' | 'select' | 'uuid' | 'datetime';
  required?: boolean;
  options?: string[];
  defaultValue?: string | number | boolean;
  generateDefault?: () => string;
  helper?: string;
  placeholder?: string;
}

function initialValues(fields: FieldDef[]): Record<string, string | boolean> {
  const values: Record<string, string | boolean> = {};
  for (const field of fields) {
    if (field.type === 'boolean') values[field.key] = Boolean(field.defaultValue ?? false);
    else if (field.generateDefault) values[field.key] = field.generateDefault();
    else values[field.key] = field.defaultValue !== undefined ? String(field.defaultValue) : '';
  }
  return values;
}

/** Coerces the raw string/boolean form state into the JSON body shape the API expects. */
export function coerceFieldValues(fields: FieldDef[], raw: Record<string, string | boolean>): Record<string, unknown> {
  const body: Record<string, unknown> = {};
  for (const field of fields) {
    const value = raw[field.key];
    if (field.type === 'boolean') {
      body[field.key] = Boolean(value);
      continue;
    }
    const stringValue = typeof value === 'string' ? value.trim() : '';
    if (!stringValue) {
      if (field.required) continue; // caught by validation before submit
      body[field.key] = null;
      continue;
    }
    if (field.type === 'number') body[field.key] = Number(stringValue);
    else if (field.type === 'decimal') body[field.key] = stringValue;
    else if (field.type === 'datetime') body[field.key] = new Date(stringValue).toISOString();
    else body[field.key] = stringValue;
  }
  return body;
}

export function CreateRecordModal({
  title,
  fields,
  submitLabel = 'Create',
  onSubmit,
  onClose,
}: {
  title: string;
  fields: FieldDef[];
  submitLabel?: string;
  onSubmit: (body: Record<string, unknown>) => Promise<void>;
  onClose: () => void;
}) {
  const [values, setValues] = useState<Record<string, string | boolean>>(() => initialValues(fields));
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function setValue(key: string, value: string | boolean) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const missing = fields.find((field) => field.required && field.type !== 'boolean' && !String(values[field.key] ?? '').trim());
    if (missing) {
      setError(`${missing.label} is required.`);
      return;
    }
    setBusy(true);
    try {
      await onSubmit(coerceFieldValues(fields, values));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'This request could not be completed.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-900/40" onClick={busy ? undefined : onClose} />
      <div className="relative bg-white rounded-2xl shadow-float border border-slate-200 w-full max-w-lg max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between p-5 border-b border-slate-100 shrink-0">
          <h3 className="text-[15px] font-bold text-slate-900">{title}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600" aria-label="Close">
            <X size={16} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="overflow-y-auto p-5 space-y-4">
          {error && <Alert variant="error">{error}</Alert>}
          {fields.map((field) => (
            <div key={field.key}>
              {field.type === 'boolean' ? (
                <label className="flex items-center gap-2.5 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={Boolean(values[field.key])}
                    onChange={(event) => setValue(field.key, event.target.checked)}
                    className="w-4 h-4 rounded border-slate-300 text-slate-700 focus:ring-slate-500/30"
                  />
                  {field.label}
                </label>
              ) : field.type === 'select' ? (
                <div className="space-y-1.5">
                  <label className="block text-sm font-medium text-slate-700">{field.label}</label>
                  <select
                    value={String(values[field.key] ?? '')}
                    onChange={(event) => setValue(field.key, event.target.value)}
                    className="w-full h-10 px-3.5 text-sm rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-slate-500/20 focus:border-slate-500"
                  >
                    <option value="">Select...</option>
                    {field.options?.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </div>
              ) : field.type === 'textarea' ? (
                <div className="space-y-1.5">
                  <label className="block text-sm font-medium text-slate-700">{field.label}</label>
                  <textarea
                    value={String(values[field.key] ?? '')}
                    onChange={(event) => setValue(field.key, event.target.value)}
                    placeholder={field.placeholder}
                    rows={3}
                    className="w-full px-3.5 py-2.5 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-500/20 focus:border-slate-500"
                  />
                </div>
              ) : (
                <Input
                  label={field.label}
                  type={field.type === 'number' || field.type === 'decimal' ? 'text' : field.type === 'datetime' ? 'datetime-local' : 'text'}
                  value={String(values[field.key] ?? '')}
                  onChange={(event) => setValue(field.key, event.target.value)}
                  placeholder={field.placeholder}
                  helper={field.helper}
                />
              )}
            </div>
          ))}
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="secondary" size="sm" onClick={onClose} disabled={busy}>
              Cancel
            </Button>
            <Button type="submit" size="sm" loading={busy}>
              {submitLabel}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
