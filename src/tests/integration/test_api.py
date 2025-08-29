"""
Integration tests for FastAPI endpoints.

Tests complete request-response cycles with database integration
and comprehensive API functionality validation.
"""

import pytest
from httpx import AsyncClient
import json
from datetime import datetime

from src.backend.models.instruments import InstrumentType, InstrumentStatus
from src.backend.models.alert_rules import RuleType, RuleCondition
from src.backend.models.alert_logs import AlertStatus, DeliveryStatus


class TestHealthAPI:
    """Test cases for health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_status_basic(self, test_client: AsyncClient):
        """Test basic health status endpoint."""
        response = await test_client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "ingestion_active" in data
        assert "api_connected" in data
        assert "active_instruments" in data
        assert "total_rules" in data
        assert isinstance(data["active_instruments"], int)
        assert isinstance(data["total_rules"], int)
    
    @pytest.mark.asyncio
    async def test_health_detailed_stats(self, test_client: AsyncClient):
        """Test detailed health statistics endpoint."""
        response = await test_client.get("/api/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "database_status" in data
        assert "total_instruments" in data
        assert "active_instruments" in data
        assert "total_rules" in data
        assert "active_rules" in data
        assert "total_ticks_today" in data
        assert "total_alerts_today" in data
        
        # Verify data types
        assert isinstance(data["total_instruments"], int)
        assert isinstance(data["active_instruments"], int)
        assert isinstance(data["total_rules"], int)
        assert isinstance(data["active_rules"], int)


class TestInstrumentsAPI:
    """Test cases for instruments API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_instruments_empty(self, test_client: AsyncClient):
        """Test getting instruments when database is empty."""
        response = await test_client.get("/api/instruments")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_get_instruments_with_data(self, test_client: AsyncClient, sample_instruments):
        """Test getting instruments with sample data."""
        response = await test_client.get("/api/instruments")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 3  # Sample fixtures provide 3 instruments
        
        # Verify instrument structure
        instrument = data[0]
        assert "id" in instrument
        assert "symbol" in instrument
        assert "name" in instrument
        assert "type" in instrument
        assert "status" in instrument
        assert "created_at" in instrument
    
    @pytest.mark.asyncio
    async def test_get_instruments_filtered_by_type(self, test_client: AsyncClient, sample_instruments):
        """Test getting instruments filtered by type."""
        response = await test_client.get("/api/instruments?type=future")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Should only return futures (ES and NQ from sample data)
        assert len(data) == 2
        
        for instrument in data:
            assert instrument["type"] == "future"
    
    @pytest.mark.asyncio
    async def test_get_instruments_active_only(self, test_client: AsyncClient, sample_instruments):
        """Test getting only active instruments."""
        response = await test_client.get("/api/instruments?active_only=true")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        for instrument in data:
            assert instrument["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_get_single_instrument(self, test_client: AsyncClient, sample_instruments):
        """Test getting a single instrument by ID."""
        instrument_id = sample_instruments[0].id
        response = await test_client.get(f"/api/instruments/{instrument_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == instrument_id
        assert data["symbol"] == sample_instruments[0].symbol
        assert data["name"] == sample_instruments[0].name
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_instrument(self, test_client: AsyncClient):
        """Test getting a non-existent instrument."""
        response = await test_client.get("/api/instruments/9999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Instrument not found"
    
    @pytest.mark.asyncio
    async def test_create_instrument(self, test_client: AsyncClient):
        """Test creating a new instrument."""
        instrument_data = {
            "symbol": "GC",
            "name": "Gold Futures",
            "type": "future",
            "status": "active"
        }
        
        response = await test_client.post("/api/instruments", json=instrument_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "GC"
        assert data["name"] == "Gold Futures"
        assert data["type"] == "future"
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_duplicate_instrument(self, test_client: AsyncClient, sample_instruments):
        """Test creating an instrument with duplicate symbol."""
        instrument_data = {
            "symbol": "ES",  # Duplicate symbol
            "name": "Another E-mini S&P 500",
            "type": "future",
            "status": "active"
        }
        
        response = await test_client.post("/api/instruments", json=instrument_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"]


class TestRulesAPI:
    """Test cases for alert rules API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_rules_empty(self, test_client: AsyncClient):
        """Test getting rules when database is empty."""
        response = await test_client.get("/api/rules")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 0
    
    @pytest.mark.asyncio
    async def test_get_rules_with_data(self, test_client: AsyncClient, sample_alert_rule):
        """Test getting rules with sample data."""
        response = await test_client.get("/api/rules")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 1
        
        # Verify rule structure
        rule = data[0]
        assert "id" in rule
        assert "instrument_id" in rule
        assert "instrument_symbol" in rule
        assert "rule_type" in rule
        assert "condition" in rule
        assert "threshold" in rule
        assert "active" in rule
        assert "created_at" in rule
    
    @pytest.mark.asyncio
    async def test_get_rules_filtered_by_instrument(self, test_client: AsyncClient, sample_alert_rule):
        """Test getting rules filtered by instrument."""
        instrument_id = sample_alert_rule.instrument_id
        response = await test_client.get(f"/api/rules?instrument_id={instrument_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        for rule in data:
            assert rule["instrument_id"] == instrument_id
    
    @pytest.mark.asyncio
    async def test_get_rules_active_only(self, test_client: AsyncClient, sample_alert_rule):
        """Test getting only active rules."""
        response = await test_client.get("/api/rules?active_only=true")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        for rule in data:
            assert rule["active"] is True
    
    @pytest.mark.asyncio
    async def test_get_single_rule(self, test_client: AsyncClient, sample_alert_rule):
        """Test getting a single rule by ID."""
        rule_id = sample_alert_rule.id
        response = await test_client.get(f"/api/rules/{rule_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == rule_id
        assert data["rule_type"] == sample_alert_rule.rule_type.value
        assert data["condition"] == sample_alert_rule.condition.value
        assert data["threshold"] == float(sample_alert_rule.threshold)
    
    @pytest.mark.asyncio
    async def test_create_rule(self, test_client: AsyncClient, sample_instruments):
        """Test creating a new alert rule."""
        instrument_id = sample_instruments[0].id
        rule_data = {
            "instrument_id": instrument_id,
            "rule_type": "threshold",
            "condition": "above",
            "threshold": 4600.0,
            "active": True,
            "name": "High Price Alert",
            "description": "Alert when ES goes above 4600",
            "cooldown_seconds": 120
        }
        
        response = await test_client.post("/api/rules", json=rule_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["instrument_id"] == instrument_id
        assert data["rule_type"] == "threshold"
        assert data["condition"] == "above"
        assert data["threshold"] == 4600.0
        assert data["active"] is True
        assert data["name"] == "High Price Alert"
        assert data["cooldown_seconds"] == 120
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_rule_invalid_instrument(self, test_client: AsyncClient):
        """Test creating a rule with invalid instrument ID."""
        rule_data = {
            "instrument_id": 9999,  # Non-existent instrument
            "rule_type": "threshold",
            "condition": "above",
            "threshold": 4600.0,
            "active": True
        }
        
        response = await test_client.post("/api/rules", json=rule_data)
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_update_rule(self, test_client: AsyncClient, sample_alert_rule):
        """Test updating an existing rule."""
        rule_id = sample_alert_rule.id
        update_data = {
            "threshold": 4550.0,
            "active": False,
            "name": "Updated Rule Name"
        }
        
        response = await test_client.put(f"/api/rules/{rule_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == rule_id
        assert data["threshold"] == 4550.0
        assert data["active"] is False
        assert data["name"] == "Updated Rule Name"
    
    @pytest.mark.asyncio
    async def test_delete_rule(self, test_client: AsyncClient, sample_alert_rule):
        """Test deleting a rule."""
        rule_id = sample_alert_rule.id
        
        response = await test_client.delete(f"/api/rules/{rule_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert str(rule_id) in data["message"]
        
        # Verify rule is deleted
        get_response = await test_client.get(f"/api/rules/{rule_id}")
        assert get_response.status_code == 404


class TestAlertsAPI:
    """Test cases for alerts API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_alerts_empty(self, test_client: AsyncClient):
        """Test getting alerts when database is empty."""
        response = await test_client.get("/api/alerts")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "alerts" in data
        assert "total" in data
        assert "has_more" in data
        assert "page" in data
        assert "limit" in data
        
        assert isinstance(data["alerts"], list)
        assert len(data["alerts"]) == 0
        assert data["total"] == 0
        assert data["has_more"] is False
        assert data["page"] == 1
        assert data["limit"] == 50
    
    @pytest.mark.asyncio
    async def test_get_alerts_with_pagination(self, test_client: AsyncClient):
        """Test getting alerts with pagination parameters."""
        response = await test_client.get("/api/alerts?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["limit"] == 10
        assert data["page"] == 1
        assert isinstance(data["alerts"], list)
    
    @pytest.mark.asyncio
    async def test_get_alerts_with_filters(self, test_client: AsyncClient, sample_instruments):
        """Test getting alerts with various filters."""
        instrument_id = sample_instruments[0].id
        
        # Test instrument filter
        response = await test_client.get(f"/api/alerts?instrument_id={instrument_id}")
        assert response.status_code == 200
        
        # Test status filters
        response = await test_client.get("/api/alerts?fired_status=fired")
        assert response.status_code == 200
        
        response = await test_client.get("/api/alerts?delivery_status=pending")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_alerts_stats(self, test_client: AsyncClient):
        """Test getting alert statistics."""
        response = await test_client.get("/api/alerts/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_alerts_today" in data
        assert "total_alerts_this_week" in data
        assert "alerts_by_instrument" in data
        assert "alerts_by_rule_type" in data
        
        assert isinstance(data["total_alerts_today"], int)
        assert isinstance(data["total_alerts_this_week"], int)
        assert isinstance(data["alerts_by_instrument"], dict)
        assert isinstance(data["alerts_by_rule_type"], dict)


class TestAPIErrorHandling:
    """Test cases for API error handling."""
    
    @pytest.mark.asyncio
    async def test_invalid_json_payload(self, test_client: AsyncClient):
        """Test handling of invalid JSON payload."""
        response = await test_client.post(
            "/api/instruments",
            content="invalid json",
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, test_client: AsyncClient):
        """Test handling of missing required fields."""
        incomplete_data = {
            "symbol": "TEST",
            # Missing required fields: name, type
        }
        
        response = await test_client.post("/api/instruments", json=incomplete_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_invalid_field_values(self, test_client: AsyncClient):
        """Test handling of invalid field values."""
        invalid_data = {
            "symbol": "TEST",
            "name": "Test Instrument",
            "type": "invalid_type",  # Invalid enum value
            "status": "active"
        }
        
        response = await test_client.post("/api/instruments", json=invalid_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_nonexistent_endpoints(self, test_client: AsyncClient):
        """Test accessing non-existent endpoints."""
        response = await test_client.get("/api/nonexistent")
        assert response.status_code == 404
        
        response = await test_client.post("/api/invalid/endpoint", json={})
        assert response.status_code == 404


class TestAPIPerformance:
    """Test cases for API performance requirements."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, test_client: AsyncClient):
        """Test that health endpoint responds within performance targets."""
        import time
        
        start_time = time.time()
        response = await test_client.get("/api/health")
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        # Health endpoint should respond within 100ms
        assert response_time_ms < 100, f"Health endpoint took {response_time_ms}ms"
    
    @pytest.mark.asyncio
    async def test_instruments_endpoint_performance(self, test_client: AsyncClient, sample_instruments):
        """Test that instruments endpoint responds within performance targets."""
        import time
        
        start_time = time.time()
        response = await test_client.get("/api/instruments")
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        # CRUD operations should respond within 100ms
        assert response_time_ms < 100, f"Instruments endpoint took {response_time_ms}ms"