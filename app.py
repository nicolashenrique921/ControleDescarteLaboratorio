import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime
from fpdf import FPDF
import io

# --- CONEXÃO COM SUPABASE (POSTGRESQL) ---
# O Streamlit gerencia a conexão automaticamente via Secrets
conn = st.connection("postgresql", type="sql")

# --- FUNÇÕES DE DADOS ---
def carregar_dados():
    # Busca dados do Supabase
    df = conn.query("SELECT * FROM descartes ORDER BY data DESC;", ttl="0")
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
    return df

def salvar_registro(dados):
    with conn.session as s:
        s.execute(
            "INSERT INTO descartes (data, equipamento, modelo, identificador, defeitos, descricao, semana, mes, ano) "
            "VALUES (:data, :equipamento, :modelo, :identificador, :defeitos, :descricao, :semana, :mes, :ano)",
            params=dados
        )
        s.commit()

def excluir_registro(id_registro):
    with conn.session as s:
        s.execute("DELETE FROM descartes WHERE id = :id", params={"id": id_registro})
        s.commit()

# --- CONFIGURAÇÕES DE TIPOS (Ainda em JSON para facilitar a sua edição rápida) ---
CONFIG_FILE = "configuracoes.json"
def carregar_config():
    if not os.path.exists(CONFIG_FILE):
        return {"Equipamentos": {"ONT": ["Fibracom"], "ONU": ["Intelbras"]}, "Defeitos": ["Queimado"]}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

# --- INTERFACE ---
st.set_page_config(page_title="Gestão Lab TI - Supabase", layout="wide")
config = carregar_config()

st.title("🖥️ Gestão de Descartes Cloud (Supabase)")

aba_dash, aba_reg, aba_config = st.tabs(["📊 Dashboard", "📝 Registrar", "⚙️ Config"])

with aba_dash:
    df = carregar_dados()
    if not df.empty:
        sub1, sub2 = st.tabs(["📈 Gráficos", "🗑️ Gerenciar"])
        
        with sub1:
            # Filtros e Gráficos (Mesmo código anterior, mas usando o DF do Postgres)
            col1, col2 = st.columns(2)
            periodo = col1.selectbox("Período", ["Tudo", "Mês Atual", "Semana Atual"])
            
            # Lógica de filtragem do Pandas permanece igual...
            st.dataframe(df, use_container_width=True) # Exemplo simples
            
        with sub2:
            st.write("### Exclusão de Registros")
            for _, row in df.iterrows():
                with st.expander(f"ID: {row['id']} | {row['equipamento']} - {row['modelo']}"):
                    if st.button(f"Confirmar Exclusão #{row['id']}", key=f"del_{row['id']}"):
                        excluir_registro(row['id'])
                        st.success("Excluído!")
                        st.rerun()
    else:
        st.info("Nenhum dado no Supabase.")

with aba_reg:
    with st.form("registro_form", clear_on_submit=True):
        # Campos de input...
        tipo_sel = st.selectbox("Tipo", list(config["Equipamentos"].keys()))
        modelo_sel = st.selectbox("Modelo", config["Equipamentos"][tipo_sel])
        identificador = st.text_input("S/N ou MAC")
        defeitos_sel = st.multiselect("Defeitos", config["Defeitos"])
        obs = st.text_area("Observações")
        
        if st.form_submit_button("Salvar no Cloud"):
            agora = datetime.now()
            dados_dict = {
                "data": agora, "equipamento": tipo_sel, "modelo": modelo_sel,
                "identificador": identificador, "defeitos": ", ".join(defeitos_sel),
                "descricao": obs, "semana": int(agora.isocalendar()[1]),
                "mes": int(agora.month), "ano": int(agora.year)
            }
            salvar_registro(dados_dict)
            st.success("Enviado para o Supabase!")
            st.rerun()

# --- ABA CONFIG (Igual ao anterior para salvar o arquivo JSON de modelos) ---