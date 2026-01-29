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

## API Endpoints Used

- GET /api/v1/client/ - List all clients
- GET /api/v1/campaigns - Get campaigns for client
- GET /api/v1/campaigns/{id}/top-level-analytics-by-date - Campaign analytics
- GET /api/v1/campaigns/{id}/sequences - Campaign sequences
- GET /api/v1/campaigns/{id}/variant-statistics - Variant statistics
