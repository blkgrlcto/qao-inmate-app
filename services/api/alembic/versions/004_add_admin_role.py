"""Add 'admin' value to the userrole enum."""
from typing import Sequence, Union

from alembic import op

revision: str = "004_add_admin_role"
down_revision: Union[str, Sequence[str], None] = "003_federal_case_cache"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Must be the only statement touching the userrole type in this transaction —
    # Postgres won't let a new enum value be used in the same transaction it was added in.
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'admin'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enums; downgrading this migration is a no-op.
    # A real rollback would require recreating the type without 'admin'.
    pass
