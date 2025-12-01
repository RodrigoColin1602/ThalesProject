import streamlit as st
from theme_config import inject_custom_css, CUSTOM_THEME


st.set_page_config(page_title="Login", layout="centered")


CARD_COLOR = "#465ED7"  #Color para el fondo de la tarjeta de login

#css
#Se define el bloque de css para estilizar la página de login
st.markdown(
    f"""
    <style>
    /* Fondo general de la app con imagen */
    .stApp {{
        background-image: url("https://media.licdn.com/dms/image/v2/C511BAQEIYltpmpE0Ig/company-background_10000/company-background_10000/0/1584477468102/aqua_mergers_acquisitions_cover?e=2147483647&v=beta&t=wAjE48JuiQtPMsGmZj_qlcOzf_1agpXHn0dkUR9GbVA");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    /* Empuja el contenido hacia abajo (ajusta el centrado vertical) */
    .block-container {{
        padding-top: 10rem; /* Ajuste para centrado */
    }}

    /* ========================================= */
    /* ESTILO DE LA TARJETA DE LOGIN */
    /* ========================================= */
    .login-card-container {{
        background-color: {CARD_COLOR} !important;
        padding: 30px 40px;
        border-radius: 15px;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4);
        max-width: 450px; /* Ancho máximo de la tarjeta */
    }}

    /* Título del login dentro de la tarjeta (ahora usa h2) */
    .login-card-container h2 {{
        color: white !important;
        text-align: center;
        margin-bottom: 20px;
        font-weight: 700;
        /* Sobreescribe el estilo predeterminado de Streamlit para el título */
    }}
    
    /* Etiquetas "Usuario" y "Contraseña" (se hacen blancas) */
    div[data-testid="stTextInput"] label {{
        color: white !important;
        font-weight: 600;
    }}

    /* Texto que se escribe dentro de los inputs (fondo blanco para inputs) */
    div[data-testid="stTextInput"] input, 
    div[data-testid="stTextInput"] div[data-testid="stInputContainer"] {{
        color: black !important;
        background-color: white !important;
        border-radius: 8px !important;
        border: none !important;
    }}
    
    /* Botón de Iniciar Sesión */
    .stButton>button:first-child {{
        background-color: #18c4d8 !important; /* Usamos un color de acento diferente */
        color: white !important;
        border: none !important;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 8px;
    }}

    </style>
    """,
    unsafe_allow_html=True
)

# Usuarios que se encuentran registrados 
USERS = {
    "usuario": {"password": "1234", "role": "viewer"},
    "policia": {"password": "abcd", "role": "analyst"},
}

# Inicializar sesión solo una vez
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["role"] = None

# Si ya hay sesión, redirigimos directo
if st.session_state["authenticated"]:
    role = st.session_state["role"]
    st.success(f"Ya tienes sesión iniciada (rol: {role.capitalize()})")

    if role == "viewer":
        st.switch_page("pages/Dashboard_usuario.py")
    elif role == "analyst":
        st.switch_page("pages/Dashboard_policia.py")

    st.stop()

#Se crea el conteneedor visual para la tarjeta de login 
st.markdown('<h2>Inicio de sesión</h2>', unsafe_allow_html=True)

username = st.text_input("Usuario:", key="login_user")
password = st.text_input("Contraseña:", type="password", key="login_pass")

#Si el usuario tienn las credenciales correctas, se inicia sesión
if st.button("Iniciar sesión", type="primary"):
    if username in USERS and USERS[username]["password"] == password:
        st.session_state["authenticated"] = True
        st.session_state["role"] = USERS[username]["role"]
        #Se da la bienvidada al usuario 
        st.success(f"Bienvenido, {username}  (rol: {st.session_state['role'].capitalize()})")

        role = st.session_state["role"]
        #Dependiendo del rol, se redirige a la página correspondiente
        if role == "viewer":
            st.switch_page("pages/Dashboard_usuario.py")
        elif role == "analyst":
            st.switch_page("pages/Dashboard_policia.py")
    else:
        st.error("Usuario o contraseña incorrectos.")

