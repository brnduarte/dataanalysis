# This script runs with Streamlit. Make sure Streamlit is installed.
# Run locally with: pip install streamlit pandas plotly

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

st.set_page_config(layout="wide")
st.title("UX/UI Feedback Impact Dashboard")

UX_TERMS = [
    "ux", "user experience", "ui", "user interface", "fragmented",
    "hard to", "difficult to find", "broken interface", "bad experience",
    "missing", "can't find", "frustration", "confusion", "issues",
    "poor", "poorly designed", "locate", "search", "searchable",
    "complex", "complicated", "inefficient", "inefficiencies",
    "missed", "limited", "unclear", "not clear", "big", "small",
    "navigate", "navigation", "pagination", "too many clicks",
    "lots of clicks", "inconsistent", "not consistent",
    "unintuitive", "non intuitive", "accessibility", "keyboard",
    "screen readers", "wcag", "a11y", "section 508", "ADA",
    "European Accessibility Act", "EAA", "disabilities",
    "contrast", "color", "can't read", "too small",
    "customisation", "translations", "translate", "localisation", "subtitle"
]

@st.cache_data
def clean_html(text):
    if pd.isnull(text):
        return ""
    text = re.sub(r'<.*?>', '', text)
    return text.lower()

@st.cache_data
def contains_ux_terms(text):
    return any(term in text for term in UX_TERMS)

try:
    uploaded_file = st.file_uploader("Upload the CSV file", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        # Ensure required columns
        required_cols = {'Feedback', 'ARR', 'Churned', 'Customer', 'Source'}
        if required_cols.issubset(df.columns):
            df["Feedback"] = df["Feedback"].apply(clean_html)
            df["is_ux_related"] = df["Feedback"].apply(contains_ux_terms)

            # Sidebar filters
            st.sidebar.header("Filters")
            churn_filter = st.sidebar.radio("Churned", options=["All", True, False], index=0)
            source_filter = st.sidebar.multiselect("Feedback Source", options=df["Source"].unique(), default=list(df["Source"].unique()))

            filtered_df = df.copy()
            if churn_filter != "All":
                filtered_df = filtered_df[filtered_df["Churned"] == churn_filter]
            filtered_df = filtered_df[filtered_df["Source"].isin(source_filter)]

            # Deduplicate ARR by customer
            ux_churned = filtered_df[(filtered_df["Churned"] == True) & (filtered_df["is_ux_related"])]
            unique_ux_arr = ux_churned.drop_duplicates(subset=["Customer"])["ARR"].sum()
            churned_count = ux_churned["Customer"].nunique()

            st.metric("Total ARR Lost from Churned UX/UI Customers", f"${unique_ux_arr:,.2f}")
            st.metric("Number of Churned Customers with UX/UI Feedback", churned_count)

            # Bar Chart: Churned UX/UI vs Non-UX
            churned_data = filtered_df[filtered_df["Churned"] == True]
            churn_grouped = churned_data.groupby("is_ux_related")["Customer"].nunique().reset_index()
            churn_grouped["Label"] = churn_grouped["is_ux_related"].map({True: "UX/UI Related", False: "Other"})
            fig1 = px.bar(churn_grouped, x="Label", y="Customer", labels={"Customer": "Churned Customers"}, title="Churned Customers by Feedback Type")
            st.plotly_chart(fig1, use_container_width=True)

            # ARR Lost Breakdown
            lost_arr_df = ux_churned.drop_duplicates(subset=["Customer"])[["Customer", "ARR", "Feedback", "Source"]]
            st.subheader("ARR Lost Details from UX/UI-Related Churned Customers")
            st.dataframe(lost_arr_df.reset_index(drop=True))

            # All filtered data
            st.subheader("Filtered Feedback Data")
            st.dataframe(filtered_df.reset_index(drop=True))

        else:
            st.error("CSV is missing required columns: Feedback, ARR, Churned, Customer, Source")

except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
