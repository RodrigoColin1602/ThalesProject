#Librerias necesarias para el funcionamiento del codigo 
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import numpy as np
import json
from datetime import timedelta
from data_loader import load_data 
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap

# ============================================================
# Tema global 
#Importar los colores definidos en los estilos de theme_config.py
try:
    from theme_config import inject_custom_css, CUSTOM_THEME
    inject_custom_css(CUSTOM_THEME)
except ImportError:
    pass

# ============================================================
# Control de acceso 
#Verificar si el usuario ha iniciado sesión con el rol adecuado
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = True
if not st.session_state["authenticated"]:
    st.warning("Acceso restringido. Por favor inicia sesión desde la página principal.")
    st.stop()

#Solo funciona si es viewer
if "role" not in st.session_state:
    st.session_state["role"] = "viewer"
if st.session_state.get("role") not in ["viewer"]:
    st.error("No tienes permiso para acceder a esta página.")
    st.stop()

# ============================================================
# Configuración de la página
st.set_page_config(page_title="Dashboard  Usuario", layout="wide")

# ============================================================
# Controles de tamaño de texto (sidebar) 
# Control para los textos de las KPIs
tam_kpi = st.sidebar.number_input(
    "Tamaño texto KPIs (Valor/Título)",
    min_value=10,
    max_value=40,
    value=15,   
    step=1,
    key="tam_kpi_usuario_new"
)

# Control para los textos de varianza de los KPIs
tam_delta = st.sidebar.number_input(
    "Tamaño texto Delta (+X.X%)",
    min_value=8,
    max_value=30,
    value=16, 
    step=1,
    key="tam_delta_usuario"
)
#Control para el de las leyendas  de las graficas
tam_graficas = st.sidebar.number_input(
    "Tamaño texto gráficas (ejes/leyendas)",
    min_value=8,
    max_value=30,
    value=12,
    step=1,
    key="tam_graficas_usuario",
)
#Control para el texto de los filtros
tam_filtros = st.sidebar.number_input(
    "Tamaño texto filtros",
    min_value=10,
    max_value=30,
    value=17,      
    step=1,
    key="tam_filtros_usuario_new"
)

# Control para la altura de las tarjetas KPI
altura_tarjetas_kpi = st.sidebar.number_input(
    "Altura de las tarjetas KPI (px)",
    min_value=100,
    max_value=300,
    value=150, 
    step=10,
    key="altura_tarjetas_kpi_usuario"
)

# ============================================================
# CSS global de las  METRICAS 
#Se utilizaron las variables definidas en el css global 
kpi_css = f"""
<style>
/* El contenedor general del KPI */
.kpi-card {{
    background-color: #000275;
    padding: 14px 18px;
    border-radius: 0.75rem; 
    min-height: {altura_tarjetas_kpi}px; 
    color: #FFFFFF;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}

/* Etiqueta (texto de arriba) - Controlada por tam_kpi */
.kpi-label {{
    font-size: {tam_kpi + 5}px; 
    font-weight: 700;
    line-height: 1.2;
    opacity: 1;
}}

/* Valor principal de la KPI (El Número) - Controlada por tam_kpi */
.kpi-value {{
    font-size: {tam_kpi + 15}px; 
    font-weight: 800;
    margin-top: 4px;
}}

/* Texto secundario (El Delta / Vs Mes Anterior) - 🟢 CONTROLADO POR tam_delta */
.kpi-sub {{
    font-size: {tam_delta}px; 
    font-weight: 600;
    opacity: 0.9;
    margin-top: 4px;
    border-radius: 4px;
    padding: 2px 6px;
    display: inline-block;
    width: fit-content;
}}

/* Clases para el color del delta */
.delta-normal {{ background-color: #19c95d; color: #FFFFFF; }} /* Verde para mejora */
.delta-inverse {{ background-color: #e73650; color: #FFFFFF; }} /* Rojo para alerta */
</style>
"""
st.markdown(kpi_css, unsafe_allow_html=True)

