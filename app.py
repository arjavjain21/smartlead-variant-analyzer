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
        st.bar_chart(df.set_index("Variant")[["RR (%)", "PRR (%)"]])

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
