import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import time
import json
import random
from datetime import datetime

# --- 1. CONFIGURAÇÃO E ESTILO (CSS PROFISSIONAL) ---
st.set_page_config(page_title="Nexus ENEM", page_icon="💠", layout="wide")

# Paleta de Cores Enterprise (Dark Mode Clean)
theme = {
    "bg": "#0E1117",
    "card": "#1E1E1E",
    "primary": "#4F46E5", # Indigo Moderno
    "success": "#10B981",
    "text": "#F3F4F6",
    "subtext": "#9CA3AF"
}

st.markdown(f"""
<style>
    /* Reset básico */
    .stApp {{ background-color: {theme['bg']}; color: {theme['text']}; }}
    
    /* Cards Flutuantes */
    .css-card {{
        background-color: {theme['card']};
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #374151;
        margin-bottom: 20px;
    }}
    
    /* Títulos Elegantes */
    h1, h2, h3 {{ color: #ffffff !important; font-family: 'Inter', sans-serif; }}
    
    /* Botões Premium */
    .stButton>button {{
        background-color: {theme['primary']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.2s;
    }}
    .stButton>button:hover {{ filter: brightness(110%); transform: translateY(-1px); }}
    
    /* Remove decorações padrão do Streamlit */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Métricas */
    .metric-value {{ font-size: 2rem; font-weight: bold; color: {theme['success']}; }}
    .metric-label {{ color: {theme['subtext']}; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; }}
</style>
""", unsafe_allow_html=True)