# CSS para filtros 
filtros_css = f"""
<style>
/* Etiqueta personalizada de filtro */
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


# ============================================================
# Inicio de la página 
#Estructura del encabezado y se definen los botones 
col_title, col_btn_perfil, col_btn_chatbot, col_btn_logout = st.columns([6, 2, 2, 2])

with col_title:
    st.markdown(
        """
        <h1 style="white-space: nowrap; margin-bottom: 0.5rem;">
            Dashboard del Usuario
        </h1>
        """,
        unsafe_allow_html=True,
    )
    
# Botón Perfiles de alcaldías
with col_btn_perfil:
    if st.button("Perfiles de alcaldías", use_container_width=True, key="logout_usuario"):
        st.switch_page("pages/Perfiles_de_alcaldias.py")

#Botón Chatbot (NUEVO)
with col_btn_chatbot:
    if st.button("Chatbot", use_container_width=True, key="chatbot_usuario"):
        # Asegúrate de que este archivo exista en la carpeta pages/
        st.switch_page("pages/Chatbot.py") 

#Botón Cerrar sesión
with col_btn_logout:
    if st.button("Cerrar sesión", use_container_width=True, key="logout_user"):
        st.session_state.clear()
        st.switch_page("menu_inicio.py")

st.markdown("---")
# ============================================================
#  CONSTANTES Y FUNCIONES
#Definición de constantes y funciones para el filtrado de los datos
DELITOS_PREFIJOS = [
    "ROBO DE VEHICULO DE SERVICIO PARTICULAR",
    "ROBO DE MOTOCICLETA",
    "ROBO DE VEHICULO DE PEDALES",
    "ROBO DE ACCESORIOS DE AUTO",
    "ROBO DE OBJETOS DEL INTERIOR DE UN VEHICULO",
]

NOMBRE_MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


@st.cache_data 
def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia la fecha y normaliza el texto de 'delito', creando columnas de tiempo."""
    df["fecha_hecho"] = pd.to_datetime(df["fecha_hecho"], errors="coerce") #Convierte la columna a datetime
    df = df.dropna(subset=["fecha_hecho"]) #Elimina filas con fechas inválidas

    if "delito" in df.columns:
        df["delito"] = df["delito"].str.upper()
    
    df["anio"] = df["fecha_hecho"].dt.year #Crea columna de año
    df["mes"] = df["fecha_hecho"].dt.month#Crea columna de mes

    return df


def calculate_delta( #Función principal apra calcular la variación mensual de incidentes
    df: pd.DataFrame, anio_filtro: int, mes_filtro: int, custom_filter: str | None = None,
) -> tuple[int, str, bool]:
    """
    Calcula incidentes del mes seleccionado completo vs. el mes anterior completo.
    Devuelve el conteo, el delta crudo, y si el cambio es positivo.
    """
    if df.empty or anio_filtro is None or mes_filtro is None:
        return 0, "0.0%", False

    df_filtered = df.copy()
    if custom_filter: #Filtro por un tipo de delito en específico
        df_filtered = df_filtered[df_filtered["delito"].str.contains(custom_filter, na=False)]
    #Conteo del periodo actual (mes seleccionado)
    current_period = df_filtered[(df_filtered["anio"] == anio_filtro) & (df_filtered["mes"] == mes_filtro)].shape[0]

    # Calcular mes anterior
    if mes_filtro == 1:
        previous_mes = 12
        previous_anio = anio_filtro - 1
    else: #Si no es enero, el mes anterior es el mes -1
        previous_mes = mes_filtro - 1
        previous_anio = anio_filtro
    #Conteo del periodo anterior (mes anterior)
    previous_period = df_filtered[(df_filtered["anio"] == previous_anio) & (df_filtered["mes"] == previous_mes)].shape[0]
#Caluclo de la varianza
    if previous_period > 0:
        delta_value = ((current_period - previous_period) / previous_period) * 100
        raw_delta_str = f"{delta_value:+.1f}%"
        is_positive = delta_value > 0
    elif current_period > 0:
        raw_delta_str = "Nuevos"
        is_positive = True
    else:
        raw_delta_str = "0.0%"
        is_positive = False
        
    return current_period, raw_delta_str, is_positive #Devuelve el conteo y si es positivo lo pinta verde 


