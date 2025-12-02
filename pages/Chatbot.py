import streamlit as st
from openai import OpenAI
import time
import json
import matplotlib.pyplot as plt
import os
import pandas as pd
import re

# Configuración de la clave API
CLIENT_API_KEY = st.secrets["openai_api_key"]
client = OpenAI(api_key=CLIENT_API_KEY)

# ============================================================
# 0. ENCABEZADO Y NAVEGACIÓN
# ============================================================

# Creamos dos columnas para alinear el título y los botones
col_title, col_btns = st.columns([7, 5])

with col_title:
    st.title("Chatbot Policial CDMX")

with col_btns:
    # 1. Botón Dashboard Usuario (SOLO para 'viewer')
    if st.session_state.get("role") == "viewer":
        if st.button("Dashboard Usuario", key="go_to_dashboard_user"):
            st.switch_page("pages/Dashboard_usuario.py")

    # 2. Botón Dashboard Policia (SOLO para 'analyst') -> AGREGADO
    if st.session_state.get("role") == "analyst":
        if st.button("Regresar Dashboard Policia", key="go_to_dashboard_policia"):
            st.switch_page("pages/Dashboard_policia.py")

    # 3. Botón Volver al Menú Principal (Para todos)
    if st.button("Volver al Menú Principal", key="go_to_menu"):
        st.switch_page("menu_inicio.py") 

# ================================
#   1. SUBIR DOCUMENTOS DESDE CARPETA
# ================================
folder_path = "archivos_chatbot"  
if "vector_store_id" not in st.session_state:
    # Crear vector store vacío una vez
    vector_store = client.vector_stores.create(name="Chatbot_VectorStore")
    st.session_state.vector_store_id = vector_store.id

    # Recorrer todos los archivos de la carpeta
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                with open(file_path, "rb") as f:
                    file_obj = client.files.create(file=f, purpose="assistants")
                client.vector_stores.files.create(
                    vector_store_id=vector_store.id,
                    file_id=file_obj.id
                )
    else:
        # Solo advertencia si no existe carpeta, para no romper el script
        pass
else:
    pass


# ================================
#   1.1 CARGAR BASE_DE_DATOS.csv Y UTILIDADES
# ================================
@st.cache_data
def cargar_base():
    file_path = "archivos_chatbot/BASE_DE_DATOS.csv"
    try:
        df = pd.read_csv(file_path, sep=";", encoding="latin-1")
        if "ï»¿anio" in df.columns and "anio" not in df.columns:
            df = df.rename(columns={"ï»¿anio": "anio"})
        return df
    except FileNotFoundError:
        st.error("No se encontró 'archivos_chatbot/BASE_DE_DATOS.csv'.")
        return pd.DataFrame()

MESES_MAP = {
    "ENERO": "ENERO", "FEBRERO": "FEBRERO", "MARZO": "MARZO", "ABRIL": "ABRIL",
    "MAYO": "MAYO", "JUNIO": "JUNIO", "JULIO": "JULIO", "AGOSTO": "AGOSTO",
    "SEPTIEMBRE": "SEPTIEMBRE", "SETIEMBRE": "SEPTIEMBRE", "OCTUBRE": "OCTUBRE",
    "NOVIEMBRE": "NOVIEMBRE", "DICIEMBRE": "DICIEMBRE",
}

DIAS_MAP = {
    "LUNES": "LUNES", "MARTES": "MARTES", "MIERCOLES": "MIÉRCOLES",
    "MIÉRCOLES": "MIÉRCOLES", "JUEVES": "JUEVES", "VIERNES": "VIERNES",
    "SABADO": "SÁBADO", "SÁBADO": "SÁBADO", "DOMINGO": "DOMINGO",
}

def normalizar_df_base(df):
    if df.empty: return df
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    if 'fecha_hecho' in df.columns:
        df['fecha_hecho'] = pd.to_datetime(df['fecha_hecho'], errors='coerce')
    return df

