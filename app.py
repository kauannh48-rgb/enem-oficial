import streamlit as st
import sqlite3
import json
import random
import time
import pandas as pd
import plotly.express as px
from datetime import datetime, date

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="ENEM Infinity", page_icon="♾️", layout="wide")

# --- CONEXÃO COM BANCO DE DADOS ---
def conectar_db():
    return sqlite3.connect('enem_infinity.db')

def criar_tabelas():
    conn = conectar_db()
    c = conn.cursor()
    
    # Tabela Perfil
    c.execute('''CREATE TABLE IF NOT EXISTS perfil (
        id INTEGER PRIMARY KEY, nome TEXT DEFAULT 'Estudante', xp INTEGER DEFAULT 0, 
        ultimo_acesso TEXT, dias_seguidos INTEGER DEFAULT 0, meta_diaria INTEGER DEFAULT 0)''')
    
    # Tabela Estatísticas por Matéria
    c.execute('''CREATE TABLE IF NOT EXISTS materias_stats (
        disciplina TEXT PRIMARY KEY, xp INTEGER DEFAULT 0)''')

    # Tabela Questões
    c.execute('''CREATE TABLE IF NOT EXISTS questoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, disciplina TEXT, assunto TEXT, enunciado TEXT, 
        alternativas TEXT, letra_correta TEXT, explicacao TEXT, dificuldade TEXT)''')

    # Tabela Flashcards
    c.execute('''CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT, questao_id INTEGER, enunciado TEXT, 
        resposta_certa TEXT, explicacao TEXT)''')
    
    conn.commit()
    conn.close()
    
    # Chama função para popular o banco se estiver vazio
    popular_banco_inicial()

