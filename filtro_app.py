
import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt

def clean_price(x):
    if pd.isnull(x):
        return 0.0
    return float(str(x).replace('$', '').replace(',', '').replace(' ', '').strip())

st.title("📊 Filtro Avanzado y Reporte de 21 Online")

uploaded_file = st.file_uploader("Sube tu archivo Excel con los datos:", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if "Empresa" not in df.columns:
        df["Empresa"] = "Desconocida"

    # Limpiar precios
    df["Precio Promoción"] = df["Precio Promoción"].apply(clean_price)
    df["Precio Cierre"] = df["Precio Cierre"].apply(clean_price)

    if not pd.api.types.is_datetime64_any_dtype(df["Fecha Cierre"]):
        df["Fecha Cierre"] = pd.to_datetime(df["Fecha Cierre"], errors='coerce')

    # Filtros avanzados
    min_date = df["Fecha Cierre"].min().date()
    max_date = df["Fecha Cierre"].max().date()
    fecha_rango = st.date_input("Selecciona el rango de fechas de cierre:", value=(min_date, max_date))

    asesores = pd.unique(df[["Asesor Captador", "Asesor Colocador"]].values.ravel('K'))
    asesores = [a for a in asesores if pd.notnull(a)]
    asesor_sel = st.selectbox("Selecciona un Asesor:", options=["Todos"] + asesores)

    empresas = pd.unique(df["Empresa"])
    empresa_sel = st.selectbox("Selecciona una Empresa:", options=["Todos"] + list(empresas))

    # Aplicar filtros
    filtered_df = df.copy()
    if fecha_rango:
        start_date, end_date = fecha_rango
        filtered_df = filtered_df[(filtered_df["Fecha Cierre"].dt.date >= start_date) &
                                  (filtered_df["Fecha Cierre"].dt.date <= end_date)]
    if asesor_sel != "Todos":
        filtered_df = filtered_df[(filtered_df["Asesor Captador"] == asesor_sel) |
                                  (filtered_df["Asesor Colocador"] == asesor_sel)]
    if empresa_sel != "Todos":
        filtered_df = filtered_df[filtered_df["Empresa"] == empresa_sel]

    st.dataframe(filtered_df)

    # Mostrar sumas
    total_prom = filtered_df["Precio Promoción"].sum()
    total_cierre = filtered_df["Precio Cierre"].sum()

    st.write(f"**Total Precio Promoción:** ${total_prom:,.2f}")
    st.write(f"**Total Precio Cierre:** ${total_cierre:,.2f}")

    # Gráfico de barras por empresa
    fig, ax = plt.subplots()
    resumen = filtered_df.groupby("Empresa")["Precio Cierre"].sum().sort_values()
    resumen.plot(kind="barh", ax=ax)
    ax.set_xlabel("Precio Cierre Total")
    ax.set_title("Ventas por Empresa")
    st.pyplot(fig)

    # Exportación de datos filtrados
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name="Datos Filtrados")
        resumen.to_frame(name="Total Precio Cierre").to_excel(writer, sheet_name="Resumen Empresa")
    buffer.seek(0)

    st.download_button(
        "Descargar reporte filtrado",
        data=buffer,
        file_name="reporte_filtrado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