def responder_desde_csv(prompt: str, df_norm: pd.DataFrame) -> str | None:
    if df_norm.empty: return None
    texto = prompt.upper()
    filtros = {}

    match_anio = re.search(r"(20[0-9]{2})", texto)
    if match_anio and "anio" in df_norm.columns: filtros["anio"] = int(match_anio.group(1))

    if "mes" in df_norm.columns:
        for palabra, mes_val in MESES_MAP.items():
            if palabra in texto:
                filtros["mes"] = mes_val
                break

    if "dia" in df_norm.columns:
        for palabra, dia_val in DIAS_MAP.items():
            if palabra in texto:
                filtros["dia"] = dia_val
                break

    if "hora" in df_norm.columns:
        match_hora = re.search(r"\b([01]?[0-9]|2[0-3])\b", texto)
        if match_hora: filtros["hora"] = int(match_hora.group(1))

    alcaldia_encontrada = None
    if "alcaldia" in df_norm.columns:
        alcaldias_posibles = df_norm["alcaldia"].dropna().unique().tolist()
        for alc in alcaldias_posibles:
            if str(alc) in texto:
                alcaldia_encontrada = alc
                break
        if alcaldia_encontrada: filtros["alcaldia"] = alcaldia_encontrada

    colonia_encontrada = None
    if "colonia" in df_norm.columns:
        colonias_posibles = df_norm["colonia"].dropna().unique().tolist()
        for col in colonias_posibles[:2000]:
            if str(col) in texto:
                colonia_encontrada = col
                break
        if colonia_encontrada: filtros["colonia"] = colonia_encontrada

    tipo_robo_encontrado = None
    if "tipo_robo" in df_norm.columns:
        tipos_posibles = df_norm["tipo_robo"].dropna().unique().tolist()
        mejor_match = None
        mejor_len = 0
        for tipo in tipos_posibles:
            if not isinstance(tipo, str): continue
            if tipo in texto:
                if len(tipo) > mejor_len:
                    mejor_len = len(tipo)
                    mejor_match = tipo
        if mejor_match: filtros["tipo_robo"] = mejor_match

    if not filtros: return None

    df_filtrado = df_norm.copy()
    for col, val in filtros.items():
        if col in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado[col] == val]

    if df_filtrado.empty: return None

    conteo = len(df_filtrado)
    partes = [f"Según BASE_DE_DATOS.csv, hubo {conteo} delitos"]
    
    # Construir frase
    if "tipo_robo" in filtros: partes.append(f"del tipo '{filtros['tipo_robo'].title()}'")
    if "colonia" in filtros: partes.append(f"en la colonia {filtros['colonia'].title()}")
    if "alcaldia" in filtros: partes.append(f"en la alcaldía {filtros['alcaldia'].title()}")
    if "dia" in filtros: partes.append(f"en día {filtros['dia'].title()}")
    if "mes" in filtros: partes.append(f"en el mes de {filtros['mes'].title()}")
    if "anio" in filtros: partes.append(f"en el año {filtros['anio']}")
    if "hora" in filtros: partes.append(f"a la hora {filtros['hora']:02d}:00")

    respuesta = ", ".join(partes) + "."
    return respuesta

def es_pregunta_conteo_simple(prompt: str) -> bool:
    p = prompt.lower()
    palabras_top = ["top", "ranking", "rank", "tabla", "lista", "mayores", "más altos"]
    if any(w in p for w in palabras_top): return False
    palabras_conteo = ["cuantos", "cuántos", "numero de", "número de", "cantidad de"]
    return any(w in p for w in palabras_conteo)

# =======================================
# 2. INICIALIZAR DATOS Y ASISTENTE
# =======================================

# CARGAMOS LOS DATAFRAMES GLOBALES (Importante para que funcione el chat)
df = cargar_base()
df_norm_global = normalizar_df_base(df.copy())

if "assistant_id" not in st.session_state:
    assistant = client.beta.assistants.create(
        name="Chatbot Policial CDMX",
        model="gpt-4o-mini",
        instructions="""
Eres un asistente experto en crimen vehicular en CDMX.

El sistema de backend tiene cargado un archivo BASE_DE_DATOS.csv con estas columnas:
- 'anio', 'mes', 'dia', 'hora', 'alcaldia', 'colonia', 'tipo_robo'.

Tienes TRES modos de responder:

1) CUANDO el usuario pida UNA GRÁFICA:
   Devuelve SOLO un JSON:
   {
     "graph_request": true,
     "query_type": "...",
     "chart_type": "line | bar | pie | hist",
     "filters": { ... },
     "group_by": "hora",
     "title": "...",
     "xlabel": "...",
     "ylabel": "..."
   }

2) CUANDO el usuario pida un RESUMEN NUMÉRICO o TOPs (pero NO gráfica):
   Devuelve SOLO un JSON:
   {
     "table_request": true,
     "operation": "top_k",
     "k": 5,
     "filters": { ... },
     "group_by": "colonia",
     "metric": "conteo_delitos",
     "title": "..."
   }

3) CUANDO el usuario haga preguntas CUALITATIVAS o de contexto general:
   Responde en TEXTO NORMAL usando file_search.
""",
        tools=[{"type": "file_search"}]
    )
    st.session_state.assistant_id = assistant.id
    
    client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [st.session_state.vector_store_id]}}
    )

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id


# ================================
#   4. CHAT DE USUARIO
# ================================
prompt = st.chat_input("Haz una pregunta sobre el proyecto o la CDMX...")

