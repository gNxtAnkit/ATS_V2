# db/models/alembic_env_snippet.py
"""Copy this pattern into alembic/env.py.

The important part is importing db.models before reading Base.metadata,
because the import loads every domain model into the SQLAlchemy registry.
"""

from db.models import Base  # imports all model modules through db/models/__init__.py

target_metadata = Base.metadata
