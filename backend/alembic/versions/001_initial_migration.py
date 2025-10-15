"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable required PostgreSQL extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "unaccent"')
    
    # Create users table
    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('role', sa.Enum('admin', 'user', name='userrole'), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create audits table
    op.create_table('audits',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('action', sa.Enum('login', 'logout', 'upload', 'download', 'search', 'user_create', 'user_update', 'user_delete', 'password_reset', name='auditaction'), nullable=False),
    sa.Column('doc_id', sa.String(length=255), nullable=True),
    sa.Column('doc_title', sa.Text(), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('details', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audits_doc_id'), 'audits', ['doc_id'], unique=False)
    
    # Create search_helpers table
    op.create_table('search_helpers',
    sa.Column('doc_id', sa.String(length=255), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('normalized_text', postgresql.TSVECTOR(), nullable=True),
    sa.Column('enumbers', postgresql.ARRAY(sa.String()), nullable=False),
    sa.Column('normalized_title', sa.Text(), nullable=True),
    sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('doc_id')
    )
    op.create_index('ix_search_helpers_normalized_text', 'search_helpers', ['normalized_text'], unique=False, postgresql_using='gin')
    op.create_index('ix_search_helpers_enumbers', 'search_helpers', ['enumbers'], unique=False, postgresql_using='gin')
    op.create_index('ix_search_helpers_normalized_title', 'search_helpers', ['normalized_title'], unique=False, postgresql_using='gin')
    op.create_index('ix_search_helpers_last_seen', 'search_helpers', ['last_seen_at'], unique=False)
    
    # Create settings table
    op.create_table('settings',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('paperless_base_url', sa.String(length=500), nullable=True),
    sa.Column('paperless_api_token', sa.Text(), nullable=True),
    sa.Column('allow_self_signup', sa.Boolean(), nullable=False),
    sa.Column('max_upload_mb', sa.String(length=10), nullable=False),
    sa.Column('session_timeout_hours', sa.String(length=5), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('settings')
    op.drop_index('ix_search_helpers_last_seen', table_name='search_helpers')
    op.drop_index('ix_search_helpers_normalized_title', table_name='search_helpers')
    op.drop_index('ix_search_helpers_enumbers', table_name='search_helpers')
    op.drop_index('ix_search_helpers_normalized_text', table_name='search_helpers')
    op.drop_table('search_helpers')
    op.drop_index(op.f('ix_audits_doc_id'), table_name='audits')
    op.drop_table('audits')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
