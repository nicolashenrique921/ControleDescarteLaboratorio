import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import json
import os
from datetime import datetime
from fpdf import FPDF
import io

# --- CONFIGURAÇÕES DO BANCO DE DADOS ---
DB_NAME = "dados_descarte.db"
CONFIG_FILE = "configuracoes.json"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Cria a tabela se não existir
    c.execute('''CREATE TABLE IF NOT EXISTS descartes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  data TEXT,
                  equipamento TEXT,
                  modelo TEXT,
                  identificador TEXT,
                  defeitos TEXT,
                  descricao TEXT,
                  semana INTEGER,
                  mes INTEGER,
                  ano INTEGER)''')
    conn.commit()
    conn.close()

def carregar_dados_db():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM descartes", conn)
    conn.close()
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
    return df

def salvar_registro_db(dados):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO descartes 
                 (data, equipamento, modelo, identificador, defeitos, descricao, semana, mes, ano)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', dados)
    conn.commit()
    conn.close()

def excluir_registro_db(id_registro):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM descartes WHERE id=?", (id_registro,))
    conn.commit()
    conn.close()

# Inicializa o banco ao abrir o app
init_db()

# --- (Restante das funções de config e exportação permanecem similares) ---

st.set_page_config(page_title="Gestão de Descartes DB", layout="wide")
config = json.load(open(CONFIG_FILE)) if os.path.exists(CONFIG_FILE) else {"Equipamentos": {}, "Defeitos": []}

aba_dash, aba_reg, aba_config = st.tabs(["📊 Métricas e Gestão", "📝 Novo Registro", "⚙️ Configurações"])

# --- ABA 1: DASHBOARD ---
with aba_dash:
    df = carregar_dados_db()
    if not df.empty:
        sub_tab1, sub_tab2 = st.tabs(["📈 Gráficos", "🗑️ Gerenciar"])
        
        with sub_tab1:
            # Lógica de filtros igual à anterior, usando o df vindo do SQLite
            col_f1, col_f2 = st.columns(2)
            periodo = col_f1.selectbox("Período", ["Tudo", "Mês Atual", "Semana Atual"])
            
            df_filtrado = df # Aplicar filtros de data aqui como antes
            
            st.metric("Total", len(df_filtrado))
            # Gráficos... (código anterior funciona igual)

        with sub_tab2:
            st.write("### Lista de Registros (Banco de Dados)")
            for index, row in df.iterrows():
                with st.expander(f"ID {row['id']} | {row['equipamento']} - {row['modelo']}"):
                    st.write(f"SN: {row['identificador']}")
                    if st.button(f"Confirmar Exclusão do ID {row['id']}", key=f"del_{row['id']}"):
                        excluir_registro_db(row['id'])
                        st.success("Excluído!")
                        st.rerun()
    else:
        st.info("Banco de dados vazio.")

# --- ABA 2: REGISTRO ---
with aba_reg:
    with st.form("form_registro"):
        # Inputs...
        if st.form_submit_button("Salvar no Banco"):
            agora = datetime.now()
            dados = (agora.strftime("%Y-%m-%d %H:%M:%S"), tipo_sel, modelo_sel, 
                     identificador, ", ".join(defeitos_sel), obs, 
                     agora.isocalendar()[1], agora.month, agora.year)
            salvar_registro_db(dados)
            st.success("Salvo no SQLite!")
            st.rerun()