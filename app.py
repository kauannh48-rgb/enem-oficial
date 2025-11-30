import streamlit as st
import sqlite3
import json
import random
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Plataforma ENEM IA", layout="centered")

# --- FUNÇÕES DE BANCO DE DADOS ---
def conectar_db():
    return sqlite3.connect('enem_simulado.db')

def criar_tabelas():
    conn = conectar_db()
    cursor = conn.cursor()
    # Cria tabela de questões
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disciplina TEXT,
            enunciado TEXT,
            alternativas TEXT,
            letra_correta TEXT,
            explicacao TEXT,
            dificuldade TEXT
        )
    ''')
    # Cria tabela de resultados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            acertos INTEGER,
            total INTEGER
        )
    ''')
    
    # Se o banco estiver vazio, adiciona questões de exemplo
    cursor.execute('SELECT count(*) FROM questoes')
    if cursor.fetchone()[0] == 0:
        questoes_seed = [
            ("Matemática", "Um produto custava R$ 100 e teve aumento de 20%, depois desconto de 20%. Qual preço final?", 
             json.dumps({"A": "100", "B": "96", "C": "98", "D": "104", "E": "92"}), "B", "100 + 20% = 120. 120 - 20% (24) = 96.", "Média"),
            ("História", "Quem proclamou a independência do Brasil?", 
             json.dumps({"A": "D. Pedro II", "B": "D. Pedro I", "C": "Deodoro", "D": "Vargas", "E": "Lula"}), "B", "Foi D. Pedro I em 1822.", "Fácil"),
            ("Química", "Qual o símbolo do Ouro na tabela periódica?", 
             json.dumps({"A": "Ou", "B": "Ag", "C": "Au", "D": "Fe", "E": "O"}), "C", "Vem do latim Aurum.", "Média"),
            ("Física", "Qual a unidade de força no Sistema Internacional?", 
             json.dumps({"A": "Joule", "B": "Watt", "C": "Newton", "D": "Pascal", "E": "Volt"}), "C", "A unidade de força é o Newton (N).", "Fácil")
        ]
        cursor.executemany('INSERT INTO questoes (disciplina, enunciado, alternativas, letra_correta, explicacao, dificuldade) VALUES (?, ?, ?, ?, ?, ?)', questoes_seed)
        conn.commit()
    conn.close()

# --- INICIALIZAÇÃO ---
criar_tabelas()

# Controle de Sessão
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'home'
if 'acertos' not in st.session_state:
    st.session_state.acertos = 0

# --- TELA: HOME ---
if st.session_state.pagina == 'home':
    st.title("🎓 Plataforma de Estudos ENEM")
    st.write("Bem-vindo ao seu simulador inteligente.")
    st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🤖 Modo Treino")
        if st.button("🚀 Iniciar Simulado Rápido"):
            conn = conectar_db()
            cursor = conn.cursor()
            # Pega 3 questões aleatórias
            cursor.execute('SELECT * FROM questoes ORDER BY RANDOM() LIMIT 3')
            questoes = cursor.fetchall()
            conn.close()
            
            if not questoes:
                st.error("Erro: Banco de dados vazio.")
            else:
                st.session_state.questoes_atuais = questoes
                st.session_state.indice_q = 0
                st.session_state.acertos = 0
                st.session_state.pagina = 'quiz'
                st.rerun()
            
    with col2:
        st.subheader("📈 Desempenho")
        if st.button("Ver Histórico"):
            conn = conectar_db()
            df = conn.execute('SELECT data, acertos, total FROM resultados ORDER BY id DESC LIMIT 5').fetchall()
            conn.close()
            st.write("**Últimos Resultados:**")
            if not df:
                st.info("Nenhum simulado feito ainda.")
            for row in df:
                st.success(f"📅 {row[0]} | ✅ Acertos: {row[1]}/{row[2]}")

# --- TELA: QUIZ (RESPONDER QUESTÕES) ---
elif st.session_state.pagina == 'quiz':
    q_atual = st.session_state.questoes_atuais[st.session_state.indice_q]
    # Estrutura q_atual: (0:id, 1:disciplina, 2:enunciado, 3:alts, 4:correta, 5:expl, 6:dif)
    
    # Barra de progresso
    progresso = (st.session_state.indice_q + 1) / len(st.session_state.questoes_atuais)
    st.progress(progresso)
    
    st.caption(f"Questão {st.session_state.indice_q + 1} de {len(st.session_state.questoes_atuais)} | {q_atual[1]} | Dificuldade: {q_atual[6]}")
    st.markdown(f"### {q_atual[2]}")
    
    alternativas = json.loads(q_atual[3])
    
    # Formulário para evitar recarregamento antes da hora
    with st.form(key=f"form_q{q_atual[0]}"):
        opcao_escolhida = st.radio("Selecione a resposta:", list(alternativas.keys()), format_func=lambda x: f"{x}) {alternativas[x]}")
        botao_confirmar = st.form_submit_button("Confirmar Resposta")

    if botao_confirmar:
        if opcao_escolhida == q_atual[4]:
            st.balloons()
            st.success("✅ CORRETO! Muito bem.")
            st.session_state.acertos += 1
        else:
            st.error(f"❌ ERRADO. A resposta certa era letra {q_atual[4]}.")
            st.warning(f"💡 **Explicação do Professor:** {q_atual[5]}")
        
        # Botão para próxima questão (aparece fora do formulário)
        if st.session_state.indice_q < len(st.session_state.questoes_atuais) - 1:
            if st.button("Próxima Questão ➡️"):
                st.session_state.indice_q += 1
                st.rerun()
        else:
            if st.button("Ver Resultado Final 🏁"):
                conn = conectar_db()
                conn.execute('INSERT INTO resultados (data, acertos, total) VALUES (?, ?, ?)', 
                             (datetime.now().strftime("%d/%m %H:%M"), st.session_state.acertos, len(st.session_state.questoes_atuais)))
                conn.commit()
                conn.close()
                st.session_state.pagina = 'resultado'
                st.rerun()

# --- TELA: RESULTADO FINAL ---
elif st.session_state.pagina == 'resultado':
    st.title("🏁 Resultado do Simulado")
    
    total = len(st.session_state.questoes_atuais)
    acertos = st.session_state.acertos
    nota_tri = (acertos / total) * 1000
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Acertos", f"{acertos}/{total}")
    col2.metric("Nota Estimada", f"{nota_tri:.0f}")
    
    if acertos == total:
        st.success("PARABÉNS! Você gabaritou! 🏆")
    elif acertos > total/2:
        st.info("Bom trabalho! Continue estudando.")
    else:
        st.warning("Precisa estudar mais um pouco. Não desista! 💪")
    
    if st.button("Voltar ao Início"):
        st.session_state.pagina = 'home'
        st.rerun()
