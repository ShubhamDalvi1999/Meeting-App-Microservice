"""Initial schema

Revision ID: initial_schema
Revises: None
Create Date: 2024-01-09 02:35:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic
revision = 'initial_schema'
down_revision = None

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(120), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(128), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        
        # Security fields
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('email_verification_token', sa.String(100), nullable=True),
        sa.Column('email_verification_sent_at', sa.DateTime(), nullable=True),
        sa.Column('password_reset_token', sa.String(100), nullable=True),
        sa.Column('password_reset_sent_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('last_password_change', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login_ip', sa.String(45), nullable=True),
        sa.Column('login_count', sa.Integer(), nullable=False, server_default='0'),
        
        # User preferences
        sa.Column('preferences', JSONB(), nullable=False, server_default='{}'),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('name')
    )

    # Create meetings table
    op.create_table(
        'meetings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('meeting_type', sa.String(20), nullable=False, server_default='regular'),
        sa.Column('max_participants', sa.Integer(), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_recorded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('recording_url', sa.String(500), nullable=True),
        sa.Column('recurring_pattern', sa.String(50), nullable=True),
        sa.Column('parent_meeting_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_meeting_id'], ['meetings.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create meeting_participants table
    op.create_table(
        'meeting_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meeting_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('role', sa.String(20), nullable=False, server_default='attendee'),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.Column('is_banned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('total_time', sa.Integer(), nullable=True),
        sa.Column('connection_quality', sa.Float(), nullable=True),
        sa.Column('participation_score', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create meeting_co_hosts table
    op.create_table(
        'meeting_co_hosts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meeting_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('meeting_id', 'user_id', name='uq_meeting_co_hosts')
    )

    # Create meeting_audit_logs table
    op.create_table(
        'meeting_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meeting_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('details', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_name', 'users', ['name'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_is_email_verified', 'users', ['is_email_verified'])
    op.create_index('idx_users_email_verification_token', 'users', ['email_verification_token'])
    op.create_index('idx_users_password_reset_token', 'users', ['password_reset_token'])
    op.create_index('idx_users_preferences', 'users', ['preferences'], postgresql_using='gin')

    op.create_index('idx_meetings_created_by', 'meetings', ['created_by'])
    op.create_index('idx_meetings_start_time', 'meetings', ['start_time'])
    op.create_index('idx_meetings_end_time', 'meetings', ['end_time'])
    op.create_index('idx_meetings_meeting_type', 'meetings', ['meeting_type'])
    op.create_index('idx_meetings_parent_id', 'meetings', ['parent_meeting_id'])

    op.create_index('idx_meeting_participants_meeting_id', 'meeting_participants', ['meeting_id'])
    op.create_index('idx_meeting_participants_user_id', 'meeting_participants', ['user_id'])
    op.create_index('idx_meeting_participants_status', 'meeting_participants', ['status'])

    op.create_index('idx_meeting_co_hosts_meeting_id', 'meeting_co_hosts', ['meeting_id'])
    op.create_index('idx_meeting_co_hosts_user_id', 'meeting_co_hosts', ['user_id'])

    op.create_index('idx_meeting_audit_logs_meeting_id', 'meeting_audit_logs', ['meeting_id'])
    op.create_index('idx_meeting_audit_logs_user_id', 'meeting_audit_logs', ['user_id'])
    op.create_index('idx_meeting_audit_logs_created_at', 'meeting_audit_logs', ['created_at'])

def downgrade():
    # Drop indexes first
    op.drop_index('idx_meeting_audit_logs_created_at')
    op.drop_index('idx_meeting_audit_logs_user_id')
    op.drop_index('idx_meeting_audit_logs_meeting_id')
    op.drop_index('idx_meeting_co_hosts_user_id')
    op.drop_index('idx_meeting_co_hosts_meeting_id')
    op.drop_index('idx_meeting_participants_status')
    op.drop_index('idx_meeting_participants_user_id')
    op.drop_index('idx_meeting_participants_meeting_id')
    op.drop_index('idx_meetings_parent_id')
    op.drop_index('idx_meetings_meeting_type')
    op.drop_index('idx_meetings_end_time')
    op.drop_index('idx_meetings_start_time')
    op.drop_index('idx_meetings_created_by')
    op.drop_index('idx_users_preferences')
    op.drop_index('idx_users_password_reset_token')
    op.drop_index('idx_users_email_verification_token')
    op.drop_index('idx_users_is_email_verified')
    op.drop_index('idx_users_is_active')
    op.drop_index('idx_users_name')
    op.drop_index('idx_users_email')

    # Drop tables
    op.drop_table('meeting_audit_logs')
    op.drop_table('meeting_co_hosts')
    op.drop_table('meeting_participants')
    op.drop_table('meetings')
    op.drop_table('users') 