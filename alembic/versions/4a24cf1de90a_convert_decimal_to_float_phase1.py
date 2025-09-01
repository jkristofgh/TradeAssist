"""convert_decimal_to_float_phase1

Revision ID: 4a24cf1de90a
Revises: df856072bded
Create Date: 2025-08-31 12:32:00.000000

Phase 1: Database Performance Optimization - Data Type Conversion
This migration converts DECIMAL columns to FLOAT for improved calculation performance.

MarketData Table:
- Converts price, bid, ask, open_price, high_price, low_price from DECIMAL(12,4) to FLOAT
- Expected 2-3x calculation speed improvement

AlertLog Table:
- Converts trigger_value, threshold_value from DECIMAL(12,4) to FLOAT
- Improves alert evaluation performance

Note: API responses will maintain 4-decimal precision through application layer validation.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = '4a24cf1de90a'
down_revision: Union[str, None] = 'df856072bded'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert DECIMAL columns to FLOAT for better performance."""
    
    # Note: SQLite doesn't support ALTER COLUMN directly
    # We need to check if we're using SQLite or another database
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    if dialect_name == 'sqlite':
        # SQLite requires special handling - recreate tables with new column types
        # For SQLite, we'll use batch operations
        
        # Convert MarketData table columns
        with op.batch_alter_table('market_data', schema=None) as batch_op:
            batch_op.alter_column('price',
                                existing_type=sa.DECIMAL(precision=12, scale=4),
                                type_=sa.Float(),
                                existing_nullable=True)
            batch_op.alter_column('bid',
                                existing_type=sa.DECIMAL(precision=12, scale=4),
                                type_=sa.Float(),
                                existing_nullable=True)
            batch_op.alter_column('ask',
                                existing_type=sa.DECIMAL(precision=12, scale=4),
                                type_=sa.Float(),
                                existing_nullable=True)
            batch_op.alter_column('open_price',
                                existing_type=sa.DECIMAL(precision=12, scale=4),
                                type_=sa.Float(),
                                existing_nullable=True)
            batch_op.alter_column('high_price',
                                existing_type=sa.DECIMAL(precision=12, scale=4),
                                type_=sa.Float(),
                                existing_nullable=True)
            batch_op.alter_column('low_price',
                                existing_type=sa.DECIMAL(precision=12, scale=4),
                                type_=sa.Float(),
                                existing_nullable=True)
        
        # Convert AlertLog table columns
        with op.batch_alter_table('alert_logs', schema=None) as batch_op:
            batch_op.alter_column('trigger_value',
                                existing_type=sa.DECIMAL(precision=12, scale=4),
                                type_=sa.Float(),
                                existing_nullable=False)
            batch_op.alter_column('threshold_value',
                                existing_type=sa.DECIMAL(precision=12, scale=4),
                                type_=sa.Float(),
                                existing_nullable=False)
    else:
        # For PostgreSQL, MySQL, etc. - direct ALTER COLUMN
        # MarketData table
        op.alter_column('market_data', 'price',
                       existing_type=sa.DECIMAL(precision=12, scale=4),
                       type_=sa.Float(),
                       existing_nullable=True)
        op.alter_column('market_data', 'bid',
                       existing_type=sa.DECIMAL(precision=12, scale=4),
                       type_=sa.Float(),
                       existing_nullable=True)
        op.alter_column('market_data', 'ask',
                       existing_type=sa.DECIMAL(precision=12, scale=4),
                       type_=sa.Float(),
                       existing_nullable=True)
        op.alter_column('market_data', 'open_price',
                       existing_type=sa.DECIMAL(precision=12, scale=4),
                       type_=sa.Float(),
                       existing_nullable=True)
        op.alter_column('market_data', 'high_price',
                       existing_type=sa.DECIMAL(precision=12, scale=4),
                       type_=sa.Float(),
                       existing_nullable=True)
        op.alter_column('market_data', 'low_price',
                       existing_type=sa.DECIMAL(precision=12, scale=4),
                       type_=sa.Float(),
                       existing_nullable=True)
        
        # AlertLog table
        op.alter_column('alert_logs', 'trigger_value',
                       existing_type=sa.DECIMAL(precision=12, scale=4),
                       type_=sa.Float(),
                       existing_nullable=False)
        op.alter_column('alert_logs', 'threshold_value',
                       existing_type=sa.DECIMAL(precision=12, scale=4),
                       type_=sa.Float(),
                       existing_nullable=False)
    
    print("✓ DECIMAL to FLOAT conversion complete")
    print("  - MarketData: 6 price columns converted")
    print("  - AlertLog: 2 value columns converted")


