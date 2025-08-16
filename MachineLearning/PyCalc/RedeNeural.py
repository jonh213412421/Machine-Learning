import numpy as np
import streamlit as st
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt
from pysr import PySRRegressor

def fit(coordenadas, epochs):
    parar = st.button("Parar", key="botao_parar")
    print(f"parar no loop: {parar}")
    X_train = np.array([p["x"] for p in coordenadas], dtype=np.float32).reshape(-1, 1)
    y_train = np.array([p["y"] for p in coordenadas], dtype=np.float32).reshape(-1, 1)
    if st.session_state.get("parar", False):
        st.warning("Treinamento interrompido.")
        st.session_state.clear()
        st.rerun()  # Reinicia app com tudo resetado
        return
    model = Sequential([
        Dense(25, input_dim=1, activation='relu'),
        Dense(25, activation='relu'),
        Dense(1)
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

    plot_placeholder = st.empty()
    progress_bar = st.progress(0)
    status_placeholder = st.empty()

    # Escala fixa
    x_min, x_max = X_train.min(), X_train.max()
    y_min, y_max = y_train.min(), y_train.max()
    padding_x = 0.1 * (x_max - x_min + 1e-5)
    padding_y = 0.1 * (y_max - y_min + 1e-5)

    for epoch in range(epochs):
        print(f"botão parar na epoch {epoch}")
        if st.session_state.iniciado:

            st.markdown("""
                <style>
                div.st-key-botao_parar button {
                    background-color: red !important;
                    color: white !important;
                }
                div.st-key-parar button:hover {
                    box-shadow: 0px 4px 12px rgba(255, 0, 0, 0.6);
                    transform: scale(1.05);
                }
                </style>
            """, unsafe_allow_html=True)


        y_pred = model.predict(X_train, verbose=0)

        # Atualiza gráfico
        fig, ax = plt.subplots()
        ax.scatter(X_train, y_train, color='blue', label='Verdadeiros')
        ax.scatter(X_train, y_pred, color='red', marker='x', label='Previstos')
        ax.set_xlim(x_min - padding_x, x_max + padding_x)
        ax.set_ylim(y_min - padding_y, y_max + padding_y)
        ax.set_title(f"Epoch {epoch + 1}/{epochs}")
        ax.legend()
        plot_placeholder.pyplot(fig)

        status_placeholder.markdown(
            f"<h3 style='text-align: center;'>Trabalhando... {((epoch + 1) / epochs) * 100:.2f}%</h3>",
            unsafe_allow_html=True
        )
        progress_bar.progress((epoch + 1) / epochs)
