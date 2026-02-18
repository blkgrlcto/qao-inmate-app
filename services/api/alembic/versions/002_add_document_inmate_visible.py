"""Add inmate_visible to documents."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_add_document_inmate_visible"
down_revision: Union[str, Sequence[str], None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("inmate_visible", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("documents", "inmate_visible")
