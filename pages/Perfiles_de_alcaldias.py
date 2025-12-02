import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import altair as alt
from theme_config import inject_custom_css, CUSTOM_THEME

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Dashboard de Clustering: Alcaldías y Colonias",
    layout="wide"
)

# Aplicar estilos globales del tema
inject_custom_css(CUSTOM_THEME)

# --- FUNCIÓN CON ESTILOS EN LÍNEA (FORCE BLUE) ---
def mostrar_kpi(titulo, valor, comparativa, es_positivo=True):
    """
    Genera la tarjeta HTML con estilos en línea para asegurar 
    que se vea AZUL OSCURO (#000275) sin importar el tema.
    """
    # Colores definidos manualmente
    bg_color = "#000275"  # Azul oscuro
    text_color = "#FFFFFF" # Blanco
    badge_bg = "#4CAF50" if es_positivo else "#E53935" # Verde o Rojo
    
    html_card = f"""
    <div style="
        background-color: {bg_color};
        padding: 20px;
        border-radius: 12px;
        color: {text_color};
        font-family: sans-serif;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    ">
        <div style="font-size: 1.1rem; font-weight: 600; opacity: 0.9; margin-bottom: 8px;">
            {titulo}
        </div>
        <div style="font-size: 2.5rem; font-weight: 800; line-height: 1.1; margin-bottom: 12px;">
            {valor}
        </div>
        <div>
            <span style="
                background-color: {badge_bg};
                color: white;
                padding: 4px 12px;
                border-radius: 15px;
                font-size: 0.85rem;
                font-weight: bold;
                display: inline-block;
            ">
                {comparativa}
            </span>
        </div>
    </div>
    """
    st.markdown(html_card, unsafe_allow_html=True)

# ==========================================
# DATOS ESPECÍFICOS POR CLUSTER (NUEVO)
# ==========================================
DATOS_KPI_CLUSTERS = {
    0: {
        "titulo_panel": "Cluster 0: Zona de Alta Densidad y Actividad (Nivel 1)",
        "delitos": {"val": "73.7", "comp": "+66.3% vs Promedio", "pos": False}, 
        "ue":      {"val": "865",  "comp": "+26.9% vs Promedio", "pos": True},
        "alum":    {"val": "334",  "comp": "+43.0% vs Promedio", "pos": True},
        "hog":     {"val": "6,914","comp": "+39.6% vs Promedio", "pos": False}
    },
    1: {
        "titulo_panel": "Cluster 1: Zona Residencial Baja Densidad (Nivel 2)",
        "delitos": {"val": "18.2", "comp": "-58.8% vs Promedio", "pos": True},
        "ue":      {"val": "117",  "comp": "-82.8% vs Promedio", "pos": False},
        "alum":    {"val": "68",   "comp": "-70.8% vs Promedio", "pos": False},
        "hog":     {"val": "1,066","comp": "-78.5% vs Promedio", "pos": True}
    },
    2: {
        "titulo_panel": "Cluster 2: Zona de Transición / Mixta (Nivel 3)",
        "delitos": {"val": "13.4", "comp": "-69.7% vs Promedio", "pos": True},
        "ue":      {"val": "629",  "comp": "-7.7% vs Promedio",  "pos": False},
        "alum":    {"val": "154",  "comp": "-33.9% vs Promedio", "pos": False},
        "hog":     {"val": "3,638","comp": "-26.5% vs Promedio", "pos": True}
    }
}

# Paleta de colores compartida
PALETA_IDS = {
    "Muy bajo":  "#808080",  # Cluster 0
    "Bajo":      "#57A5F8",  # Cluster 1
    "Medio":     "#041A88",  # Cluster 2
    "Alto":      "#0929C8",  # Cluster 3
    "Muy alto":  "#5255FC",  # Cluster 4
}

CLUSTER_COLORS = list(PALETA_IDS.values())

