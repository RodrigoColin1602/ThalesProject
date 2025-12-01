import streamlit as st
from openai import OpenAI
import time
import json
import matplotlib.pyplot as plt
import os
import pandas as pd

CLIENT_API_KEY = st.secrets["openai_api_key"]

client = OpenAI(api_key=CLIENT_API_KEY)

# ============================================================
# 0. ENCABEZADO Y NAVEGACIÓN
# ============================================================

# Creamos dos columnas para alinear el título y los botones
col_title, col_btns = st.columns([8, 4])

with col_title:
    st.title("Chatbot Policial CDMX")

with col_btns:
    # Botón Dashboard Usuario (SOLO para 'viewer')
    if st.session_state.get("role") == "viewer":
        if st.button("Dashboard Usuario", key="go_to_dashboard"):
            # Asegúrate que el archivo sea pages/Dashboard_usuario.py
            st.switch_page("pages/Dashboard_usuario.py")

    # Botón Volver al Menú Principal (Para todos)
    if st.button("Volver al Menú Principal", key="go_to_menu"):
        # La forma correcta de navegar a la página raíz es solo el nombre del archivo
        st.switch_page("menu_inicio.py") 

# ================================
#   1. SUBIR DOCUMENTOS DESDE CARPETA
# ================================
folder_path =  "bases_de_datos/chatbot_files"  
if "vector_store_id" not in st.session_state:

    # Crear vector store vacío una vez
    vector_store = client.vector_stores.create(name="Chatbot_VectorStore")
    st.session_state.vector_store_id = vector_store.id

    # Recorrer todos los archivos de la carpeta
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Solo archivos reales
        if os.path.isfile(file_path):
            with open(file_path, "rb") as f:
                file_obj = client.files.create(
                    file=f,
                    purpose="assistants"
                )

            # Asociarlo al vector store
            client.vector_stores.files.create(
                vector_store_id=vector_store.id,
                file_id=file_obj.id
            )

    # Mensajes de estado de creación (comentados por limpieza)
    # st.success(f"Vector Store creado con archivos: {vector_store.id}")

else:
    pass
    # st.info(f"Vector Store ya existe: {st.session_state.vector_store_id}")


# ================================
#   1.1 CARGAR BASE_DE_DATOS.csv
# ================================
@st.cache_data
def cargar_base():
    # Ruta relativa correcta
    file_path = "archivos_chatbot/BASE_DE_DATOS.csv"

    # CAMBIO AQUÍ: Usamos "latin-1" para que lea bien los acentos de Excel
    df = pd.read_csv(file_path, sep=";", encoding="latin-1")

    # Por si ya quedó leída con el nombre raro, lo corregimos:
    if "ï»¿anio" in df.columns and "anio" not in df.columns:
        df = df.rename(columns={"ï»¿anio": "anio"})

    return df


### DETECTAR PREGUNTAS NÚMERICAS Y RESPUESTAS EN TEXTO NORMAL DEL CSV.

import re

MESES_MAP = {
    "ENERO": "ENERO",
    "FEBRERO": "FEBRERO",
    "MARZO": "MARZO",
    "ABRIL": "ABRIL",
    "MAYO": "MAYO",
    "JUNIO": "JUNIO",
    "JULIO": "JULIO",
    "AGOSTO": "AGOSTO",
    "SEPTIEMBRE": "SEPTIEMBRE",
    "SETIEMBRE": "SEPTIEMBRE",
    "OCTUBRE": "OCTUBRE",
    "NOVIEMBRE": "NOVIEMBRE",
    "DICIEMBRE": "DICIEMBRE",
}

DIAS_MAP = {
    "LUNES": "LUNES",
    "MARTES": "MARTES",
    "MIERCOLES": "MIÉRCOLES",
    "MIÉRCOLES": "MIÉRCOLES",
    "JUEVES": "JUEVES",
    "VIERNES": "VIERNES",
    "SABADO": "SÁBADO",
    "SÁBADO": "SÁBADO",
    "DOMINGO": "DOMINGO",
}

def normalizar_df_base(df: pd.DataFrame) -> pd.DataFrame:
    df_norm = df.copy()
    for col in ["alcaldia", "mes", "dia", "tipo_robo", "colonia"]:
        if col in df_norm.columns:
            df_norm[col] = df_norm[col].astype(str).str.strip().str.upper()
    return df_norm

