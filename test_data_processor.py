"""
Tests for data processor layer
"""
import pytest
from collections import defaultdict
from datetime import date
from data_processor import (
    aggregate_variant_performance,
    calculate_campaign_stats
)


def test_aggregate_variant_performance():
    """Test aggregating by variant label"""
    rows = [
        {"variant_label": "A", "variant_sent_count": 100, "variant_reply_count": 10, "variant_positive_reply_count": 5},
        {"variant_label": "B", "variant_sent_count": 100, "variant_reply_count": 15, "variant_positive_reply_count": 8},
        {"variant_label": "A", "variant_sent_count": 50, "variant_reply_count": 6, "variant_positive_reply_count": 3},
    ]

    result = aggregate_variant_performance(rows)

    assert len(result) == 2
    assert result["A"]["total_sent"] == 150
    assert result["A"]["total_replies"] == 16
    assert result["B"]["total_sent"] == 100


def test_calculate_campaign_stats():
    """Test campaign-level aggregation"""
    rows = [
        {"campaign_id": 1, "campaign_name": "Camp A", "variant_sent_count": 100, "variant_reply_count": 10, "variant_positive_reply_count": 5},
        {"campaign_id": 1, "campaign_name": "Camp A", "variant_sent_count": 50, "variant_reply_count": 6, "variant_positive_reply_count": 3},
        {"campaign_id": 2, "campaign_name": "Camp B", "variant_sent_count": 200, "variant_reply_count": 20, "variant_positive_reply_count": 10},
    ]

    result = calculate_campaign_stats(rows)

    assert len(result) == 2
    assert result[1]["total_sent"] == 150
    assert result[2]["total_sent"] == 200
