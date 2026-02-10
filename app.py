import streamlit as st
import json
import os

# =============================
# CONFIGURAÇÃO DA PÁGINA
# =============================
st.set_page_config(
    page_title="Controle de Despesas",
    page_icon="💰",
    layout="centered"
)

USUARIOS_FILE = "usuarios.json"

ADMIN_EMAIL = st.secrets["ADMIN_EMAIL"]
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]

# =============================
# FUNÇÕES DE PERSISTÊNCIA
# =============================
def carregar_usuarios():
    if not os.path.exists(USUARIOS_FILE):
        return {}
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)

# =============================
# AUTENTICAÇÃO
# =============================
def autenticar(email, senha, usuarios):
    # ADMINISTRADOR
    if email == ADMIN_EMAIL and senha == ADMIN_PASSWORD:
        return {"tipo": "admin", "aprovado": True}

    # USUÁRIO COMUM
    if email in usuarios:
        usuario = usuarios[email]
        if usuario["senha"] == senha:
            return {"tipo": "usuario", "aprovado": usuario["aprovado"]}

    return None

# =============================
# TELAS
# =============================
def tela_login():
    st.title("🔐 Login")

    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        usuarios = carregar_usuarios()
        resultado = autenticar(email, senha, usuarios)

        if resultado is None:
            st.error("E-mail ou senha inválidos")

        elif resultado["tipo"] == "admin":
            st.session_state.usuario = email
            st.session_state.tipo = "admin"
            st.rerun()

        elif resultado["aprovado"]:
            st.session_state.usuario = email
            st.session_state.tipo = "usuario"
            st.rerun()

        else:
            st.warning("Cadastro pendente de aprovação do administrador")

    st.divider()
    tela_cadastro()

def tela_cadastro():
    st.subheader("📝 Cadastro de Usuário")

    email = st.text_input("Novo e-mail", key="cad_email")
    senha = st.text_input("Nova senha", type="password", key="cad_senha")

    if st.button("Cadastrar"):
        if email == ADMIN_EMAIL:
            st.error("Este e-mail é exclusivo do administrador")
            return

        usuarios = carregar_usuarios()

        if email in usuarios:
            st.error("Usuário já cadastrado")
            return

        usuarios[email] = {
            "senha": senha,
            "aprovado": False
        }

        salvar_usuarios(usuarios)
        st.success("Cadastro realizado. Aguarde aprovação do administrador.")

def painel_admin():
    st.title("👑 Painel do Administrador")

    usuarios = carregar_usuarios()

    if not usuarios:
        st.info("Nenhum usuário cadastrado.")
        return

    for email, dados in usuarios.items():
        col1, col2, col3 = st.columns([4, 2, 2])

        col1.write(email)
        col2.write("✅ Aprovado" if dados["aprovado"] else "⏳ Pendente")

        if not dados["aprovado"]:
            if col3.button("Aprovar", key=email):
                usuarios[email]["aprovado"] = True
                salvar_usuarios(usuarios)
                st.success(f"{email} aprovado com sucesso")
                st.rerun()

def painel_usuario():
    st.title("📊 Controle de Despesas")
    st.write(f"Usuário logado: **{st.session_state.usuario}**")
    st.info("Dashboard de despesas será exibido aqui.")

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
