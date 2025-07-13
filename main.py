import streamlit as st
from openai import OpenAI

# Configura el cliente con tu API Key
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Preconsulta Ginecológica", page_icon="🩺")
st.title("🩺 Clasificador de síntomas para consulta ginecológica")
st.markdown("Completa el siguiente campo contando con tus propias palabras cómo te sientes:")

user_input = st.text_area("¿Qué síntomas tienes? ¿Desde cuándo? ¿Antecedentes? ¿Qué te preocupa?")

if st.button("Generar resumen para la doctora") and user_input.strip() != "":
    with st.spinner("Analizando síntomas..."):

        prompt = f"""
Eres un asistente clínico que ayuda a una ginecóloga a preparar la consulta con pacientes en edad menopáusica.
Una paciente ha escrito libremente sus síntomas y preocupaciones. Genera un resumen clínico estructurado para la doctora que incluya:

- Edad estimada
- Principales síntomas
- Antecedentes médicos personales o familiares
- Motivo de la consulta
- Preguntas implícitas o explícitas de la paciente

Texto de la paciente:
\"\"\"{user_input}\"\"\"
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        result = response.choices[0].message.content.strip()
        st.success("Resumen generado para la doctora:")
        st.code(result, language="yaml")