#====================
# DICCIONARIO PARA ALCALDÍAS (5 CLUSTERS)
INFO_ALCALDIAS = {
    0: {"titulo": "Muy Bajo (C0)", "desc": "Zonas periféricas o de muy baja densidad comercial. Incidencia mínima.", "color": "#808080"},
    1: {"titulo": "Bajo (C1)", "desc": "Áreas residenciales tranquilas. Actividad comercial moderada.", "color": "#57A5F8"},
    2: {"titulo": "Medio (C2)", "desc": "Zonas de transición (mixtas). Equilibrio entre vivienda y comercio.", "color": "#041A88"},
    3: {"titulo": "Alto (C3)", "desc": "Corredores comerciales importantes. Alta afluencia y actividad económica.", "color": "#0929C8"},
    4: {"titulo": "Muy Alto (C4)", "desc": "Hotspots críticos. Máxima concentración de delitos y población flotante.", "color": "#5255FC"}
}

# --- DICCIONARIO PARA COLONIAS ---


# ==========================================
# 2. CONTROL DE SESIÓN
# ==========================================
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Acceso restringido. Por favor inicia sesión desde la página principal.")
    st.stop()

if st.session_state["role"] not in ["viewer", "analyst"]:
    st.error("No tienes permiso para acceder a este módulo.")
    st.stop()

# Barra superior de navegación
top_left, top_center, top_right = st.columns([1, 5, 1])
with top_left:
    if st.button("Regresar", use_container_width=True):
        st.switch_page("pages/Dashboard_usuario.py")
with top_right:
    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.clear()
        st.switch_page("pages/Login.py")

st.title("Análisis de agrupación por alcaldias y colonias")
st.markdown("---")

# ==========================================
# 3. CREACIÓN DE PESTAÑAS
tab_alcaldias, tab_colonias = st.tabs(["Alcaldías", "Nivel Colonias"])

