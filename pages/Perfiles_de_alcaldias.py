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

# Aplicar estilos globales
inject_custom_css(CUSTOM_THEME)

# Paleta de colores compartida (usada para mapear 0->Gris, 1->Azul Claro, etc.)
PALETA_IDS = {
    "Muy bajo":  "#808080",  # Cluster 0
    "Bajo":      "#57A5F8",  # Cluster 1
    "Medio":     "#041A88",  # Cluster 2
    "Alto":      "#0929C8",  # Cluster 3
    "Muy alto":  "#5255FC",  # Cluster 4
}

# Lista ordenada de colores
CLUSTER_COLORS = list(PALETA_IDS.values())

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

st.title("Análisis de Clustering: Segmentación Territorial")
st.markdown("---")

# ==========================================
# 3. CREACIÓN DE PESTAÑAS
# ==========================================
tab_alcaldias, tab_colonias = st.tabs(["Alcaldías", "Nivel Colonias"])

# ==============================================================================
# PESTAÑA 1: CLUSTERING DE ALCALDÍAS
# ==============================================================================
with tab_alcaldias:
    st.subheader("Perfiles de Alcaldías (Cámaras vs. Delitos vs. IDS)")
    
    # --- Carga de datos Alcaldías ---
    try:
        df_alc = pd.read_csv("bases_de_datos/clustering_alcaldias.csv")
        cent_alc = pd.read_csv("bases_de_datos/clustering_centroides.csv")
    except FileNotFoundError:
        st.error("⚠️ No se encontraron los archivos de Alcaldías en 'bases_de_datos/'.")
        st.stop()

    # Preprocesamiento Alcaldías
    tabla_clusters_alc = df_alc[["alcaldia", "cluster"]].sort_values("cluster").reset_index(drop=True)
    tabla_clusters_alc["Centro"] = "C" + tabla_clusters_alc["cluster"].astype(str)
    
    df_alc["cluster_str"] = df_alc["cluster"].astype(str)
    
    # Preprocesamiento Centroides
    cent_alc_proc = cent_alc.copy()
    cent_alc_proc["cluster"] = cent_alc_proc.index
    cent_alc_proc["cluster_str"] = cent_alc_proc["cluster"].astype(str)
    cent_alc_proc["label"] = "C" + cent_alc_proc["cluster_str"]

    # Dominio fijo para colores
    domain_alc = sorted(df_alc["cluster_str"].unique())
    K_OPTIMO_ALC = df_alc["cluster"].nunique()

    # --- Filtros 2D Alcaldías ---
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

    # --- Gráfica Altair Alcaldías ---
    base_alc = alt.Chart(df_p_alc).mark_circle(size=150, stroke="gray", strokeWidth=1).encode(
        x=alt.X("camaras_por_10k:Q", title="Cámaras por 10k"),
        y=alt.Y("Delitos_por_10k_hab:Q", title="Delitos por 10k Hab."),
        color=alt.Color(
            "cluster_str:N", 
            scale=alt.Scale(domain=domain_alc, range=CLUSTER_COLORS), 
            legend=None
        ),
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
    ).configure(
        background='white' # <--- FONDO BLANCO ALTAIR
    ).configure_axis(
        gridColor='#E0E0E0', labelColor='black', titleColor='black'
    ).configure_view(
        strokeWidth=0
    ).interactive()

    with col_c2d_alc:
        st.altair_chart(chart_alc, use_container_width=True)

    # --- Tabla Alcaldías ---
    with st.expander("Ver lista de Alcaldías por grupo"):
        st.dataframe(tabla_clusters_alc, use_container_width=True)

    # --- Vista 3D Alcaldías ---
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

    # FONDO BLANCO Y MEJORA VISUAL PLOTLY
    fig_alc.update_layout(
        height=600,
        template="plotly_white", # <--- TEMA CLARO
        scene=dict(
            xaxis_title="Cámaras/10k",
            yaxis_title="Delitos/10k",
            zaxis_title="IDS",
            bgcolor="white", # <--- FONDO ESCENA BLANCO
            xaxis=dict(backgroundcolor="white", gridcolor="#E0E0E0", showbackground=True, color="black"),
            yaxis=dict(backgroundcolor="white", gridcolor="#E0E0E0", showbackground=True, color="black"),
            zaxis=dict(backgroundcolor="white", gridcolor="#E0E0E0", showbackground=True, color="black"),
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        paper_bgcolor="white" # <--- FONDO PAPEL BLANCO
    )

    with col_c3d_alc:
        st.plotly_chart(fig_alc, use_container_width=True)


# ==============================================================================
# PESTAÑA 2: CLUSTERING DE COLONIAS
# ==============================================================================
with tab_colonias:
    st.subheader("Perfiles de Colonias (Escala Logarítmica)")
    

    X_VAR, Y_VAR, Z_VAR = "ue_por_1k_log", "delitos_por_1k_log", "alumbrado_por_1k_log"
    LABELS = {X_VAR: "UE (Log)", Y_VAR: "Delitos (Log)", Z_VAR: "Alumbrado (Log)"}

    # --- Carga de datos Colonias ---
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
        color=alt.Color(
            "cluster_str:N", 
            scale=alt.Scale(domain=domain_col, range=CLUSTER_COLORS), 
            legend=None
        ),
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
    ).configure(
        background='white' # <--- FONDO BLANCO ALTAIR
    ).configure_axis(
        gridColor='#E0E0E0', labelColor='black', titleColor='black'
    ).configure_view(
        strokeWidth=0
    ).interactive()

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

    # FONDO BLANCO Y MEJORA VISUAL PLOTLY
    fig_col.update_layout(
        height=600,
        template="plotly_white", # <--- TEMA CLARO
        scene=dict(
            xaxis_title=LABELS[X_VAR],
            yaxis_title=LABELS[Y_VAR],
            zaxis_title=LABELS[Z_VAR],
            bgcolor="white", # <--- FONDO ESCENA BLANCO
            xaxis=dict(backgroundcolor="white", gridcolor="#E0E0E0", showbackground=True, color="black"),
            yaxis=dict(backgroundcolor="white", gridcolor="#E0E0E0", showbackground=True, color="black"),
            zaxis=dict(backgroundcolor="white", gridcolor="#E0E0E0", showbackground=True, color="black"),
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        paper_bgcolor="white" # <--- FONDO PAPEL BLANCO
    )

    with col_c3d_col:
        st.plotly_chart(fig_col, use_container_width=True)