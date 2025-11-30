import streamlit as st
import sqlite3
import json
import random
import time
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="ENEM Legends", page_icon="🏆", layout="wide")

# --- SISTEMA DE TÍTULOS E CONQUISTAS ---
TITULOS = {
    "Matemática": [
        (20, "Calculadora Humana 🧮"), (50, "Mente Brilhante 🧠"), (100, "Arquimedes Moderno 📐")
    ],
    "Física": [
        (20, "Curioso da Gravidade 🍎"), (50, "Mecânico Quântico ⚛️"), (100, "Herdeiro de Newton 🌌")
    ],
    "História": [
        (20, "Explorador do Passado 📜"), (50, "Historiador Real 🏛️"), (100, "Viajante do Tempo ⏳")
    ],
    "Química": [
        (20, "Alquimista Iniciante 🧪"), (50, "Mestre das Reações 💥"), (100, "Tabela Periódica Viva ☢️")
    ],
    "Biologia": [
        (20, "Observador da Vida 🌿"), (50, "Geneticista 🧬"), (100, "Darwinista 🦍")
    ],
    "Geral": [
        (0, "Novato"), (100, "Veterano"), (500, "Lenda do ENEM")
    ]
}

RANKS_PATENTE = {
    "Ferro": {"min": 0, "cor": "#95a5a6"},
    "Bronze": {"min": 100, "cor": "#cd7f32"},
    "Prata": {"min": 300, "cor": "#bdc3c7"},
    "Ouro": {"min": 600, "cor": "#f1c40f"},
    "Diamante": {"min": 1000, "cor": "#3498db"},
    "Lendário": {"min": 2000, "cor": "#9b59b6"}
}

# --- FUNÇÕES DE BANCO DE DADOS ---
def conectar_db():
    return sqlite3.connect('enem_social.db')

def criar_tabelas():
    conn = conectar_db()
    c = conn.cursor()
    
    # Tabela Perfil (Geral)
    c.execute('''CREATE TABLE IF NOT EXISTS perfil (
        id INTEGER PRIMARY KEY, nome TEXT DEFAULT 'Estudante', xp INTEGER DEFAULT 0)''')
    
    # Tabela XP por Matéria (Para os Títulos)
    c.execute('''CREATE TABLE IF NOT EXISTS materias_stats (
        disciplina TEXT PRIMARY KEY, xp INTEGER DEFAULT 0)''')

    # Tabela Amigos (Simulação)
    c.execute('''CREATE TABLE IF NOT EXISTS amigos (
        id INTEGER PRIMARY KEY, nome TEXT, xp INTEGER)''')
        
    c.execute('''CREATE TABLE IF NOT EXISTS questoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, disciplina TEXT, assunto TEXT, enunciado TEXT, 
        alternativas TEXT, letra_correta TEXT, explicacao TEXT, dificuldade TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT, questao_id INTEGER, enunciado TEXT, 
        resposta_certa TEXT, explicacao TEXT)''')
    
    # INICIALIZAÇÃO DO PERFIL
    c.execute('SELECT count(*) FROM perfil')
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO perfil (nome, xp) VALUES ('Eu (Você)', 0)")
        # Adiciona alguns rivais iniciais (Bots)
        c.execute("INSERT INTO amigos (nome, xp) VALUES ('Ana_Estudos', 150)")
        c.execute("INSERT INTO amigos (nome, xp) VALUES ('Joao_1000', 320)")
        
    # POPULA BANCO DE QUESTÕES (SEED SIMPLIFICADO PARA O CÓDIGO NÃO FICAR GIGANTE)
    # (Em produção, você teria centenas aqui. Mantive as principais para teste)
    c.execute('SELECT count(*) FROM questoes')
    if c.fetchone()[0] == 0:
        questoes_base = [
            ("Matemática", "Básica", "Quanto é 20% de 500?", '{"A":"50", "B":"100", "C":"150", "D":"200"}', "B", "10% é 50, logo 20% é 100.", "Fácil"),
            ("Física", "Cinemática", "Se v = 10m/s, quanto anda em 5s?", '{"A":"20m", "B":"50m", "C":"10m", "D":"100m"}', "B", "d = v.t -> 10 * 5 = 50.", "Fácil"),
            ("História", "Brasil", "Quem descobriu o Brasil?", '{"A":"Cabral", "B":"Colombo", "C":"Caminha", "D":"Lula"}', "A", "Pedro Álvares Cabral.", "Fácil"),
            ("Química", "Atomística", "Carga do elétron?", '{"A":"Positiva", "B":"Neutra", "C":"Negativa", "D":"Nula"}', "C", "Elétrons são negativos.", "Média"),
            ("Biologia", "Celular", "DNA fica onde?", '{"A":"Núcleo", "B":"Membrana", "C":"Golgi", "D":"Lisossomo"}', "A", "No núcleo.", "Fácil"),
            ("Matemática", "Geometria", "Area quadrado lado 3?", '{"A":"6", "B":"9", "C":"12", "D":"3"}', "B", "3x3=9.", "Fácil"),
            ("Física", "Dinâmica", "F=m.a é qual lei?", '{"A":"1ª Newton", "B":"2ª Newton", "C":"3ª Newton", "D":"Kepler"}', "B", "Princípio Fundamental.", "Média")
        ]
        # Multiplicando para ter volume
        for _ in range(3): 
            c.executemany('INSERT INTO questoes (disciplina, assunto, enunciado, alternativas, letra_correta, explicacao, dificuldade) VALUES (?,?,?,?,?,?,?)', questoes_base)
        conn.commit()
    conn.close()

