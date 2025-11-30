import streamlit as st
import sqlite3
import json
import random
import pandas as pd
from datetime import datetime
import time

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="ENEM Game", page_icon="🎮", layout="wide")

# --- SISTEMA DE RANKING E GAMIFICAÇÃO ---
RANKS = {
    "Ferro": {"min_xp": 0, "max_xp": 100, "icon": "🛡️", "cor": "#7f8c8d"},
    "Bronze": {"min_xp": 101, "max_xp": 300, "icon": "🥉", "cor": "#cd7f32"},
    "Prata": {"min_xp": 301, "max_xp": 600, "icon": "🥈", "cor": "#bdc3c7"},
    "Ouro": {"min_xp": 601, "max_xp": 1000, "icon": "🥇", "cor": "#f1c40f"},
    "Diamante": {"min_xp": 1001, "max_xp": 99999, "icon": "💎", "cor": "#3498db"}
}

def calcular_patente(xp):
    for nome, dados in RANKS.items():
        if dados["min_xp"] <= xp <= dados["max_xp"]:
            return nome, dados
    return "Diamante", RANKS["Diamante"]

# --- FUNÇÕES DE BANCO DE DADOS ---
def conectar_db():
    return sqlite3.connect('enem_game.db') # Novo nome para garantir base limpa

def criar_tabelas():
    conn = conectar_db()
    c = conn.cursor()
    
    # Tabela Perfil (Salva o XP do usuário)
    c.execute('''CREATE TABLE IF NOT EXISTS perfil (
        id INTEGER PRIMARY KEY, xp INTEGER DEFAULT 0, nivel INTEGER DEFAULT 1)''')
    
    # Inicializa perfil se não existir
    c.execute('SELECT count(*) FROM perfil')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO perfil (xp, nivel) VALUES (0, 1)')

    c.execute('''CREATE TABLE IF NOT EXISTS questoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, disciplina TEXT, assunto TEXT, enunciado TEXT, 
        alternativas TEXT, letra_correta TEXT, explicacao TEXT, dificuldade TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT, questao_id INTEGER, enunciado TEXT, 
        resposta_certa TEXT, explicacao TEXT)''')
    
    # --- SEED (BANCO DE QUESTÕES EXPANDIDO) ---
    c.execute('SELECT count(*) FROM questoes')
    if c.fetchone()[0] == 0:
        # Lista Gigante de Questões (Exemplo compactado)
        questoes_base = [
            # MATEMÁTICA (Fácil)
            ("Matemática", "Básica", "Quanto é 15% de 200?", '{"A":"20", "B":"30", "C":"40", "D":"25", "E":"35"}', "B", "10% é 20, 5% é 10. Total 30.", "Fácil"),
            ("Matemática", "Geometria", "Área de um quadrado de lado 4m?", '{"A":"16", "B":"12", "C":"8", "D":"20", "E":"24"}', "A", "4x4=16.", "Fácil"),
            # MATEMÁTICA (Média)
            ("Matemática", "Funções", "Raízes de x² - 5x + 6 = 0?", '{"A":"2 e 3", "B":"-2 e -3", "C":"1 e 6", "D":"-1 e -6", "E":"0 e 5"}', "A", "Soma 5, Produto 6 -> 2 e 3.", "Média"),
            ("Matemática", "Probabilidade", "Chance de tirar Cara em uma moeda?", '{"A":"25%", "B":"50%", "C":"75%", "D":"10%", "E":"100%"}', "B", "1 em 2 = 50%.", "Média"),
            # MATEMÁTICA (Difícil)
            ("Matemática", "Logaritmo", "Se log 2 = 0.3, qual log 8?", '{"A":"0.6", "B":"0.9", "C":"1.2", "D":"0.8", "E":"2.4"}', "B", "log 2³ = 3 * log 2 = 3 * 0.3 = 0.9.", "Difícil"),
            
            # PORTUGUÊS
            ("Português", "Gramática", "Qual palavra está escrita corretamente?", '{"A":"Exceção", "B":"Eceção", "C":"Essesão", "D":"Exseção", "E":"Ecceção"}', "A", "Exceção vem de exceto.", "Fácil"),
            ("Português", "Literatura", "Autor de Dom Casmurro?", '{"A":"Jorge Amado", "B":"Machado de Assis", "C":"Drummond", "D":"Alencar", "E":"Pessoa"}', "B", "Machado de Assis.", "Média"),
            ("Português", "Figuras", " 'O vento beijou meu rosto' é uma:", '{"A":"Metáfora", "B":"Prosopopeia", "C":"Antítese", "D":"Hipérbole", "E":"Pleonasmo"}', "B", "Atribuir ações humanas a seres inanimados.", "Difícil"),

            # HISTÓRIA
            ("História", "Brasil", "Quem descobriu o Brasil?", '{"A":"Cabral", "B":"Colombo", "C":"Caminha", "D":"Vespucci", "E":"Dias"}', "A", "Pedro Álvares Cabral em 1500.", "Fácil"),
            ("História", "Geral", "Causa principal da 1ª Guerra?", '{"A":"Morte de Franz Ferdinand", "B":"Invasão da Polônia", "C":"Revolução Russa", "D":"Queda da Bastilha", "E":"Pearl Harbor"}', "A", "Assassinato do Arquiduque.", "Média"),
            ("História", "Brasil Império", "O que foi a Noite das Garrafadas?", '{"A":"Festa imperial", "B":"Conflito entre brs e port", "C":"Revolta escrava", "D":"Guerra do Paraguai", "E":"Proclamação"}', "B", "Conflito que antecedeu a abdicação de D. Pedro I.", "Difícil"),

            # GEOGRAFIA
            ("Geografia", "Relevo", "Ponto mais alto do Brasil?", '{"A":"Pico da Bandeira", "B":"Pico da Neblina", "C":"Monte Roraima", "D":"Pão de Açúcar", "E":"Everest"}', "B", "Pico da Neblina (AM).", "Média"),
            ("Geografia", "População", "País mais populoso do mundo (2023)?", '{"A":"China", "B":"EUA", "C":"Índia", "D":"Brasil", "E":"Rússia"}', "C", "A Índia ultrapassou a China.", "Média"),
            
            # BIOLOGIA
            ("Biologia", "Genética", "O DNA fica no:", '{"A":"Citoplasma", "B":"Núcleo", "C":"Membrane", "D":"Lisossomo", "E":"Golgi"}', "B", "Núcleo celular.", "Fácil"),
            ("Biologia", "Ecologia", "Animal que come plantas e carne é:", '{"A":"Herbívoro", "B":"Carnívoro", "C":"Onívoro", "D":"Detritívoro", "E":"Produtor"}', "C", "Onívoro.", "Fácil"),
            
            # FÍSICA E QUÍMICA
            ("Física", "Mecânica", "Fórmula da Força?", '{"A":"F=m.a", "B":"F=m/a", "C":"F=m+a", "D":"F=v.t", "E":"F=E.c"}', "A", "Lei de Newton.", "Fácil"),
            ("Química", "Tabela", "Símbolo do Ferro?", '{"A":"Fe", "B":"F", "C":"Fr", "D":"Ir", "E":"Fi"}', "A", "Ferrum.", "Fácil"),
            ("Química", "Orgânica", "O carbono faz quantas ligações?", '{"A":"2", "B":"3", "C":"4", "D":"5", "E":"1"}', "C", "Tetravalente.", "Média")
        ]
        
        # Duplicando e variando para encher o banco (simulação de volume)
        c.executemany('INSERT INTO questoes (disciplina, assunto, enunciado, alternativas, letra_correta, explicacao, dificuldade) VALUES (?,?,?,?,?,?,?)', questoes_base)
        conn.commit()
    conn.close()

