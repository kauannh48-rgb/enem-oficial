import streamlit as st
import sqlite3
import json
import random
import pandas as pd
from datetime import datetime

# --- LISTAS DE CONTEÚDO ---
FRASES_MOTIVACIONAIS = [
    "Acredite: você é capaz de coisas incríveis! 🌟",
    "Um passo de cada vez. O importante é não parar. 🚀",
    "O erro é apenas um degrau para o acerto. Respire e tente de novo. 💙",
    "Seu potencial é infinito. Confie no seu processo.",
    "Você não está atrasado, você está no seu próprio tempo. ⏳",
    "A educação é a arma mais poderosa para mudar o mundo (e o seu futuro). 🌍"
]

# Configurações dos Temas
TEMAS = {
    "Padrão (Azul)": {
        "primary": "#2E86C1", "bg": "#FFFFFF", "text": "#000000", "icon": "🎓",
        "msg": "Vamos estudar!"
    },
    "Hogwarts (Mágico)": {
        "primary": "#7F0909", "bg": "#F5F5DC", "text": "#2C1705", "icon": "⚡", 
        "msg": "A magia do conhecimento espera por você!"
    },
    "Pride (Inclusivo)": {
        "primary": "#FF0080", "bg": "#FFF0F5", "text": "#333333", "icon": "🌈",
        "msg": "Seja você, estude do seu jeito! Todo amor é bem-vindo."
    },
    "Zen (Foco/Atípico)": {
        "primary": "#4B6E59", "bg": "#E8F5E9", "text": "#1B2E21", "icon": "🌿",
        "msg": "Respire. Foco. Calma. Você consegue."
    }
}

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Plataforma ENEM", page_icon="🎓", layout="wide")

# --- FUNÇÕES ---
def conectar_db():
    return sqlite3.connect('enem_simulado.db')