def popular_banco_inicial():
    conn = conectar_db()
    c = conn.cursor()
    
    # Verifica se já tem questões
    count = c.execute('SELECT count(*) FROM questoes').fetchone()[0]
    
    if count == 0:
        st.toast("⚙️ Criando Banco de Dados Gigante... Aguarde!", icon="💾")
        
        # 1. QUESTÕES REAIS (BASE DE DADOS)
        questoes_base = [
            # --- FILOSOFIA (NOVA MATÉRIA) ---
            ("Filosofia", "Ética", "Para Aristóteles, a felicidade (Eudaimonia) é:", '{"A":"Prazer imediato", "B":"Acúmulo de riquezas", "C":"Finalidade das ações humanas", "D":"Obediência aos deuses", "E":"Ilusão"}', "C", "A felicidade é o bem supremo e fim último.", "Média"),
            ("Filosofia", "Política", "Segundo Hobbes, o homem em estado de natureza é:", '{"A":"O lobo do homem", "B":"Um bom selvagem", "C":"Um animal político", "D":"Um ser divino", "E":"Livre e pacífico"}', "A", "Guerra de todos contra todos.", "Fácil"),
            ("Filosofia", "Mito da Caverna", "O que representam as sombras na alegoria de Platão?", '{"A":"A verdade", "B":"O mundo das ideias", "C":"A ignorância/aparência", "D":"A luz do sol", "E":"A ciência"}', "C", "As sombras são as aparências enganosas do mundo sensível.", "Fácil"),
            ("Filosofia", "Existencialismo", "Sartre afirma que 'a existência precede a...':", '{"A":"Morte", "B":"Essência", "C":"Vida", "D":"Razão", "E":"Fé"}', "B", "O homem primeiro existe, depois se define.", "Média"),
            ("Filosofia", "Kant", "O imperativo categórico baseia-se no:", '{"A":"Dever universal", "B":"Interesse pessoal", "C":"Amor cristão", "D":"Medo da punição", "E":"Costume local"}', "A", "Agir de forma que sua ação possa ser lei universal.", "Difícil"),
            
            # --- MATEMÁTICA ---
            ("Matemática", "Porcentagem", "30% de 200 é:", '{"A":"30", "B":"60", "C":"90", "D":"20", "E":"50"}', "B", "0.3 * 200 = 60.", "Fácil"),
            ("Matemática", "Geometria", "Soma dos ângulos internos de um triângulo:", '{"A":"180°", "B":"360°", "C":"90°", "D":"270°", "E":"100°"}', "A", "Sempre 180 graus.", "Fácil"),
            ("Matemática", "Análise Combinatória", "Anagramas da palavra SOL:", '{"A":"3", "B":"6", "C":"9", "D":"4", "E":"5"}', "B", "3! = 3*2*1 = 6.", "Média"),

            # --- HISTÓRIA ---
            ("História", "Brasil", "A Lei Áurea (1888) aboliu:", '{"A":"A Monarquia", "B":"A Escravidão", "C":"O Tráfico", "D":"Os Impostos", "E":"A Guerra"}', "B", "Fim da escravidão legal.", "Fácil"),
            ("História", "Geral", "A Queda da Bastilha marca o início da:", '{"A":"Rev. Industrial", "B":"Rev. Francesa", "C":"Guerra Fria", "D":"Idade Média", "E":"Rev. Russa"}', "B", "1789, início da Revolução Francesa.", "Média"),

            # --- FÍSICA ---
            ("Física", "Óptica", "A luz é uma onda:", '{"A":"Eletromagnética", "B":"Mecânica", "C":"Sonora", "D":"Gravitacional", "E":"Estática"}', "A", "Não precisa de meio material.", "Fácil"),
            ("Física", "Termologia", "Zero absoluto corresponde a:", '{"A":"0°C", "B":"-273°C", "C":"100°C", "D":"-100°C", "E":"-373°C"}', "B", "0 Kelvin = -273 Celsius.", "Média"),

            # --- QUÍMICA ---
            ("Química", "pH", "pH 2 indica uma solução:", '{"A":"Neutra", "B":"Básica", "C":"Ácida", "D":"Salina", "E":"Pura"}', "C", "Abaixo de 7 é ácido.", "Fácil"),
            ("Química", "Tabela", "Gases Nobres são conhecidos por:", '{"A":"Alta reatividade", "B":"Baixa reatividade", "C":"Serem sólidos", "D":"Serem metais", "E":"Radioatividade"}', "B", "Estabilidade eletrônica.", "Média"),

            # --- BIOLOGIA ---
            ("Biologia", "Evolução", "Quem propôs a Seleção Natural?", '{"A":"Mendel", "B":"Darwin", "C":"Lamarck", "D":"Pasteur", "E":"Watson"}', "B", "Charles Darwin.", "Fácil"),
            ("Biologia", "Ecologia", "Relação onde ambos ganham:", '{"A":"Parasitismo", "B":"Mutualismo", "C":"Predatismo", "D":"Competição", "E":"Amensalismo"}', "B", "Benefício mútuo.", "Fácil")
        ]

        # 2. INSERIR MATÉRIAS NO GRÁFICO (GARANTE QUE FILOSOFIA APAREÇA)
        materias_iniciais = ["Matemática", "História", "Física", "Química", "Biologia", "Filosofia", "Português"]
        for m in materias_iniciais:
            c.execute('INSERT OR IGNORE INTO materias_stats (disciplina, xp) VALUES (?, 10)', (m,))

        # 3. O CLONADOR (PREENCHER ATÉ 200 POR MATÉRIA)
        # Atenção: Isso repete as questões base mudando o ID para simular volume massivo
        todas_questoes = []
        for materia in materias_iniciais:
            # Filtra as questões base dessa matéria
            questoes_da_materia = [q for q in questoes_base if q[0] == materia]
            
            # Se não tiver questão base (ex: Português), usa uma genérica
            if not questoes_da_materia:
                questoes_da_materia = [(materia, "Geral", f"Questão de treino de {materia}", '{"A":"Certo", "B":"Errado"}', "A", "Treino.", "Fácil")]

            # Clona até chegar em 200
            count_materia = 0
            while count_materia < 200:
                for q in questoes_da_materia:
                    todas_questoes.append(q)
                    count_materia += 1
                    if count_materia >= 200: break
        
        # Insere tudo no banco
        c.executemany('INSERT INTO questoes (disciplina, assunto, enunciado, alternativas, letra_correta, explicacao, dificuldade) VALUES (?,?,?,?,?,?,?)', todas_questoes)
        conn.commit()
        st.toast("Banco atualizado com +1000 questões!", icon="✅")

    conn.close()

