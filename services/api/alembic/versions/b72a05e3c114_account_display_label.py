"""Optional signed-claim label with monotonic claim provenance."""

from alembic import op
import sqlalchemy as sa

revision = "b72a05e3c114"
down_revision = "a61c84b0e921"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("accounts", sa.Column("display_name", sa.String(120), nullable=True))
    op.add_column(
        "accounts", sa.Column("profile_claim_iat", sa.BigInteger(), nullable=True)
    )


def downgrade():
    op.drop_column("accounts", "profile_claim_iat")
    op.drop_column("accounts", "display_name")
