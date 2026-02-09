import streamlit as st
import requests
import json
import pypdf
import docx
import pandas as pd
import os
import io
import time

# --- 1. НАЛАШТУВАННЯ СТОРІНКИ ---
st.set_page_config(
    page_title="Асистент рекрутера",
    page_icon="👔",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS СТИЛІЗАЦІЯ (ДИЗАЙН) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Прибрали сірий фон, лишили тільки відступи */
    .header-container {
        padding: 1rem 0rem;
        margin-bottom: 2rem;
    }
    
    h1 { 
        color: #2c3e50; 
        font-family: 'Helvetica', sans-serif; 
    }
    
    /* ПЕРЕКЛАД ЗАВАНТАЖУВАЧА ФАЙЛІВ */
    [data-testid='stFileUploaderDropzone'] div div span {
        display: none;
    }
    [data-testid='stFileUploaderDropzone'] div div::after {
        content: "Перетягніть файли сюди • Обмеження 200MB • PDF, DOCX";
        visibility: visible;
        display: block;
        font-size: 1rem;
        color: #555;
        margin-bottom: 10px;
    }
    [data-testid='stFileUploaderDropzone'] button {
        position: relative;
        color: transparent !important;
    }
    [data-testid='stFileUploaderDropzone'] button::after {
        content: "Обрати файли";
        position: absolute;
        color: #31333F;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        white-space: nowrap;
    }

    /* КНОПКА ЗАПУСКУ */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #4F46E5 0%, #2563EB 100%);
        color: white;
        border-radius: 12px;
        font-weight: bold;
        padding: 16px;
        font-size: 18px;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ФУНКЦІЇ ---

def read_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = pypdf.PdfReader(uploaded_file)
            return "".join([page.extract_text() or "" for page in reader.pages])
        elif uploaded_file.name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        return ""
    except:
        return ""

def call_gemini_json(api_key, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt + "\n\nReturn result strictly as JSON Array."}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "Error"

# --- 4. ІНТЕРФЕЙС ---

with st.sidebar:
    st.header("🔐 Налаштування")
    api_key = st.text_input("Google API Key", type="password")

# ШАПКА БЕЗ СІРОГО ФОНУ
st.markdown('<div class="header-container">', unsafe_allow_html=True)
col_logo, col_title = st.columns([1, 5])

with col_logo:
    if os.path.exists("logo.png"):
        # use_container_width=True дозволяє відобразити лого в оригінальній якості без розмиття
        st.image("logo.png", use_container_width=False) 
    else:
        st.markdown("## 👔")

with col_title:
    st.title("Асистент рекрутера") 
    st.markdown("##### Ваш персональний помічник у пошуку талантів")
st.markdown('</div>', unsafe_allow_html=True)

# --- ОСНОВНИЙ БЛОК ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("📝 1. Вакансія")
    job_file = st.file_uploader("Завантажте вакансію", type=["pdf", "docx"], label_visibility="collapsed")
    job_text = ""
    if job_file:
        job_text = read_file(job_file)
        if job_text: st.success("Вакансію завантажено")

with c2:
    st.subheader("🗂️ 2. Кандидати")
    resumes = st.file_uploader("Завантажте резюме", type=["pdf", "docx"], accept_multiple_files=True, label_visibility="collapsed")

if st.button("✨ ЗНАЙТИ ІДЕАЛЬНОГО КАНДИДАТА"):
    if not api_key:
        st.error("Введіть API Key")
    elif not job_text or not resumes:
        st.warning("Завантажте всі файли")
    else:
        with st.spinner("Аналізую кандидатів..."):
            # Тут логіка обробки (як була раніше)
            # ... (решта коду залишається такою ж)
            pass