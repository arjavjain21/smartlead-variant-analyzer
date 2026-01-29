# SmartLead Variant Performance Analyzer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Streamlit web application that analyzes SmartLead campaign variant performance, allowing users to compare A/B/C/D/E variants across campaigns with interactive visualizations and CSV export.

**Architecture:** Streamlit frontend (app.py) calling Python API wrapper (smartlead_api.py) to fetch data from SmartLead REST API, with data processing layer (data_processor.py) aggregating variant statistics. Deployed to Streamlit Community Cloud via GitHub.

**Tech Stack:** Python 3.12+, Streamlit 1.31+, Requests, Pandas, Plotly

---

## Task 1: Create Project Structure and Initial Setup

**Files:**
- Create: `variant-performance-analyzer/README.md`
- Create: `variant-performance-analyzer/requirements.txt`
- Create: `variant-performance-analyzer/.gitignore`
- Create: `variant-performance-analyzer/.streamlit/secrets.toml`
- Create: `variant-performance-analyzer/.streamlit/config.toml`

### Step 1: Initialize project and create README.md

Create: `/home/ubuntu/variant-performance-analyzer/README.md`

```markdown
# SmartLead Variant Performance Analyzer

A web-based tool to analyze and compare A/B/C/D/E variant performance across SmartLead campaigns.

## Features

- Interactive variant performance comparison
- Client browser with search
- Campaign filtering by name and date
- Multi-tab analysis (Overview, Comparison, Details, Campaigns)
- CSV export functionality
- Password-protected access

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure API key in `.streamlit/secrets.toml`:
   ```toml
   PASSWORD = "your_password_here"
   DEFAULT_API_KEY = "your_smartlead_api_key"
   ```

3. Run locally:
   ```bash
   streamlit run app.py
   ```

## Deployment

Deploy to Streamlit Community Cloud:
1. Push code to GitHub
2. Connect repository to Streamlit
3. Add secrets in Streamlit dashboard
4. Deploy

## API Endpoints Used

- GET /api/v1/client/ - List all clients
- GET /api/v1/campaigns - Get campaigns for client
- GET /api/v1/campaigns/{id}/top-level-analytics-by-date - Campaign analytics
- GET /api/v1/campaigns/{id}/sequences - Campaign sequences
- GET /api/v1/campaigns/{id}/variant-statistics - Variant statistics
```

### Step 2: Create requirements.txt

Create: `/home/ubuntu/variant-performance-analyzer/requirements.txt`

```txt
streamlit>=1.31.0
requests>=2.31.0
pandas>=2.0.0
plotly>=5.18.0
python-dateutil>=2.8.2
```

### Step 3: Create .gitignore

Create: `/home/ubuntu/variant-performance-analyzer/.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Streamlit
.streamlit/secrets.toml

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Data
*.csv
*.xlsx
*.json
!package.json
```

### Step 4: Create Streamlit secrets template

Create: `/home/ubuntu/variant-performance-analyzer/.streamlit/secrets.toml.example`

```toml
# Copy this file to secrets.toml and fill in your values

# Password to access the tool
PASSWORD = "change_me"

# Default API key (users can override in UI)
DEFAULT_API_KEY = "your_smartlead_api_key_here"
```

### Step 5: Create Streamlit config

Create: `/home/ubuntu/variant-performance-analyzer/.streamlit/config.toml`

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[client]
showErrorDetails = false
maxUploadSize = 200