df_norm_global = normalizar_df_base(df)


def responder_desde_csv(prompt: str, df_norm: pd.DataFrame) -> str | None:
    """
    Intenta interpretar preguntas numéricas sobre la base, usando combinaciones de:
    anio, mes, dia, hora, alcaldia, colonia, tipo_robo.
    Devuelve un texto con el conteo o None si no reconoce filtros.
    """

    texto = prompt.upper()

    filtros = {}

    # =============================
    # 1) AÑO
    # =============================
    match_anio = re.search(r"(20[0-9]{2})", texto)
    if match_anio and "anio" in df_norm.columns:
        filtros["anio"] = int(match_anio.group(1))

    # =============================
    # 2) MES (por nombre)
    # =============================
    if "mes" in df_norm.columns:
        for palabra, mes_val in MESES_MAP.items():
            if palabra in texto:
                filtros["mes"] = mes_val
                break

    # =============================
    # 3) DÍA DE LA SEMANA
    # =============================
    if "dia" in df_norm.columns:
        for palabra, dia_val in DIAS_MAP.items():
            if palabra in texto:
                filtros["dia"] = dia_val
                break

    # =============================
    # 4) HORA (muy simple: primer número 0-23)
    #    Podemos capturar cosas como "a las 8", "a las 20", "a las 13 horas"
    # =============================
    if "hora" in df_norm.columns:
        match_hora = re.search(r"\b([01]?[0-9]|2[0-3])\b", texto)
        if match_hora:
            filtros["hora"] = int(match_hora.group(1))

    # =============================
    # 5) ALCALDÍA (buscamos matches exactos dentro del texto)
    # =============================
    alcaldia_encontrada = None
    if "alcaldia" in df_norm.columns:
        alcaldias_posibles = df_norm["alcaldia"].dropna().unique().tolist()
        for alc in alcaldias_posibles:
            # Ej. "TLALPAN" en el texto
            if alc in texto:
                alcaldia_encontrada = alc
                break
        if alcaldia_encontrada:
            filtros["alcaldia"] = alcaldia_encontrada

    # =============================
    # 6) COLONIA (similar, pero ojo: puede ser muchas)
    #    Aquí hacemos algo muy simple: si la pregunta contiene el nombre exacto
    #    de alguna colonia.
    # =============================
    colonia_encontrada = None
    if "colonia" in df_norm.columns:
        colonias_posibles = df_norm["colonia"].dropna().unique().tolist()
        # Para no morir, limitamos a las primeras N colonias
        # (puedes ajustar este límite si tu dataset es gigante)
        for col in colonias_posibles[:2000]:
            if col in texto:
                colonia_encontrada = col
                break
        if colonia_encontrada:
            filtros["colonia"] = colonia_encontrada

    # =============================
    # 7) TIPO_ROBO (matching aproximado simple)
    #    Buscamos el tipo_robo cuyo texto sea más parecido a lo que aparece
    #    en la pregunta.
    # =============================
    tipo_robo_encontrado = None
    if "tipo_robo" in df_norm.columns:
        tipos_posibles = df_norm["tipo_robo"].dropna().unique().tolist()

        # Estrategia simple: si el texto contiene una gran parte del tipo_robo,
        # o si alguna palabra clave coincide.
        mejor_match = None
        mejor_len = 0
        for tipo in tipos_posibles:
            if not tipo:
                continue
            # Si la frase completa está en el texto
            if tipo in texto:
                if len(tipo) > mejor_len:
                    mejor_len = len(tipo)
                    mejor_match = tipo

        # Si no hubo match de frase completa, intentamos por palabras clave
        if mejor_match is None:
            palabras_texto = texto.split()
            for tipo in tipos_posibles:
                palabras_tipo = tipo.split()
                inter = set(palabras_texto) & set(palabras_tipo)
                # Si comparten al menos 2 palabras, lo tomamos
                if len(inter) >= 2 and len(" ".join(palabras_tipo)) > mejor_len:
                    mejor_len = len(" ".join(palabras_tipo))
                    mejor_match = tipo

        if mejor_match:
            tipo_robo_encontrado = mejor_match
            filtros["tipo_robo"] = tipo_robo_encontrado

    # Si no detectamos NINGÚN filtro, no intentamos nada
    if not filtros:
        return None

    # =============================
    # 8) APLICAR FILTROS AL DATAFRAME
    # =============================
    df_filtrado = df_norm.copy()

    if "anio" in filtros:
        df_filtrado = df_filtrado[df_filtrado["anio"] == filtros["anio"]]

    if "mes" in filtros:
        df_filtrado = df_filtrado[df_filtrado["mes"] == filtros["mes"]]

    if "dia" in filtros:
        # Puede haber tildes en el DF, ya usamos el valor canonizado (por ejemplo MIÉRCOLES)
        df_filtrado = df_filtrado[df_filtrado["dia"] == filtros["dia"]]

    if "hora" in filtros:
        df_filtrado = df_filtrado[df_filtrado["hora"] == filtros["hora"]]

    if "alcaldia" in filtros:
        df_filtrado = df_filtrado[df_filtrado["alcaldia"] == filtros["alcaldia"]]

    if "colonia" in filtros:
        df_filtrado = df_filtrado[df_filtrado["colonia"] == filtros["colonia"]]

    if "tipo_robo" in filtros:
        df_filtrado = df_filtrado[df_filtrado["tipo_robo"] == filtros["tipo_robo"]]

    if df_filtrado.empty:
        # No forzamos respuesta numérica si no hay datos
        return None

    conteo = len(df_filtrado)

    # =============================
    # 9) ARMAR RESPUESTA EN TEXTO
    # =============================
    partes = [f"Según BASE_DE_DATOS.csv, hubo {conteo} delitos"]

    # Agregar condiciones para explicar el filtro
    if "tipo_robo" in filtros:
        partes.append(f"del tipo '{filtros['tipo_robo'].title()}'")

    if "colonia" in filtros:
        partes.append(f"en la colonia {filtros['colonia'].title()}")

    if "alcaldia" in filtros:
        partes.append(f"en la alcaldía {filtros['alcaldia'].title()}")

    if "dia" in filtros:
        partes.append(f"en día {filtros['dia'].title()}")

    if "mes" in filtros:
        partes.append(f"en el mes de {filtros['mes'].title()}")

    if "anio" in filtros:
        partes.append(f"en el año {filtros['anio']}")

    if "hora" in filtros:
        partes.append(f"a la hora {filtros['hora']:02d}:00")

    respuesta = ", ".join(partes) + "."
    return respuesta


