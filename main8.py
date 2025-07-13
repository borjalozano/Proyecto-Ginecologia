import streamlit as st
from openai import OpenAI
from fpdf import FPDF
import base64
import fitz  # PyMuPDF
import re
from datetime import date
import yagmail
import traceback

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Asistente Ginecológico IA", page_icon="🩺")
st.title("🩺 Asistente clínico para ginecología")
st.markdown("Selecciona un modo de uso:")

if "historial" not in st.session_state:
    st.session_state.historial = []
if "chat_pdf" not in st.session_state:
    st.session_state.chat_pdf = []
if "pdf_texto" not in st.session_state:
    st.session_state.pdf_texto = ""

# ... (resto del código intacto hasta tabs)

# Tabs actualizadas

tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Triaje de síntomas",
    "🧾 Generador de recetas y órdenes",
    "📋 Resumen de exámenes previos",
    "💬 Chat sobre examen PDF"
])

# --- TAB 4: Chat sobre PDF ---
tab4.subheader("💬 Chat sobre informe médico en PDF")
archivo_pdf_chat = tab4.file_uploader("Sube un informe médico en PDF", type=["pdf"], key="chat_pdf_upload")

if archivo_pdf_chat:
    with st.spinner("Extrayendo texto del PDF..."):
        doc = fitz.open(stream=archivo_pdf_chat.read(), filetype="pdf")
        texto_extraido = ""
        for page in doc:
            texto_extraido += page.get_text()
        st.session_state.pdf_texto = texto_extraido
        tab4.success("Texto extraído con éxito")
        tab4.text_area("Contenido del documento", texto_extraido, height=200)

if st.session_state.pdf_texto:
    pregunta = tab4.text_input("Haz una pregunta sobre el documento:")
    if pregunta:
        with st.spinner("Consultando el documento..."):
            prompt_chat = f"""
Eres un asistente médico. A continuación, tienes un informe clínico en texto.
Responde únicamente en base a este contenido.

INFORME:
{st.session_state.pdf_texto}

PREGUNTA:
{pregunta}
"""
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt_chat}],
                temperature=0.2
            )
            respuesta = response.choices[0].message.content.strip()
            st.session_state.chat_pdf.append((pregunta, respuesta))

for q, r in st.session_state.chat_pdf[::-1]:
    with tab4.expander(f"❓ {q}"):
        tab4.markdown(r)