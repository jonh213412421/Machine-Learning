import numpy as np
import streamlit as st
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt

def fit(coordenadas, epochs):

    X_train = np.array([p["x"] for p in coordenadas], dtype=np.float32).reshape(-1, 1)
    y_train = np.array([p["y"] for p in coordenadas], dtype=np.float32).reshape(-1, 1)

    model = Sequential([
        Dense(25, input_dim=1, activation='relu'),
        Dense(25, activation='relu'),
        Dense(1)
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

    plot_placeholder = st.empty()
    progress_bar = st.progress(0)
    status_placeholder = st.empty()
    button_placeholder = st.empty()

    with button_placeholder:
        parar = st.button("Parar", key="botao_parar_treinamento")
        if parar:
            st.session_state.parar = True
            st.session_state.iniciado = False
            return

    # Escala fixa
    x_min, x_max = X_train.min(), X_train.max()
    y_min, y_max = y_train.min(), y_train.max()
    padding_x = 0.1 * (x_max - x_min + 1e-5)
    padding_y = 0.1 * (y_max - y_min + 1e-5)

    for epoch in range(epochs):

        print(f"botão parar na epoch {epoch}")

        model.fit(X_train, y_train, epochs=1, verbose=0)

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