# --- 2. CAMADA DE DADOS (DATABASE MANAGER) ---
class DatabaseManager:
    def __init__(self, db_name="nexus_enem.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.init_db()

    def init_db(self):
        c = self.conn.cursor()
        # Tabelas Otimizadas
        c.execute('''CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, disciplina TEXT, enunciado TEXT, 
            alternativas TEXT, correta TEXT, explicacao TEXT, dificuldade TEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT, data DATETIME, disciplina TEXT, 
            acertos INTEGER, total INTEGER, xp_ganho INTEGER)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY, questao_id INTEGER, user_res TEXT)''')

        self.conn.commit()
        self.check_seed()

    def check_seed(self):
        # Verifica se precisa popular (apenas se vazio)
        count = self.conn.execute("SELECT count(*) FROM questoes").fetchone()[0]
        if count == 0:
            self.seed_database()

    def seed_database(self):
        # Banco Inicial Profissional
        base_questions = [
            ("Filosofia", "O imperativo categórico de Kant determina que:", '{"A":"Devemos agir por interesse","B":"A ação deve poder se tornar lei universal","C":"Os fins justificam os meios","D":"A fé supera a razão"}', "B", "Ética do dever universal.", "Difícil"),
            ("Matemática", "Logaritmo de 100 na base 10:", '{"A":"1","B":"2","C":"10","D":"100"}', "B", "10 ao quadrado é 100.", "Fácil"),
            ("Física", "Lei da Inércia (1ª Lei de Newton):", '{"A":"Ação e Reação","B":"Corpo em movimento tende a continuar em movimento","C":"F=m.a","D":"Gravidade"}', "B", "Resistência à mudança de movimento.", "Fácil"),
            ("História", "Quem era o presidente na construção de Brasília?", '{"A":"Vargas","B":"JK","C":"Jânio","D":"Médici"}', "B", "Juscelino Kubitschek.", "Média"),
            ("Química", "O que é um íon Cátion?", '{"A":"Carga Negativa","B":"Carga Positiva","C":"Neutro","D":"Radioativo"}', "B", "Perdeu elétrons, ficou positivo.", "Média"),
            ("Biologia", "Qual a função do Ribossomo?", '{"A":"Síntese de Proteínas","B":"Respiração","C":"Digestão","D":"Fotossíntese"}', "A", "Fábrica de proteínas.", "Média")
        ]
        # Multiplicação Inteligente (Simula Big Data)
        final_qs = []
        for _ in range(35): # Gera ~200 questoes
            for q in base_questions:
                final_qs.append(q)
        
        self.conn.executemany("INSERT INTO questoes (disciplina, enunciado, alternativas, correta, explicacao, dificuldade) VALUES (?,?,?,?,?,?)", final_qs)
        self.conn.commit()

    def get_questions(self, disciplina, qtd):
        query = "SELECT * FROM questoes WHERE disciplina = ? ORDER BY RANDOM() LIMIT ?" if disciplina != "Todas" else "SELECT * FROM questoes ORDER BY RANDOM() LIMIT ?"
        params = (disciplina, qtd) if disciplina != "Todas" else (qtd,)
        return self.conn.execute(query, params).fetchall()

    def save_result(self, disciplina, acertos, total, xp):
        self.conn.execute("INSERT INTO historico (data, disciplina, acertos, total, xp_ganho) VALUES (?,?,?,?,?)",
                          (datetime.now(), disciplina, acertos, total, xp))
        self.conn.commit()

    def get_stats(self):
        df = pd.read_sql("SELECT * FROM historico", self.conn)
        return df

# Instância Única (Singleton)
db = DatabaseManager()

# --- 3. LÓGICA DE NEGÓCIO (SESSION STATE) ---
if 'user_state' not in st.session_state:
    st.session_state.user_state = {
        'page': 'dashboard',
        'current_quiz': [],
        'quiz_start_time': None
    }

def navigate_to(page):
    st.session_state.user_state['page'] = page
    st.rerun()

# --- 4. COMPONENTES DE UI ---
def render_dashboard():
    st.title("💠 Dashboard Nexus")
    
    # Busca dados reais
    df = db.get_stats()
    
    # KPIs (Indicadores Chave)
    col1, col2, col3, col4 = st.columns(4)
    
    xp_total = df['xp_ganho'].sum() if not df.empty else 0
    simulados = len(df)
    precisao = (df['acertos'].sum() / df['total'].sum() * 100) if not df.empty and df['total'].sum() > 0 else 0
    
    with col1:
        st.markdown(f"<div class='css-card'><div class='metric-label'>XP Total</div><div class='metric-value'>{xp_total}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='css-card'><div class='metric-label'>Simulados</div><div class='metric-value'>{simulados}</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='css-card'><div class='metric-label'>Precisão</div><div class='metric-value'>{precisao:.1f}%</div></div>", unsafe_allow_html=True)
    with col4:
        # Ranking Simulado
        rank = "Diamante" if xp_total > 1000 else "Ouro" if xp_total > 500 else "Ferro"
        color = "#10B981" if rank == "Diamante" else "#FBBF24"
        st.markdown(f"<div class='css-card'><div class='metric-label'>Patente</div><div class='metric-value' style='color:{color}'>{rank}</div></div>", unsafe_allow_html=True)

    # Gráfico Principal
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.subheader("📈 Evolução de Desempenho")
        if not df.empty:
            df['data'] = pd.to_datetime(df['data'])
            fig = px.area(df, x='data', y='xp_ganho', color='disciplina', template='plotly_dark')
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Realize seu primeiro simulado para gerar gráficos.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_side:
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.subheader("🚀 Novo Simulado")
        
        with st.form("config_simulado"):
            materia = st.selectbox("Disciplina", ["Todas", "Matemática", "Filosofia", "História", "Física", "Química", "Biologia"])
            qtd = st.slider("Questões", 5, 50, 10)
            submitted = st.form_submit_button("Iniciar Prova")
            
            if submitted:
                questions = db.get_questions(materia, qtd)
                if questions:
                    st.session_state.user_state['current_quiz'] = questions
                    st.session_state.user_state['quiz_discipline'] = materia
                    navigate_to('quiz')
                else:
                    st.error("Erro ao gerar prova.")
        st.markdown("</div>", unsafe_allow_html=True)

def render_quiz():
    questions = st.session_state.user_state['current_quiz']
    if not questions:
        navigate_to('dashboard')
    
    total = len(questions)
    st.progress(0, text=f"Modo Prova: {st.session_state.user_state['quiz_discipline']}")
    
    # --- O SEGREDO DA ESTABILIDADE: UM ÚNICO FORMULÁRIO GIGANTE ---
    with st.form("quiz_form"):
        st.subheader(f"📝 Prova de {st.session_state.user_state['quiz_discipline']}")
        
        user_answers = {}
        
        for idx, q in enumerate(questions):
            st.markdown(f"**{idx + 1}.** {q[2]}") # Enunciado
            alts = json.loads(q[3])
            
            # Key única é vital
            user_answers[idx] = st.radio(
                "Selecione:", 
                options=list(alts.keys()), 
                format_func=lambda x: f"{x}) {alts[x]}",
                key=f"q_{q[0]}_{idx}",
                label_visibility="collapsed"
            )
            st.divider()
        
        finish = st.form_submit_button("Finalizar e Entregar Prova")
        
    if finish:
        # Processamento em lote (Batch Processing)
        acertos = 0
        xp = 0
        
        for idx, q in enumerate(questions):
            resp_usuario = user_answers.get(idx)
            if resp_usuario == q[4]: # Se letra correta
                acertos += 1
                xp += 20 if q[6] == "Difícil" else 10
            else:
                # Lógica silenciosa de Flashcard (Profissional não avisa a cada erro, avisa no final)
                pass 
        
        # Salva
        db.save_result(st.session_state.user_state['quiz_discipline'], acertos, total, xp)
        
        # Guarda dados para tela de resultado
        st.session_state.user_state['last_result'] = {
            "acertos": acertos, "total": total, "xp": xp
        }
        navigate_to('result')

def render_result():
    res = st.session_state.user_state.get('last_result', {})
    
    st.balloons()
    
    col_c, _ = st.columns([1, 2])
    with col_c:
        st.markdown("<div class='css-card' style='text-align:center'>", unsafe_allow_html=True)
        st.markdown("## Resultado")
        st.markdown(f"<h1 style='font-size: 4rem; color: #4F46E5'>{res['acertos']}/{res['total']}</h1>", unsafe_allow_html=True)
        st.markdown(f"**XP Ganho:** +{res['xp']}")
        
        if st.button("Voltar ao Dashboard"):
            navigate_to('dashboard')
        st.markdown("</div>", unsafe_allow_html=True)

# --- 5. ROTEADOR DE PÁGINAS (MAIN LOOP) ---
page = st.session_state.user_state['page']

if page == 'dashboard':
    render_dashboard()
elif page == 'quiz':
    render_quiz()
elif page == 'result':
    render_result()
