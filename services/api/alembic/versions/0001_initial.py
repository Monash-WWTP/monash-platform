"""Initial scenario and simulation schema.

Revision ID: 0001_initial
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("capacity_mld", sa.Float(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("stp_type", sa.String(), nullable=False),
        sa.Column("ef_ch4", sa.Float(), nullable=False),
        sa.Column("ef_n2o", sa.Float(), nullable=False),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "plant_units",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plant_id", sa.Integer(), sa.ForeignKey("plants.id"), nullable=False),
        sa.Column("unit_type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("baseline_availability", sa.Float(), nullable=False),
    )
    op.create_table(
        "compliance_limits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plant_id", sa.Integer(), sa.ForeignKey("plants.id"), nullable=False),
        sa.Column("metric", sa.String(), nullable=False),
        sa.Column("limit_value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
    )
    op.create_table(
        "scenarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plant_id", sa.Integer(), sa.ForeignKey("plants.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("horizon", sa.String(), nullable=False),
        sa.Column("forecast", sa.JSON(), nullable=False),
        sa.Column("maintenance", sa.JSON(), nullable=False),
        sa.Column("operating_parameters", sa.JSON(), nullable=False),
        sa.Column("is_baseline", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scenario_id", sa.Integer(), sa.ForeignKey("scenarios.id"), nullable=False),
        sa.Column("model_id", sa.String(), nullable=False),
        sa.Column("model_version", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("kpis", sa.JSON(), nullable=False),
        sa.Column("exceedances", sa.JSON(), nullable=False),
        sa.Column("timeseries", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("simulation_runs")
    op.drop_table("scenarios")
    op.drop_table("compliance_limits")
    op.drop_table("plant_units")
    op.drop_table("plants")
