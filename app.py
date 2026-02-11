import streamlit as st
import json
import os
import hashlib

# ===============================
# CONFIGURAÇÃO
# ===============================
USUARIOS_FILE = "usuarios.json"
DESPESAS_FILE = "despesas.json"

ADMIN_EMAIL = st.secrets["ADMIN_EMAIL"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# ===============================
# FUNÇÕES UTILITÁRIAS
# ===============================
def carregar_json(arquivo, padrao):
    if not os.path.exists(arquivo):
        with open(arquivo, "w") as f:
            json.dump(padrao, f)
    with open(arquivo, "r") as f:
        return json.load(f)

def salvar_json(arquivo, dados):
    with open(arquivo, "w") as f:
        json.dump(dados, f, indent=4)

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# ===============================
# CARREGAMENTO DOS DADOS
# ===============================
usuarios = carregar_json(USUARIOS_FILE, {})
despesas = carregar_json(DESPESAS_FILE, {})

# ===============================
# LOGIN
# ===============================
def login():
    st.title("🔐 Login")

    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        senha_hash = hash_senha(senha)

        # ADMIN
        if email == ADMIN_EMAIL and senha == ADMIN_PASSWORD:
            st.session_state.usuario = email
            st.session_state.admin = True
            st.rerun()

        # USUÁRIO NORMAL
        elif email in usuarios:
            if not usuarios[email]["aprovado"]:
                st.error("Usuário ainda não aprovado pelo administrador.")
            elif usuarios[email]["senha"] == senha_hash:
                st.session_state.usuario = email
                st.session_state.admin = False
                st.rerun()
            else:
                st.error("Senha incorreta.")
        else:
            st.error("Usuário não encontrado.")

    st.divider()
    cadastro()

# ===============================
# CADASTRO
# ===============================
def cadastro():
    st.subheader("📝 Cadastro")

    email = st.text_input("Novo e-mail", key="cad_email")
    senha = st.text_input("Nova senha", type="password", key="cad_senha")

    if st.button("Cadastrar"):
        if email in usuarios:
            st.warning("Usuário já existe.")
        else:
            usuarios[email] = {
                "senha": hash_senha(senha),
                "aprovado": False,
                "admin": False
            }
            salvar_json(USUARIOS_FILE, usuarios)
            st.success("Cadastro realizado! Aguarde aprovação do administrador.")

# ===============================
# PAINEL ADMIN
# ===============================
def painel_admin():
    st.title("🛠️ Painel do Administrador")

    st.subheader("Usuários cadastrados")

    for email, dados in list(usuarios.items()):
        col1, col2, col3 = st.columns([4, 2, 2])

        with col1:
            st.write(email)

        with col2:
            if not dados["aprovado"]:
                if st.button("Aprovar", key=f"aprovar_{email}"):
                    usuarios[email]["aprovado"] = True
                    salvar_json(USUARIOS_FILE, usuarios)
                    st.rerun()
            else:
                st.success("Aprovado")

        with col3:
            if st.button("❌ Excluir", key=f"excluir_{email}"):
                excluir_usuario(email)
                st.rerun()

    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()

# ===============================
# EXCLUIR USUÁRIO (FUNÇÃO CRÍTICA)
# ===============================
def excluir_usuario(email):
    if email in usuarios:
        del usuarios[email]
        salvar_json(USUARIOS_FILE, usuarios)

    if email in despesas:
        del despesas[email]
        salvar_json(DESPESAS_FILE, despesas)

# ===============================
# PAINEL USUÁRIO
# ===============================
def painel_usuario():
    usuario = st.session_state.usuario
    st.title("💰 Controle de Despesas")

    if usuario not in despesas:
        despesas[usuario] = []
        salvar_json(DESPESAS_FILE, despesas)

    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor", min_value=0.0, format="%.2f")

    if st.button("Adicionar despesa"):
        despesas[usuario].append({"descricao": descricao, "valor": valor})
        salvar_json(DESPESAS_FILE, despesas)
        st.success("Despesa adicionada.")

    st.subheader("Minhas despesas")
    total = 0
    for d in despesas[usuario]:
        st.write(f"- {d['descricao']} | R$ {d['valor']:.2f}")
        total += d["valor"]

    st.metric("Total", f"R$ {total:.2f}")

    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()

# ===============================
# CONTROLE DE SESSÃO
# ===============================
if "usuario" not in st.session_state:
    login()
else:
    if st.session_state.get("admin"):
        painel_admin()
    else:
        painel_usuario()
