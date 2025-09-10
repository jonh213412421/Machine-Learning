# -*- coding: utf-8 -*-
"""
Este código implementa uma Rede Adversarial Geradora Convolucional Profunda (DCGAN)
para gerar rostos de celebridades, com base no dataset CelebA.
Todos os arquivos do dataset serão baixados e processados no diretório
especificado: /content/sample_data/
"""


# ==============================================================================
# 1. IMPORTAÇÃO DAS BIBLIOTECAS E CONFIGURAÇÃO INICIAL
# ==============================================================================
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import time
import os
import zipfile
from IPython import display


print("TensorFlow versão:", tf.__version__)


# Configurações do modelo e treinamento
BUFFER_SIZE = 60000
BATCH_SIZE = 256
IMG_WIDTH = 64
IMG_HEIGHT = 64
LATENT_DIM = 100 # Dimensão do espaço latente (vetor de ruído)
EPOCHS = 5 # Conforme solicitado


# --- MODIFICAÇÃO: DEFININDO O CAMINHO DE TRABALHO ---
# Define o diretório de destino para o dataset
TARGET_PATH = "/content/sample_data"
# Garante que o diretório de destino exista
os.makedirs(TARGET_PATH, exist_ok=True)
print(f"Diretório de trabalho definido como: {TARGET_PATH}")
# ---------------------------------------------------


# ==============================================================================
# 2. DOWNLOAD E PREPARAÇÃO DO DATASET CELEBA NO CAMINHO ESPECÍFICO
# ==============================================================================
print("\nIniciando download e preparação do dataset CelebA...")


# URL do dataset (versão alinhada e cortada)
DATASET_URL = 'https://s3-us-west-1.amazonaws.com/udacity-dlnfd/datasets/celeba.zip'


# Baixa o arquivo .zip para o diretório de cache padrão do Keras
path_to_zip_default = tf.keras.utils.get_file('celeba.zip', origin=DATASET_URL, extract=False)


# Define o caminho final para as imagens extraídas
PATH_TO_IMAGES = os.path.join(TARGET_PATH, 'img_align_celeba')


# Extrai o arquivo .zip para o diretório de destino se ainda não foi extraído
if not os.path.exists(PATH_TO_IMAGES):
    print(f"Extraindo arquivos para {TARGET_PATH}...")
    with zipfile.ZipFile(path_to_zip_default, 'r') as zip_ref:
        zip_ref.extractall(TARGET_PATH)
    print("Dataset extraído com sucesso.")
else:
    print("Diretório de imagens já existe em /content/sample_data/.")


# Carregando e pré-processando as imagens
def preprocess_image(image_path):
    """Carrega e normaliza uma imagem."""
    image = tf.io.read_file(image_path)
    image = tf.image.decode_jpeg(image, channels=3)
    # Corta o centro da imagem para focar no rosto
    image = tf.image.resize_with_crop_or_pad(image, 108, 108)
    # Redimensiona para o tamanho de entrada da rede
    image = tf.image.resize(image, [IMG_HEIGHT, IMG_WIDTH])
    # Normaliza os pixels para o intervalo [-1, 1], ideal para a função de ativação tanh
    image = (tf.cast(image, tf.float32) - 127.5) / 127.5
    return image


# Cria o dataset TensorFlow a partir do caminho especificado
image_paths = [os.path.join(PATH_TO_IMAGES, f) for f in os.listdir(PATH_TO_IMAGES)]
train_dataset = tf.data.Dataset.from_tensor_slices(image_paths).map(preprocess_image).shuffle(BUFFER_SIZE).batch(BATCH_SIZE)


print(f"{len(image_paths)} imagens carregadas de '{PATH_TO_IMAGES}' e prontas para o treinamento.")


# ==============================================================================
# 3. CRIAÇÃO DOS MODELOS (GERADOR E DISCRIMINADOR)
# ==============================================================================


# -----------------
# Modelo Gerador
# -----------------
def make_generator_model():
    model = tf.keras.Sequential()
    model.add(tf.keras.layers.Dense(4*4*1024, use_bias=False, input_shape=(LATENT_DIM,)))
    model.add(tf.keras.layers.BatchNormalization())
    model.add(tf.keras.layers.LeakyReLU())
    model.add(tf.keras.layers.Reshape((4, 4, 1024)))
    model.add(tf.keras.layers.Conv2DTranspose(512, (5, 5), strides=(2, 2), padding='same', use_bias=False))
    model.add(tf.keras.layers.BatchNormalization())
    model.add(tf.keras.layers.LeakyReLU())
    model.add(tf.keras.layers.Conv2DTranspose(256, (5, 5), strides=(2, 2), padding='same', use_bias=False))
    model.add(tf.keras.layers.BatchNormalization())
    model.add(tf.keras.layers.LeakyReLU())
    model.add(tf.keras.layers.Conv2DTranspose(128, (5, 5), strides=(2, 2), padding='same', use_bias=False))
    model.add(tf.keras.layers.BatchNormalization())
    model.add(tf.keras.layers.LeakyReLU())
    model.add(tf.keras.layers.Conv2DTranspose(3, (5, 5), strides=(2, 2), padding='same', use_bias=False, activation='tanh'))
    return model


