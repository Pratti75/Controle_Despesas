import streamlit as st
import pandas as pd
import json
from uuid import uuid4
from datetime import datetime
import plotly.express as px
import hashlib
import io
import os

# =========================
# CONFIGURAÇÃO
# =========================
st.set_page_config(
    page_title="Controle de Despesas",
    page_icon="icon.png",
    layout="centered"
)

DATA_FILE = "despesas.json"
USERS_FILE = "usuarios.json"
SESSION_FILE = "session.json"

# =========================
# FUNÇÕES BASE
# =========================
def load_json(file, default):
    if not os.path.exists(file):
        return default
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# =========================
# SESSÃO PERSISTENTE
# =========================
session = load_json(SESSION_FILE, {"logado": False, "usuario": None})

if "logado" not in st.session_state:
    st.session_state.logado = session["logado"]
    st.session_state.usuario = session["usuario"]

def salvar_sessao():
    save_json(SESSION_FILE, {
        "logado": st.session_state.logado,
        "usuario": st.session_state.usuario
    })

# =========================
# AUTENTICAÇÃO
# =========================
def autenticar(usuario, senha):
    usuarios = load_json(USERS_FILE, [])
    return any(
        u["usuario"] == usuario and u["senha"] == hash_senha(senha)
        for u in usuarios
    )

def cadastrar_usuario(usuario, senha):
    usuarios = load_json(USERS_FILE, [])
    if any(u["usuario"] == usuario for u in usuarios):
        return False
    usuarios.append({
        "usuario": usuario,
        "senha": hash_senha(senha)
    })
    save_json(USERS_FILE, usuarios)
    return True

# =========================
# DESPESAS
# =========================
def carregar_despesas():
    return [
        d for d in load_json(DATA_FILE, [])
        if d["usuario"] == st.session_state.usuario
    ]

def salvar_despesas(lista):
    todas = load_json(DATA_FILE, [])
    todas = [d for d in todas if d["usuario"] != st.session_state.usuario]
    todas.extend(lista)
    save_json(DATA_FILE, todas)

# =========================
# TELA LOGIN
# =========================
def tela_login():
    st.title("💰 Controle de Despesas")

    aba = st.radio("Acesso", ["Entrar", "Cadastrar"], horizontal=True)

    if aba == "Entrar":
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if autenticar(usuario, senha):
                st.session_state.logado = True
                st.session_state.usuario = usuario
                salvar_sessao()
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

    else:
        usuario = st.text_input("Novo usuário")
        senha = st.text_input("Nova senha", type="password")

        if st.button("Cadastrar"):
            if cadastrar_usuario(usuario, senha):
                st.success("Usuário cadastrado com sucesso")
            else:
                st.error("Usuário já existe")

# =========================
# TELA PRINCIPAL
# =========================
def tela_despesas():
    st.title("📊 Controle de Despesas")

    if st.button("Sair"):
        st.session_state.logado = False
        st.session_state.usuario = None
        salvar_sessao()
        st.rerun()

    despesas = carregar_despesas()
    df = pd.DataFrame(despesas)

    st.subheader("Adicionar despesa")
    col1, col2 = st.columns(2)
    valor = col1.number_input("Valor (R$)", min_value=0.0, step=1.0)
    categoria = col2.text_input("Categoria")

    if st.button("Salvar despesa"):
        despesas.append({
            "id": str(uuid4()),
            "usuario": st.session_state.usuario,
            "valor": valor,
            "categoria": categoria,
            "data": datetime.now().strftime("%Y-%m")
        })
        salvar_despesas(despesas)
        st.success("Despesa salva")
        st.rerun()

    if df.empty:
        st.info("Nenhuma despesa cadastrada")
        return

    st.subheader("Despesas")
    st.dataframe(df[["valor", "categoria", "data"]], use_container_width=True)

    st.subheader("Excluir despesa")
    id_excluir = st.selectbox("Selecione", df["id"].tolist())

    if st.button("Excluir"):
        despesas = [d for d in despesas if d["id"] != id_excluir]
        salvar_despesas(despesas)
        st.success("Despesa removida")
        st.rerun()

    st.subheader("Resumo mensal")
    st.metric("Total gasto", f"R$ {df['valor'].sum():.2f}")

    fig = px.bar(df, x="categoria", y="valor", color="categoria")
    st.plotly_chart(fig, use_container_width=True)

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        "📥 Exportar Excel",
        data=buffer,
        file_name="despesas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =========================
# FLUXO
# =========================
if st.session_state.logado:
    tela_despesas()
else:
    tela_login()
