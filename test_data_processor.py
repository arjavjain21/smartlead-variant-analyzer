"""
Tests for data processor layer
"""
import pytest
from collections import defaultdict
from datetime import date
from data_processor import (
    aggregate_variant_performance,
    calculate_campaign_stats,
    build_variant_rows
)


def test_aggregate_variant_performance():
    """Test aggregating variant metrics by label (A, B, C, D, E)"""
    # Mock variant statistics data
    variant_stats_by_campaign = {
        1001: {
            1: {  # sequence_id
                10: {  # variant_id
                    "variant_sent_count": 100,
                    "variant_open_count": 50,
                    "variant_click_count": 20,
                    "variant_reply_count": 10,
                    "variant_bounce_count": 2,
                    "variant_positive_reply_count": 5,
                    "variant_label": "A",
                    "variant_reply_rate": 10.0,
                    "variant_positive_reply_rate": 5.0,
                    "variant_positive_reply_rate_of_replies": 50.0,
                    "variant_open_rate": 50.0,
                    "variant_click_rate": 20.0,
                },
                11: {
                    "variant_sent_count": 200,
                    "variant_open_count": 80,
                    "variant_click_count": 30,
                    "variant_reply_count": 15,
                    "variant_bounce_count": 3,
                    "variant_positive_reply_count": 8,
                    "variant_label": "B",
                    "variant_reply_rate": 7.5,
                    "variant_positive_reply_rate": 4.0,
                    "variant_positive_reply_rate_of_replies": 53.33,
                    "variant_open_rate": 40.0,
                    "variant_click_rate": 15.0,
                },
                12: {
                    "variant_sent_count": 150,
                    "variant_open_count": 60,
                    "variant_click_count": 25,
                    "variant_reply_count": 12,
                    "variant_bounce_count": 1,
                    "variant_positive_reply_count": 6,
                    "variant_label": "A",  # Same label as first variant
                    "variant_reply_rate": 8.0,
                    "variant_positive_reply_rate": 4.0,
                    "variant_positive_reply_rate_of_replies": 50.0,
                    "variant_open_rate": 40.0,
                    "variant_click_rate": 16.67,
                },
            }
        }
    }

    campaign_sequences = {
        1001: [
            {
                "sequence_id": 1,
                "seq_number": 1,
                "sequence_subject": "Test Subject",
                "variants": [
                    {
                        "variant_id": 10,
                        "variant_label": "A",
                        "variant_subject": "Subject A",
                        "variant_email_body": "Body A",
                    },
                    {
                        "variant_id": 11,
                        "variant_label": "B",
                        "variant_subject": "Subject B",
                        "variant_email_body": "Body B",
                    },
                    {
                        "variant_id": 12,
                        "variant_label": "A",
                        "variant_subject": "Subject A2",
                        "variant_email_body": "Body A2",
                    },
                ]
            }
        ]
    }

    result = aggregate_variant_performance(variant_stats_by_campaign, campaign_sequences)

    # Should aggregate by variant label across all sequences
    assert len(result) == 1  # One campaign
    assert 1001 in result

    variants = result[1001]
    assert len(variants) == 2  # Two unique labels: A and B

    # Check variant A (aggregated from variant_ids 10 and 12)
    variant_a = next(v for v in variants if v["variant_label"] == "A")
    assert variant_a["variant_sent_count"] == 250  # 100 + 150
    assert variant_a["variant_open_count"] == 110  # 50 + 60
    assert variant_a["variant_click_count"] == 45  # 20 + 25
    assert variant_a["variant_reply_count"] == 22  # 10 + 12
    assert variant_a["variant_positive_reply_count"] == 11  # 5 + 6
    assert variant_a["variant_reply_rate"] == 8.8  # 22/250 * 100
    assert variant_a["variant_positive_reply_rate"] == 4.4  # 11/250 * 100
    assert round(variant_a["variant_positive_reply_rate_of_replies"], 2) == 50.0  # 11/22 * 100
    assert variant_a["variant_open_rate"] == 44.0  # 110/250 * 100
    assert variant_a["variant_click_rate"] == 18.0  # 45/250 * 100

    # Check variant B
    variant_b = next(v for v in variants if v["variant_label"] == "B")
    assert variant_b["variant_sent_count"] == 200
    assert variant_b["variant_open_count"] == 80
    assert variant_b["variant_reply_count"] == 15
    assert variant_b["variant_positive_reply_count"] == 8


