"""
Data processing layer for variant performance analysis

Aggregates and processes variant performance data from the API.
Combines campaign, sequence, and variant data to calculate metrics
at the variant level (A, B, C, D, E) and campaign level.
"""
from collections import defaultdict
from typing import List, Dict, Any


def _calculate_rate(numerator: int, denominator: int) -> float:
    """
    Calculate percentage rate, handling zero division

    Args:
        numerator: The numerator value
        denominator: The denominator value

    Returns:
        Percentage rate rounded to 2 decimal places, or 0.0 if denominator is 0
    """
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def aggregate_variant_performance(
    variant_stats_by_campaign: Dict[int, Dict[int, Dict[int, Dict[str, Any]]]],
    campaign_sequences: Dict[int, List[Dict[str, Any]]]
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Aggregate variant performance metrics by variant label (A, B, C, D, E)

    Combines metrics from multiple sequences within a campaign, aggregating
    variants with the same label (e.g., all "A" variants across sequences).

    Args:
        variant_stats_by_campaign: Dictionary mapping campaign_id -> sequence_id -> variant_id -> metrics
        campaign_sequences: Dictionary mapping campaign_id -> list of sequences with variants

    Returns:
        Dictionary mapping campaign_id -> list of aggregated variant metrics.
        Only includes variants with labels A, B, C, D, E.
    """
    result = {}

    for campaign_id, sequences in campaign_sequences.items():
        # Use defaultdict to aggregate by variant label
        variant_aggregates = defaultdict(lambda: {
            "variant_sent_count": 0,
            "variant_open_count": 0,
            "variant_click_count": 0,
            "variant_reply_count": 0,
            "variant_bounce_count": 0,
            "variant_positive_reply_count": 0,
            "variant_unsubscribed_count": 0,
            "variant_failed_count": 0,
            "variant_stopped_count": 0,
            "variant_skipped_count": 0,
            "variant_total_count": 0,
        })

        # Track first subject/body seen for each label
        variant_metadata = {}

        for sequence in sequences:
            sequence_id = sequence["sequence_id"]

            # Get variant stats for this sequence
            if campaign_id not in variant_stats_by_campaign:
                continue
            if sequence_id not in variant_stats_by_campaign[campaign_id]:
                continue

            sequence_variants_stats = variant_stats_by_campaign[campaign_id][sequence_id]

            # Aggregate by variant label
            for variant_info in sequence["variants"]:
                variant_id = variant_info["variant_id"]
                variant_label = variant_info["variant_label"]

                # Only process A, B, C, D, E variants
                if variant_label not in ("A", "B", "C", "D", "E"):
                    continue

                # Get stats for this variant
                if variant_id not in sequence_variants_stats:
                    continue

                stats = sequence_variants_stats[variant_id]

                # Aggregate counts
                variant_aggregates[variant_label]["variant_sent_count"] += stats.get("variant_sent_count", 0)
                variant_aggregates[variant_label]["variant_open_count"] += stats.get("variant_open_count", 0)
                variant_aggregates[variant_label]["variant_click_count"] += stats.get("variant_click_count", 0)
                variant_aggregates[variant_label]["variant_reply_count"] += stats.get("variant_reply_count", 0)
                variant_aggregates[variant_label]["variant_bounce_count"] += stats.get("variant_bounce_count", 0)
                variant_aggregates[variant_label]["variant_positive_reply_count"] += stats.get("variant_positive_reply_count", 0)
                variant_aggregates[variant_label]["variant_unsubscribed_count"] += stats.get("variant_unsubscribed_count", 0)
                variant_aggregates[variant_label]["variant_failed_count"] += stats.get("variant_failed_count", 0)
                variant_aggregates[variant_label]["variant_stopped_count"] += stats.get("variant_stopped_count", 0)
                variant_aggregates[variant_label]["variant_skipped_count"] += stats.get("variant_skipped_count", 0)
                variant_aggregates[variant_label]["variant_total_count"] += stats.get("variant_total_count", 0)

                # Store metadata from first variant with this label
                if variant_label not in variant_metadata:
                    variant_metadata[variant_label] = {
                        "variant_subject": variant_info.get("variant_subject", ""),
                        "variant_email_body": variant_info.get("variant_email_body", ""),
                    }

        # Build final variant list with calculated rates
        variants = []
        for variant_label, counts in variant_aggregates.items():
            sent_count = counts["variant_sent_count"]
            reply_count = counts["variant_reply_count"]
            positive_reply_count = counts["variant_positive_reply_count"]
            open_count = counts["variant_open_count"]
            click_count = counts["variant_click_count"]

            variant_data = {
                "variant_label": variant_label,
                **counts,
                **variant_metadata[variant_label],
                # Calculate rates
                "variant_reply_rate": _calculate_rate(reply_count, sent_count),
                "variant_positive_reply_rate": _calculate_rate(positive_reply_count, sent_count),
                "variant_positive_reply_rate_of_replies": _calculate_rate(positive_reply_count, reply_count),
                "variant_open_rate": _calculate_rate(open_count, sent_count),
                "variant_click_rate": _calculate_rate(click_count, sent_count),
            }
            variants.append(variant_data)

        # Sort by label for consistent ordering
        variants.sort(key=lambda v: v["variant_label"])

        if variants:
            result[campaign_id] = variants

    return result


def calculate_campaign_stats(
    campaign_analytics: Dict[int, Dict[str, Any]],
    campaigns: List[Dict[str, Any]]
) -> Dict[int, Dict[str, Any]]:
    """
    Calculate campaign-level statistics from analytics data

    Args:
        campaign_analytics: Dictionary mapping campaign_id -> analytics metrics
        campaigns: List of campaign dictionaries

    Returns:
        Dictionary mapping campaign_id -> campaign statistics
    """
    result = {}

    for campaign in campaigns:
        campaign_id = campaign.get("id")
        if campaign_id is None:
            continue

        if campaign_id not in campaign_analytics:
            continue

        analytics = campaign_analytics[campaign_id]

        result[campaign_id] = {
            "campaign_id": campaign_id,
            "campaign_name": campaign.get("name", ""),
            "total_sent": analytics.get("sent_count", 0),
            "total_opens": analytics.get("open_count", 0),
            "total_clicks": analytics.get("click_count", 0),
            "total_replies": analytics.get("reply_count", 0),
            "total_positive_replies": analytics.get("positive_reply_count", 0),
            "campaign_reply_rate": analytics.get("reply_rate", 0.0),
            "campaign_positive_reply_rate": analytics.get("positive_reply_rate", 0.0),
            "campaign_positive_reply_rate_of_replies": analytics.get("positive_reply_rate_of_replies", 0.0),
            "campaign_open_rate": analytics.get("open_rate", 0.0),
            "campaign_click_rate": analytics.get("click_rate", 0.0),
        }

    return result


def build_variant_rows(
    campaigns: List[Dict[str, Any]],
    campaign_analytics: Dict[int, Dict[str, Any]],
    campaign_sequences: Dict[int, List[Dict[str, Any]]],
    variant_stats_by_campaign: Dict[int, Dict[int, Dict[int, Dict[str, Any]]]]
) -> List[Dict[str, Any]]:
    """
    Build complete variant rows combining all data sources

    Each row contains:
    - Campaign information
    - Sequence information
    - Variant metrics (aggregated by label)
    - Campaign-level statistics

    Args:
        campaigns: List of campaign dictionaries
        campaign_analytics: Dictionary mapping campaign_id -> analytics metrics
        campaign_sequences: Dictionary mapping campaign_id -> list of sequences
        variant_stats_by_campaign: Dictionary mapping campaign_id -> sequence_id -> variant_id -> metrics

    Returns:
        List of variant rows with all combined data
    """
    # Get campaign stats
    campaign_stats = calculate_campaign_stats(campaign_analytics, campaigns)

    # Get aggregated variant performance
    aggregated_variants = aggregate_variant_performance(
        variant_stats_by_campaign,
        campaign_sequences
    )

    # Build rows
    rows = []

    for campaign in campaigns:
        campaign_id = campaign.get("id")
        if campaign_id is None:
            continue

        # Skip if no campaign stats
        if campaign_id not in campaign_stats:
            continue

        # Skip if no aggregated variants
        if campaign_id not in aggregated_variants:
            continue

        stats = campaign_stats[campaign_id]
        variants = aggregated_variants[campaign_id]

        # Get sequences for this campaign
        sequences = campaign_sequences.get(campaign_id, [])

        for variant in variants:
            # Find the first sequence that has this variant label
            variant_label = variant["variant_label"]
            sequence_info = None

            for sequence in sequences:
                for v in sequence["variants"]:
                    if v["variant_label"] == variant_label:
                        sequence_info = {
                            "sequence_id": sequence["sequence_id"],
                            "seq_number": sequence["seq_number"],
                            "sequence_subject": sequence["sequence_subject"],
                        }
                        break
                if sequence_info:
                    break

            # If no sequence found, use defaults
            if not sequence_info:
                sequence_info = {
                    "sequence_id": None,
                    "seq_number": None,
                    "sequence_subject": "",
                }

            # Build complete row
            row = {
                # Campaign info
                "campaign_id": campaign_id,
                "campaign_name": campaign.get("name", ""),
                # Sequence info
                "sequence_id": sequence_info["sequence_id"],
                "seq_number": sequence_info["seq_number"],
                "sequence_subject": sequence_info["sequence_subject"],
                # Variant info and metrics
                **variant,
                # Campaign stats
                "campaign_reply_rate": stats["campaign_reply_rate"],
                "campaign_positive_reply_rate": stats["campaign_positive_reply_rate"],
                "campaign_positive_reply_rate_of_replies": stats["campaign_positive_reply_rate_of_replies"],
                "campaign_open_rate": stats["campaign_open_rate"],
                "campaign_click_rate": stats["campaign_click_rate"],
            }

            rows.append(row)

    return rows