#Función para generar los graficos de linea
def plot_delito_variation(
    df: pd.DataFrame, delito_prefix: str, color_hex: str = "#FF4B4B"
) -> None:
    """Gráfico de línea de la evolución diaria de un delito."""
    df_delito = df[df["delito"].str.contains(delito_prefix, na=False)]
    #Función altair para gráfico de línea
    df_daily = (
        df_delito.groupby(df_delito["fecha_hecho"].dt.date)
        .size()
        .reset_index(name="total")
    )
    df_daily.rename(columns={"fecha_hecho": "Fecha"}, inplace=True)

    if df_daily.empty:
        st.info(f"No hay datos para el delito: {delito_prefix}")
        return

    chart = (
        alt.Chart(df_daily)
        .mark_line(point=alt.OverlayMarkDef(color="white", size=40), color=color_hex)
        .encode(
            x=alt.X("Fecha:T", title="Fecha", axis=alt.Axis(format="%Y-%m-%d")),
            y=alt.Y("total:Q", title="Incidentes diarios"),
            tooltip=["Fecha:T", "total:Q"],
        )
        .properties(
            height=280,
            title=f"Evolución diaria de {delito_prefix}",
        )
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)


# ============================================================
# 2. CARGA Y PREPROCESAMIENTO
#Se define la carga y el preprocesamiento de los datos que se encuentra en el path de base de datos. 
try:
    df_raw = load_data(path="bases_de_datos/df_rt.csv") #carga el dataframe donde están los datos
    df = preprocess_data(df_raw)
except Exception as e:
    st.error(f" No se pudieron cargar o preprocesar los datos: {e}")
    st.stop()


if df.empty:
    st.error("El DataFrame está vacío después del preprocesamiento.")
    st.stop()
    
# Determinar el último mes/año disponible para el valor por defecto
if not df.empty:
    max_date = df["fecha_hecho"].max()
    default_anio = max_date.year
    default_mes = max_date.month
else:
    default_anio = 2024
    default_mes = 1


# ============================================================
# 3. Filtros para las metricas del inicio
#Aqui se muestran los filros en una select box de Año y Mes para controlar las tarjteas de kpi 
st.markdown("### Filtros de periodo para el resumen de incidentes")

col_f1, col_f2, _ = st.columns([1, 1, 2])

# 1. Filtro de Año
with col_f1:
    st.markdown('<div class="filtro-label">Año de referencia:</div>', unsafe_allow_html=True)
    
    anios_disponibles = sorted(df["anio"].unique())
    anio_sel_metricas = st.selectbox(
        "Año de referencia",
        options=anios_disponibles,
        index=anios_disponibles.index(default_anio) if default_anio in anios_disponibles else len(anios_disponibles) - 1,
        key="anio_metricas",
        label_visibility="collapsed"
    )

# 2. Filtro de Mes
with col_f2:
    st.markdown('<div class="filtro-label">Mes de referencia:</div>', unsafe_allow_html=True)
    #se crea un df temporal con la columna de año para filtrar los meses disponibles
    df_temp = df[df["anio"] == anio_sel_metricas] 
    meses_disp_num = sorted(df_temp["mes"].unique())
    meses_disp_nombre = [NOMBRE_MESES[m] for m in meses_disp_num if m in NOMBRE_MESES]
    #Se obtienen los meses disponibles en nombre y se selecciona el mes por defecto 
    default_mes_nombre = NOMBRE_MESES.get(default_mes, meses_disp_nombre[-1])
    default_index_mes = meses_disp_nombre.index(default_mes_nombre) if default_mes_nombre in meses_disp_nombre else len(meses_disp_nombre) - 1
    
    #Aqui se crea la select box para el mes
    nombre_mes_sel = st.selectbox(
        "Mes de referencia",
        options=meses_disp_nombre,
        index=default_index_mes,
        key="mes_metricas",
        label_visibility="collapsed"
    )
    #Convertimos el nombre del mes seleccionado a su valor numérico
    mes_sel_metricas = [k for k, v in NOMBRE_MESES.items() if v == nombre_mes_sel][0]


delito_filtro_total = None
    
etiqueta_mes = f"({nombre_mes_sel} {anio_sel_metricas})"

st.markdown("---")

# ============================================================
# 4. MÉTRICAS KPI CARDS
#Se crean las tarjetas de kpi con los datos filtrados, usando una estrucutra html para un diseño más libre
st.markdown(f"### Resumen de incidentes por mes {etiqueta_mes}")

cols_kpis_total = st.columns(5)  # Se crean 5 columnas para que el kpi tenga el mimsmo ancho  que los otros 5 kpi 

