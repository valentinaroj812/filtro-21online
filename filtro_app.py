
import streamlit as st
import pandas as pd
import openpyxl

st.set_page_config(layout="wide", page_title="21 Online App", page_icon="📊")

st.markdown("<style>h1, h2, h3 {color: #B4975A;}</style>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>📊 21 Online - App Pro</h1>", unsafe_allow_html=True)

ACCESS_CODE = "21ONLINE2024"
code_input = st.sidebar.text_input("🔑 Ingresa el código de acceso:", type="password")
if code_input != ACCESS_CODE:
    st.warning("🔒 Código de acceso requerido para usar la app.")
    st.stop()

def clean_price(x):
    if pd.isnull(x):
        return 0.0
    try:
        return float(str(x).replace('$', '').replace(',', '').replace(' ', '').strip())
    except:
        return 0.0

def find_column(columns, name_keywords):
    for col in columns:
        if any(keyword.lower() in col.lower() for keyword in name_keywords):
            return col
    return None

def load_and_merge(files):
    dfs = []
    for file in files:
        try:
            df = pd.read_excel(file, header=0)
            dfs.append(df)
        except:
            st.error(f"⚠ No se pudo leer el archivo: {file.name}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()

uploaded_files = st.file_uploader("📂 Sube uno o más archivos Excel:", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    df = load_and_merge(uploaded_files)

    if df.empty:
        st.warning("⚠ No se pudo procesar ningún archivo válido.")
    else:
        col_prom = find_column(df.columns, ["promocion"])
        col_cierre = find_column(df.columns, ["cierre"])
        if col_prom:
            df[col_prom] = df[col_prom].apply(clean_price)
        if col_cierre:
            df[col_cierre] = df[col_cierre].apply(clean_price)

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

        # Mostrar totales si las columnas existen
        if col_cierre and col_prom:
            total_cierre = filtered_df[col_cierre].sum()
            total_promocion = filtered_df[col_prom].sum()
            st.markdown(f"### 💰 Total {col_cierre}: ${total_cierre:,.2f}")
            st.markdown(f"### 💡 Total {col_prom}: ${total_promocion:,.2f}")
        else:
            st.info("No se encontraron columnas de cierre o promoción para mostrar totales.")
