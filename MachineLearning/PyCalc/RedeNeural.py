import time
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

def fit(modelo, coordenadas, epochs, tamanho_rede, i, parar, plot_placeholder, progress_bar, status_placeholder):
    print(tamanho_rede)

    X_train = np.array([p["x"] for p in coordenadas], dtype=np.float32).reshape(-1, 1)
    y_train = np.array([p["y"] for p in coordenadas], dtype=np.float32).reshape(-1, 1)

    if parar:
        print(st.session_state.iniciado)
        st.session_state.parar = True
        st.session_state.iniciado = False
        return 0

    # Escala fixa
    x_min, x_max = X_train.min(), X_train.max()
    y_min, y_max = y_train.min(), y_train.max()
    padding_x = 0.1 * (x_max - x_min + 1e-5)
    padding_y = 0.1 * (y_max - y_min + 1e-5)


    hist = modelo.fit(X_train, y_train, epochs=1, verbose=0)
    perda = hist.history['loss'][0]

    y_pred = modelo.predict(X_train, verbose=0)

    # Atualiza gráfico
    if i % 10 == 0 or i==epochs-1:
        fig, ax = plt.subplots()
        ax.scatter(X_train, y_train, color='blue', label='Verdadeiros')
        ax.scatter(X_train, y_pred, color='red', marker='x', label='Previstos pelo Modelo')
        ax.set_xlim(x_min - padding_x, x_max + padding_x)
        ax.set_ylim(y_min - padding_y, y_max + padding_y)
        ax.set_title(f"Treinando... ({i + 1}/{epochs})", fontweight="bold", fontsize=20)
        if i == epochs-1:
            ax.set_title("Treinado!", color="green", fontweight="bold", fontsize=20)
            ax.legend()
        ax.legend()
        plot_placeholder.pyplot(fig)

        status_placeholder.markdown(
            f"<h3 style='text-align: center;'>Trabalhando... {((i + 1) / epochs) * 100:.2f}% | Perda: {perda:.4f}</h3>",
            unsafe_allow_html=True
        )
        progress_bar.progress((i + 1) / epochs)

    return y_pred
