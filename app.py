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
ADMIN_EMAIL = "engepratti@gmail.com"  # TROQUE PARA O SEU E-MAIL

st.set_page_config(
    page_title="Controle de Despesas",
    page_icon="💰",
    layout="centered"
)

DATA_FILE = "despesas.json"
USERS_FILE = "usuarios.json"
PENDING_FILE = "cadastros_pendentes.json"
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

def solicitar_cadastro(usuario, senha, email):
    pendentes = load_json(PENDING_FILE, [])
    pendentes.append({
        "usuario": usuario,
        "senha": hash_senha(senha),
        "email": email
    })
    save_json(PENDING_FILE, pendentes)

def aprovar_usuario(usuario):
    pendentes = load_json(PENDING_FILE, [])
    usuarios = load_json(USERS_FILE, [])

    aprovado = next(p for p in pendentes if p["usuario"] == usuario)
    usuarios.append(aprovado)

    pendentes = [p for p in pendentes if p["usuario"] != usuario]

    save_json(USERS_FILE, usuarios)
    save_json(PENDING_FILE, pendentes)

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
# LOGIN / CADASTRO
# =========================
def tela_login():
    st.title("💰 Controle de Despesas")

    aba = st.radio("Acesso", ["Entrar", "Solicitar cadastro"], horizontal=True)

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
                st.error("Usuário não aprovado ou senha inválida")

    else:
        usuario = st.text_input("Usuário desejado")
        senha = st.text_input("Senha", type="password")
        email = st.text_input("Seu e-mail")

        if st.button("Solicitar cadastro"):
            solicitar_cadastro(usuario, senha, email)
            st.info("Cadastro enviado para aprovação do administrador")

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

    # -------- ADMIN --------
    if st.session_state.usuario == ADMIN_EMAIL:
        st.subheader("👑 Administração")

        pendentes = load_json(PENDING_FILE, [])

        if not pendentes:
            st.info("Nenhum cadastro pendente")

        for p in pendentes:
            col1, col2 = st.columns([3,1])
            col1.write(f"{p['usuario']} - {p['email']}")
            if col2.button("Aprovar", key=p["usuario"]):
                aprovar_usuario(p["usuario"])
                st.success("Usuário aprovado")
                st.rerun()

    # -------- DESPESAS --------
    despesas = carregar_despesas()
    df = pd.DataFrame(despesas)

    st.subheader("Adicionar despesa")
    valor = st.number_input("Valor (R$)", min_value=0.0)
    categoria = st.text_input("Categoria")

    if st.button("Salvar despesa"):
        despesas.append({
            "id": str(uuid4()),
            "usuario": st.session_state.usuario,
            "valor": valor,
            "categoria": categoria,
            "data": datetime.now().strftime("%Y-%m")
        })
        salvar_despesas(despesas)
        st.rerun()

    if df.empty:
        st.info("Nenhuma despesa cadastrada")
        return

    st.dataframe(df[["valor", "categoria", "data"]])

    st.subheader("Excluir despesa")
    id_excluir = st.selectbox("Selecione", df["id"].tolist())

    if st.button("Excluir"):
        despesas = [d for d in despesas if d["id"] != id_excluir]
        salvar_despesas(despesas)
        st.rerun()

    st.metric("Total gasto", f"R$ {df['valor'].sum():.2f}")

    fig = px.bar(df, x="categoria", y="valor", color="categoria")
    st.plotly_chart(fig, use_container_width=True)

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        "📥 Exportar Excel",
        data=buffer,
        file_name="despesas.xlsx"
    )

# =========================
# FLUXO
# =========================
if st.session_state.logado:
    tela_despesas()
else:
    tela_login()
