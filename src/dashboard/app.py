"""
Smart Urban Grievance Redressal — Streamlit Dashboard
======================================================
Run with:
    cd src
    streamlit run dashboard/app.py

Pages:
  1. Overview          — totals, urgency breakdown, recent complaints
  2. Location Heatmap  — complaint hotspots by area
  3. Category & Sentiment — issue type distribution + sentiment analysis
  4. Pattern Mining    — association rules + sequential patterns
  5. Scraped Data      — Reddit posts with credibility scores
"""

import sys
import os

# Make sure src/ is on the path when running from the src/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy.orm import Session

from database.database import SessionLocal
from entities.complaint_entity import Complaint
from entities.scraped_post_entity import ScrapedPost
from repositories.scraped_post_repository import ScrapedPostRepository
from patterns.association_miner import run_association_mining
from patterns.sequential_miner import run_sequential_mining

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Smart Urban Grievance System",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# DB helper
# ---------------------------------------------------------------------------

@st.cache_resource
def get_db_session() -> Session:
    return SessionLocal()


def get_db():
    return get_db_session()


# ---------------------------------------------------------------------------
# Data loaders (cached so they don't re-query on every widget interaction)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def load_complaints() -> pd.DataFrame:
    db = SessionLocal()
    try:
        rows = db.query(Complaint).all()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([{
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "location": r.location,
            "category": r.category or "Unknown",
            "urgency": r.urgency or "Unknown",
            "sentiment": r.sentiment or "NEUTRAL",
            "status": r.status,
        } for r in rows])
    finally:
        db.close()


@st.cache_data(ttl=60)
def load_scraped_posts() -> pd.DataFrame:
    db = SessionLocal()
    try:
        rows = ScrapedPostRepository.get_all(db)
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([{
            "id": r.id,
            "source": r.source or "reddit",
            "title": r.title,
            "description": r.description,
            "location": r.location or "Unknown",
            "category": r.category or "Unknown",
            "urgency": r.urgency or "Unknown",
            "sentiment": r.sentiment or "NEUTRAL",
            "credibility_score": r.credibility_score,
            "url": r.url,
            "scraped_at": r.scraped_at,
        } for r in rows])
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Colour maps
# ---------------------------------------------------------------------------

URGENCY_COLORS = {"HIGH": "#e74c3c", "MEDIUM": "#f39c12", "LOW": "#2ecc71", "Unknown": "#95a5a6"}
SENTIMENT_COLORS = {"NEGATIVE": "#e74c3c", "NEUTRAL": "#3498db", "POSITIVE": "#2ecc71"}

CATEGORY_COLORS = {
    # System categories (used by classifier + citizen complaints)
    "Roads & Traffic": "#3498db",
    "Water & Sanitation": "#1abc9c",
    "Electricity": "#f1c40f",
    "Garbage & Waste": "#e67e22",
    "Flooding": "#2980b9",
    "Public Infrastructure": "#9b59b6",
    "Noise & Pollution": "#e74c3c",
    "General": "#95a5a6",
    "Unknown": "#bdc3c7",
}


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

st.sidebar.title("🏙️ Smart Grievance System")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    [
        "📊 Overview",
        "📍 Location Heatmap",
        "🏷️ Category & Sentiment",
        "🔗 Pattern Mining",
        "🌐 Scraped Data",
    ],
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()


# ===========================================================================
# PAGE 1: OVERVIEW
# ===========================================================================

if page == "📊 Overview":
    st.title("📊 Overview")
    st.markdown("Real-time summary of all citizen complaints in the system.")

    df = load_complaints()

    if df.empty:
        st.warning("No complaints in the database yet. Submit some via the API first.")
        st.stop()

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Complaints", len(df))
    col2.metric("High Urgency", len(df[df["urgency"] == "HIGH"]))
    col3.metric("Locations Covered", df["location"].nunique())
    col4.metric("Categories", df["category"].nunique())

    st.markdown("---")

    col_left, col_right = st.columns(2)

    # Urgency pie chart
    with col_left:
        st.subheader("Urgency Breakdown")
        urgency_counts = df["urgency"].value_counts().reset_index()
        urgency_counts.columns = ["urgency", "count"]
        fig = px.pie(
            urgency_counts,
            names="urgency",
            values="count",
            color="urgency",
            color_discrete_map=URGENCY_COLORS,
            hole=0.4,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig)

    # Status breakdown
    with col_right:
        st.subheader("Processing Status")
        status_counts = df["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig2 = px.bar(
            status_counts,
            x="status",
            y="count",
            color="status",
            text="count",
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2)

    st.markdown("---")
    st.subheader("Recent Complaints")

    display_cols = ["id", "title", "location", "category", "urgency", "sentiment", "status"]
    st.dataframe(
        df[display_cols].head(20),
        use_container_width=True,
        hide_index=True,
    )


# ===========================================================================
# PAGE 2: LOCATION HEATMAP
# ===========================================================================

