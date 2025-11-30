import streamlit as st
import sqlite3
import json
import random
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO INICIAL E ESTILO ---
st.set_page_config(page_title="ENEM Pro", page_icon="🎓", layout="wide")

# URLs de Imagens para deixar o app visual (Hospedadas publicamente)
IMG_BANNER = "https://img.freepik.com/free-vector/gradient-high-school-illustration_23-2149369800.jpg"
IMG_QUIZ = "https://img.freepik.com/free-vector/exams-concept-illustration_114360-2754.jpg"
IMG_RESULTADO = "https://img.freepik.com/free-vector/business-success-concept-illustration_114360-842.jpg"

# Temas Visuais
TEMAS = {
    "Padrão (Profissional)": {"primary": "#2E86C1", "bg": "#F4F6F7", "text": "#1B2631", "card_bg": "#FFFFFF"},
    "Hogwarts (Mágico)": {"primary": "#7F0909", "bg": "#F5F5DC", "text": "#2C1705", "card_bg": "#EFEFD0"},
    "Pride (Inclusivo)": {"primary": "#FF0080", "bg": "#FFF0F5", "text": "#333333", "card_bg": "#FFFFFF"},
    "Modo Foco (Zen)": {"primary": "#4B6E59", "bg": "#E8F5E9", "text": "#1B2E21", "card_bg": "#FFFFFF"}
}

# --- FUNÇÕES DE BANCO DE DADOS ---
def conectar_db():
    return sqlite3.connect('enem_pro.db')

def criar_tabelas():
    conn = conectar_db()
    c = conn.cursor()
    # Tabela Questões
    c.execute('''CREATE TABLE IF NOT EXISTS questoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, disciplina TEXT, assunto TEXT, enunciado TEXT, 
        alternativas TEXT, letra_correta TEXT, explicacao TEXT, dificuldade TEXT)''')
    # Tabela Resultados
    c.execute('''CREATE TABLE IF NOT EXISTS resultados (
        id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, acertos INTEGER, total INTEGER, disciplina TEXT)''')
    # Tabela Flashcards (Erros)
    c.execute('''CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT, questao_id INTEGER, enunciado TEXT, 
        resposta_certa TEXT, explicacao TEXT, revisado INTEGER DEFAULT 0)''')
    
    # POPULAR BANCO (SEED EXPANDIDO)
    c.execute('SELECT count(*) FROM questoes')
    if c.fetchone()[0] == 0:
        questoes = [
            # Matemática
            ("Matemática", "Porcentagem", "Um celular custa R$ 1.000. Com 20% de desconto à vista, qual o valor?", '{"A":"800", "B":"900", "C":"850", "D":"950", "E":"820"}', "A", "1000 - 200 = 800.", "Fácil"),
            ("Matemática", "Geometria", "Qual a área de um quadrado de lado 5cm?", '{"A":"20", "B":"25", "C":"10", "D":"15", "E":"30"}', "B", "Lado x Lado = 5x5 = 25.", "Fácil"),
            ("Matemática", "Funções", "Se f(x) = 2x + 1, qual o valor de f(3)?", '{"A":"5", "B":"6", "C":"7", "D":"8", "E":"9"}', "C", "2(3) + 1 = 6 + 1 = 7.", "Média"),
            ("Matemática", "Probabilidade", "Lançando um dado, qual a chance de sair número par?", '{"A":"20%", "B":"50%", "C":"30%", "D":"25%", "E":"100%"}', "B", "Pares: 2,4,6 (3 chances em 6) = 50%.", "Média"),
            # Humanas
            ("História", "Brasil Colônia", "Qual foi o primeiro ciclo econômico do Brasil?", '{"A":"Ouro", "B":"Café", "C":"Pau-Brasil", "D":"Cana", "E":"Soja"}', "C", "Extração de pau-brasil foi a primeira atividade.", "Fácil"),
            ("História", "Era Vargas", "A CLT foi criada em qual governo?", '{"A":"Lula", "B":"FHC", "C":"Vargas", "D":"JK", "E":"Pedro II"}', "C", "Getúlio Vargas criou a CLT em 1943.", "Fácil"),
            ("Geografia", "Urbanização", "O processo de crescimento das cidades chama-se:", '{"A":"Ruralização", "B":"Urbanização", "C":"Êxodo", "D":"Conurbação", "E":"Gentrificação"}', "B", "Urbanização é o crescimento urbano.", "Fácil"),
            # Natureza
            ("Biologia", "Citologia", "A 'usina de energia' da célula é a:", '{"A":"Mitocôndria", "B":"Núcleo", "C":"Ribossomo", "D":"Golgi", "E":"Vacúolo"}', "A", "Mitocôndrias produzem ATP.", "Média"),
            ("Física", "Cinemática", "Fórmula da velocidade média:", '{"A":"Vm=d/t", "B":"F=m.a", "C":"E=mc2", "D":"V=R.i", "E":"P=m.g"}', "A", "Distância dividido pelo tempo.", "Fácil"),
            ("Química", "Atomística", "O átomo é formado por:", '{"A":"Só prótons", "B":"Prótons, Nêutrons e Elétrons", "C":"Água", "D":"Células", "E":"Só elétrons"}', "B", "Estrutura básica: núcleo e eletrosfera.", "Fácil")
        ]
        c.executemany('INSERT INTO questoes (disciplina, assunto, enunciado, alternativas, letra_correta, explicacao, dificuldade) VALUES (?,?,?,?,?,?,?)', questoes)
        conn.commit()
    conn.close()

