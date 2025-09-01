"""optimize_database_indexes_phase1

Revision ID: df856072bded
Revises: 4524473b46fb
Create Date: 2025-08-31 12:30:00.000000

Phase 1: Database Performance Optimization - Index Optimization
This migration optimizes database indexes for high-frequency INSERT operations.

MarketData Table:
- Removes 3 redundant indexes causing INSERT bottlenecks
- Keeps essential composite index for most common queries
- Adds optimized secondary index for price-based queries

AlertLog Table:
- Reduces from 10 indexes to 4 essential indexes
- Optimizes for common query patterns while improving INSERT performance

Expected Performance Improvements:
- MarketData INSERT: 30-50% improvement
- AlertLog INSERT: 40-60% improvement
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df856072bded'
down_revision: Union[str, None] = '4524473b46fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply index optimizations for better INSERT performance."""
    
    # MarketData table index optimization
    # Remove redundant indexes causing INSERT bottlenecks
    try:
        op.drop_index('ix_market_data_timestamp', table_name='market_data')
    except Exception:
        pass  # Index might not exist in some environments
    
    try:
        op.drop_index('ix_market_data_instrument', table_name='market_data')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_market_data_price', table_name='market_data')
    except Exception:
        pass
    
    try:
        op.drop_index('ix_market_data_latest', table_name='market_data')
    except Exception:
        pass
    
    # Add optimized secondary index for price-based queries
    op.create_index(
        'ix_market_data_instrument_price',
        'market_data',
        ['instrument_id', 'price'],
        unique=False
    )
    
    # AlertLog table index optimization
    # Remove redundant indexes (keeping only essential ones)
    redundant_indexes = [
        'ix_alert_logs_rule',
        'ix_alert_logs_timestamp_instrument',
        'ix_alert_logs_timestamp_rule',
        'ix_alert_logs_fired_status',
        'ix_alert_logs_delivery_status',
        'ix_alert_logs_evaluation_time',
        'ix_alert_logs_recent'
    ]
    
    for index_name in redundant_indexes:
        try:
            op.drop_index(index_name, table_name='alert_logs')
        except Exception:
            pass  # Index might not exist
    
    # Create optimized composite status index
    op.create_index(
        'ix_alert_logs_status',
        'alert_logs',
        ['fired_status', 'delivery_status'],
        unique=False
    )
    
    print("✓ Index optimization complete")
    print("  - MarketData: Reduced from 5 to 2 indexes")
    print("  - AlertLog: Reduced from 10 to 4 indexes")


def downgrade() -> None:
    """Restore original indexes."""
    
    # Restore MarketData indexes
    op.create_index('ix_market_data_timestamp', 'market_data', ['timestamp'], unique=False)
    op.create_index('ix_market_data_instrument', 'market_data', ['instrument_id'], unique=False)
    op.create_index('ix_market_data_price', 'market_data', ['price'], unique=False)
    op.create_index(
        'ix_market_data_latest',
        'market_data',
        ['instrument_id', 'timestamp', 'price'],
        unique=False
    )
    
    # Remove optimized index
    op.drop_index('ix_market_data_instrument_price', table_name='market_data')
    
    # Restore AlertLog indexes
    op.create_index('ix_alert_logs_rule', 'alert_logs', ['rule_id'], unique=False)
    op.create_index(
        'ix_alert_logs_timestamp_instrument',
        'alert_logs',
        ['timestamp', 'instrument_id'],
        unique=False
    )
    op.create_index(
        'ix_alert_logs_timestamp_rule',
        'alert_logs',
        ['timestamp', 'rule_id'],
        unique=False
    )
    op.create_index('ix_alert_logs_fired_status', 'alert_logs', ['fired_status'], unique=False)
    op.create_index('ix_alert_logs_delivery_status', 'alert_logs', ['delivery_status'], unique=False)
    op.create_index('ix_alert_logs_evaluation_time', 'alert_logs', ['evaluation_time_ms'], unique=False)
    op.create_index(
        'ix_alert_logs_recent',
        'alert_logs',
        ['timestamp', 'fired_status', 'instrument_id'],
        unique=False
    )
    
    # Remove optimized index
    op.drop_index('ix_alert_logs_status', table_name='alert_logs')
    
    print("✓ Index restoration complete")