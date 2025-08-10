import numpy as np
import streamlit as st
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt
from pysr import PySRRegressor

def fit(coordenadas, epochs, parar):

    X_train = np.array([p["x"] for p in coordenadas], dtype=np.float32).reshape(-1, 1)
    y_train = np.array([p["y"] for p in coordenadas], dtype=np.float32).reshape(-1, 1)

    model = Sequential([
        Dense(25, input_dim=1, activation='relu'),
        Dense(25, activation='relu'),
        Dense(1)
    ])

    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

    plot_placeholder = st.empty()
    #cria os elementos
    progress_bar = st.progress(0)
    status_placeholder = st.empty()

    # Treinamento manual por época
    for epoch in range(epochs):

        # Previsões para plot
        y_pred = model.predict(X_train, verbose=0)

        # Atualiza gráfico de pontos
        fig, ax = plt.subplots()
        ax.scatter(X_train, y_train, color='blue', label='Verdadeiros')
        ax.scatter(X_train, y_pred, color='red', marker='x', label='Previstos')
        ax.set_title(f'Epoch {epoch + 1}/{epochs}')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.legend()
        plot_placeholder.pyplot(fig)
        status_placeholder.markdown(f"<h3 style='text-align: center;'>Trabalhando... {((epoch + 1) / epochs) * 100:.2f}%</h3>", unsafe_allow_html=True)
        progress_bar.progress((epoch + 1) / epochs)
        if parar:
            break

    regressor = PySRRegressor(
        niterations=1000,
        binary_operators=["+", "-", "*", "/"],
        unary_operators=["sin", "cos", "exp", "log"],
    )

    regressor.fit(X_train, y_train.ravel())

    equations = regressor.get_best()

    plt.text(np.min(X_train), np.max(y_train), str(equations), fontsize=12,
             color='red', bbox=dict(facecolor='white', alpha=0.5))

    plt.ioff()
    plt.show()

    print("Melhor equação encontrada pela PySR:")
    print(equations)

#coordenadas_exemplo = [{"x": x, "y": x ** 3} for x in np.linspace(-10, 10, 100)]
#fit(coordenadas_exemplo, 2500)
