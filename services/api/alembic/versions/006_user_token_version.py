"""Add token_version to users for JWT revocation."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_user_token_version"
down_revision: Union[str, Sequence[str], None] = "005_opinion_precedent_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("users", "token_version")
