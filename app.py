import streamlit as st
import sqlite3
import json
import random
import pandas as pd # Vamos usar pandas para gráficos bonitos
from datetime import datetime

# --- CONFIGURAÇÃO VISUAL DA PÁGINA ---
st.set_page_config(
    page_title="ENEM Master",
    page_icon="🎓",
    layout="wide", # Layout mais largo (tela cheia)
    initial_sidebar_state="expanded"
)

# --- CSS PERSONALIZADO (A MÁGICA DO DESIGN) ---
st.markdown("""
<style>
    /* Estilo dos Botões */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    /* Caixa da Questão */
    .stAlert {
        border-radius: 10px;
    }
    /* Título Principal */
    h1 {
        color: #2E86C1;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE BANCO DE DADOS ---
def conectar_db():
    return sqlite3.connect('enem_simulado.db')

def criar_tabelas():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disciplina TEXT, enunciado TEXT, alternativas TEXT,
            letra_correta TEXT, explicacao TEXT, dificuldade TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT, acertos INTEGER, total INTEGER
        )
    ''')
    
    # Seed (Dados iniciais)
    cursor.execute('SELECT count(*) FROM questoes')
    if cursor.fetchone()[0] == 0:
        questoes_seed = [
            ("Matemática", "Um produto custava R$ 100 e teve aumento de 20%, depois desconto de 20%. Qual preço final?", 
             json.dumps({"A": "100", "B": "96", "C": "98", "D": "104", "E": "92"}), "B", "100 + 20% = 120. 120 - 20% (24) = 96.", "Média"),
            ("História", "Quem proclamou a independência do Brasil?", 
             json.dumps({"A": "D. Pedro II", "B": "D. Pedro I", "C": "Deodoro", "D": "Vargas", "E": "Lula"}), "B", "Foi D. Pedro I em 1822.", "Fácil"),
            ("Química", "Qual o símbolo do Ouro na tabela periódica?", 
             json.dumps({"A": "Ou", "B": "Ag", "C": "Au", "D": "Fe", "E": "O"}), "C", "Vem do latim Aurum.", "Média"),
            ("Física", "Qual a fórmula da velocidade média?", 
             json.dumps({"A": "Vm = d/t", "B": "Vm = m.a", "C": "Vm = m.g", "D": "Vm = d.t", "E": "Vm = t/d"}), "A", "Velocidade é a distância dividida pelo tempo.", "Fácil"),
            ("Biologia", "Qual a organela responsável pela respiração celular?", 
             json.dumps({"A": "Ribossomo", "B": "Mitocôndria", "C": "Lisossomo", "D": "Golgi", "E": "Núcleo"}), "B", "A mitocôndria produz energia (ATP).", "Média")
        ]
        cursor.executemany('INSERT INTO questoes (disciplina, enunciado, alternativas, letra_correta, explicacao, dificuldade) VALUES (?, ?, ?, ?, ?, ?)', questoes_seed)
        conn.commit()
    conn.close()

# --- BARRA LATERAL (SIDEBAR) ---
def mostrar_sidebar():
    with st.sidebar:
        st.header("👤 Perfil do Aluno")
        st.info("Status: Estudante Focado 🚀")
        
        st.divider()
        st.subheader("📜 Histórico Recente")
        
        conn = conectar_db()
        try:
            df = pd.read_sql_query('SELECT data, acertos, total FROM resultados ORDER BY id DESC LIMIT 5', conn)
            if not df.empty:
                # Mostra uma tabela limpa sem index
                st.dataframe(df, hide_index=True, use_container_width=True)
                
                # Cálculo rápido de média
                total_questoes = df['total'].sum()
                total_acertos = df['acertos'].sum()
                if total_questoes > 0:
                    media = (total_acertos / total_questoes) * 100
                    st.metric("Sua Precisão Global", f"{media:.1f}%")
            else:
                st.write("Nenhum simulado ainda.")
        except:
            st.write("Carregando histórico...")
        finally:
            conn.close()
            
        st.divider()
        st.caption("Desenvolvido com Python & Streamlit")

# --- INICIALIZAÇÃO ---
criar_tabelas()
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'home'

mostrar_sidebar()

# --- TELA: HOME ---
if st.session_state.pagina == 'home':
    # Cabeçalho bonito
    col_a, col_b = st.columns([1, 4])
    with col_a:
        st.image("https://cdn-icons-png.flaticon.com/512/3407/3407024.png", width=100)
    with col_b:
        st.title("Plataforma ENEM Master")
        st.write("Sua jornada para a universidade começa aqui.")

    st.divider()

    # Cards de Ação (Usando colunas para organizar)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        with st.container(border=True):
            st.subheader("📝 Simulado Rápido")
            st.write("3 questões aleatórias para testar conhecimentos.")
            if st.button("Começar Agora", type="primary"):
                conn = conectar_db()
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM questoes ORDER BY RANDOM() LIMIT 3')
                st.session_state.questoes_atuais = cursor.fetchall()
                conn.close()
                st.session_state.indice_q = 0
                st.session_state.acertos = 0
                st.session_state.respostas_usuario = {}
                st.session_state.pagina = 'quiz'
                st.rerun()

    with c2:
        with st.container(border=True):
            st.subheader("📚 Revisão")
            st.write("Veja questões que você errou anteriormente.")
            st.button("Em Breve", disabled=True)

    with c3:
        with st.container(border=True):
            st.subheader("🏆 Ranking")
            st.write("Compare seu desempenho com outros alunos.")
            st.button("Em Breve", disabled=True)

# --- TELA: QUIZ ---
elif st.session_state.pagina == 'quiz':
    if 'questoes_atuais' not in st.session_state or not st.session_state.questoes_atuais:
        st.session_state.pagina = 'home'
        st.rerun()

    q_atual = st.session_state.questoes_atuais[st.session_state.indice_q]
    total_q = len(st.session_state.questoes_atuais)
    
    # Barra de Progresso no Topo
    st.progress((st.session_state.indice_q) / total_q, text=f"Questão {st.session_state.indice_q + 1} de {total_q}")
    
    # Layout da Questão em um "Container"
    with st.container(border=True):
        # Cabeçalho da questão (Disciplina e Dificuldade)
        c_topo1, c_topo2 = st.columns([3, 1])
        with c_topo1:
            st.markdown(f"**Disciplina:** {q_atual[1]}")
        with c_topo2:
            cor_badge = "orange" if q_atual[6] == "Média" else "green" if q_atual[6] == "Fácil" else "red"
            st.markdown(f":{cor_badge}[{q_atual[6]}]")
        
        st.divider()
        
        # Enunciado (Fonte maior)
        st.markdown(f"### {q_atual[2]}")
        
        alternativas = json.loads(q_atual[3])
        chave_radio = f"radio_{q_atual[0]}"
        
        # Opções
        opcao = st.radio(
            "Selecione a alternativa:", 
            list(alternativas.keys()), 
            format_func=lambda x: f"{x}) {alternativas[x]}",
            key=chave_radio
        )

    # Botão de Ação (Abaixo do card)
    col_btn1, col_btn2 = st.columns([1, 2])
    
    with col_btn2:
        if st.button("✅ Confirmar Resposta", type="primary"):
            if opcao == q_atual[4]:
                st.toast("Resposta Correta!", icon="🎉") # Notificação pop-up
                if chave_radio not in st.session_state.respostas_usuario:
                     st.session_state.acertos += 1
                     st.session_state.respostas_usuario[chave_radio] = True
                
                # Pula automático após pequeno delay (simulado)
                if st.session_state.indice_q < total_q - 1:
                    st.session_state.indice_q += 1
                    st.rerun()
                else:
                    # Fim do quiz
                    conn = conectar_db()
                    conn.execute('INSERT INTO resultados (data, acertos, total) VALUES (?, ?, ?)', 
                                 (datetime.now().strftime("%d/%m %H:%M"), st.session_state.acertos, total_q))
                    conn.commit()
                    conn.close()
                    st.session_state.pagina = 'resultado'
                    st.rerun()
            else:
                st.error(f"❌ Errado! A resposta certa era {q_atual[4]}.")
                with st.expander("💡 Ver Explicação do Professor"):
                    st.write(q_atual[5])
                
                # Botão para avançar manual se errou
                if st.button("Continuar ➡️"):
                     if st.session_state.indice_q < total_q - 1:
                        st.session_state.indice_q += 1
                        st.rerun()
                     else:
                        st.session_state.pagina = 'resultado'
                        st.rerun()

    with col_btn1:
        if st.button("Sair"):
            st.session_state.pagina = 'home'
            st.rerun()

# --- TELA: RESULTADO ---
elif st.session_state.pagina == 'resultado':
    st.balloons()
    
    # Centralizar resultado
    st.markdown("<h1 style='text-align: center;'>Resultado do Simulado</h1>", unsafe_allow_html=True)
    
    acertos = st.session_state.acertos
    total = len(st.session_state.questoes_atuais)
    nota = (acertos / total) * 1000
    
    # Métricas Grandes
    c1, c2, c3 = st.columns(3)
    c1.metric("Acertos", f"{acertos}", f"de {total}")
    c2.metric("Nota TRI", f"{nota:.0f}", delta_color="normal")
    c3.metric("Aproveitamento", f"{(acertos/total)*100:.0f}%")
    
    st.divider()
    
    # Feedback Visual
    if nota > 700:
        st.success("🌟 Desempenho Incrível! Você está pronto.")
    elif nota > 400:
        st.warning("⚠️ Bom começo, mas vamos revisar as matérias.")
    else:
        st.error("🚨 Atenção! Precisamos focar na base.")
        
    st.button("🏠 Voltar ao Início", on_click=lambda: st.session_state.update(pagina='home'), type="primary")
