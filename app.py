import streamlit as st
import pandas as pd
import json
import os
import hashlib
from datetime import datetime

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="Controle de Despesas",
    page_icon="💰",
    layout="centered"
)

# =========================
# ADMIN FIXO (SECRETS)
# =========================
ADMIN_EMAIL = st.secrets.get("ADMIN_EMAIL", "")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "")

# =========================
# ARQUIVOS
# =========================
USUARIOS_FILE = "usuarios.json"
DESPESAS_FILE = "despesas.csv"

# =========================
# FUNÇÕES AUXILIARES
# =========================
def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

def carregar_usuarios():
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)

def garantir_admin():
    usuarios = carregar_usuarios()
    if ADMIN_EMAIL and ADMIN_EMAIL not in usuarios:
        usuarios[ADMIN_EMAIL] = {
            "nome": "Administrador",
            "senha": hash_senha(ADMIN_PASSWORD),
            "aprovado": True
        }
        salvar_usuarios(usuarios)

def carregar_despesas(email):
    if os.path.exists(DESPESAS_FILE):
        df = pd.read_csv(DESPESAS_FILE)
        return df[df["email"] == email]
    return pd.DataFrame(columns=["email", "descricao", "valor", "data"])

def salvar_despesa(email, descricao, valor):
    nova = pd.DataFrame([{
        "email": email,
        "descricao": descricao,
        "valor": valor,
        "data": datetime.now().strftime("%Y-%m-%d")
    }])

    if os.path.exists(DESPESAS_FILE):
        df = pd.read_csv(DESPESAS_FILE)
        df = pd.concat([df, nova], ignore_index=True)
    else:
        df = nova

    df.to_csv(DESPESAS_FILE, index=False)

def excluir_despesa(index, email):
    df = pd.read_csv(DESPESAS_FILE)
    df = df.drop(df[(df.index == index) & (df["email"] == email)].index)
    df.to_csv(DESPESAS_FILE, index=False)

# =========================
# INICIALIZAÇÃO
# =========================
garantir_admin()

if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.email = ""

# =========================
# TELA DE LOGIN / CADASTRO
# =========================
st.title("💰 Controle de Despesas")

if not st.session_state.logado:
    modo = st.radio("Acesso", ["Entrar", "Solicitar cadastro"])

    usuarios = carregar_usuarios()

    if modo == "Entrar":
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if email in usuarios:
                if usuarios[email]["senha"] == hash_senha(senha):
                    if usuarios[email]["aprovado"]:
                        st.session_state.logado = True
                        st.session_state.email = email
                        st.experimental_rerun()
                    else:
                        st.error("Cadastro ainda não aprovado.")
                else:
                    st.error("Senha incorreta.")
            else:
                st.error("Usuário não encontrado.")

    else:
        nome = st.text_input("Nome")
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")

        if st.button("Solicitar cadastro"):
            if email in usuarios:
                st.warning("Usuário já cadastrado.")
            else:
                usuarios[email] = {
                    "nome": nome,
                    "senha": hash_senha(senha),
                    "aprovado": False
                }
                salvar_usuarios(usuarios)
                st.success("Cadastro enviado para aprovação do administrador.")

    st.stop()

# =========================
# PAINEL ADMIN
# =========================
usuarios = carregar_usuarios()

if st.session_state.email == ADMIN_EMAIL:
    st.subheader("👑 Painel do Administrador")

    pendentes = {e: u for e, u in usuarios.items() if not u["aprovado"]}

    if pendentes:
        for email, dados in pendentes.items():
            col1, col2 = st.columns([3, 1])
            col1.write(f"📧 {email} | {dados['nome']}")
            if col2.button("Aprovar", key=email):
                usuarios[email]["aprovado"] = True
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
    if descricao and valor > 0:
        salvar_despesa(st.session_state.email, descricao, valor)
        st.success("Despesa registrada.")
    else:
        st.warning("Preencha descrição e valor.")

df = carregar_despesas(st.session_state.email)

if not df.empty:
    st.subheader("📋 Despesas registradas")

    for i, row in df.iterrows():
        col1, col2, col3 = st.columns([4, 2, 1])
        col1.write(row["descricao"])
        col2.write(f"R$ {row['valor']:.2f}")
        if col3.button("❌", key=f"del_{i}"):
            excluir_despesa(i, st.session_state.email)
            st.experimental_rerun()

    st.subheader("📈 Dashboard")
    df["mes"] = pd.to_datetime(df["data"]).dt.to_period("M").astype(str)
    resumo = df.groupby("mes")["valor"].sum()
    st.bar_chart(resumo)

if st.button("Sair"):
    st.session_state.logado = False
    st.experimental_rerun()
