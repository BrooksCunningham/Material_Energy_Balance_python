import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Sugar Mill Data Entry", layout="centered")

st.title("🏭 Sugar Mill Production Entry")
st.markdown("Enter the hourly lab analysis and milling data below.")

# Organizing inputs into a form to prevent the app from 
# refreshing after every single character typed
with st.form("mill_data_form"):
    
    col1, col2 = st.columns(2)
    
    with col1:
        entry_date = st.date_input("Processing Date", value=date.today())
        shift = st.selectbox("Shift", ["Shift A (06:00-14:00)", "Shift B (14:00-22:00)", "Shift C (22:00-06:00)"])
        tandem_id = st.radio("Mill Tandem", ["Tandem 1", "Tandem 2"])

    with col2:
        cane_crushed = st.number_input("Cane Crushed (Tons)", min_value=0.0, step=0.1)
        imbibition_water = st.number_input("Imbibition Water % Cane", min_value=0.0, max_value=100.0)

    st.divider()
    st.subheader("Laboratory Analysis")
    
    # Using columns for lab metrics
    lab1, lab2, lab3 = st.columns(3)
    brix = lab1.number_input("Primary Juice Brix", min_value=0.0, max_value=30.0, format="%.2f")
    pol = lab2.number_input("Primary Juice Pol", min_value=0.0, max_value=30.0, format="%.2f")
    purity = 0.0
    if brix > 0:
        purity = (pol / brix) * 100
    lab3.metric("Calculated Purity", f"{purity:.2f}%")

    # Form submission button
    submitted = st.form_submit_button("Save Entry")
    
    if submitted:
        # Create a dictionary of the input data
        data = {
            "Date": entry_date,
            "Shift": shift,
            "Tandem": tandem_id,
            "Cane_Tons": cane_crushed,
            "Brix": brix,
            "Pol": pol,
            "Purity": purity
        }
        
        st.success("✅ Data submitted successfully!")
        st.write("### Review Submitted Data:")
        st.dataframe(pd.DataFrame([data]))
