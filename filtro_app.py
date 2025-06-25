
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

def normalize_column_names(df):
    df.columns = [
        col.strip().lower()
        .replace("á", "a").replace("é", "e").replace("í", "i")
        .replace("ó", "o").replace("ú", "u")
        .replace("  ", " ").replace("\n", " ")
        for col in df.columns
    ]
    return df

def load_excel_with_header_guess(file):
    for header_row in [0, 1, 2]:
        try:
            df = pd.read_excel(file, header=header_row)
            df = normalize_column_names(df)
            return df
        except:
            continue
    return pd.DataFrame()

uploaded_files = st.file_uploader("📂 Sube uno o más archivos Excel:", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    dfs = [load_excel_with_header_guess(f) for f in uploaded_files]
    df = pd.concat(dfs, ignore_index=True)

    if df.empty:
        st.warning("⚠ No se encontró información válida en los archivos.")
    else:
        if "precio promocion" in df.columns:
            df["precio promocion"] = df["precio promocion"].apply(clean_price)
        if "precio cierre" in df.columns:
            df["precio cierre"] = df["precio cierre"].apply(clean_price)
        if "fecha cierre" in df.columns:
            df["fecha cierre"] = pd.to_datetime(df["fecha cierre"], errors='coerce')

        with st.sidebar:
            st.header("Filtros")

            # Filtro por Asesor Captador o Colocador
            asesores = []
            if "asesor captador" in df.columns:
                asesores += df["asesor captador"].dropna().unique().tolist()
            if "asesor colocador" in df.columns:
                asesores += df["asesor colocador"].dropna().unique().tolist()
            asesores = sorted(set(asesores))
            if asesores:
                asesor_sel = st.multiselect("👤 Asesor (captador o colocador):", asesores, default=asesores)
                mask = pd.Series(False, index=df.index)
                if "asesor captador" in df.columns:
                    mask = mask | df["asesor captador"].isin(asesor_sel)
                if "asesor colocador" in df.columns:
                    mask = mask | df["asesor colocador"].isin(asesor_sel)
                df = df[mask]

            # Filtro por subtipo
            if "subtipo de propiedad" in df.columns:
                subtipos = sorted(df["subtipo de propiedad"].dropna().unique())
                subtipo_sel = st.multiselect("🏠 Subtipo de Propiedad:", subtipos, default=subtipos)
                df = df[df["subtipo de propiedad"].isin(subtipo_sel)]

            # Filtro por fecha
            if "fecha cierre" in df.columns:
                min_fecha = df["fecha cierre"].min()
                max_fecha = df["fecha cierre"].max()
                fecha_sel = st.date_input("📅 Rango de Fecha Cierre:", [min_fecha, max_fecha])
                if len(fecha_sel) == 2:
                    df = df[(df["fecha cierre"] >= pd.to_datetime(fecha_sel[0])) & 
                            (df["fecha cierre"] <= pd.to_datetime(fecha_sel[1]))]

            # Búsqueda
            search = st.text_input("🔎 Buscar palabra clave (dirección, código, cliente):").strip()
            if search:
                search_cols = ["direccion", "codigo", "cliente"]
                mask = pd.Series(False, index=df.index)
                for col in search_cols:
                    if col in df.columns:
                        mask = mask | df[col].astype(str).str.contains(search, case=False, na=False)
                df = df[mask]

        st.dataframe(df)

        if "precio cierre" in df.columns:
            total_cierre = df["precio cierre"].sum()
            st.markdown(f"### 💰 Total Precio Cierre: ${total_cierre:,.2f}")
        else:
            st.info("No se encontró la columna 'Precio Cierre'.")

        if "precio promocion" in df.columns:
            total_promocion = df["precio promocion"].sum()
            st.markdown(f"### 💡 Total Precio Promoción: ${total_promocion:,.2f}")
        else:
            st.info("No se encontró la columna 'Precio Promoción'.")
