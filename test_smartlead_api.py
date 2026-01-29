"""
Tests for SmartLead API wrapper
"""
import pytest
from unittest.mock import patch, MagicMock
from smartlead_api import (
    list_clients,
    get_campaigns_for_client,
    get_campaign_analytics,
    get_campaign_sequences,
    get_variant_statistics
)

def test_list_clients_success():
    """Test successful client listing"""
    with patch('smartlead_api.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 831, "name": "SEM", "email": "sem@example.com"},
            {"id": 107636, "name": "JAX", "email": "jax@example.com"}
        ]
        mock_get.return_value = mock_response

        result = list_clients("test_api_key")

        assert len(result) == 2
        assert result[0]["id"] == 831
        assert result[0]["name"] == "SEM"

def test_list_clients_retry_on_500():
    """Test retry logic on server error"""
    with patch('smartlead_api.requests.get') as mock_get:
        mock_get.side_effect = [
            MagicMock(status_code=500),  # First call fails
            MagicMock(status_code=200, json=lambda: [{"id": 831, "name": "SEM"}])  # Second succeeds
        ]

        result = list_clients("test_api_key")

        assert mock_get.call_count == 2
        assert len(result) == 1

def test_get_campaigns_filters_by_name_and_date():
    """Test campaign filtering logic"""
    with patch('smartlead_api.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 1,
                "name": "Sequence #34 Campaign A",
                "created_at": "2025-11-20T10:00:00Z"
            },
            {
                "id": 2,
                "name": "Other Campaign",
                "created_at": "2025-11-20T10:00:00Z"
            },
            {
                "id": 3,
                "name": "Sequence #34 Campaign B",
                "created_at": "2025-11-10T10:00:00Z"  # Too early
            }
        ]
        mock_get.return_value = mock_response

        from datetime import date
        result = get_campaigns_for_client(
            831,
            date(2025, 11, 15),
            "Sequence #34",
            "test_key"
        )

        assert len(result) == 1
        assert result[0]["id"] == 1
