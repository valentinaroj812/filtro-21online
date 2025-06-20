
import streamlit as st
import pandas as pd
import io
import openpyxl

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

            if "Fecha Cierre" in df.columns:
                min_date = df["Fecha Cierre"].min().date()
                max_date = df["Fecha Cierre"].max().date()
                fecha_rango = st.date_input("Rango de fechas", value=(min_date, max_date))
            else:
                fecha_rango = None
                st.warning("No hay columna 'Fecha Cierre'")

            asesores = []
            if "Asesor Captador" in df.columns or "Asesor Colocador" in df.columns:
                asesores = pd.unique(df.get(["Asesor Captador", "Asesor Colocador"], pd.DataFrame()).values.ravel('K'))
                asesores = [a for a in asesores if pd.notnull(a)]
                asesor_sel = st.multiselect("Asesores", options=asesores)
            else:
                asesor_sel = []

            if "Subtipo de Propiedad" in df.columns:
                subtipos = pd.unique(df["Subtipo de Propiedad"].dropna())
                subtipo_sel = st.multiselect("Subtipo de Propiedad", options=subtipos)
            else:
                subtipo_sel = []

            if "Precio Promoción" in df.columns:
                min_prom = float(df["Precio Promoción"].min())
                max_prom = float(df["Precio Promoción"].max())
                rango_prom = st.slider("Rango Precio Promoción", min_value=min_prom, max_value=max_prom, value=(min_prom, max_prom))
            else:
                rango_prom = None

            if "Precio Cierre" in df.columns:
                min_cierre = float(df["Precio Cierre"].min())
                max_cierre = float(df["Precio Cierre"].max())
                rango_cierre = st.slider("Rango Precio Cierre", min_value=min_cierre, max_value=max_cierre, value=(min_cierre, max_cierre))
            else:
                rango_cierre = None

        filtered_df = df.copy()

        if search:
            search_cols = ["Dirección", "Código", "Cliente"]
            mask = pd.Series(False, index=filtered_df.index)
            for col in search_cols:
                if col in filtered_df.columns:
                    mask = mask | filtered_df[col].astype(str).str.contains(search, case=False, na=False)
            filtered_df = filtered_df[mask]

        if fecha_rango:
            start_date, end_date = fecha_rango
            filtered_df = filtered_df[(filtered_df["Fecha Cierre"].dt.date >= start_date) &
                                      (filtered_df["Fecha Cierre"].dt.date <= end_date)]
        if asesor_sel:
            filtered_df = filtered_df[(filtered_df.get("Asesor Captador", "").isin(asesor_sel)) |
                                      (filtered_df.get("Asesor Colocador", "").isin(asesor_sel))]
        if subtipo_sel:
            filtered_df = filtered_df[filtered_df["Subtipo de Propiedad"].isin(subtipo_sel)]
        if rango_prom:
            filtered_df = filtered_df[(filtered_df["Precio Promoción"] >= rango_prom[0]) &
                                      (filtered_df["Precio Promoción"] <= rango_prom[1])]
        if rango_cierre:
            filtered_df = filtered_df[(filtered_df["Precio Cierre"] >= rango_cierre[0]) &
                                      (filtered_df["Precio Cierre"] <= rango_cierre[1])]

        st.dataframe(filtered_df)