# -----------------
# Modelo Discriminador
# -----------------
def make_discriminator_model():
    model = tf.keras.Sequential()
    model.add(tf.keras.layers.Conv2D(64, (5, 5), strides=(2, 2), padding='same', input_shape=[IMG_HEIGHT, IMG_WIDTH, 3]))
    model.add(tf.keras.layers.LeakyReLU())
    model.add(tf.keras.layers.Dropout(0.3))
    model.add(tf.keras.layers.Conv2D(128, (5, 5), strides=(2, 2), padding='same'))
    model.add(tf.keras.layers.LeakyReLU())
    model.add(tf.keras.layers.Dropout(0.3))
    model.add(tf.keras.layers.Conv2D(256, (5, 5), strides=(2, 2), padding='same'))
    model.add(tf.keras.layers.LeakyReLU())
    model.add(tf.keras.layers.Dropout(0.3))
    model.add(tf.keras.layers.Flatten())
    model.add(tf.keras.layers.Dense(1))
    return model


generator = make_generator_model()
discriminator = make_discriminator_model()
print("\nModelos Gerador e Discriminador criados.")


# ==============================================================================
# 4. DEFINIÇÃO DAS FUNÇÕES DE PERDA E OTIMIZADORES
# ==============================================================================
cross_entropy = tf.keras.losses.BinaryCrossentropy(from_logits=True)


def discriminator_loss(real_output, fake_output):
    real_loss = cross_entropy(tf.ones_like(real_output), real_output)
    fake_loss = cross_entropy(tf.zeros_like(fake_output), fake_output)
    return real_loss + fake_loss


def generator_loss(fake_output):
    return cross_entropy(tf.ones_like(fake_output), fake_output)


generator_optimizer = tf.keras.optimizers.Adam(1e-4)
discriminator_optimizer = tf.keras.optimizers.Adam(1e-4)


# Vetor de ruído fixo para visualização do progresso
seed = tf.random.normal([16, LATENT_DIM])


# ==============================================================================
# 5. LÓGICA DE TREINAMENTO
# ==============================================================================
@tf.function
def train_step(images):
    noise = tf.random.normal([BATCH_SIZE, LATENT_DIM])
    with tf.GradientTape() as gen_tape, tf.GradientTape() as disc_tape:
        generated_images = generator(noise, training=True)
        real_output = discriminator(images, training=True)
        fake_output = discriminator(generated_images, training=True)
        gen_loss = generator_loss(fake_output)
        disc_loss = discriminator_loss(real_output, fake_output)
    gradients_of_generator = gen_tape.gradient(gen_loss, generator.trainable_variables)
    gradients_of_discriminator = disc_tape.gradient(disc_loss, discriminator.trainable_variables)
    generator_optimizer.apply_gradients(zip(gradients_of_generator, generator.trainable_variables))
    discriminator_optimizer.apply_gradients(zip(gradients_of_discriminator, discriminator.trainable_variables))


def generate_and_show_progress(model, epoch, test_input):
    predictions = model(test_input, training=False)
    fig = plt.figure(figsize=(4, 4))
    for i in range(predictions.shape[0]):
        plt.subplot(4, 4, i+1)
        plt.imshow((predictions[i, :, :, :] + 1) / 2)
        plt.axis('off')
    plt.show()


def train(dataset, epochs):
    print("\nIniciando o treinamento...")
    for epoch in range(epochs):
        start_time = time.time()
        for image_batch in dataset:
            train_step(image_batch)
        display.clear_output(wait=True)
        generate_and_show_progress(generator, epoch + 1, seed)
        print (f'Tempo para a época {epoch + 1} foi de {time.time()-start_time:.2f} segundos')
    display.clear_output(wait=True)
    print(f"\nTreinamento concluído após {epochs} épocas.")


# Inicia o treinamento
train(train_dataset, EPOCHS)


# ==============================================================================
# 6. GERAÇÃO DA IMAGEM FINAL DE TESTE
# ==============================================================================
print("\nGerando um rosto de teste final...")
test_noise = tf.random.normal([1, LATENT_DIM])
generated_image = generator(test_noise, training=False)


plt.imshow((generated_image[0, :, :, :] + 1) / 2)
plt.title("Rosto Gerado Após 5 Épocas")
plt.axis('off')
plt.show()

