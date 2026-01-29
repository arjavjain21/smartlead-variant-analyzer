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
    rows: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate variant performance by variant label (A, B, C, D, E)

    Args:
        rows: List of variant-level data rows

    Returns:
        Dictionary mapping variant_label -> aggregated metrics
    """
    variant_stats = defaultdict(lambda: {
        'total_sent': 0,
        'total_replies': 0,
        'total_positive_replies': 0,
        'total_opens': 0,
        'total_clicks': 0,
        'campaign_count': set(),
    })

    for row in rows:
        variant_label = row.get('variant_label', '').strip().upper()
        if not variant_label or variant_label not in ['A', 'B', 'C', 'D', 'E']:
            continue

        campaign_id = row.get('campaign_id', '')

        variant_stats[variant_label]['total_sent'] += row.get('variant_sent_count', 0)
        variant_stats[variant_label]['total_replies'] += row.get('variant_reply_count', 0)
        variant_stats[variant_label]['total_positive_replies'] += row.get('variant_positive_reply_count', 0)
        variant_stats[variant_label]['total_opens'] += row.get('variant_open_count', 0)
        variant_stats[variant_label]['total_clicks'] += row.get('variant_click_count', 0)
        variant_stats[variant_label]['campaign_count'].add(campaign_id)

    # Calculate rates and prepare results
    results = {}
    for variant_label, stats in variant_stats.items():
        total_sent = stats['total_sent']
        total_replies = stats['total_replies']
        total_positive_replies = stats['total_positive_replies']
        total_opens = stats['total_opens']
        total_clicks = stats['total_clicks']
        num_campaigns = len(stats['campaign_count'])

        reply_rate = _calculate_rate(total_replies, total_sent)
        positive_reply_rate = _calculate_rate(total_positive_replies, total_sent)
        positive_reply_rate_of_replies = _calculate_rate(total_positive_replies, total_replies)
        open_rate = _calculate_rate(total_opens, total_sent)
        click_rate = _calculate_rate(total_clicks, total_sent)

        results[variant_label] = {
            'variant': variant_label,
            'total_sent': total_sent,
            'total_replies': total_replies,
            'total_positive_replies': total_positive_replies,
            'reply_rate': reply_rate,
            'positive_reply_rate': positive_reply_rate,
            'positive_reply_rate_of_replies': positive_reply_rate_of_replies,
            'open_rate': open_rate,
            'click_rate': click_rate,
            'num_campaigns': num_campaigns,
        }

    return results


def calculate_campaign_stats(
    rows: List[Dict[str, Any]]
) -> Dict[int, Dict[str, Any]]:
    """
    Aggregate metrics at campaign level

    Args:
        rows: List of variant-level data rows

    Returns:
        Dictionary mapping campaign_id -> campaign metrics
    """
    campaign_stats = {}

    for row in rows:
        campaign_id = row.get('campaign_id')

        if campaign_id not in campaign_stats:
            campaign_stats[campaign_id] = {
                'campaign_name': row.get('campaign_name', ''),
                'total_sent': 0,
                'total_replies': 0,
                'total_positive': 0,
                'variant_count': 0,
            }

        stats = campaign_stats[campaign_id]
        stats['total_sent'] += row.get('variant_sent_count', 0)
        stats['total_replies'] += row.get('variant_reply_count', 0)
        stats['total_positive'] += row.get('variant_positive_reply_count', 0)
        stats['variant_count'] += 1

    # Calculate rates
    for campaign_id, stats in campaign_stats.items():
        total_sent = stats['total_sent']
        total_replies = stats['total_replies']
        total_positive = stats['total_positive']

        stats['reply_rate'] = _calculate_rate(total_replies, total_sent)
        stats['positive_reply_rate'] = _calculate_rate(total_positive, total_sent)
        stats['positive_reply_rate_of_replies'] = _calculate_rate(total_positive, total_replies)

    return campaign_stats


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
