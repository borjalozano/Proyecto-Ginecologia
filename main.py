import streamlit as st
import openai
import os
#from dotenv import load_dotenv

# Cargar API Key
#load_dotenv()
#openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="Preconsulta Menopausia", page_icon="🩺")
st.title("🩺 Clasificador de síntomas para consulta ginecológica")
st.markdown("Completa el siguiente campo contando con tus propias palabras cómo te sientes:")

# Input del paciente
user_input = st.text_area("¿Qué síntomas tienes? ¿Desde cuándo? ¿Antecedentes? ¿Qué te preocupa?")

# Botón de envío
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

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        result = response.choices[0].message.content.strip()
        st.success("Resumen generado para la doctora:")
        st.code(result, language="yaml")