# KPI total
with cols_kpis_total[0]: 
    total_incidentes, delta_raw, is_positive = calculate_delta( #Calcula la variación a partir de los filtros seleccionados
        df, 
        anio_filtro=anio_sel_metricas,
        mes_filtro=mes_sel_metricas,
        custom_filter=delito_filtro_total
    )
    
    label_total = f"Total de incidentes" #Nombre que se va a mostrar en total incidentes
    delta_class = "delta-inverse" if is_positive else "delta-normal"  #Si es positivo es verde si es opuesto es rojo

    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">{label_total}</div>
            <div class="kpi-value">{total_incidentes:,.0f}</div>
            <div class="kpi-sub {delta_class}">
                {delta_raw} vs Mes Anterior
            </div>
        </div>
    """, unsafe_allow_html=True) #Renderiza el HTML de la tarjeta


st.markdown(f"### Robos relacionados con vehículos ") 
cols_delitos = st.columns(len(DELITOS_PREFIJOS)) #Se crean 5 columans para los 5 tipos de delitos. 

for i, delito in enumerate(DELITOS_PREFIJOS): #Se itera sobre la lista de los prefijos definidios anteriormente 
    col = cols_delitos[i]
    conteo, delta_raw, is_positive = calculate_delta( #Calcula la variación a partir de los filtros seleccionados
        df, 
        custom_filter=delito, 
        anio_filtro=anio_sel_metricas,
        mes_filtro=mes_sel_metricas,
    )
    
    # Si es positivo es verde si es opuesto es rojo
    delta_class = "delta-inverse" if is_positive else "delta-normal"
    
    with col: #Se pintan las tarjetas con la estructura html
        st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{delito.title()}</div>
                <div class="kpi-value">{conteo:,.0f}</div>
                <div class="kpi-sub {delta_class}">
                    {delta_raw} vs Mes Anterior
                </div>
            </div>
        """, unsafe_allow_html=True)

# ============================================================
# Tendencia diaria de robos de vehículos
#Se muestra la tendencia diaria de robos de vehículos con filtros para año, mes y tipo de robo
st.markdown("### Tendencia diaria de robos de vehículos")

df_vehiculos = df[df["delito"].str.contains("|".join(DELITOS_PREFIJOS), na=False)].copy()

if df_vehiculos.empty:
    st.info("No hay datos de esos tipos de robo en el dataset.")
else:
    col_filters, col_chart = st.columns([1, 3])

    with col_filters: #Filtros para la grafica de tendencia 
        st.markdown("#### Filtros")

        anios_disponibles_graf = sorted(df_vehiculos["anio"].unique())
        anio_seleccionado = st.selectbox("Año:", options=anios_disponibles_graf, key="graf_anio")

        meses_disponibles = sorted(
            df_vehiculos[df_vehiculos["anio"] == anio_seleccionado]["mes"].unique()
        )
        opciones_meses = [NOMBRE_MESES[m] for m in meses_disponibles if m in NOMBRE_MESES]
        nombre_mes_sel_graf = st.selectbox("Mes:", options=opciones_meses, key="graf_mes")

        mes_seleccionado = [k for k, v in NOMBRE_MESES.items() if v == nombre_mes_sel_graf][0]

        delito_seleccionado = st.selectbox( #Filtro por tipo de robo
            "Tipo de robo:",
            options=["Todos"] + DELITOS_PREFIJOS,
            key="graf_delito"
        )

    df_mes = df_vehiculos[ #Filtro por año y mes seleccionado
        (df_vehiculos["anio"] == anio_seleccionado)
        & (df_vehiculos["mes"] == mes_seleccionado)
    ].copy()

    if delito_seleccionado != "Todos": #Filtro para cuando se seleccione todos los  tipos de robo seleccionado
        df_mes = df_mes[df_mes["delito"].str.contains(delito_seleccionado, na=False)] 
        
    titulo_grafica = ""

    #Definición de la columna donde se va a pintar la grafica
    with col_chart:
        st.markdown(f"#### {titulo_grafica}")

        if df_mes.empty:
            st.info("No hay datos para el filtro seleccionado (año / mes / tipo de robo).")
        else: #Si hay datos, se pintan los datos de los datos encontrados en el df
            df_mes["Fecha"] = df_mes["fecha_hecho"].dt.date
            
            df_daily_tipo = (
                df_mes.groupby(["Fecha", "delito"])
                .size()
                .reset_index(name="total")
            )
            df_daily_tipo.rename(columns={"delito": "tipo_robo"}, inplace=True)
            #Función altair para gráfico de línea
            chart_evolucion = (
                alt.Chart(df_daily_tipo)
                .mark_line(point=True)
                .encode(
                    x=alt.X("Fecha:T", title="Fecha"), #Eje X - Fecha
                    y=alt.Y("total:Q", title="Incidentes diarios"),#Eje Y - Incidentes diarios
                    color=alt.Color("tipo_robo:N", title="Tipo de robo"), #Titulo de la leyenda
                    tooltip=["Fecha:T", "tipo_robo:N", "total:Q"], #Información al pasar el mouse
                )
                .properties(height=280)
                .configure_axis(
                    labelFontSize=tam_graficas,
                    titleFontSize=tam_graficas + 2,
                )
                .configure_legend(
                    labelFontSize=tam_graficas,
                    titleFontSize=tam_graficas + 2,
                )
                .interactive()
            )

            st.altair_chart(chart_evolucion, use_container_width=True)

