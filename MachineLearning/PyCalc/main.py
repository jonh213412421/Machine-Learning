import time
import streamlit as st
import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import RedeNeural

def cheio(coord):
    return (coord["x"] != 0.0) or (coord["y"] != 0.0)

st.markdown("<h1 style='text-align: center;'>Rede Neural de Regressão</h1>", unsafe_allow_html=True)
st.markdown("## Entre com os pontos ou faça o upload de um arquivo CSV (pontos devem ser separados por um espaço)")

#barra lateral
st.sidebar.title("Instruções")
with st.sidebar:
    st.markdown("Carregue as coordenadas manualmente ou por meio de um arquivo csv.\n"
            "## IMPORTANTE: Caso carregue o arquivo csv, as coordenadas manuais serão substituídas")

#adiciona barra lateral de configurações
st.sidebar.title("Configurações")

def criar_modelo():
    st.session_state.modelo = Sequential([
        Dense(tamanho_rede, input_dim=1, activation=st.session_state.funcao_ativacao),
        Dense(tamanho_rede, activation=st.session_state.funcao_ativacao),
        Dense(1)
    ])
    st.session_state.modelo.compile(optimizer=Adam(learning_rate=st.session_state.aprendizado), loss='mse')

#estabelece variáveis do session_state
if "coordenadas" not in st.session_state:
    st.session_state.coordenadas = [{"x": 0.0, "y": 0.0}]

if "indice_epoca" not in st.session_state:
    st.session_state.indice_epoca = 0

if "perda" not in st.session_state:
    st.session_state.perda = 0

if "estado_treinamento" not in st.session_state:
    st.session_state.estado_treinamento = None

if "modelo_treinado" not in st.session_state:
    st.session_state.modelo_treinado = False

if "parar_placeholder" not in st.session_state:
    st.session_state.parar_placeholder = st.empty()

if "mostrar_csv_dialog" not in st.session_state:
    st.session_state.mostrar_csv_dialog = True

if "mostrar_tabela" not in st.session_state:
    st.session_state.mostrar_tabela = True

if "modelo treinado" not in st.session_state:
    st.session_state.modelo_treinado = False

if "iniciado" not in st.session_state:
    st.session_state.iniciado = False

#Começa com arquivo nulo carregado
uploaded_file = ""
print(f"arquivo carregado no início da execução: {uploaded_file}")

coordenadas = st.session_state.coordenadas
st.session_state.parar = False
parar = st.session_state.parar

print(f"coordenadas na memória logo antes do expander: {coordenadas}")
print(f"len do array de coordenadas: {len(coordenadas)}")

with st.sidebar.expander("Parâmetros avançados"):
    st.session_state.funcao_ativacao = st.selectbox("Escolha a função de ativação", options=["relu", "sigmoid", "linear", "softmax", "swish"])
    st.session_state.aprendizado = st.select_slider("Taxa de Aprendizado", [0.001, 0.01, 0.1], value=0.01, disabled=st.session_state.iniciado)
    epochs = st.slider("Quantidade de Eras de Treinamento", 100, 10000, value=2500, disabled=st.session_state.iniciado)
    tamanho_rede = st.slider("Número de Nodes na Rede", 5, 50, value=10, disabled=st.session_state.iniciado)
    st.button("Reconfigurar Modelo", on_click=criar_modelo, disabled=st.session_state.iniciado)

print(f"Função de ativação: {st.session_state.funcao_ativacao}")

#cria a rede neural. É por isso que o parâmetro "tamanho da rede vem antes"
if "modelo" not in st.session_state:
    st.session_state.modelo = Sequential([
        Dense(tamanho_rede, input_dim=1, activation="relu"),
        Dense(tamanho_rede, activation="relu"),
        Dense(1)
    ])
    st.session_state.modelo.compile(optimizer=Adam(learning_rate=0.01), loss='mse')

