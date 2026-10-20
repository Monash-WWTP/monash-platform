"""Append-only plant configuration provenance."""
from alembic import op
import sqlalchemy as sa

revision = 'e43b2c90ab01'
down_revision = 'd57267a1d090'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('plant_configuration_revisions',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('plant_id',sa.Integer(),sa.ForeignKey('plants.id'),nullable=False),
        sa.Column('version',sa.Integer(),nullable=False),
        sa.Column('actor_id',sa.String(36),sa.ForeignKey('accounts.id'),nullable=False),
        sa.Column('reason',sa.String(),nullable=False),
        sa.Column('payload',sa.JSON(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),
        sa.UniqueConstraint('plant_id','version'))
    op.create_index('ix_plant_configuration_revisions_plant_id','plant_configuration_revisions',['plant_id'])


def downgrade():
    op.drop_index('ix_plant_configuration_revisions_plant_id',table_name='plant_configuration_revisions')
    op.drop_table('plant_configuration_revisions')
