from __future__ import annotations

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from html import escape
from typing import Protocol
from urllib.parse import urlencode

from gnxthire_common.errors import AppError

from gnxthire_identity.config import IdentitySettings


class EmailDeliveryError(AppError):
    code = "email_delivery_failed"
    status_code = 502


@dataclass(frozen=True)
class IdentityEmail:
    to_email: str
    subject: str
    text_body: str
    html_body: str


class EmailSender(Protocol):
    def send(self, message: IdentityEmail) -> None:
        """Deliver an identity-owned transactional email."""
        ...


class SmtpEmailSender:
    def __init__(self, settings: IdentitySettings) -> None:
        self._settings = settings

    def send(self, message: IdentityEmail) -> None:
        email_message = EmailMessage()
        email_message["From"] = f"{self._settings.smtp_from_name} <{self._settings.smtp_from_email}>"
        email_message["To"] = message.to_email
        email_message["Subject"] = message.subject
        email_message.set_content(message.text_body)
        email_message.add_alternative(message.html_body, subtype="html")

        try:
            if self._settings.smtp_use_ssl:
                smtp_client: smtplib.SMTP = smtplib.SMTP_SSL(
                    self._settings.smtp_host, self._settings.smtp_port, timeout=10
                )
            else:
                smtp_client = smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port, timeout=10)
            with smtp_client:
                if self._settings.smtp_use_tls:
                    smtp_client.starttls()
                if self._settings.smtp_username:
                    password = (
                        self._settings.smtp_password.get_secret_value()
                        if self._settings.smtp_password is not None
                        else ""
                    )
                    smtp_client.login(self._settings.smtp_username, password)
                smtp_client.send_message(email_message)
        except (OSError, smtplib.SMTPException, ssl.SSLError) as exc:
            raise EmailDeliveryError(
                "SMTP email delivery failed",
                safe_detail="Email delivery failed",
            ) from exc


class CapturingEmailSender:
    def __init__(self) -> None:
        self.messages: list[IdentityEmail] = []

    def send(self, message: IdentityEmail) -> None:
        self.messages.append(message)


def build_email_verification_url(
    settings: IdentitySettings, *, token: str, tenant: str | None = None, platform_admin: bool = False
) -> str:
    base_url = (
        settings.frontend_platform_admin_email_verify_url
        if platform_admin
        else settings.frontend_email_verify_url
    )
    return _build_url(str(base_url), token=token, tenant=tenant)


def build_password_reset_url(
    settings: IdentitySettings, *, token: str, tenant: str | None = None, platform_admin: bool = False
) -> str:
    base_url = (
        settings.frontend_platform_admin_password_reset_url
        if platform_admin
        else settings.frontend_password_reset_url
    )
    return _build_url(str(base_url), token=token, tenant=tenant)


def verification_email(to_email: str, *, verification_url: str) -> IdentityEmail:
    safe_url = escape(verification_url, quote=True)
    return IdentityEmail(
        to_email=to_email,
        subject="Verify your gNxtHire email",
        text_body=f"Verify your email by opening this link: {verification_url}",
        html_body=f"<p>Verify your email by opening this link:</p><p><a href=\"{safe_url}\">Verify email</a></p>",
    )


def password_reset_email(to_email: str, *, reset_url: str) -> IdentityEmail:
    safe_url = escape(reset_url, quote=True)
    return IdentityEmail(
        to_email=to_email,
        subject="Reset your gNxtHire password",
        text_body=f"Reset your password by opening this link: {reset_url}",
        html_body=f"<p>Reset your password by opening this link:</p><p><a href=\"{safe_url}\">Reset password</a></p>",
    )


def password_changed_email(to_email: str) -> IdentityEmail:
    return IdentityEmail(
        to_email=to_email,
        subject="Your gNxtHire password was changed",
        text_body="Your gNxtHire password was changed. If this was not you, contact support immediately.",
        html_body="<p>Your gNxtHire password was changed. If this was not you, contact support immediately.</p>",
    )


def mfa_enabled_email(to_email: str) -> IdentityEmail:
    return IdentityEmail(
        to_email=to_email,
        subject="MFA enabled for your gNxtHire account",
        text_body="Multi-factor authentication was enabled for your gNxtHire account.",
        html_body="<p>Multi-factor authentication was enabled for your gNxtHire account.</p>",
    )


def mfa_disabled_email(to_email: str) -> IdentityEmail:
    return IdentityEmail(
        to_email=to_email,
        subject="MFA disabled for your gNxtHire account",
        text_body="Multi-factor authentication was disabled for your gNxtHire account.",
        html_body="<p>Multi-factor authentication was disabled for your gNxtHire account.</p>",
    )


def _build_url(base_url: str, *, token: str, tenant: str | None) -> str:
    separator = "&" if "?" in base_url else "?"
    params = {"token": token} if tenant is None else {"token": token, "tenant": tenant}
    return f"{base_url}{separator}{urlencode(params)}"
