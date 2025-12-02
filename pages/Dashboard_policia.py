import streamlit as st
import pandas as pd
import branca.colormap as cm
import geopandas as gpd
import folium
from shapely.geometry import shape
import ast
from streamlit_folium import st_folium

# ======================================
# CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Sistema de seguridad CDMX",
    layout="wide"
)

# ======================================
# CONTROL DE SESIÓN
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Acceso restringido. Por favor inicia sesión desde la página principal.")
    st.stop()

# Solamente acceden usuarios con rol 'analyst'
if st.session_state["role"] not in ["analyst"]:
    st.error(" No tienes permiso para acceder a este módulo.")
    st.stop()

# ======================================
# ENCABEZADO CON BOTONES
col_header, col_btn_chat, col_btn_logout = st.columns([6, 1, 1])

with col_header:
    st.title("Mapa de predicciones de robos por cuadrante CDMX")

with col_btn_chat:
    # Botón para ir al Chatbot
    if st.button("Chatbot", use_container_width=True, key="nav_chatbot_policia"):
        st.switch_page("pages/Chatbot.py")

with col_btn_logout:
    # Botón para cerrar sesión
    if st.button("Cerrar sesión", use_container_width=True, key="logout_policia"):
        st.session_state.clear()
        st.switch_page("menu_inicio.py")

# ======================================

# CARGA Y PREPARACIÓN DE DATOS
@st.cache_data
def load_cuadrantes(path_csv: str):
    df = pd.read_csv(path_csv)

    def parse_geo_shape(geo_string):
        try:
            geo_dict = ast.literal_eval(geo_string)
            return shape(geo_dict)
        except Exception:
            return None

    df["geometry"] = df["geo_shape"].apply(parse_geo_shape)
    df = df[~df["geometry"].isna()].copy()

    gdf = gpd.GeoDataFrame(
        df,
        geometry="geometry",
        crs="EPSG:4326"
    )
    return gdf


@st.cache_data
def load_predicciones(path_csv: str):
    df = pd.read_csv(path_csv, parse_dates=["ds"])
    return df

# Rutas de los archivos
RUTA_CUADRANTES = "bases_de_datos/cuadrantes.csv"
RUTA_PREDICCIONES = "bases_de_datos/predicciones_xgb.csv"

# Cargar los mapas y predicciones
try:
    gdf_cuadrantes = load_cuadrantes(RUTA_CUADRANTES)
except FileNotFoundError:
    st.error(f"No se encontró el archivo `{RUTA_CUADRANTES}`. Verifica la ruta.")
    st.stop()

if gdf_cuadrantes.empty:
    st.warning("El GeoDataFrame de cuadrantes está vacío después de procesar geometrías.")
    st.stop()

try:
    df_pred = load_predicciones(RUTA_PREDICCIONES)
except FileNotFoundError:
    st.error(f"No se encontró el archivo `{RUTA_PREDICCIONES}`. Verifica la ruta.")
    st.stop()

# =====================================================
# MAPA DE PREDICCIONES XGBoost POR CUADRANTE
df_pred["anio"] = df_pred["ds"].dt.year
df_pred["mes"] = df_pred["ds"].dt.month

# Enumeración de meses
NOMBRE_MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

# ======================================
# CONTROLES DE TAMAÑO EN LA SIDEBAR
# Tamaño texto KPIs
tam_kpi = st.sidebar.number_input(
    "Tamaño texto KPIs",
    min_value=10,
    max_value=40,
    value=25, 
    step=1,
    key="tam_kpi_policia"
)

# Tamaño texto filtros
tam_filtros = st.sidebar.number_input(
    "Tamaño texto filtros",
    min_value=10,
    max_value=30,
    value=14,      # valor inicial
    step=1,
    key="tam_filtros_policia"
)

# CSS  para las tarjetas de KPIs
kpi_css = f"""
<style>
.kpi-card {{
    background-color: #000275;
    padding: 14px 18px;
    border-radius: 12px;
    color: #FFFFFF;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}

/* Etiqueta (texto de arriba) */
.kpi-label {{
    font-size: {tam_kpi - 6}px;
    opacity: 0.9;
}}

/* Valor principal de la KPI */
.kpi-value {{
    font-size: {tam_kpi}px;
    font-weight: 700;
    margin-top: 4px;
}}

/* Texto secundario (si se usa) */
.kpi-sub {{
    font-size: {tam_kpi - 8}px;
    opacity: 0.75;
    margin-top: 2px;
}}
</style>
"""
st.markdown(kpi_css, unsafe_allow_html=True)