def es_pregunta_conteo_simple(prompt: str) -> bool:
    """
    Devuelve True si la pregunta parece pedir SOLO un conteo total,
    no un top/ranking/tabla.
    Ej: 'cuántos delitos hubo en Tlalpan en 2016'
    """
    p = prompt.lower()

    # Si menciona top, ranking, tabla, etc., NO es conteo simple
    palabras_top = ["top", "ranking", "rank", "tabla", "lista", "mayores", "más altos"]
    if any(w in p for w in palabras_top):
        return False

    # Si pregunta explícitamente cuántos / número / cantidad, lo tomamos como conteo simple
    palabras_conteo = ["cuantos", "cuántos", "numero de", "número de", "cantidad de"]
    return any(w in p for w in palabras_conteo)


# =======================================
# 2. CREAR ASSISTANT UNA SOLA VEZ
# =======================================
assistant = client.beta.assistants.create(
    name="Chatbot Policial CDMX",
    model="gpt-4o-mini",
    instructions="""
Eres un asistente experto en crimen vehicular en CDMX.

El sistema de backend tiene cargado un archivo BASE_DE_DATOS.csv con estas columnas:
- 'anio': año del incidente.
- 'mes': mes del incidente (texto).
- 'dia': día de la semana del incidente (texto).
- 'hora': hora del día en formato 0–23.
- 'alcaldia': alcaldía donde ocurrió el delito (16 alcaldías de la CDMX).
- 'colonia': colonia donde ocurrió el delito.
- 'tipo_robo': categoría del robo.

Tienes TRES modos de responder:

1) CUANDO el usuario pida UNA GRÁFICA:
   NO debes inventar números ni armar listas tú mismo.
   Devuelve SOLO un JSON que describa la consulta que el backend debe ejecutar.

   Formato del JSON para solicitudes de gráfica:

   {
     "graph_request": true,
     "query_type": "tipo_de_consulta",
     "chart_type": "line | bar | pie | hist",
     "filters": {
       "alcaldia": "TLALPAN",
       "tipo_robo": "ROBO DE ACCESORIOS DE AUTO",
       "anio": 2016,
       "mes": "Enero",
       "dia": "VIERNES"
     },
     "group_by": "hora",
     "title": "Título de la gráfica",
     "xlabel": "Etiqueta del eje X",
     "ylabel": "Etiqueta del eje Y"
   }

   Reglas:
   - "graph_request" debe ser true cuando el usuario pida una gráfica.
   - "query_type" debe ser una palabra corta que describa el tipo de consulta:
     - "delitos_por_hora"
     - "delitos_por_dia_semana"
     - "delitos_por_alcaldia"
     - "delitos_por_tipo_robo"
   - "chart_type" debe indicar el tipo de visualización cuando el usuario lo especifique:
     - Si pide "gráfico de líneas" → "line"
     - Si pide "gráfico de barras" → "bar"
     - Si pide "gráfico de pastel" o "pie chart" → "pie"
     - Si pide "distribución", "histograma" o "frecuencia" → "hist"
     - Si el usuario no especifica tipo, puedes usar "line" por defecto.
   - "filters" debe contener los filtros relevantes según la pregunta del usuario.
   - "group_by" es la columna por la que se va a agrupar en el backend.
   - NO devuelvas datos numéricos de la gráfica, solo la descripción de cómo obtenerlos.
   - NO incluyas ningún texto fuera del JSON.

2) CUANDO el usuario pida un RESUMEN NUMÉRICO o TOPs (pero NO gráfica),
   por ejemplo: "las 5 colonias con más robos en Tlalpan", "top 3 alcaldías con más delitos en 2018":
   devuelve SOLO un JSON con este formato:

   {
     "table_request": true,
     "operation": "top_k",
     "k": 5,
     "filters": {
       "alcaldia": "TLALPAN",
       "anio": 2018
     },
     "group_by": "colonia",
     "metric": "conteo_delitos",
     "title": "Top 5 colonias con más delitos en Tlalpan en 2018"
   }

   Reglas:
   - "table_request" debe ser true cuando NO se pida gráfica,
     pero sí un conteo, ranking, top, comparación numérica, etc.
   - "operation" de momento usa "top_k".
   - "k" es el número de filas que el backend debe devolver (por ejemplo, 3, 5, 10).
   - "filters" funciona igual que en el caso de gráfica.
   - "group_by" es la columna por la que se agrupará (ej. "alcaldia", "colonia", "tipo_robo").
   - "metric" por ahora siempre será "conteo_delitos".
   - NO incluyas ningún texto fuera del JSON.

3) CUANDO el usuario haga preguntas CUALITATIVAS o de contexto general,
   y no pida ni gráfica ni ranking numérico,
   responde en TEXTO NORMAL, usando:
   - Lo que conozcas del tema.
   - La información de los documentos del vector store (herramienta file_search).
""",
    tools=[{"type": "file_search"}]
)


