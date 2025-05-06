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

UI_COMPONENT_TERMS = [
    "search", "pagination", "navigation", "buttons", "menus",
    "form", "dropdown", "toggle", "filter", "tabs", "input", "checkbox"
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
def contains_ui_component_terms(text):
    return any(term in text for term in UI_COMPONENT_TERMS)

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
    uploaded_main = st.file_uploader("Upload Dashboard Dataset (CSV)", type=["csv"], key="main")
    uploaded_notes = st.file_uploader("Upload Customer Notes (CSV)", type=["csv"], key="notes")

    # ---------------------- CUSTOMER NOTES SECTION ----------------------
    if uploaded_notes is not None:
        st.header("Customer Notes Analysis")
        customer_notes_df = pd.read_csv(uploaded_notes)

        if "Feedback" in customer_notes_df.columns:
            customer_notes_df["Feedback"] = customer_notes_df["Feedback"].apply(clean_html)
            customer_notes_df["is_ux_related"] = customer_notes_df["Feedback"].apply(contains_ux_terms)
            customer_notes_df["is_ui_component_related"] = customer_notes_df["Feedback"].apply(contains_ui_component_terms)

            st.sidebar.markdown("---")
            st.sidebar.subheader("Customer Notes Filters")
            ux_only = st.sidebar.checkbox("Only show UX-related notes", value=True)
            churn_values = customer_notes_df["Churned"].unique() if "Churned" in customer_notes_df.columns else []
            source_values = customer_notes_df["Source"].unique() if "Source" in customer_notes_df.columns else []

            churn_filter = st.sidebar.multiselect("Churned", options=churn_values.tolist(), default=churn_values.tolist()) if churn_values.size > 0 else []
            source_filter = st.sidebar.multiselect("Source", options=source_values.tolist(), default=source_values.tolist()) if len(source_values) > 0 else []

            filtered_notes = customer_notes_df.copy()
            if ux_only:
                filtered_notes = filtered_notes[filtered_notes["is_ux_related"] == True]
            if churn_values.size > 0:
                filtered_notes = filtered_notes[filtered_notes["Churned"].isin(churn_filter)]
            if len(source_values) > 0:
                filtered_notes = filtered_notes[filtered_notes["Source"].isin(source_filter)]

            st.metric("Total UX-Related Notes", filtered_notes.shape[0])
            st.subheader("Filtered Customer Notes")
            st.dataframe(filtered_notes.reset_index(drop=True))

            freq_data = count_ux_term_frequency(filtered_notes["Feedback"])
            if freq_data:
                terms, freqs = zip(*freq_data)
                fig_freq = px.bar(x=terms, y=freqs, labels={'x': 'UX Term', 'y': 'Frequency'},
                                  title="Frequency of UX Terms in Customer Notes")
                st.plotly_chart(fig_freq, use_container_width=True)

            ui_related_df = filtered_notes[filtered_notes["is_ui_component_related"] == True]
            if not ui_related_df.empty:
                st.subheader("Customer Feedback Specifically About UI Components")
                st.dataframe(ui_related_df[["Customer", "Feedback", "ARR"]] if "ARR" in ui_related_df.columns else ui_related_df[["Customer", "Feedback"]])

    # ---------------------- DASHBOARD SECTION ----------------------
    if uploaded_main is not None:
        st.header("Dashboard Analysis")
        df = pd.read_csv(uploaded_main)
        required_cols = {'Feedback', 'ARR', 'Churned', 'Customer', 'Source'}

        if required_cols.issubset(df.columns):
            df["Feedback"] = df["Feedback"].apply(clean_html)
            df["is_ux_related"] = df["Feedback"].apply(contains_ux_terms)

            st.sidebar.header("Dashboard Filters")
            churn_filter = st.sidebar.radio("Churned", options=["All", True, False], index=0)
            source_filter = st.sidebar.multiselect("Feedback Source", options=df["Source"].unique(), default=list(df["Source"].unique()))

            filtered_df = df.copy()
            if churn_filter != "All":
                filtered_df = filtered_df[filtered_df["Churned"] == churn_filter]
            filtered_df = filtered_df[filtered_df["Source"].isin(source_filter)]

            ux_requests = filtered_df[filtered_df["is_ux_related"]]
            ux_churned = ux_requests[ux_requests["Churned"] == True]
            unique_ux_arr = ux_churned.drop_duplicates(subset=["Customer"])["ARR"].sum()
            churned_count = ux_churned["Customer"].nunique()

            st.subheader("UX/UI-Related Business Impact")
            st.metric("Total ARR Lost from Churned UX/UI Customers", f"${unique_ux_arr:,.2f}")
            st.metric("Churned Customers with UX/UI Feedback", churned_count)

            churn_grouped = filtered_df[filtered_df["Churned"] == True].groupby("is_ux_related")["Customer"].nunique().reset_index()
            churn_grouped["Label"] = churn_grouped["is_ux_related"].map({True: "UX/UI Related", False: "Other"})
            fig1 = px.bar(churn_grouped, x="Label", y="Customer", labels={"Customer": "Churned Customers"},
                         title="Churned Customers by Feedback Type")
            st.plotly_chart(fig1, use_container_width=True)

            lost_arr_df = ux_churned.drop_duplicates(subset=["Customer"])[["Customer", "ARR", "Feedback", "Source"]]
            st.subheader("ARR Lost Breakdown (Churned UX/UI Customers)")
            st.dataframe(lost_arr_df.reset_index(drop=True))

            st.subheader("All Filtered Feedback")
            st.dataframe(filtered_df.reset_index(drop=True))

        else:
            st.error("Dashboard data is missing required columns: Feedback, ARR, Churned, Customer, Source")

except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
