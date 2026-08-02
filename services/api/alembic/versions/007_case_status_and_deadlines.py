"""Convert cases.status to a structured enum and add the deadlines table."""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_case_status_and_deadlines"
down_revision: Union[str, Sequence[str], None] = "006_user_token_version"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    case_status = postgresql.ENUM(
        "open", "active", "awaiting_decision", "closed", name="casestatus"
    )
    case_status.create(op.get_bind(), checkfirst=True)

    # Existing rows only ever contain "open" (the old free-text default),
    # which matches the new enum's value exactly, so a straight cast is safe.
    op.execute("ALTER TABLE cases ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE cases ALTER COLUMN status TYPE casestatus USING status::casestatus")
    op.execute("ALTER TABLE cases ALTER COLUMN status SET DEFAULT 'open'")

    op.create_table(
        "deadlines",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deadlines_case_id_due_date", "deadlines", ["case_id", "due_date"])


def downgrade() -> None:
    op.drop_index("ix_deadlines_case_id_due_date", table_name="deadlines")
    op.drop_table("deadlines")

    op.execute("ALTER TABLE cases ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE cases ALTER COLUMN status TYPE VARCHAR(50) USING status::text")
    op.execute("ALTER TABLE cases ALTER COLUMN status SET DEFAULT 'open'")
    op.execute("DROP TYPE IF EXISTS casestatus")
