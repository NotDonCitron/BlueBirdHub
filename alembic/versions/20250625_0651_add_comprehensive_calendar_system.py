"""add_comprehensive_calendar_system

Revision ID: 20250625_0651_calendar
Revises: 879fb5a39b2f
Create Date: 2025-06-25 06:51:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '20250625_0651_calendar'
down_revision = '879fb5a39b2f'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create calendar_integrations table
    op.create_table('calendar_integrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.Enum('GOOGLE', 'MICROSOFT', 'APPLE', 'INTERNAL', name='calendarprovider'), nullable=False),
        sa.Column('provider_user_id', sa.String(255), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scope', sa.String(500), nullable=True),
        sa.Column('settings', sa.VARCHAR(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CONFLICT', name='syncstatus'), nullable=True),
        sa.Column('sync_error_message', sa.Text(), nullable=True),
        sa.Column('webhook_url', sa.String(500), nullable=True),
        sa.Column('webhook_token', sa.String(255), nullable=True),
        sa.Column('webhook_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'provider', name='uix_user_provider')
    )
    op.create_index(op.f('ix_calendar_integrations_id'), 'calendar_integrations', ['id'], unique=False)

    # Create calendars table
    op.create_table('calendars',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('provider', sa.Enum('GOOGLE', 'MICROSOFT', 'APPLE', 'INTERNAL', name='calendarprovider'), nullable=True),
        sa.Column('external_calendar_id', sa.String(255), nullable=True),
        sa.Column('integration_id', sa.Integer(), nullable=True),
        sa.Column('auto_sync_enabled', sa.Boolean(), nullable=True),
        sa.Column('sync_interval_minutes', sa.Integer(), nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_token', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['calendar_integrations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendars_id'), 'calendars', ['id'], unique=False)

    # Create calendar_events table
    op.create_table('calendar_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('calendar_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(500), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('is_all_day', sa.Boolean(), nullable=True),
        sa.Column('status', sa.Enum('CONFIRMED', 'TENTATIVE', 'CANCELLED', name='calendareventstatus'), nullable=True),
        sa.Column('visibility', sa.Enum('DEFAULT', 'PUBLIC', 'PRIVATE', 'CONFIDENTIAL', name='calendareventvisibility'), nullable=True),
        sa.Column('recurrence_type', sa.Enum('NONE', 'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY', 'CUSTOM', name='calendareventrecurrencetype'), nullable=True),
        sa.Column('recurrence_rule', sa.Text(), nullable=True),
        sa.Column('recurrence_end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recurrence_count', sa.Integer(), nullable=True),
        sa.Column('is_recurring_instance', sa.Boolean(), nullable=True),
        sa.Column('recurring_event_id', sa.Integer(), nullable=True),
        sa.Column('external_event_id', sa.String(255), nullable=True),
        sa.Column('external_sync_token', sa.String(255), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CONFLICT', name='syncstatus'), nullable=True),
        sa.Column('meeting_url', sa.String(500), nullable=True),
        sa.Column('meeting_phone', sa.String(50), nullable=True),
        sa.Column('meeting_passcode', sa.String(50), nullable=True),
        sa.Column('reminders', sa.VARCHAR(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['calendar_id'], ['calendars.id'], ),
        sa.ForeignKeyConstraint(['recurring_event_id'], ['calendar_events.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendar_events_id'), 'calendar_events', ['id'], unique=False)

    # Create calendar_event_attendees table
    op.create_table('calendar_event_attendees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(200), nullable=True),
        sa.Column('response_status', sa.String(20), nullable=True),
        sa.Column('is_organizer', sa.Boolean(), nullable=True),
        sa.Column('is_resource', sa.Boolean(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['calendar_events.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendar_event_attendees_id'), 'calendar_event_attendees', ['id'], unique=False)

    # Create calendar_shares table
    op.create_table('calendar_shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('calendar_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('shared_by_user_id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=True),
        sa.Column('permission', sa.Enum('READ', 'WRITE', 'ADMIN', name='calendarsharepermission'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['calendar_id'], ['calendars.id'], ),
        sa.ForeignKeyConstraint(['shared_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('calendar_id', 'user_id', name='uix_calendar_user_share')
    )
    op.create_index(op.f('ix_calendar_shares_id'), 'calendar_shares', ['id'], unique=False)

    # Create calendar_conflicts table
    op.create_table('calendar_conflicts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event1_id', sa.Integer(), nullable=False),
        sa.Column('event2_id', sa.Integer(), nullable=False),
        sa.Column('conflict_type', sa.String(50), nullable=True),
        sa.Column('severity', sa.String(20), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=True),
        sa.Column('resolution_type', sa.String(50), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_by_user_id', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['event1_id'], ['calendar_events.id'], ),
        sa.ForeignKeyConstraint(['event2_id'], ['calendar_events.id'], ),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendar_conflicts_id'), 'calendar_conflicts', ['id'], unique=False)

    # Create calendar_sync_logs table
    op.create_table('calendar_sync_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('calendar_id', sa.Integer(), nullable=False),
        sa.Column('integration_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('sync_type', sa.String(50), nullable=True),
        sa.Column('direction', sa.String(20), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CONFLICT', name='syncstatus'), nullable=True),
        sa.Column('events_processed', sa.Integer(), nullable=True),
        sa.Column('events_created', sa.Integer(), nullable=True),
        sa.Column('events_updated', sa.Integer(), nullable=True),
        sa.Column('events_deleted', sa.Integer(), nullable=True),
        sa.Column('conflicts_detected', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.VARCHAR(), nullable=True),
        sa.ForeignKeyConstraint(['calendar_id'], ['calendars.id'], ),
        sa.ForeignKeyConstraint(['integration_id'], ['calendar_integrations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendar_sync_logs_id'), 'calendar_sync_logs', ['id'], unique=False)

    # Create time_blocks table
    op.create_table('time_blocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('calendar_id', sa.Integer(), nullable=True),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('block_type', sa.String(50), nullable=True),
        sa.Column('is_flexible', sa.Boolean(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), nullable=True),
        sa.Column('recurrence_rule', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['calendar_id'], ['calendars.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_time_blocks_id'), 'time_blocks', ['id'], unique=False)

    # Set default values for new columns
    op.execute("UPDATE calendar_integrations SET sync_status = 'PENDING' WHERE sync_status IS NULL")
    op.execute("UPDATE calendar_integrations SET is_active = 1 WHERE is_active IS NULL")
    
    op.execute("UPDATE calendars SET provider = 'INTERNAL' WHERE provider IS NULL")
    op.execute("UPDATE calendars SET timezone = 'UTC' WHERE timezone IS NULL")
    op.execute("UPDATE calendars SET is_active = 1 WHERE is_active IS NULL")
    op.execute("UPDATE calendars SET is_primary = 0 WHERE is_primary IS NULL")
    op.execute("UPDATE calendars SET is_public = 0 WHERE is_public IS NULL")
    op.execute("UPDATE calendars SET auto_sync_enabled = 1 WHERE auto_sync_enabled IS NULL")
    op.execute("UPDATE calendars SET sync_interval_minutes = 15 WHERE sync_interval_minutes IS NULL")
    
    op.execute("UPDATE calendar_events SET timezone = 'UTC' WHERE timezone IS NULL")
    op.execute("UPDATE calendar_events SET is_all_day = 0 WHERE is_all_day IS NULL")
    op.execute("UPDATE calendar_events SET status = 'CONFIRMED' WHERE status IS NULL")
    op.execute("UPDATE calendar_events SET visibility = 'DEFAULT' WHERE visibility IS NULL")
    op.execute("UPDATE calendar_events SET recurrence_type = 'NONE' WHERE recurrence_type IS NULL")
    op.execute("UPDATE calendar_events SET is_recurring_instance = 0 WHERE is_recurring_instance IS NULL")
    op.execute("UPDATE calendar_events SET sync_status = 'PENDING' WHERE sync_status IS NULL")
    
    op.execute("UPDATE calendar_event_attendees SET response_status = 'needsAction' WHERE response_status IS NULL")
    op.execute("UPDATE calendar_event_attendees SET is_organizer = 0 WHERE is_organizer IS NULL")
    op.execute("UPDATE calendar_event_attendees SET is_resource = 0 WHERE is_resource IS NULL")
    
    op.execute("UPDATE calendar_shares SET permission = 'READ' WHERE permission IS NULL")
    op.execute("UPDATE calendar_shares SET is_active = 1 WHERE is_active IS NULL")
    
    op.execute("UPDATE calendar_conflicts SET severity = 'medium' WHERE severity IS NULL")
    op.execute("UPDATE calendar_conflicts SET is_resolved = 0 WHERE is_resolved IS NULL")
    
    op.execute("UPDATE calendar_sync_logs SET events_processed = 0 WHERE events_processed IS NULL")
    op.execute("UPDATE calendar_sync_logs SET events_created = 0 WHERE events_created IS NULL")
    op.execute("UPDATE calendar_sync_logs SET events_updated = 0 WHERE events_updated IS NULL")
    op.execute("UPDATE calendar_sync_logs SET events_deleted = 0 WHERE events_deleted IS NULL")
    op.execute("UPDATE calendar_sync_logs SET conflicts_detected = 0 WHERE conflicts_detected IS NULL")
    
    op.execute("UPDATE time_blocks SET timezone = 'UTC' WHERE timezone IS NULL")
    op.execute("UPDATE time_blocks SET block_type = 'work' WHERE block_type IS NULL")
    op.execute("UPDATE time_blocks SET is_flexible = 0 WHERE is_flexible IS NULL")
    op.execute("UPDATE time_blocks SET priority = 50 WHERE priority IS NULL")
    op.execute("UPDATE time_blocks SET is_recurring = 0 WHERE is_recurring IS NULL")


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_index(op.f('ix_time_blocks_id'), table_name='time_blocks')
    op.drop_table('time_blocks')
    
    op.drop_index(op.f('ix_calendar_sync_logs_id'), table_name='calendar_sync_logs')
    op.drop_table('calendar_sync_logs')
    
    op.drop_index(op.f('ix_calendar_conflicts_id'), table_name='calendar_conflicts')
    op.drop_table('calendar_conflicts')
    
    op.drop_index(op.f('ix_calendar_shares_id'), table_name='calendar_shares')
    op.drop_table('calendar_shares')
    
    op.drop_index(op.f('ix_calendar_event_attendees_id'), table_name='calendar_event_attendees')
    op.drop_table('calendar_event_attendees')
    
    op.drop_index(op.f('ix_calendar_events_id'), table_name='calendar_events')
    op.drop_table('calendar_events')
    
    op.drop_index(op.f('ix_calendars_id'), table_name='calendars')
    op.drop_table('calendars')
    
    op.drop_index(op.f('ix_calendar_integrations_id'), table_name='calendar_integrations')
    op.drop_table('calendar_integrations')
    
    # Drop custom enum types (SQLite doesn't need this, but other DBs might)
    op.execute("DROP TYPE IF EXISTS calendarprovider")
    op.execute("DROP TYPE IF EXISTS calendareventstatus")
    op.execute("DROP TYPE IF EXISTS calendareventvisibility")
    op.execute("DROP TYPE IF EXISTS calendareventrecurrencetype")
    op.execute("DROP TYPE IF EXISTS calendarsharepermission")
    op.execute("DROP TYPE IF EXISTS syncstatus")