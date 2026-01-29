"""
SmartLead API wrapper with retry logic
"""
import time
import requests
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional


BASE_URL = "https://server.smartlead.ai/api/v1"

# Retry configuration
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0
TIMEOUT = 30


def safe_int(value: Any) -> int:
    """Safely convert value to int"""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def calculate_rate(numerator: int, denominator: int) -> float:
    """Calculate percentage rate, handling zero denominator"""
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def get_with_retry(path: str, params: Dict[str, Any], max_retries: int = MAX_RETRIES) -> Dict[str, Any]:
    """
    Generic GET request with exponential backoff retry logic

    Args:
        path: API endpoint path (e.g., "/campaigns")
        params: Query parameters
        max_retries: Maximum number of retry attempts

    Returns:
        JSON response data

    Raises:
        RuntimeError: If request fails after all retries
    """
    url = f"{BASE_URL}{path}"

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
        except requests.RequestException as e:
            if attempt == max_retries:
                raise RuntimeError(f"Request error calling {url}: {e}")
            sleep_time = BACKOFF_FACTOR ** (attempt - 1)
            time.sleep(sleep_time)
            continue

        if resp.status_code == 200:
            try:
                return resp.json()
            except ValueError:
                raise RuntimeError(f"Invalid JSON from {url}: {resp.text}")

        # Retry on common transient codes
        if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
            sleep_time = BACKOFF_FACTOR ** (attempt - 1)
            time.sleep(sleep_time)
            continue

        # Any other non-200 is a hard error
        raise RuntimeError(
            f"GET {url} failed with {resp.status_code}: {resp.text}"
        )

    # Shouldn't reach here, but just in case
    raise RuntimeError(f"Failed to complete request to {url} after {max_retries} attempts")


def list_clients(api_key: str) -> List[Dict[str, Any]]:
    """
    Fetch all clients for the authenticated account

    Args:
        api_key: SmartLead API key

    Returns:
        List of client dictionaries with id, name, email, etc.

    Raises:
        RuntimeError: If API request fails
    """
    params = {"api_key": api_key}
    data = get_with_retry("/client/", params)

    if not isinstance(data, list):
        raise RuntimeError("Expected /client/ endpoint to return a list")

    return data


def get_campaigns_for_client(
    client_id: int,
    created_after: date,
    name_filter: str,
    api_key: str
) -> List[Dict[str, Any]]:
    """
    Fetch campaigns for a client, filtered by creation date and name pattern

    Args:
        client_id: SmartLead client ID
        created_after: Only include campaigns created on or after this date
        name_filter: Filter campaigns where name contains this string (case-insensitive)
        api_key: SmartLead API key

    Returns:
        List of filtered campaign dictionaries

    Raises:
        RuntimeError: If API request fails
    """
    params = {
        "api_key": api_key,
        "client_id": client_id,
    }

    data = get_with_retry("/campaigns", params)

    if not isinstance(data, list):
        raise RuntimeError("Expected campaigns endpoint to return a list")

    created_after_dt = datetime.combine(created_after, datetime.min.time(), tzinfo=timezone.utc)
    filtered = []

    for camp in data:
        # Filter by name pattern
        campaign_name = camp.get("name", "")
        if name_filter.lower() not in campaign_name.lower():
            continue

        # Filter by creation date
        created_at_str = camp.get("created_at")
        if not created_at_str:
            continue
        try:
            created_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        except ValueError:
            continue
        if created_dt >= created_after_dt:
            filtered.append(camp)

    return filtered


def get_campaign_analytics(
    campaigns: List[Dict[str, Any]],
    start_date: date,
    end_date: date,
    api_key: str
) -> Dict[int, Dict[str, Any]]:
    """
    Fetch top-level analytics for each campaign

    Args:
        campaigns: List of campaign dictionaries
        start_date: Analytics start date
        end_date: Analytics end date
        api_key: SmartLead API key

    Returns:
        Dictionary mapping campaign_id -> analytics metrics

    Raises:
        RuntimeError: If API request fails
    """
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    analytics = {}

    for camp in campaigns:
        campaign_id = camp.get("id")
        if campaign_id is None:
            continue

        params = {
            "api_key": api_key,
            "start_date": start_str,
            "end_date": end_str,
        }

        try:
            data = get_with_retry(
                f"/campaigns/{campaign_id}/top-level-analytics-by-date", params
            )
        except RuntimeError as e:
            # Log warning but continue with other campaigns
            print(f"Warning: failed campaign analytics for {campaign_id}: {e}")
            data = {}

        sent_count = safe_int(data.get("sent_count"))
        reply_count = safe_int(data.get("reply_count"))
        positive_reply_count = safe_int(data.get("positive_reply_count"))

        metrics = {
            "total_count": safe_int(data.get("total_count")),
            "sent_count": sent_count,
            "skipped_count": safe_int(data.get("skipped_count")),
            "open_count": safe_int(data.get("open_count")),
            "click_count": safe_int(data.get("click_count")),
            "reply_count": reply_count,
            "bounce_count": safe_int(data.get("bounce_count")),
            "failed_count": safe_int(data.get("failed_count")),
            "stopped_count": safe_int(data.get("stopped_count")),
            "unsubscribed_count": safe_int(data.get("unsubscribed_count")),
            "positive_reply_count": positive_reply_count,
            # Calculate rates
            "reply_rate": calculate_rate(reply_count, sent_count),
            "positive_reply_rate": calculate_rate(positive_reply_count, sent_count),
            "positive_reply_rate_of_replies": calculate_rate(positive_reply_count, reply_count),
            "open_rate": calculate_rate(safe_int(data.get("open_count")), sent_count),
            "click_rate": calculate_rate(safe_int(data.get("click_count")), sent_count),
        }

        analytics[campaign_id] = metrics

    return analytics