# adiciona possibilidade de fazer upload de arquivo
if st.session_state.mostrar_csv_dialog:
    uploaded_file = st.file_uploader("Escolha um arquivo CSV", ".csv", accept_multiple_files=False)

    if uploaded_file:
        st.session_state.coordenadas.clear()
        df = pd.read_csv(uploaded_file, sep=r"[;,\s]+", engine="python", header=0)
        print(df)
        coordenadas = [{"x": float(row[0]), "y": float(row[1])} for row in df.to_numpy()]
        st.session_state.coordenadas = coordenadas
        print(st.session_state.coordenadas)

if not st.session_state.iniciado:

    def iniciar():
        if len(coordenadas) == 1:
            st.warning("Nenhum dado foi inserido. Insira dados e tente novamente")
            time.sleep(2)
        st.session_state.iniciado = True
        st.session_state.epochs = epochs
        st.session_state.mostrar_csv_dialog = False
        st.session_state.mostrar_tabela = False

    iniciar = st.button("Iniciar", key="iniciar", on_click=iniciar)

    #estabelece o estilo do botão de iniciar
    st.markdown("""
        <style>
        div.st-key-iniciar button {
            background-color: green !important;
            color: white !important;
        }
        div.st-key-iniciar button:hover {
            box-shadow: 0px 4px 12px rgba(0, 255, 0, 0.6);
            transform: scale(1.05);
        }
        </style>
    """, unsafe_allow_html=True)

# Interface de entrada
if st.session_state.mostrar_tabela:
    with st.expander("Inserir pontos", expanded=True):
        for i in range(len(coordenadas)):
            col1, col2 = st.columns(2)
            key_x = f"x_{i}"
            key_y = f"y_{i}"

            print(f"key_x no loop: {key_x}")
            print(f"key_y no loop: {key_y}")

            # Garante que as chaves estejam no session_state antes da criação dos widgets
            if key_x not in st.session_state:
                st.session_state[key_x] = coordenadas[i]["x"]
            if key_y not in st.session_state:
                st.session_state[key_y] = coordenadas[i]["y"]

            with col1:
                st.number_input(f"X[{i+1}]", key=key_x, step=1.0, format="%.2f")
            with col2:
                st.number_input(f"Y[{i+1}]", key=key_y, step=1.0, format="%.2f")

        # Atualiza coordenadas com os valores atuais do session_state
        for i in range(len(coordenadas)):
            coordenadas[i]["x"] = st.session_state[f"x_{i}"]
            coordenadas[i]["y"] = st.session_state[f"y_{i}"]
            print(f"atualização de coordenada x no loop: {coordenadas[i]['x']}")
            print(f"atualização de coordenada y no loop: {coordenadas[i]['y']}")