# --- LÓGICA DE JOGO ---
def ganhar_xp(disciplina, quantidade):
    conn = conectar_db()
    # XP Geral
    conn.execute('UPDATE perfil SET xp = xp + ?', (quantidade,))
    
    # XP da Matéria
    check = conn.execute('SELECT xp FROM materias_stats WHERE disciplina = ?', (disciplina,)).fetchone()
    if check:
        conn.execute('UPDATE materias_stats SET xp = xp + ? WHERE disciplina = ?', (quantidade, disciplina))
    else:
        conn.execute('INSERT INTO materias_stats (disciplina, xp) VALUES (?, ?)', (disciplina, quantidade))
    
    # Simula evolução dos amigos (para eles não ficarem parados)
    if random.random() > 0.5:
        bot_xp = random.randint(5, 30)
        conn.execute('UPDATE amigos SET xp = xp + ? WHERE id = (SELECT id FROM amigos ORDER BY RANDOM() LIMIT 1)', (bot_xp,))
        
    conn.commit()
    conn.close()

def get_titulos_usuario():
    conn = conectar_db()
    stats = conn.execute('SELECT disciplina, xp FROM materias_stats').fetchall()
    conn.close()
    
    meus_titulos = []
    stats_dict = {disc: xp for disc, xp in stats}
    
    for materia, lista_conquistas in TITULOS.items():
        xp_atual = stats_dict.get(materia, 0)
        for xp_req, nome_titulo in lista_conquistas:
            if xp_atual >= xp_req:
                meus_titulos.append(f"{materia}: {nome_titulo}")
    
    if not meus_titulos:
        return ["Aspirante ao Saber"]
    return meus_titulos

# --- CSS E ESTILO ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    
    /* Card Ranking */
    .ranking-card {
        background-color: #1f2937; padding: 15px; border-radius: 10px;
        border-left: 5px solid #f1c40f; margin-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
    }
    
    /* Badge de Título */
    .badge {
        background-color: #374151; color: #60a5fa; padding: 5px 10px;
        border-radius: 15px; font-size: 12px; margin-right: 5px; border: 1px solid #60a5fa;
    }
    
    /* Botões */
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO ---
criar_tabelas()
if 'pagina' not in st.session_state: st.session_state.pagina = 'home'

# Dados do Usuário
conn = conectar_db()
perfil = conn.execute('SELECT xp, nome FROM perfil').fetchone()
xp_total = perfil[0]
nome_user = perfil[1]
conn.close()

# Calcula Patente Atual
patente_atual = "Ferro"
cor_patente = "#95a5a6"
for p, dados in RANKS_PATENTE.items():
    if xp_total >= dados['min']:
        patente_atual = p
        cor_patente = dados['cor']

