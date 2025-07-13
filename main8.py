import streamlit as st
from openai import OpenAI
from fpdf import FPDF
import base64
import fitz
import re
from datetime import date
import yagmail
import traceback

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Asistente Ginecológico IA", page_icon="🩺")
st.title("🩺 Asistente clínico para ginecología")

# Inicialización de estado
if "historial" not in st.session_state:
    st.session_state.historial = []
if "chat_pdf" not in st.session_state:
    st.session_state.chat_pdf = []
if "pdf_texto" not in st.session_state:
    st.session_state.pdf_texto = ""

# Funciones
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

def descargar_pdf_button(content, filename, paciente_info):
    encabezado = f"Paciente: {paciente_info.get('nombre', '---')}\nRUT: {paciente_info.get('rut', '---')}\nFecha: {date.today().strftime('%d-%m-%Y')}"
    texto_limpio = limpiar_emojis(content)
    generar_pdf(texto_limpio, filename, encabezado)
    with open(filename, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        href = f'<a href="data:application/pdf;base64,{base64_pdf}" download="{filename}">📄 Descargar PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

def enviar_por_correo(filename, destinatario):
    try:
        yag = yagmail.SMTP(user=st.secrets["EMAIL_USER"], password=st.secrets["EMAIL_PASSWORD"])
        yag.send(
            to=destinatario,
            subject="Documento clínico generado",
            contents="Adjunto encontrará el resumen generado por la consulta médica.",
            attachments=filename
        )
        st.success(f"Correo enviado a {destinatario}")
    except Exception as e:
        st.error(f"Error al enviar correo: {e}")
        st.exception(traceback.format_exc())

# Datos del paciente
st.sidebar.markdown("### 🧍 Datos del paciente")
nombre_paciente = st.sidebar.text_input("Nombre completo")
rut_paciente = st.sidebar.text_input("RUT (opcional)")
correo_paciente = st.sidebar.text_input("✉️ Correo electrónico (opcional)")
paciente_info = {"nombre": nombre_paciente, "rut": rut_paciente, "correo": correo_paciente}

# Historial
st.sidebar.markdown("---")
if nombre_paciente:
    fichas = [f for f in st.session_state.historial if f["nombre"] == nombre_paciente]
    if fichas:
        st.sidebar.markdown(f"### 📚 Historial de {nombre_paciente}")
        for ficha in fichas[::-1]:
            with st.sidebar.expander(f"{ficha['tipo']} - {ficha['fecha']}"):
                st.code(ficha["contenido"], language="yaml")

# Tabs
tab1, tab2, tab3, tab4 , tab5 = st.tabs([
    "📝 Triaje de síntomas",
    "🧾 Generador de recetas y órdenes",
    "📋 Resumen de exámenes previos",
    "💬 Chat sobre examen PDF"
    "📊 Panel clínico"
])

# --- PESTAÑA 1 ---
with tab1:
    st.subheader("📝 Clasificador de síntomas")
    entrada = st.text_area("Describe tus síntomas:", key="triaje_input")

    if st.button("Generar resumen", key="triaje"):
        if not entrada.strip():
            st.warning("Por favor escribe algo.")
        else:
            prompt = f"""
Eres un asistente clínico. Resume los síntomas de una paciente y genera un reporte estructurado.

Texto:
\"\"\"{entrada}\"\"\"
"""
            with st.spinner("Procesando..."):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                resultado = response.choices[0].message.content.strip()
                ...  # dentro de with tab1:
                st.session_state["resultado_triaje"] = resultado
                st.success("Resumen generado:")
                st.code(resultado, language="yaml")
                
                # Si ya hay diagnóstico anterior, combínalo
                resumen_completo = resultado
                if "dx_triaje" in st.session_state:
                    resumen_completo += "\n\n---\n\n🩺 Diagnóstico sugerido:\n" + st.session_state["dx_triaje"]

                archivo = "Resumen_triaje.pdf"
                descargar_pdf_button(resumen_completo, archivo, paciente_info)

                if correo_paciente and st.button("📤 Enviar por correo", key="mail_triaje"):
                    enviar_por_correo(archivo, correo_paciente)

                st.session_state.historial.append({
                    "nombre": nombre_paciente,
                    "rut": rut_paciente,
                    "fecha": date.today().isoformat(),
                    "tipo": "Triaje",
                    "contenido": resultado
                })

    # Botón diagnóstico solo si existe resumen previo
    if "resultado_triaje" in st.session_state:
        st.markdown("---")
        st.markdown("### 🔍 ¿Quieres sugerir un diagnóstico clínico con códigos CIE-10?")
        if st.button("Sugerir diagnóstico clínico + CIE-10", key="cie10_triaje"):
            with st.spinner("Generando diagnóstico sugerido..."):
                prompt_dx = f"""
Eres un asistente clínico que revisa un resumen de síntomas de una paciente.

A partir del siguiente texto, entrega:
- Un diagnóstico clínico sugerido
- Los códigos CIE-10 más probables (máximo 3)

Resumen clínico:
{st.session_state['resultado_triaje']}
"""
                response_dx = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt_dx}],
                    temperature=0.2
                )
                dx = response_dx.choices[0].message.content.strip()
                st.session_state["dx_triaje"] = dx  # lo guardamos para PDF
                st.success("Diagnóstico sugerido:")
                st.markdown(dx)
                st.session_state.historial.append({
                    "nombre": nombre_paciente,
                    "rut": rut_paciente,
                    "fecha": date.today().isoformat(),
                    "tipo": "Diagnóstico CIE-10",
                    "contenido": dx
                })

