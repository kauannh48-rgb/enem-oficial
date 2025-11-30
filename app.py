import streamlit as st
import sqlite3
import json
import random
import time
import pandas as pd
import plotly.express as px # Biblioteca de Gráficos Bonitos
from datetime import datetime, date

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="ENEM Analytics", page_icon="📊", layout="wide")

# --- CONEXÃO COM BANCO ---
def conectar_db():
    return sqlite3.connect('enem_analytics.db')

def criar_tabelas():
    conn = conectar_db()
    c = conn.cursor()
    # Tabelas Base
    c.execute('''CREATE TABLE IF NOT EXISTS perfil (
        id INTEGER PRIMARY KEY, nome TEXT DEFAULT 'Estudante', xp INTEGER DEFAULT 0, 
        ultimo_acesso TEXT, dias_seguidos INTEGER DEFAULT 0, meta_diaria INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS materias_stats (
        disciplina TEXT PRIMARY KEY, xp INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS questoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, disciplina TEXT, assunto TEXT, enunciado TEXT, 
        alternativas TEXT, letra_correta TEXT, explicacao TEXT, dificuldade TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT, questao_id INTEGER, enunciado TEXT, 
        resposta_certa TEXT, explicacao TEXT)''')
    
    # SEED (Garante que existem matérias para o gráfico não quebrar)
    c.execute('SELECT count(*) FROM materias_stats')
    if c.fetchone()[0] == 0:
        materias = ["Matemática", "Física", "História", "Química", "Biologia", "Português"]
        for m in materias:
            c.execute('INSERT INTO materias_stats (disciplina, xp) VALUES (?, 10)', (m,)) # Começa com 10xp para o gráfico aparecer
        conn.commit()
        
    # SEED QUESTOES (Exemplo Rápido)
    c.execute('SELECT count(*) FROM questoes')
    if c.fetchone()[0] == 0:
        qs = [
            ("Matemática", "Básica", "50% de 80?", '{"A":"40","B":"30"}', "A", "Metade de 80.", "Fácil"),
            ("História", "Brasil", "Ano da Independência?", '{"A":"1889","B":"1822"}', "B", "7 de Setembro.", "Fácil"),
            ("Física", "Mecânica", "Gravidade da Terra?", '{"A":"9.8","B":"1.6"}', "A", "Aprox 10m/s².", "Média"),
            ("Química", "Água", "Fórmula da água?", '{"A":"HO2","B":"H2O"}', "B", "2 Hidrogênios 1 Oxigênio.", "Fácil"),
            ("Biologia", "Vírus", "Vírus é ser vivo?", '{"A":"Sim","B":"Não há consenso"}', "B", "Não tem célula.", "Difícil")
        ]
        for _ in range(5): c.executemany('INSERT INTO questoes (disciplina, assunto, enunciado, alternativas, letra_correta, explicacao, dificuldade) VALUES (?,?,?,?,?,?,?)', qs)
        conn.commit()
    conn.close()

# --- LÓGICA DE STREAK (DIAS SEGUIDOS) ---
def verificar_streak():
    conn = conectar_db()
    hj = str(date.today())
    perfil = conn.execute('SELECT ultimo_acesso, dias_seguidos, meta_diaria FROM perfil').fetchone()
    
    if not perfil: # Cria perfil se não existir
        conn.execute("INSERT INTO perfil (ultimo_acesso, dias_seguidos) VALUES (?, 1)", (hj,))
        streak = 1
        meta = 0
    else:
        ultimo, streak, meta = perfil
        if ultimo != hj:
            # Se logou ontem, aumenta streak. Se logou antes, zera.
            # (Simplificação: aqui apenas atualiza data para teste, lógica real precisa comparar dias)
            conn.execute('UPDATE perfil SET ultimo_acesso = ?, dias_seguidos = dias_seguidos + 1, meta_diaria = 0 WHERE id=1', (hj,))
            streak += 1
            meta = 0 # Zera meta do dia novo
    
    conn.commit()
    conn.close()
    return streak, meta

def atualizar_xp_materia(disc, pts):
    conn = conectar_db()
    conn.execute('UPDATE materias_stats SET xp = xp + ? WHERE disciplina = ?', (pts, disc))
    conn.execute('UPDATE perfil SET xp = xp + ?, meta_diaria = meta_diaria + ?', (pts, pts)) # XP Geral e Meta
    conn.commit()
    conn.close()

# --- GRÁFICOS (PLOTLY) ---
def plotar_radar():
    conn = conectar_db()
    df = pd.read_sql_query("SELECT disciplina, xp FROM materias_stats", conn)
    conn.close()
    
    if df.empty: return None
    
    # Cria o gráfico aranha
    fig = px.line_polar(df, r='xp', theta='disciplina', line_close=True, 
                        title="Seu Radar de Conhecimento",
                        template="plotly_dark")
    fig.update_traces(fill='toself', line_color='#00ff00')
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(df['xp'].max(), 100)])),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white")
    )
    return fig

# --- INTERFACE ---
criar_tabelas()
streak_atual, meta_hoje = verificar_streak()
META_ALVO = 100 # Meta de 100 XP por dia

