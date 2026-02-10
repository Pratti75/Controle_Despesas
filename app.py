import streamlit as st
import pandas as pd
import json
from uuid import uuid4
from datetime import datetime
import plotly.express as px
import hashlib
import io


ARQ_DADOS = "despesas.json"
ARQ_USERS = "usuarios.json"

# ---------------- SEGURANÇA ----------------
def hash_senha(s):
    return hashlib.sha256(s.encode()).hexdigest()

# ---------------- USUÁRIOS ----------------
def load_users():
    try:
        with open(ARQ_USERS, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(ARQ_USERS, "w") as f:
        json.dump(users, f, indent=4)

# ---------------- DESPESAS ----------------
def load_data():
    try:
        with open(ARQ_DADOS, "r") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(ARQ_DADOS, "w") as f:
        json.dump(data, f, indent=4)

# ---------------- LOGIN ----------------
def login():
    st.subheader("Login")
    user = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        users = load_users()
        if user in users and users[user] == hash_senha(senha):
            st.session_state.user = user
            st.success("Login realizado com sucesso")
        else:
            st.error("Usuário ou senha inválidos")

# ---------------- CADASTRO ----------------
def cadastro():
    st.subheader("Cadastro de novo usuário")
    user = st.text_input("Novo usuário")
    senha = st.text_input("Nova senha", type="password")

    if st.button("Cadastrar"):
        users = load_users()
        if user in users:
            st.error("Usuário já existe")
        else:
            users[user] = hash_senha(senha)
            save_users(users)
            st.success("Usuário cadastrado com sucesso")

# ---------------- APP PRINCIPAL ----------------
def app():
    st.title("Controle de Despesas Mensais")

    descricao = st.text_input("Descrição da despesa")
    categoria = st.selectbox(
        "Categoria",
        ["Alimentação", "Transporte", "Moradia", "Lazer", "Outros"]
    )
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
    data = st.date_input("Data", datetime.today())

    if st.button("Adicionar despesa"):
        dados = load_data()
        dados.append({
            "id": str(uuid4()),
            "usuario": st.session_state.user,
            "descricao": descricao,
            "categoria": categoria,
            "valor": valor,
            "data": str(data)
        })
        save_data(dados)
        st.success("Despesa adicionada com sucesso")

    df = pd.DataFrame(load_data())

    if not df.empty:
        df = df[df["usuario"] == st.session_state.user]

        if not df.empty:
            df["data"] = pd.to_datetime(df["data"])
            df["mes"] = df["data"].dt.to_period("M").astype(str)

            st.subheader("Despesas registradas")
            st.dataframe(df[["descricao", "categoria", "valor", "data"]])

            id_excluir = st.selectbox("Selecione a despesa para excluir", df["id"])
            if st.button("Excluir despesa"):
                dados = load_data()
                dados = [d for d in dados if d["id"] != id_excluir]
                save_data(dados)
                st.warning("Despesa removida")

            st.subheader("Dashboard mensal")

            total_mes = df.groupby("mes")["valor"].sum().reset_index()
            fig1 = px.bar(
                total_mes,
                x="mes",
                y="valor",
                title="Total de despesas por mês"
            )
            st.plotly_chart(fig1, use_container_width=True)

            categoria_mes = (
                df.groupby(["mes", "categoria"])["valor"]
                .sum()
                .reset_index()
            )
            fig2 = px.pie(
                categoria_mes,
                values="valor",
                names="categoria",
                title="Distribuição por categoria"
            )
            st.plotly_chart(fig2, use_container_width=True)

            import io

buffer = io.BytesIO()
df.to_excel(buffer, index=False)
buffer.seek(0)

st.download_button(
    label="Exportar despesas para Excel",
    data=buffer,
    file_name="despesas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


# ---------------- EXECUÇÃO ----------------
st.sidebar.title("Acesso")

if "user" not in st.session_state:
    opcao = st.sidebar.radio("Escolha", ["Login", "Cadastro"])
    if opcao == "Login":
        login()
    else:
        cadastro()
else:
    app()
