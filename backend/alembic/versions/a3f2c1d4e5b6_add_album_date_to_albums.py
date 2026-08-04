"""add album_date to albums

Revision ID: a3f2c1d4e5b6
Revises: 28a1588f7b74
Create Date: 2026-08-02

"""
from alembic import op
import sqlalchemy as sa

revision = 'a3f2c1d4e5b6'
down_revision = '28a1588f7b74'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('albums', sa.Column('album_date', sa.Date(), nullable=True))


def downgrade():
    op.drop_column('albums', 'album_date')