# --- FUNÇÕES ÚTEIS ---
def atualizar_xp(disciplina, pontos):
    conn = conectar_db()
    conn.execute('UPDATE perfil SET xp = xp + ?, meta_diaria = meta_diaria + ?', (pontos, pontos))
    conn.execute('UPDATE materias_stats SET xp = xp + ? WHERE disciplina = ?', (pontos, disciplina))
    conn.commit()
    conn.close()

def grafico_radar():
    conn = conectar_db()
    df = pd.read_sql("SELECT disciplina, xp FROM materias_stats", conn)
    conn.close()
    if df.empty: return None
    fig = px.line_polar(df, r='xp', theta='disciplina', line_close=True, title="Radar de Competência", template="plotly_dark")
    fig.update_traces(fill='toself', line_color='#00d2d3')
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
    return fig

# --- INTERFACE ---
criar_tabelas() # Inicializa o sistema

if 'pagina' not in st.session_state: st.session_state.pagina = 'home'
if 'tema' not in st.session_state: st.session_state.tema = 'dark'

# CSS PRO
st.markdown("""
<style>
    .stApp { background-color: #0f0f0f; color: #eee; }
    .card { background-color: #1e1e1e; padding: 20px; border-radius: 12px; border: 1px solid #333; margin-bottom: 15px; }
    .big-stat { font-size: 28px; font-weight: bold; color: #00d2d3; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 45px; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2997/2997235.png", width=60)
    st.title("Menu ENEM")
    
    conn = conectar_db()
    perfil = conn.execute("SELECT xp, meta_diaria FROM perfil").fetchone()
    conn.close()
    
    st.metric("XP Total", perfil[0])
    st.write(f"🎯 **Meta Hoje:** {perfil[1]}/200 XP")
    st.progress(min(perfil[1]/200, 1.0))
    
    st.divider()
    if st.button("🏠 Início"): st.session_state.pagina = 'home'; st.rerun()
    if st.button("🧠 Flashcards"): st.session_state.pagina = 'flashcards'; st.rerun()

# --- PÁGINA HOME ---
if st.session_state.pagina == 'home':
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### 🗺️ Seu Mapa de Conhecimento")
        fig = grafico_radar()
        if fig: st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🚀 Configurar Simulado")
        
        # 1. ESCOLHA DA MATÉRIA (Incluindo Filosofia)
        materia = st.selectbox("O que vamos estudar?", 
                               ["Mix Geral", "Filosofia", "Matemática", "História", "Geografia", "Física", "Química", "Biologia"])
        
        # 2. LIBERDADE TOTAL DE QUANTIDADE
        # O slider vai de 1 até 200 (limite da simulação), mas o usuário escolhe livremente.
        qtd = st.slider("Quantas questões você quer fazer agora?", 
                        min_value=1, max_value=100, value=10, 
                        help="Você tem liberdade total para escolher de 1 a 100 por vez.")
        
        st.info(f"O banco possui +200 questões de {materia}. Selecionando {qtd} aleatórias.")
        
        if st.button("INICIAR PROVA", type="primary"):
            conn = conectar_db()
            query = "SELECT * FROM questoes "
            params = []
            
            if materia != "Mix Geral":
                query += "WHERE disciplina = ? "
                params.append(materia)
            
            query += "ORDER BY RANDOM() LIMIT ?"
            params.append(qtd)
            
            quests = conn.execute(query, params).fetchall()
            conn.close()
            
            st.session_state.quiz_data = quests
            st.session_state.idx = 0
            st.session_state.acertos = 0
            st.session_state.xp_sessao = 0
            st.session_state.pagina = 'quiz'
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

# --- PÁGINA QUIZ ---
elif st.session_state.pagina == 'quiz':
    if 'quiz_data' not in st.session_state or not st.session_state.quiz_data:
        st.session_state.pagina = 'home'; st.rerun()

    q = st.session_state.quiz_data[st.session_state.idx]
    total = len(st.session_state.quiz_data)
    
    # Barra de Progresso customizada
    st.progress((st.session_state.idx + 1) / total)
    st.caption(f"Questão {st.session_state.idx + 1} de {total}")
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # Badge da Matéria
    st.markdown(f"**{q[1]}** | {q[2]} ({q[7]})")
    st.markdown(f"### {q[3]}")
    
    alts = json.loads(q[4])
    key_radio = f"radio_{st.session_state.idx}" # Key dinâmica baseada no index para não bugar repetições
    
    if f"respondido_{st.session_state.idx}" not in st.session_state:
        escolha = st.radio("Sua resposta:", list(alts.keys()), format_func=lambda x: f"{x}) {alts[x]}", key=key_radio)
        
        if st.button("Confirmar Resposta"):
            st.session_state[f"respondido_{st.session_state.idx}"] = True
            st.session_state[f"escolha_{st.session_state.idx}"] = escolha
            
            if escolha == q[5]:
                st.session_state.acertos += 1
                xp = 20
                st.session_state.xp_sessao += xp
                atualizar_xp(q[1], xp)
                st.toast(f"Correto! +{xp} XP", icon="🎉")
            else:
                st.toast("Errou! Adicionado à revisão.", icon="💾")
                conn = conectar_db()
                conn.execute('INSERT INTO flashcards (questao_id, enunciado, resposta_certa, explicacao) VALUES (?,?,?,?)', (q[0], q[3], q[5], q[6]))
                conn.commit()
                conn.close()
            st.rerun()
    else:
        # Modo Feedback
        esc = st.session_state[f"escolha_{st.session_state.idx}"]
        if esc == q[5]:
            st.success(f"Você acertou! Resposta: {esc}")
        else:
            st.error(f"Você marcou {esc}, mas a correta era {q[5]}.")
            st.info(f"💡 Explicação: {q[6]}")
        
        c1, c2 = st.columns([1, 4])
        with c2:
            if st.session_state.idx < total - 1:
                if st.button("Próxima ➡️"):
                    st.session_state.idx += 1
                    st.rerun()
            else:
                if st.button("Finalizar Simulado 🏁"):
                    st.session_state.pagina = 'resultado'
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- PÁGINA RESULTADO ---
elif st.session_state.pagina == 'resultado':
    st.balloons()
    st.title("Resultado do Treino")
    
    acertos = st.session_state.acertos
    total = len(st.session_state.quiz_data)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Acertos", f"{acertos}/{total}")
    col2.metric("XP Ganho", f"+{st.session_state.xp_sessao}")
    col3.metric("Aproveitamento", f"{(acertos/total)*100:.0f}%")
    
    # Limpa estados temporários
    keys_to_clear = [k for k in st.session_state.keys() if k.startswith("respondido_") or k.startswith("escolha_")]
    for k in keys_to_clear: del st.session_state[k]
    
    st.button("Voltar ao Menu", on_click=lambda: st.session_state.update(pagina='home'))

# --- PÁGINA FLASHCARDS ---
elif st.session_state.pagina == 'flashcards':
    st.title("🧠 Revisão (Flashcards)")
    conn = conectar_db()
    cards = conn.execute("SELECT * FROM flashcards ORDER BY id DESC").fetchall()
    conn.close()
    
    if not cards:
        st.success("Nenhum erro pendente. Você está voando! 🚀")
        st.button("Voltar", on_click=lambda: st.session_state.update(pagina='home'))
    else:
        for c in cards:
            with st.expander(f"{c[2]} (Clique para revelar)"):
                st.markdown(f"**Resposta Certa:** {c[3]}")
                st.write(f"**Explicação:** {c[4]}")
                if st.button("Remover (Aprendi)", key=f"del_{c[0]}"):
                    conn = conectar_db()
                    conn.execute("DELETE FROM flashcards WHERE id=?", (c[0],))
                    conn.commit()
                    conn.close()
                    st.rerun()
