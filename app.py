import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF
import io

# --- CONEXÃO ---
conn = st.connection("postgresql", type="sql")

# --- FUNÇÕES DE DADOS (REGISTROS) ---
def carregar_dados():
    return conn.query("SELECT * FROM descartes ORDER BY data DESC;", ttl=0)

def salvar_registro(d):
    with conn.session as s:
        s.execute(
            "INSERT INTO descartes (data, equipamento, modelo, identificador, defeitos, descricao, semana, mes, ano) "
            "VALUES (:data, :equipamento, :modelo, :identificador, :defeitos, :descricao, :semana, :mes, :ano)",
            params=d
        )
        s.commit()

def excluir_registro(id_reg):
    with conn.session as s:
        s.execute("DELETE FROM descartes WHERE id = :id", params={"id": id_reg})
        s.commit()

# --- FUNÇÕES DE CONFIGURAÇÃO (AGORA NO DB) ---
def carregar_config_equipamentos():
    df = conn.query("SELECT tipo, modelo FROM config_equipamentos ORDER BY tipo, modelo;", ttl=0)
    # Transforma o DF em um dicionário agrupado { 'ONT': ['Huawei', 'Fibracom'], ... }
    dict_equip = {}
    for t in df['tipo'].unique():
        dict_equip[t] = df[df['tipo'] == t]['modelo'].tolist()
    return dict_equip

def carregar_config_defeitos():
    df = conn.query("SELECT defeito FROM config_defeitos ORDER BY defeito;", ttl=0)
    return df['defeito'].tolist()

def add_modelo_db(tipo, modelo):
    with conn.session as s:
        s.execute("INSERT INTO config_equipamentos (tipo, modelo) VALUES (:t, :m) ON CONFLICT DO NOTHING", {"t": tipo, "m": modelo})
        s.commit()

def add_defeito_db(defeito):
    with conn.session as s:
        s.execute("INSERT INTO config_defeitos (defeito) VALUES (:d) ON CONFLICT DO NOTHING", {"d": defeito})
        s.commit()

# --- INTERFACE ---
st.set_page_config(page_title="Lab TI Cloud", layout="wide")
st.title("🖥️ Gestão de Descartes 100% Cloud")

# Carregar listas dinâmicas do Banco de Dados
mapa_equipamentos = carregar_config_equipamentos()
lista_defeitos = carregar_config_defeitos()

aba_dash, aba_reg, aba_config = st.tabs(["📊 Dashboard e Gestão", "📝 Novo Registro", "⚙️ Configurações"])

# --- ABA 1: DASHBOARD ---
with aba_dash:
    df = carregar_dados()
    if not df.empty:
        sub1, sub2 = st.tabs(["📈 Gráficos", "🗑️ Lista/Exclusão"])
        with sub1:
            # Filtros e Gráficos (Mesma lógica anterior)
            st.write("Gráficos de métricas aqui...")
            st.dataframe(df, use_container_width=True)
        with sub2:
            for _, row in df.iterrows():
                with st.expander(f"ID {row['id']} | {row['equipamento']} {row['modelo']} | {row['data']}"):
                    if st.button(f"Excluir #{row['id']}", key=f"btn_{row['id']}"):
                        excluir_registro(row['id'])
                        st.rerun()
    else:
        st.info("Nenhum registro encontrado.")

# --- ABA 2: REGISTRO ---
with aba_reg:
    if not mapa_equipamentos:
        st.warning("Adicione tipos de equipamentos na aba Configurações primeiro.")
    else:
        with st.form("form_reg", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                t_sel = st.selectbox("Tipo", list(mapa_equipamentos.keys()))
                m_sel = st.selectbox("Modelo", mapa_equipamentos[t_sel])
                ident = st.text_input("S/N ou MAC")
            with c2:
                d_sel = st.multiselect("Defeitos", lista_defeitos)
                obs = st.text_area("Observações")
            if st.form_submit_button("Salvar no Supabase"):
                agora = datetime.now()
                salvar_registro({
                    "data": agora, "equipamento": t_sel, "modelo": m_sel, "identificador": ident,
                    "defeitos": ", ".join(d_sel), "descricao": obs,
                    "semana": agora.isocalendar()[1], "mes": agora.month, "ano": agora.year
                })
                st.success("Salvo!")
                st.rerun()

# --- ABA 3: CONFIG ---
with aba_config:
    st.subheader("Gerenciar Opções do Banco de Dados")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Adicionar Modelo")
        # Lista de tipos fixos ou você pode criar uma tabela só para tipos também
        tipo_base = st.selectbox("Tipo de Equipamento", ["ONT", "ONU", "Roteador", "Fonte POE", "Placa", "Switch", "Antena Rádio"])
        novo_m = st.text_input("Novo Modelo/Marca")
        if st.button("Cadastrar Modelo"):
            if novo_m:
                add_modelo_db(tipo_base, novo_m)
                st.success(f"Modelo {novo_m} adicionado!")
                st.rerun()

    with col2:
        st.write("### Adicionar Defeito")
        novo_d = st.text_input("Nome do Defeito")
        if st.button("Cadastrar Defeito"):
            if novo_d:
                add_defeito_db(novo_d)
                st.success("Defeito adicionado!")
                st.rerun()