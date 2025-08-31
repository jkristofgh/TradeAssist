# Extension Phase 1 Requirements - Database Schema Foundation

## Phase Overview
- **Phase Number**: 1
- **Phase Name**: Database Schema Foundation
- **Extension Name**: Database Performance & Integrity
- **Dependencies**: Current database schema and existing migration system

## Phase Objectives
### Primary Goals
- Optimize database indexes to achieve 30-50% INSERT performance improvement
- Convert DECIMAL to FLOAT data types for 2-3x calculation speed improvement
- Implement soft delete mechanism to prevent accidental data loss
- Replace CASCADE DELETE with RESTRICT for data safety

### Deliverables
- Index optimization migration scripts for MarketData and AlertLog tables
- Data type conversion migrations (DECIMAL → FLOAT)
- Soft delete mechanism with `deleted_at` columns
- Referential integrity safety updates (CASCADE → RESTRICT)
- Migration rollback procedures and validation scripts

## Existing System Context
### Available Integration Points (from CODEBASE_ANALYSIS.md)
- **Alembic Migration System**: Existing migration framework for zero-downtime schema changes
- **SQLAlchemy Models**: Base class and TimestampMixin patterns for consistency
- **Database Connection**: Async SQLAlchemy with connection pooling infrastructure
- **Structured Logging**: Performance metrics integration with existing logging system

### Existing Patterns to Follow
- **Migration Pattern**: Use existing Alembic workflow with `alembic revision --autogenerate`
- **Model Pattern**: Follow Base class and TimestampMixin inheritance patterns
- **Index Pattern**: Use existing `__table_args__` Index specification format
- **Error Handling**: Use existing session management and rollback patterns

### APIs and Services Available
- **Database Connection**: `get_db_session()` async context manager
- **Migration System**: Alembic commands and version control
- **Base Model**: Existing `Base` and `TimestampMixin` classes
- **Configuration**: Existing database settings and environment management

## Phase Implementation Requirements
### Backend Requirements

#### **Index Optimization (MarketData Table)**
- Remove 3 non-essential indexes causing INSERT bottlenecks:
  - `ix_market_data_timestamp` (single column)
  - `ix_market_data_instrument` (single column)  
  - `ix_market_data_price` (single column)
  - `ix_market_data_latest` (composite covering index)
- Keep essential composite index: `ix_market_data_timestamp_instrument`
- Add optimized secondary index: `ix_market_data_instrument_price`

#### **Index Optimization (AlertLog Table)**
- Reduce from 11 indexes to 4 essential indexes:
  - Keep: `ix_alert_logs_timestamp` (primary time-series)
  - Keep: `ix_alert_logs_rule_timestamp` (rule performance)
  - Keep: `ix_alert_logs_instrument` (instrument alerts)
  - Keep: `ix_alert_logs_status` (status monitoring)
- Remove 7 redundant indexes causing INSERT performance degradation

#### **Data Type Optimization**
- Convert MarketData price fields from DECIMAL(12,4) to FLOAT:
  - `price`, `bid`, `ask`, `open_price`, `high_price`, `low_price`
- Convert AlertLog value fields from DECIMAL(12,4) to FLOAT:
  - `trigger_value`, `threshold_value`
- Maintain data precision through API response validation

#### **Soft Delete Implementation**
- Add `deleted_at` timestamp columns to both MarketData and AlertLog tables
- Create indexes on `deleted_at` columns for query performance
- Implement SoftDeleteMixin class following existing TimestampMixin pattern

#### **Referential Integrity Safety**
- Update foreign key constraints from CASCADE to RESTRICT
- Preserve existing relationships while preventing accidental data loss
- Handle SQLite constraint limitation through documented procedures