def test_calculate_campaign_stats():
    """Test calculating campaign-level statistics"""
    # Mock campaign analytics data
    campaign_analytics = {
        1001: {
            "total_count": 1000,
            "sent_count": 950,
            "skipped_count": 50,
            "open_count": 400,
            "click_count": 150,
            "reply_count": 80,
            "bounce_count": 10,
            "failed_count": 5,
            "stopped_count": 3,
            "unsubscribed_count": 2,
            "positive_reply_count": 40,
            "reply_rate": 8.42,
            "positive_reply_rate": 4.21,
            "positive_reply_rate_of_replies": 50.0,
            "open_rate": 42.11,
            "click_rate": 15.79,
        }
    }

    campaigns = [
        {
            "id": 1001,
            "name": "Test Campaign",
            "created_at": "2025-11-20T10:00:00Z",
            "status": "running"
        }
    ]

    result = calculate_campaign_stats(campaign_analytics, campaigns)

    assert len(result) == 1
    assert 1001 in result

    stats = result[1001]
    assert stats["campaign_id"] == 1001
    assert stats["campaign_name"] == "Test Campaign"
    assert stats["total_sent"] == 950
    assert stats["total_opens"] == 400
    assert stats["total_clicks"] == 150
    assert stats["total_replies"] == 80
    assert stats["total_positive_replies"] == 40
    assert stats["campaign_reply_rate"] == 8.42
    assert stats["campaign_positive_reply_rate"] == 4.21
    assert stats["campaign_open_rate"] == 42.11
    assert stats["campaign_click_rate"] == 15.79


def test_aggregate_variant_performance_filters_to_abcde():
    """Test that only variants with labels A, B, C, D, E are included"""
    variant_stats_by_campaign = {
        1001: {
            1: {
                10: {
                    "variant_sent_count": 100,
                    "variant_open_count": 50,
                    "variant_click_count": 20,
                    "variant_reply_count": 10,
                    "variant_bounce_count": 0,
                    "variant_positive_reply_count": 5,
                    "variant_label": "A",
                    "variant_reply_rate": 10.0,
                    "variant_positive_reply_rate": 5.0,
                    "variant_positive_reply_rate_of_replies": 50.0,
                    "variant_open_rate": 50.0,
                    "variant_click_rate": 20.0,
                },
                11: {
                    "variant_sent_count": 100,
                    "variant_open_count": 50,
                    "variant_click_count": 20,
                    "variant_reply_count": 10,
                    "variant_bounce_count": 0,
                    "variant_positive_reply_count": 5,
                    "variant_label": "F",  # Should be filtered out
                    "variant_reply_rate": 10.0,
                    "variant_positive_reply_rate": 5.0,
                    "variant_positive_reply_rate_of_replies": 50.0,
                    "variant_open_rate": 50.0,
                    "variant_click_rate": 20.0,
                },
            }
        }
    }

    campaign_sequences = {
        1001: [
            {
                "sequence_id": 1,
                "seq_number": 1,
                "sequence_subject": "Test",
                "variants": [
                    {
                        "variant_id": 10,
                        "variant_label": "A",
                        "variant_subject": "Subject A",
                        "variant_email_body": "Body A",
                    },
                    {
                        "variant_id": 11,
                        "variant_label": "F",
                        "variant_subject": "Subject F",
                        "variant_email_body": "Body F",
                    },
                ]
            }
        ]
    }

    result = aggregate_variant_performance(variant_stats_by_campaign, campaign_sequences)

    # Only variant A should be included
    assert len(result[1001]) == 1
    assert result[1001][0]["variant_label"] == "A"


