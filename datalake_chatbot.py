# streamlit_fast_csv_chat_sia_egypt.py
import os
import pandas as pd
import streamlit as st
from io import StringIO
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# ===== LOAD ENV =====
load_dotenv()


# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="SIA-EGYPT Chat & Analysis",
    layout="wide"
)

# ===== CUSTOM DARK UI =====
st.markdown("""
<style>
body {background-color:#0B0C10; color:#E5E5E5; font-family:'Segoe UI', sans-serif;}
h1,h2,h3,h4 {color:#00FFFF;}
.stButton>button {background-color:#00BFFF; color:white; border-radius:12px; padding:0.5rem 1rem; font-weight:bold; transition:all 0.3s;}
.stButton>button:hover {background-color:#0099CC; transform:scale(1.98);}
.card {background-color:#111827; padding:15px; border-radius:12px; margin-bottom:12px; box-shadow:0 4px 12px rgba(0,0,0,0.5);}
.input-box {background-color:#1F2937; padding:12px; border-radius:10px; margin-bottom:20px;}
.sidebar .sidebar-content {background-color:#0F111A; padding:15px; border-radius:10px;}
.stSlider > div{color:#E5E5E5;}
</style>
""", unsafe_allow_html=True)

# ===== HEADER =====
st.title("SIA-EGYPT Chatbot")
st.markdown("---")

# ===== AZURE CSV LOADER =====
def load_csv_from_azure(account_name, account_key, container_name):
    from azure.storage.blob import BlobServiceClient
    all_dfs = {}
    try:
        conn_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
        service_client = BlobServiceClient.from_connection_string(conn_str)
        container_client = service_client.get_container_client(container_name)
        for blob in container_client.list_blobs():
            if blob.name.endswith(".csv"):
                blob_client = container_client.get_blob_client(blob)
                csv_bytes = blob_client.download_blob().readall()
                df = pd.read_csv(StringIO(csv_bytes.decode('utf-8')))
                all_dfs[blob.name] = df
    except Exception as e:
        st.error(f"Error loading CSVs from Azure: {e}")
    return all_dfs

# ===== LOAD CSVs =====
dfs_state = st.text("Loading CSV files from Azure Data Lake...")
dataframes = load_csv_from_azure(
    account_name=os.environ.get("STORAGE_ACCOUNT_NAME"),
    account_key=os.environ.get("STORAGE_ACCOUNT_KEY"),
    container_name=os.environ.get("CONTAINER_NAME")
)
dfs_state.text(f"Total CSV files loaded: {len(dataframes)}")

# ===== LAYOUT =====
col1, col2 = st.columns([2,1])

# ===== LEFT COLUMN: CHATBOT =====
with col1:
    st.subheader("Ask Your CSV Data")
    if dataframes:
        file_choice = st.selectbox("Select CSV file:", list(dataframes.keys()))
        df = dataframes[file_choice]
        
        query = st.text_input("Enter your question (e.g., 'How many rows?', 'Sum of column X'):")
        
        if st.button("Ask") and query:
            try:
                # Simple predefined queries
                query_lower = query.lower()
                if "how many rows" in query_lower:
                    answer = len(df)
                elif "how many columns" in query_lower:
                    answer = len(df.columns)
                elif "columns" in query_lower:
                    answer = ", ".join(df.columns)
                elif "sum of" in query_lower:
                    col_name = query_lower.replace("sum of", "").strip()
                    if col_name in df.columns:
                        answer = df[col_name].sum()
                    else:
                        answer = f"Column '{col_name}' not found."
                else:
                    answer = "Query not recognized. Try 'How many rows?' or 'Sum of column X'."
                
                st.markdown(f'<div class="card"><b>Question:</b> {query}<br><b>Answer:</b> {answer}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error processing question: {e}")
    else:
        st.info("No CSVs loaded yet.")

# ===== RIGHT COLUMN: DATA ANALYSIS =====
with col2:
    st.subheader("Quick Data Analysis")
    if dataframes:
        file_choice_ana = st.selectbox("Select CSV for analysis:", list(dataframes.keys()), key="ana")
        df_ana = dataframes[file_choice_ana]
        st.dataframe(df_ana.head())

        numeric_cols = df_ana.select_dtypes(include='number').columns.tolist()
        all_cols = df_ana.columns.tolist()
        x_col = st.selectbox("X-axis column", all_cols, key="x_col")
        y_col = st.selectbox("Y-axis column (numeric)", numeric_cols, key="y_col")
        chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Histogram", "Boxplot"], key="chart_type")
        
        if st.button("Generate Chart", key="gen_chart"):
            try:
                fig, ax = plt.subplots()
                if chart_type == "Bar":
                    g = df_ana.groupby(x_col)[y_col].sum().reset_index()
                    ax.bar(g[x_col].astype(str), g[y_col])
                elif chart_type == "Line":
                    df_ana[x_col] = pd.to_datetime(df_ana[x_col], errors='coerce')
                    g = df_ana.groupby(x_col)[y_col].sum().reset_index()
                    ax.plot(g[x_col], g[y_col])
                elif chart_type == "Histogram":
                    ax.hist(df_ana[y_col].dropna())
                elif chart_type == "Boxplot":
                    ax.boxplot(df_ana[y_col].dropna())
                st.pyplot(fig)
            except Exception as e:
                st.error(f"Chart error: {e}")
    else:
        st.info("No CSVs loaded for analysis.")
