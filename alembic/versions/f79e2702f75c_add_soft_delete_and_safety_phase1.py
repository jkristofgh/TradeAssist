"""add_soft_delete_and_safety_phase1

Revision ID: f79e2702f75c
Revises: 4a24cf1de90a
Create Date: 2025-08-31 12:35:00.000000

Phase 1: Database Performance Optimization - Soft Delete & Referential Integrity
This migration adds soft delete capability and updates foreign key constraints for safety.

Changes:
- Adds deleted_at columns to MarketData and AlertLog tables
- Updates foreign key constraints from CASCADE to RESTRICT (where supported)
- Creates indexes on deleted_at columns for query performance

Note: SQLite doesn't support altering foreign key constraints directly,
so CASCADE to RESTRICT changes are documented but require table recreation.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f79e2702f75c'
down_revision: Union[str, None] = '4a24cf1de90a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add soft delete columns and update referential integrity."""
    
    # Add deleted_at column to market_data table
    op.add_column('market_data', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_index('ix_market_data_deleted_at', 'market_data', ['deleted_at'], unique=False)
    
    # Add deleted_at column to alert_logs table
    op.add_column('alert_logs', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.create_index('ix_alert_logs_deleted_at', 'alert_logs', ['deleted_at'], unique=False)
    
    # Note: Foreign key constraint updates from CASCADE to RESTRICT
    # SQLite doesn't support altering foreign key constraints directly
    # For production migration to non-SQLite databases, the following would be used:
    
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    if dialect_name != 'sqlite':
        # For PostgreSQL, MySQL, etc. - Update foreign key constraints
        # MarketData table
        op.drop_constraint('fk_market_data_instrument_id', 'market_data', type_='foreignkey')
        op.create_foreign_key(
            'fk_market_data_instrument_id',
            'market_data',
            'instruments',
            ['instrument_id'],
            ['id'],
            ondelete='RESTRICT'
        )
        
        # AlertLog table
        op.drop_constraint('fk_alert_logs_rule_id', 'alert_logs', type_='foreignkey')
        op.create_foreign_key(
            'fk_alert_logs_rule_id',
            'alert_logs',
            'alert_rules',
            ['rule_id'],
            ['id'],
            ondelete='RESTRICT'
        )
        
        op.drop_constraint('fk_alert_logs_instrument_id', 'alert_logs', type_='foreignkey')
        op.create_foreign_key(
            'fk_alert_logs_instrument_id',
            'alert_logs',
            'instruments',
            ['instrument_id'],
            ['id'],
            ondelete='RESTRICT'
        )
    else:
        # For SQLite, document the constraint changes
        print("⚠ SQLite detected: Foreign key constraints cannot be altered directly.")
        print("  To apply RESTRICT constraints, tables would need to be recreated.")
        print("  Current CASCADE behavior will continue in SQLite.")
    
    print("✓ Soft delete functionality added")
    print("  - MarketData: deleted_at column and index added")
    print("  - AlertLog: deleted_at column and index added")
    if dialect_name != 'sqlite':
        print("  - Foreign key constraints updated to RESTRICT")


def downgrade() -> None:
    """Remove soft delete columns and restore CASCADE constraints."""
    
    # Remove indexes first
    op.drop_index('ix_market_data_deleted_at', table_name='market_data')
    op.drop_index('ix_alert_logs_deleted_at', table_name='alert_logs')
    
    # Remove deleted_at columns
    op.drop_column('market_data', 'deleted_at')
    op.drop_column('alert_logs', 'deleted_at')
    
    # Restore CASCADE constraints (for non-SQLite databases)
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    if dialect_name != 'sqlite':
        # MarketData table
        op.drop_constraint('fk_market_data_instrument_id', 'market_data', type_='foreignkey')
        op.create_foreign_key(
            'fk_market_data_instrument_id',
            'market_data',
            'instruments',
            ['instrument_id'],
            ['id'],
            ondelete='CASCADE'
        )
        
        # AlertLog table
        op.drop_constraint('fk_alert_logs_rule_id', 'alert_logs', type_='foreignkey')
        op.create_foreign_key(
            'fk_alert_logs_rule_id',
            'alert_logs',
            'alert_rules',
            ['rule_id'],
            ['id'],
            ondelete='CASCADE'
        )
        
        op.drop_constraint('fk_alert_logs_instrument_id', 'alert_logs', type_='foreignkey')
        op.create_foreign_key(
            'fk_alert_logs_instrument_id',
            'alert_logs',
            'instruments',
            ['instrument_id'],
            ['id'],
            ondelete='CASCADE'
        )
    
    print("✓ Soft delete functionality removed")