if prompt:
    st.chat_message("user").write(prompt)

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )

    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=st.session_state.assistant_id
    )

    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )
        if run_status.status == "completed":
            break
        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
    answer = messages.data[0].content[0].text.value

    # =========================================
    #   INTENTAR INTERPRETAR COMO JSON
    # =========================================
    data = None
    es_json = False
    try:
        data = json.loads(answer)
        es_json = isinstance(data, dict)
    except json.JSONDecodeError:
        es_json = False

    # -----------------------------------------
    #   MODO GRÁFICA
    # -----------------------------------------
    if es_json and data.get("graph_request"):
        query_type = data.get("query_type")
        filters = data.get("filters", {})
        group_by = data.get("group_by")
        chart_type = data.get("chart_type", "line")

        df_filtrado = df.copy()

        # Normalizar texto para filtrado
        for col in ["alcaldia", "mes", "dia", "tipo_robo"]:
            if col in df_filtrado.columns:
                df_filtrado[col] = df_filtrado[col].astype(str).str.strip().str.upper()

        # Aplicar filtros
        if "alcaldia" in filters:
            df_filtrado = df_filtrado[df_filtrado["alcaldia"] == str(filters["alcaldia"]).upper()]
        if "anio" in filters:
            df_filtrado = df_filtrado[df_filtrado["anio"] == int(filters["anio"])]
        if "mes" in filters:
            df_filtrado = df_filtrado[df_filtrado["mes"] == str(filters["mes"]).upper()]
        if "dia" in filters:
            df_filtrado = df_filtrado[df_filtrado["dia"] == str(filters["dia"]).upper()]
        if "tipo_robo" in filters:
            df_filtrado = df_filtrado[df_filtrado["tipo_robo"] == str(filters["tipo_robo"]).upper()]

        if df_filtrado.empty:
            st.error("No se encontraron datos con esos filtros.")
        else:
            if group_by in df_filtrado.columns:
                conteo = df_filtrado.groupby(group_by).size().reset_index(name="conteo")
                try:
                    conteo = conteo.sort_values(group_by)
                except: pass

                x = conteo[group_by]
                y = conteo["conteo"]
                fig, ax = plt.subplots(figsize=(8, 4))

                chart_type_lower = str(chart_type).lower()
                if chart_type_lower == "bar":
                    ax.bar(x, y)
                elif chart_type_lower in ["pie", "pastel"]:
                    ax.pie(y, labels=x, autopct="%1.1f%%")
                else:
                    ax.plot(x, y, marker="o")

                if chart_type_lower not in ["pie", "pastel"]:
                    ax.set_xlabel(data.get("xlabel", group_by))
                    ax.set_ylabel(data.get("ylabel", "Número de delitos"))
                
                ax.set_title(data.get("title", "Gráfica"))
                ax.grid(True, linestyle="--", alpha=0.4)
                st.pyplot(fig)
            else:
                st.error(f"Columna {group_by} no disponible.")

    # -----------------------------------------
    #   MODO TABLA (TOP K)
    # -----------------------------------------
    elif es_json and data.get("table_request"):
        # Prioridad a conteo simple directo
        if es_pregunta_conteo_simple(prompt):
            respuesta_csv = responder_desde_csv(prompt, df_norm_global)
            if respuesta_csv:
                st.chat_message("assistant").write(respuesta_csv)
            else:
                st.chat_message("assistant").write("No encontré datos exactos en el CSV.")
        else:
            k = int(data.get("k", 5))
            filters = data.get("filters", {})
            group_by = data.get("group_by")
            
            df_filtrado = df.copy()
            for col in ["alcaldia", "mes", "dia", "tipo_robo"]:
                if col in df_filtrado.columns:
                    df_filtrado[col] = df_filtrado[col].astype(str).str.strip().str.upper()

            # Aplicar filtros (mismo bloque abreviado)
            if "alcaldia" in filters: df_filtrado = df_filtrado[df_filtrado["alcaldia"] == str(filters["alcaldia"]).upper()]
            if "anio" in filters: df_filtrado = df_filtrado[df_filtrado["anio"] == int(filters["anio"])]
            
            if df_filtrado.empty:
                st.info("Sin datos para esta tabla.")
            else:
                conteo = df_filtrado.groupby(group_by).size().reset_index(name="conteo").sort_values("conteo", ascending=False)
                st.subheader(data.get("title", "Resultados"))
                st.dataframe(conteo.head(k))

    # -----------------------------------------
    #   MODO TEXTO NORMAL
    # -----------------------------------------
    else:
        if es_pregunta_conteo_simple(prompt):
            respuesta_csv = responder_desde_csv(prompt, df_norm_global)
            if respuesta_csv:
                st.chat_message("assistant").write(respuesta_csv)
            else:
                st.chat_message("assistant").write(answer)
        else:
            st.chat_message("assistant").write(answer)