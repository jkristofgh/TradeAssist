"""
Data Archival Service for Long-Term Data Retention.

Provides automated archival procedures for old partitions with configurable
compression, storage management, and recovery capabilities.
"""

import os
import gzip
import json
import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import structlog

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_db_session
from ..config import settings

logger = structlog.get_logger(__name__)


@dataclass
class ArchiveRecord:
    """Record of an archived partition."""
    
    partition_name: str
    table_name: str
    archived_at: datetime
    start_date: date
    end_date: date
    original_row_count: int
    archived_row_count: int
    archive_path: str
    compressed: bool = True
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchivalConfig:
    """Configuration for data archival operations."""
    
    # Storage settings
    archive_base_path: str = "./data/archive"
    enable_compression: bool = True
    compression_level: int = 6
    
    # File organization
    organize_by_year: bool = True
    organize_by_table: bool = True
    
    # Validation settings
    verify_archives: bool = True
    keep_checksums: bool = True
    
    # Cleanup settings
    cleanup_after_archive: bool = True
    verification_sample_size: int = 1000
    
    # Metadata settings
    include_table_schema: bool = True
    include_index_definitions: bool = True
    
    # Recovery settings
    enable_recovery_testing: bool = False
    recovery_test_interval_days: int = 30


class DataArchivalService:
    """
    Service for automated data archival and long-term retention.
    
    Handles archival of old partitions with compression, verification,
    and recovery capabilities for long-term data management.
    
    Features:
    - Automated partition data export and compression
    - Archive verification and integrity checking
    - Configurable storage organization and retention
    - Recovery procedures for archived data
    """
    
    def __init__(self, config: Optional[ArchivalConfig] = None):
        """Initialize data archival service."""
        self.config = config or ArchivalConfig()
        self._archive_registry: List[ArchiveRecord] = []
        
        # Ensure archive directory exists
        self._ensure_archive_directories()
        
        # Load existing archive registry
        self._load_archive_registry()
    
    def _ensure_archive_directories(self) -> None:
        """Ensure archive directory structure exists."""
        base_path = Path(self.config.archive_base_path)
        base_path.mkdir(parents=True, exist_ok=True)
        
        if self.config.organize_by_table:
            (base_path / "market_data").mkdir(exist_ok=True)
            (base_path / "alert_logs").mkdir(exist_ok=True)
        
        # Registry file directory
        (base_path / "registry").mkdir(exist_ok=True)
    
    def _load_archive_registry(self) -> None:
        """Load the archive registry from disk."""
        registry_path = Path(self.config.archive_base_path) / "registry" / "archive_registry.json"
        
        if registry_path.exists():
            try:
                with open(registry_path, 'r') as f:
                    registry_data = json.load(f)
                
                self._archive_registry = [
                    ArchiveRecord(
                        partition_name=record['partition_name'],
                        table_name=record['table_name'],
                        archived_at=datetime.fromisoformat(record['archived_at']),
                        start_date=date.fromisoformat(record['start_date']),
                        end_date=date.fromisoformat(record['end_date']),
                        original_row_count=record['original_row_count'],
                        archived_row_count=record['archived_row_count'],
                        archive_path=record['archive_path'],
                        compressed=record.get('compressed', True),
                        checksum=record.get('checksum'),
                        metadata=record.get('metadata', {})
                    )
                    for record in registry_data
                ]
                
                logger.info("Loaded archive registry", 
                          archive_count=len(self._archive_registry))
                
            except Exception as e:
                logger.warning("Failed to load archive registry", error=str(e))
                self._archive_registry = []
    
    def _save_archive_registry(self) -> None:
        """Save the archive registry to disk."""
        registry_path = Path(self.config.archive_base_path) / "registry" / "archive_registry.json"
        
        try:
            registry_data = [
                {
                    'partition_name': record.partition_name,
                    'table_name': record.table_name,
                    'archived_at': record.archived_at.isoformat(),
                    'start_date': record.start_date.isoformat(),
                    'end_date': record.end_date.isoformat(),
                    'original_row_count': record.original_row_count,
                    'archived_row_count': record.archived_row_count,
                    'archive_path': record.archive_path,
                    'compressed': record.compressed,
                    'checksum': record.checksum,
                    'metadata': record.metadata
                }
                for record in self._archive_registry
            ]
            
            with open(registry_path, 'w') as f:
                json.dump(registry_data, f, indent=2, default=str)
                
            logger.debug("Saved archive registry", archive_count=len(registry_data))
            
        except Exception as e:
            logger.error("Failed to save archive registry", error=str(e))
    
    async def archive_partition(
        self, 
        partition_name: str, 
        table_name: str,
        start_date: date,
        end_date: date
    ) -> ArchiveRecord:
        """
        Archive a partition to long-term storage.
        
        Args:
            partition_name: Name of the partition table to archive
            table_name: Base table name ('market_data' or 'alert_logs')
            start_date: Start date of the partition data
            end_date: End date of the partition data
            
        Returns:
            ArchiveRecord containing archival information
        """
        logger.info("Starting partition archival",
                   partition=partition_name,
                   table=table_name,
                   date_range=f"{start_date} to {end_date}")
        
        try:
            # Step 1: Export partition data
            export_data = await self._export_partition_data(partition_name)
            
            # Step 2: Create archive file path
            archive_path = self._create_archive_path(
                table_name, partition_name, start_date
            )
            
            # Step 3: Save data with optional compression
            archived_row_count = await self._save_archive_data(
                archive_path, export_data, partition_name
            )
            
            # Step 4: Verify archive if enabled
            checksum = None
            if self.config.verify_archives:
                checksum = await self._verify_archive(archive_path, export_data)
            
            # Step 5: Create archive record
            archive_record = ArchiveRecord(
                partition_name=partition_name,
                table_name=table_name,
                archived_at=datetime.now(),
                start_date=start_date,
                end_date=end_date,
                original_row_count=len(export_data['rows']),
                archived_row_count=archived_row_count,
                archive_path=str(archive_path),
                compressed=self.config.enable_compression,
                checksum=checksum,
                metadata={
                    'schema': export_data['schema'] if self.config.include_table_schema else None,
                    'indexes': export_data['indexes'] if self.config.include_index_definitions else None
                }
            )
            
            # Step 6: Register archive
            self._archive_registry.append(archive_record)
            self._save_archive_registry()
            
            logger.info("Successfully archived partition",
                       partition=partition_name,
                       archive_path=archive_path,
                       row_count=archived_row_count)
            
            return archive_record
            
        except Exception as e:
            logger.error("Failed to archive partition",
                        partition=partition_name, error=str(e))
            raise
    
    async def _export_partition_data(self, partition_name: str) -> Dict[str, Any]:
        """Export all data from a partition."""
        export_data = {
            'partition_name': partition_name,
            'exported_at': datetime.now().isoformat(),
            'rows': [],
            'schema': {},
            'indexes': []
        }
        
        async with get_db_session() as session:
            # Export table data
            result = await session.execute(text(f"SELECT * FROM {partition_name}"))
            columns = result.keys()
            
            rows = []
            for row in result:
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    # Convert datetime objects to ISO strings
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    elif isinstance(value, date):
                        value = value.isoformat()
                    row_dict[column] = value
                rows.append(row_dict)
            
            export_data['rows'] = rows
            
            # Export schema information if requested
            if self.config.include_table_schema:
                schema_result = await session.execute(
                    text(f"PRAGMA table_info({partition_name})")
                )
                export_data['schema'] = [
                    {
                        'cid': row[0],
                        'name': row[1],
                        'type': row[2],
                        'notnull': bool(row[3]),
                        'dflt_value': row[4],
                        'pk': bool(row[5])
                    }
                    for row in schema_result
                ]
            
            # Export index information if requested
            if self.config.include_index_definitions:
                index_result = await session.execute(
                    text(f"PRAGMA index_list({partition_name})")
                )
                
                indexes = []
                for index_row in index_result:
                    index_name = index_row[1]
                    
                    # Get index details
                    index_info_result = await session.execute(
                        text(f"PRAGMA index_info({index_name})")
                    )
                    
                    index_columns = [info[2] for info in index_info_result]
                    
                    indexes.append({
                        'name': index_name,
                        'unique': bool(index_row[2]),
                        'columns': index_columns
                    })
                
                export_data['indexes'] = indexes
        
        return export_data
    
    def _create_archive_path(self, table_name: str, partition_name: str, start_date: date) -> Path:
        """Create the archive file path."""
        base_path = Path(self.config.archive_base_path)
        
        # Organize by table if configured
        if self.config.organize_by_table:
            base_path = base_path / table_name
        
        # Organize by year if configured
        if self.config.organize_by_year:
            base_path = base_path / str(start_date.year)
        
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Create filename
        filename = f"{partition_name}_{start_date.isoformat()}.json"
        if self.config.enable_compression:
            filename += ".gz"
        
        return base_path / filename
    
    async def _save_archive_data(
        self, 
        archive_path: Path, 
        export_data: Dict[str, Any],
        partition_name: str
    ) -> int:
        """Save archive data to disk with optional compression."""
        try:
            json_data = json.dumps(export_data, indent=2, default=str)
            
            if self.config.enable_compression:
                with gzip.open(archive_path, 'wt', compresslevel=self.config.compression_level) as f:
                    f.write(json_data)
            else:
                with open(archive_path, 'w') as f:
                    f.write(json_data)
            
            row_count = len(export_data['rows'])
            
            logger.debug("Saved archive data",
                        path=archive_path,
                        row_count=row_count,
                        compressed=self.config.enable_compression)
            
            return row_count
            
        except Exception as e:
            logger.error("Failed to save archive data", 
                        path=archive_path, error=str(e))
            raise
    
    async def _verify_archive(self, archive_path: Path, original_data: Dict[str, Any]) -> Optional[str]:
        """Verify archive integrity by reading and comparing sample data."""
        try:
            # Read archive data
            if self.config.enable_compression:
                with gzip.open(archive_path, 'rt') as f:
                    archived_data = json.load(f)
            else:
                with open(archive_path, 'r') as f:
                    archived_data = json.load(f)
            
            # Basic verification
            original_row_count = len(original_data['rows'])
            archived_row_count = len(archived_data['rows'])
            
            if original_row_count != archived_row_count:
                raise ValueError(f"Row count mismatch: {original_row_count} vs {archived_row_count}")
            
            # Sample verification
            sample_size = min(self.config.verification_sample_size, original_row_count)
            if sample_size > 0:
                sample_indices = list(range(0, original_row_count, max(1, original_row_count // sample_size)))
                
                for i in sample_indices:
                    if original_data['rows'][i] != archived_data['rows'][i]:
                        raise ValueError(f"Data mismatch at row {i}")
            
            # Calculate simple checksum
            checksum = str(hash(str(archived_data['rows'])))
            
            logger.debug("Archive verification successful",
                        path=archive_path,
                        row_count=archived_row_count,
                        checksum=checksum)
            
            return checksum
            
        except Exception as e:
            logger.error("Archive verification failed", 
                        path=archive_path, error=str(e))
            raise
    
    async def restore_partition(self, archive_record: ArchiveRecord) -> str:
        """
        Restore a partition from archive.
        
        Args:
            archive_record: Archive record to restore
            
        Returns:
            Name of the restored partition table
        """
        logger.info("Starting partition restoration",
                   partition=archive_record.partition_name,
                   archive_path=archive_record.archive_path)
        
        try:
            # Step 1: Load archive data
            archive_data = await self._load_archive_data(archive_record.archive_path)
            
            # Step 2: Create partition table
            await self._create_partition_table_from_archive(archive_record, archive_data)
            
            # Step 3: Insert data
            await self._insert_archive_data(archive_record.partition_name, archive_data['rows'])
            
            # Step 4: Recreate indexes
            if archive_data.get('indexes'):
                await self._recreate_indexes(archive_record.partition_name, archive_data['indexes'])
            
            logger.info("Successfully restored partition",
                       partition=archive_record.partition_name,
                       row_count=len(archive_data['rows']))
            
            return archive_record.partition_name
            
        except Exception as e:
            logger.error("Failed to restore partition",
                        partition=archive_record.partition_name, error=str(e))
            raise
    
    async def _load_archive_data(self, archive_path: str) -> Dict[str, Any]:
        """Load data from an archive file."""
        path = Path(archive_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Archive file not found: {archive_path}")
        
        try:
            if path.suffix == '.gz':
                with gzip.open(path, 'rt') as f:
                    return json.load(f)
            else:
                with open(path, 'r') as f:
                    return json.load(f)
                    
        except Exception as e:
            logger.error("Failed to load archive data", path=archive_path, error=str(e))
            raise
    
    async def _create_partition_table_from_archive(
        self, 
        archive_record: ArchiveRecord, 
        archive_data: Dict[str, Any]
    ) -> None:
        """Create partition table structure from archive data."""
        partition_name = archive_record.partition_name
        base_table = archive_record.table_name
        
        async with get_db_session() as session:
            # Create table with same structure as base table
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {partition_name} (
                LIKE {base_table} INCLUDING ALL
            );
            """
            
            await session.execute(text(create_sql))
            
            # Add partition constraints
            constraint_sql = f"""
            ALTER TABLE {partition_name} ADD CONSTRAINT {partition_name}_check
            CHECK (timestamp >= '{archive_record.start_date}' 
                   AND timestamp <= '{archive_record.end_date} 23:59:59');
            """
            
            try:
                await session.execute(text(constraint_sql))
            except Exception as e:
                # Constraint might already exist
                logger.debug("Could not add partition constraint", error=str(e))
            
            await session.commit()
    
    async def _insert_archive_data(self, partition_name: str, rows: List[Dict[str, Any]]) -> None:
        """Insert archived data into the restored partition."""
        if not rows:
            return
        
        # Build insert statement
        columns = list(rows[0].keys())
        placeholders = ', '.join([f':{col}' for col in columns])
        insert_sql = f"INSERT INTO {partition_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        async with get_db_session() as session:
            # Convert ISO strings back to datetime objects for timestamp columns
            processed_rows = []
            for row in rows:
                processed_row = {}
                for key, value in row.items():
                    if key == 'timestamp' and isinstance(value, str):
                        try:
                            processed_row[key] = datetime.fromisoformat(value)
                        except:
                            processed_row[key] = value
                    else:
                        processed_row[key] = value
                processed_rows.append(processed_row)
            
            await session.execute(text(insert_sql), processed_rows)
            await session.commit()
    
    async def _recreate_indexes(self, partition_name: str, indexes: List[Dict[str, Any]]) -> None:
        """Recreate indexes on the restored partition."""
        async with get_db_session() as session:
            for index in indexes:
                try:
                    index_name = f"ix_{partition_name}_{index['name'].split('_')[-1]}"
                    columns = ', '.join(index['columns'])
                    unique = "UNIQUE " if index['unique'] else ""
                    
                    create_index_sql = f"CREATE {unique}INDEX IF NOT EXISTS {index_name} ON {partition_name} ({columns})"
                    await session.execute(text(create_index_sql))
                    
                except Exception as e:
                    logger.warning("Failed to recreate index",
                                 partition=partition_name,
                                 index=index['name'],
                                 error=str(e))
            
            await session.commit()
    
    def get_archive_status(self) -> Dict[str, Any]:
        """Get current archive status and metrics."""
        total_archived_rows = sum(record.archived_row_count for record in self._archive_registry)
        
        # Group by table
        archives_by_table = {}
        for record in self._archive_registry:
            if record.table_name not in archives_by_table:
                archives_by_table[record.table_name] = []
            archives_by_table[record.table_name].append(record)
        
        return {
            "total_archives": len(self._archive_registry),
            "total_archived_rows": total_archived_rows,
            "archive_base_path": self.config.archive_base_path,
            "compression_enabled": self.config.enable_compression,
            "archives_by_table": {
                table: [
                    {
                        "partition_name": record.partition_name,
                        "archived_at": record.archived_at.isoformat(),
                        "date_range": f"{record.start_date} to {record.end_date}",
                        "row_count": record.archived_row_count,
                        "archive_path": record.archive_path,
                        "compressed": record.compressed
                    }
                    for record in records
                ]
                for table, records in archives_by_table.items()
            }
        }
    
    def find_archive_by_partition(self, partition_name: str) -> Optional[ArchiveRecord]:
        """Find archive record by partition name."""
        for record in self._archive_registry:
            if record.partition_name == partition_name:
                return record
        return None
    
    def find_archives_by_date_range(
        self, 
        table_name: str, 
        start_date: date, 
        end_date: date
    ) -> List[ArchiveRecord]:
        """Find archive records that overlap with the given date range."""
        matching_archives = []
        
        for record in self._archive_registry:
            if record.table_name == table_name:
                # Check for date range overlap
                if (record.start_date <= end_date and record.end_date >= start_date):
                    matching_archives.append(record)
        
        return sorted(matching_archives, key=lambda x: x.start_date)


# Global instance management
_data_archival_service = None


def get_data_archival_service(config: Optional[ArchivalConfig] = None) -> DataArchivalService:
    """Get global DataArchivalService instance."""
    global _data_archival_service
    
    if _data_archival_service is None:
        _data_archival_service = DataArchivalService(config)
        logger.info("DataArchivalService initialized")
    
    return _data_archival_service