# CSS  para filtros 
filtros_css = f"""
<style>
.filtro-label {{
    font-size: {tam_filtros}px;
    font-weight: 500;
    margin-bottom: 3px;
}}

/* Texto dentro de los selectbox (opción seleccionada) */
.stSelectbox div[data-baseweb="select"] > div {{
    font-size: {tam_filtros - 1}px;
}}
</style>
"""
st.markdown(filtros_css, unsafe_allow_html=True)

# ======================================
# FILTROS (AÑO, MES, DELITO, CELDA)
col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    st.markdown('<div class="filtro-label">Año de predicción:</div>', unsafe_allow_html=True)
    anios_disponibles = sorted(df_pred["anio"].unique())
    anio_sel = st.selectbox(
        "Año de predicción",
        options=anios_disponibles,
        index=len(anios_disponibles) - 1,
        key="anio_pred_policia",
        label_visibility="collapsed"
    )

with col_f2:
    st.markdown('<div class="filtro-label">Mes de predicción:</div>', unsafe_allow_html=True)
    meses_disp = sorted(df_pred[df_pred["anio"] == anio_sel]["mes"].unique())
    opciones_meses = [NOMBRE_MESES[m] for m in meses_disp]
    nombre_mes_sel = st.selectbox(
        "Mes de predicción",
        options=opciones_meses,
        index=len(opciones_meses) - 1,
        key="mes_pred_policia",
        label_visibility="collapsed"
    )
    mes_sel = [k for k, v in NOMBRE_MESES.items() if v == nombre_mes_sel][0]

with col_f3:
    st.markdown('<div class="filtro-label">Tipo de robo:</div>', unsafe_allow_html=True)
    delitos_unicos = sorted(df_pred["delito"].unique())
    opciones_delito = ["Todos los delitos"] + delitos_unicos
    delito_sel = st.selectbox(
        "Tipo de robo",
        options=opciones_delito,
        index=0,
        key="delito_pred_policia",
        label_visibility="collapsed"
    )

with col_f4:
    st.markdown('<div class="filtro-label">ID del cuadrante :</div>', unsafe_allow_html=True)
    ids_unicos = sorted(df_pred["cell_id"].unique())
    opciones_celda = ["Todos los cuadrantes"] + [str(i) for i in ids_unicos]
    celda_sel = st.selectbox(
        "ID del cuadrante",
        options=opciones_celda,
        index=0,
        key="celda_pred_policia",
        label_visibility="collapsed"
    )

# Filtro para escoger variable
col_var = st.columns(1)[0]
with col_var:
    st.markdown('<div class="filtro-label">Variable a visualizar:</div>', unsafe_allow_html=True)
    variable_sel = st.selectbox(
        "Variable a visualizar",
        options=["score", "yhat_cnt_xgb"],
        format_func=lambda v: "Probabilidad (score)" if v == "score" else "Conteo esperado",
        key="variable_pred_policia",
        label_visibility="collapsed"
    )

# Base global para rangos de colores
df_pred_base = df_pred[
    (df_pred["anio"] == anio_sel) &
    (df_pred["mes"] == mes_sel)
].copy()

if delito_sel != "Todos los delitos":
    df_pred_base = df_pred_base[df_pred_base["delito"] == delito_sel]

# Filtro para KPIs y mapa
df_pred_filtro = df_pred_base.copy()

if celda_sel != "Todos los cuadrantes":
    id_celda = int(celda_sel)
    df_pred_filtro = df_pred_filtro[df_pred_filtro["cell_id"] == id_celda]

# ======================================
# KPIs + MAPA
if df_pred_filtro.empty:
    st.info("No hay predicciones para esa combinación de filtros.")
