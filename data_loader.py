import pandas as pd
import streamlit as st

@st.cache_data
def load_data(path="df_rt.csv", for_stmap=False):
    """
    Carga y limpia el dataset base de incidentes.
    
    Parámetros:
        path (str): ruta del archivo CSV.
        for_stmap (bool): si True, renombra las columnas para usar con st.map().
    
    Retorna:
        pd.DataFrame: datos listos para visualización.
    """
    try:
        # Leer el CSV
        df = pd.read_csv(path)
        #st.info(f"Archivo cargado: {len(df)} registros totales.")
        return df

    except Exception as e:
        st.error(f"Error al cargar el dataset: {e}")
        return pd.DataFrame()
