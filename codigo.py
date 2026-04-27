import streamlit as st
import fitz  # PyMuPDF
from docx import Document
from openai import OpenAI
import os

# 1. Configuración de la interfaz
st.set_page_config(page_title="Ingeniería Eléctrica AI", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    .stChatFloatingInputContainer { bottom: 20px; }
    .reportview-container { background: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Asistente")
st.caption("Cálculos, ATS, Reportes Económicos y Proyectos de Innovación")

# 2. Barra lateral para API y Archivos
with st.sidebar:
    st.header("⚙️ Configuración")
    # Tu llave que ya probamos que funciona
    api_key = st.text_input("NVIDIA API Key", value="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", type="password")
    
    st.divider()
    st.header("📂 Documentos de Referencia")
    archivos = st.file_uploader("Sube PDF, Word o TXT (Tablas, CNE, ATS)", 
                               accept_multiple_files=True, 
                               type=["pdf", "docx", "txt"])
    
    if st.button("🗑️ Limpiar historial"):
        st.session_state.messages = []
        st.rerun()

# 3. Inicializar el cliente de IA
client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)

# 4. Función para leer múltiples formatos
def leer_documentos(lista_archivos):
    texto_total = ""
    for arc in lista_archivos:
        ext = arc.name.split('.')[-1].lower()
        try:
            if ext == "pdf":
                doc = fitz.open(stream=arc.read(), filetype="pdf")
                for pagina in doc: texto_total += pagina.get_text()
            elif ext == "docx":
                doc = Document(arc)
                for para in doc.paragraphs: texto_total += para.text + "\n"
            elif ext == "txt":
                texto_total += str(arc.read().decode("utf-8"))
        except Exception as e:
            st.error(f"Error leyendo {arc.name}: {e}")
    return texto_total

# 5. Cargar contexto
contexto_documentos = ""
if archivos:
    contexto_documentos = leer_documentos(archivos)
    st.sidebar.success(f"📖 {len(archivos)} archivos cargados.")

# 6. Historial de Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes previos
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. Lógica de Chat con corrección de IndexError
if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        respuesta_placeholder = st.empty()
        full_response = ""
        
        # Construcción del prompt maestro
        prompt_final = f"""Actúa como un Ingeniero Electricista Senior. 
        CONTEXTO DE DOCUMENTOS SUBIDOS:
        {contexto_documentos[:15000]} 
        
        PREGUNTA DEL USUARIO:
        {prompt}"""

        try:
            stream = client.chat.completions.create(
                model="meta/llama-3.1-405b-instruct",
                messages=[{"role": "user", "content": prompt_final}],
                stream=True
            )
            
            for chunk in stream:
                # SOLUCIÓN AL INDEXERROR: Validar que existan choices
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    content = chunk.choices[0].delta.content
                    if content:
                        full_response += content
                        respuesta_placeholder.markdown(full_response + "▌")
            
            respuesta_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Hubo un error con la IA: {e}")
