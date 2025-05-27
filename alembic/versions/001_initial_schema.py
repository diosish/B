"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('telegram_id', sa.Integer(), nullable=False),
                    sa.Column('full_name', sa.String(length=255), nullable=False),
                    sa.Column('city', sa.String(length=100), nullable=True),
                    sa.Column('role', sa.String(length=20), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('is_active', sa.Boolean(), nullable=True),
                    sa.Column('volunteer_type', sa.String(length=50), nullable=True),
                    sa.Column('skills', sa.Text(), nullable=True),
                    sa.Column('resume', sa.Text(), nullable=True),
                    sa.Column('rating', sa.Float(), nullable=True),
                    sa.Column('org_type', sa.String(length=50), nullable=True),
                    sa.Column('org_name', sa.String(length=255), nullable=True),
                    sa.Column('inn', sa.String(length=20), nullable=True),
                    sa.Column('description', sa.Text(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('telegram_id')
                    )

    # Create events table
    op.create_table('events',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('title', sa.String(length=255), nullable=False),
                    sa.Column('description', sa.Text(), nullable=True),
                    sa.Column('city', sa.String(length=100), nullable=True),
                    sa.Column('date', sa.DateTime(), nullable=True),
                    sa.Column('duration', sa.Integer(), nullable=True),
                    sa.Column('payment', sa.Float(), nullable=True),
                    sa.Column('work_type', sa.String(length=50), nullable=True),
                    sa.Column('status', sa.String(length=20), nullable=True),
                    sa.Column('organizer_id', sa.Integer(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['organizer_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Create applications table
    op.create_table('applications',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=True),
                    sa.Column('volunteer_id', sa.Integer(), nullable=True),
                    sa.Column('status', sa.String(length=20), nullable=True),
                    sa.Column('applied_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
                    sa.ForeignKeyConstraint(['volunteer_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Create reviews table
    op.create_table('reviews',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=True),
                    sa.Column('volunteer_id', sa.Integer(), nullable=True),
                    sa.Column('organizer_id', sa.Integer(), nullable=True),
                    sa.Column('rating', sa.Integer(), nullable=True),
                    sa.Column('comment', sa.Text(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
                    sa.ForeignKeyConstraint(['organizer_id'], ['users.id'], ),
                    sa.ForeignKeyConstraint(['volunteer_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Create indexes
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)
    op.create_index(op.f('ix_events_organizer_id'), 'events', ['organizer_id'], unique=False)
    op.create_index(op.f('ix_events_status'), 'events', ['status'], unique=False)
    op.create_index(op.f('ix_applications_event_id'), 'applications', ['event_id'], unique=False)
    op.create_index(op.f('ix_applications_volunteer_id'), 'applications', ['volunteer_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_applications_volunteer_id'), table_name='applications')
    op.drop_index(op.f('ix_applications_event_id'), table_name='applications')
    op.drop_index(op.f('ix_events_status'), table_name='events')
    op.drop_index(op.f('ix_events_organizer_id'), table_name='events')
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')

    op.drop_table('reviews')
    op.drop_table('applications')
    op.drop_table('events')
    op.drop_table('users')