# ============================================================
# Proporción CON/SIN violencia
#Analiza y visualiza los robos con y sin violencia encontrados en el dataset
st.markdown("### Proporción de robos con y sin violencia")
#Creamos una copia del df para no modificar el original
base_violencia = df.copy()

#Usamos los prefijos definidos para filtrar los robos relacionados con vehículos
base_violencia = base_violencia[
    base_violencia["delito"].str.contains("|".join(DELITOS_PREFIJOS), na=False)
].copy()

if base_violencia.empty:
    st.info("No hay datos para esos tipos de robo.")
else:#Si hay datos, se pintan los datos de los datos encontrados en el df
    col_filters, col_chart = st.columns([1, 3])
    #Filtro para poder seleccionar por tipo de robo 
    with col_filters:
        st.markdown("#### Filtros")
        opcion_delito = st.selectbox(
            "Filtrar por tipo de robo:",
            options=["Todos"] + DELITOS_PREFIJOS,
            key="filtro_violencia",
        )

    df_filtro = base_violencia.copy()
    #Si se selecciona opción para todos muestra todos los tipos de robo
    if opcion_delito != "Todos":
        df_filtro = df_filtro[df_filtro["delito"].str.contains(opcion_delito, na=False)]

    if df_filtro.empty:
        st.info("No hay datos para ese filtro de delito.")
    else: #Filtro para buscar tipo de robos si por violencia o sin violencia
        df_filtro["tipo_violencia"] = np.where(
            df_filtro["delito"].str.contains("CON VIOLENCIA", na=False),
            "CON VIOLENCIA",
            "SIN VIOLENCIA",
        )
        #Agrupamos y contamos los tipos que contengan violencia y los que no
        conteo_violencia = (
            df_filtro.groupby("tipo_violencia")
            .size()
            .reset_index(name="total")
        )

        if conteo_violencia.empty:
            st.info("No hay registros CON o SIN VIOLENCIA para este filtro.")
        else:
            #Pintamos la grafica de barras con los delitos violentos y no violentos. 
            with col_chart:
                barras = (
                    alt.Chart(conteo_violencia)
                    .mark_bar()
                    .encode(
                        x=alt.X( #Eje X - Tipo de violencia
                            "tipo_violencia:N",
                            title="",
                            axis=alt.Axis(
                                labelAngle=0,
                                labelFontSize=tam_graficas,
                                labelPadding=10,
                            ),
                        ),
                        y=alt.Y( #Eje Y - Número de incidentes
                            "total:Q",
                            title="Número de incidentes",
                        ),
                        color=alt.Color(
                            "tipo_violencia:N",
                            title="Tipo de incidente",
                            scale=alt.Scale(
                                domain=["CON VIOLENCIA", "SIN VIOLENCIA"],
                                range=["#FF4B4B", "#4CAF50"],
                            ),
                        ), #Cuanto pasamos el mouse por encima muestra la información
                        tooltip=["tipo_violencia:N", "total:Q"],
                    )
                    .properties(width=450, height=280)
                )

                etiquetas = ( #Etiquetas de los totales encima de las barras
                    alt.Chart(conteo_violencia)
                    .mark_text(dy=-8, fontSize=tam_graficas)
                    .encode(
                        x="tipo_violencia:N",
                        y="total:Q",
                        text=alt.Text("total:Q", format=","),
                    )
                )
                chart_barras = (
                    (barras + etiquetas)
                    .configure_axis(
                        labelFontSize=tam_graficas,
                        titleFontSize=tam_graficas + 2,
                    )
                    .configure_legend(
                        labelFontSize=tam_graficas,
                        titleFontSize=tam_graficas + 2,
                    )
                )

                st.altair_chart(chart_barras, use_container_width=True)