else:
    # KPIs PRINCIPALES
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    # Robos esperados en el mes - Se suman las predicciones
    total_robos = df_pred_filtro["yhat_cnt_xgb"].sum()

    # Riesgo promedio en el subset
    riesgo_prom = df_pred_filtro["score"].mean()

    # Cuadrantes críticos en el subset percentil 75
    umbral_alto = df_pred_filtro["score"].quantile(0.75)
    n_criticos = df_pred_filtro[df_pred_filtro["score"] >= umbral_alto]["cell_id"].nunique()
    total_celdas = df_pred_filtro["cell_id"].nunique()

    # Cuadrantes en riesgo bajo percentil 25
    q1 = df_pred_filtro["score"].quantile(0.25)
    pct_bajo = (df_pred_filtro["score"] <= q1).mean() * 100

    with kpi1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Robos esperados (mes)</div>
            <div class="kpi-value">{total_robos:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Riesgo promedio por cuadrante</div>
            <div class="kpi-value">{riesgo_prom:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Cuadrantes críticos (score alto)</div>
            <div class="kpi-value">{n_criticos} / {total_celdas}</div>
        </div>
        """, unsafe_allow_html=True)



    st.markdown("---")

    # ============================
    # MAPA DE PREDICCIONES
    # Agregado para el subset filtrado
    df_pred_agg = (
        df_pred_filtro
        .groupby("cell_id", as_index=False)[variable_sel]
        .mean()
    )

    #Union de cuadrantes con predicciones
    gdf_pred = gdf_cuadrantes.merge(
        df_pred_agg,
        left_on="id",
        right_on="cell_id",
        how="inner"
    )

    if gdf_pred.empty:
        st.info("No hay cuadrantes con geometría para esas predicciones.")
    else:
        df_pred_agg_global = (
            df_pred_base
            .groupby("cell_id", as_index=False)[variable_sel]
            .mean()
        )
        # Rango global para colores
        vmin = df_pred_agg_global[variable_sel].min()
        vmax = df_pred_agg_global[variable_sel].max()
        if vmin == vmax:
            vmax = vmin + 1e-6

        datetime_cols = gdf_pred.select_dtypes(
            include=["datetime64[ns]", "datetime64[ns, UTC]"]
        ).columns
        for c in datetime_cols:
            gdf_pred[c] = gdf_pred[c].dt.strftime("%Y-%m-%d")
        # Centro del mapa
        centro_pred = gdf_pred.geometry.unary_union.centroid
        centro_lat_pred = centro_pred.y
        centro_lon_pred = centro_pred.x

        mapa_pred = folium.Map(
            location=[centro_lat_pred, centro_lon_pred],
            zoom_start=11,
            tiles="CartoDB positron"
        )

        # Capa base
        tooltip_base = folium.GeoJsonTooltip(
            fields=["id", "alcaldia", "zona", "sector", "no_region", "no_cuadran"],
            aliases=["ID:", "Alcaldía:", "Zona:", "Sector:", "Región:", "Cuadrante:"],
            sticky=True
        )
        # Capa de cuadrantes
        folium.GeoJson(
            gdf_cuadrantes.to_json(),
            name="Sectores de patrullaje",
            tooltip=tooltip_base,
            style_function=lambda feature: {
                "fillColor": "rgba(0, 0, 255, 0.1)",
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.1,
            },
        ).add_to(mapa_pred)

        # Capa de predicciones
        colormap = cm.linear.YlOrRd_09.scale(vmin, vmax)

        etiqueta_delito = (
            "Todos los delitos" if delito_sel == "Todos los delitos" else delito_sel
        )

        if celda_sel != "Todos los cuadrantes":
            extra_celda = f" - Cuadrante {celda_sel}"
        else:
            extra_celda = ""

        colormap.caption = (
            f"Nivel de riesgo ({'score' if variable_sel == 'score' else 'conteo esperado'}) "
            f"- {etiqueta_delito} - {nombre_mes_sel} {anio_sel}{extra_celda}"
        )

        tooltip_pred = folium.GeoJsonTooltip(
            fields=["id", "alcaldia", "zona", "sector", variable_sel],
            aliases=["ID:", "Alcaldía:", "Zona:", "Sector:", "Predicción (promedio mensual):"],
            sticky=True
        )

        folium.GeoJson(
            gdf_pred.to_json(),
            name="Predicciones XGB",
            style_function=lambda feature: {
                "fillColor": colormap(feature["properties"][variable_sel]),
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.7,
            },
            tooltip=tooltip_pred,
        ).add_to(mapa_pred)

        colormap.add_to(mapa_pred)
        folium.LayerControl().add_to(mapa_pred)

        st_folium(mapa_pred, width="100%", height=600)