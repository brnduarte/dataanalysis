# This script runs with Streamlit. Make sure Streamlit is installed.
# Run locally with: pip install streamlit pandas plotly

import streamlit as st
import pandas as pd
import plotly.express as px
import re
from collections import Counter

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

@st.cache_data
def count_ux_term_frequency(texts):
    all_text = " ".join(texts)
    counts = Counter()
    for term in UX_TERMS:
        pattern = re.escape(term)
        match_count = len(re.findall(pattern, all_text))
        if match_count > 0:
            counts[term] = match_count
    return counts.most_common()

try:
    uploaded_main = st.file_uploader("Upload Main Dataset (CSV)", type=["csv"], key="main")
    uploaded_notes = st.file_uploader("Upload Customer Notes (CSV)", type=["csv"], key="notes")

    if uploaded_notes is not None:
        customer_notes_df = pd.read_csv(uploaded_notes)

        if "Feedback" in customer_notes_df.columns:
            customer_notes_df["Feedback"] = customer_notes_df["Feedback"].apply(clean_html)
            customer_notes_df["is_ux_related"] = customer_notes_df["Feedback"].apply(contains_ux_terms)

            st.sidebar.markdown("---")
            st.sidebar.subheader("Customer Notes Filters")
            ux_filter = st.sidebar.checkbox("Show only UX-related notes", value=True)

            filtered_notes = customer_notes_df.copy()
            if ux_filter:
                filtered_notes = filtered_notes[filtered_notes["is_ux_related"]]

            st.subheader("Filtered Feedback from 'Customer Notes'")
            st.dataframe(filtered_notes.reset_index(drop=True))

            freq_data = count_ux_term_frequency(filtered_notes["Feedback"])
            if freq_data:
                terms, freqs = zip(*freq_data)
                fig_freq = px.bar(x=terms, y=freqs, labels={'x': 'UX Term', 'y': 'Frequency'},
                                  title="Frequency of UX Terms in 'Customer Notes'")
                st.plotly_chart(fig_freq, use_container_width=True)

    if uploaded_main is not None:
        df = pd.read_csv(uploaded_main)
        required_cols = {'Feedback', 'ARR', 'Churned', 'Customer', 'Source'}
        if required_cols.issubset(df.columns):
            df["Feedback"] = df["Feedback"].apply(clean_html)
            df["is_ux_related"] = df["Feedback"].apply(contains_ux_terms)

            st.sidebar.header("Main Data Filters")
            churn_filter = st.sidebar.radio("Churned", options=["All", True, False], index=0)
            source_filter = st.sidebar.multiselect("Feedback Source", options=df["Source"].unique(), default=list(df["Source"].unique()))

            filtered_df = df.copy()
            if churn_filter != "All":
                filtered_df = filtered_df[filtered_df["Churned"] == churn_filter]
            filtered_df = filtered_df[filtered_df["Source"].isin(source_filter)]

            ux_churned = filtered_df[(filtered_df["Churned"] == True) & (filtered_df["is_ux_related"])]
            unique_ux_arr = ux_churned.drop_duplicates(subset=["Customer"])["ARR"].sum()
            churned_count = ux_churned["Customer"].nunique()

            st.metric("Total ARR Lost from Churned UX/UI Customers", f"${unique_ux_arr:,.2f}")
            st.metric("Number of Churned Customers with UX/UI Feedback", churned_count)

            churned_data = filtered_df[filtered_df["Churned"] == True]
            churn_grouped = churned_data.groupby("is_ux_related")["Customer"].nunique().reset_index()
            churn_grouped["Label"] = churn_grouped["is_ux_related"].map({True: "UX/UI Related", False: "Other"})
            fig1 = px.bar(churn_grouped, x="Label", y="Customer", labels={"Customer": "Churned Customers"},
                         title="Churned Customers by Feedback Type")
            st.plotly_chart(fig1, use_container_width=True)

            lost_arr_df = ux_churned.drop_duplicates(subset=["Customer"])[["Customer", "ARR", "Feedback", "Source"]]
            st.subheader("ARR Lost Details from UX/UI-Related Churned Customers")
            st.dataframe(lost_arr_df.reset_index(drop=True))

            st.subheader("Filtered Feedback Data")
            st.dataframe(filtered_df.reset_index(drop=True))

        else:
            st.error("Main sheet is missing required columns: Feedback, ARR, Churned, Customer, Source")

except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
