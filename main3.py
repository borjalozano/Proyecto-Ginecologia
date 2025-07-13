import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Asistente Ginecológico IA", page_icon="🩺")
st.title("🩺 Asistente clínico para ginecología")
st.markdown("Selecciona un modo de uso:")

tab1, tab2, tab3 = st.tabs([
    "📝 Triaje de síntomas",
    "🧾 Generador de recetas y órdenes",
    "📋 Resumen de exámenes previos"
])

# TAB 1 - Triaje de síntomas
with tab1:
    st.subheader("📝 Clasificador de síntomas para preconsulta")
    st.markdown("Completa el campo con tus síntomas, preocupaciones o antecedentes:")

    user_input_triaje = st.text_area("¿Qué síntomas tienes? ¿Desde cuándo? ¿Antecedentes? ¿Qué te preocupa?")

    if st.button("Generar resumen para la doctora", key="triaje"):
        if not user_input_triaje.strip():
            st.warning("Por favor, escribe algo antes de generar el resumen.")
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
\"\"\"{user_input_triaje}\"\"\"
"""

                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt_triaje}],
                    temperature=0.2
                )

                result = response.choices[0].message.content.strip()
                st.success("Resumen generado:")
                st.code(result, language="yaml")

# TAB 2 - Plan de tratamiento → Recetas y órdenes
with tab2:
    st.subheader("🧾 Generador automático de recetas y órdenes")
    st.markdown("Ingresa el plan de manejo clínico que escribirías en la ficha:")

    user_input_plan = st.text_area("Plan clínico", placeholder="Ej: Inicio de terapia hormonal con lenzetto 2 + didrogesterona medio\nMamo - eco\nDmo\nExs grales\nControl en 2 meses con resultados")

    if st.button("Generar documentos", key="ordenes"):
        if not user_input_plan.strip():
            st.warning("Por favor, escribe un plan clínico antes de generar.")
        else:
            with st.spinner("Generando recetas y órdenes..."):

                prompt_ordenes = f"""
Eres un asistente médico que transforma planes de manejo escritos por una ginecóloga en documentos clínicos estructurados. A partir del texto entregado, genera tres secciones:

1. 📄 Receta médica: lista los medicamentos mencionados con dosis, vía de administración y duración.
2. 🧪 Órdenes médicas: lista de exámenes a realizar, explicados con nombre completo.
3. 📅 Seguimiento: indicación de control o nueva consulta.

Texto del plan:
\"\"\"{user_input_plan}\"\"\"
"""

                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt_ordenes}],
                    temperature=0.3
                )

                result = response.choices[0].message.content.strip()
                st.success("Documentos generados:")
                st.markdown(result)

# TAB 3 - Exámenes previos
with tab3:
    st.subheader("📋 Resumen de exámenes previos")
    st.markdown("Las pacientes pueden anotar los resultados que ya tengan. El sistema generará un resumen estructurado para revisión médica.")

    user_input_examenes = st.text_area("Resultados disponibles", placeholder="Ej:\nPAP en julio 2023, normal\nMamografía en abril 2024, BI-RADS 2\nDMO: osteopenia leve\nColesterol 230, glicemia normal, TSH 2.1")

    if st.button("Generar resumen de exámenes", key="examenes"):
        if not user_input_examenes.strip():
            st.warning("Por favor, completa los datos de exámenes.")
        else:
            with st.spinner("Resumiendo exámenes..."):

                prompt_examenes = f"""
Eres un asistente clínico que ayuda a una ginecóloga a revisar exámenes previos informados por una paciente. A partir del texto ingresado, estructura los resultados en las siguientes categorías:

- 📄 PAP: fecha, resultado, recomendación
- 🧠 Mamografía/Ecografía: fecha, resultado, interpretación
- 🦴 DMO: interpretación y sugerencia
- 🧪 Exámenes generales: colesterol, glicemia, TSH u otros

Indica si algún examen está vencido o si requiere seguimiento.

Texto del paciente:
\"\"\"{user_input_examenes}\"\"\"
"""

                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt_examenes}],
                    temperature=0.2
                )

                result = response.choices[0].message.content.strip()
                st.success("Resumen de exámenes:")
                st.markdown(result)