if 'pagina' not in st.session_state: st.session_state.pagina = 'home'

# CSS Estilizado
st.markdown("""
<style>
    .stApp { background-color: #111; color: #fff; }
    .card-metric { background-color: #222; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #333; }
    .big-number { font-size: 24px; font-weight: bold; color: #00ff00; }
    .stProgress > div > div > div > div { background-color: #00ff00; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: DASHBOARD PESSOAL ---
with st.sidebar:
    st.title("📊 Painel do Aluno")
    
    # Card de Ofensiva (Streak)
    st.markdown(f"""
    <div class="card-metric">
        🔥 Ofensiva <br>
        <span class="big-number">{streak_atual} Dias</span>
    </div>
    <br>
    """, unsafe_allow_html=True)
    
    # Meta Diária
    st.write(f"🎯 **Meta Diária:** {meta_hoje}/{META_ALVO} XP")
    st.progress(min(meta_hoje / META_ALVO, 1.0))
    if meta_hoje >= META_ALVO:
        st.success("Meta Batida! 🏆")
    
    st.divider()
    if st.button("🏠 Home"): st.session_state.pagina = 'home'
    if st.button("📚 Flashcards"): st.session_state.pagina = 'flashcards'

# --- PAGINA HOME ---
if st.session_state.pagina == 'home':
    st.title("Central de Inteligência")
    
    col_grafico, col_botoes = st.columns([2, 1])
    
    with col_grafico:
        # Exibe o gráfico Aranha
        figura = plotar_radar()
        if figura:
            st.plotly_chart(figura, use_container_width=True)
            
    with col_botoes:
        st.subheader("O que vamos treinar?")
        disc = st.selectbox("Matéria Foco:", ["Matemática", "Física", "História", "Química", "Biologia", "Português"])
        
        st.info("O Sistema recomenda focar onde seu gráfico está menor!")
        
        if st.button("🚀 INICIAR TREINO", type="primary"):
            conn = conectar_db()
            quests = conn.execute("SELECT * FROM questoes WHERE disciplina = ? ORDER BY RANDOM() LIMIT 3", (disc,)).fetchall()
            # Fallback se não achar a materia
            if not quests: quests = conn.execute("SELECT * FROM questoes ORDER BY RANDOM() LIMIT 3").fetchall()
            conn.close()
            
            st.session_state.quiz_data = quests
            st.session_state.idx = 0
            st.session_state.acertos = 0
            st.session_state.xp_sessao = 0
            st.session_state.pagina = 'quiz'
            st.rerun()

# --- PAGINA QUIZ ---
elif st.session_state.pagina == 'quiz':
    if 'quiz_data' not in st.session_state: st.rerun()
    
    q = st.session_state.quiz_data[st.session_state.idx]
    total = len(st.session_state.quiz_data)
    
    st.progress((st.session_state.idx + 1)/total)
    st.markdown(f"**{q[1]}** | Dificuldade: {q[7]}")
    st.markdown(f"### {q[3]}")
    
    alts = json.loads(q[4])
    k = f"q_{q[0]}"
    
    if k not in st.session_state:
        escolha = st.radio("Alternativa:", list(alts.keys()), format_func=lambda x: f"{x}) {alts[x]}", key=f"rad_{q[0]}")
        if st.button("Confirmar"):
            st.session_state[k] = escolha
            if escolha == q[5]:
                ganho = 20
                st.session_state.acertos += 1
                st.session_state.xp_sessao += ganho
                atualizar_xp_materia(q[1], ganho) # Atualiza o gráfico em tempo real
                st.toast(f"Boa! +{ganho} XP em {q[1]}", icon="✅")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Errou!")
                # Salva Flashcard
                conn = conectar_db()
                conn.execute('INSERT INTO flashcards (questao_id, enunciado, resposta_certa, explicacao) VALUES (?,?,?,?)', (q[0], q[3], q[5], q[6]))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        if st.session_state[k] == q[5]:
            st.success("Correto!")
        else:
            st.error(f"Era a letra {q[5]}")
            st.write(q[6])
            
        if st.session_state.idx < total - 1:
            if st.button("Próxima"):
                st.session_state.idx += 1
                st.rerun()
        else:
            if st.button("Ver Resultado"):
                st.session_state.pagina = 'home'
                st.rerun()
                
# --- FLASHCARDS ---
elif st.session_state.pagina == 'flashcards':
    st.title("Revisão Espaçada")
    conn = conectar_db()
    cards = conn.execute("SELECT * FROM flashcards").fetchall()
    conn.close()
    
    if not cards:
        st.success("Nada para revisar hoje!")
        if st.button("Voltar"): st.session_state.pagina = 'home'; st.rerun()
    
    for c in cards:
        with st.expander(f"Revisar: {c[2]}"):
            st.write(f"**Resposta:** {c[3]}")
            st.write(f"**Explicação:** {c[4]}")
            if st.button("Aprendi!", key=f"del_{c[0]}"):
                conn = conectar_db()
                conn.execute("DELETE FROM flashcards WHERE id=?", (c[0],))
                conn.commit()
                st.rerun()
