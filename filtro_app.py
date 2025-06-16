
import streamlit as st
import pandas as pd
import io
import openpyxl

st.set_page_config(layout="wide")

def clean_price(x):
    if pd.isnull(x):
        return 0.0
    return float(str(x).replace('$', '').replace(',', '').replace(' ', '').strip())

def load_excel_dynamic(file):
    # Intentar con header=0
    df = pd.read_excel(file, header=0)
    if "Fecha Cierre" not in df.columns and "Asesor Captador" not in df.columns:
        # Intentar con header=1 si no se detectan columnas clave
        df = pd.read_excel(file, header=1)
    return df

st.markdown("""
<h1 style='text-align: center; color: #4CAF50;'>📊 Analizador Universal de Archivos 21 Online</h1>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("📂 Sube tu archivo Excel para analizar:", type=["xlsx"])

if uploaded_file:
    df = load_excel_dynamic(uploaded_file)

    st.markdown("---")

    if "Precio Promoción" in df.columns:
        df["Precio Promoción"] = df["Precio Promoción"].apply(clean_price)
    if "Precio Cierre" in df.columns:
        df["Precio Cierre"] = df["Precio Cierre"].apply(clean_price)

    if "Fecha Cierre" in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df["Fecha Cierre"]):
            df["Fecha Cierre"] = pd.to_datetime(df["Fecha Cierre"], errors='coerce')

    if "Fecha Cierre" in df.columns:
        min_date = df["Fecha Cierre"].min().date()
        max_date = df["Fecha Cierre"].max().date()
        fecha_rango = st.date_input("📅 Selecciona el rango de fechas de cierre:", value=(min_date, max_date))
    else:
        fecha_rango = None
        st.warning("⚠ El archivo no tiene la columna 'Fecha Cierre' para filtrar por fecha.")

    if "Asesor Captador" in df.columns or "Asesor Colocador" in df.columns:
        asesores = pd.unique(df.get(["Asesor Captador", "Asesor Colocador"], pd.DataFrame()).values.ravel('K'))
        asesores = [a for a in asesores if pd.notnull(a)]
        asesor_sel = st.selectbox("👤 Selecciona un Asesor:", options=["Todos"] + asesores)
    else:
        asesor_sel = "Todos"
        st.warning("⚠ El archivo no tiene las columnas de asesor para filtrar.")

    if "Subtipo de Propiedad" in df.columns:
        subtipos = pd.unique(df["Subtipo de Propiedad"].dropna())
        subtipo_sel = st.selectbox("🏠 Selecciona el Subtipo de Propiedad:", options=["Todos"] + list(subtipos))
    else:
        subtipo_sel = "Todos"
        st.warning("⚠ El archivo no tiene la columna 'Subtipo de Propiedad' para filtrar.")

    st.markdown("---")

    filtered_df = df.copy()
    if fecha_rango:
        start_date, end_date = fecha_rango
        filtered_df = filtered_df[(filtered_df["Fecha Cierre"].dt.date >= start_date) &
                                  (filtered_df["Fecha Cierre"].dt.date <= end_date)]
    if asesor_sel != "Todos":
        filtered_df = filtered_df[(filtered_df.get("Asesor Captador", "") == asesor_sel) |
                                  (filtered_df.get("Asesor Colocador", "") == asesor_sel)]
    if subtipo_sel != "Todos":
        filtered_df = filtered_df[filtered_df["Subtipo de Propiedad"] == subtipo_sel]

    st.dataframe(filtered_df)

    st.markdown("---")

    col3, col4 = st.columns(2)
    if "Precio Promoción" in filtered_df.columns:
        total_prom = filtered_df["Precio Promoción"].sum()
        col3.metric(label="💰 Total Precio Promoción", value=f"${total_prom:,.2f}")
    if "Precio Cierre" in filtered_df.columns:
        total_cierre = filtered_df["Precio Cierre"].sum()
        col4.metric(label="💵 Total Precio Cierre", value=f"${total_cierre:,.2f}")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name="Datos Filtrados")
        ws = writer.book["Datos Filtrados"]
        accounting_fmt = "$#,##0.00_);[Red]($#,##0.00)"
        col_map = {col: idx+1 for idx, col in enumerate(filtered_df.columns)}
        for col_name in ["Precio Promoción", "Precio Cierre"]:
            if col_name in col_map:
                col_letter = openpyxl.utils.get_column_letter(col_map[col_name])
                for cell in ws[col_letter][1:]:
                    cell.number_format = accounting_fmt
    buffer.seek(0)

    st.download_button(
        "📥 Descargar reporte filtrado",
        data=buffer,
        file_name="reporte_filtrado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
