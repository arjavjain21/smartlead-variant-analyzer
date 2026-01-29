"""
Data processing layer for variant performance analysis

Aggregates and processes variant performance data from the API.
Combines campaign, sequence, and variant data to calculate metrics
at the variant level (A, B, C, D, E) and campaign level.
"""
from collections import defaultdict
from typing import List, Dict, Any


def _safe_int(value: Any) -> int:
    """Safely convert value to int"""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


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
        variant_label = (row.get('variant_label') or '').strip().upper()
        if not variant_label or variant_label not in ['A', 'B', 'C', 'D', 'E']:
            continue

        campaign_id = row.get('campaign_id', '')

        variant_stats[variant_label]['total_sent'] += _safe_int(row.get('variant_sent_count'))
        variant_stats[variant_label]['total_replies'] += _safe_int(row.get('variant_reply_count'))
        variant_stats[variant_label]['total_positive_replies'] += _safe_int(row.get('variant_positive_reply_count'))
        variant_stats[variant_label]['total_opens'] += _safe_int(row.get('variant_open_count'))
        variant_stats[variant_label]['total_clicks'] += _safe_int(row.get('variant_click_count'))
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
        stats['total_sent'] += _safe_int(row.get('variant_sent_count'))
        stats['total_replies'] += _safe_int(row.get('variant_reply_count'))
        stats['total_positive'] += _safe_int(row.get('variant_positive_reply_count'))
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
    - Variant metrics
    - Campaign-level analytics

    Args:
        campaigns: List of campaign dictionaries
        campaign_analytics: Dictionary mapping campaign_id -> analytics metrics
        campaign_sequences: Dictionary mapping campaign_id -> list of sequences
        variant_stats_by_campaign: Dictionary mapping campaign_id -> sequence_id -> variant_id -> metrics

    Returns:
        List of variant rows with all combined data
    """
    rows = []
    campaigns_by_id = {c["id"]: c for c in campaigns if c.get("id") is not None}

    for campaign_id, sequences in campaign_sequences.items():
        camp = campaigns_by_id.get(campaign_id)
        if not camp:
            continue

        c_metrics = campaign_analytics.get(campaign_id, {}) or {}
        variant_stats_map = variant_stats_by_campaign.get(campaign_id, {}) or {}

        for seq in sequences:
            seq_id = seq.get("sequence_id")
            variants = seq.get("variants", []) or []

            for variant in variants:
                variant_id = variant.get("variant_id")
                v_metrics = variant_stats_map.get(seq_id, {}).get(variant_id, {}) or {}

                # Default variant metrics
                v_metrics_default = {
                    "variant_sent_count": 0,
                    "variant_open_count": 0,
                    "variant_click_count": 0,
                    "variant_reply_count": 0,
                    "variant_positive_reply_count": 0,
                    "variant_reply_rate": 0.0,
                    "variant_positive_reply_rate": 0.0,
                    "variant_positive_reply_rate_of_replies": 0.0,
                    "variant_open_rate": 0.0,
                    "variant_click_rate": 0.0,
                    "variant_label": variant.get("variant_label", "Unknown"),
                }
                v_metrics_full = {**v_metrics_default, **v_metrics}

                row = {
                    # Campaign level
                    "client_id": camp.get("client_id"),
                    "campaign_id": campaign_id,
                    "campaign_name": camp.get("name"),
                    "campaign_status": camp.get("status"),
                    "campaign_created_at": camp.get("created_at"),
                    # Campaign metrics
                    "campaign_sent_count": c_metrics.get("sent_count", 0),
                    "campaign_reply_count": c_metrics.get("reply_count", 0),
                    "campaign_positive_reply_count": c_metrics.get("positive_reply_count", 0),
                    "campaign_reply_rate": c_metrics.get("reply_rate", 0.0),
                    "campaign_positive_reply_rate": c_metrics.get("positive_reply_rate", 0.0),
                    "campaign_positive_reply_rate_of_replies": c_metrics.get("positive_reply_rate_of_replies", 0.0),
                    "campaign_open_count": c_metrics.get("open_count", 0),
                    "campaign_click_count": c_metrics.get("click_count", 0),
                    "campaign_open_rate": c_metrics.get("open_rate", 0.0),
                    "campaign_click_rate": c_metrics.get("click_rate", 0.0),
                    # Sequence level
                    "sequence_id": seq_id,
                    "sequence_number": seq.get("seq_number"),
                    "sequence_subject": seq.get("sequence_subject"),
                    # Variant level
                    "variant_id": variant_id,
                    "variant_label": v_metrics_full["variant_label"],
                    "variant_subject": variant.get("variant_subject", ""),
                    "variant_sent_count": v_metrics_full["variant_sent_count"],
                    "variant_open_count": v_metrics_full["variant_open_count"],
                    "variant_click_count": v_metrics_full["variant_click_count"],
                    "variant_reply_count": v_metrics_full["variant_reply_count"],
                    "variant_positive_reply_count": v_metrics_full["variant_positive_reply_count"],
                    "variant_reply_rate": v_metrics_full["variant_reply_rate"],
                    "variant_positive_reply_rate": v_metrics_full["variant_positive_reply_rate"],
                    "variant_positive_reply_rate_of_replies": v_metrics_full["variant_positive_reply_rate_of_replies"],
                    "variant_open_rate": v_metrics_full["variant_open_rate"],
                    "variant_click_rate": v_metrics_full["variant_click_rate"],
                }

                rows.append(row)

    return rows