def get_campaign_sequences(
    campaigns: List[Dict[str, Any]],
    api_key: str
) -> Dict[int, List[Dict[str, Any]]]:
    """
    Fetch sequences for each campaign

    Args:
        campaigns: List of campaign dictionaries
        api_key: SmartLead API key

    Returns:
        Dictionary mapping campaign_id -> list of sequences with variants

    Raises:
        RuntimeError: If API request fails
    """
    campaign_sequences = {}

    for camp in campaigns:
        campaign_id = camp.get("id")
        if campaign_id is None:
            continue

        params = {"api_key": api_key}

        try:
            data = get_with_retry(f"/campaigns/{campaign_id}/sequences", params)
        except RuntimeError as e:
            print(f"Warning: failed sequences fetch for {campaign_id}: {e}")
            continue

        # Normalize to a list
        if isinstance(data, list):
            sequences_raw = data
        elif isinstance(data, dict):
            if "data" in data and isinstance(data["data"], list):
                sequences_raw = data["data"]
            else:
                sequences_raw = [data]
        else:
            print(f"Warning: unexpected sequences format for campaign {campaign_id}")
            continue

        sequences = []
        for seq in sequences_raw:
            seq_id = seq.get("id")
            if seq_id is None:
                continue

            variants_raw = seq.get("sequence_variants", []) or []
            variants = []
            for v in variants_raw:
                if v.get("is_deleted", False):
                    continue
                variants.append({
                    "variant_id": v.get("id"),
                    "variant_label": v.get("variant_label"),
                    "variant_subject": v.get("subject"),
                    "variant_email_body": v.get("email_body", ""),
                })

            if variants:  # Only add sequences that have variants
                sequences.append({
                    "sequence_id": seq_id,
                    "seq_number": seq.get("seq_number"),
                    "sequence_subject": seq.get("subject"),
                    "variants": variants,
                })

        if sequences:
            campaign_sequences[campaign_id] = sequences

    return campaign_sequences


def get_variant_statistics(
    campaign_ids: List[int],
    api_key: str
) -> Dict[int, Dict[int, Dict[str, Any]]]:
    """
    Fetch variant statistics for campaigns

    Args:
        campaign_ids: List of campaign IDs to fetch variants for
        api_key: SmartLead API key

    Returns:
        Dictionary mapping campaign_id -> sequence_id -> variant_id -> metrics

    Raises:
        RuntimeError: If API request fails
    """
    variant_stats_by_campaign = {}

    for campaign_id in campaign_ids:
        params = {"api_key": api_key}

        try:
            data = get_with_retry(f"/campaigns/{campaign_id}/variant-statistics", params)
        except RuntimeError as e:
            print(f"Warning: failed variant statistics for {campaign_id}: {e}")
            variant_stats_by_campaign[campaign_id] = {}
            continue

        if not isinstance(data, dict) or not data.get("ok"):
            print(f"Warning: unexpected variant statistics format for {campaign_id}")
            variant_stats_by_campaign[campaign_id] = {}
            continue

        rows = data.get("data", []) or []
        variant_stats = {}
        for row in rows:
            seq_id = row.get("email_campaign_seq_id")
            variant_id = row.get("seq_variant_id")

            # Skip entries without variant_id (sequence-level aggregates)
            if variant_id is None:
                continue

            if seq_id not in variant_stats:
                variant_stats[seq_id] = {}

            sent_count = safe_int(row.get("sent_count"))
            reply_count = safe_int(row.get("reply_count"))
            positive_reply_count = safe_int(row.get("positive_reply_count"))

            variant_stats[seq_id][variant_id] = {
                "variant_sent_count": sent_count,
                "variant_open_count": safe_int(row.get("open_count")),
                "variant_click_count": safe_int(row.get("click_count")),
                "variant_reply_count": reply_count,
                "variant_bounce_count": safe_int(row.get("bounce_count")),
                "variant_unsubscribed_count": safe_int(row.get("unsubscribed_count")),
                "variant_failed_count": safe_int(row.get("failed_count")),
                "variant_stopped_count": safe_int(row.get("stopped_count")),
                "variant_positive_reply_count": positive_reply_count,
                "variant_skipped_count": safe_int(row.get("skipped_count")),
                "variant_total_count": safe_int(row.get("total_count")),
                "variant_label": row.get("variant_label"),
                "variant_reply_rate": calculate_rate(reply_count, sent_count),
                "variant_positive_reply_rate": calculate_rate(positive_reply_count, sent_count),
                "variant_positive_reply_rate_of_replies": calculate_rate(positive_reply_count, reply_count),
                "variant_open_rate": calculate_rate(safe_int(row.get("open_count")), sent_count),
                "variant_click_rate": calculate_rate(safe_int(row.get("click_count")), sent_count),
            }

        variant_stats_by_campaign[campaign_id] = variant_stats

    return variant_stats_by_campaign