# ============================================================
# Alcaldías con más y menos robos
#Muestra el ranking de alcaldías con más y menos robos según los filtros seleccionados 
st.markdown("### Alcaldías con más y menos robos")

#Definimos la columna para verificar si existe alcaldia_hecho_N o alcaldia_hecho
col_alc = (
    "alcaldia_hecho_N" if "alcaldia_hecho_N" in df_vehiculos.columns else "alcaldia_hecho"
)

col_filters, col_charts = st.columns([1, 3])
 #Filtros para poder seleccionar por tipo de robo 
with col_filters:
    st.markdown("#### Filtros")
    delito_barras = st.selectbox(
        "Tipo de robo para el ranking de alcaldías:",
        options=["Todos"] + DELITOS_PREFIJOS,
        key="delito_barras",
    )
    
try: #Se filtran por año y mes seleccionado
    current_anio_rank = anio_seleccionado
    current_mes_rank = mes_seleccionado
except NameError:
    current_anio_rank = df["anio"].max()
    current_mes_rank = df[df["anio"] == current_anio_rank]["mes"].max()

#Se define el df top para poder hacer el ranking
df_top = df_vehiculos[
    (df_vehiculos["anio"] == current_anio_rank)
    & (df_vehiculos["mes"] == current_mes_rank)
].copy()

#Se pinta la grafica de barras para grafcarlo cuando tenga la opción de todos.
if delito_barras != "Todos":
    df_top = df_top[df_top["delito"].str.contains(delito_barras, na=False)]


if df_top.empty:
    st.info(f"No hay datos suficientes para este filtro (Año: {current_anio_rank} / Mes: {current_mes_rank} / Tipo de robo: {delito_barras}).")
else:
    conteo_alc = (
        df_top.groupby(col_alc)
        .size()
        .reset_index(name="total_delitos")
    )
    #Solo se muestra el top 5 de alcaldias con más y menos robos
    TOP_N = 5
    conteo_top = conteo_alc.sort_values("total_delitos", ascending=False).head(TOP_N) #Hacemos el conteo para poder asi definir el ranking TOP
    conteo_bottom = conteo_alc.sort_values("total_delitos", ascending=True).head(TOP_N)#Hacemos el conteo para poder asi definir el ranking Ultimos

    #Se pintan las gráficas de barras para el top y ultimo de alcaldias
    with col_charts:
        col_mas, col_menos = st.columns(2)
        #Gráfico para el top 
        chart_top = (
            alt.Chart(conteo_top)
            .mark_bar()
            .encode(
                x=alt.X("total_delitos:Q", title="Número de incidentes"), #Eje X - Número de incidentes
                y=alt.Y(f"{col_alc}:N", sort="-x", title="Alcaldía"), #Eje Y - Alcaldía
                tooltip=[f"{col_alc}:N", "total_delitos:Q"], #Información al pasar el mouse
            )
            .properties(height=260)
            .configure_axis(
                labelFontSize=tam_graficas,
                titleFontSize=tam_graficas + 2,
            )
        )
        #Grafico para el ultimo 
        chart_bottom = (
            alt.Chart(conteo_bottom)
            .mark_bar()
            .encode(
                x=alt.X("total_delitos:Q", title="Número de incidentes"),
                y=alt.Y(f"{col_alc}:N", sort="x", title="Alcaldía"),
                tooltip=[f"{col_alc}:N", "total_delitos:Q"],
            )
            .properties(height=260)
            .configure_axis(
                labelFontSize=tam_graficas,
                titleFontSize=tam_graficas + 2,
            )
        )

        with col_mas:
            st.markdown(f"#### Top {TOP_N} alcaldías con mayor cantidad de robos")
            st.altair_chart(chart_top, use_container_width=True)

        with col_menos:
            st.markdown(f"#### Top {TOP_N} alcaldías con menor cantidad de robos")
            st.altair_chart(chart_bottom, use_container_width=True)

# ============================================================
# Mapa de calor día / hora
st.markdown("### Mapa de calor día/hora robos")

