import streamlit as st
from openai import OpenAI
from fpdf import FPDF
import base64
import fitz  # PyMuPDF
import re
from datetime import date
import yagmail
import os

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Asistente Ginecológico IA", page_icon="🩺")
st.title("🩺 Asistente clínico para ginecología")
st.markdown("Selecciona un modo de uso:")

# Inicializar historial
if "historial" not in st.session_state:
    st.session_state.historial = []

# Función PDF común con limpieza de emojis y encabezado personalizado
def limpiar_emojis(texto):
    return re.sub(r'[^\x00-\x7F]+', '', texto)

def generar_pdf(texto, filename="documento_clinico.pdf", encabezado=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    if encabezado:
        pdf.multi_cell(0, 10, encabezado)
        pdf.ln(5)
    for line in texto.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)
    return filename

def descargar_pdf_button(content, nombre_archivo, paciente_info):
    encabezado = f"Paciente: {paciente_info.get('nombre', '---')}\nRUT: {paciente_info.get('rut', '---')}\nFecha: {date.today().strftime('%d-%m-%Y')}"
    texto_limpio = limpiar_emojis(content)
    generar_pdf(texto_limpio, nombre_archivo, encabezado=encabezado)
    with open(nombre_archivo, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        href = f'<a href="data:application/pdf;base64,{base64_pdf}" download="{nombre_archivo}">📄 Descargar PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

# Función para enviar correo
def enviar_por_correo(archivo_pdf, destinatario):
    try:
        yag = yagmail.SMTP(user=st.secrets["EMAIL_USER"], password=st.secrets["EMAIL_PASSWORD"])
        yag.send(
            to=destinatario,
            subject="Documento clínico generado",
            contents="Adjunto encontrará el resumen generado por la consulta médica.",
            attachments=archivo_pdf
        )
        st.success(f"Correo enviado a {destinatario}")
    except Exception as e:
        st.error(f"Error al enviar correo: {e}")

# Datos del paciente
st.sidebar.markdown("### 🧍 Datos del paciente")
nombre_paciente = st.sidebar.text_input("Nombre completo")
rut_paciente = st.sidebar.text_input("RUT (opcional)")
correo_paciente = st.sidebar.text_input("✉️ Correo electrónico (opcional)")
paciente_info = {"nombre": nombre_paciente, "rut": rut_paciente, "correo": correo_paciente}

# Mostrar historial por paciente
st.sidebar.markdown("---")
if nombre_paciente:
    fichas = [f for f in st.session_state.historial if f["nombre"] == nombre_paciente]
    if fichas:
        st.sidebar.markdown(f"### 📚 Historial de {nombre_paciente}")
        for ficha in fichas[::-1]:
            with st.sidebar.expander(f"{ficha['tipo']} - {ficha['fecha']}"):
                st.code(ficha["contenido"], language="yaml")

# Tabs

tab1, tab2, tab3 = st.tabs([
    "📝 Triaje de síntomas",
    "🧾 Generador de recetas y órdenes",
    "📋 Resumen de exámenes previos"
])

# TAB 1 - Triaje
tab1.subheader("📝 Clasificador de síntomas para preconsulta")
tab1.markdown("Completa el campo con tus síntomas, preocupaciones o antecedentes:")

user_input_triaje = tab1.text_area("¿Qué síntomas tienes? ¿Desde cuándo? ¿Antecedentes? ¿Qué te preocupa?", key="triaje_input")

if tab1.button("Generar resumen para la doctora", key="triaje"):
    if not user_input_triaje.strip():
        tab1.warning("Por favor, escribe algo antes de generar el resumen.")
    else:
        with st.spinner("Analizando síntomas..."):
            prompt_triaje = f"""
Eres un asistente clínico que ayuda a una ginecóloga a preparar la consulta con pacientes en edad menopáusica.
Una paciente ha escrito libremente sus síntomas y preocupaciones. Genera un resumen clínico estructurado para la doctora que incluya:

- Edad estimada
- Principales síntomas
- Antecedentes médicos personales o familiares
- Motivo de la consulta
- Preguntas implícitas o explícitas de la paciente

Texto de la paciente:
"""
            prompt_triaje += user_input_triaje + """
"""
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt_triaje}],
                temperature=0.2
            )
            result = response.choices[0].message.content.strip()
            tab1.success("Resumen generado:")
            tab1.code(result, language="yaml")
            archivo = "Resumen_triaje.pdf"
            descargar_pdf_button(result, archivo, paciente_info)
            if correo_paciente:
                if tab1.button("📤 Enviar por correo", key="mail_triaje"):
                    enviar_por_correo(archivo, correo_paciente)
            st.session_state.historial.append({"nombre": nombre_paciente, "rut": rut_paciente, "fecha": date.today().isoformat(), "tipo": "Triaje", "contenido": result})
