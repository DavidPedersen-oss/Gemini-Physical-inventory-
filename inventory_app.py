import streamlit as st
import pandas as pd
import io

# Configure the page for a polished look and mobile responsiveness
st.set_page_config(page_title="Physical Inventory Tracker", page_icon="📦", layout="wide")

# App Header
st.title("📦 Property Management Inventory Tracker")
st.markdown("Conduct departmental physical inventory, verify assets, and export updated records.")
st.divider()

# Sidebar for file upload
with st.sidebar:
    st.header("1. Load Data")
    uploaded_file = st.file_uploader("Upload Active Inventory (.xls / .xlsx)", type=["xls", "xlsx"])
    st.markdown("---")
    st.markdown("**Instructions:**")
    st.markdown("1. Upload the backend master list.")
    st.markdown("2. Select a department to audit.")
    st.markdown("3. Search for specific tags or serials.")
    st.markdown("4. Check 'Verified OK' or update fields.")
    st.markdown("5. Download the updated list.")

if uploaded_file is not None:
    # Read the Excel file into a Pandas DataFrame
    @st.cache_data
    def load_data(file):
        df = pd.read_excel(file)
        # Ensure we have a Status/Verified column to act as our "OK" checkbox
        if "Verified OK" not in df.columns:
            df.insert(0, "Verified OK", False)
        # Ensure standard columns exist to prevent errors (adjust these to match your actual Excel headers)
        expected_cols = ["Property Tag #", "Asset ID", "Serial Number", "Department", "Location", "Description"]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = "N/A"
        return df

    # Load data into session state so edits are preserved
    if 'inventory_data' not in st.session_state:
        st.session_state.inventory_data = load_data(uploaded_file)

    df = st.session_state.inventory_data

    # Main dashboard controls
    col1, col2 = st.columns(2)

    with col1:
        # Department filter
        departments = ["All"] + sorted(df["Department"].dropna().unique().tolist())
        selected_dept = st.selectbox("Filter by Department", departments)

    with col2:
        # Search bar
        search_query = st.text_input("Search (Tag #, Asset ID, Serial #, or Description)", "")

    # Apply filters
    filtered_df = df.copy()

    if selected_dept != "All":
        filtered_df = filtered_df[filtered_df["Department"] == selected_dept]

    if search_query:
        # Convert all relevant columns to string and search for the query (case-insensitive)
        search_mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        filtered_df = filtered_df[search_mask]

    st.subheader(f"Inventory List ({len(filtered_df)} items found)")

    # Display the interactive, editable dataframe
    # Users can click checkboxes, edit text, and sort by clicking column headers
    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Verified OK": st.column_config.CheckboxColumn(
                "Verified OK",
                help="Check if the asset is present and requires no changes.",
                default=False,
            )
        },
        hide_index=True,
    )

    # Update the main session state with the edited data
    st.session_state.inventory_data.update(edited_df)

    st.divider()

    # Export functionality
    st.subheader("Export Updated Data")
    st.markdown("Download the verified and updated list to import into PeopleSoft.")
    
    # Convert dataframe back to Excel for download
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        st.session_state.inventory_data.to_excel(writer, index=False, sheet_name='Updated_Inventory')
    processed_data = output.getvalue()

    st.download_button(
        label="📥 Download Updated Excel File",
        data=processed_data,
        file_name="Updated_Campus_Inventory.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👈 Please upload your Active Inventory Excel file in the sidebar to begin.")

