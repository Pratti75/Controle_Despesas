import streamlit as st
import json
import os
import hashlib
import pandas as pd
import matplotlib.pyplot as plt

# =============================
# CONFIGURAÇÕES
# =============================
USUARIOS_FILE = "usuarios.json"
DESPESAS_FILE = "despesas.json"

ADMIN_EMAIL = st.secrets["ADMIN_EMAIL"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# =============================
# FUNÇÕES BASE
# =============================
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

# =============================
# CARREGAMENTO
# =============================
usuarios = carregar_json(USUARIOS_FILE, {})
despesas = carregar_json(DESPESAS_FILE, {})

# =============================
# LOGIN / CADASTRO
# =============================
def tela_login():
    st.title("🔐 Controle de Despesas")

    tab1, tab2 = st.tabs(["Entrar", "Cadastrar"])

    with tab1:
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            if email == ADMIN_EMAIL and senha == ADMIN_PASSWORD:
                st.session_state.usuario = email
                st.session_state.admin = True
                st.rerun()

            elif email in usuarios:
                if not usuarios[email]["aprovado"]:
                    st.error("Usuário não aprovado pelo administrador.")
                elif usuarios[email]["senha"] == hash_senha(senha):
                    st.session_state.usuario = email
                    st.session_state.admin = False
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
            else:
                st.error("Usuário não encontrado.")

    with tab2:
        novo_email = st.text_input("Novo e-mail")
        nova_senha = st.text_input("Nova senha", type="password")

        if st.button("Solicitar cadastro"):
            if novo_email in usuarios:
                st.warning("Usuário já existe.")
            else:
                usuarios[novo_email] = {
                    "senha": hash_senha(nova_senha),
                    "aprovado": False
                }
                salvar_json(USUARIOS_FILE, usuarios)
                st.success("Cadastro solicitado. Aguarde aprovação.")

# =============================
# PAINEL ADMIN
# =============================
def painel_admin():
    st.title("🛠️ Administração de Usuários")

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
            usuarios.pop(email)
            despesas.pop(email, None)
            salvar_json(USUARIOS_FILE, usuarios)
            salvar_json(DESPESAS_FILE, despesas)
            st.rerun()

    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()

# =============================
# PAINEL USUÁRIO
# =============================
def painel_usuario():
    usuario = st.session_state.usuario
    st.title("💰 Minhas Despesas")

    if usuario not in despesas:
        despesas[usuario] = []
        salvar_json(DESPESAS_FILE, despesas)

    # ➕ Nova despesa
    st.subheader("➕ Adicionar despesa")
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor", min_value=0.0, step=0.01)

    if st.button("Adicionar"):
        despesas[usuario].append({
            "id": len(despesas[usuario]) + 1,
            "descricao": desc,
            "valor": valor
        })
        salvar_json(DESPESAS_FILE, despesas)
        st.rerun()

    # 📋 Lista de despesas
    st.subheader("📋 Despesas cadastradas")
    total = 0

    for d in despesas[usuario]:
        col1, col2, col3 = st.columns([4, 2, 1])
        col1.write(d["descricao"])
        col2.write(f"R$ {d['valor']:.2f}")
        total += d["valor"]

        if col3.button("🗑️", key=f"del_{usuario}_{d['id']}"):
            despesas[usuario] = [x for x in despesas[usuario] if x["id"] != d["id"]]
            salvar_json(DESPESAS_FILE, despesas)
            st.rerun()

    st.metric("💵 Total gasto", f"R$ {total:.2f}")

    # 📊 DASHBOARD
    if despesas[usuario]:
        st.subheader("📊 Dashboard")

        df = pd.DataFrame(despesas[usuario])

        # Gráfico de barras
        st.bar_chart(df.set_index("descricao")["valor"])

        # Gráfico de pizza (MATPLOTLIB)
        fig, ax = plt.subplots()
        ax.pie(
            df["valor"],
            labels=df["descricao"],
            autopct="%1.1f%%",
            startangle=90
        )
        ax.axis("equal")
        st.pyplot(fig)

    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()

# =============================
# CONTROLE PRINCIPAL
# =============================
if "usuario" not in st.session_state:
    tela_login()
else:
    if st.session_state.get("admin"):
        painel_admin()
    else:
        painel_usuario()
