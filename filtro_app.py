
import streamlit as st
import pandas as pd
import openpyxl
from io import BytesIO
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="21 Online App", page_icon="📊")
st.markdown("<style>h1, h2, h3 {color: #B4975A;}</style>", unsafe_allow_html=True)
st.title("📊 21 Online - Reportes con Exportación y Gráficos")

ACCESS_CODE = "21ONLINE2024"
code_input = st.sidebar.text_input("🔑 Código de acceso:", type="password")
if code_input != ACCESS_CODE:
    st.warning("🔒 Código incorrecto.")
    st.stop()

def clean_price(x):
    if pd.isnull(x): return 0.0
    return float(str(x).replace('$','').replace(',','').strip())

def load_and_merge(files):
    dfs = []
    for file in files:
        try:
            temp = pd.read_excel(file, header=None)
            header_row = temp[temp.apply(lambda row: row.astype(str).str.contains("Fecha Cierre").any(), axis=1)].index
            if not header_row.empty:
                df = pd.read_excel(file, header=header_row[0])
                dfs.append(df)
        except: pass
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

uploaded_files = st.file_uploader("📂 Sube uno o más archivos Excel:", type=["xlsx"], accept_multiple_files=True)
if uploaded_files:
    df = load_and_merge(uploaded_files)
    if df.empty:
        st.warning("⚠ No se pudo procesar ningún archivo válido.")
    else:
        for col in ["Precio Promoción", "Precio Cierre"]:
            if col in df.columns:
                df[col] = df[col].apply(clean_price)
        if "Fecha Cierre" in df.columns:
            df["Fecha Cierre"] = pd.to_datetime(df["Fecha Cierre"], errors='coerce')

        with st.sidebar:
            search = st.text_input("🔍 Buscar palabra clave:").strip()
            if "Fecha Cierre" in df.columns:
                min_d, max_d = df["Fecha Cierre"].min().date(), df["Fecha Cierre"].max().date()
                date_range = st.date_input("📅 Rango de fechas", value=(min_d, max_d))
            else: date_range = None

            asesores = []
            if "Asesor Captador" in df.columns or "Asesor Colocador" in df.columns:
                asesores = pd.unique(df.get(["Asesor Captador", "Asesor Colocador"], pd.DataFrame()).values.ravel("K"))
                asesores = [a for a in asesores if pd.notnull(a)]
                asesor_sel = st.multiselect("👤 Asesores", options=asesores)
            else: asesor_sel = []

            if "Subtipo de Propiedad" in df.columns:
                subtipo_sel = st.multiselect("🏠 Subtipo", options=df["Subtipo de Propiedad"].dropna().unique())
            else: subtipo_sel = []

        filtered_df = df.copy()
        if search:
            for col in ["Dirección", "Código", "Cliente"]:
                if col in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(search, case=False, na=False)]
        if date_range:
            start, end = date_range
            filtered_df = filtered_df[(filtered_df["Fecha Cierre"].dt.date >= start) & (filtered_df["Fecha Cierre"].dt.date <= end)]
        if asesor_sel:
            filtered_df = filtered_df[
                (filtered_df.get("Asesor Captador", "").isin(asesor_sel)) |
                (filtered_df.get("Asesor Colocador", "").isin(asesor_sel))]
        if subtipo_sel:
            filtered_df = filtered_df[filtered_df["Subtipo de Propiedad"].isin(subtipo_sel)]

        st.dataframe(filtered_df)

        # Totales
        st.markdown("### Totales")
        col1, col2 = st.columns(2)
        if "Precio Promoción" in filtered_df.columns:
            col1.metric("🔹 Total Promoción", f"${filtered_df['Precio Promoción'].sum():,.2f}")
        if "Precio Cierre" in filtered_df.columns:
            col2.metric("🔸 Total Cierre", f"${filtered_df['Precio Cierre'].sum():,.2f}")

        # Exportar a Excel
        towrite = BytesIO()
        filtered_df.to_excel(towrite, index=False, engine="openpyxl")
        towrite.seek(0)
        st.download_button("📥 Descargar Excel", towrite, file_name="reporte_21online.xlsx")

        # Gráfico por asesor
        if "Asesor Captador" in filtered_df.columns:
            st.markdown("### 📊 Cierre por Asesor Captador")
            chart_data = filtered_df.groupby("Asesor Captador")["Precio Cierre"].sum().sort_values(ascending=False)
            fig, ax = plt.subplots()
            chart_data.plot(kind="bar", ax=ax)
            ax.set_ylabel("Total Cierre")
            ax.set_title("Cierre por Asesor")
            st.pyplot(fig)

        # Gráfico por mes
        if "Fecha Cierre" in filtered_df.columns:
            st.markdown("### 📈 Cierre por Mes")
            monthly = filtered_df.copy()
            monthly["Mes"] = monthly["Fecha Cierre"].dt.to_period("M").astype(str)
            chart_data = monthly.groupby("Mes")["Precio Cierre"].sum()
            fig2, ax2 = plt.subplots()
            chart_data.plot(kind="bar", ax=ax2)
            ax2.set_ylabel("Total Cierre")
            ax2.set_title("Cierre Mensual")
            st.pyplot(fig2)