### Database Schema Changes
```python
# MarketData table changes
- ALTER COLUMN price TYPE FLOAT (from DECIMAL(12,4))
- ALTER COLUMN bid TYPE FLOAT (from DECIMAL(12,4))
- ALTER COLUMN ask TYPE FLOAT (from DECIMAL(12,4))
- ALTER COLUMN open_price TYPE FLOAT (from DECIMAL(12,4))
- ALTER COLUMN high_price TYPE FLOAT (from DECIMAL(12,4))
- ALTER COLUMN low_price TYPE FLOAT (from DECIMAL(12,4))
- ADD COLUMN deleted_at DATETIME NULL
- DROP INDEX ix_market_data_timestamp
- DROP INDEX ix_market_data_instrument
- DROP INDEX ix_market_data_price
- DROP INDEX ix_market_data_latest
- CREATE INDEX ix_market_data_instrument_price ON (instrument_id, price)
- CREATE INDEX ix_market_data_deleted_at ON (deleted_at)

# AlertLog table changes  
- ALTER COLUMN trigger_value TYPE FLOAT (from DECIMAL(12,4))
- ALTER COLUMN threshold_value TYPE FLOAT (from DECIMAL(12,4))
- ADD COLUMN deleted_at DATETIME NULL
- DROP 7 redundant indexes (keep 4 essential)
- CREATE INDEX ix_alert_logs_deleted_at ON (deleted_at)
```

### Migration Scripts Required
1. **optimize_market_data_indexes.py**: Remove 3 indexes, add 1 optimized index
2. **optimize_alert_log_indexes.py**: Remove 7 indexes, keep 4 essential
3. **convert_decimal_to_float.py**: Convert all price fields to FLOAT
4. **add_soft_delete_safety.py**: Add deleted_at columns and RESTRICT constraints

## Compatibility Requirements
### Backward Compatibility
- All existing queries must continue to work with optimized indexes
- API responses maintain 4-decimal precision despite FLOAT storage
- Existing service layer code continues to function without changes
- No breaking changes to existing database access patterns

### API Contract Preservation  
- MarketData API responses maintain existing field formats
- AlertLog API responses preserve existing precision
- Health API continues to report database status
- WebSocket data feeds maintain existing message formats

## Testing Requirements
### Migration Testing
- Test each migration script in isolation with rollback capability
- Validate data integrity before and after DECIMAL to FLOAT conversion
- Confirm query performance with optimized indexes
- Test soft delete functionality with existing data patterns

### Performance Testing
- Measure INSERT performance improvement with reduced indexes
- Benchmark calculation performance with FLOAT vs DECIMAL
- Validate query performance maintained with optimized indexes  
- Test connection pool behavior with schema changes

### Data Safety Testing
- Confirm soft delete prevents data loss in all scenarios
- Validate RESTRICT prevents accidental CASCADE deletions
- Test data migration accuracy with precision validation
- Verify rollback procedures restore original state

## Success Criteria
- [ ] MarketData table INSERT operations show 30-50% performance improvement
- [ ] AlertLog table INSERT operations show significant performance improvement  
- [ ] Price calculations show 2-3x speed improvement with FLOAT arithmetic
- [ ] Soft delete mechanism prevents accidental data loss
- [ ] All existing queries continue to work with optimized indexes
- [ ] Data migration maintains precision within acceptable tolerance (<0.0001)
- [ ] Migration rollback procedures tested and documented
- [ ] Zero data loss during entire migration process

## Phase Completion Definition
This phase is complete when:
- [ ] All 4 migration scripts execute successfully in staging environment
- [ ] Performance improvements measured and documented
- [ ] Data integrity validation passes for all converted fields
- [ ] Soft delete mechanism operational and tested
- [ ] Rollback procedures validated for all schema changes
- [ ] All existing functionality remains intact
- [ ] Migration scripts ready for production deployment

## Next Phase Preparation
### For Phase 2 Integration
- Optimized database schema ready for service layer updates
- SoftDeleteMixin available for model class inheritance
- Performance improvements documented for service layer optimization
- Migration procedures documented for production deployment

### APIs Available for Phase 2
- Database schema with optimized performance characteristics
- Soft delete mechanism available for model integration
- Improved INSERT/query performance ready for service utilization
- Schema foundation ready for repository pattern enhancements