import numpy as np
import streamlit
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt
from pysr import PySRRegressor

def teste(coordenadas, epochs):

    X_train = np.array([p["x"] for p in coordenadas], dtype=np.float32).reshape(-1, 1)
    y_train = np.array([p["y"] for p in coordenadas], dtype=np.float32).reshape(-1, 1)

    model = Sequential([
        Dense(25, input_dim=1, activation='relu'),
        Dense(25, activation='relu'),
        Dense(1)
    ])

    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

    fig, (ax1) = plt.subplots(1, 1)

    def plot_loss(X, y):
        y_pred = model.predict(X, verbose=0)
        ax1.clear()
        ax1.scatter(X, y, color='blue', label='Valores verdadeiros')
        ax1.scatter(X, y_pred, color='red', marker='x', label='Valores previstos')
        ax1.set_xlabel('x')
        ax1.set_ylabel('y')
        ax1.set_title('Valores verdadeiros vs. previstos')
        ax1.legend()
        

    class PlotLossCallback(tf.keras.callbacks.Callback):
        def on_epoch_end(self, epoch, logs=None):
            plot_loss(X_train, y_train)

    model.fit(
        X_train, y_train,
        epochs=epochs,
        batch_size=32,
        verbose=1,
        callbacks=[PlotLossCallback()]
    )

    predictions = model.predict(X_train)

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

    # Exemplo de uso:


coordenadas_exemplo = [{"x": x, "y": x ** 3} for x in np.linspace(-10, 10, 100)]
teste(coordenadas_exemplo, 2500)
