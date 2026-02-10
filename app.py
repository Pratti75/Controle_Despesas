import streamlit as st
import pandas as pd
import json
import os
import hashlib
from datetime import datetime

# =========================
# CONFIGURAÇÃO DO ADMIN
# =========================
ADMIN_EMAIL = "engepratti@gmail.com"

USUARIOS_FILE = "usuarios.json"
DESPESAS_FILE = "despesas.csv"

# =========================
# FUNÇÕES AUXILIARES
# =========================
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def carregar_usuarios():
    if not os.path.exists(USUARIOS_FILE):
        return {}
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)

def carregar_despesas():
    if not os.path.exists(DESPESAS_FILE):
        return pd.DataFrame(columns=["email", "descricao", "valor", "data"])
    return pd.read_csv(DESPESAS_FILE)

def salvar_despesas(df):
    df.to_csv(DESPESAS_FILE, index=False)

# =========================
# CONTROLE DE SESSÃO
# =========================
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.email = None

# =========================
# TELA DE LOGIN / CADASTRO
# =========================
def tela_acesso():
    st.title("💰 Controle de Despesas")

    modo = st.radio("Acesso", ["Entrar", "Solicitar cadastro"])
    usuarios = carregar_usuarios()

    if modo == "Entrar":
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if email not in usuarios:
                st.error("Usuário não encontrado.")
                return

            if not usuarios[email]["aprovado"]:
                st.error("Cadastro ainda não aprovado.")
                return

            if usuarios[email]["senha"] != hash_senha(senha):
                st.error("Senha incorreta.")
                return

            st.session_state.logado = True
            st.session_state.email = email
            st.rerun()

    else:
        nome = st.text_input("Usuário desejado")
        email = st.text_input("Seu e-mail")
        senha = st.text_input("Senha", type="password")

        if st.button("Solicitar cadastro"):
            if email in usuarios:
                st.warning("E-mail já cadastrado.")
                return

            aprovado = email == ADMIN_EMAIL

            usuarios[email] = {
                "nome": nome,
                "senha": hash_senha(senha),
                "aprovado": aprovado
            }

            salvar_usuarios(usuarios)

            if aprovado:
                st.success("Administrador criado. Faça login.")
            else:
                st.info("Cadastro enviado para aprovação.")

# =========================
# PAINEL PRINCIPAL
# =========================
def painel():
    email = st.session_state.email
    usuarios = carregar_usuarios()

    st.sidebar.success(f"Logado como: {email}")

    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.session_state.email = None
        st.rerun()

    # =========================
    # PAINEL ADMIN
    # =========================
    if email == ADMIN_EMAIL:
        st.subheader("👑 Painel do Administrador")

        pendentes = {e: u for e, u in usuarios.items() if not u["aprovado"]}

        if pendentes:
            for e, u in pendentes.items():
                col1, col2 = st.columns([3, 1])
                col1.write(f"📧 {e} — {u['nome']}")
                if col2.button("Aprovar", key=f"aprovar_{e}"):
                    usuarios[e]["aprovado"] = True
                    salvar_usuarios(usuarios)
                    st.rerun()
        else:
            st.success("Nenhum cadastro pendente.")

        st.divider()

    # =========================
    # REGISTRO DE DESPESAS
    # =========================
    st.subheader("➕ Nova Despesa")

    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)

    if st.button("Adicionar despesa"):
        if not descricao.strip():
            st.warning("Informe a descrição.")
            return

        df = carregar_despesas()

        nova = {
            "email": email,
            "descricao": descricao,
            "valor": valor,
            "data": datetime.now().strftime("%Y-%m-%d")
        }

        df = pd.concat([df, pd.DataFrame([nova])], ignore_index=True)
        salvar_despesas(df)
        st.success("Despesa adicionada.")
        st.rerun()

    # =========================
    # LISTAGEM + EXCLUSÃO
    # =========================
    df = carregar_despesas()
    df_user = df[df["email"] == email].reset_index(drop=True)

    if not df_user.empty:
        st.subheader("📋 Despesas registradas")

        for i, row in df_user.iterrows():
            col1, col2, col3, col4 = st.columns([4, 2, 2, 1])

            col1.write(row["descricao"])
            col2.write(f"R$ {row['valor']:.2f}")
            col3.write(row["data"])

            if col4.button("🗑", key=f"del_{i}"):
                df.drop(df_user.index[i], inplace=True)
                salvar_despesas(df)
                st.rerun()

        total = df_user["valor"].sum()
        st.metric("💰 Total gasto", f"R$ {total:.2f}")

        # =========================
        # DASHBOARD MENSAL
        # =========================
        st.subheader("📊 Dashboard Mensal")

        df_user["data"] = pd.to_datetime(df_user["data"])
        df_user["mes"] = df_user["data"].dt.to_period("M").astype(str)

        resumo = df_user.groupby("mes")["valor"].sum().reset_index()
        resumo.columns = ["Mês", "Total"]

        st.bar_chart(resumo.set_index("Mês"))
    else:
        st.info("Nenhuma despesa registrada.")

# =========================
# EXECUÇÃO
# =========================
if not st.session_state.logado:
    tela_acesso()
else:
    painel()
