"""Add updated_at field to users table

Revision ID: 003
Revises: 002
Create Date: 2025-05-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем поле updated_at в таблицу users
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # Устанавливаем значение по умолчанию для существующих записей равным created_at
    op.execute("UPDATE users SET updated_at = created_at WHERE updated_at IS NULL")


def downgrade() -> None:
    # Удаляем поле updated_at
    op.drop_column('users', 'updated_at')