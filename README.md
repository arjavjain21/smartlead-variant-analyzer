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
