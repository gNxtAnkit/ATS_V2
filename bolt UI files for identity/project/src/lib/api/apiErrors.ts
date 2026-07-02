export type SafeErrorKind =
  | 'invalid_credentials'
  | 'email_verification_required'
  | 'account_restricted'
  | 'invalid_mfa_code'
  | 'rate_limited'
  | 'invalid_reset_token'
  | 'invalid_verification_token'
  | 'validation'
  | 'network'
  | 'server'
  | 'unknown';

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fieldErrors: Record<string, string>;

  constructor(message: string, options: { status: number; code: string; fieldErrors?: Record<string, string> }) {
    super(message);
    this.name = 'ApiError';
    this.status = options.status;
    this.code = options.code;
    this.fieldErrors = options.fieldErrors ?? {};
  }
}

export function toSafeError(error: unknown, context?: 'login' | 'mfa' | 'reset' | 'verify'): { kind: SafeErrorKind; message: string } {
  if (!(error instanceof ApiError)) {
    return { kind: 'network', message: 'We could not reach the server. Please check your connection and try again.' };
  }

  if (error.code === 'rate_limited' || error.status === 429) {
    return { kind: 'rate_limited', message: 'Too many attempts. Please wait a few minutes and try again.' };
  }

  if (context === 'reset' && error.status === 401) {
    return { kind: 'invalid_reset_token', message: 'This password reset link is invalid or has expired.' };
  }

  if (context === 'verify' && error.status === 401) {
    return { kind: 'invalid_verification_token', message: 'This verification link is invalid, expired, or already used.' };
  }

  if (context === 'mfa' && error.status === 401) {
    return { kind: 'invalid_mfa_code', message: 'Invalid code. Please check your authenticator app and try again.' };
  }

  if (error.message.toLowerCase().includes('email verification required')) {
    return { kind: 'email_verification_required', message: 'Please verify your email before signing in.' };
  }

  if (error.status === 401 && context === 'login') {
    return { kind: 'invalid_credentials', message: 'The email or password you entered is incorrect. Please try again.' };
  }

  if (error.status === 401 || error.status === 403) {
    return { kind: 'account_restricted', message: 'Access is restricted for this account. Contact your administrator.' };
  }

  if (error.status === 400) {
    return { kind: 'validation', message: 'Please check the form and try again.' };
  }

  if (error.status >= 500) {
    return { kind: 'server', message: 'Something went wrong on our side. Please try again.' };
  }

  return { kind: 'unknown', message: 'We could not complete that request. Please try again.' };
}
