from __future__ import annotations

import logging

from gnxthire_identity.config import get_identity_settings
from gnxthire_identity.email import CapturingEmailSender
from gnxthire_identity.rate_limit import MemoryRateLimiter
from gnxthire_identity.request_metadata import RequestMetadata
from gnxthire_identity.tenant.repository import TenantIdentityRepository
from gnxthire_identity.tenant.service import TenantIdentityService

METADATA = RequestMetadata(request_id="test-request", correlation_id=None, ip_address="127.0.0.1", user_agent="pytest")


def test_login_and_reset_flow_never_logs_raw_secrets(caplog, db_engine, seed_tenant, seed_tenant_user) -> None:
    from sqlalchemy.orm import sessionmaker

    session = sessionmaker(bind=db_engine, expire_on_commit=False, future=True)()
    sender = CapturingEmailSender()
    service = TenantIdentityService(
        repository=TenantIdentityRepository(session),
        settings=get_identity_settings(),
        email_sender=sender,
        rate_limiter=MemoryRateLimiter(),
    )
    tenant_id = seed_tenant()
    password = "Sup3rS3cretPassword!"
    email = seed_tenant_user(tenant_id=tenant_id, password=password)

    with caplog.at_level(logging.DEBUG):
        service.login(email=email, password=password, metadata=METADATA)
        service.forgot_password(email=email, metadata=METADATA)

    session.commit()
    session.close()

    raw_reset_token = sender.messages[0].text_body.rsplit("token=", 1)[1]
    log_text = "\n".join(record.getMessage() for record in caplog.records)

    assert password not in log_text
    assert raw_reset_token not in log_text
