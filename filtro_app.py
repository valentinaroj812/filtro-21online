
import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")

def clean_price(x):
    if pd.isnull(x):
        return 0.0
    return float(str(x).replace('$', '').replace(',', '').replace(' ', '').strip())

st.markdown("""
<h1 style='text-align: center; color: #4CAF50;'>📊 Filtro Avanzado de 21 Online</h1>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("📂 Sube tu archivo Excel con los datos:", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Limpiar precios
    df["Precio Promoción"] = df["Precio Promoción"].apply(clean_price)
    df["Precio Cierre"] = df["Precio Cierre"].apply(clean_price)

    if not pd.api.types.is_datetime64_any_dtype(df["Fecha Cierre"]):
        df["Fecha Cierre"] = pd.to_datetime(df["Fecha Cierre"], errors='coerce')

    st.markdown("---")

    # Filtros avanzados
    min_date = df["Fecha Cierre"].min().date()
    max_date = df["Fecha Cierre"].max().date()
    col1, col2 = st.columns(2)
    with col1:
        fecha_rango = st.date_input("📅 Selecciona el rango de fechas de cierre:", value=(min_date, max_date))
    with col2:
        asesores = pd.unique(df[["Asesor Captador", "Asesor Colocador"]].values.ravel('K'))
        asesores = [a for a in asesores if pd.notnull(a)]
        asesor_sel = st.selectbox("👤 Selecciona un Asesor:", options=["Todos"] + asesores)

    subtipos = pd.unique(df["Subtipo de Propiedad"].dropna())
    subtipo_sel = st.selectbox("🏠 Selecciona el Subtipo de Propiedad:", options=["Todos"] + list(subtipos))

    st.markdown("---")

    # Aplicar filtros
    filtered_df = df.copy()
    if fecha_rango:
        start_date, end_date = fecha_rango
        filtered_df = filtered_df[(filtered_df["Fecha Cierre"].dt.date >= start_date) &
                                  (filtered_df["Fecha Cierre"].dt.date <= end_date)]
    if asesor_sel != "Todos":
        filtered_df = filtered_df[(filtered_df["Asesor Captador"] == asesor_sel) |
                                  (filtered_df["Asesor Colocador"] == asesor_sel)]
    if subtipo_sel != "Todos":
        filtered_df = filtered_df[filtered_df["Subtipo de Propiedad"] == subtipo_sel]

    if "Empresa" in filtered_df.columns:
        filtered_df = filtered_df.drop(columns=["Empresa"])

    st.dataframe(filtered_df)

    st.markdown("---")

    # Mostrar sumas en columnas
    col3, col4 = st.columns(2)
    total_prom = filtered_df["Precio Promoción"].sum()
    total_cierre = filtered_df["Precio Cierre"].sum()
    col3.metric(label="💰 Total Precio Promoción", value=f"${total_prom:,.2f}")
    col4.metric(label="💵 Total Precio Cierre", value=f"${total_cierre:,.2f}")

    # Exportación con formato contable en Excel
    import openpyxl
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name="Datos Filtrados")
        ws = writer.book["Datos Filtrados"]
        accounting_fmt = "$#,##0.00_);[Red]($#,##0.00)"
        for col_letter in ['P', 'Q']:
            for cell in ws[col_letter][1:]:
                cell.number_format = accounting_fmt
    buffer.seek(0)

    st.download_button(
        "📥 Descargar reporte filtrado",
        data=buffer,
        file_name="reporte_filtrado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.markdown("""
    <p style='text-align: center; color: gray; font-size: small;'>Aplicación generada por 21 Online ©</p>
    """, unsafe_allow_html=True)
