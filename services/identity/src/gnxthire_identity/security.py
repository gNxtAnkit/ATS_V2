from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote, urlencode

from gnxthire_common.errors import AuthenticationError, ValidationFailure

from gnxthire_identity.config import IdentitySettings

PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 600_000


@dataclass(frozen=True)
class SignedTokenClaims:
    subject: str
    actor_type: str
    token_type: str
    audience: str
    issuer: str
    expires_at: datetime
    session_id: str | None = None
    tenant_id: str | None = None
    extra: dict[str, Any] | None = None


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "$".join(
        [
            PASSWORD_ALGORITHM,
            str(PASSWORD_ITERATIONS),
            _b64url_encode(salt),
            _b64url_encode(digest),
        ]
    )


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        algorithm, iterations_text, salt_text, digest_text = stored_hash.split("$", 3)
        if algorithm != PASSWORD_ALGORITHM:
            return False
        salt = _b64url_decode(salt_text)
        expected_digest = _b64url_decode(digest_text)
        actual_digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iterations_text)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual_digest, expected_digest)


def validate_password_policy(password: str, email: str, settings: IdentitySettings) -> None:
    field_errors: list[str] = []
    if len(password) < settings.password_min_length:
        field_errors.append("Password is too short")
    if len(password) > settings.password_max_length:
        field_errors.append("Password is too long")
    if settings.password_require_uppercase and not any(char.isupper() for char in password):
        field_errors.append("Password must contain an uppercase letter")
    if settings.password_require_lowercase and not any(char.islower() for char in password):
        field_errors.append("Password must contain a lowercase letter")
    if settings.password_require_number and not any(char.isdigit() for char in password):
        field_errors.append("Password must contain a number")
    if settings.password_require_special and not any(not char.isalnum() for char in password):
        field_errors.append("Password must contain a special character")
    if settings.password_prevent_email_similarity and email:
        local_part = email.split("@", 1)[0].lower()
        if local_part and local_part in password.lower():
            field_errors.append("Password must not contain the email local part")
    if field_errors:
        raise ValidationFailure("; ".join(field_errors), safe_detail="Password does not meet policy")


def generate_opaque_token(byte_length: int = 32) -> str:
    return secrets.token_urlsafe(byte_length)


def token_hmac(raw_token: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), raw_token.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"sha256:{digest}"


def create_signed_token(claims: SignedTokenClaims, secret: str) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": claims.subject,
        "jti": secrets.token_urlsafe(16),
        "iss": claims.issuer,
        "aud": claims.audience,
        "exp": int(claims.expires_at.timestamp()),
        "iat": int(now.timestamp()),
        "actor_type": claims.actor_type,
        "typ": claims.token_type,
    }
    if claims.session_id is not None:
        payload["sid"] = claims.session_id
    if claims.tenant_id is not None:
        payload["tid"] = claims.tenant_id
    if claims.extra:
        payload.update(claims.extra)
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = ".".join(
        [
            _b64url_json(header),
            _b64url_json(payload),
        ]
    )
    signature = _sign(signing_input, secret)
    return f"{signing_input}.{signature}"


def verify_signed_token(
    token: str,
    *,
    secret: str,
    issuer: str,
    audience: str,
    token_type: str,
) -> dict[str, Any]:
    try:
        header_text, payload_text, signature = token.split(".", 2)
        signing_input = f"{header_text}.{payload_text}"
        expected_signature = _sign(signing_input, secret)
        if not hmac.compare_digest(signature, expected_signature):
            raise AuthenticationError("Invalid token", safe_detail="Invalid token")
        header = json.loads(_b64url_decode(header_text))
        payload = json.loads(_b64url_decode(payload_text))
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuthenticationError("Invalid token", safe_detail="Invalid token") from exc

    if header.get("alg") != "HS256":
        raise AuthenticationError("Invalid token algorithm", safe_detail="Invalid token")
    if payload.get("iss") != issuer or payload.get("aud") != audience or payload.get("typ") != token_type:
        raise AuthenticationError("Invalid token claims", safe_detail="Invalid token")
    if int(payload.get("exp", 0)) < int(time.time()):
        raise AuthenticationError("Expired token", safe_detail="Token expired")
    return payload


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def build_totp_uri(*, issuer: str, account_name: str, secret: str, digits: int, interval: int) -> str:
    label = f"{issuer}:{account_name}"
    query = urlencode(
        {
            "secret": secret,
            "issuer": issuer,
            "algorithm": "SHA1",
            "digits": digits,
            "period": interval,
        }
    )
    return f"otpauth://totp/{quote(label)}?{query}"


