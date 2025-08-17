import streamlit as st
import numpy as np
import pandas as pd
import RedeNeural

st.markdown("<h1 style='text-align: center;'>Calculadora de Regressão Polinomial - CRP</h1>", unsafe_allow_html=True)
st.markdown("## Entre com os pontos ou faça o upload de um arquivo CSV (pontos devem ser separados por um espaço)")

if "coordenadas" not in st.session_state:
    st.session_state.coordenadas = [{"x": 0.0, "y": 0.0}]

if "parar_placeholder" not in st.session_state:
    st.session_state.parar_placeholder = st.empty()

coordenadas = st.session_state.coordenadas
st.session_state.parar = False
parar = st.session_state.parar

print(f"coordenadas na memória logo antes do expander: {coordenadas}")
print(f"len do array de coordenadas: {len(coordenadas)}")

def cheio(coord):
    return (coord["x"] != 0.0) or (coord["y"] != 0.0)

st.sidebar.title("Instruções")
with st.sidebar:
    st.markdown("Carregue as coordenadas manualmente ou por meio de um arquivo csv.\n"
            "## IMPORTANTE: Caso carregue o arquivo csv, as coordenadas manuais sumirão")

#adiciona barra lateral de configurações
st.sidebar.title("Configurações")
with st.sidebar.expander("Parâmetros avançados"):
    epochs = st.slider("quantidade de eras de treinamento", 100, 10000, value=2500)
    tamanho_rede = st.slider("número de nodes na rede", 10, 50, value=25)

# adiciona possibilidade de fazer upload de arquivo
uploaded_file = st.file_uploader("Escolha um arquivo CSV", ".csv", accept_multiple_files=False)

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=r"[;,\s]+", engine="python", header=None)
    print(df)
    coordenadas = [{"x": float(row[0]), "y": float(row[1])} for row in df.to_numpy()]
    st.session_state.coordenadas = coordenadas
    print(st.session_state.coordenadas)

# Interface de entrada
if not uploaded_file:
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
ultimo = coordenadas[-1]
filled_now = cheio(ultimo)

print(f"último: {ultimo}")
print(f"filled_now: {filled_now}")

if filled_now and not uploaded_file:
    coordenadas.append({"x": 0.0, "y": 0.0})
    st.session_state[f"x_{len(coordenadas) - 1}"] = 0.0
    st.session_state[f"y_{len(coordenadas) - 1}"] = 0.0
    with col1:
        st.number_input(f"X[{len(coordenadas)}]", key=f"x_{len(coordenadas) -1}", step=1.0, format="%.2f")
    with col2:
        st.number_input(f"Y[{len(coordenadas)}]", key=f"y_{len(coordenadas) -1}", step=1.0, format="%.2f")
print(f"coordenadas no final: {coordenadas}")

#botão para começar a regressão
if "iniciado" not in st.session_state:
    st.session_state.iniciado = False

if not st.session_state.iniciado:

    iniciar = st.button("Iniciar", key="iniciar")

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

    if iniciar:
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
        RedeNeural.fit([{"x": x, "y": x ** 3} for x in np.linspace(-10, 10, 100)], epochs)

else:
        st.session_state.parar = True
        st.session_state.iniciado = False
