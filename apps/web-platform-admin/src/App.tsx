import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './lib/auth/AuthProvider';
import { RequireAuth, RedirectIfAuthenticated, RequireMfaChallenge } from './lib/auth/RouteGuards';
import { LoginPage } from './features/auth/LoginPage';
import { ForgotPasswordPage } from './features/auth/ForgotPasswordPage';
import { ResetPasswordPage } from './features/auth/ResetPasswordPage';
import { VerifyEmailPage } from './features/auth/VerifyEmailPage';
import { MfaVerifyPage } from './features/mfa/MfaVerifyPage';
import { OverviewPage } from './features/dashboard/OverviewPage';
import { SecurityPage } from './features/security/SecurityPage';
import { PlatformUsersPage } from './features/users/PlatformUsersPage';
import { ModulePage } from './features/modules/ModulePage';
import { TenantManagementPage } from './features/tenants/TenantManagementPage';
import { TenantDetailPage } from './features/tenants/TenantDetailPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Route paths under /auth/* mirror the links the identity service
              emails to admins (see FRONTEND_PLATFORM_ADMIN_* URLs in .env),
              so password-reset and verification emails land on real pages. */}
          <Route
            path="/auth/login"
            element={
              <RedirectIfAuthenticated>
                <LoginPage />
              </RedirectIfAuthenticated>
            }
          />
          <Route
            path="/auth/forgot-password"
            element={
              <RedirectIfAuthenticated>
                <ForgotPasswordPage />
              </RedirectIfAuthenticated>
            }
          />
          <Route path="/auth/reset-password" element={<ResetPasswordPage />} />
          <Route path="/auth/verify-email" element={<VerifyEmailPage />} />
          <Route
            path="/auth/mfa/verify"
            element={
              <RequireMfaChallenge>
                <MfaVerifyPage />
              </RequireMfaChallenge>
            }
          />

          <Route
            path="/"
            element={
              <RequireAuth>
                <OverviewPage />
              </RequireAuth>
            }
          />
          <Route
            path="/platform-users"
            element={
              <RequireAuth>
                <PlatformUsersPage />
              </RequireAuth>
            }
          />
          <Route
            path="/tenants"
            element={
              <RequireAuth>
                <TenantManagementPage />
              </RequireAuth>
            }
          />
          <Route
            path="/tenants/:tenantId"
            element={
              <RequireAuth>
                <TenantDetailPage />
              </RequireAuth>
            }
          />
          <Route
            path="/security"
            element={
              <RequireAuth>
                <SecurityPage />
              </RequireAuth>
            }
          />
          <Route
            path="/platform/:moduleSlug"
            element={
              <RequireAuth>
                <ModulePage />
              </RequireAuth>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
