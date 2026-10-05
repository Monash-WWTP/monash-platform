"""Persist native credential recovery revocation boundary."""

from alembic import op
import sqlalchemy as sa

revision = "d57267a1d090"
down_revision = "c04995eb0733"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "accounts",
        sa.Column("revoked_before", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("accounts", "revoked_before")
