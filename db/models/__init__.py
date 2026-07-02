# db/models/__init__.py
"""Central SQLAlchemy model registry for Alembic autogenerate.

Import this package in alembic/env.py before using Base.metadata.
"""

from .core import Base

# Import every mapped model so Alembic can discover the full metadata.
from .platform import *  # noqa: F401,F403,E402
from .tenant import *  # noqa: F401,F403,E402
from .candidates import *  # noqa: F401,F403,E402
from .corporate import *  # noqa: F401,F403,E402
from .agency import *  # noqa: F401,F403,E402
from .workflow import *  # noqa: F401,F403,E402
from .ai import *  # noqa: F401,F403,E402
from .integrations import *  # noqa: F401,F403,E402
from .billing import *  # noqa: F401,F403,E402
from .analytics import *  # noqa: F401,F403,E402

__all__ = ["Base"]
