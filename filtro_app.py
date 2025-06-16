
import streamlit as st
import pandas as pd
import io
import openpyxl
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile

st.set_page_config(layout="wide")

# --- Autenticación simple ---
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

st.markdown("""
<h1 style='text-align: center; color: #4CAF50;'>📊 21 Online - App Completa</h1>
""", unsafe_allow_html=True)

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
            st.header("Filtros")
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
                st.warning("No hay columnas de asesor")

            if "Subtipo de Propiedad" in df.columns:
                subtipos = pd.unique(df["Subtipo de Propiedad"].dropna())
                subtipo_sel = st.multiselect("Subtipo de Propiedad", options=subtipos)
            else:
                subtipo_sel = []
                st.warning("No hay columna 'Subtipo de Propiedad'")

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

            # Ordenamiento dinámico
            sort_col = st.selectbox("Ordenar por:", options=df.columns.tolist())
            sort_asc = st.radio("Orden:", options=["Ascendente", "Descendente"]) == "Ascendente"

        filtered_df = df.copy()
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

        filtered_df = filtered_df.sort_values(by=sort_col, ascending=sort_asc)

        col1, col2 = st.columns(2)
        if "Precio Promoción" in filtered_df.columns:
            total_prom = filtered_df["Precio Promoción"].sum()
            col1.metric(label="💰 Total Precio Promoción", value=f"${total_prom:,.2f}")
        if "Precio Cierre" in filtered_df.columns:
            total_cierre = filtered_df["Precio Cierre"].sum()
            col2.metric(label="💵 Total Precio Cierre", value=f"${total_cierre:,.2f}")

        st.dataframe(filtered_df)

        # Gráfico
        if "Asesor Captador" in filtered_df.columns:
            st.markdown("### 🔎 Ventas por Asesor Captador")
            resumen = filtered_df.groupby("Asesor Captador")["Precio Cierre"].sum().sort_values()
            fig, ax = plt.subplots()
            resumen.plot(kind="barh", ax=ax)
            ax.set_xlabel("Precio Cierre Total")
            st.pyplot(fig)

        # Excel export
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
        st.download_button("📥 Descargar Excel filtrado", data=buffer, file_name="reporte_completo.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # PDF export
        if st.button("📄 Generar PDF con gráfico"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Reporte 21 Online", ln=True, align="C")
            pdf.ln(10)
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 10, f"Total Precio Promoción: ${total_prom:,.2f}", ln=True)
            pdf.cell(0, 10, f"Total Precio Cierre: ${total_cierre:,.2f}", ln=True)
            # Guardar gráfico temporal
            with tempfile.NamedTemporaryFile(suffix=".png") as tmpfile:
                fig.savefig(tmpfile.name)
                pdf.image(tmpfile.name, x=10, y=None, w=180)
                pdf.ln(10)
            pdf_output = buffer = io.BytesIO()
            pdf.output(pdf_output)
            st.download_button("📥 Descargar PDF", data=pdf_output.getvalue(),
                               file_name="reporte_completo.pdf", mime="application/pdf")

st.markdown("<p style='text-align: center; color: gray; font-size: small;'>Aplicación 21 Online ©</p>", unsafe_allow_html=True)
