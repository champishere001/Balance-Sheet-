import streamlit as st
import pdfplumber
import pandas as pd
import re
import io

# 1. Page Configuration (The HTML-style Interface)
st.set_page_config(page_title="PLFS Scrutiny Portal", layout="wide")
st.title("🛡️ Financial Scrutiny & CSV Streamliner")

# 2. The Logic to hunt for data "Anywhere" on the page
def extract_and_streamline(file):
    with pdfplumber.open(file) as pdf:
        # Merges all pages into one text block
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    
    # Headers to hunt for (Case-insensitive matching)
    mapping = {
        "Revenue": [r"Revenue", r"Turnover", r"Total Income"],
        "Net Profit": [r"Net Profit", r"PAT", r"Profit for the period"],
        "Total Assets": [r"Total Assets"],
        "Total Liabilities": [r"Total Liabilities"],
        "Equity": [r"Equity Share Capital", r"Shareholders' Funds"]
    }

    found_row = {}
    lines = text.split('\n')
    
    for header, keywords in mapping.items():
        found_row[header] = 0.0 # Default value if not found
        for line in lines:
            # Look for keyword anywhere in the line
            if any(re.search(k, line, re.IGNORECASE) for k in keywords):
                # Seize the number found in that line
                nums = re.findall(r'\(?\d[\d,.]*\)?', line)
                if nums:
                    val = nums[0].replace(',', '')
                    # Handle (brackets) as negative numbers
                    if '(' in val: val = '-' + val.replace('(', '').replace(')', '')
                    try:
                        found_row[header] = float(val)
                        break # Move to the next header once found
                    except:
                        continue
    return pd.DataFrame([found_row])

# 3. Active User Interface
st.info("Upload a PDF. The system will seize variables regardless of their location on the page.")
uploaded_file = st.file_uploader("Upload Company PDF", type="pdf")

if uploaded_file:
    df = extract_and_streamline(uploaded_file)
    
    st.subheader("📊 Extracted Table Content")
    st.dataframe(df, use_container_width=True) # Displays headers with values below
    
    # Scrutiny Logic: Asset vs Liability Match
    asset_val = df["Total Assets"][0]
    liab_val = df["Total Liabilities"][0]
    diff = asset_val - liab_val
    
    if abs(diff) > 1:
        st.error(f"❌ Scrutiny Alert: Mismatch of {diff:,.2f}")
    else:
        st.success("✅ Mathematical Check Passed: Assets match Liabilities.")

    # 4. Portable CSV Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Streamlined CSV Report",
        data=csv,
        file_name="scrutiny_report.csv",
        mime="text/csv"
    )
