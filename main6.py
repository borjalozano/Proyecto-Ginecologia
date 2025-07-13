import streamlit as st
from openai import OpenAI
from fpdf import FPDF
import base64
import fitz  # PyMuPDF
import re
from datetime import date

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

# Datos del paciente
st.sidebar.markdown("### 🧍 Datos del paciente")
nombre_paciente = st.sidebar.text_input("Nombre completo")
rut_paciente = st.sidebar.text_input("RUT (opcional)")
paciente_info = {"nombre": nombre_paciente, "rut": rut_paciente}

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
            descargar_pdf_button(result, "Resumen_triaje.pdf", paciente_info)
            st.session_state.historial.append({"nombre": nombre_paciente, "rut": rut_paciente, "fecha": date.today().isoformat(), "tipo": "Triaje", "contenido": result})

# TAB 2 - Órdenes y recetas
tab2.subheader("🧾 Generador automático de recetas y órdenes")
tab2.markdown("Ingresa el plan de manejo que escribirías en la ficha clínica:")

user_input_plan = tab2.text_area("Plan clínico", placeholder="Ej: Inicio de terapia hormonal con lenzetto 2 + didrogesterona medio\nMamo - eco\nDmo\nExs grales\nControl en 2 meses con resultados", key="plan_input")

if tab2.button("Generar documentos", key="ordenes"):
    if not user_input_plan.strip():
        tab2.warning("Por favor, escribe un plan clínico antes de generar.")
    else:
        with st.spinner("Generando recetas y órdenes..."):
            prompt_ordenes = f"""
Eres un asistente médico que transforma planes de manejo escritos por una ginecóloga en documentos clínicos estructurados. A partir del texto entregado, genera tres secciones:

1. Receta médica: lista los medicamentos mencionados con dosis, vía de administración y duración.
2. Órdenes médicas: lista de exámenes a realizar, explicados con nombre completo.
3. Seguimiento: indicación de control o nueva consulta.

Texto del plan:
"""
            prompt_ordenes += user_input_plan + """
"""
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt_ordenes}],
                temperature=0.3
            )
            result = response.choices[0].message.content.strip()
            tab2.success("Documentos generados:")
            tab2.markdown(result)
            descargar_pdf_button(result, "Ordenes_y_recetas.pdf", paciente_info)
            st.session_state.historial.append({"nombre": nombre_paciente, "rut": rut_paciente, "fecha": date.today().isoformat(), "tipo": "Plan", "contenido": result})

# TAB 3 - Exámenes previos
tab3.subheader("📋 Resumen de exámenes previos")
tab3.markdown("Ingresa los resultados que ya tengas disponibles antes de la consulta:")

user_input_examenes = tab3.text_area("Resultados disponibles", placeholder="Ej:\nPAP en julio 2023, normal\nMamografía en abril 2024, BI-RADS 2\nDMO: osteopenia leve\nColesterol 230, glicemia normal, TSH 2.1", key="examenes_input")

if tab3.button("Generar resumen de exámenes", key="examenes"):
    if not user_input_examenes.strip():
        tab3.warning("Por favor, completa los datos de exámenes.")
    else:
        with st.spinner("Resumiendo exámenes..."):
            prompt_examenes = f"""
Eres un asistente clínico que ayuda a una ginecóloga a revisar exámenes previos informados por una paciente. A partir del texto ingresado, estructura los resultados en las siguientes categorías:

- PAP: fecha, resultado, recomendación
- Mamografía/Ecografía: fecha, resultado, interpretación
- DMO: interpretación y sugerencia
- Exámenes generales: colesterol, glicemia, TSH u otros

Indica si algún examen está vencido o si requiere seguimiento.

Texto del paciente:
"""
            prompt_examenes += user_input_examenes + """
"""
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt_examenes}],
                temperature=0.2
            )
            result = response.choices[0].message.content.strip()
            tab3.success("Resumen generado:")
            tab3.markdown(result)
            descargar_pdf_button(result, "Resumen_examenes.pdf", paciente_info)
            st.session_state.historial.append({"nombre": nombre_paciente, "rut": rut_paciente, "fecha": date.today().isoformat(), "tipo": "Exámenes", "contenido": result})
