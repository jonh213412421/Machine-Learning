import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt
from pysr import PySRRegressor

# Função que gera dados
def generate_data(num_samples=1000):
    X = np.linspace(-10, 10, num_samples).reshape(-1, 1)
    y = X**3
    return X, y

# Gera dados ### ponto crítico. Quais dados usar??
X_train, y_train = generate_data()

# Definir modelo
model = Sequential([
    Dense(15, input_dim=1, activation='relu'),   # Hidden layer 1
    Dense(15, activation='relu'),                # Hidden layer 2
    Dense(1)                                     # Output layer
])

# Compilar modelo
model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

# perda
fig, (ax, ax1) = plt.subplots(1,2)
losses = []

def plot_loss(logs, X_train, y_train):
    y_pred = model.predict(X_train, verbose=1)
    ax1.clear()
    ax1.plot(X_train, y_train, color='blue', label='Verdadeira função (y = x^3)')
    ax1.plot(X_train, y_pred, color='red', linestyle='--', label='função prevista')
    ax1.set_xlabel('x')
    ax1.set_ylabel('y')
    ax1.set_title('Valores verdadeiros X Valores previstos')
    ax1.legend()
    losses.append(logs['loss'])
    ax.clear()
    ax.plot(losses, label='Training Loss')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.set_title('Loss por Epoch')
    ax.legend()
    plt.draw()
    plt.pause(0.1)  # Pause to allow the plot to update

# plot em tempo real
class PlotLossCallback(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs=None):
        plot_loss(logs, X_train, y_train)

# Treina o modelo
history = model.fit(
    X_train, y_train,
    epochs=1000,
    batch_size=32,
    verbose=1, 
    callbacks=[PlotLossCallback()]
)

regressor = PySRRegressor(
    niterations=1000,  # Number of iterations for the search
    binary_operators=["+", "-", "*", "/"],  # Operators to use
    unary_operators=["sin", "cos", "exp", "log"],  # Unary functions to use
    # Add more parameters if needed
)

predictions = model.predict(X_train)

# Prepare data for PySR
data = np.hstack((X_train, predictions))
targets = y_train

# Faz a regressão
regressor.fit(X_train, y_train)

# pega a melhor equação
equations = regressor.get_best()

plt.text(-6, 500, str(equations), fontsize=12, color='red', bbox=dict(facecolor='white', alpha=0.5))
print(equations)

# Finalize the plot
plt.ioff()  # desliga modo iterativo
plt.show()  # mostra o gráfico final

# gera dados de teste
X_test, y_test = generate_data(num_samples=100)

print(f'Prediction for x = {X_test[0]}: {model.predict(X_test)[0][0]:.4f}')
