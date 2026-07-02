# Identity UI Integration Notes

## Detected Frontend Stack

- Approved Bolt UI project: `bolt UI files for identity/project`
- Framework: React 18 + Vite 5 + TypeScript
- Routing: `react-router-dom` with `HashRouter`, `Routes`, and route elements in `src/App.tsx`
- Styling: Tailwind CSS, global CSS in `src/index.css`, custom React UI primitives in `src/components/ui`
- Component libraries: custom components plus `lucide-react` icons
- No shadcn/ui, Radix, Chakra, Redux, Zustand, React Hook Form, Zod, Axios, or TanStack Query detected in the approved UI project

## Detected Styling Approach

- Tailwind utility classes are used directly throughout the approved screens.
- Existing tokens were already partially present in `tailwind.config.js` for brand, AI accent, surface colors, font family, and shadows.
- Centralized CSS custom properties were added in `src/index.css`.
- Shared UI class constants were added in `src/lib/theme.ts` for repeated focus, checkbox, logo, card, app surface, sidebar, and topbar styles.
- Hardcoded values were only replaced where low-risk and visually equivalent.
- Many approved layout-specific classes remain local to avoid visual regression.

## Detected Routing Approach

- `src/App.tsx` defines all routes using `HashRouter`.
- Tenant auth routes:
  - `/auth/login`
  - `/auth/forgot-password`
  - `/auth/reset-password`
  - `/auth/verify-email-required`
  - `/auth/verify-email`
  - `/auth/mfa/verify`
  - `/auth/mfa/recovery-code`
- Tenant protected routes:
  - `/dashboard`
  - `/settings/security/mfa/setup`
  - `/settings/security/mfa/setup/qr`
  - `/settings/security/mfa/recovery-codes`
- Platform admin routes:
  - `/platform-admin/login`
  - `/platform-admin/dashboard`
  - `/platform-admin/security/mfa/setup`
  - `/platform-admin/security/mfa/setup/qr`
  - `/platform-admin/security/mfa/recovery-codes`

## Detected Backend Identity Service API Endpoints

Tenant base path: `/v1/identity`

- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/forgot-password`
- `POST /auth/reset-password`
- `POST /auth/request-email-verification`
- `POST /auth/verify-email`
- `GET /auth/password-policy`
- `POST /mfa/totp/setup`
- `POST /mfa/totp/confirm`
- `POST /mfa/totp/verify`
- `POST /mfa/recovery-code/verify`

Platform admin base path: `/v1/identity/platform-admin`

- Same auth, password, email verification, session, and MFA endpoints as tenant, under the platform-admin base path.

## Detected Auth / Session Mechanism

- Backend returns frontend-managed bearer access tokens and rotating refresh tokens.
- The frontend stores only the current token pair and realm in `localStorage`.
- MFA challenge tokens are stored only in `sessionStorage` while completing login MFA.
- Recovery codes are passed through React Router navigation state and are not persisted in `localStorage` or `sessionStorage`.
- API calls use `Authorization: Bearer <access_token>` for authenticated endpoints.
- Current session is restored by calling `/auth/me` on app startup.
- Refresh token rotation is attempted once on authenticated `401` responses.
- Logout clears local state first and calls the backend logout endpoint with the refresh token.

## Files Modified

- `bolt UI files for identity/project/src/App.tsx`: added auth provider, public/protected route guards, tenant/platform route separation.
- `bolt UI files for identity/project/src/index.css`: added CSS custom properties for extracted approved theme values.
- `bolt UI files for identity/project/tailwind.config.js`: mapped existing approved theme values to CSS variables.
- `bolt UI files for identity/project/src/lib/theme.ts`: added shared UI class tokens.
- `bolt UI files for identity/project/src/lib/api/apiErrors.ts`: added safe Identity error normalization.
- `bolt UI files for identity/project/src/lib/api/httpClient.ts`: added shared fetch client, bearer auth, refresh retry, backend error parsing.
- `bolt UI files for identity/project/src/lib/api/identityApi.ts`: added typed Identity API methods.
- `bolt UI files for identity/project/src/lib/qr/qrCode.ts`: added in-repo QR encoder for backend `otpauth://` provisioning URIs.
- `bolt UI files for identity/project/src/components/ui/QrCode.tsx`: added SVG QR rendering component.
- `bolt UI files for identity/project/src/lib/auth/authTypes.ts`: added session/API types.
- `bolt UI files for identity/project/src/lib/auth/authStorage.ts`: added token/challenge storage helpers.
- `bolt UI files for identity/project/src/lib/auth/authRealm.ts`: added shared tenant/platform realm resolution.
- `bolt UI files for identity/project/src/lib/auth/authSession.tsx`: added current-session provider and logout behavior.
- `bolt UI files for identity/project/src/lib/auth/authGuards.tsx`: added public/protected route guards.
- `bolt UI files for identity/project/src/features/auth/LoginPage.tsx`: replaced demo login routes with tenant login API integration.
- `bolt UI files for identity/project/src/features/auth/PlatformAdminLoginPage.tsx`: replaced demo platform login with platform-admin API integration.
- `bolt UI files for identity/project/src/features/auth/ForgotPasswordPage.tsx`: integrated forgot-password API with enumeration-safe success.
- `bolt UI files for identity/project/src/features/auth/ResetPasswordPage.tsx`: integrated token reset flow and safe invalid/expired handling.
- `bolt UI files for identity/project/src/features/auth/EmailVerificationPage.tsx`: integrated resend and token verification flows.
- `bolt UI files for identity/project/src/features/mfa/MfaVerifyPage.tsx`: integrated MFA challenge verification.
- `bolt UI files for identity/project/src/features/mfa/MfaRecoveryCodePage.tsx`: integrated recovery-code verification through explicit backend recovery-code endpoint.
- `bolt UI files for identity/project/src/features/mfa/MfaSetupIntroPage.tsx`: integrated MFA setup start endpoint.
- `bolt UI files for identity/project/src/features/mfa/MfaSetupQrPage.tsx`: integrated setup confirmation and backend manual secret display.
- `bolt UI files for identity/project/src/features/mfa/MfaRecoveryCodesPage.tsx`: integrated backend recovery-code display once through navigation state.
- `bolt UI files for identity/project/src/components/layout/AppShell.tsx`: reused centralized app surface token.
- `bolt UI files for identity/project/src/components/layout/Sidebar.tsx`: added tenant/platform navigation separation.
- `bolt UI files for identity/project/src/components/layout/TopBar.tsx`: replaced hardcoded user/logout with current session and backend logout.
- `bolt UI files for identity/project/src/components/ui/Button.tsx`: reused approved brand token.
- `bolt UI files for identity/project/src/components/ui/PasswordStrength.tsx`: uses backend password policy values instead of fixed UI-only rules.
- `bolt UI files for identity/project/src/pages/DashboardPage.tsx`: uses current session name and realm-specific MFA path.
- `services/identity/src/gnxthire_identity/config.py`: added platform-admin email verification frontend URL setting.
- `services/identity/src/gnxthire_identity/email.py`: supports tenant vs platform-admin verification URL generation.
- `services/identity/src/gnxthire_identity/platform_admin/service.py`: sends platform-admin email verification links to the platform-admin frontend URL.
- `services/identity/src/gnxthire_identity/schemas.py`: added password-policy and recovery-code verification DTOs.
- `services/identity/src/gnxthire_identity/api/tenant_routes.py`: added password-policy and explicit recovery-code verification routes.
- `services/identity/src/gnxthire_identity/api/platform_routes.py`: added password-policy and explicit recovery-code verification routes.
- `tests/identity/test_mfa.py`: added route coverage for recovery-code single-use verification and password-policy endpoint.
- `tests/identity/test_password_reset_and_email_verification.py`: added platform-admin email verification URL coverage.
- `tests/identity/conftest.py`: extended platform-admin seed fixture to support unverified email setup.
- `.env.example`: added `FRONTEND_PLATFORM_ADMIN_EMAIL_VERIFY_URL`.
- `docs/api/identity-api.md`: documented password-policy and recovery-code verification endpoints.
- `integration_notes.md`: this implementation note.

