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
    
    /* --- СІРИЙ ФОН ДЛЯ ШАПКИ --- */
    .gray-header {
        background-color: #f0f2f6; /* Світло-сірий */
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 1px solid #e0e0e0;
    }
    
    h1 { 
        color: #2c3e50; 
        font-family: 'Helvetica', sans-serif; 
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* --- ПЕРЕКЛАД ЗАВАНТАЖУВАЧА ФАЙЛІВ (CSS HACK) --- */
    
    /* 1. Приховуємо оригінальний англійський текст інструкції */
    [data-testid='stFileUploaderDropzone'] div div span {
        display: none;
    }
    
    /* 2. Додаємо український текст замість нього */
    [data-testid='stFileUploaderDropzone'] div div::after {
        content: "Перетягніть файли сюди • Обмеження 200MB • PDF, DOCX";
        visibility: visible;
        display: block;
        font-size: 1rem;
        color: #555;
        margin-bottom: 10px;
    }

    /* 3. Переклад кнопки "Browse files" */
    [data-testid='stFileUploaderDropzone'] button {
        position: relative;
        color: transparent !important; /* Ховаємо текст кнопки */
    }
    
    [data-testid='stFileUploaderDropzone'] button::after {
        content: "Обрати файли"; /* Новий текст */
        position: absolute;
        color: #31333F; /* Колір тексту (темний, як стандартний) */
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        white-space: nowrap;
        font-weight: 400;
    }

    /* --- КНОПКА ЗАПУСКУ --- */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #4F46E5 0%, #2563EB 100%);
        color: white;
        border-radius: 12px;
        font-weight: bold;
        padding: 16px;
        font-size: 18px;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
    }
    
    /* --- АНІМАЦІЯ --- */
    .loading-text {
        font-size: 24px;
        font-weight: bold;
        color: #2563EB;
        text-align: center;
        padding: 20px;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
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
    base_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    model_name = "gemini-1.5-flash"
    
    try:
        r = requests.get(base_url)
        if r.status_code == 200:
            data = r.json()
            for m in data.get('models', []):
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    if 'flash' in m['name']: 
                        model_name = m['name'].replace('models/', '')
                        break
    except:
        pass

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    final_prompt = prompt + "\n\nReturn the result strictly as a JSON Array of objects."
    
    data = {
        "contents": [{"parts": [{"text": final_prompt}]}],
        "generationConfig": {
            "temperature": 0.2, 
            "responseMimeType": "application/json"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code != 200: return f"Error: {response.text}"
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Error: {str(e)}"

# --- 4. ЗБЕРЕЖЕННЯ СТАНУ ---
if 'results_df' not in st.session_state:
    st.session_state.results_df = None

# --- ІНТЕРФЕЙС ---

with st.sidebar:
    st.header("🔐 Налаштування")
    api_key = st.text_input("Google API Key", type="password")
    if api_key:
        st.success("Ключ прийнято")

# --- ШАПКА САЙТУ (СІРИЙ ФОН) ---
# Ми відкриваємо HTML контейнер для сірого фону
st.markdown('<div class="gray-header">', unsafe_allow_html=True)

col_logo, col_title = st.columns([1, 6], gap="medium")

with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120) 
    else:
        st.markdown("## 👔")

with col_title:
    st.title("Асистент рекрутера") 
    st.markdown("##### Інтелектуальна система суворого відбору")

# Закриваємо контейнер
st.markdown('</div>', unsafe_allow_html=True)

# --- ОСНОВНА ЧАСТИНА ---

c1, c2 = st.columns(2)

# ВАКАНСІЯ
with c1:
    st.subheader("📝 1. Вакансія")
    tab1, tab2 = st.tabs(["📤 Файл", "✍️ Текст"])
    
    job_text_final = ""
    
    with tab1:
        # label_visibility="collapsed" приховує стандартний напис, щоб ми додали свій CSS
        job_file = st.file_uploader("Файл вакансії", type=["pdf", "docx"], key="j_up", label_visibility="collapsed")
        if job_file:
            extracted = read_file(job_file)
            if extracted:
                job_text_final = extracted
                st.success("Файл прочитано")
    
    with tab2:
        text_input = st.text_area("Вставте текст:", height=300, key="j_txt")
        if not job_text_final and text_input:
            job_text_final = text_input

# РЕЗЮМЕ
with c2:
    st.subheader("🗂️ 2. Кандидати")
    # Тут так само ховаємо лейбл, бо CSS все зробить красиво
    uploaded_files = st.file_uploader("Резюме", type=["pdf", "docx"], accept_multiple_files=True, label_visibility="collapsed")
    if uploaded_files:
        st.info(f"✅ Готово: {len(uploaded_files)} файлів")

st.markdown("###")
start_btn = st.button("✨ ЗНАЙТИ ІДЕАЛЬНОГО КАНДИДАТА", type="primary")

if start_btn:
    st.session_state.results_df = None
    
    if not api_key:
        st.error("Будь ласка, введіть API Key у боковому меню зліва.")
    elif not job_text_final or not uploaded_files:
        st.warning("Будь ласка, завантажте опис вакансії та резюме кандидатів.")
    else:
        # АНІМАЦІЯ
        loading_phrases = [
            "🧠 Аналізую вимоги...", 
            "⚖️ Вмикаю режим суворого відбору...",
            "🔍 Шукаю приховані ризики...",
            "💎 Відсіюю невідповідних кандидатів...",
            "🚀 Формую фінальний рейтинг..."
        ]
        
        status_container = st.empty()
        for phrase in loading_phrases:
            status_container.markdown(f'<div class="loading-text">{phrase}</div>', unsafe_allow_html=True)
            time.sleep(0.7)
            
        full_text = ""
        for f in uploaded_files:
            content = read_file(f)
            clean_content = content.replace("\n", " ")[:6000]
            full_text += f"\n--- File: {f.name} ---\n{clean_content}"
        
        # --- ПРОМПТ ---
        prompt = f"""
        ##Роль
        Ти — бот-помічник рекрутера (Асистент рекрутера).

        ##Задачі
        Допомогти в попередній оцінці кандидатів.
        !!ВАЖЛИВО: Оцінюй максимально строго. Відсів важливіше приємних коментарів.

        ##Дані
        Вакансія: {job_text_final}
        Резюме: {full_text}

        ##Результат (JSON)
        Поверни масив об'єктів:
        1. "Name"
        2. "Age_Exp" (Вік/Досвід)
        3. "Strengths" (Теги плюсів)
        4. "Weaknesses" (Теги мінусів)
        5. "Highlights" (Важливе/Незвичне)
        6. "Score" (1-10)
        7. "Verdict" ("Не варто спілкуватися" [1-3], "Резерв" [4-6], "Запросити" [7-10])
        8. "Risks"

        Мова: Українська.
        """
        
        raw_response = call_gemini_json(api_key, prompt)
        status_container.empty()
        
        try:
            clean_json = raw_response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            df = pd.DataFrame(data)
            
            if 'Score' in df.columns:
                df = df.sort_values(by='Score', ascending=False)
            
            display_df = df.rename(columns={
                "Name": "Кандидат", "Age_Exp": "Досвід", "Strengths": "Плюси",
                "Weaknesses": "Мінуси", "Highlights": "Важливе", "Score": "Бал", 
                "Verdict": "Вердикт", "Risks": "Ризики"
            })
            
            st.session_state.results_df = display_df

        except Exception as e:
            st.error("Помилка обробки. Спробуйте ще раз.")
            st.code(raw_response)

# ВІДОБРАЖЕННЯ
if st.session_state.results_df is not None:
    df = st.session_state.results_df
    
    st.success("✅ Аналіз завершено!")
    
    def color_rows(val):
        s = str(val).lower()
        if 'запросити' in s: return 'background-color: #dcfce7; color: #166534; font-weight: bold'
        if 'не варто' in s: return 'background-color: #fee2e2; color: #991b1b'
        return 'background-color: #fef9c3; color: #854d0e'

    st.dataframe(df.style.map(color_rows, subset=['Вердикт']), use_container_width=True, hide_index=True)
    
    st.markdown("###")
    
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Скачати Excel таблицю",
        data=csv_data,
        file_name="recruiter_assistant_report.csv",
        mime="text/csv",
        use_container_width=True
    )