elif page == "📍 Location Heatmap":
    st.title("📍 Location Heatmap")
    st.markdown("Complaint volume and category distribution across locations.")

    df = load_complaints()

    if df.empty:
        st.warning("No complaints in the database yet.")
        st.stop()

    # Complaints per location
    location_counts = (
        df.groupby("location")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Complaints by Location")
        fig = px.bar(
            location_counts,
            x="location",
            y="count",
            color="count",
            color_continuous_scale="Reds",
            text="count",
        )
        fig.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False)
        st.plotly_chart(fig)

    with col2:
        st.subheader("🔥 Top Hotspots")
        for _, row in location_counts.head(5).iterrows():
            st.markdown(f"**{row['location']}** — {row['count']} complaints")

    st.markdown("---")
    st.subheader("Category Distribution per Location")

    location_category = (
        df.groupby(["location", "category"])
        .size()
        .reset_index(name="count")
    )

    fig2 = px.bar(
        location_category,
        x="location",
        y="count",
        color="category",
        color_discrete_map=CATEGORY_COLORS,
        barmode="stack",
        text_auto=True,
    )
    fig2.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig2)

    st.markdown("---")
    st.subheader("Urgency by Location")

    location_urgency = (
        df.groupby(["location", "urgency"])
        .size()
        .reset_index(name="count")
    )

    fig3 = px.bar(
        location_urgency,
        x="location",
        y="count",
        color="urgency",
        color_discrete_map=URGENCY_COLORS,
        barmode="group",
    )
    fig3.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig3)


# ===========================================================================
# PAGE 3: CATEGORY & SENTIMENT
# ===========================================================================

elif page == "🏷️ Category & Sentiment":
    st.title("🏷️ Category & Sentiment Analysis")
    st.markdown("Issue type distribution and sentiment breakdown across all complaints.")

    df = load_complaints()

    if df.empty:
        st.warning("No complaints in the database yet.")
        st.stop()

    col1, col2 = st.columns(2)

    # Category distribution
    with col1:
        st.subheader("Category Distribution")
        cat_counts = df["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]
        fig = px.pie(
            cat_counts,
            names="category",
            values="count",
            color="category",
            color_discrete_map=CATEGORY_COLORS,
            hole=0.3,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig)

    # Sentiment distribution
    with col2:
        st.subheader("Sentiment Distribution")
        sent_counts = df["sentiment"].value_counts().reset_index()
        sent_counts.columns = ["sentiment", "count"]
        fig2 = px.pie(
            sent_counts,
            names="sentiment",
            values="count",
            color="sentiment",
            color_discrete_map=SENTIMENT_COLORS,
            hole=0.3,
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig2)

    st.markdown("---")

    # Sentiment per category
    st.subheader("Sentiment Breakdown per Category")
    cat_sent = (
        df.groupby(["category", "sentiment"])
        .size()
        .reset_index(name="count")
    )
    fig3 = px.bar(
        cat_sent,
        x="category",
        y="count",
        color="sentiment",
        color_discrete_map=SENTIMENT_COLORS,
        barmode="stack",
        text_auto=True,
    )
    fig3.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig3)

    st.markdown("---")

    # Urgency per category
    st.subheader("Urgency Breakdown per Category")
    cat_urg = (
        df.groupby(["category", "urgency"])
        .size()
        .reset_index(name="count")
    )
    fig4 = px.bar(
        cat_urg,
        x="category",
        y="count",
        color="urgency",
        color_discrete_map=URGENCY_COLORS,
        barmode="group",
    )
    fig4.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig4)


# ===========================================================================
# PAGE 4: PATTERN MINING
# ===========================================================================