def test_aggregate_variant_performance_handles_zero_denominator():
    """Test that zero division is handled correctly"""
    variant_stats_by_campaign = {
        1001: {
            1: {
                10: {
                    "variant_sent_count": 0,  # Zero sent count
                    "variant_open_count": 0,
                    "variant_click_count": 0,
                    "variant_reply_count": 0,
                    "variant_bounce_count": 0,
                    "variant_positive_reply_count": 0,
                    "variant_label": "A",
                    "variant_reply_rate": 0.0,
                    "variant_positive_reply_rate": 0.0,
                    "variant_positive_reply_rate_of_replies": 0.0,
                    "variant_open_rate": 0.0,
                    "variant_click_rate": 0.0,
                },
            }
        }
    }

    campaign_sequences = {
        1001: [
            {
                "sequence_id": 1,
                "seq_number": 1,
                "sequence_subject": "Test",
                "variants": [
                    {
                        "variant_id": 10,
                        "variant_label": "A",
                        "variant_subject": "Subject A",
                        "variant_email_body": "Body A",
                    },
                ]
            }
        ]
    }

    result = aggregate_variant_performance(variant_stats_by_campaign, campaign_sequences)

    # Should handle zero gracefully
    assert len(result[1001]) == 1
    variant = result[1001][0]
    assert variant["variant_sent_count"] == 0
    assert variant["variant_reply_rate"] == 0.0
    assert variant["variant_open_rate"] == 0.0


def test_build_variant_rows_combines_all_data_sources():
    """Test that build_variant_rows combines campaign, sequence, and variant data"""
    campaigns = [
        {"id": 1001, "name": "Campaign A", "created_at": "2025-11-20T10:00:00Z"},
    ]

    campaign_analytics = {
        1001: {
            "sent_count": 1000,
            "reply_rate": 10.0,
            "positive_reply_rate": 5.0,
            "open_rate": 40.0,
            "click_rate": 15.0,
        }
    }

    campaign_sequences = {
        1001: [
            {
                "sequence_id": 1,
                "seq_number": 1,
                "sequence_subject": "Sequence Subject",
                "variants": [
                    {
                        "variant_id": 10,
                        "variant_label": "A",
                        "variant_subject": "Variant Subject",
                        "variant_email_body": "Variant Body",
                    }
                ]
            }
        ]
    }

    variant_stats_by_campaign = {
        1001: {
            1: {
                10: {
                    "variant_sent_count": 100,
                    "variant_open_count": 50,
                    "variant_click_count": 20,
                    "variant_reply_count": 10,
                    "variant_bounce_count": 2,
                    "variant_positive_reply_count": 5,
                    "variant_label": "A",
                    "variant_reply_rate": 10.0,
                    "variant_positive_reply_rate": 5.0,
                    "variant_positive_reply_rate_of_replies": 50.0,
                    "variant_open_rate": 50.0,
                    "variant_click_rate": 20.0,
                }
            }
        }
    }

    result = build_variant_rows(
        campaigns,
        campaign_analytics,
        campaign_sequences,
        variant_stats_by_campaign
    )

    assert len(result) == 1
    row = result[0]

    # Check campaign fields
    assert row["campaign_id"] == 1001
    assert row["campaign_name"] == "Campaign A"

    # Check sequence fields
    assert row["sequence_id"] == 1
    assert row["seq_number"] == 1
    assert row["sequence_subject"] == "Sequence Subject"

    # Check variant fields
    assert row["variant_label"] == "A"
    assert row["variant_subject"] == "Variant Subject"
    assert row["variant_email_body"] == "Variant Body"
    assert row["variant_sent_count"] == 100
    assert row["variant_reply_count"] == 10

    # Check campaign stats
    assert row["campaign_reply_rate"] == 10.0
    assert row["campaign_open_rate"] == 40.0
