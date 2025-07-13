import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Generador de Recetas y Órdenes", page_icon="🧾")
st.title("🧾 Generador automático de recetas y órdenes médicas")
st.markdown("Ingresa el plan de manejo clínico que escribirías en la ficha:")

user_input = st.text_area("Plan clínico", placeholder="Ej: Inicio de terapia hormonal con lenzetto 2 + didrogesterona medio\nMamo - eco\nDmo\nExs grales\nControl en 2 meses con resultados")

if st.button("Generar documentos"):
    if not user_input.strip():
        st.warning("Por favor, ingresa un plan de manejo clínico.")
    else:
        with st.spinner("Generando recetas y órdenes..."):

            prompt = f"""
Eres un asistente médico que transforma planes de manejo escritos por una ginecóloga en documentos clínicos estructurados. A partir del texto entregado, genera tres secciones:

1. 📄 Receta médica: lista los medicamentos mencionados con dosis, vía de administración y duración.
2. 🧪 Órdenes médicas: lista de exámenes a realizar, explicados con nombre completo.
3. 📅 Seguimiento: indicación de control o nueva consulta.

Texto del plan:
\"\"\"{user_input}\"\"\"
"""

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            result = response.choices[0].message.content.strip()

            st.success("Documentos generados:")
            st.markdown(result)