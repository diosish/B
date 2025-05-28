"""Fix telegram_id to BigInteger

Revision ID: 002
Revises: 001
Create Date: 2025-05-28 13:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Изменяем тип telegram_id с integer на bigint
    op.alter_column('users', 'telegram_id',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)


def downgrade() -> None:
    # Возвращаем обратно к integer (может привести к потере данных если есть большие ID)
    op.alter_column('users', 'telegram_id',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=False)