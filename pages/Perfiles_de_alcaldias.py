import streamlit as st          
import pandas as pd             
import matplotlib.pyplot as plt 
import plotly.graph_objects as go
import seaborn as sns           
import altair as alt            
import numpy as np
from theme_config import inject_custom_css, CUSTOM_THEME

# SIEMPRE LO PRIMERO EN LA PÁGINA
st.set_page_config(
    page_title="Perfiles de alcaldías",
    layout="wide"
)

# Aplicar estilos globales
inject_custom_css(CUSTOM_THEME)

PALETA_IDS = {
    "Muy bajo":  "#808080",
    "Bajo":      "#BBC6FC",
    "Medio":     "#637CF8",
    "Alto":      "#0929C8",
    "Muy alto":  "#000275",
    "SIN CLASIFICAR":  "#95A5A6",
}

CLUSTER_COLORS = [
    PALETA_IDS["Muy bajo"],
    PALETA_IDS["Bajo"],
    PALETA_IDS["Medio"],
    PALETA_IDS["Alto"],
    PALETA_IDS["Muy alto"],
]

# Bloqueo de acceso si no hay sesión activa
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Acceso restringido. Por favor inicia sesión desde la página principal.")
    st.stop()

if st.session_state["role"] not in ["viewer"]:
    st.error("No tienes permiso para acceder a este módulo.")
    st.stop()

# ====== Barra superior de navegación (Regresar / Cerrar sesión) ======
top_left, top_center, top_right = st.columns([1, 5, 1])

with top_left:
    if st.button("Regresar", use_container_width=True):
        st.switch_page("pages/Dashboard_usuario.py")

with top_right:
    if st.button("Cerrar sesión", use_container_width=True):
        st.session_state.clear()
        st.switch_page("pages/Login.py")

st.markdown("---")

# ================== CARGA DE DATOS ==================
df_agrupado = pd.read_csv(
    "/Users/rodrigocolin/Desktop/Tec/Septimo semestre/Omar/Programación/ProyectoThales/bases_de_datos/clustering_alcaldias.csv"
)
df_centroids = pd.read_csv(
    "/Users/rodrigocolin/Desktop/Tec/Septimo semestre/Omar/Programación/ProyectoThales/bases_de_datos/clustering_centroides.csv"
)

# ================= TABLA RESUMEN: ALCALDÍA → CLÚSTER =================
tabla_clusters = (
    df_agrupado[["alcaldia", "cluster"]]
    .sort_values("cluster")
    .reset_index(drop=True)
)
tabla_clusters["Centro"] = "C" + tabla_clusters["cluster"].astype(str)

# Asegurar que cluster sea string
df_agrupado["cluster_str"] = df_agrupado["cluster"].astype(str)

# Número de clusters detectados (solo para el título)
K_OPTIMO = df_agrupado["cluster"].nunique()

centroids_alt = df_centroids.copy()
centroids_alt["cluster_str"] = centroids_alt.index.astype(str)
centroids_alt["label"] = "C" + centroids_alt["cluster_str"]

# =====================================================
#GRÁFICA 2D 

st.subheader("Agrupamiento de alcaldías")

col_filters_2d, col_chart_2d = st.columns([1, 3])

with col_filters_2d:
    st.markdown("#### Filtros (2D)")
    clusters_disponibles_2d = sorted(df_agrupado["cluster"].unique())
    opciones_clusters_2d = ["Todos"] + [f"C{c}" for c in clusters_disponibles_2d]

    cluster_2d_sel = st.selectbox(
        "Clúster para vista 2D:",
        options=opciones_clusters_2d,
        index=0,
        key="cluster_2d",
    )

# Dataframes SOLO para la vista 2D
if cluster_2d_sel == "Todos":
    df_plot_2d = df_agrupado.copy()
    centroids_2d = centroids_alt.copy()
    tabla_clusters_filtrada = tabla_clusters.copy()
