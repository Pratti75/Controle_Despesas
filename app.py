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
    with open(USUARIOS_FILE, "r") as f:
        return json.load(f)

def salvar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w") as f:
        json.dump(usuarios, f, indent=4)

def carregar_despesas():
    if not os.path.exists(DESPESAS_FILE):
        return pd.DataFrame(columns=["email", "descricao", "valor", "data"])
    return pd.read_csv(DESPESAS_FILE)

def salvar_despesas(df):
    df.to_csv(DESPESAS_FILE, index=False)

# =========================
# INICIALIZAÇÃO DE SESSÃO
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
            if email in usuarios:
                user = usuarios[email]
                if not user["aprovado"]:
                    st.error("Cadastro ainda não aprovado pelo administrador.")
                elif user["senha"] == hash_senha(senha):
                    st.session_state.logado = True
                    st.session_state.email = email
                    st.experimental_rerun()
                else:
                    st.error("Senha incorreta.")
            else:
                st.error("Usuário não encontrado.")

    else:
        nome = st.text_input("Usuário desejado")
        email = st.text_input("Seu e-mail")
        senha = st.text_input("Senha", type="password")

        if st.button("Solicitar cadastro"):
            if email in usuarios:
                st.warning("Este e-mail já está cadastrado.")
                return

            aprovado = True if email == ADMIN_EMAIL else False

            usuarios[email] = {
                "nome": nome,
                "senha": hash_senha(senha),
                "aprovado": aprovado
            }

            salvar_usuarios(usuarios)

            if aprovado:
                st.success("Administrador criado com sucesso. Faça login.")
            else:
                st.info("Cadastro enviado para aprovação do administrador.")

# =========================
# PAINEL PRINCIPAL
# =========================
def painel():
    email = st.session_state.email
    usuarios = carregar_usuarios()

    st.sidebar.success(f"Logado como: {email}")

    # =========================
    # PAINEL ADMIN
    # =========================
    if email == ADMIN_EMAIL:
        st.subheader("👑 Painel do Administrador")

        pendentes = {
            e: u for e, u in usuarios.items() if not u["aprovado"]
        }

        if pendentes:
            for e, u in pendentes.items():
                col1, col2 = st.columns([3, 1])
                col1.write(f"📧 {e} — {u['nome']}")
                if col2.button("Aprovar", key=e):
                    usuarios[e]["aprovado"] = True
                    salvar_usuarios(usuarios)
                    st.experimental_rerun()
        else:
            st.success("Nenhum cadastro pendente.")

        st.divider()

    # =========================
    # CONTROLE DE DESPESAS
    # =========================
    st.subheader("📊 Controle de Despesas")

    descricao = st.text_input("Descrição da despesa")
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)

    if st.button("Adicionar despesa"):
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
        st.experimental_rerun()

    df = carregar_despesas()
    df_user = df[df["email"] == email]

    if not df_user.empty:
        st.dataframe(df_user)

        total = df_user["valor"].sum()
        st.metric("Total gasto", f"R$ {total:.2f}")

# =========================
# EXECUÇÃO
# =========================
if not st.session_state.logado:
    tela_acesso()
else:
    painel()
