
import streamlit as st
import pandas as pd
import io

def clean_price(x):
    if pd.isnull(x):
        return 0.0
    return float(str(x).replace('$', '').replace(',', '').replace(' ', '').strip())

st.title("Filtrado y Resumen de Datos 21 Online")

uploaded_file = st.file_uploader("Sube tu archivo Excel con los datos:", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    if "Empresa" not in df.columns:
        df["Empresa"] = "Desconocida"

    # Limpiar precios
    df["Precio Promoción"] = df["Precio Promoción"].apply(clean_price)
    df["Precio Cierre"] = df["Precio Cierre"].apply(clean_price)

    # Convertir fecha si es necesario
    if not pd.api.types.is_datetime64_any_dtype(df["Fecha Cierre"]):
        df["Fecha Cierre"] = pd.to_datetime(df["Fecha Cierre"], errors='coerce')

    # Filtros
    fecha = st.date_input("Selecciona la Fecha Exacta de Cierre", value=None)
    asesor = st.text_input("Nombre del Asesor (parte del nombre):")
    empresa = st.text_input("Nombre de la Empresa (parte del nombre):")

    # Aplicar filtros dinámicos
    filtered_df = df.copy()
    if fecha:
        filtered_df = filtered_df[filtered_df["Fecha Cierre"].dt.date == fecha]
    if asesor:
        mask = filtered_df["Asesor Captador"].str.contains(asesor, case=False, na=False) | \
               filtered_df["Asesor Colocador"].str.contains(asesor, case=False, na=False)
        filtered_df = filtered_df[mask]
    if empresa:
        filtered_df = filtered_df[filtered_df["Empresa"].str.contains(empresa, case=False, na=False)]

    # Mostrar tabla filtrada
    st.dataframe(filtered_df)

    # Mostrar sumas
    total_prom = filtered_df["Precio Promoción"].sum()
    total_cierre = filtered_df["Precio Cierre"].sum()

    st.write(f"**Total Precio Promoción:** ${total_prom:,.2f}")
    st.write(f"**Total Precio Cierre:** ${total_cierre:,.2f}")

    # Opción para descargar
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        filtered_df.to_excel(writer, index=False)
    buffer.seek(0)

    st.download_button(
        "Descargar datos filtrados",
        data=buffer,
        file_name="datos_filtrados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