def criar_tabelas():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, disciplina TEXT, enunciado TEXT, 
            alternativas TEXT, letra_correta TEXT, explicacao TEXT, dificuldade TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, acertos INTEGER, total INTEGER)''')
    
    # Verifica se precisa popular (Seed)
    cursor.execute('SELECT count(*) FROM questoes')
    if cursor.fetchone()[0] == 0:
        questoes_seed = [
            ("Matemática", "Se um bruxo compra 3 varinhas por R$ 30 cada e ganha 10% de desconto, quanto ele paga?", 
             json.dumps({"A": "R$ 80", "B": "R$ 81", "C": "R$ 90", "D": "R$ 85", "E": "R$ 75"}), "B", "3 x 30 = 90. 10% de 90 é 9. 90 - 9 = 81.", "Fácil"),
            ("História", "A Revolta da Chibata (1910) lutava contra o quê?", 
             json.dumps({"A": "A monarquia", "B": "Castigos físicos na Marinha", "C": "A escravidão", "D": "O aumento de impostos", "E": "A falta de magia"}), "B", "Liderada por João Cândido, lutava contra castigos corporais.", "Média"),
            ("Biologia", "O que diferencia uma célula vegetal de uma animal?", 
             json.dumps({"A": "A presença de mitocôndria", "B": "O DNA", "C": "A parede celular e cloroplastos", "D": "O núcleo", "E": "O tamanho"}), "C", "Células vegetais têm parede rígida e fazem fotossíntese.", "Média")
        ]
        cursor.executemany('INSERT INTO questoes (disciplina, enunciado, alternativas, letra_correta, explicacao, dificuldade) VALUES (?, ?, ?, ?, ?, ?)', questoes_seed)
        conn.commit()
    conn.close()

criar_tabelas()

# Inicializa variaveis de sessão
if 'pagina' not in st.session_state: st.session_state.pagina = 'home'
if 'tema_escolhido' not in st.session_state: st.session_state.tema_escolhido = "Padrão (Azul)"
if 'fonte_dislexia' not in st.session_state: st.session_state.fonte_dislexia = False
if 'msg_do_dia' not in st.session_state: st.session_state.msg_do_dia = random.choice(FRASES_MOTIVACIONAIS)

# --- SIDEBAR (PERSONALIZAÇÃO) ---
with st.sidebar:
    st.title("⚙️ Personalização")
    
    # Seletor de Tema
    novo_tema = st.selectbox("Escolha seu Estilo:", list(TEMAS.keys()), index=list(TEMAS.keys()).index(st.session_state.tema_escolhido))
    if novo_tema != st.session_state.tema_escolhido:
        st.session_state.tema_escolhido = novo_tema
        st.rerun()

    # Acessibilidade
    st.markdown("---")
    st.subheader("♿ Acessibilidade")
    if st.toggle("Fonte para Dislexia (OpenDyslexic)", value=st.session_state.fonte_dislexia):
        st.session_state.fonte_dislexia = True
    else:
        st.session_state.fonte_dislexia = False
        
    st.markdown("---")
    st.info(f"💡 **Mensagem do dia:**\n\n{st.session_state.msg_do_dia}")

# --- APLICAÇÃO DO ESTILO (CSS MÁGICO) ---
tema_atual = TEMAS[st.session_state.tema_escolhido]
fonte_css = "Comic Sans MS, sans-serif" if st.session_state.fonte_dislexia else "sans-serif"

st.markdown(f"""
<style>
    /* Aplica o fundo e a fonte */
    .stApp {{
        background-color: {tema_atual['bg']};
        color: {tema_atual['text']};
        font-family: {fonte_css} !important;
    }}
    /* Botões */
    .stButton>button {{
        background-color: {tema_atual['primary']};
        color: white;
        border-radius: 12px;
        border: none;
        height: 50px;
        font-weight: bold;
        width: 100%;
    }}
    /* Títulos */
    h1, h2, h3 {{
        color: {tema_atual['primary']} !important;
        font-family: {fonte_css} !important;
    }}
    /* Textos */
    p, li, label {{
        color: {tema_atual['text']};
        font-family: {fonte_css} !important;
        font-size: 18px !important; /* Aumenta letra para facilitar leitura */
    }}
</style>
""", unsafe_allow_html=True)

# --- TELA HOME ---
if st.session_state.pagina == 'home':
    col_logo, col_titulo = st.columns([1, 5])
    with col_logo:
        st.markdown(f"<h1 style='font-size: 60px;'>{tema_atual['icon']}</h1>", unsafe_allow_html=True)
    with col_titulo:
        st.title("Plataforma ENEM Inclusiva")
        st.markdown(f"*{tema_atual['msg']}*")
    
    st.markdown("---")
    
    # Botão Principal Gigante
    if st.button("🚀 INICIAR SIMULADO AGORA", type="primary"):
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

    st.markdown("<br>", unsafe_allow_html=True) # Espaço
    
    # Botões extras (Com KEYS únicas para corrigir o erro)
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.subheader("📚 Meus Erros")
            st.write("Revise o que precisa melhorar.")
            st.button("Em Breve", disabled=True, key="btn_revisao_erro") # KEY ÚNICA AQUI
    with c2:
        with st.container(border=True):
            st.subheader("🏆 Conquistas")
            st.write("Veja suas medalhas e progresso.")
            st.button("Em Breve", disabled=True, key="btn_ranking_top") # KEY ÚNICA AQUI

# --- TELA QUIZ ---
elif st.session_state.pagina == 'quiz':
    if not st.session_state.get('questoes_atuais'):
        st.session_state.pagina = 'home'
        st.rerun()
        
    q_atual = st.session_state.questoes_atuais[st.session_state.indice_q]
    total_q = len(st.session_state.questoes_atuais)
    
    st.progress((st.session_state.indice_q) / total_q)
    st.subheader(f"Questão {st.session_state.indice_q + 1} de {total_q}")
    
    with st.container(border=True):
        st.markdown(f"**{q_atual[1]}** | Nível: {q_atual[6]}")
        st.markdown(f"### {q_atual[2]}")
        
        alternativas = json.loads(q_atual[3])
        chave_radio = f"radio_{q_atual[0]}"
        
        opcao = st.radio("Sua resposta:", list(alternativas.keys()), 
                        format_func=lambda x: f"{x}) {alternativas[x]}", key=chave_radio)
        
    col_b1, col_b2 = st.columns([1, 2])
    with col_b2:
        if st.button("CONFIRMAR RESPOSTA", key="btn_confirma"):
            if opcao == q_atual[4]:
                st.toast("Parabéns! Você acertou! 🎉")
                if chave_radio not in st.session_state.respostas_usuario:
                     st.session_state.acertos += 1
                     st.session_state.respostas_usuario[chave_radio] = True
                
                if st.session_state.indice_q < total_q - 1:
                    st.session_state.indice_q += 1
                    st.rerun()
                else:
                    # Salva resultado
                    conn = conectar_db()
                    conn.execute('INSERT INTO resultados (data, acertos, total) VALUES (?, ?, ?)', 
                                 (datetime.now().strftime("%d/%m %H:%M"), st.session_state.acertos, total_q))
                    conn.commit()
                    conn.close()
                    st.session_state.pagina = 'resultado'
                    st.rerun()
            else:
                st.error(f"Poxa, não foi dessa vez. A correta é a letra {q_atual[4]}.")
                with st.expander("Ver explicação simples"):
                    st.write(q_atual[5])
                
                if st.button("Continuar", key="btn_prox_erro"):
                     if st.session_state.indice_q < total_q - 1:
                        st.session_state.indice_q += 1
                        st.rerun()
                     else:
                        st.session_state.pagina = 'resultado'
                        st.rerun()
    with col_b1:
        if st.button("Sair", key="btn_sair"):
            st.session_state.pagina = 'home'
            st.rerun()

# --- TELA RESULTADO ---
elif st.session_state.pagina == 'resultado':
    st.balloons()
    st.title("Resultado Final")
    
    acertos = st.session_state.acertos
    total = len(st.session_state.questoes_atuais)
    
    st.metric("Total de Acertos", f"{acertos} / {total}")
    
    if acertos == total:
        st.success("Perfeito! Você destruiu! 🌟")
    elif acertos > total/2:
        st.info("Mandou bem! Continue assim.")
    else:
        st.warning("Não desista. O aprendizado vem da prática. 💪")
        
    st.button("Voltar ao Início", on_click=lambda: st.session_state.update(pagina='home'))
