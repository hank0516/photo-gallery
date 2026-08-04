"""add mime_type to photos and make thumb keys nullable

Revision ID: b1c2d3e4f5a6
Revises: 1757d9a7d069
Create Date: 2026-08-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = '1757d9a7d069'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('photos', sa.Column('mime_type', sa.String(length=100), nullable=True))
    op.alter_column('photos', 'thumb_300_key', existing_type=sa.String(length=1024), nullable=True)
    op.alter_column('photos', 'thumb_800_key', existing_type=sa.String(length=1024), nullable=True)


def downgrade() -> None:
    op.alter_column('photos', 'thumb_800_key', existing_type=sa.String(length=1024), nullable=False)
    op.alter_column('photos', 'thumb_300_key', existing_type=sa.String(length=1024), nullable=False)
    op.drop_column('photos', 'mime_type')