#personaliza a área de upload de csv
st.markdown("""
    <style>
    .stFileUploader label {
        font-size: 22px !important;
        color: #2c3e50 !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Verifica se deve adicionar nova linha
try:
    ultimo = coordenadas[-1]
    filled_now = cheio(ultimo)
    print(f"último: {ultimo}")
    print(f"filled_now: {filled_now}")

except Exception as e:
    print(e)
    filled_now = True

if filled_now and not uploaded_file and st.session_state.mostrar_tabela:
    coordenadas.append({"x": 0.0, "y": 0.0})
    col1, col2 = st.columns(2)
    st.session_state[f"x_{len(coordenadas) - 1}"] = 0.0
    st.session_state[f"y_{len(coordenadas) - 1}"] = 0.0
    with col1:
        st.number_input(f"X[{len(coordenadas)}]", key=f"x_{len(coordenadas) -1}", step=1.0, format="%.2f")
    with col2:
        st.number_input(f"Y[{len(coordenadas)}]", key=f"y_{len(coordenadas) -1}", step=1.0, format="%.2f")
print(f"coordenadas no final: {coordenadas}")

if st.session_state.iniciado:

    # Muda o estilo do botão de iniciar - Display = none
    st.markdown("""
        <style>
        div.st-key-iniciar button {
            display: none;
            background-color: green !important;
            color: white !important;
        }
        div.st-key-iniciar button:hover {
            box-shadow: 0px 4px 12px rgba(0, 255, 0, 0.6);
            transform: scale(1.05);
        }
        </style>
    """, unsafe_allow_html=True)

    #Muda o estilo do botão de parar
    st.session_state.iniciado = True
    st.markdown("""
        <style>
        div.st-key-botao_parar_treinamento button {
            background-color: red !important;
            color: white !important;
        }
        div.st-key-botao_parar_treinamento button:hover {
            box-shadow: 0px 4px 12px rgba(255, 0, 0, 0.6);
            transform: scale(1.05);
        }
        </style>
    """, unsafe_allow_html=True)
    print("[REDE NEURAL INICIADA]")

    if not st.session_state.modelo_treinado:

        #Cria os placeholders antes da execução. Necessário para poder atualizar sempre o mesmo placeholder com o gráfico
        button_placeholder = st.empty()
        plot_placeholder = st.empty()
        progress_bar = st.progress(0)
        status_placeholder = st.empty()

        #função para parar no loop
        def parar():
            st.session_state.indice_epoca = 0
            st.session_state.coordenadas.clear()
            st.session_state.coordenadas = [{"x": 0.0, "y": 0.0}]
            st.session_state.modelo_treinado = False
            st.session_state.mostrar_csv_dialog = True
            st.session_state.mostrar_tabela = True
            st.session_state.parar = True
            st.session_state.iniciado = False
            st.session_state.estado_treinamento = None

        if st.session_state.indice_epoca == 0:
            with button_placeholder:
                st.session_state.parar = st.button("Parar", key="botao_parar_treinamento", on_click=parar)

        while st.session_state.indice_epoca < st.session_state.epochs:
            parar = st.session_state.parar
            st.session_state.estado_treinamento, st.session_state.perda = RedeNeural.fit(st.session_state.modelo, coordenadas, epochs, tamanho_rede, st.session_state.indice_epoca, parar, plot_placeholder, progress_bar, status_placeholder)
            print(f"y_pred: {st.session_state.estado_treinamento}")
            print(parar)

            st.session_state.indice_epoca = st.session_state.indice_epoca + 1

        button_placeholder.empty()
        plot_placeholder.empty()
        progress_bar.empty()
        st.session_state.modelo_treinado = True
        print(f"modelo treinado: {st.session_state.modelo_treinado}")
        st.session_state.coordenadas.clear()
        st.session_state.coordenadas = [{"x": 0.0, "y": 0.0}]
        if st.session_state.perda <= 100:
            status_placeholder.markdown("<h3 style='text-align:center; color:green;'>Modelo Treinado!</h3>",unsafe_allow_html=True)
        if st.session_state.perda > 100:
            status_placeholder.markdown(f"<h3 style='text-align:center; color:red;'>Modelo Treinado (perda: {st.session_state.perda:.2f})</h3>",unsafe_allow_html=True)

if st.session_state.modelo_treinado:

    def resetar():
        st.session_state.indice_epoca = 0
        st.session_state.coordenadas.clear()
        st.session_state.coordenadas = [{"x": 0.0, "y": 0.0}]
        st.session_state.modelo_treinado = False
        st.session_state.mostrar_csv_dialog = True
        st.session_state.mostrar_tabela = True
        st.session_state.parar = True
        st.session_state.iniciado = False
        st.session_state.estado_treinamento = None
        st.session_state.modelo = Sequential([
        Dense(tamanho_rede, input_dim=1, activation=st.session_state.funcao_ativacao),
        Dense(tamanho_rede, activation=st.session_state.funcao_ativacao),
        Dense(1)
        ])
        st.session_state.modelo.compile(optimizer=Adam(learning_rate=st.session_state.aprendizado), loss='mse')

    x = st.number_input("Entre com o X para ser previsto:", value=0.0, step=1.0, format="%.2f")
    if x is not None:
        y = st.session_state.modelo.predict(np.array(x, dtype=np.float32).reshape(-1, 1), verbose=0)[0][0]
        st.markdown(f"<span style='font-size:20px; font-weight:bold;'>Valor previsto para x = {x}: {y:.2f}</span>", unsafe_allow_html=True)

    st.button("Voltar ao início", on_click=resetar)