#Personalización de títulos y etiquetas de la gráfica
TITULO_GRAFICA = ""
TIT_EJE_X = "Hora del día"
TIT_EJE_Y = "Día de la semana"
TIT_LEYENDA = "Incidentes"

#Definición de columnas para filtros y gráfica
col_filters, col_chart = st.columns([1, 3])

#Se crea la columna donde van a estar los filtros 
with col_filters:
    st.markdown("#### Filtros")
    delito_calor = st.selectbox(
        "Selecciona un tipo de robo para el mapa de calor:",
        options=DELITOS_PREFIJOS,
        key="delito_calor",
    )
    #Crear columnas de hora y día de la semana si no existen seguridad extra 
    if "hora_num" not in df_vehiculos.columns:
        df_vehiculos["hora_num"] = df_vehiculos["fecha_hecho"].dt.hour
    if "dia_semana" not in df_vehiculos.columns:
        df_vehiculos["dia_semana"] = df_vehiculos["fecha_hecho"].dt.day_name()
        dias_map = { #Mapeo de días al español
            'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
            'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sabado',
            'Sunday': 'Domingo'
        }
        df_vehiculos["dia_semana"] = df_vehiculos["dia_semana"].replace(dias_map)

#Filtro por el tipo de robo seleccionado 
df_heat = df_vehiculos[df_vehiculos["delito"].str.contains(delito_calor, na=False)].copy()
#Se agrupa por el dia de la semana y la hora del día para contar los incidentes
df_heat_mapa = (
    df_heat.groupby(["dia_semana", "hora_num"])
    .size()
    .reset_index(name="total")
)
#Ordenamos los días para que se muestren correctamente en la gráfica
orden_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sabado", "Domingo"]
#Sin no hay datos suficientes se muestra un mensaje
if df_heat_mapa.empty:
    st.info("No hay datos suficientes para este tipo de robo.")
else:
    #Columna donde esta definida la gráfica
    with col_chart:
        if TITULO_GRAFICA:
            st.markdown(f"#### {TITULO_GRAFICA}")
        #Función altair para gráfico de mapa de calor
        heatmap = (
            alt.Chart(df_heat_mapa)
            .mark_rect()
            .encode(
                x=alt.X( #Eje X - Hora del día
                    "hora_num:O",
                    title=TIT_EJE_X,
                    axis=alt.Axis(labelAngle=0),
                ),
                y=alt.Y( #Eje Y - dia de la semana
                    "dia_semana:O",
                    title=TIT_EJE_Y,
                    sort=orden_dias,
                    scale=alt.Scale(paddingInner=0.1, paddingOuter=0.25),
                ),
                color=alt.Color( #Para pintar los colores en el heat map 
                    "total:Q",
                    title=TIT_LEYENDA,
                    scale=alt.Scale(scheme="reds"),
                ),
                tooltip=["dia_semana:N", "hora_num:Q", "total:Q"],
            )
            .properties(
                height=240,
                padding={"top": 5, "right": 10, "left": 0, "bottom": 0},
            )
            .configure_axis(
                labelFontSize=tam_graficas,
                titleFontSize=tam_graficas + 2,
            )
            .configure_legend(
                labelFontSize=tam_graficas,
                titleFontSize=tam_graficas + 2,
            )
        )

        st.altair_chart(heatmap, use_container_width=True)

# ============================================================
# Mapa de robos de vehículos en CDMX
#Se pintan los puntos de la base de datos  para mostrar la concentración de robos alrededor de la ciudad de méxico 
st.markdown("### Mapa de robos de vehículos en CDMX")

col_filters, col_map = st.columns([1, 3])

with col_filters:
    st.markdown("#### Filtros")
    #Se definen para el mapa los filtros de año, mes, tipo de robo y tipo de vista
    anios_disponibles_map = sorted(df_vehiculos["anio"].unique())
    opciones_anio_map = ["Todos"] + list(anios_disponibles_map) 
    anio_mapa = st.selectbox("Año:", options=opciones_anio_map, key="anio_mapa")

    meses_disponibles_map = sorted(df_vehiculos["mes"].unique()) #Filtro para mes 
    opciones_meses_map = ["Todos"] + [NOMBRE_MESES[m] for m in meses_disponibles_map if m in NOMBRE_MESES]
    nombre_mes_map = st.selectbox("Mes:", options=opciones_meses_map, key="mes_mapa")

    delito_mapa = st.selectbox( #Filtro por tipo de robo 
        "Tipo de robo:",
        options=["Todos"] + DELITOS_PREFIJOS,
        key="delito_mapa",
    )

    vista_mapa = st.radio( #Filtro para el tipo de vista del mapa son 3
        "Tipo de vista:",
        options=["Puntos", "Mapa de calor", "Puntos y mapa de calor"],
        horizontal=False,
    )

