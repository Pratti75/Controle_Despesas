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
# CONFIGURAÇÃO INICIAL
# =========================
st.set_page_config(
    page_title="Controle de Despesas",
    page_icon="💰",
    layout="centered"
)

DATA_FILE = "despesas.json"
USERS_FILE = "usuarios.json"

# =========================
# ESTADO DE SESSÃO
# =========================
if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# =========================
# FUNÇÕES AUXILIARES
# =========================
def carregar_json(arquivo):
    if not os.path.exists(arquivo):
        return []
    with open(arquivo, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def autenticar(usuario, senha):
    usuarios = carregar_json(USERS_FILE)
    senha_hash = hash_senha(senha)
    return any(u["usuario"] == usuario and u["senha"] == senha_hash for u in usuarios)

def cadastrar_usuario(usuario, senha):
    usuarios = carregar_json(USERS_FILE)
    if any(u["usuario"] == usuario for u in usuarios):
        return False
    usuarios.append({
        "usuario": usuario,
        "senha": hash_senha(senha)
    })
    salvar_json(USERS_FILE, usuarios)
    return True

def carregar_despesas():
    despesas = carregar_json(DATA_FILE)
    return [d for d in despesas if d["usuario"] == st.session_state.usuario]

def salvar_despesas(lista):
    todas = carregar_json(DATA_FILE)
    todas = [d for d in todas if d["usuario"] != st.session_state.usuario]
    todas.extend(lista)
    salvar_json(DATA_FILE, todas)

# =========================
# TELA LOGIN / CADASTRO
# =========================
def tela_login():
    st.title("💰 Controle de Despesas")

    opcao = st.radio("Escolha uma opção", ["Entrar", "Cadastrar"], horizontal=True)

    if opcao == "Entrar":
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if autenticar(usuario, senha):
                st.session_state.logado = True
                st.session_state.usuario = usuario
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

    else:
        novo_usuario = st.text_input("Novo usuário")
        nova_senha = st.text_input("Nova senha", type="password")

        if st.button("Cadastrar"):
            if cadastrar_usuario(novo_usuario, nova_senha):
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

    st.subheader("Despesas do mês")
    st.dataframe(df[["valor", "categoria", "data"]], use_container_width=True)

    # =========================
    # EXCLUSÃO SEGURA
    # =========================
    st.subheader("Excluir despesa")

    id_excluir = st.selectbox(
        "Selecione a despesa",
        df["id"].tolist()
    )

    if st.button("Excluir despesa"):
        despesas = [d for d in despesas if d["id"] != id_excluir]
        salvar_despesas(despesas)
        st.success("Despesa removida")
        st.rerun()

    # =========================
    # DASHBOARD
    # =========================
    st.subheader("Resumo mensal")

    total = df["valor"].sum()
    st.metric("Total gasto", f"R$ {total:.2f}")

    fig = px.bar(
        df,
        x="categoria",
        y="valor",
        title="Gastos por categoria",
        color="categoria"
    )
    st.plotly_chart(fig, use_container_width=True)

    # =========================
    # EXPORTAR EXCEL
    # =========================
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        "📥 Exportar para Excel",
        data=buffer,
        file_name="despesas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =========================
# CONTROLE DE FLUXO
# =========================
def app():
    if not st.session_state.logado:
        tela_login()
    else:
        tela_despesas()

app()
