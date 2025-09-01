"""
Historical Data Validator Component

Handles data validation, integrity checks, and quality assurance.
Extracted from HistoricalDataService as part of Phase 3 decomposition.
"""

import structlog
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict

logger = structlog.get_logger()


@dataclass
class ValidationRule:
    """Represents a single validation rule for market data."""
    name: str
    description: str
    validator_func: callable
    severity: str  # 'error', 'warning', 'info'


@dataclass
class ValidationError:
    """Represents a validation error or warning."""
    rule_name: str
    severity: str
    message: str
    bar_index: Optional[int] = None
    field_name: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of market data validation."""
    is_valid: bool
    quality_score: float  # 0.0 to 1.0
    total_bars: int
    valid_bars: int
    errors: List[ValidationError]
    warnings: List[ValidationError]
    info: List[ValidationError]
    
    
@dataclass
class DataGap:
    """Represents a gap in time series data."""
    symbol: str
    frequency: str
    gap_start: datetime
    gap_end: datetime
    expected_bars: int
    actual_bars: int
    gap_duration_minutes: int
    severity: str  # 'minor', 'major', 'critical'


class HistoricalDataValidator:
    """
    Handles data validation, integrity checks, and quality assurance.
    
    Responsibilities:
    - Market data validation and sanitization
    - Duplicate detection and resolution strategies
    - Data quality scoring and reporting
    - Gap detection and reporting for time series data
    - Business rule validation (price ranges, volume checks)
    """
    
    def __init__(self):
        self._validation_rules = self._initialize_validation_rules()
        self._quality_thresholds = self._initialize_quality_thresholds()
        
        # Performance tracking
        self._validations_performed = 0
        self._duplicates_resolved = 0
        self._gaps_detected = 0
        self._quality_scores: List[float] = []
        
        logger.debug("HistoricalDataValidator initialized")

    async def validate_market_data(self, data: List[Dict[str, Any]]) -> ValidationResult:
        """
        Comprehensive market data validation.
        
        Args:
            data: List of market data bar dictionaries
            
        Returns:
            ValidationResult with detailed validation information
        """
        if not data:
            return ValidationResult(
                is_valid=True,
                quality_score=0.0,
                total_bars=0,
                valid_bars=0,
                errors=[],
                warnings=[],
                info=[]
            )
            
        logger.debug(f"Validating {len(data)} market data bars")
        
        errors = []
        warnings = []
        info = []
        valid_bars = 0
        
        # Validate each bar
        for i, bar in enumerate(data):
            bar_errors, bar_warnings, bar_info = await self._validate_single_bar(bar, i)
            errors.extend(bar_errors)
            warnings.extend(bar_warnings)
            info.extend(bar_info)
            
            # Count as valid if no errors (warnings are okay)
            if not bar_errors:
                valid_bars += 1
                
        # Validate time series consistency
        series_errors, series_warnings, series_info = await self._validate_time_series(data)
        errors.extend(series_errors)
        warnings.extend(series_warnings)
        info.extend(series_info)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(data, errors, warnings)
        
        # Determine overall validity
        is_valid = len(errors) == 0
        
        result = ValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            total_bars=len(data),
            valid_bars=valid_bars,
            errors=errors,
            warnings=warnings,
            info=info
        )
        
        self._validations_performed += 1
        self._quality_scores.append(quality_score)
        
        # Keep only recent quality scores
        if len(self._quality_scores) > 1000:
            self._quality_scores = self._quality_scores[-1000:]
            
        logger.info(
            f"Validation completed: {valid_bars}/{len(data)} valid bars, "
            f"quality score: {quality_score:.2f}"
        )
        
        return result

    async def handle_duplicates(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect and resolve duplicate market data entries.
        
        Args:
            data: List of market data bars
            
        Returns:
            List of deduplicated market data bars
        """
        if not data:
            return data
            
        logger.debug(f"Processing {len(data)} bars for duplicates")
        
        # Group bars by timestamp for duplicate detection
        timestamp_groups: Dict[datetime, List[Tuple[int, Dict[str, Any]]]] = defaultdict(list)
        
        for i, bar in enumerate(data):
            if 'timestamp' in bar and bar['timestamp']:
                timestamp_groups[bar['timestamp']].append((i, bar))
                
        # Process duplicates
        deduplicated_data = []
        duplicates_found = 0
        
        for timestamp, bars_group in timestamp_groups.items():
            if len(bars_group) == 1:
                # No duplicates
                deduplicated_data.append(bars_group[0][1])
            else:
                # Handle duplicates
                duplicates_found += len(bars_group) - 1
                resolved_bar = await self._resolve_duplicate_bars(bars_group)
                deduplicated_data.append(resolved_bar)
                
        # Sort by timestamp to maintain order
        deduplicated_data.sort(key=lambda x: x.get('timestamp', datetime.min))
        
        self._duplicates_resolved += duplicates_found
        
        logger.info(
            f"Duplicate processing complete: {duplicates_found} duplicates resolved, "
            f"{len(deduplicated_data)} bars remaining"
        )
        
        return deduplicated_data

    def detect_data_gaps(
        self, 
        data: List[Dict[str, Any]], 
        expected_frequency: str,
        symbol: str = "UNKNOWN"
    ) -> List[DataGap]:
        """
        Identify gaps in time series data.
        
        Args:
            data: List of market data bars
            expected_frequency: Expected data frequency
            symbol: Symbol name for gap reporting
            
        Returns:
            List of detected gaps
        """
        if len(data) < 2:
            return []
            
        logger.debug(f"Detecting gaps in {len(data)} bars for {symbol}")
        
        # Sort data by timestamp
        sorted_data = sorted(data, key=lambda x: x.get('timestamp', datetime.min))
        
        # Get expected time delta for frequency
        expected_delta = self._get_expected_time_delta(expected_frequency)
        if not expected_delta:
            logger.warning(f"Unknown frequency '{expected_frequency}' for gap detection")
            return []
            
        gaps = []
        tolerance_minutes = expected_delta.total_seconds() / 60 * 0.1  # 10% tolerance
        
        for i in range(len(sorted_data) - 1):
            current_bar = sorted_data[i]
            next_bar = sorted_data[i + 1]
            
            if 'timestamp' not in current_bar or 'timestamp' not in next_bar:
                continue
                
            time_diff = next_bar['timestamp'] - current_bar['timestamp']
            expected_bars = int(time_diff.total_seconds() / expected_delta.total_seconds())
            
            # Detect significant gaps (more than expected + tolerance)
            if expected_bars > 1 + tolerance_minutes:
                gap_duration_minutes = int(time_diff.total_seconds() / 60)
                
                # Classify gap severity
                if gap_duration_minutes < 60:  # Less than 1 hour
                    severity = "minor"
                elif gap_duration_minutes < 1440:  # Less than 1 day
                    severity = "major"
                else:  # 1 day or more
                    severity = "critical"
                    
                gap = DataGap(
                    symbol=symbol,
                    frequency=expected_frequency,
                    gap_start=current_bar['timestamp'],
                    gap_end=next_bar['timestamp'],
                    expected_bars=expected_bars,
                    actual_bars=1,  # Only the bars we have
                    gap_duration_minutes=gap_duration_minutes,
                    severity=severity
                )
                gaps.append(gap)
                
        self._gaps_detected += len(gaps)
        
        logger.info(f"Gap detection complete: {len(gaps)} gaps found for {symbol}")
        return gaps

    def calculate_data_quality_score(self, data: List[Dict[str, Any]]) -> float:
        """
        Calculate overall data quality score (0.0 to 1.0).
        
        Args:
            data: List of market data bars
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not data:
            return 0.0
            
        # Run full validation to get detailed results
        validation_result = None
        try:
            # Use a simple synchronous approach for quality calculation
            validation_result = self._calculate_quality_score_sync(data)
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.0
            
        return validation_result

    def get_validator_stats(self) -> Dict[str, Any]:
        """
        Get validation performance statistics.
        
        Returns:
            Dictionary with validator performance metrics
        """
        avg_quality_score = (
            sum(self._quality_scores) / len(self._quality_scores)
            if self._quality_scores else 0.0
        )
        
        return {
            "validations_performed": self._validations_performed,
            "duplicates_resolved": self._duplicates_resolved,
            "gaps_detected": self._gaps_detected,
            "avg_quality_score": round(avg_quality_score, 3),
            "quality_score_samples": len(self._quality_scores),
            "validation_rules_count": len(self._validation_rules)
        }

    # Private helper methods
    
    def _initialize_validation_rules(self) -> List[ValidationRule]:
        """Initialize market data validation rules."""
        return [
            ValidationRule(
                name="required_fields",
                description="Check for required OHLCV fields",
                validator_func=self._validate_required_fields,
                severity="error"
            ),
            ValidationRule(
                name="numeric_fields", 
                description="Ensure numeric fields are valid numbers",
                validator_func=self._validate_numeric_fields,
                severity="error"
            ),
            ValidationRule(
                name="price_relationships",
                description="Validate OHLC price relationships (high >= low, etc.)",
                validator_func=self._validate_price_relationships,
                severity="error"
            ),
            ValidationRule(
                name="positive_values",
                description="Ensure prices and volume are positive",
                validator_func=self._validate_positive_values,
                severity="error"
            ),
            ValidationRule(
                name="reasonable_ranges",
                description="Check for reasonable price and volume ranges",
                validator_func=self._validate_reasonable_ranges,
                severity="warning"
            ),
            ValidationRule(
                name="timestamp_format",
                description="Validate timestamp format and value",
                validator_func=self._validate_timestamp,
                severity="error"
            ),
            ValidationRule(
                name="volume_consistency",
                description="Check volume consistency and patterns",
                validator_func=self._validate_volume_consistency,
                severity="info"
            )
        ]

    def _initialize_quality_thresholds(self) -> Dict[str, Any]:
        """Initialize quality assessment thresholds."""
        return {
            "min_price": 0.01,
            "max_price": 1000000.0,
            "min_volume": 0,
            "max_volume": 1000000000,
            "max_price_change_percent": 50.0,  # 50% max change between bars
            "min_quality_score": 0.8,  # 80% minimum quality
            "gap_tolerance_minutes": {
                "1min": 2,
                "5min": 10, 
                "15min": 30,
                "30min": 60,
                "1h": 120,
                "1d": 1440
            }
        }

    async def _validate_single_bar(
        self, 
        bar: Dict[str, Any], 
        index: int
    ) -> Tuple[List[ValidationError], List[ValidationError], List[ValidationError]]:
        """Validate a single market data bar."""
        errors = []
        warnings = []
        info = []
        
        for rule in self._validation_rules:
            try:
                rule_errors = rule.validator_func(bar, index)
                
                for error_msg in rule_errors:
                    error = ValidationError(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=error_msg,
                        bar_index=index
                    )
                    
                    if rule.severity == "error":
                        errors.append(error)
                    elif rule.severity == "warning":
                        warnings.append(error)
                    else:
                        info.append(error)
                        
            except Exception as e:
                # If validation rule fails, treat as error
                error = ValidationError(
                    rule_name=rule.name,
                    severity="error",
                    message=f"Validation rule failed: {e}",
                    bar_index=index
                )
                errors.append(error)
                
        return errors, warnings, info

    async def _validate_time_series(
        self, 
        data: List[Dict[str, Any]]
    ) -> Tuple[List[ValidationError], List[ValidationError], List[ValidationError]]:
        """Validate time series consistency."""
        errors = []
        warnings = []
        info = []
        
        if len(data) < 2:
            return errors, warnings, info
            
        # Check timestamp ordering
        timestamps = [bar.get('timestamp') for bar in data if bar.get('timestamp')]
        if len(timestamps) != len(data):
            errors.append(ValidationError(
                rule_name="timestamp_series",
                severity="error", 
                message="Some bars missing timestamps"
            ))
        else:
            # Check if timestamps are in order
            sorted_timestamps = sorted(timestamps)
            if timestamps != sorted_timestamps:
                warnings.append(ValidationError(
                    rule_name="timestamp_series",
                    severity="warning",
                    message="Timestamps not in chronological order"
                ))
                
            # Check for duplicate timestamps
            unique_timestamps = set(timestamps)
            if len(unique_timestamps) != len(timestamps):
                duplicate_count = len(timestamps) - len(unique_timestamps)
                warnings.append(ValidationError(
                    rule_name="timestamp_series",
                    severity="warning",
                    message=f"Found {duplicate_count} duplicate timestamps"
                ))
                
        return errors, warnings, info

    async def _resolve_duplicate_bars(
        self, 
        bars_group: List[Tuple[int, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Resolve duplicate bars using latest data strategy."""
        if len(bars_group) == 1:
            return bars_group[0][1]
            
        # Strategy: Take the bar with the highest volume, or latest in sequence
        best_bar = None
        best_volume = -1
        best_index = -1
        
        for index, bar in bars_group:
            volume = bar.get('volume', 0)
            if volume > best_volume or (volume == best_volume and index > best_index):
                best_bar = bar
                best_volume = volume
                best_index = index
                
        logger.debug(f"Resolved {len(bars_group)} duplicate bars, selected bar with volume {best_volume}")
        return best_bar

    def _calculate_quality_score(
        self, 
        data: List[Dict[str, Any]], 
        errors: List[ValidationError], 
        warnings: List[ValidationError]
    ) -> float:
        """Calculate data quality score based on validation results."""
        if not data:
            return 0.0
            
        # Base score starts at 1.0
        score = 1.0
        
        # Deduct for errors (major impact)
        error_penalty = len(errors) / len(data) * 0.5  # Up to 50% penalty
        score -= min(error_penalty, 0.5)
        
        # Deduct for warnings (minor impact)  
        warning_penalty = len(warnings) / len(data) * 0.2  # Up to 20% penalty
        score -= min(warning_penalty, 0.2)
        
        # Additional quality factors
        
        # Completeness factor (penalize missing data)
        complete_bars = sum(1 for bar in data if self._is_bar_complete(bar))
        completeness = complete_bars / len(data)
        score *= completeness
        
        # Consistency factor (penalize extreme variations)
        consistency_score = self._calculate_consistency_score(data)
        score *= consistency_score
        
        return max(0.0, min(1.0, score))

    def _calculate_quality_score_sync(self, data: List[Dict[str, Any]]) -> float:
        """Synchronous version of quality score calculation."""
        return self._calculate_quality_score(data, [], [])

    def _is_bar_complete(self, bar: Dict[str, Any]) -> bool:
        """Check if a bar has all required fields."""
        required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        return all(field in bar and bar[field] is not None for field in required_fields)

    def _calculate_consistency_score(self, data: List[Dict[str, Any]]) -> float:
        """Calculate consistency score based on price movements."""
        if len(data) < 2:
            return 1.0
            
        extreme_movements = 0
        total_movements = 0
        
        for i in range(1, len(data)):
            prev_bar = data[i-1]
            curr_bar = data[i]
            
            if (prev_bar.get('close') and curr_bar.get('open') and
                prev_bar['close'] > 0 and curr_bar['open'] > 0):
                
                change_percent = abs((curr_bar['open'] - prev_bar['close']) / prev_bar['close'] * 100)
                total_movements += 1
                
                # Flag movements greater than 20%
                if change_percent > 20.0:
                    extreme_movements += 1
                    
        if total_movements == 0:
            return 1.0
            
        # Penalize datasets with many extreme movements
        consistency_ratio = 1.0 - (extreme_movements / total_movements * 0.5)
        return max(0.5, consistency_ratio)  # Minimum 50% consistency score

    def _get_expected_time_delta(self, frequency: str) -> Optional[timedelta]:
        """Get expected time delta for a frequency."""
        frequency_deltas = {
            "1min": timedelta(minutes=1),
            "5min": timedelta(minutes=5),
            "15min": timedelta(minutes=15),
            "30min": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1),
            "1w": timedelta(weeks=1),
            "1M": timedelta(days=30)  # Approximate
        }
        return frequency_deltas.get(frequency)

    # Validation rule implementations
    
    def _validate_required_fields(self, bar: Dict[str, Any], index: int) -> List[str]:
        """Validate required fields are present."""
        required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        errors = []
        
        for field in required_fields:
            if field not in bar or bar[field] is None:
                errors.append(f"Missing required field: {field}")
                
        return errors

    def _validate_numeric_fields(self, bar: Dict[str, Any], index: int) -> List[str]:
        """Validate numeric fields are valid numbers."""
        numeric_fields = ['open', 'high', 'low', 'close', 'volume']
        errors = []
        
        for field in numeric_fields:
            if field in bar and bar[field] is not None:
                try:
                    float(bar[field])
                except (ValueError, TypeError):
                    errors.append(f"Invalid numeric value for {field}: {bar[field]}")
                    
        return errors

    def _validate_price_relationships(self, bar: Dict[str, Any], index: int) -> List[str]:
        """Validate OHLC price relationships."""
        errors = []
        
        try:
            open_price = float(bar.get('open', 0))
            high_price = float(bar.get('high', 0))
            low_price = float(bar.get('low', 0))
            close_price = float(bar.get('close', 0))
            
            if high_price < max(open_price, close_price, low_price):
                errors.append("High price is less than open, close, or low price")
                
            if low_price > min(open_price, close_price, high_price):
                errors.append("Low price is greater than open, close, or high price")
                
        except (ValueError, TypeError):
            # Numeric validation will catch this
            pass
            
        return errors

    def _validate_positive_values(self, bar: Dict[str, Any], index: int) -> List[str]:
        """Validate that prices and volume are positive."""
        errors = []
        positive_fields = ['open', 'high', 'low', 'close', 'volume']
        
        for field in positive_fields:
            if field in bar and bar[field] is not None:
                try:
                    value = float(bar[field])
                    if value < 0:
                        errors.append(f"Negative value for {field}: {value}")
                    elif field in ['open', 'high', 'low', 'close'] and value == 0:
                        errors.append(f"Zero price for {field}")
                except (ValueError, TypeError):
                    pass
                    
        return errors

    def _validate_reasonable_ranges(self, bar: Dict[str, Any], index: int) -> List[str]:
        """Check for reasonable price and volume ranges."""
        warnings = []
        
        price_fields = ['open', 'high', 'low', 'close']
        for field in price_fields:
            if field in bar and bar[field] is not None:
                try:
                    value = float(bar[field])
                    if value < self._quality_thresholds["min_price"]:
                        warnings.append(f"Very low {field} price: {value}")
                    elif value > self._quality_thresholds["max_price"]:
                        warnings.append(f"Very high {field} price: {value}")
                except (ValueError, TypeError):
                    pass
                    
        if 'volume' in bar and bar['volume'] is not None:
            try:
                volume = float(bar['volume'])
                if volume > self._quality_thresholds["max_volume"]:
                    warnings.append(f"Very high volume: {volume}")
            except (ValueError, TypeError):
                pass
                
        return warnings

    def _validate_timestamp(self, bar: Dict[str, Any], index: int) -> List[str]:
        """Validate timestamp format and value."""
        errors = []
        
        if 'timestamp' not in bar or bar['timestamp'] is None:
            errors.append("Missing timestamp")
            return errors
            
        timestamp = bar['timestamp']
        
        if not isinstance(timestamp, datetime):
            try:
                # Try to parse if it's a string
                if isinstance(timestamp, str):
                    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    errors.append(f"Invalid timestamp type: {type(timestamp)}")
            except ValueError:
                errors.append(f"Invalid timestamp format: {timestamp}")
                
        return errors

    def _validate_volume_consistency(self, bar: Dict[str, Any], index: int) -> List[str]:
        """Check volume consistency and patterns."""
        info = []
        
        if 'volume' in bar and bar['volume'] is not None:
            try:
                volume = float(bar['volume'])
                if volume == 0:
                    info.append("Zero volume detected")
            except (ValueError, TypeError):
                pass
                
        return info