st.session_state.assistant_id = assistant.id
# st.success(f"Assistant creado: {assistant.id}") # Comentado para limpiar UI

# 2. Agregar el vector store al assistant
client.beta.assistants.update(
    assistant_id=assistant.id,
    tool_resources={
        "file_search": {
            "vector_store_ids": [st.session_state.vector_store_id]
        }
    }
)

# st.success("Vector Store vinculado al Assistant correctamente.") # Comentado para limpiar UI

# ================================
#   3. CREAR THREAD UNA VEZ
# ================================
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

    # Esperar a que termine
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )

        if run_status.status == "completed":
            break
        time.sleep(1)

    # Obtener respuesta
    messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id
    )

    answer = messages.data[0].content[0].text.value

    # =========================================
    #   INTENTAR INTERPRETAR COMO JSON
    # =========================================
    data = None
    es_json = False

    try:
        data = json.loads(answer)
        es_json = isinstance(data, dict)
        # st.write("DEBUG JSON:", data)  # Descomenta si quieres ver el JSON
    except json.JSONDecodeError:
        es_json = False

    # -----------------------------------------
    #   MODO GRÁFICA
    # -----------------------------------------
    if es_json and data.get("graph_request"):
        # (mantén exactamente la lógica que ya tienes para gráficos,
        # incluyendo la parte de chart_type que añadiste antes)
        query_type = data.get("query_type")
        filters = data.get("filters", {})
        group_by = data.get("group_by")
        chart_type = data.get("chart_type", "line")

        df_filtrado = df.copy()

        # Normalizar texto
        for col in ["alcaldia", "mes", "dia", "tipo_robo"]:
            if col in df_filtrado.columns:
                df_filtrado[col] = (
                    df_filtrado[col].astype(str).str.strip().str.upper()
                )

        # Aplicar filtros (igual que antes)...
        if "alcaldia" in filters and "alcaldia" in df_filtrado.columns:
            valor = str(filters["alcaldia"]).strip().upper()
            df_filtrado = df_filtrado[df_filtrado["alcaldia"] == valor]

        if "anio" in filters and "anio" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["anio"] == int(filters["anio"])]

        if "mes" in filters and "mes" in df_filtrado.columns:
            mes_val = str(filters["mes"]).strip().upper()
            df_filtrado["mes"] = df_filtrado["mes"].astype(str).str.strip().str.upper()
            df_filtrado = df_filtrado[df_filtrado["mes"] == mes_val]

        if "dia" in filters and "dia" in df_filtrado.columns:
            dia_val = str(filters["dia"]).strip().upper()
            df_filtrado["dia"] = df_filtrado["dia"].astype(str).str.strip().str.upper()
            df_filtrado = df_filtrado[df_filtrado["dia"] == dia_val]

        if "tipo_robo" in filters and "tipo_robo" in df_filtrado.columns:
            tipo_val = str(filters["tipo_robo"]).strip().upper()
            df_filtrado["tipo_robo"] = (
                df_filtrado["tipo_robo"].astype(str).str.strip().str.upper()
            )
            df_filtrado = df_filtrado[df_filtrado["tipo_robo"] == tipo_val]

        if df_filtrado.empty:
            st.error("No se encontraron datos con esos filtros en BASE_DE_DATOS.csv")
        else:
            if group_by not in df_filtrado.columns:
                st.error(f"No existe la columna '{group_by}' en BASE_DE_DATOS.csv")
                st.write("Columnas disponibles:", df_filtrado.columns.tolist())
            else:
                conteo = (
                    df_filtrado
                    .groupby(group_by)
                    .size()
                    .reset_index(name="conteo")
                )

                # ordenar si aplica
                try:
                    conteo = conteo.sort_values(group_by)
                except Exception:
                    pass

                x = conteo[group_by]
                y = conteo["conteo"]

                fig, ax = plt.subplots(figsize=(8, 4))

                chart_type_lower = str(chart_type).lower()

                if chart_type_lower == "bar":
                    ax.bar(x, y)
                elif chart_type_lower in ["pie", "pastel"]:
                    ax.pie(y, labels=x, autopct="%1.1f%%")
                elif chart_type_lower in ["hist", "histograma", "distribution"]:
                    if group_by in df_filtrado.columns and pd.api.types.is_numeric_dtype(df_filtrado[group_by]):
                        ax.hist(df_filtrado[group_by], bins=10)
                    else:
                        ax.bar(x, y)
                else:
                    ax.plot(x, y, marker="o")

                if chart_type_lower not in ["pie", "pastel"]:
                    ax.set_xlabel(data.get("xlabel", group_by))
                    ax.set_ylabel(data.get("ylabel", "Número de delitos"))

                ax.set_title(data.get("title", "Gráfica"))
                ax.grid(True, linestyle="--", alpha=0.4)

                fig.tight_layout()
                st.pyplot(fig)


    # -----------------------------------------
    #   MODO TABLA (top_k, rankings, etc.)
    # -----------------------------------------
    elif es_json and data.get("table_request"):

        # --- NUEVO: si la PREGUNTA es un conteo simple, priorizamos el conteo directo desde CSV
        if es_pregunta_conteo_simple(prompt):
            respuesta_csv = responder_desde_csv(prompt, df_norm_global)
            if respuesta_csv is not None:
                st.chat_message("assistant").write(respuesta_csv)
                # saltamos el manejo de table_request porque el usuario pedía un conteo simple
                # y ya respondimos desde la base.
                # (No retornamos, solo evitamos dibujar la tabla)
                # Si quieres terminar aquí la ejecución, puedes usar `continue` dentro de un loop,
                # pero en este script de Streamlit simplemente evitamos el resto.
                # Para claridad, ponemos un flag:
                tabla_procesada = True
            else:
                tabla_procesada = False
        else:
            tabla_procesada = False

        if tabla_procesada:
            pass  # ya respondimos con conteo simple
        else:
            operation = data.get("operation")
            k = int(data.get("k", 5))  # default 5
            filters = data.get("filters", {})
            group_by = data.get("group_by")
            metric = data.get("metric", "conteo_delitos")

            df_filtrado = df.copy()

            # Normalizar texto
            for col in ["alcaldia", "mes", "dia", "tipo_robo"]:
                if col in df_filtrado.columns:
                    df_filtrado[col] = (
                        df_filtrado[col].astype(str).str.strip().str.upper()
                    )

            # Aplicar filtros (igual que antes)...
            if "alcaldia" in filters and "alcaldia" in df_filtrado.columns:
                valor = str(filters["alcaldia"]).strip().upper()
                df_filtrado = df_filtrado[df_filtrado["alcaldia"] == valor]

            if "anio" in filters and "anio" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["anio"] == int(filters["anio"])]

            if "mes" in filters and "mes" in df_filtrado.columns:
                mes_val = str(filters["mes"]).strip().upper()
                df_filtrado["mes"] = df_filtrado["mes"].astype(str).str.strip().str.upper()
                df_filtrado = df_filtrado[df_filtrado["mes"] == mes_val]

            if "dia" in filters and "dia" in df_filtrado.columns:
                dia_val = str(filters["dia"]).strip().upper()
                df_filtrado["dia"] = df_filtrado["dia"].astype(str).str.strip().str.upper()
                df_filtrado = df_filtrado[df_filtrado["dia"] == dia_val]

            if "tipo_robo" in filters and "tipo_robo" in df_filtrado.columns:
                tipo_val = str(filters["tipo_robo"]).strip().upper()
                df_filtrado["tipo_robo"] = (
                    df_filtrado["tipo_robo"].astype(str).str.strip().str.upper()
                )
                df_filtrado = df_filtrado[df_filtrado["tipo_robo"] == tipo_val]

            if df_filtrado.empty:
                st.error("No se encontraron datos con esos filtros en BASE_DE_DATOS.csv")
            else:
                if group_by not in df_filtrado.columns:
                    st.error(f"No existe la columna '{group_by}' en BASE_DE_DATOS.csv")
                    st.write("Columnas disponibles:", df_filtrado.columns.tolist())
                else:
                    conteo = (
                        df_filtrado
                        .groupby(group_by)
                        .size()
                        .reset_index(name="conteo")
                        .sort_values("conteo", ascending=False)
                    )

                    # aseguramos k razonable y mostramos el top_k
                    if k <= 0:
                        k = len(conteo)
                    k = min(k, len(conteo))

                    top_k = conteo.head(k).reset_index(drop=True)

                    st.subheader(data.get("title", "Resultados"))
                    st.dataframe(top_k)

                    # Resumen textual
                    resumen = []
                    for _, row in top_k.iterrows():
                        resumen.append(f"{row[group_by]}: {row['conteo']} delitos")
                    st.write("Resumen:")
                    st.write("\n".join(resumen))


    # -----------------------------------------
    #   MODO TEXTO NORMAL
    # -----------------------------------------
    else:
        # Solo intentamos usar el CSV para preguntas de CONTEO simple
        # (cuántos delitos...), NO para TOPs ni rankings.
        if es_pregunta_conteo_simple(prompt):
            respuesta_csv = responder_desde_csv(prompt, df_norm_global)
        else:
            respuesta_csv = None

        if respuesta_csv is not None:
            # Respuesta numérica basada en CSV
            st.chat_message("assistant").write(respuesta_csv)
        else:
            # Respuesta libre del assistant (texto normal o explicación)
            st.chat_message("assistant").write(answer)