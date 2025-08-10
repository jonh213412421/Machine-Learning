import streamlit as st
import numpy as np
import RedeNeural as rn

st.markdown("<h1 style='text-align: center;'>Calculadora de Regressão Polinomial - CRP</h1>", unsafe_allow_html=True)
st.markdown("## Entre com os pontos ou faça o upload de um arquivo CSV (pontos devem ser separados por um espaço)")

if "coordenadas" not in st.session_state:
    st.session_state.coordenadas = [{"x": 0.0, "y": 0.0}]

#print(f"coordenadas no session state logo após o if coordenadas: {st.session_state.coodenadas}")

#if "last_filled" not in st.session_state:
#    st.session_state.last_filled = False

coordenadas = st.session_state.coordenadas

print(f"coordenadas na memória logo antes do expander: {coordenadas}")
print(f"len do array de coordenadas: {len(coordenadas)}")

def cheio(coord):
    return (coord["x"] != 0.0) or (coord["y"] != 0.0)

st.sidebar.title("Configurações")
with st.sidebar.expander("Parâmetros avançados"):
    epochs = st.slider("quantidade de eras de treinamento", 3000, 10000, value=3000)

# Interface de entrada
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

st.markdown("<h1 style='text-align: center;'>Adicione um arquivo aqui</h1>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("", ".csv", accept_multiple_files=False, )

# Verifica se deve adicionar nova linha
ultimo = coordenadas[-1]
filled_now = cheio(ultimo)

print(f"último: {ultimo}")
print(f"filled_now: {filled_now}")

if filled_now:
    coordenadas.append({"x": 0.0, "y": 0.0})
    st.session_state[f"x_{len(coordenadas) - 1}"] = 0.0
    st.session_state[f"y_{len(coordenadas) - 1}"] = 0.0
    with col1:
        st.number_input(f"X[{len(coordenadas)}]", key=f"x_{len(coordenadas) -1}", step=1.0, format="%.2f")
    with col2:
        st.number_input(f"Y[{len(coordenadas)}]", key=f"y_{len(coordenadas) -1}", step=1.0, format="%.2f")
print(f"coordenadas no final: {coordenadas}")

parar = st.checkbox("parar")

rn.fit([{"x": x, "y": x ** 3} for x in np.linspace(-10, 10, 100)], 2500, parar=parar)