def downgrade() -> None:
    """Restore DECIMAL column types."""
    
    bind = op.get_bind()
    dialect_name = bind.dialect.name
    
    if dialect_name == 'sqlite':
        # SQLite batch operations for downgrade
        with op.batch_alter_table('market_data', schema=None) as batch_op:
            batch_op.alter_column('price',
                                existing_type=sa.Float(),
                                type_=sa.DECIMAL(precision=12, scale=4),
                                existing_nullable=True)
            batch_op.alter_column('bid',
                                existing_type=sa.Float(),
                                type_=sa.DECIMAL(precision=12, scale=4),
                                existing_nullable=True)
            batch_op.alter_column('ask',
                                existing_type=sa.Float(),
                                type_=sa.DECIMAL(precision=12, scale=4),
                                existing_nullable=True)
            batch_op.alter_column('open_price',
                                existing_type=sa.Float(),
                                type_=sa.DECIMAL(precision=12, scale=4),
                                existing_nullable=True)
            batch_op.alter_column('high_price',
                                existing_type=sa.Float(),
                                type_=sa.DECIMAL(precision=12, scale=4),
                                existing_nullable=True)
            batch_op.alter_column('low_price',
                                existing_type=sa.Float(),
                                type_=sa.DECIMAL(precision=12, scale=4),
                                existing_nullable=True)
        
        with op.batch_alter_table('alert_logs', schema=None) as batch_op:
            batch_op.alter_column('trigger_value',
                                existing_type=sa.Float(),
                                type_=sa.DECIMAL(precision=12, scale=4),
                                existing_nullable=False)
            batch_op.alter_column('threshold_value',
                                existing_type=sa.Float(),
                                type_=sa.DECIMAL(precision=12, scale=4),
                                existing_nullable=False)
    else:
        # Direct ALTER COLUMN for other databases
        op.alter_column('market_data', 'price',
                       existing_type=sa.Float(),
                       type_=sa.DECIMAL(precision=12, scale=4),
                       existing_nullable=True)
        op.alter_column('market_data', 'bid',
                       existing_type=sa.Float(),
                       type_=sa.DECIMAL(precision=12, scale=4),
                       existing_nullable=True)
        op.alter_column('market_data', 'ask',
                       existing_type=sa.Float(),
                       type_=sa.DECIMAL(precision=12, scale=4),
                       existing_nullable=True)
        op.alter_column('market_data', 'open_price',
                       existing_type=sa.Float(),
                       type_=sa.DECIMAL(precision=12, scale=4),
                       existing_nullable=True)
        op.alter_column('market_data', 'high_price',
                       existing_type=sa.Float(),
                       type_=sa.DECIMAL(precision=12, scale=4),
                       existing_nullable=True)
        op.alter_column('market_data', 'low_price',
                       existing_type=sa.Float(),
                       type_=sa.DECIMAL(precision=12, scale=4),
                       existing_nullable=True)
        
        op.alter_column('alert_logs', 'trigger_value',
                       existing_type=sa.Float(),
                       type_=sa.DECIMAL(precision=12, scale=4),
                       existing_nullable=False)
        op.alter_column('alert_logs', 'threshold_value',
                       existing_type=sa.Float(),
                       type_=sa.DECIMAL(precision=12, scale=4),
                       existing_nullable=False)
    
    print("✓ FLOAT to DECIMAL restoration complete")