else:
    num_cluster_2d = int(cluster_2d_sel.replace("C", ""))
    df_plot_2d = df_agrupado[df_agrupado["cluster"] == num_cluster_2d].copy()
    centroids_2d = centroids_alt[centroids_alt["cluster_str"] == str(num_cluster_2d)].copy()
    tabla_clusters_filtrada = tabla_clusters[tabla_clusters["cluster"] == num_cluster_2d].copy()

# Scatter de alcaldías coloreadas por clúster 2D
base_2d = (
    alt.Chart(df_plot_2d)
    .mark_circle(size=120, stroke="black", strokeWidth=1)
    .encode(
        x=alt.X(
            "camaras_por_10k:Q",
            title="Total cámaras instaladas"
        ),
        y=alt.Y(
            "Delitos_por_10k_hab:Q",
            title="Delitos por 10k Hab."
        ),
        color=alt.Color(
            "cluster_str:N",
            title="Clúster",
            scale=alt.Scale(range=CLUSTER_COLORS),
        ),
        tooltip=[
            "alcaldia:N",
            "camaras_por_10k:Q",
            "Delitos_por_10k_hab:Q",
            "cluster_str:N",
        ],
    )
)

#Puntos de centroides 
centroids_points_2d = (
    alt.Chart(centroids_2d)
    .mark_point(size=220, shape="X")
    .encode(
        x="camaras_por_10k:Q",
        y="Delitos_por_10k_hab:Q",
        color=alt.value("black"),
        tooltip=["label:N"],
    )
)

# 
centroids_labels_2d = (
    alt.Chart(centroids_2d)
    .mark_text(fontSize=14, fontWeight="bold", dy=-10)
    .encode(
        x="camaras_por_10k:Q",
        y="Delitos_por_10k_hab:Q",
        text="label:N",
    )
)

chart_clusters_2d = (
    base_2d + centroids_points_2d + centroids_labels_2d
).properties(
    width=700,
    height=500,
    title=f"K-Means con {K_OPTIMO} centros",
).configure_view(
    fill="white",
    strokeWidth=0
).configure(
    background="white"
).configure_axis(
    labelColor="black",
    titleColor="black",
    gridColor="#E0E0E0",
).configure_legend(
    labelColor="black",
    titleColor="black",
).configure_title(
    color="black"
)

with col_chart_2d:
    st.markdown("#### Distribución de alcaldías por cámaras y delitos")
    st.altair_chart(chart_clusters_2d, use_container_width=True, theme=None)

st.markdown("---")
st.subheader("Alcaldías por clúster")
st.dataframe(tabla_clusters_filtrada, use_container_width=True)

# =========================
# Vista 3D del clustering

st.markdown("---")
st.subheader("Vista 3D del agrupamiento de alcaldías")

# Variables de los ejes
X_COL = "camaras_por_10k"
Y_COL = "Delitos_por_10k_hab"
Z_COL = "IDS"  

# Paleta específica para la vista 3D
CLUSTER_COLORS_3D = {
    0: "#BBC6FC",  # C0
    1: "#637CF8",  # C1
    2: "#0929C8",  # C2
    3: "#000275",  # C3
    4: "#FF4B4B",  # C4 
}

col_filters_3d, col_chart_3d = st.columns([1, 3])

with col_filters_3d:
    st.markdown("#### Filtros (3D)")
    clusters_disponibles_3d = sorted(df_agrupado["cluster"].unique())
    opciones_centros_3d = ["Todos"] + [f"C{c}" for c in clusters_disponibles_3d]

    centro_3d_sel = st.selectbox(
        "Clúster para vista 3D:",
        options=opciones_centros_3d,
        index=0,
        key="centro_3d_sel",
    )


df_3d_base = df_agrupado.copy()
centroids_3d_base = centroids_alt.copy()

if centro_3d_sel == "Todos":
    df_3d = df_3d_base.copy()
    centroids_3d = centroids_3d_base.copy()
    tabla_clusters_3d = tabla_clusters.copy()
else:
    num_centro_3d = int(centro_3d_sel.replace("C", ""))
    df_3d = df_3d_base[df_3d_base["cluster"] == num_centro_3d].copy()
    centroids_3d = centroids_3d_base[centroids_3d_base["cluster_str"] == str(num_centro_3d)].copy()
    tabla_clusters_3d = tabla_clusters[tabla_clusters["cluster"] == num_centro_3d].copy()

