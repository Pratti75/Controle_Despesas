import streamlit as st
import json
import os
import hashlib
import pandas as pd
from datetime import datetime

# =============================
# CONFIGURAÇÃO
# =============================
st.set_page_config(
    page_title="Controle de Despesas",
    page_icon="💰",
    layout="centered"
)

USUARIOS_FILE = "usuarios.json"
DESPESAS_FILE = "despesas.json"

# =============================
# SECRETS
# =============================
try:
    ADMIN_EMAIL = st.secrets["ADMIN_EMAIL"]
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except KeyError:
    st.error("Configure ADMIN_EMAIL e ADMIN_PASSWORD nos Secrets do Streamlit")
    st.stop()

ADMIN_HASH = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()

# =============================
# FUNÇÕES UTILITÁRIAS
# =============================
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def carregar_json(arquivo):
    if not os.path.exists(arquivo):
        return {}
    with open(arquivo, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# =============================
# AUTENTICAÇÃO
# =============================
def autenticar(email, senha, usuarios):
    senha_hash = hash_senha(senha)

    if email == ADMIN_EMAIL and senha_hash == ADMIN_HASH:
        return {"tipo": "admin"}

    if email in usuarios and usuarios[email]["senha"] == senha_hash:
        if usuarios[email]["aprovado"]:
            return {"tipo": "usuario"}

    return None

# =============================
# TELAS
# =============================
def tela_login():
    st.title("🔐 Login")

    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        usuarios = carregar_json(USUARIOS_FILE)
        resultado = autenticar(email, senha, usuarios)

        if resultado:
            st.session_state.usuario = email
            st.session_state.tipo = resultado["tipo"]
            st.rerun()
        else:
            st.error("Login inválido ou usuário não aprovado")

    st.divider()
    tela_cadastro()

def tela_cadastro():
    st.subheader("📝 Cadastro")

    email = st.text_input("Novo e-mail", key="cad_email")
    senha = st.text_input("Nova senha", type="password", key="cad_senha")

    if st.button("Cadastrar"):
        if email == ADMIN_EMAIL:
            st.error("E-mail reservado ao administrador")
            return

        usuarios = carregar_json(USUARIOS_FILE)

        if email in usuarios:
            st.error("Usuário já cadastrado")
            return

        usuarios[email] = {
            "senha": hash_senha(senha),
            "aprovado": False
        }

        salvar_json(USUARIOS_FILE, usuarios)
        st.success("Cadastro realizado. Aguarde aprovação.")

def painel_admin():
    st.title("👑 Painel do Administrador")

    usuarios = carregar_json(USUARIOS_FILE)

    for email, dados in usuarios.items():
        col1, col2, col3 = st.columns([4, 2, 2])
        col1.write(email)
        col2.write("✅ Aprovado" if dados["aprovado"] else "⏳ Pendente")

        if not dados["aprovado"]:
            if col3.button("Aprovar", key=email):
                usuarios[email]["aprovado"] = True
                salvar_json(USUARIOS_FILE, usuarios)
                st.success(f"{email} aprovado")
                st.rerun()

def painel_usuario():
    st.title("📊 Controle de Despesas")

    usuario = st.session_state.usuario
    despesas = carregar_json(DESPESAS_FILE)

    if usuario not in despesas:
        despesas[usuario] = []

    with st.form("nova_despesa"):
        descricao = st.text_input("Descrição")
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        data = st.date_input("Data", value=datetime.today())

        if st.form_submit_button("Adicionar"):
            despesas[usuario].append({
                "descricao": descricao,
                "valor": valor,
                "data": data.strftime("%Y-%m-%d")
            })
            salvar_json(DESPESAS_FILE, despesas)
            st.success("Despesa adicionada")
            st.rerun()

    if despesas[usuario]:
        df = pd.DataFrame(despesas[usuario])
        df["data"] = pd.to_datetime(df["data"])
        df["mes"] = df["data"].dt.to_period("M").astype(str)

        st.subheader("📈 Dashboard Mensal")
        st.bar_chart(df.groupby("mes")["valor"].sum())

        st.subheader("📋 Despesas")
        st.dataframe(df)

# =============================
# CONTROLE DE SESSÃO
# =============================
if "usuario" not in st.session_state:
    tela_login()
else:
    if st.sidebar.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.tipo == "admin":
        painel_admin()
    else:
        painel_usuario()