## Assumptions Made

- Frontend API base URL is `VITE_IDENTITY_API_BASE_URL`, defaulting to `http://localhost:8001`.
- Default auth realm is `VITE_DEFAULT_AUTH_REALM` when set, otherwise port `5174` means platform admin and all other ports mean tenant.
- Backend token responses are the source of truth for session state.
- The approved Bolt project is the frontend target because `apps/web-*` currently contain README placeholders only.

## Backend Gaps or Mismatches Found and Resolved

- Added explicit `POST /mfa/recovery-code/verify` endpoints for tenant and platform-admin realms. These call the existing single-use recovery-code service logic and keep the API contract clear.
- Added an in-repo SVG QR encoder/renderer, so MFA setup now displays a real scannable QR from the backend `otpauth://` provisioning URI without adding a dependency.
- Added `FRONTEND_PLATFORM_ADMIN_EMAIL_VERIFY_URL` and updated platform-admin email verification email generation to use the platform-admin frontend URL.
- Added `GET /auth/password-policy` endpoints for both realms and updated the reset-password UI checklist/validation to use backend policy values.
- No known Identity UI/backend integration gaps remain from this pass.

## Verification Steps Completed

- `npm.cmd ci --ignore-scripts --cache .\.npm-cache`: passed; installed local dependencies. npm reported 18 audit findings in existing dependency tree.
- `npm.cmd run typecheck`: passed.
- `npm.cmd run lint`: passed.
- `npm.cmd run build`: passed when run by the user locally. Output included 1512 transformed modules and generated `dist/index.html`, CSS, and JS assets.
- `python -m pytest tests\identity\test_mfa.py tests\identity\test_password_reset_and_email_verification.py`: passed, 13 tests.
- `python -m pytest tests\identity`: passed, 36 tests. Pytest emitted a cache warning for `.pytest_cache`, but all tests passed.

## Manual Verification Status

- Static/code verification completed for:
  - tenant login has email/password only and no tenant/company/workspace field
  - platform admin login uses separate endpoint and redirect
  - forgot password shows enumeration-safe success text
  - reset password reads URL token
  - reset password uses backend password-policy endpoint
  - email verification reads URL token
  - platform-admin email verification links use the platform-admin frontend URL
  - MFA input supports paste via existing `OtpInput`
  - MFA setup renders a real QR code from the backend provisioning URI
  - MFA recovery-code verification calls explicit backend route and remains single-use
  - recovery codes are not stored in `localStorage` or `sessionStorage`
  - protected tenant and platform route guards are separate
  - logout calls backend and clears frontend session
  - mock auth handlers and demo credential blocks were removed
- Live browser/API walkthrough was not completed because no Identity backend server was running in this turn, but backend route tests and frontend build/type/lint checks passed.