df_mapa = df_vehiculos.copy()

#Aplicación de filtros por año , mes y delito del mapa
if anio_mapa != "Todos": #Si no es todos, filtra por el año seleccionado
    df_mapa = df_mapa[df_mapa["anio"] == anio_mapa]

if nombre_mes_map != "Todos": #Si no es todos, filtra por el mes seleccionado
    mes_num = [k for k, v in NOMBRE_MESES.items() if v == nombre_mes_map][0]
    df_mapa = df_mapa[df_mapa["mes"] == mes_num]

if delito_mapa != "Todos": #Si no es todos, filtra por el tipo de robo seleccionado
    df_mapa = df_mapa[df_mapa["delito"].str.contains(delito_mapa, na=False)]

df_mapa = df_mapa.dropna(subset=["latitud", "longitud"]) #Se eliminan los que no tienen latitud ni longitud

with col_map: #Columna donde se va a mapear el mapa
    if df_mapa.empty:
        st.info("No hay datos para el filtro seleccionado (año / mes / tipo de robo).")
    else:
        MAX_PUNTOS = 150 #Cantidad de puntos mostrados en el mapa 
        if len(df_mapa) > MAX_PUNTOS:
            df_mapa_sample = df_mapa.sample(MAX_PUNTOS, random_state=42)
        else:
            df_mapa_sample = df_mapa
        #Se calcula el centro del mapa basado en los puntos muestrados
        if not df_mapa_sample.empty:
            centro_lat = df_mapa_sample["latitud"].mean()
            centro_lon = df_mapa_sample["longitud"].mean()
        else:
            centro_lat, centro_lon = 19.4326, -99.1332 

        m = folium.Map( #Inicializa el mapa de folium 
            location=[centro_lat, centro_lon],
            zoom_start=11,
            tiles="CartoDB positron",
        )

        try: #Carga el archivo geojson con las delimimitaciones de las alcaldias
            with open("bases_de_datos/limite-de-las-alcaldias.json", "r", encoding="utf-8") as f:
                gj_alcaldias = json.load(f)

            folium.GeoJson( # Pinta las delimitaciones de las alcaldias en el mapa de la CDMX
                gj_alcaldias,
                name="Límites de alcaldías",
                style_function=lambda feature: {
                    "fillOpacity": 0,
                    "color": "#2b2b2b",
                    "weight": 1.5,
                },
            ).add_to(m)
        except FileNotFoundError:
            st.warning("No se encontró el archivo GeoJSON de alcaldías.")
        except Exception as e:
            st.warning(f"Error al cargar el GeoJSON: {e}")


        if vista_mapa in ["Puntos", "Puntos y mapa de calor"]:#Filtro para mostrar los puntos en el mapa
            for _, row in df_mapa_sample.iterrows():
                tipo = row.get("delito", "Sin tipo")
                anio = row.get("anio", row["fecha_hecho"].year)

                folium.CircleMarker(
                    location=[row["latitud"], row["longitud"]],
                    radius=3,
                    color="#FF4B4B",
                    fill=True,
                    fill_opacity=0.6,
                    popup=f"{tipo} - {row.get('alcaldia_hecho', '')}",
                    tooltip=folium.Tooltip(
                        f"{tipo} | Año: {anio}",
                        sticky=True,
                    ),
                ).add_to(m)

        if vista_mapa in ["Mapa de calor", "Puntos y mapa de calor"]: #Filtro para mostrar el mapa de calor 
            heat_data = df_mapa_sample[["latitud", "longitud"]].values.tolist()

            HeatMap( #Configuración del mapa de calor
                heat_data,
                radius=12,
                blur=18,
                max_zoom=13,
            ).add_to(m)

        folium.LayerControl().add_to(m) #Se añaden las capas 
        st_folium(m, width="100%", height=500) #Se muestran el mapa en streamlit