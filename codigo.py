import streamlit as st
import fitz  # PyMuPDF
from docx import Document
from openai import OpenAI

# 1. Configuración de la interfaz
st.set_page_config(page_title="Ingeniería Eléctrica PRO", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
    .stChatFloatingInputContainer { bottom: 20px; }
    .stSidebar { background-color: #0e1117; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Asistente de Ingeniería Eléctrica")
st.caption("Especialista en Dimensionamiento, Normativa CNE/NEC y Análisis de Proyectos")

# 2. Barra lateral
with st.sidebar:
    st.header("🔑 Acceso")
    user_api_key = st.text_input("Introduce tu NVIDIA API Key:", type="password", placeholder="nvapi-...")
    
    st.divider()
    st.header("📂 Documentos")
    archivos = st.file_uploader("Sube manuales, tablas o ATS", accept_multiple_files=True, type=["pdf", "docx", "txt"])
    
    if st.button("🗑️ Limpiar historial"):
        st.session_state.messages = []
        st.rerun()

# 3. Cliente de IA
client = None
if user_api_key:
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=user_api_key)

# 4. Procesamiento de documentos
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
            st.error(f"Error en {arc.name}: {e}")
    return texto_total

contexto_documentos = leer_documentos(archivos) if archivos else ""

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Lógica de Chat Mejorada (Anti-Errores)
if prompt := st.chat_input("¿Qué cálculo o análisis realizamos?"):
    if not client:
        st.error("❌ Introduce tu API Key en la barra lateral.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            respuesta_placeholder = st.empty()
            full_response = ""
            
            # INSTRUCCIONES ESTRICTAS PARA EVITAR ERRORES MATEMÁTICOS
            prompt_maestro = f"""Eres un Ingeniero Eléctrico Senior experto en cálculos de potencia y conductores. 
            REGLAS CRÍTICAS:
            1. Para cálculos de caída de tensión (Delta V) en Monofásica o CC, usa siempre L*2 (ida y vuelta).
            2. Usa conductividad (gamma) del cobre = 56 (a 20°C) o 48 (a 70°C). Para Aluminio usa 35.
            3. Estructura tu respuesta así: 
               - DATOS IDENTIFICADOS
               - FÓRMULAS A USAR
               - DESARROLLO PASO A PASO
               - RESULTADO FINAL Y SECCIÓN COMERCIAL RECOMENDADA.
            4. Si el usuario subió documentos, dales prioridad absoluta sobre el conocimiento general.
            
            CONTEXTO DE ARCHIVOS: {contexto_documentos[:15000]}
            PREGUNTA: {prompt}"""

            try:
                stream = client.chat.completions.create(
                    model="meta/llama-3.1-405b-instruct",
                    messages=[{"role": "user", "content": prompt_maestro}],
                    stream=True
                )
                
                for chunk in stream:
                    if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                        content = chunk.choices[0].delta.content
                        if content:
                            full_response += content
                            respuesta_placeholder.markdown(full_response + "▌")
                
                respuesta_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                st.error(f"Error: {e}")
