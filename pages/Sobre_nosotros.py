import streamlit as st
import matplotlib.pyplot as plt
import altair as alt


# Configuración de la pagina 
st.set_page_config(
    page_title="Sobre nosotros | Sentinela",
    layout="wide",
    initial_sidebar_state="collapsed"
)

#Estilos
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f7f9fc;
        color: #222222;
    }

    /* Botones tipo pastilla turquesa */
    div.stButton > button:first-child {
        background-color: #18c4d8 !important;
        color: white !important;
        border: none !important;
        padding: 0.60rem 2.2rem;
        font-size: 1.05rem !important;
        border-radius: 999px;
        white-space: nowrap;
    }
    div.stButton > button:first-child:hover {
        background-color: #12a3b5 !important;
    }

    /* Tipografía general un poco más grande */
    p {
        font-size: 1.05rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ENCABEZADO: botones "Sobre nosotros" y "Iniciar sesión"
col_left, col_center, col_right = st.columns([1, 4, 2])

with col_right:
    top_col1, top_col2 = st.columns([1, 1])

    with top_col1:
        st.button("Sobre nosotros", key="btn_sobre_header")

    with top_col2:
        if st.button("Iniciar Sesión", key="btn_login_header"):
            st.switch_page("pages/Login.py")

st.markdown("---")

# Sobre nosotros    

left, right = st.columns([1.3, 1.7])

with left:
    st.markdown(
        """
        <h1 style="
            font-size: 3.2rem;
            color:#18c4d8;
            line-height: 1.05;
            margin-bottom: 1.5rem;
        ">
            SOBRE<br>NOSOTROS
        </h1>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <p style="text-align: justify;">
        Somos una plataforma de analítica urbana que integra datos geoespaciales para predecir 
        robos relacionados con vehículos. Nos enfocamos en cuatro tipos de delitos: robo de motos, 
        robo de autos, robo de bicicletas y robo de objetos al interior de vehículos particulares.
        </p>
        <p style="text-align: justify;">
        Adaptamos el alcance y el nivel de detalle según las necesidades de cada cliente. SENTINELA 
        genera mapas coropléticos con hotspots predictivos de las últimas 48 horas por zona de 
        patrullaje, además de mostrar tendencias delictivas y otros indicadores clave para la 
        gestión de nuevas estrategias innovadoras basadas en datos.
        </p>
        """,
        unsafe_allow_html=True,
    )

with right:
 
    spacer_left, cards_center, spacer_right = st.columns([0.15, 4.1, 0.75])

    with cards_center:
      
        st.markdown(
            "<div style='margin-top: 3.2rem;'></div>",
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns(3)

        card_style = """
            background-color:#e6eef7;
            border-radius:18px;
            padding:1.6rem 1.7rem;
            box-shadow:0 6px 18px rgba(0,0,0,0.10);
            height: 310px;
            display:flex;
            flex-direction:column;
            justify-content:flex-start;
        """

        
        with col1:
            st.markdown(
                f"""
                <div style="{card_style}">
                    <h3 style="margin:0 0 0.7rem 0; font-size:1.2rem; color:#2b3a67;">
                        Robo de Birruedas
                    </h3>
                    <p style="margin:0; font-size:1.03rem; line-height:1.55; text-align:justify;">
                        Incidentes relacionados a motocicletas y bicicletas, ya sea
                        estacionadas o en movimiento.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

       
        with col2:
            st.markdown(
                f"""
                <div style="{card_style}">
                    <h3 style="margin:0 0 0.7rem 0; font-size:1.2rem; color:#2b3a67;">
                        Robo a Interiores
                    </h3>
                    <p style="margin:0; font-size:1.03rem; line-height:1.55; text-align:justify;">
                        Robos relacionados a objetos al interior de un vehículo,
                        como electrónicos o pertenencias personales.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        
        with col3:
            st.markdown(
                f"""
                <div style="{card_style}">
                    <h3 style="margin:0 0 0.7rem 0; font-size:1.2rem; color:#2b3a67;">
                        Robo de Autos
                    </h3>
                    <p style="margin:0; font-size:1.03rem; line-height:1.55; text-align:justify;">
                        Robos a vehículos particulares, ya sea con o sin violencia.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ===================================================================
# Boton regresasar

st.write("") 
col_back, _ = st.columns([1, 5])

with col_back:
    if st.button("Volver al inicio", key="btn_volver_inicio"):
        st.switch_page("menu_inicio.py")