def mostrar_tarjetas_informativas(info_dict):
    for i in range(len(info_dict)):
        info = info_dict.get(i)
        if info:
            st.markdown(f"""
            <div style="
                background-color: white;
                border: 1px solid #e0e0e0;
                border-top: 5px solid {info['color']};
                border-radius: 8px;
                padding: 15px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                color: black;
            ">
                <h5 style="color: {info['color']}; margin: 0 0 10px 0; font-weight: bold;">{info['titulo']}</h5>
                <p style="font-size: 13px; line-height: 1.4; color: #555;">{info['desc']}</p>
            </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# PESTAÑA 1: CLUSTERING DE ALCALDÍAS

with tab_alcaldias:
    st.subheader("Perfiles de Alcaldías (Cámaras vs. Delitos vs. IDS)")
    mostrar_tarjetas_informativas(INFO_ALCALDIAS)
    
    try:
        df_alc = pd.read_csv("bases_de_datos/clustering_alcaldias.csv")
        cent_alc = pd.read_csv("bases_de_datos/clustering_centroides.csv")
    except FileNotFoundError:
        st.error("⚠️ No se encontraron los archivos de Alcaldías en 'bases_de_datos/'.")
        st.stop()

    tabla_clusters_alc = df_alc[["alcaldia", "cluster"]].sort_values("cluster").reset_index(drop=True)
    tabla_clusters_alc["Centro"] = "C" + tabla_clusters_alc["cluster"].astype(str)
    
    df_alc["cluster_str"] = df_alc["cluster"].astype(str)
    
    cent_alc_proc = cent_alc.copy()
    cent_alc_proc["cluster"] = cent_alc_proc.index
    cent_alc_proc["cluster_str"] = cent_alc_proc["cluster"].astype(str)
    cent_alc_proc["label"] = "C" + cent_alc_proc["cluster_str"]

    domain_alc = sorted(df_alc["cluster_str"].unique())
    K_OPTIMO_ALC = df_alc["cluster"].nunique()

    col_f2d_alc, col_c2d_alc = st.columns([1, 3])
    with col_f2d_alc:
        st.markdown("#### Filtros (2D)")
        opts_alc = ["Todos"] + [f"C{c}" for c in sorted(df_alc["cluster"].unique())]
        sel_alc_2d = st.selectbox("Clúster:", options=opts_alc, key="sel_alc_2d")

    if sel_alc_2d == "Todos":
        df_p_alc = df_alc.copy()
        c_p_alc = cent_alc_proc.copy()
    else:
        n_c = int(sel_alc_2d.replace("C", ""))
        df_p_alc = df_alc[df_alc["cluster"] == n_c].copy()
        c_p_alc = cent_alc_proc[cent_alc_proc["cluster"] == n_c].copy()

    base_alc = alt.Chart(df_p_alc).mark_circle(size=150, stroke="gray", strokeWidth=1).encode(
        x=alt.X("camaras_por_10k:Q", title="Cámaras por 10k"),
        y=alt.Y("Delitos_por_10k_hab:Q", title="Delitos por 10k Hab."),
        color=alt.Color("cluster_str:N", scale=alt.Scale(domain=domain_alc, range=CLUSTER_COLORS), legend=None),
        tooltip=["alcaldia", "camaras_por_10k", "Delitos_por_10k_hab", "cluster_str"]
    )
    pt_cent_alc = alt.Chart(c_p_alc).mark_point(size=250, shape="X", color="black", filled=True).encode(
        x="camaras_por_10k:Q", y="Delitos_por_10k_hab:Q", tooltip=["label"]
    )
    lbl_cent_alc = alt.Chart(c_p_alc).mark_text(dy=-20, fontSize=14, fontWeight="bold", color="black").encode(
        x="camaras_por_10k:Q", y="Delitos_por_10k_hab:Q", text="label"
    )

    chart_alc = (base_alc + pt_cent_alc + lbl_cent_alc).properties(
        height=500, title=f"Alcaldías: K-Means ({K_OPTIMO_ALC} grupos)"
    ).configure(background='white').configure_axis(gridColor='#E0E0E0', labelColor='black', titleColor='black').configure_view(strokeWidth=0).interactive()

    with col_c2d_alc:
        st.altair_chart(chart_alc, use_container_width=True)

    with st.expander("Ver lista de Alcaldías por grupo"):
        st.dataframe(tabla_clusters_alc, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Vista 3D: Alcaldías")
    col_f3d_alc, col_c3d_alc = st.columns([1, 3])
    with col_f3d_alc:
        sel_alc_3d = st.selectbox("Resaltar Clúster 3D:", options=opts_alc, key="sel_alc_3d")

    if sel_alc_3d == "Todos":
        df_3d_a = df_alc.copy()
        cent_3d_a = cent_alc_proc.copy()
    else:
        n_c3 = int(sel_alc_3d.replace("C", ""))
        df_3d_a = df_alc[df_alc["cluster"] == n_c3].copy()
        cent_3d_a = cent_alc_proc[cent_alc_proc["cluster"] == n_c3].copy()

    fig_alc = go.Figure()
    color_map_3d_alc = {int(c): CLUSTER_COLORS[i] for i, c in enumerate(domain_alc) if i < len(CLUSTER_COLORS)}

    for c in sorted(df_3d_a["cluster"].unique()):
        sub = df_3d_a[df_3d_a["cluster"] == c]
        fig_alc.add_trace(go.Scatter3d(
            x=sub["camaras_por_10k"], y=sub["Delitos_por_10k_hab"], z=sub["IDS"],
            mode="markers",
            marker=dict(size=8, color=color_map_3d_alc.get(int(c), "#999"), opacity=0.9, line=dict(width=1, color='white')),
            name=f"C{c}", text=sub["alcaldia"],
            hovertemplate="<b>%{text}</b><br>Cam: %{x}<br>Del: %{y}<br>IDS: %{z}"
        ))

    fig_alc.add_trace(go.Scatter3d(
        x=cent_3d_a["camaras_por_10k"], y=cent_3d_a["Delitos_por_10k_hab"], z=cent_3d_a["IDS"],
        mode="markers+text", marker=dict(size=12, color="black", symbol="x"),
        text=cent_3d_a["label"], textposition="top center", name="Centros"
    ))
    fig_alc.update_layout(height=600, template="plotly_white", margin=dict(l=0, r=0, b=0, t=30), paper_bgcolor="white")
    with col_c3d_alc:
        st.plotly_chart(fig_alc, use_container_width=True)


# ==============================================================================
# PESTAÑA 2: CLUSTERING DE COLONIAS
with tab_colonias:
    st.subheader("Perfiles de Colonias ")
    
    X_VAR, Y_VAR, Z_VAR = "ue_por_1k_log", "delitos_por_1k_log", "alumbrado_por_1k_log"
    LABELS = {X_VAR: "UE (Log)", Y_VAR: "Delitos (Log)", Z_VAR: "Alumbrado (Log)"}

    try:
        df_col = pd.read_csv("bases_de_datos/resultados_colonias_clusters.csv")
        cent_col = pd.read_csv("bases_de_datos/centroides_valores_reales.csv")
    except FileNotFoundError:
        st.error("⚠️ Faltan los archivos CSV en 'bases_de_datos/'.")
        st.stop()

    if "cluster_kmeans" in df_col.columns:
        df_col.rename(columns={"cluster_kmeans": "cluster"}, inplace=True)
    
    df_col["cluster_str"] = df_col["cluster"].astype(str)
    cent_col["cluster_str"] = cent_col["cluster"].astype(str)
    cent_col["label"] = "C" + cent_col["cluster_str"]
    domain_col = sorted(df_col["cluster_str"].unique())

    # --- Filtros 2D Colonias ---
    col_f2d_col, col_c2d_col = st.columns([1, 3])
    with col_f2d_col:
        st.markdown("#### Filtros")
        opts_col = ["Todos"] + [f"C{c}" for c in sorted(df_col["cluster"].unique())]
        sel_col_2d = st.selectbox("Clúster:", options=opts_col, key="sel_col_log_2d")

    # ====================================================================
    # LÓGICA DINÁMICA DE TARJETAS AZULES 
    if sel_col_2d != "Todos":
        # Extraemos el número del cluster 
        n_cluster_sel = int(sel_col_2d.replace("C", ""))
        
        # Obtenemos los datos del diccionario
        kpi_data = DATOS_KPI_CLUSTERS.get(n_cluster_sel)

        if kpi_data:
            st.markdown(f"### 📊 {kpi_data['titulo_panel']}")
            
            k1, k2, k3, k4 = st.columns(4)
            
            with k1:
                mostrar_kpi("Delitos por km²", kpi_data['delitos']['val'], kpi_data['delitos']['comp'], kpi_data['delitos']['pos'])
            
            with k2:
                mostrar_kpi("Unid. Econ. / km²", kpi_data['ue']['val'], kpi_data['ue']['comp'], kpi_data['ue']['pos'])

            with k3:
                mostrar_kpi("Alumbrado / km²", kpi_data['alum']['val'], kpi_data['alum']['comp'], kpi_data['alum']['pos'])

            with k4:
                mostrar_kpi("Hogares / km²", kpi_data['hog']['val'], kpi_data['hog']['comp'], kpi_data['hog']['pos'])
            
            st.markdown("---")
    else:
        st.info("💡 Selecciona un Clúster específico (C0, C1, C2) en el filtro de arriba para ver las métricas detalladas.")
    # ====================================================================

    if sel_col_2d == "Todos":
        df_p_col = df_col.copy()
        c_p_col = cent_col.copy()
    else:
        n_cc = int(sel_col_2d.replace("C", ""))
        df_p_col = df_col[df_col["cluster"] == n_cc].copy()
        c_p_col = cent_col[cent_col["cluster"] == n_cc].copy()

    # --- Gráfica Altair Colonias ---
    base_col = alt.Chart(df_p_col).mark_circle(size=80, opacity=0.7).encode(
        x=alt.X(f"{X_VAR}:Q", title=LABELS[X_VAR]),
        y=alt.Y(f"{Y_VAR}:Q", title=LABELS[Y_VAR]),
        color=alt.Color("cluster_str:N", scale=alt.Scale(domain=domain_col, range=CLUSTER_COLORS), legend=None),
        tooltip=["colonia_hog", "alcaldia", f"{X_VAR}", f"{Y_VAR}", "cluster_str"]
    )
    pt_cent_col = alt.Chart(c_p_col).mark_point(size=250, shape="diamond", filled=True, color="black").encode(
        x=f"{X_VAR}:Q", y=f"{Y_VAR}:Q", tooltip=["label"]
    )
    lbl_cent_col = alt.Chart(c_p_col).mark_text(dy=-20, fontSize=14, fontWeight="bold", color="black").encode(
        x=f"{X_VAR}:Q", y=f"{Y_VAR}:Q", text="label"
    )
    chart_col = (base_col + pt_cent_col + lbl_cent_col).properties(
        height=500, title="Distribución de Clusters (Espacio Logarítmico)"
    ).configure(background='white').configure_axis(gridColor='#E0E0E0', labelColor='black', titleColor='black').configure_view(strokeWidth=0).interactive()

    with col_c2d_col:
        st.altair_chart(chart_col, use_container_width=True)

    # --- Vista 3D Colonias ---
    st.markdown("---")
    col_f3d_col, col_c3d_col = st.columns([1, 3])
    with col_f3d_col:
        st.markdown("#### Vista 3D")
        sel_col_3d = st.selectbox("Resaltar Clúster 3D:", options=opts_col, key="sel_col_log_3d")

    if sel_col_3d == "Todos":
        df_3d_c = df_col.copy()
        cent_3d_c = cent_col.copy()
    else:
        n_cc3 = int(sel_col_3d.replace("C", ""))
        df_3d_c = df_col[df_col["cluster"] == n_cc3].copy()
        cent_3d_c = cent_col[cent_col["cluster"] == n_cc3].copy()

    fig_col = go.Figure()
    color_map_3d_col = {int(c): CLUSTER_COLORS[i] for i, c in enumerate(domain_col) if i < len(CLUSTER_COLORS)}

    for c in sorted(df_3d_c["cluster"].unique()):
        sub_c = df_3d_c[df_3d_c["cluster"] == c]
        fig_col.add_trace(go.Scatter3d(
            x=sub_c[X_VAR], y=sub_c[Y_VAR], z=sub_c[Z_VAR],
            mode="markers",
            marker=dict(size=5, color=color_map_3d_col.get(int(c), "#999"), opacity=0.8, line=dict(width=0.5, color='white')),
            name=f"C{c}", text=sub_c["colonia_hog"],
            hovertemplate="<b>%{text}</b><br>X (Log): %{x:.2f}<br>Y (Log): %{y:.2f}<br>Z (Log): %{z:.2f}"
        ))

    fig_col.add_trace(go.Scatter3d(
        x=cent_3d_c[X_VAR], y=cent_3d_c[Y_VAR], z=cent_3d_c[Z_VAR],
        mode="markers+text", marker=dict(size=10, color="black", symbol="diamond"),
        text=cent_3d_c["label"], textposition="top center", name="Centros"
    ))
    fig_col.update_layout(height=600, template="plotly_white", margin=dict(l=0, r=0, b=0, t=30), paper_bgcolor="white", scene=dict(xaxis_title=LABELS[X_VAR], yaxis_title=LABELS[Y_VAR], zaxis_title=LABELS[Z_VAR], bgcolor="white", xaxis=dict(backgroundcolor="white", gridcolor="#E0E0E0"), yaxis=dict(backgroundcolor="white", gridcolor="#E0E0E0"), zaxis=dict(backgroundcolor="white", gridcolor="#E0E0E0")))

    with col_c3d_col:
        st.plotly_chart(fig_col, use_container_width=True)