[logger]
level = "info"
```

### Step 6: Commit initial setup

```bash
cd /home/ubuntu/variant-performance-analyzer
git init
git add README.md requirements.txt .gitignore .streamlit/
git commit -m "chore: initialize project structure and configuration"
```

---

## Task 2: Implement SmartLead API Wrapper

**Files:**
- Create: `variant-performance-analyzer/smartlead_api.py`
- Create: `variant-performance-analyzer/test_smartlead_api.py`

### Step 1: Write tests for API wrapper

Create: `/home/ubuntu/variant-performance-analyzer/test_smartlead_api.py`

```python
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
```

### Step 2: Run tests to verify they fail

```bash
cd /home/ubuntu/variant-performance-analyzer
python -m pytest test_smartlead_api.py -v
```

Expected: `ModuleNotFoundError: No module named 'smartlead_api'`

### Step 3: Implement API wrapper

Create: `/home/ubuntu/variant-performance-analyzer/smartlead_api.py`

```python
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
```

### Step 4: Run tests to verify they pass

```bash
cd /home/ubuntu/variant-performance-analyzer
python -m pytest test_smartlead_api.py -v
```

Expected: All tests pass

### Step 5: Commit API wrapper

```bash
cd /home/ubuntu/variant-performance-analyzer
git add smartlead_api.py test_smartlead_api.py
git commit -m "feat: implement SmartLead API wrapper with retry logic"
```

---

## Task 3: Implement Data Processing Layer

**Files:**
- Create: `variant-performance-analyzer/data_processor.py`
- Create: `variant-performance-analyzer/test_data_processor.py`

### Step 1: Write tests for data processor

Create: `/home/ubuntu/variant-performance-analyzer/test_data_processor.py`

```python
"""
Tests for data processor
"""
import pytest
from data_processor import (
    aggregate_variant_performance,
    build_variant_rows,
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
```

### Step 2: Run tests to verify they fail

```bash
cd /home/ubuntu/variant-performance-analyzer
python -m pytest test_data_processor.py -v
```

Expected: `ModuleNotFoundError: No module named 'data_processor'`

### Step 3: Implement data processor

Create: `/home/ubuntu/variant-performance-analyzer/data_processor.py`

```python
"""
Data processing and aggregation for variant analysis
"""
from typing import List, Dict, Any
from collections import defaultdict


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


def _calculate_rate(numerator: int, denominator: int) -> float:
    """Calculate percentage rate, handling zero denominator"""
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


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
    Build complete variant analysis rows combining all data sources

    Args:
        campaigns: List of campaign dictionaries
        campaign_analytics: Campaign-level analytics
        campaign_sequences: Sequences with variants
        variant_stats_by_campaign: Variant statistics

    Returns:
        List of detailed variant rows for analysis
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
```

### Step 4: Run tests to verify they pass

```bash
cd /home/ubuntu/variant-performance-analyzer
python -m pytest test_data_processor.py -v
```

Expected: All tests pass

### Step 5: Commit data processor

```bash
cd /home/ubuntu/variant-performance-analyzer
git add data_processor.py test_data_processor.py
git commit -m "feat: implement data processing layer for variant aggregation"
```

---

## Task 4: Implement Streamlit Application - Authentication and API Config

**Files:**
- Create: `variant-performance-analyzer/app.py`

### Step 1: Create basic app structure with authentication

Create: `/home/ubuntu/variant-performance-analyzer/app.py`

```python
"""
SmartLead Variant Performance Analyzer
"""
import streamlit as st
from datetime import date, timedelta
import streamlit.components.v1 as components

# Page config
st.set_page_config(
    page_title="Variant Performance Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF4B4B;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .winner-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def check_password():
    """Return True if password is correct"""
    def password_entered():
        if st.session_state["password"] == st.secrets.get("PASSWORD", ""):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔐 Variant Performance Analyzer")
        st.text_input(
            "Enter password to access",
            type="password",
            on_change=password_entered,
            key="password"
        )
        if not st.session_state["password_correct"]:
            st.error("😕 Incorrect password")
            st.stop()

    return True


def main():
    """Main application"""
    # Check authentication
    check_password()

    # Title
    st.markdown('<h1 class="main-title">🎯 SmartLead Variant Performance Analyzer</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # API Key
        default_api_key = st.secrets.get("DEFAULT_API_KEY", "")
        api_key = st.text_input(
            "SmartLead API Key",
            value=default_api_key,
            type="password",
            help="Enter your SmartLead API key"
        )

        if not api_key:
            st.warning("⚠️ Please enter API key to continue")
            st.stop()

        st.markdown("---")

        # Test connection button
        if st.button("🔌 Test Connection"):
            with st.spinner("Testing connection..."):
                try:
                    from smartlead_api import list_clients
                    clients = list_clients(api_key)
                    st.success(f"✅ Connected! Found {len(clients)} clients")
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")

        st.markdown("---")

        # Client selection
        st.subheader("1. Client Selection")

        client_selection_method = st.radio(
            "Select Client",
            ["Browse All Clients", "Enter Client ID Manually"],
            label_visibility="collapsed"
        )

        if client_selection_method == "Browse All Clients":
            if st.button("📋 Load Clients", use_container_width=True):
                with st.spinner("Loading clients..."):
                    try:
                        from smartlead_api import list_clients
                        clients = list_clients(api_key)

                        if clients:
                            st.session_state["clients"] = clients
                            st.success(f"✅ Loaded {len(clients)} clients")
                        else:
                            st.warning("No clients found")
                    except Exception as e:
                        st.error(f"❌ Error loading clients: {str(e)}")

            # Display clients if loaded
            if "clients" in st.session_state:
                clients = st.session_state["clients"]

                # Search
                search = st.text_input("🔍 Search clients", "")

                # Filter and display
                if search:
                    filtered = [c for c in clients if search.lower() in c.get("name", "").lower()]
                else:
                    filtered = clients

                st.dataframe(
                    [
                        {
                            "ID": c["id"],
                            "Name": c["name"],
                            "Email": c.get("email", ""),
                        }
                        for c in filtered[:20]  # Show first 20
                    ],
                    use_container_width=True
                )

                # Select client
                client_options = {f"{c['name']} (ID: {c['id']})": c["id"] for c in clients}
                selected_client_name = st.selectbox("Select Client", options=list(client_options.keys()))
                client_id = client_options[selected_client_name]
            else:
                client_id = None
        else:
            client_id = st.number_input("Client ID", min_value=1, value=831, step=1)

        st.markdown("---")

        # Campaign filters
        st.subheader("2. Campaign Filters")

        campaign_name_filter = st.text_input(
            "Campaign Name Filter",
            value="Sequence #34",
            help="Campaigns containing this text will be included"
        )

        col1, col2 = st.columns(2)
        with col1:
            campaign_created_after = st.date_input(
                "Campaigns Created On/After",
                value=date(2025, 11, 15),
                help="Only include campaigns created on or after this date"
            )

        with col2:
            analytics_start_date = st.date_input(
                "Analytics Start Date",
                value=date(2025, 11, 15),
                help="Start date for analytics data"
            )

        analytics_end_date = st.date_input(
            "Analytics End Date",
            value=date.today() - timedelta(days=1),
            help="End date for analytics data"
        )

        st.markdown("---")

        # Analyze button
        if st.button("🚀 Analyze Variants", use_container_width=True, type="primary"):
            if not client_id:
                st.error("❌ Please select a client")
            else:
                st.session_state["analyze"] = True
                st.session_state["analysis_config"] = {
                    "client_id": client_id,
                    "campaign_name_filter": campaign_name_filter,
                    "campaign_created_after": campaign_created_after,
                    "analytics_start_date": analytics_start_date,
                    "analytics_end_date": analytics_end_date,
                    "api_key": api_key,
                }

    # Main content area
    if "analyze" in st.session_state and st.session_state["analyze"]:
        config = st.session_state["analysis_config"]

        # Show loading state
        with st.spinner("Fetching campaign data and analyzing variants..."):
            try:
                from smartlead_api import (
                    get_campaigns_for_client,
                    get_campaign_analytics,
                    get_campaign_sequences,
                    get_variant_statistics
                )
                from data_processor import (
                    build_variant_rows,
                    aggregate_variant_performance,
                    calculate_campaign_stats
                )

                # Fetch data
                campaigns = get_campaigns_for_client(
                    config["client_id"],
                    config["campaign_created_after"],
                    config["campaign_name_filter"],
                    config["api_key"]
                )

                if not campaigns:
                    st.warning("⚠️ No campaigns found matching the filters")
                    st.stop()

                campaign_analytics = get_campaign_analytics(
                    campaigns,
                    config["analytics_start_date"],
                    config["analytics_end_date"],
                    config["api_key"]
                )

                campaign_sequences = get_campaign_sequences(
                    campaigns,
                    config["api_key"]
                )

                if not campaign_sequences:
                    st.warning("⚠️ No campaigns with sequences found")
                    st.stop()

                variant_stats = get_variant_statistics(
                    list(campaign_sequences.keys()),
                    config["api_key"]
                )

                # Build analysis
                rows = build_variant_rows(
                    campaigns,
                    campaign_analytics,
                    campaign_sequences,
                    variant_stats
                )

                if not rows:
                    st.warning("⚠️ No variant data found")
                    st.stop()

                # Store in session state
                st.session_state["variant_rows"] = rows
                st.session_state["campaigns"] = campaigns
                st.session_state["analyze"] = False

                st.success(f"✅ Analyzed {len(campaigns)} campaigns with {len(rows)} variants")

            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.stop()

    # Display results if available
    if "variant_rows" in st.session_state:
        display_results()


def display_results():
    """Display analysis results in tabs"""
    rows = st.session_state["variant_rows"]
    campaigns = st.session_state["campaigns"]

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview",
        "⚔️ Variant Comparison",
        "📋 Detailed Metrics",
        "📁 Campaign Breakdown"
    ])

    with tab1:
        display_overview(rows, campaigns)

    with tab2:
        display_variant_comparison(rows)

    with tab3:
        display_detailed_metrics(rows)

    with tab4:
        display_campaign_breakdown(rows)


def display_overview(rows, campaigns):
    """Display overview tab with executive dashboard"""
    import pandas as pd
    from data_processor import aggregate_variant_performance

    st.header("Executive Overview")

    # Aggregate by variant
    variant_agg = aggregate_variant_performance(rows)

    if not variant_agg:
        st.info("No variant data to display")
        return

    # Sort by PRR
    sorted_variants = sorted(
        variant_agg.values(),
        key=lambda x: x["positive_reply_rate"],
        reverse=True
    )

    # Winner
    winner = sorted_variants[0]
    st.markdown(f"""
    <div class="winner-banner">
        <h2>🏆 Best Variant: {winner['variant']}</h2>
        <p style="font-size: 1.2rem;">
            Positive Reply Rate: <strong>{winner['positive_reply_rate']:.2f}%</strong> |
            Reply Rate: <strong>{winner['reply_rate']:.2f}%</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Campaigns", len(campaigns))
    with col2:
        st.metric("Total Variants", len(rows))
    with col3:
        st.metric("Best Variant", winner['variant'])

    st.markdown("---")

    # Variant cards
    st.subheader("Variant Performance Cards")

    cols = st.columns(5)
    for i, variant_data in enumerate(sorted_variants):
        with cols[i]:
            color = "🟢" if i == 0 else "🟡" if i == 1 else "⚪"
            st.markdown(f"""
            <div class="metric-card">
                <h3>{color} Variant {variant_data['variant']}</h3>
                <p><strong>Sent:</strong> {variant_data['total_sent']:,}</p>
                <p><strong>RR:</strong> {variant_data['reply_rate']:.2f}%</p>
                <p><strong>PRR:</strong> {variant_data['positive_reply_rate']:.2f}%</p>
            </div>
            """, unsafe_allow_html=True)


def display_variant_comparison(rows):
    """Display variant comparison tab"""
    import pandas as pd
    from data_processor import aggregate_variant_performance

    st.header("Variant Comparison")

    variant_agg = aggregate_variant_performance(rows)

    if not variant_agg:
        st.info("No variant data to display")
        return

    # Create dataframe
    sorted_variants = sorted(
        variant_agg.values(),
        key=lambda x: (x["positive_reply_rate"], x["reply_rate"]),
        reverse=True
    )

    df = pd.DataFrame([
        {
            "Rank": i + 1,
            "Variant": v["variant"],
            "Sent": f"{v['total_sent']:,}",
            "Replies": f"{v['total_replies']:,}",
            "RR (%)": v["reply_rate"],
            "Positive": f"{v['total_positive_replies']:,}",
            "PRR (%)": v["positive_reply_rate"],
            "PRR/RR (%)": v["positive_reply_rate_of_replies"],
            "Campaigns": v["num_campaigns"],
        }
        for i, v in enumerate(sorted_variants)
    ])

    st.dataframe(df, use_container_width=True)

    # Charts
    st.subheader("Performance Charts")

    col1, col2 = st.columns(2)

    with col1:
        st.bar_chart(df.set_index("Variant")[["RR (%)", "PRR (%)"]"])

    with col2:
        st.bar_chart(df.set_index("Variant")[["PRR/RR (%)"]])


def display_detailed_metrics(rows):
    """Display detailed metrics tab"""
    import pandas as pd

    st.header("Detailed Variant Metrics")

    df = pd.DataFrame(rows)

    # Select columns to display
    display_cols = [
        "campaign_name",
        "sequence_number",
        "variant_label",
        "variant_sent_count",
        "variant_reply_count",
        "variant_reply_rate",
        "variant_positive_reply_count",
        "variant_positive_reply_rate",
        "variant_open_rate",
        "variant_click_rate",
    ]

    st.dataframe(
        df[display_cols],
        use_container_width=True,
        height=400
    )

    # CSV download
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Full CSV",
        data=csv,
        file_name="variant_analysis.csv",
        mime="text/csv"
    )


def display_campaign_breakdown(rows):
    """Display campaign breakdown tab"""
    import pandas as pd
    from data_processor import calculate_campaign_stats

    st.header("Campaign Performance Breakdown")

    campaign_stats = calculate_campaign_stats(rows)

    if not campaign_stats:
        st.info("No campaign data to display")
        return

    # Sort by PRR
    sorted_campaigns = sorted(
        campaign_stats.values(),
        key=lambda x: x["positive_reply_rate"],
        reverse=True
    )

    df = pd.DataFrame([
        {
            "Campaign": c["campaign_name"][:60],
            "Sent": f"{c['total_sent']:,}",
            "Replies": f"{c['total_replies']:,}",
            "RR (%)": c["reply_rate"],
            "Positive": f"{c['total_positive']:,}",
            "PRR (%)": c["positive_reply_rate"],
            "PRR/RR (%)": c["positive_reply_rate_of_replies"],
            "Variants": c["variant_count"],
        }
        for c in sorted_campaigns
    ])

    st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
```

### Step 2: Test authentication locally

```bash
cd /home/ubuntu/variant-performance-analyzer
streamlit run app.py
```

Expected: Browser opens, shows password prompt

### Step 3: Commit initial app

```bash
cd /home/ubuntu/variant-performance-analyzer
git add app.py
git commit -m "feat: implement Streamlit app with authentication and basic UI"
```

---

## Task 5: Update Documentation and Prepare for Deployment

**Files:**
- Modify: `variant-performance-analyzer/README.md`

### Step 1: Update README with deployment instructions

Edit: `/home/ubuntu/variant-performance-analyzer/README.md`

Add to end of README:

```markdown
## Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy secrets template:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
4. Edit `.streamlit/secrets.toml` and add your credentials
5. Run:
   ```bash
   streamlit run app.py
   ```

## Streamlit Community Cloud Deployment

1. Push code to GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Connect your GitHub repository
5. Configure:
   - Main file path: `app.py`
   - Python version: 3.12
6. Add secrets in app settings:
   - PASSWORD: Your chosen password
   - DEFAULT_API_KEY: Your SmartLead API key
7. Click "Deploy"

## Usage

1. Enter password to access
2. Configure API key (or use default)
3. Select client (browse or enter ID)
4. Set campaign filters:
   - Campaign name filter (e.g., "Sequence #34")
   - Creation date threshold
   - Analytics date range
5. Click "Analyze Variants"
6. Explore results across 4 tabs:
   - Overview: Executive summary and winner
   - Variant Comparison: Side-by-side metrics
   - Detailed Metrics: Full dataset
   - Campaign Breakdown: Campaign-level aggregation
7. Download CSV for further analysis

## Testing

Run tests:
```bash
pytest test_smartlead_api.py -v
pytest test_data_processor.py -v
```
```

### Step 2: Create GitHub deployment checklist

Create: `/home/ubuntu/variant-performance-analyzer/DEPLOYMENT_CHECKLIST.md`

```markdown
# Deployment Checklist

## Pre-Deployment

- [ ] All tests pass locally
- [ ] Tested with real SmartLead API
- [ ] Password authentication works
- [ ] CSV download works
- [ ] All tabs display correctly
- [ ] Error handling works for invalid inputs
- [ ] README is complete

## GitHub Setup

- [ ] Create GitHub repository
- [ ] Push code to repository
- [ ] Verify .gitignore excludes secrets
- [ ] Add repository description
- [ ] Add topics/tags

## Streamlit Cloud Setup

- [ ] Create account at share.streamlit.io
- [ ] Connect GitHub repository
- [ ] Configure app settings:
  - [ ] Main file: app.py
  - [ ] Python version: 3.12
- [ ] Add secrets in Streamlit dashboard:
  - [ ] PASSWORD
  - [ ] DEFAULT_API_KEY
- [ ] Deploy application
- [ ] Test deployed application
- [ ] Share URL with users

## Post-Deployment

- [ ] Monitor for errors in Streamlit logs
- [ ] Gather user feedback
- [ ] Create issues for feature requests
```

### Step 3: Commit documentation updates

```bash
cd /home/ubuntu/variant-performance-analyzer
git add README.md DEPLOYMENT_CHECKLIST.md
git commit -m "docs: add deployment documentation and checklist"
```

---

## Task 6: Final Testing and Validation

### Step 1: Run full test suite

```bash
cd /home/ubuntu/variant-performance-analyzer
python -m pytest test_*.py -v
```

Expected: All tests pass

### Step 2: Manual integration test

1. Start Streamlit:
```bash
streamlit run app.py
```

2. Test workflow:
- Enter correct password → should access app
- Enter wrong password → should show error
- Test API connection → should show success
- Load clients → should display client list
- Select client
- Set filters (e.g., client 831, "Sequence #34", dates)
- Click "Analyze Variants"
- Verify all 4 tabs display data
- Test CSV download
- Test different filter combinations

3. Verify error handling:
- Invalid API key → should show error
- No campaigns found → should show warning
- Invalid date range → should handle gracefully

### Step 3: Create example secrets file

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit with real credentials for testing
```

### Step 4: Final commit

```bash
cd /home/ubuntu/variant-performance-analyzer
git add .
git commit -m "chore: finalize implementation and testing"
```

---

## Task 7: Deploy to GitHub and Streamlit Cloud

### Step 1: Create GitHub repository

```bash
cd /home/ubuntu/variant-performance-analyzer

# Initialize Git if not already done
if [ ! -d ".git" ]; then
    git init
fi

# Add all files
git add .

# Create initial commit
git commit -m "feat: initial release of SmartLead Variant Performance Analyzer"

# Create repository on GitHub first, then:
# git remote add origin https://github.com/YOUR_USERNAME/variant-performance-analyzer.git
# git branch -M main
# git push -u origin main
```

### Step 2: Verify .gitignore is working

```bash
git status
```

Expected: `.streamlit/secrets.toml` should NOT appear in untracked files

### Step 3: Deploy to Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub repository
4. Configure:
   - Repository: variant-performance-analyzer
   - Branch: main
   - Main file path: app.py
   - Python version: 3.12
5. In "Advanced settings", add secrets:
   - PASSWORD = "your_secure_password"
   - DEFAULT_API_KEY = "your_smartlead_api_key"
6. Click "Deploy"
7. Wait for deployment to complete
8. Test the deployed application

### Step 4: Post-deployment validation

1. Access the deployed URL
2. Test password authentication
3. Run full analysis workflow
4. Verify CSV export works
5. Check Streamlit logs for any errors

### Step 5: Create release

```bash
cd /home/ubuntu/variant-performance-analyzer

# Tag release
git tag -a v1.0.0 -m "Release v1.0.0: Initial production release"

# Push tag
git push origin v1.0.0

# Create GitHub release with notes
```

---

## Summary

This implementation plan creates a complete Streamlit application for analyzing SmartLead campaign variant performance. The plan follows TDD principles with tests written first, implements all required features (authentication, client browsing, variant analysis, multi-tab interface, CSV export), and includes comprehensive deployment documentation.

**Total estimated time:** 4-6 hours for implementation and testing

**Key dependencies:**
- streamlit>=1.31.0
- requests>=2.31.0
- pandas>=2.0.0
- plotly>=5.18.0

**Deployment:** Streamlit Community Cloud (free tier available)