# Função para Salvar Erro no Flashcard
def salvar_erro_flashcard(q_dados):
    conn = conectar_db()
    # Verifica se já existe para não duplicar
    check = conn.execute('SELECT * FROM flashcards WHERE questao_id = ?', (q_dados[0],)).fetchone()
    if not check:
        conn.execute('INSERT INTO flashcards (questao_id, enunciado, resposta_certa, explicacao) VALUES (?,?,?,?)', 
                     (q_dados[0], q_dados[3], q_dados[5], q_dados[6]))
        conn.commit()
    conn.close()

# --- INICIALIZAÇÃO DO ESTADO ---
criar_tabelas()
if 'pagina' not in st.session_state: st.session_state.pagina = 'home'
if 'tema' not in st.session_state: st.session_state.tema = "Padrão (Profissional)"

# --- APLICAÇÃO DE ESTILO CSS DINÂMICO ---
tema = TEMAS[st.session_state.tema]
st.markdown(f"""
<style>
    .stApp {{ background-color: {tema['bg']}; color: {tema['text']}; }}
    .stButton>button {{ background-color: {tema['primary']}; color: white; border-radius: 8px; border: none; height: 45px; width: 100%; }}
    .card {{ background-color: {tema['card_bg']}; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }}
    h1, h2, h3 {{ color: {tema['primary']} !important; }}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4792/4792929.png", width=80)
    st.title("Menu do Aluno")
    
    if st.button("🏠 Início", use_container_width=True):
        st.session_state.pagina = 'home'
        st.rerun()
        
    if st.button("🧠 Meus Flashcards (Erros)", use_container_width=True):
        st.session_state.pagina = 'flashcards'
        st.rerun()

    st.markdown("---")
    st.write("🎨 **Personalize:**")
    novo_tema = st.selectbox("Tema:", list(TEMAS.keys()), index=list(TEMAS.keys()).index(st.session_state.tema))
    if novo_tema != st.session_state.tema:
        st.session_state.tema = novo_tema
        st.rerun()

    # Frase motivacional aleatória sempre que carrega
    frases = ["O sucesso é a soma de pequenos esforços.", "Você é capaz!", "Respire fundo e continue.", "Cada erro é um aprendizado."]
    st.info(f"💡 {random.choice(frases)}")

# --- PÁGINA: HOME ---
if st.session_state.pagina == 'home':
    # Banner Hero
    st.image(IMG_BANNER, use_container_width=True)
    
    st.title(f"Bem-vindo(a), Estudante!")
    st.markdown("### Prepare-se para o ENEM de forma inteligente.")
    
    st.markdown("---")
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🚀 Gerar Simulado")
        
        # Filtro de Matéria
        opcoes_materia = ["Mix Geral (Todas)", "Matemática", "História", "Biologia", "Física", "Química", "Geografia"]
        materia_escolhida = st.selectbox("Qual o foco de hoje?", opcoes_materia)
        
        qtd_questoes = st.slider("Quantas questões?", 3, 10, 5)
        
        if st.button("Começar Prova"):
            conn = conectar_db()
            if materia_escolhida == "Mix Geral (Todas)":
                query = 'SELECT * FROM questoes ORDER BY RANDOM() LIMIT ?'
                params = (qtd_questoes,)
            else:
                query = 'SELECT * FROM questoes WHERE disciplina = ? ORDER BY RANDOM() LIMIT ?'
                params = (materia_escolhida, qtd_questoes)
            
            questoes = conn.execute(query, params).fetchall()
            conn.close()
            
            if not questoes:
                st.error("Poxa, ainda não temos questões suficientes dessa matéria no banco!")
            else:
                st.session_state.questoes_atuais = questoes
                st.session_state.indice = 0
                st.session_state.acertos = 0
                st.session_state.respostas_user = {}
                st.session_state.disciplina_atual = materia_escolhida
                st.session_state.pagina = 'quiz'
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 Seu Progresso")
        conn = conectar_db()
        df = pd.read_sql_query("SELECT * FROM resultados ORDER BY id DESC LIMIT 3", conn)
        conn.close()
        
        if not df.empty:
            for index, row in df.iterrows():
                st.markdown(f"**{row['data']}** | {row['disciplina']}")
                st.progress(row['acertos'] / row['total'])
        else:
            st.info("Faça seu primeiro simulado para ver as estatísticas!")
        st.markdown('</div>', unsafe_allow_html=True)

# --- PÁGINA: QUIZ (SIMULADO) ---
elif st.session_state.pagina == 'quiz':
    if 'questoes_atuais' not in st.session_state:
        st.session_state.pagina = 'home'
        st.rerun()
        
    q = st.session_state.questoes_atuais[st.session_state.indice]
    total = len(st.session_state.questoes_atuais)
    
    # Visual do Quiz
    col_img, col_txt = st.columns([1, 3])
    with col_img:
        st.image(IMG_QUIZ, width=150)
    with col_txt:
        st.progress((st.session_state.indice + 1) / total)
        st.caption(f"Questão {st.session_state.indice + 1} de {total} | {q[1]} ({q[2]})")
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"### {q[3]}") # Enunciado
    
    alts = json.loads(q[4])
    chave = f"q_{q[0]}"
    
    # Se já respondeu, mostra estado, senão mostra input
    ja_respondeu = chave in st.session_state.respostas_user
    
    if not ja_respondeu:
        escolha = st.radio("Alternativa:", list(alts.keys()), format_func=lambda x: f"{x}) {alts[x]}", key=chave)
        
        if st.button("Confirmar Resposta"):
            st.session_state.respostas_user[chave] = escolha
            if escolha == q[5]:
                st.toast("✅ ACERTOU!", icon="🔥")
                st.session_state.acertos += 1
            else:
                st.toast("❌ Errou! Salvando no Flashcard...", icon="💾")
                # LÓGICA DE FLASHCARD AUTOMÁTICO
                salvar_erro_flashcard(q)
            st.rerun() # Recarrega para mostrar o feedback
            
    else:
        # TELA DE FEEDBACK PÓS-RESPOSTA
        escolha_feita = st.session_state.respostas_user[chave]
        if escolha_feita == q[5]:
            st.success(f"Você marcou {escolha_feita}. Correto! 🎉")
        else:
            st.error(f"Você marcou {escolha_feita}. A correta era {q[5]}.")
            st.warning(f"📝 **Flashcard Criado!** Essa questão foi para sua revisão.")
            with st.expander("Ver Explicação"):
                st.write(q[6])
        
        # Botão Próximo / Finalizar
        if st.session_state.indice < total - 1:
            if st.button("Próxima Questão ➡️"):
                st.session_state.indice += 1
                st.rerun()
        else:
            if st.button("Finalizar Simulado 🏁"):
                conn = conectar_db()
                conn.execute("INSERT INTO resultados (data, acertos, total, disciplina) VALUES (?,?,?,?)",
                             (datetime.now().strftime("%d/%m %H:%M"), st.session_state.acertos, total, st.session_state.disciplina_atual))
                conn.commit()
                conn.close()
                st.session_state.pagina = 'resultado'
                st.rerun()
                
    st.markdown('</div>', unsafe_allow_html=True)

# --- PÁGINA: RESULTADO ---
elif st.session_state.pagina == 'resultado':
    st.balloons()
    st.markdown('<div class="card" style="text-align:center">', unsafe_allow_html=True)
    st.image(IMG_RESULTADO, width=200)
    st.title("Simulado Finalizado!")
    
    acertos = st.session_state.acertos
    total = len(st.session_state.questoes_atuais)
    nota = (acertos/total) * 1000
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Acertos", f"{acertos}/{total}")
    c2.metric("Nota Estimada", f"{nota:.0f}")
    c3.metric("Erros (Flashcards)", f"{total - acertos}")
    
    st.divider()
    
    if total - acertos > 0:
        if st.button("🧠 Revisar meus Erros agora (Flashcards)"):
            st.session_state.pagina = 'flashcards'
            st.rerun()
            
    if st.button("🏠 Voltar ao Início"):
        st.session_state.pagina = 'home'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- PÁGINA: FLASHCARDS (REVISÃO) ---
elif st.session_state.pagina == 'flashcards':
    st.title("🧠 Revisão Inteligente (Flashcards)")
    st.write("Aqui estão as questões que você errou. Treine até aprender!")
    
    conn = conectar_db()
    cards = conn.execute("SELECT * FROM flashcards").fetchall()
    
    if not cards:
        st.image("https://cdn-icons-png.flaticon.com/512/7486/7486744.png", width=150)
        st.success("Você não tem flashcards pendentes! Você é um gênio! 🤓")
        if st.button("Voltar"):
            st.session_state.pagina = 'home'
            st.rerun()
    else:
        # Mostra cards em Grid
        for card in cards:
            # card: id, q_id, enun, resp, expl, revisado
            with st.container(border=True):
                c_a, c_b = st.columns([4, 1])
                with c_a:
                    st.markdown(f"**Questão:** {card[2]}")
                with c_b:
                    if st.button("🗑️", key=f"del_{card[0]}", help="Já aprendi, remover"):
                        conn.execute("DELETE FROM flashcards WHERE id = ?", (card[0],))
                        conn.commit()
                        st.rerun()
                
                # Efeito de "Virar Carta" usando Expander
                with st.expander("Ocultar/Mostrar Resposta"):
                    st.info(f"**Resposta Correta:** {card[3]}")
                    st.write(f"**Explicação:** {card[4]}")
        
        conn.close()