elif page == "🔗 Pattern Mining":
    st.title("🔗 Pattern Mining")
    st.markdown(
        "Discover hidden relationships and temporal sequences in complaint data "
        "using Association Rule Mining and Sequential Pattern Mining."
    )

    db = SessionLocal()

    try:
        # ---- Association Rules ----
        st.subheader("🔀 Association Rules (Apriori)")
        st.markdown(
            "Rules show which issue types tend to co-occur in the same location. "
            "High **lift** (> 1) means the issues are positively correlated."
        )

        col1, col2, col3 = st.columns(3)
        min_support = col1.slider("Min Support", 0.01, 0.5, 0.05, 0.01)
        min_confidence = col2.slider("Min Confidence", 0.1, 1.0, 0.4, 0.05)
        min_lift = col3.slider("Min Lift", 1.0, 5.0, 1.0, 0.1)

        if st.button("Run Association Mining"):
            with st.spinner("Mining association rules..."):
                rules_df = run_association_mining(
                    db,
                    min_support=min_support,
                    min_confidence=min_confidence,
                    min_lift=min_lift,
                )

            if rules_df.empty:
                st.info(
                    "No rules found with current thresholds. "
                    "Try lowering min_support or min_confidence, "
                    "or add more complaint data."
                )
            else:
                st.success(f"Found {len(rules_df)} association rules.")

                # Format for display
                display_df = rules_df.copy()
                display_df["support"] = display_df["support"].map("{:.3f}".format)
                display_df["confidence"] = display_df["confidence"].map("{:.3f}".format)
                display_df["lift"] = display_df["lift"].map("{:.3f}".format)

                st.dataframe(display_df, hide_index=True)

                # Visualise top rules
                if len(rules_df) > 0:
                    st.subheader("Top Rules by Lift")
                    top_rules = rules_df.head(10).copy()
                    top_rules["rule"] = top_rules["antecedents"] + " → " + top_rules["consequents"]
                    fig = px.bar(
                        top_rules,
                        x="lift",
                        y="rule",
                        orientation="h",
                        color="confidence",
                        color_continuous_scale="Blues",
                        text=top_rules["lift"].map("{:.2f}".format),
                    )
                    fig.update_layout(yaxis={"categoryorder": "total ascending"})
                    st.plotly_chart(fig)

        st.markdown("---")

        # ---- Sequential Patterns ----
        st.subheader("⏱️ Sequential Patterns (PrefixSpan)")
        st.markdown(
            "Sequences show the typical order in which issues escalate at a location. "
            "**A → B → C** means A tends to be reported first, then B, then C."
        )

        min_seq_support = st.slider("Min Sequence Support (locations)", 1, 10, 2)

        if st.button("Run Sequential Mining"):
            with st.spinner("Mining sequential patterns..."):
                patterns = run_sequential_mining(db, min_support=min_seq_support)

            if not patterns:
                st.info(
                    "No patterns found. Try lowering min support, "
                    "or add more complaint data from multiple locations."
                )
            else:
                st.success(f"Found {len(patterns)} sequential patterns.")
                for p in patterns:
                    arrow = " → ".join(p["pattern"])
                    st.markdown(
                        f"- **{arrow}** &nbsp;&nbsp; *(support: {p['support']} location(s))*"
                    )

    finally:
        db.close()


# ===========================================================================
# PAGE 5: SCRAPED DATA
# ===========================================================================

elif page == "🌐 Scraped Data":
    st.title("🌐 Scraped Data & Credibility")
    st.markdown("Reddit posts collected by the scraper, scored by PageRank-based credibility.")

    df = load_scraped_posts()

    if df.empty:
        st.warning(
            "No scraped posts yet. Run the Reddit scraper first:\n\n"
            "```bash\ncd src\npython scraper/reddit.py\n```"
        )
        st.stop()

    # KPI row
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Posts", len(df))
    col2.metric("Sources", df["source"].nunique())
    col3.metric("Locations Found", df[df["location"] != "Unknown"]["location"].nunique())

    st.markdown("---")

    # High credibility alerts
    if df["credibility_score"].notna().any():
        high_cred = df[df["credibility_score"] >= 0.6].sort_values(
            "credibility_score", ascending=False
        )
        if not high_cred.empty:
            st.subheader(f"🚨 High Credibility Alerts ({len(high_cred)} posts)")
            st.markdown("These posts are highly corroborated — likely real issues needing attention.")
            for _, row in high_cred.head(5).iterrows():
                with st.expander(f"[{row['urgency']}] {row['title'][:80]}..."):
                    col_a, col_b = st.columns(2)
                    col_a.markdown(f"**Location:** {row['location']}")
                    col_a.markdown(f"**Category:** {row['category']}")
                    col_a.markdown(f"**Urgency:** {row['urgency']}")
                    col_b.markdown(f"**Credibility Score:** {row['credibility_score']:.3f}")
                    if row.get("description"):
                        col_b.markdown(f"**Summary:** {row['description']}")
                    if row["url"]:
                        col_b.markdown(f"[View Source]({row['url']})")

        st.markdown("---")

        # Credibility score distribution
        st.subheader("Credibility Score Distribution")
        fig = px.histogram(
            df[df["credibility_score"].notna()],
            x="credibility_score",
            nbins=20,
            color_discrete_sequence=["#3498db"],
        )
        fig.add_vline(x=0.6, line_dash="dash", line_color="red",
                      annotation_text="High credibility threshold")
        st.plotly_chart(fig)

    st.markdown("---")

    # Category breakdown of scraped posts
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Category Distribution")
        cat_counts = df["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]
        fig2 = px.bar(
            cat_counts,
            x="category",
            y="count",
            color="category",
            color_discrete_map=CATEGORY_COLORS,
            text="count",
        )
        fig2.update_layout(showlegend=False, xaxis_tickangle=-30)
        st.plotly_chart(fig2)

    with col2:
        st.subheader("Source Breakdown")
        sub_counts = df["source"].value_counts().reset_index()
        sub_counts.columns = ["source", "count"]
        fig3 = px.pie(sub_counts, names="source", values="count", hole=0.3)
        st.plotly_chart(fig3)

    st.markdown("---")

    # Full posts table
    st.subheader("All Scraped Posts")
    display_cols = ["id", "source", "title", "location", "category",
                    "urgency", "sentiment", "credibility_score"]
    available_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[available_cols], hide_index=True)