# --- LÓGICA DO JOGO (ENGINE) ---
def atualizar_xp(pontos):
    conn = conectar_db()
    c = conn.cursor()
    c.execute('UPDATE perfil SET xp = xp + ?', (pontos,))
    conn.commit()
    
    # Pega XP atualizado
    c.execute('SELECT xp FROM perfil')
    novo_xp = c.fetchone()[0]
    conn.close()
    return novo_xp

def get_perfil():
    conn = conectar_db()
    c = conn.cursor()
    c.execute('SELECT xp, nivel FROM perfil')
    dados = c.fetchone()
    conn.close()
    return dados # (xp, nivel)

def salvar_flashcard(q):
    conn = conectar_db()
    # Verifica duplicidade
    check = conn.execute('SELECT id FROM flashcards WHERE questao_id = ?', (q[0],)).fetchone()
    if not check:
        conn.execute('INSERT INTO flashcards (questao_id, enunciado, resposta_certa, explicacao) VALUES (?,?,?,?)', 
                     (q[0], q[3], q[5], q[6]))
        conn.commit()
    conn.close()

# --- INTERFACE ---
criar_tabelas()
if 'pagina' not in st.session_state: st.session_state.pagina = 'home'

# Carregar dados do Jogador
xp_atual, nivel_atual = get_perfil()
nome_patente, dados_patente = calcular_patente(xp_atual)

