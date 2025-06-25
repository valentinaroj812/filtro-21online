
import streamlit as st
import pandas as pd
import openpyxl

st.set_page_config(layout="wide", page_title="21 Online App", page_icon="📊")
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
            temp = pd.read_excel(file, header=None)
            # Encuentra fila que contiene "Fecha Cierre" y úsala como header
            header_row = temp[temp.apply(lambda row: row.astype(str).str.contains("Fecha Cierre").any(), axis=1)].index
            if not header_row.empty:
                df = pd.read_excel(file, header=header_row[0])
                dfs.append(df)
            else:
                st.error(f"⚠ No se encontró encabezado en el archivo: {file.name}")
        except Exception as e:
            st.error(f"⚠ No se pudo leer el archivo: {file.name}")
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()

st.markdown("<h1 style='text-align: center;'>📊 21 Online - Filtros Profesionales</h1>", unsafe_allow_html=True)

uploaded_files = st.file_uploader("📂 Sube uno o más archivos Excel:", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    df = load_and_merge(uploaded_files)

    if df.empty:
        st.warning("⚠ No se pudo procesar ningún archivo válido.")
    else:
        # Limpieza
        for col in ["Precio Promoción", "Precio Cierre"]:
            if col in df.columns:
                df[col] = df[col].apply(clean_price)

        if "Fecha Cierre" in df.columns:
            df["Fecha Cierre"] = pd.to_datetime(df["Fecha Cierre"], errors='coerce')

        with st.sidebar:
            st.header("Filtros")
            search = st.text_input("🔎 Buscar palabra clave (dirección, código, cliente):").strip()
            if "Fecha Cierre" in df.columns:
                min_date = df["Fecha Cierre"].min().date()
                max_date = df["Fecha Cierre"].max().date()
                fecha_rango = st.date_input("Rango de fechas", value=(min_date, max_date))
            else:
                fecha_rango = None

            asesores = []
            if "Asesor Captador" in df.columns or "Asesor Colocador" in df.columns:
                asesores = pd.unique(df.get(["Asesor Captador", "Asesor Colocador"], pd.DataFrame()).values.ravel("K"))
                asesores = [a for a in asesores if pd.notnull(a)]
                asesor_sel = st.multiselect("Asesores", options=asesores)
            else:
                asesor_sel = []

            if "Subtipo de Propiedad" in df.columns:
                subtipos = pd.unique(df["Subtipo de Propiedad"].dropna())
                subtipo_sel = st.multiselect("Subtipo de Propiedad", options=subtipos)
            else:
                subtipo_sel = []

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
            filtered_df = filtered_df[
                (filtered_df["Fecha Cierre"].dt.date >= start_date) &
                (filtered_df["Fecha Cierre"].dt.date <= end_date)
            ]

        if asesor_sel:
            filtered_df = filtered_df[
                (filtered_df.get("Asesor Captador", "").isin(asesor_sel)) |
                (filtered_df.get("Asesor Colocador", "").isin(asesor_sel))
            ]
        if subtipo_sel:
            filtered_df = filtered_df[filtered_df["Subtipo de Propiedad"].isin(subtipo_sel)]

        st.dataframe(filtered_df)

        st.markdown("### Totales")
        col1, col2 = st.columns(2)
        with col1:
            if "Precio Promoción" in filtered_df.columns:
                total_prom = filtered_df["Precio Promoción"].sum()
                st.metric("🔹 Total Promoción", f"${total_prom:,.2f}")
        with col2:
            if "Precio Cierre" in filtered_df.columns:
                total_cierre = filtered_df["Precio Cierre"].sum()
                st.metric("🔸 Total Cierre", f"${total_cierre:,.2f}")
