import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime
import warnings

# Configurações iniciais da página
st.set_page_config(page_title="Gestão de Descartes - Lab TI", layout="wide")
warnings.filterwarnings('ignore')

# --- ARQUIVOS E PERSISTÊNCIA DE DADOS ---
DATA_FILE = "registro_descartes.csv"
CONFIG_FILE = "opcoes_defeitos.json"

# Tipos de Equipamento Fixos
TIPOS_EQUIPAMENTO = [
    "ONT", "ONU", "Roteador", "Fonte POE", 
    "Placa", "Switch", "Antena Rádio"
]

# Defeitos Iniciais (Padrão)
DEFEITOS_PADRAO = [
    "Queimado", "Quedas de sinal", "Porta LAN queimada", 
    "Não navegando rede Wireless", "Não sobe rede", 
    "LED queimado", "Antena/Carcaça avariada"
]

# Função para carregar defeitos
def carregar_defeitos():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFEITOS_PADRAO, f)
        return DEFEITOS_PADRAO
    else:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)

# Função para salvar novo defeito
def salvar_novo_defeito(novo_defeito):
    defeitos = carregar_defeitos()
    if novo_defeito and novo_defeito not in defeitos:
        defeitos.append(novo_defeito)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(defeitos, f)
        return True
    return False

# Função para carregar dados
def carregar_dados():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["Data", "Equipamento", "Defeitos", "Descricao", "Semana", "Mes", "Ano"])
    return pd.read_csv(DATA_FILE)

# Função para salvar registro
def salvar_registro(tipo, defeitos_selecionados, descricao):
    df = carregar_dados()
    agora = datetime.now()
    
    novo_registro = {
        "Data": agora,
        "Equipamento": tipo,
        "Defeitos": ", ".join(defeitos_selecionados), # Salva como string separada por vírgula
        "Descricao": descricao,
        "Semana": agora.isocalendar()[1],
        "Mes": agora.month,
        "Ano": agora.year
    }
    
    df = pd.concat([df, pd.DataFrame([novo_registro])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

# --- INTERFACE DO USUÁRIO ---

st.title("🖥️ Controle de Descarte - Laboratório TI")

# Criação das Abas
aba_dashboard, aba_registro, aba_config = st.tabs(["📊 Dashboard & Métricas", "📝 Registrar Descarte", "⚙️ Opções de Defeito"])

# --- ABA 1: DASHBOARD ---
with aba_dashboard:
    df = carregar_dados()
    
    if df.empty:
        st.info("Nenhum dado registrado ainda. Vá para a aba de Registro para começar.")
    else:
        # Converter coluna Data para datetime
        df['Data'] = pd.to_datetime(df['Data'])
        hoje = datetime.now()
        semana_atual = hoje.isocalendar()[1]
        mes_atual = hoje.month
        ano_atual = hoje.year

        # Filtros de Dados
        df_semana = df[(df['Semana'] == semana_atual) & (df['Ano'] == ano_atual)]
        df_mes = df[(df['Mes'] == mes_atual) & (df['Ano'] == ano_atual)]

        # --- SEÇÃO SEMANAL ---
        st.markdown("### 📅 Esta Semana")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Descartes (Semana)", len(df_semana))
        
        if not df_semana.empty:
            # Gráfico de Pizza: Por Tipo de Equipamento
            fig_tipo_sem = px.pie(df_semana, names='Equipamento', title='Descartes por Tipo (Semana)', hole=0.4)
            col2.plotly_chart(fig_tipo_sem, use_container_width=True)

            # Processamento para contar Defeitos individuais (pois podem ser múltiplos)
            defeitos_semana = df_semana['Defeitos'].str.split(', ', expand=True).stack().reset_index(level=1, drop=True)
            defeitos_semana.name = 'Defeito Individual'
            contagem_defeitos_sem = defeitos_semana.value_counts().reset_index()
            contagem_defeitos_sem.columns = ['Defeito', 'Qtd']
            
            fig_def_sem = px.bar(contagem_defeitos_sem, x='Qtd', y='Defeito', orientation='h', title="Principais Motivos (Semana)")
            col3.plotly_chart(fig_def_sem, use_container_width=True)
        else:
            st.warning("Sem dados nesta semana.")

        st.divider()

        # --- SEÇÃO MENSAL ---
        st.markdown("### 📆 Este Mês")
        col4, col5, col6 = st.columns(3)
        col4.metric("Total Descartes (Mês)", len(df_mes))

        if not df_mes.empty:
            # Gráfico de Pizza: Por Tipo de Equipamento
            fig_tipo_mes = px.pie(df_mes, names='Equipamento', title='Descartes por Tipo (Mês)', hole=0.4)
            col5.plotly_chart(fig_tipo_mes, use_container_width=True)

            # Processamento Defeitos Mês
            defeitos_mes = df_mes['Defeitos'].str.split(', ', expand=True).stack().reset_index(level=1, drop=True)
            contagem_defeitos_mes = defeitos_mes.value_counts().reset_index()
            contagem_defeitos_mes.columns = ['Defeito', 'Qtd']

            fig_def_mes = px.bar(contagem_defeitos_mes, x='Qtd', y='Defeito', orientation='h', title="Principais Motivos (Mês)")
            col6.plotly_chart(fig_def_mes, use_container_width=True)
        else:
             st.warning("Sem dados neste mês.")

# --- ABA 2: REGISTRO ---
with aba_registro:
    st.header("Novo Registro de Descarte")
    
    col_form1, col_form2 = st.columns(2)
    
    with col_form1:
        tipo_selecionado = st.selectbox("Tipo de Equipamento", TIPOS_EQUIPAMENTO)
        
        # Carrega lista dinâmica de defeitos
        lista_defeitos = carregar_defeitos()
        defeitos_selecionados = st.multiselect(
            "Selecione o(s) Defeito(s)", 
            options=lista_defeitos,
            help="Você pode selecionar mais de um defeito."
        )

    with col_form2:
        descricao = st.text_area("Descrição / Observações (Opcional)", height=145)

    if st.button("💾 Registrar Descarte", type="primary"):
        if not defeitos_selecionados:
            st.error("Por favor, selecione pelo menos um defeito.")
        else:
            salvar_registro(tipo_selecionado, defeitos_selecionados, descricao)
            st.success("Equipamento registrado com sucesso!")
            st.rerun() # Atualiza a página para limpar e atualizar gráficos

# --- ABA 3: CONFIGURAÇÕES ---
with aba_config:
    st.header("Gerenciar Opções de Defeito")
    st.write("Adicione novos motivos de descarte que aparecerão na lista de seleção.")
    
    novo_defeito_input = st.text_input("Nome do novo defeito")
    
    if st.button("➕ Adicionar Opção"):
        if salvar_novo_defeito(novo_defeito_input):
            st.success(f"Opção '{novo_defeito_input}' adicionada com sucesso!")
            st.rerun()
        else:
            st.warning("O campo está vazio ou o defeito já existe.")
            
    st.markdown("---")
    st.markdown("**Lista Atual de Defeitos:**")
    st.write(carregar_defeitos())