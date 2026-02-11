import streamlit as st
import json
import os
import hashlib
import pandas as pd

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
# CARREGAMENTO
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

        if email == ADMIN_EMAIL and senha == ADMIN_PASSWORD:
            st.session_state.usuario = email
            st.session_state.admin = True
            st.rerun()

        elif email in usuarios:
            if not usuarios[email]["aprovado"]:
                st.error("Usuário ainda não aprovado.")
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
            st.success("Cadastro realizado. Aguarde aprovação.")

# ===============================
# PAINEL ADMIN
# ===============================
def painel_admin():
    st.title("🛠️ Painel do Administrador")

    for email, dados in list(usuarios.items()):
        col1, col2, col3 = st.columns([4, 2, 2])

        col1.write(email)

        if not dados["aprovado"]:
            if col2.button("Aprovar", key=f"ap_{email}"):
                usuarios[email]["aprovado"] = True
                salvar_json(USUARIOS_FILE, usuarios)
                st.rerun()
        else:
            col2.success("Aprovado")

        if col3.button("❌ Excluir", key=f"ex_{email}"):
            excluir_usuario(email)
            st.rerun()

    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()

def excluir_usuario(email):
    usuarios.pop(email, None)
    despesas.pop(email, None)
    salvar_json(USUARIOS_FILE, usuarios)
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

    # ===== Nova Despesa =====
    st.subheader("➕ Nova despesa")
    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor", min_value=0.0, format="%.2f")

    if st.button("Adicionar"):
        novo_id = len(despesas[usuario]) + 1
        despesas[usuario].append({
            "id": novo_id,
            "descricao": descricao,
            "valor": valor
        })
        salvar_json(DESPESAS_FILE, despesas)
        st.success("Despesa adicionada.")
        st.rerun()

    # ===== Lista + Exclusão =====
    st.subheader("📋 Minhas despesas")
    total = 0

    for d in despesas[usuario]:
        col1, col2, col3 = st.columns([4, 2, 1])
        col1.write(d["descricao"])
        col2.write(f"R$ {d['valor']:.2f}")
        total += d["valor"]

        if col3.button("🗑️", key=f"del_{d['id']}"):
            despesas[usuario] = [x for x in despesas[usuario] if x["id"] != d["id"]]
            salvar_json(DESPESAS_FILE, despesas)
            st.rerun()

    st.metric("💵 Total gasto", f"R$ {total:.2f}")

    # ===== DASHBOARD =====
    if despesas[usuario]:
        st.subheader("📊 Dashboard")

        df = pd.DataFrame(despesas[usuario])

        st.bar_chart(df.set_index("descricao")["valor"])
        st.pyplot(
            df.set_index("descricao")["valor"].plot.pie(
                autopct="%1.1f%%",
                ylabel=""
            ).figure
        )

    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()

# ===============================
# CONTROLE
# ===============================
if "usuario" not in st.session_state:
    login()
else:
    if st.session_state.get("admin"):
        painel_admin()
    else:
        painel_usuario()
