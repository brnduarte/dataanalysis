
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Load data
ui_agg = pd.DataFrame({
    'ui_elements': ['search', 'button', 'navigation', 'pagination'],
    'ARR': [3200000, 2800000, 1500000, 1200000]
})

feature_agg = pd.DataFrame({
    'features': ['users', 'courses', 'learning paths', 'reports', 'dashboard'],
    'ARR': [6335633.30, 5858841.54, 2447966.84, 1971926.80, 730444.76]
})

st.title("UX/UI ARR Impact Dashboard")

# UI Element ARR
st.header("ARR Impact by UI Element")
fig_ui, ax_ui = plt.subplots(figsize=(8, 5))
ax_ui.barh(ui_agg['ui_elements'], ui_agg['ARR'])
ax_ui.set_xlabel("ARR (USD)")
ax_ui.set_title("UI Elements Mentioned in Feedback")
ax_ui.invert_yaxis()
st.pyplot(fig_ui)

# Feature ARR
st.header("ARR Impact by Feature")
fig_feat, ax_feat = plt.subplots(figsize=(8, 5))
ax_feat.barh(feature_agg['features'], feature_agg['ARR'])
ax_feat.set_xlabel("ARR (USD)")
ax_feat.set_title("Product Features Mentioned in Feedback")
ax_feat.invert_yaxis()
st.pyplot(fig_feat)
