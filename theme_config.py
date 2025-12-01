import streamlit as st

# Paleta para IDS / niveles de riesgo
PALETA_IDS = {
    "Muy bajo":      "#808080",
    "Bajo":          "#BBC6FC",
    "Medio":         "#637CF8",
    "Alto":          "#465ED7",
    "Muy alto":      "#000275",
    "SIN CLASIFICAR": "#FD0000",
}

# ===================================================================
#CONFIGURACIÓN CENTRAL DE COLORES Y ESTILOS

CUSTOM_THEME = {
    # Fondo general de la app
    "background_color": "#000000",
    # Color primario (botones, acentos)
    "primary_color": "#8A8A8A",
    # Fondo de tarjetas / contenedores
    "secondary_background_color": "#000000",
    # Color de texto
    "text_color": "#FFFFFF",
}


def inject_custom_css(theme):
    css = f"""
    <style>
    /* ===== Fondo general de la app ===== */
    .stApp {{
        background-color: {theme['background_color']};
        color: {theme['text_color']};
    }}
    
    /* ===== Botones ===== */
    .stButton>button {{
        background-color: {theme['primary_color']} !important;
        border-color: {theme['primary_color']} !important;
        color: white !important;
        border-radius: 5px;
        transition: 0.2s;
    }}
    .stButton>button:hover {{
        opacity: 0.9;
    }}

    /* ===== Contenedores / alerts ===== */
    div.stAlert, div[data-testid*="stContainer"], div[data-testid*="stVerticalBlock"] {{
        background-color: {theme['secondary_background_color']};
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }}
    
    /* ===== Títulos principales ===== */
    h1 {{
        color: {theme['primary_color']};
    }}

    /* Borde lateral de st.info con el color primario */
    .stAlert.info {{
        border-left: 5px solid {theme['primary_color']} !important;
    }}

    /* ===== Tarjetas para métricas (st.metric) ===== */
    div[data-testid="stMetric"] {{
        background-color: #000275;      /* azul fuerte */
        border-radius: 14px;
        padding: 10px 18px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }}

    /* Título de la métrica */
    div[data-testid="stMetric"] label {{
        color: #F0F2F6;
        font-weight: 600;
        font-size: 0.9rem;
    }}

    /* Valor principal */
    div[data-testid="stMetricValue"] {{
        color: #FFFFFF;
        font-weight: 700;
        font-size: 1.4rem;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
