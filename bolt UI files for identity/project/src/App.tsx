import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthSessionProvider } from './lib/auth/authSession';
import { ProtectedRoute, PublicOnlyRoute } from './lib/auth/authGuards';
import { LoginPage } from './features/auth/LoginPage';
import { PlatformAdminLoginPage } from './features/auth/PlatformAdminLoginPage';
import { ForgotPasswordPage } from './features/auth/ForgotPasswordPage';
import { ResetPasswordPage } from './features/auth/ResetPasswordPage';
import {
  EmailVerificationRequiredPage,
  EmailVerificationResultPage,
} from './features/auth/EmailVerificationPage';
import { AccountLockedPage } from './features/auth/AccountLockedPage';
import { MfaVerifyPage } from './features/mfa/MfaVerifyPage';
import { MfaRecoveryCodePage } from './features/mfa/MfaRecoveryCodePage';
import { MfaSetupIntroPage } from './features/mfa/MfaSetupIntroPage';
import { MfaSetupQrPage } from './features/mfa/MfaSetupQrPage';
import { MfaRecoveryCodesPage } from './features/mfa/MfaRecoveryCodesPage';
import { DashboardPage } from './pages/DashboardPage';

export default function App() {
  return (
    <AuthSessionProvider>
      <BrowserRouter>
        <Routes>
        {/* Default */}
        <Route path="/" element={<Navigate to="/auth/login" replace />} />

        {/* Auth screens */}
        <Route path="/auth/login" element={<PublicOnlyRoute realm="tenant"><LoginPage /></PublicOnlyRoute>} />
        <Route path="/auth/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/auth/reset-password" element={<ResetPasswordPage />} />
        <Route path="/auth/verify-email-required" element={<EmailVerificationRequiredPage />} />
        <Route path="/auth/verify-email" element={<EmailVerificationResultPage />} />
        <Route path="/auth/mfa/verify" element={<MfaVerifyPage />} />
        <Route path="/auth/mfa/recovery-code" element={<MfaRecoveryCodePage />} />
        <Route path="/auth/account-locked" element={<AccountLockedPage />} />

        {/* Platform admin */}
        <Route path="/platform-admin/login" element={<PublicOnlyRoute realm="platform"><PlatformAdminLoginPage /></PublicOnlyRoute>} />

        {/* App shell — authenticated routes */}
        <Route path="/dashboard" element={<ProtectedRoute realm="tenant"><DashboardPage /></ProtectedRoute>} />
        <Route path="/settings/security/mfa/setup" element={<ProtectedRoute realm="tenant"><MfaSetupIntroPage /></ProtectedRoute>} />
        <Route path="/settings/security/mfa/setup/qr" element={<ProtectedRoute realm="tenant"><MfaSetupQrPage /></ProtectedRoute>} />
        <Route path="/settings/security/mfa/recovery-codes" element={<ProtectedRoute realm="tenant"><MfaRecoveryCodesPage /></ProtectedRoute>} />
        <Route path="/platform-admin/dashboard" element={<ProtectedRoute realm="platform"><DashboardPage /></ProtectedRoute>} />
        <Route path="/platform-admin/security/mfa/setup" element={<ProtectedRoute realm="platform"><MfaSetupIntroPage /></ProtectedRoute>} />
        <Route path="/platform-admin/security/mfa/setup/qr" element={<ProtectedRoute realm="platform"><MfaSetupQrPage /></ProtectedRoute>} />
        <Route path="/platform-admin/security/mfa/recovery-codes" element={<ProtectedRoute realm="platform"><MfaRecoveryCodesPage /></ProtectedRoute>} />
        <Route path="/platform-admin/users" element={<ProtectedRoute realm="platform"><DashboardPage /></ProtectedRoute>} />
        <Route path="/platform-admin/audit" element={<ProtectedRoute realm="platform"><DashboardPage /></ProtectedRoute>} />
        <Route path="/platform-admin/reports" element={<ProtectedRoute realm="platform"><DashboardPage /></ProtectedRoute>} />
        <Route path="/platform-admin/help" element={<ProtectedRoute realm="platform"><DashboardPage /></ProtectedRoute>} />

        {/* Placeholder routes to avoid dead links from nav */}
        <Route path="/jobs" element={<ProtectedRoute realm="tenant"><DashboardPage /></ProtectedRoute>} />
        <Route path="/candidates" element={<ProtectedRoute realm="tenant"><DashboardPage /></ProtectedRoute>} />
        <Route path="/pipeline" element={<ProtectedRoute realm="tenant"><DashboardPage /></ProtectedRoute>} />
        <Route path="/interviews" element={<ProtectedRoute realm="tenant"><DashboardPage /></ProtectedRoute>} />
        <Route path="/inbox" element={<ProtectedRoute realm="tenant"><DashboardPage /></ProtectedRoute>} />
        <Route path="/reports" element={<ProtectedRoute realm="tenant"><DashboardPage /></ProtectedRoute>} />
        <Route path="/help" element={<ProtectedRoute realm="tenant"><DashboardPage /></ProtectedRoute>} />

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/auth/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthSessionProvider>
  );
}