def verify_totp_code(
    *,
    secret: str,
    code: str,
    digits: int,
    interval: int,
    valid_window: int,
    at_time: int | None = None,
) -> bool:
    if not code.isdigit() or len(code) != digits:
        return False
    timestamp = int(time.time()) if at_time is None else at_time
    counter = timestamp // interval
    for offset in range(-valid_window, valid_window + 1):
        expected = _totp_at_counter(secret, counter + offset, digits)
        if hmac.compare_digest(code, expected):
            return True
    return False


def generate_recovery_codes(count: int, length: int) -> list[str]:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return ["".join(secrets.choice(alphabet) for _ in range(length)) for _ in range(count)]


def encrypt_secret(plaintext: str, key: str) -> str:
    nonce = secrets.token_bytes(16)
    plaintext_bytes = plaintext.encode("utf-8")
    keystream = _derive_keystream(key, nonce, len(plaintext_bytes))
    ciphertext = bytes(left ^ right for left, right in zip(plaintext_bytes, keystream, strict=True))
    tag = hmac.new(key.encode("utf-8"), nonce + ciphertext, hashlib.sha256).digest()
    return ".".join(_b64url_encode(part) for part in (nonce, ciphertext, tag))


def decrypt_secret(encrypted: str, key: str) -> str:
    try:
        nonce_text, ciphertext_text, tag_text = encrypted.split(".", 2)
        nonce = _b64url_decode(nonce_text)
        ciphertext = _b64url_decode(ciphertext_text)
        tag = _b64url_decode(tag_text)
    except ValueError as exc:
        raise AuthenticationError("Invalid protected secret", safe_detail="Invalid protected secret") from exc
    expected_tag = hmac.new(key.encode("utf-8"), nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected_tag):
        raise AuthenticationError("Invalid protected secret", safe_detail="Invalid protected secret")
    keystream = _derive_keystream(key, nonce, len(ciphertext))
    plaintext = bytes(left ^ right for left, right in zip(ciphertext, keystream, strict=True))
    return plaintext.decode("utf-8")


def utcnow() -> datetime:
    return datetime.now(UTC)


def expires_in(**kwargs: int) -> datetime:
    return utcnow() + timedelta(**kwargs)


def _totp_at_counter(secret: str, counter: int, digits: int) -> str:
    padded_secret = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded_secret, casefold=True)
    message = counter.to_bytes(8, "big")
    digest = hmac.new(key, message, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = int.from_bytes(digest[offset : offset + 4], "big") & 0x7FFFFFFF
    return str(binary % (10**digits)).zfill(digits)


def _derive_keystream(key: str, nonce: bytes, length: int) -> bytes:
    output = bytearray()
    block = 0
    while len(output) < length:
        output.extend(
            hmac.new(
                key.encode("utf-8"),
                nonce + block.to_bytes(4, "big"),
                hashlib.sha256,
            ).digest()
        )
        block += 1
    return bytes(output[:length])


def _sign(signing_input: str, secret: str) -> str:
    return _b64url_encode(hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest())


def _b64url_json(value: dict[str, Any]) -> str:
    return _b64url_encode(json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * ((4 - len(value) % 4) % 4))