if df_3d.empty:
    with col_chart_3d:
        st.info("No hay datos para este clúster en la vista 3D.")
else:
    # Rangos dinámicos con padding
    x_min, x_max = df_3d[X_COL].min(), df_3d[X_COL].max()
    y_min, y_max = df_3d[Y_COL].min(), df_3d[Y_COL].max()
    z_min, z_max = df_3d[Z_COL].min(), df_3d[Z_COL].max()

    def rango_con_padding(vmin, vmax, factor=0.2, minimo=1):
        rango = vmax - vmin
        pad = max(rango * factor, minimo) if rango != 0 else minimo
        return [vmin - pad, vmax + pad]

    x_range = rango_con_padding(x_min, x_max)
    y_range = rango_con_padding(y_min, y_max)
    z_range = rango_con_padding(z_min, z_max, factor=0.1, minimo=0.05)


    clusters_unicos_3d = sorted(df_3d["cluster"].unique())
    cluster_color_map_3d = {
        c: CLUSTER_COLORS_3D.get(c, "#BBBBBB")
        for c in clusters_unicos_3d
    }

    fig_3d = go.Figure()

    # Puntos de alcaldías
    for c in clusters_unicos_3d:
        df_c = df_3d[df_3d["cluster"] == c]

        if df_c.empty:
            continue

        fig_3d.add_trace(
            go.Scatter3d(
                x=df_c[X_COL],
                y=df_c[Y_COL],
                z=df_c[Z_COL],
                mode="markers",
                marker=dict(
                    size=7,
                    color=cluster_color_map_3d[c],
                    opacity=0.9,
                ),
                name=f"C{c}",
                text=df_c["alcaldia"],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    f"{X_COL}: " + "%{x:.2f}<br>"
                    f"{Y_COL}: " + "%{y:.2f}<br>"
                    f"{Z_COL}: " + "%{z:.2f}<extra></extra>"
                ),
            )
        )

    # Centroides
    if not centroids_3d.empty:
        fig_3d.add_trace(
            go.Scatter3d(
                x=centroids_3d[X_COL],
                y=centroids_3d[Y_COL],
                z=centroids_3d[Z_COL],
                mode="markers+text",
                marker=dict(
                    size=11,
                    color="black",
                    symbol="x",
                ),
                text=centroids_3d["label"],
                textposition="top center",
                name="Centroides",
                hovertemplate="<b>%{text}</b><extra></extra>",
            )
        )


    fig_3d.update_layout(
        title=dict(
            text=f"Clustering 3D de alcaldías (K = {K_OPTIMO})",
            font=dict(color="white", size=18),
            x=0.5
        ),
        height=600,
        margin=dict(l=0, r=0, t=60, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        scene=dict(
            bgcolor="#FFFFFF",
            aspectmode="cube",
            xaxis=dict(
                title="Total cámaras instaladas",
                backgroundcolor="#FFFFFF",
                gridcolor="#E0E0E0",
                showbackground=True,
                zerolinecolor="#BEBEBE",
                color="black",
                range=x_range,
            ),
            yaxis=dict(
                title="Delitos por 10k Hab.",
                backgroundcolor="#FFFFFF",
                gridcolor="#E0E0E0",
                showbackground=True,
                zerolinecolor="#BEBEBE",
                color="black",
                range=y_range,
            ),
            zaxis=dict(
                title=Z_COL,
                backgroundcolor="#FFFFFF",
                gridcolor="#E0E0E0",
                showbackground=True,
                zerolinecolor="#BEBEBE",
                color="black",
                range=z_range,
            ),
            camera=dict(
                eye=dict(x=1.6, y=1.6, z=1.2)
            ),
        ),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
        ),
    )

    with col_chart_3d:
        st.markdown("#### Distribución 3D de alcaldías por cámaras, delitos e IDS")
        st.plotly_chart(fig_3d, use_container_width=True)


st.markdown("---")
st.subheader("Alcaldías por grupos")
st.dataframe(tabla_clusters_3d, use_container_width=True)