# --- CSS GAMEFICADO ---
st.markdown(f"""
<style>
    .stApp {{ background-color: #1e272e; color: white; }}
    .css-1d391kg {{ background-color: #2c3e50; }}
    
    /* Card da Questão */
    .game-card {{
        background-color: #2c3e50;
        border: 2px solid {dados_patente['cor']};
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 0 15px {dados_patente['cor']}40;
        margin-bottom: 20px;
    }}
    
    /* Botões */
    .stButton>button {{
        background: linear-gradient(to right, #3498db, #2980b9);
        border: none;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        height: 50px;
        transition: transform 0.2s;
    }}
    .stButton>button:hover {{
        transform: scale(1.02);
    }}
    
    /* Barra de XP Customizada */
    .xp-container {{
        width: 100%;
        background-color: #555;
        border-radius: 10px;
        margin-top: 5px;
    }}
    .xp-bar {{
        width: {(xp_atual / dados_patente['max_xp']) * 100}%;
        height: 10px;
        background-color: {dados_patente['cor']};
        border-radius: 10px;
        transition: width 0.5s;
    }}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (PERFIL DO JOGADOR) ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; font-size: 60px;'>{dados_patente['icon']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; color: {dados_patente['cor']};'>{nome_patente}</h2>", unsafe_allow_html=True)
    
    st.write(f"**XP Total:** {xp_atual}")
    # Barra de XP Visual
    st.markdown(f"""
    <div class='xp-container'>
        <div class='xp-bar'></div>
    </div>
    <p style='font-size: 12px; text-align: right;'>Próximo Rank: {dados_patente['max_xp']} XP</p>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    if st.button("🏠 Lobby Principal"):
        st.session_state.pagina = 'home'
        st.rerun()
    if st.button("⚔️ Missões (Flashcards)"):
        st.session_state.pagina = 'flashcards'
        st.rerun()

# --- PÁGINA: HOME (LOBBY) ---
if st.session_state.pagina == 'home':
    st.title("🎮 ENEM Quest: A Jornada")
    st.write("Complete simulados para ganhar XP e subir de patente!")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<div class='game-card'>", unsafe_allow_html=True)
        st.subheader("🚀 Iniciar Missão")
        
        # Seletor de Matéria
        disciplina = st.selectbox("Escolha o Campo de Batalha:", 
                                  ["Todas as Matérias", "Matemática", "Português", "História", "Geografia", "Biologia", "Física", "Química"])
        
        if st.button("COMEÇAR BATALHA", type="primary"):
            conn = conectar_db()
            
            # LÓGICA ADAPTATIVA (DIFICULDADE BASEADA NO RANK)
            # Se for Ferro/Bronze (Iniciante): 80% Fáceis, 20% Médias
            # Se for Prata (Intermediário): 50% Médias, 30% Fáceis, 20% Difíceis
            # Se for Ouro+ (Avançado): 50% Difíceis, 50% Médias
            
            dificuldade_foco = "Fácil"
            if nome_patente in ["Prata"]: dificuldade_foco = "Média"
            if nome_patente in ["Ouro", "Diamante"]: dificuldade_foco = "Difícil"
            
            # Query Híbrida: Tenta pegar questões do nível do usuário, mas mistura um pouco
            filtro_disc = "" if disciplina == "Todas as Matérias" else f"AND disciplina = '{disciplina}'"
            
            # Pega 5 questões focadas no nível + 2 aleatórias para surpresa
            q1 = conn.execute(f"SELECT * FROM questoes WHERE dificuldade = '{dificuldade_foco}' {filtro_disc} ORDER BY RANDOM() LIMIT 4").fetchall()
            q2 = conn.execute(f"SELECT * FROM questoes WHERE dificuldade != '{dificuldade_foco}' {filtro_disc} ORDER BY RANDOM() LIMIT 2").fetchall()
            
            questoes_finais = q1 + q2
            random.shuffle(questoes_finais)
            
            if not questoes_finais:
                 # Fallback se não achar questões específicas
                 questoes_finais = conn.execute(f"SELECT * FROM questoes ORDER BY RANDOM() LIMIT 5").fetchall()

            conn.close()
            
            st.session_state.questoes = questoes_finais
            st.session_state.indice = 0
            st.session_state.acertos = 0
            st.session_state.xp_ganho = 0
            st.session_state.pagina = 'quiz'
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.info(f"💡 **Dica de Jogo:**\nVocê está no rank **{nome_patente}**.\n\nQuestões Fáceis valem **10 XP**\nMédias valem **20 XP**\nDifíceis valem **50 XP**.")

# --- PÁGINA: QUIZ (BATALHA) ---
elif st.session_state.pagina == 'quiz':
    if 'questoes' not in st.session_state or not st.session_state.questoes:
        st.session_state.pagina = 'home'
        st.rerun()
        
    q = st.session_state.questoes[st.session_state.indice]
    total = len(st.session_state.questoes)
    
    # Barra de Progresso da Missão
    st.progress((st.session_state.indice + 1) / total, text=f"Questão {st.session_state.indice + 1}/{total}")
    
    # Card da Questão
    st.markdown("<div class='game-card'>", unsafe_allow_html=True)
    
    # Badge de Dificuldade
    cor_dif = "#2ecc71" if q[7] == "Fácil" else "#f1c40f" if q[7] == "Média" else "#e74c3c"
    st.markdown(f"<span style='background-color:{cor_dif}; padding: 5px 10px; border-radius: 5px; font-size: 12px; font-weight: bold;'>{q[7].upper()}</span> **{q[1]}**", unsafe_allow_html=True)
    
    st.markdown(f"### {q[3]}")
    
    alts = json.loads(q[4])
    chave = f"q_{q[0]}"
    
    # Se ainda não respondeu
    if chave not in st.session_state:
        opcao = st.radio("Sua resposta:", list(alts.keys()), format_func=lambda x: f"{x}) {alts[x]}", key=f"radio_{q[0]}")
        
        if st.button("ATACAR (Responder) ⚔️"):
            st.session_state[chave] = opcao # Marca que respondeu
            
            if opcao == q[5]:
                # Acertou: Calcula XP
                xp_base = 10 if q[7] == "Fácil" else 20 if q[7] == "Média" else 50
                st.session_state.xp_ganho += xp_base
                atualizar_xp(xp_base)
                st.session_state.acertos += 1
                st.toast(f"ACERTO CRÍTICO! +{xp_base} XP", icon="🔥")
                time.sleep(1) # Delay dramático
                st.rerun()
            else:
                # Errou
                st.toast("DANO SOFRIDO! (Errou)", icon="💔")
                salvar_flashcard(q)
                st.rerun()
                
    else:
        # Já respondeu, mostra feedback
        escolha = st.session_state[chave]
        if escolha == q[5]:
            st.success(f"Correto! A resposta era {q[5]}.")
        else:
            st.error(f"Errou! Você marcou {escolha}, mas era {q[5]}.")
            st.info(f"📜 **Sábio diz:** {q[6]}")
        
        # Botão Próximo
        if st.session_state.indice < total - 1:
            if st.button("Próximo Desafio ➡️"):
                st.session_state.indice += 1
                st.rerun()
        else:
            if st.button("Finalizar Missão 🏁"):
                st.session_state.pagina = 'resultado'
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# --- PÁGINA: RESULTADO (DEBRIEFING) ---
elif st.session_state.pagina == 'resultado':
    st.balloons()
    st.title("Missão Cumprida!")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Inimigos Derrotados (Acertos)", st.session_state.acertos)
    c2.metric("XP Obtido", f"+{st.session_state.xp_ganho}", delta_color="normal")
    
    # Verifica se subiu de rank
    novo_xp, _ = get_perfil()
    novo_rank, _ = calcular_patente(novo_xp)
    
    st.markdown(f"""
    <div style='background-color: #27ae60; padding: 20px; border-radius: 10px; text-align: center;'>
        <h2>XP TOTAL ATUAL: {novo_xp}</h2>
        <h3>Patente: {novo_rank}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Voltar ao Lobby"):
        st.session_state.pagina = 'home'
        st.rerun()

# --- PÁGINA: FLASHCARDS (TREINO) ---
elif st.session_state.pagina == 'flashcards':
    st.title("⚔️ Campo de Treino (Flashcards)")
    st.write("Revise seus erros para ficar mais forte.")
    
    conn = conectar_db()
    cards = conn.execute("SELECT * FROM flashcards").fetchall()
    conn.close()
    
    if not cards:
        st.success("Nenhum erro pendente! Você está imbatível.")
        if st.button("Voltar"):
            st.session_state.pagina = 'home'
            st.rerun()
    else:
        for card in cards:
            with st.container():
                st.markdown(f"<div class='game-card'>**Revisão:** {card[2]}</div>", unsafe_allow_html=True)
                with st.expander("Ver Resposta"):
                    st.write(f"Correta: {card[3]}")
                    st.write(f"Explicação: {card[4]}")
                    if st.button("Já dominei essa!", key=f"del_{card[0]}"):
                        c2 = conectar_db()
                        c2.execute("DELETE FROM flashcards WHERE id = ?", (card[0],))
                        c2.commit()
                        c2.close()
                        st.rerun()
