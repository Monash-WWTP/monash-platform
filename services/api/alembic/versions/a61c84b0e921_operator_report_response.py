"""Private operator response state and append-only events."""

from alembic import op
import sqlalchemy as sa

revision = "a61c84b0e921"
down_revision = "e43b2c90ab01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "report_responses",
        sa.Column(
            "report_id",
            sa.String(36),
            sa.ForeignKey("citizen_reports.id"),
            primary_key=True,
        ),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("assignee_id", sa.String(36), sa.ForeignKey("accounts.id")),
        sa.Column("plant_id", sa.Integer(), sa.ForeignKey("plants.id")),
        sa.Column(
            "station_code", sa.String(), sa.ForeignKey("monitoring_stations.code")
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "report_response_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "report_id",
            sa.String(36),
            sa.ForeignKey("citizen_reports.id"),
            nullable=False,
        ),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column(
            "actor_id", sa.String(36), sa.ForeignKey("accounts.id"), nullable=False
        ),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("report_id", "revision"),
    )
    op.create_index(
        "ix_report_response_events_report_id", "report_response_events", ["report_id"]
    )


def downgrade():
    op.drop_index(
        "ix_report_response_events_report_id", table_name="report_response_events"
    )
    op.drop_table("report_response_events")
    op.drop_table("report_responses")