# --- PESTAÑA 2 ---
with tab2:
    st.subheader("🧾 Generador de recetas y órdenes")
    entrada = st.text_area("Plan de manejo:", key="plan_input")
    if st.button("Generar documentos", key="ordenes"):
        if not entrada.strip():
            st.warning("Por favor escribe un plan.")
        else:
            prompt = f"""
Eres un asistente médico. A partir del siguiente plan, genera:

- Receta médica
- Órdenes de exámenes
- Seguimiento

Texto:
\"\"\"{entrada}\"\"\"
"""
            with st.spinner("Procesando..."):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                resultado = response.choices[0].message.content.strip()
                st.success("Documentos generados:")
                st.markdown(resultado)
                archivo = "Ordenes_y_recetas.pdf"
                descargar_pdf_button(resultado, archivo, paciente_info)
                if correo_paciente and st.button("📤 Enviar por correo", key="mail_orden"):
                    enviar_por_correo(archivo, correo_paciente)
                st.session_state.historial.append({
                    "nombre": nombre_paciente,
                    "rut": rut_paciente,
                    "fecha": date.today().isoformat(),
                    "tipo": "Plan",
                    "contenido": resultado
                })

# --- PESTAÑA 3 ---
with tab3:
    st.subheader("📋 Resumen de exámenes previos")
    entrada = st.text_area("Resultados de exámenes:", key="examen_input")
    if st.button("Generar resumen", key="examenes"):
        if not entrada.strip():
            st.warning("Por favor escribe los resultados.")
        else:
            prompt = f"""
Eres un asistente clínico. Resume los resultados médicos ingresados por la paciente:

\"\"\"{entrada}\"\"\"
"""
            with st.spinner("Resumiendo..."):
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                resultado = response.choices[0].message.content.strip()
                st.success("Resumen generado:")
                st.markdown(resultado)
                archivo = "Resumen_examenes.pdf"
                descargar_pdf_button(resultado, archivo, paciente_info)
                if correo_paciente and st.button("📤 Enviar por correo", key="mail_exam"):
                    enviar_por_correo(archivo, correo_paciente)
                st.session_state.historial.append({
                    "nombre": nombre_paciente,
                    "rut": rut_paciente,
                    "fecha": date.today().isoformat(),
                    "tipo": "Exámenes",
                    "contenido": resultado
                })

# --- PESTAÑA 4 ---
with tab4:
    st.subheader("💬 Chat sobre informe en PDF")
    archivo_pdf = st.file_uploader("Sube un PDF de examen o informe médico", type=["pdf"])
    if archivo_pdf:
        with st.spinner("Leyendo PDF..."):
            doc = fitz.open(stream=archivo_pdf.read(), filetype="pdf")
            texto = ""
            for page in doc:
                texto += page.get_text()
            st.session_state.pdf_texto = texto
            st.text_area("Texto extraído:", texto, height=200)

    if st.session_state.pdf_texto:
        pregunta = st.text_input("Haz una pregunta sobre el informe:")
        if pregunta:
            with st.spinner("Consultando el documento..."):
                prompt_chat = f"""
Eres un asistente clínico. A continuación tienes el texto de un informe médico.
Responde solo en base a ese contenido.

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
        with st.expander(f"❓ {q}"):
            st.markdown(r)

...  # Agregar al final del bloque tabs

# --- PESTAÑA 5: Panel clínico ---
tab5 = st.tabs(["📝 Triaje", "🧾 Recetas", "📋 Exámenes", "💬 Chat PDF", "📊 Panel clínico"])[4]

with tab5:
    st.subheader("📊 Panel clínico de pacientes")

    # Agrupar historial por paciente
    pacientes = {}
    for ficha in st.session_state.historial:
        key = ficha['nombre']
        if key not in pacientes:
            pacientes[key] = []
        pacientes[key].append(ficha)

    # Buscar paciente
    nombres_disponibles = sorted(pacientes.keys())
    buscado = st.selectbox("Selecciona un paciente:", [""] + nombres_disponibles)

    if buscado:
        fichas = pacientes[buscado]
        st.markdown(f"### 📁 Historial de {buscado}")
        for ficha in fichas[::-1]:
            with st.expander(f"🗓️ {ficha['fecha']} - {ficha['tipo']}"):
                st.code(ficha["contenido"], language="yaml")
    else:
        st.markdown("_Selecciona un paciente en el menú desplegable para ver su historial._")
