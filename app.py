# This script runs with Streamlit. Make sure Streamlit is installed.
# Run locally with: pip install streamlit pandas matplotlib

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import re

st.set_page_config(layout="wide")
st.title("UX/UI Feedback Impact Dashboard")

try:
    uploaded_file = st.file_uploader("Upload the CSV file", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        # Ensure column names are correct
        required_cols = {'Feedback', 'ARR', 'Churned', 'is_ux_related'}
        if required_cols.issubset(df.columns):

            # Total ARR for UX/UI issues
            ux_arr_total = df[df["is_ux_related"]]["ARR"].sum()

            # Churn comparison
            churn_comparison = df[df["Churned"]].groupby("is_ux_related")["Customer"].count()

            # Common terms in all feedback
            all_feedback = " ".join(df["Feedback"].fillna("").astype(str)).lower()
            words = re.findall(r'\b\w+\b', all_feedback)
            common_words = Counter(words).most_common(15)

            # Common terms in UX feedback
            ux_feedback = df[df["is_ux_related"]]["Feedback"].fillna("").str.lower()
            ux_words = " ".join(ux_feedback)
            ux_terms = re.findall(r'\b\w+\b', ux_words)
            ux_common_words = Counter(ux_terms).most_common(15)

            # Layout
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Total ARR from UX/UI-Related Customers", f"${ux_arr_total:,.2f}")

                st.subheader("Churned Customers: UX/UI vs. Non-UX/UI")
                fig1, ax1 = plt.subplots()
                churn_comparison.plot(kind="bar", ax=ax1)
                ax1.set_xticks(range(len(churn_comparison)))
                ax1.set_xticklabels(["Not UX/UI-Related", "UX/UI-Related"], rotation=0)
                ax1.set_ylabel("Churned Customers")
                st.pyplot(fig1)

            with col2:
                st.subheader("Most Common Terms in All Feedback")
                if common_words:
                    labels, counts = zip(*common_words)
                    fig2, ax2 = plt.subplots()
                    ax2.barh(labels[::-1], counts[::-1])
                    st.pyplot(fig2)

                st.subheader("Top Terms in UX/UI-Related Feedback")
                if ux_common_words:
                    ux_labels, ux_counts = zip(*ux_common_words)
                    fig3, ax3 = plt.subplots()
                    ax3.barh(ux_labels[::-1], ux_counts[::-1])
                    st.pyplot(fig3)

        else:
            st.error("CSV is missing required columns: Feedback, ARR, Churned, is_ux_related")

except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