# --- SIDEBAR: PERFIL E RANKING ---
with st.sidebar:
    st.markdown(f"<h1 style='color:{cor_patente}; text-align:center'>🛡️ {patente_atual}</h1>", unsafe_allow_html=True)
    st.progress(min((xp_total % 300) / 300, 1.0))
    st.caption(f"{xp_total} XP Total")
    
    st.divider()
    
    st.subheader("🏆 Leaderboard (Top 5)")
    # Busca ranking misturando usuário e amigos
    conn = conectar_db()
    ranking = []
    # Adiciona usuário
    ranking.append({"nome": nome_user, "xp": xp_total, "eu": True})
    # Adiciona amigos
    amigos = conn.execute("SELECT nome, xp FROM amigos").fetchall()
    for a in amigos:
        ranking.append({"nome": a[0], "xp": a[1], "eu": False})
    conn.close()
    
    # Ordena
    ranking = sorted(ranking, key=lambda x: x['xp'], reverse=True)
    
    for i, p in enumerate(ranking[:5]):
        icon = "🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else f"{i+1}º"
        bg = "#2c3e50" if p['eu'] else "#1f2937"
        border = "2px solid #f1c40f" if p['eu'] else "none"
        
        st.markdown(f"""
        <div style='background-color:{bg}; padding:10px; border-radius:8px; margin-bottom:5px; border:{border}; display:flex; justify-content:space-between;'>
            <span>{icon} <strong>{p['nome']}</strong></span>
            <span>{p['xp']} XP</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Adicionar Amigo
    novo_amigo = st.text_input("Adicionar Rival (Nome):")
    if st.button("➕ Adicionar"):
        if novo_amigo:
            conn = conectar_db()
            # Cria amigo com XP próximo ao do usuário para ter graça
            xp_rival = random.randint(max(0, xp_total - 100), xp_total + 100)
            conn.execute("INSERT INTO amigos (nome, xp) VALUES (?, ?)", (novo_amigo, xp_rival))
            conn.commit()
            conn.close()
            st.rerun()

# --- HOME ---
if st.session_state.pagina == 'home':
    st.title(f"Olá, {nome_user}!")
    
    # Títulos Conquistados
    meus_titulos = get_titulos_usuario()
    st.write("🏅 **Suas Conquistas:**")
    html_titulos = ""
    for t in meus_titulos:
        html_titulos += f"<span class='badge'>{t}</span>"
    st.markdown(html_titulos, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("⚔️ Escolha sua Batalha")
        disc_escolhida = st.selectbox("Matéria:", ["Mix Geral", "Matemática", "Física", "História", "Química", "Biologia"])
        
        if st.button("INICIAR DESAFIO", type="primary"):
            conn = conectar_db()
            filtro = "" if disc_escolhida == "Mix Geral" else f"WHERE disciplina = '{disc_escolhida}'"
            quests = conn.execute(f"SELECT * FROM questoes {filtro} ORDER BY RANDOM() LIMIT 5").fetchall()
            conn.close()
            
            if not quests:
                st.warning("Sem missões disponíveis nesta área ainda.")
            else:
                st.session_state.questoes = quests
                st.session_state.indice = 0
                st.session_state.acertos = 0
                st.session_state.xp_temp = 0
                st.session_state.pagina = 'quiz'
                st.rerun()

    with col2:
        st.info("💡 **Dica Competitiva:**\nConvide amigos para o ranking. Quem tiver mais XP no fim da semana paga o lanche! 🍔")
        if st.button("Ver Flashcards"):
            st.session_state.pagina = 'flashcards'
            st.rerun()

# --- QUIZ ---
elif st.session_state.pagina == 'quiz':
    q = st.session_state.questoes[st.session_state.indice]
    total = len(st.session_state.questoes)
    
    st.progress((st.session_state.indice + 1) / total)
    st.markdown(f"**{q[1]}** ({q[7]})")
    st.markdown(f"### {q[3]}")
    
    alts = json.loads(q[4])
    chave = f"rad_{q[0]}"
    
    if chave not in st.session_state:
        op = st.radio("Resposta:", list(alts.keys()), format_func=lambda x: f"{x}) {alts[x]}", key=f"radio_{q[0]}")
        if st.button("Responder"):
            st.session_state[chave] = op
            if op == q[5]:
                # Acertou
                ganho = 20 if q[7] == "Média" else 10
                st.session_state.xp_temp += ganho
                # Salva no banco (Mastery e Geral)
                ganhar_xp(q[1], ganho)
                st.toast(f"+{ganho} XP em {q[1]}!", icon="📈")
                st.session_state.acertos += 1
                time.sleep(1)
                st.rerun()
            else:
                st.toast("Errou! Adicionado aos Flashcards.", icon="💾")
                conn = conectar_db()
                conn.execute('INSERT INTO flashcards (questao_id, enunciado, resposta_certa, explicacao) VALUES (?,?,?,?)', (q[0], q[3], q[5], q[6]))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        # Feedback
        if st.session_state[chave] == q[5]:
            st.success("Correto! 🎉")
        else:
            st.error(f"Errado! Era {q[5]}.")
            st.write(q[6])
            
        if st.session_state.indice < total - 1:
            if st.button("Próxima"):
                st.session_state.indice += 1
                st.rerun()
        else:
            if st.button("Ver Resultados"):
                st.session_state.pagina = 'home'
                st.rerun()

# --- FLASHCARDS ---
elif st.session_state.pagina == 'flashcards':
    st.title("Cartas de Memória")
    conn = conectar_db()
    cards = conn.execute("SELECT * FROM flashcards").fetchall()
    conn.close()
    
    if not cards:
        st.success("Tudo limpo!")
        if st.button("Voltar"):
            st.session_state.pagina = 'home'
            st.rerun()
            
    for c in cards:
        with st.expander(f"{c[2]}"):
            st.write(f"**Resposta:** {c[3]}")
            st.write(f"**Explicação:** {c[4]}")
            if st.button("Já decorei!", key=f"del_{c[0]}"):
                conn = conectar_db()
                conn.execute("DELETE FROM flashcards WHERE id=?", (c[0],))
                conn.commit()
                conn.close()
                st.rerun()
