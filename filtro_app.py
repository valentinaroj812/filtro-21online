
import streamlit as st
import pandas as pd
import io
import openpyxl
from fpdf import FPDF

st.set_page_config(layout="wide", page_title="21 Online App", page_icon="📊")

# --- Estilos básicos seguros ---
st.markdown("<style>h1, h2, h3 {color: #B4975A;}</style>", unsafe_allow_html=True)

st.write("✅ App cargada correctamente")

ACCESS_CODE = "21ONLINE2024"
code_input = st.sidebar.text_input("🔑 Ingresa el código de acceso:", type="password")
if code_input != ACCESS_CODE:
    st.warning("🔒 Código de acceso requerido para usar la app.")
    st.stop()

def clean_price(x):
    if pd.isnull(x):
        return 0.0
    return float(str(x).replace('$', '').replace(',', '').replace(' ', '').strip())

def load_and_merge(files):
    dfs = []
    for file in files:
        try:
            df = pd.read_excel(file, header=0)
            if "Fecha Cierre" not in df.columns:
                df = pd.read_excel(file, header=1)
            dfs.append(df)
        except:
            st.error(f"⚠ No se pudo leer el archivo: {file.name}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()

st.markdown("<h1 style='text-align: center;'>📊 21 Online - App Pro</h1>", unsafe_allow_html=True)

uploaded_files = st.file_uploader("📂 Sube uno o más archivos Excel:", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    df = load_and_merge(uploaded_files)

    if df.empty:
        st.warning("⚠ No se pudo procesar ningún archivo válido.")
    else:
        if "Precio Promoción" in df.columns:
            df["Precio Promoción"] = df["Precio Promoción"].apply(clean_price)
        if "Precio Cierre" in df.columns:
            df["Precio Cierre"] = df["Precio Cierre"].apply(clean_price)
        if "Fecha Cierre" in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df["Fecha Cierre"]):
                df["Fecha Cierre"] = pd.to_datetime(df["Fecha Cierre"], errors='coerce')

        with st.sidebar:
            st.header("Filtros avanzados")
            search = st.text_input("🔎 Buscar palabra clave (dirección, código, cliente):").strip()

        filtered_df = df.copy()

        if search:
            search_cols = ["Dirección", "Código", "Cliente"]
            mask = pd.Series(False, index=filtered_df.index)
            for col in search_cols:
                if col in filtered_df.columns:
                    mask = mask | filtered_df[col].astype(str).str.contains(search, case=False, na=False)
            filtered_df = filtered_df[mask]

        st.dataframe(filtered_df)
