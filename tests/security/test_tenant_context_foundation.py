from uuid import uuid4

from gnxthire_common.context import ActorType, RequestContext
from gnxthire_common.rls import require_tenant_context


def test_tenant_user_database_path_requires_tenant_context() -> None:
    context = RequestContext(
        request_id="req_tenant",
        tenant_id=uuid4(),
        actor_id=uuid4(),
        actor_type=ActorType.TENANT_USER,
    )

    require_tenant_context(context)
