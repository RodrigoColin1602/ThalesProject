import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import numpy as np

# ===================================================================
# CONFIGURACIÓN DE LA PÁGINA

st.set_page_config(
    page_title="Inicio | Proyecto de Seguridad", # Titulo de la pestaña en el navegador 
    layout="wide", # Diseño de la página (wide = ancho completo)
    initial_sidebar_state="collapsed"  # Ocultamos la barra lateral en el inicio
)

# USUARIOs QUE SE ENCUENTRAN REGISTRADOS con credenciales 
USERS = {
    "usuario": {"password": "1234", "role": "viewer"},
    "policia": {"password": "abcd", "role": "analyst"},
}

# ESTADO DE SESIÓN
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["role"] = None

# ===================================================================
# IMÁGENES
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Thales_Logo.svg/968px-Thales_Logo.svg.png"
HERO_URL = "https://edicom.mx/.imaging/default/website/es_mx/blog/tipos-dashboards-ejemplos-kpis/image"

# ===================================================================
# ESTILO GLOBAL
#Se implementa el css para estilizar la página de inicio

st.markdown(
    f"""
    <style>
    .stApp {{
        background: 
            linear-gradient(rgba(255,255,255,0.75), rgba(255,255,255,0.75)),
            url('{HERO_URL}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: black !important;
    }}

    /* Botones turquesa tipo pastilla */
    div.stButton > button:first-child {{
        background-color: #18c4d8 !important;
        color: white !important;
        border: none !important;
        padding: 0.55rem 1.8rem;
        font-size: 1.05rem !important;
        border-radius: 999px;
        white-space: nowrap;
    }}
    div.stButton > button:first-child:hover {{
        background-color: #12a3b5 !important;
        background-color: #12a3b5 !important;
    }}

    /* Título del login */
    .login-title {{
        font-size: 2.3rem;
        font-weight: 800;
        color: #002b7f;
        margin-bottom: 1.2rem;
    }}

    /* INPUTS: color de texto y bordes redondeados */
    div[data-testid="stTextInput"] input {{
        background-color: #ffffff !important;
        color: #222222 !important;
        border-radius: 10px !important;
    }}

    /* Etiquetas Usuario / Contraseña en NEGRO */
    div[data-testid="stTextInput"] > label {{
        color: #000000 !important;
        font-weight: 600;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ===================================================================

#Se divide el encabezado en tres columnas 
col_logo, col_title, col_buttons = st.columns([1, 4, 3]) # Ajustamos el ancho de las columnas

with col_buttons:
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)

   #Columnas
    col_about, col_chatbot, col_login = st.columns([1, 1, 1]) 
    #Columna para el boton sobre nosotros 
    with col_about:
        if st.button("Sobre nosotros", key="about_btn"):
            st.switch_page("pages/Sobre_nosotros.py")
    #Columna para el boton de chatbot
    with col_chatbot:
        if st.button("Chatbot", key="chatbot_btn"):
             st.switch_page("pages/Chatbot.py") #
    #Columna para el boton de login
    with col_login:
        # Este botón ya no hace switch, solo queda como UI
        st.button("Iniciar Sesión", key="login_btn_header")

st.markdown("---")

hero_left, hero_right = st.columns([1, 1])

# -------------------------- LADO IZQUIERDO ---------------------------
with hero_left:
    st.markdown(
        f"""
        <h1 style="
            font-size: 6rem;
            color:#18c4d8;
            margin-bottom:0rem;
            line-height: 1.0;
        ">
            SENTINELA
        </h1>

        <div style="
            display:flex;
            align-items:center;
            gap:10px;
            margin-top:-1rem;
        ">
            <span style="font-size:1.8rem; color:#000275;">by</span>
            <img src="{LOGO_URL}" style="height:42px;">
        </div>

        <p style="color:#000275; font-weight:650; margin-top:3rem; font-size:1.25rem;">
            Inteligencia predictiva para tu ciudad: de reaccionar al crimen a anticiparlo.
        </p>

        <p style="max-width: 520px; text-align: justify; font-size:1.5rem; line-height:1.5;">
            Visualiza patrones de robos de motos, coches y objetos al interior de vehículos.
            <strong>Sentinela</strong> integra datos históricos, mapas y analítica predictiva
            para apoyar decisiones de autoridades y ciudadanía.
        </p>
        """,
        unsafe_allow_html=True,
    )

# LADO DERECHO 
with hero_right:
    # Título del login 
    st.markdown('<div class="login-title">Inicio de sesión</div>', unsafe_allow_html=True)

    # Si ya hay sesión iniciada, lo mostramos
    if st.session_state["authenticated"]:
        role = st.session_state["role"]
        st.success(f"Ya tienes sesión iniciada  (rol: {role.capitalize()})")
        # Si esta autenticado, redirigimos según el rol
        if role == "viewer":
             st.switch_page("pages/Dashboard_usuario.py")
        elif role == "analyst":
             st.switch_page("pages/Dashboard_policia.py")

    # Campos de usuario y contraseña
    username = st.text_input("Usuario:", key="home_user")
    password = st.text_input("Contraseña:", type="password", key="home_pass")

    #Boton iniciar sesión donde se verifica si las credenciales son correctas
    if st.button("Iniciar sesión", key="home_login_btn", type="primary"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state["authenticated"] = True
            st.session_state["role"] = USERS[username]["role"]

            role = st.session_state["role"]

            st.success(
                f"Bienvenido, {username} "
                f"(rol: {role.capitalize()})"
            )

            #Redirección según el rol
            if role == "viewer":
                st.switch_page("pages/Dashboard_usuario.py")
            elif role == "analyst":
                st.switch_page("pages/Dashboard_policia.py")

        else:
            st.error("Usuario o contraseña incorrectos. Inténtalo de nuevo.")


st.markdown("---")