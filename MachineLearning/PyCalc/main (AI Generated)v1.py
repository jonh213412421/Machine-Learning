import streamlit as st
import tensorflow as tf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time


# --- Configuração da Página ---
st.set_page_config(
   page_title="Regressão com Redes Neurais",
   page_icon="🤖",
   layout="wide",
   initial_sidebar_state="expanded"
)


# --- Estilos CSS para botões e interface ---
st.markdown("""
<style>
   /* Estilo para o container principal */
   .main {
       background-color: #f5f5ff;
   }
   /* Estilo para botões primários (verde) */
   .stButton>button {
       color: white;
       background-color: #28a745; /* Verde */
       border: none;
       border-radius: 5px;
       padding: 10px 24px;
       font-size: 16px;
   }
   .stButton>button:hover {
       background-color: #218838;
       color: white;
   }
   /* Classe customizada para botão vermelho */
   div.stButton.red-button > button {
       background-color: #dc3545; /* Vermelho */
   }
   div.stButton.red-button > button:hover {
       background-color: #c82333;
   }
</style>
""", unsafe_allow_html=True)




# --- Funções do Modelo ---


def build_and_compile_model(activation, learning_rate):
   """Cria e compila o modelo de rede neural."""
   model = tf.keras.Sequential([
       # CORREÇÃO: A primeira camada DEVE ter o input_shape especificado.
       # units=1: queremos uma única saída (y)
       # input_shape=[1]: informa ao modelo para esperar uma única entrada (x)
       tf.keras.layers.Dense(units=1, input_shape=[1], activation=activation)
   ])


   optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate)
   model.compile(optimizer=optimizer, loss='mean_squared_error')
   return model




# --- Inicialização do Estado da Sessão ---
# O st.session_state é usado para manter as variáveis entre as interações do usuário.
if 'training_in_progress' not in st.session_state:
   st.session_state.training_in_progress = False
if 'model_weights' not in st.session_state:
   st.session_state.model_weights = None
if 'final_params' not in st.session_state:
   st.session_state.final_params = None
if 'data' not in st.session_state:
   st.session_state.data = pd.DataFrame(columns=['x', 'y'])
if 'manual_rows' not in st.session_state:
   st.session_state.manual_rows = 3  # Começa com 3 linhas para inserção manual


# --- Barra Lateral (Sidebar) de Configurações ---
with st.sidebar:
   st.header("⚙️ Personalização do Modelo")


   activation_function = st.selectbox(
       "Função de Ativação",
       ['linear', 'relu', 'sigmoid', 'tanh'],
       help="A função 'linear' é a mais indicada para problemas de regressão simples."
   )


   learning_rate = st.select_slider(
       "Taxa de Aprendizado (Learning Rate)",
       options=[0.0001, 0.001, 0.01, 0.1, 1.0],
       value=0.01,
       help="Define o quão rápido o modelo aprende. Valores menores são mais lentos, mas podem ser mais precisos."
   )


   epochs = st.number_input(
       "Número de Épocas (Epochs)",
       min_value=10,
       max_value=10000,
       value=100,
       step=10,
       help="O número de vezes que o modelo verá todos os dados de treinamento."
   )


# --- Tela Principal ---
st.title("🤖 Regressor com Rede Neural Interativa")
st.write("Insira seus dados, personalize o modelo e treine uma rede neural para encontrar a equação de regressão.")


# --- Seção de Entrada de Dados ---
data_container = st.container(border=True)
with data_container:
   st.subheader("1. Forneça os Dados")


   tab1, tab2 = st.tabs([" Entrada Manual ", " Upload de CSV "])


   with tab1:
       st.write("Adicione seus pontos `[x, y]` manualmente.")


       # Cria colunas para os inputs manuais
       col_x, col_y = st.columns(2)
       col_x.markdown("##### Valor de X")
       col_y.markdown("##### Valor de Y")


       manual_data = {'x': [], 'y': []}
       for i in range(st.session_state.manual_rows):
           with col_x:
               x_val = st.number_input(f"x_{i + 1}", key=f"x_{i}", label_visibility="collapsed")
           with col_y:
               y_val = st.number_input(f"y_{i + 1}", key=f"y_{i}", label_visibility="collapsed")
           manual_data['x'].append(x_val)
           manual_data['y'].append(y_val)


       # Botões para adicionar/remover linhas
       bcol1, bcol2 = st.columns(2)
       if bcol1.button("➕ Adicionar Ponto", use_container_width=True):
           st.session_state.manual_rows += 1
           st.rerun()


       if bcol2.button("➖ Remover Ponto", use_container_width=True, disabled=(st.session_state.manual_rows <= 1)):
           st.session_state.manual_rows -= 1
           st.rerun()


   with tab2:
       uploaded_file = st.file_uploader(
           "Carregue um arquivo CSV com as colunas 'x' e 'y'.",
           type=['csv']
       )
       if uploaded_file:
           try:
               df_csv = pd.read_csv(uploaded_file)
               if 'x' in df_csv.columns and 'y' in df_csv.columns:
                   st.session_state.data = df_csv[['x', 'y']]
                   st.success("Arquivo CSV carregado com sucesso!")
               else:
                   st.error("O arquivo CSV precisa conter as colunas 'x' e 'y'.")
           except Exception as e:
               st.error(f"Erro ao ler o arquivo: {e}")


   # Botão para usar os dados manuais
   if st.button("Usar Dados Manuais"):
       st.session_state.data = pd.DataFrame(manual_data)
       st.success("Dados manuais carregados!")


# Se dados foram carregados, exibe a tabela e o botão de iniciar
if not st.session_state.data.empty and not st.session_state.training_in_progress:
   st.subheader("Dados Carregados")
   st.dataframe(st.session_state.data, use_container_width=True)


   if st.button("🚀 Iniciar Treinamento", use_container_width=True, type="primary"):
       st.session_state.training_in_progress = True
       st.session_state.final_params = None
       st.rerun()  # Reinicia o script para entrar no modo de treinamento


# --- Lógica de Treinamento e Visualização ---
if st.session_state.training_in_progress:
   st.subheader("2. Acompanhe o Treinamento")


   # Prepara os dados
   X = st.session_state.data['x'].values.astype(np.float32)
   y = st.session_state.data['y'].values.astype(np.float32)


   # Cria o modelo
   model = build_and_compile_model(activation_function, learning_rate)


   # Placeholders para o gráfico e as estatísticas
   plot_placeholder = st.empty()
   stats_placeholder = st.empty()


   # Botão de Parar
   st.markdown('<div class="stButton red-button">', unsafe_allow_html=True)
   if st.button("🛑 Parar Treinamento", use_container_width=True):
       st.session_state.training_in_progress = False
       st.warning("Treinamento interrompido pelo usuário.")
       time.sleep(2)  # Pausa para o usuário ver a mensagem
       st.rerun()
   st.markdown('</div>', unsafe_allow_html=True)


   # Loop de treinamento (época por época para atualização em tempo real)
   try:
       fig, ax = plt.subplots()


       for epoch in range(epochs):
           if not st.session_state.training_in_progress:
               break


           # Treina por uma época
           history = model.fit(X, y, epochs=1, verbose=0)
           loss = history.history['loss'][0]


           # Faz predições com o estado atual do modelo
           y_pred = model.predict(X, verbose=0)


           # Atualiza o gráfico
           ax.clear()
           ax.scatter(X, y, color='blue', label='Dados Originais')
           ax.plot(X, y_pred, color='red', linewidth=2, label='Previsão do Modelo')
           ax.set_title("Progresso do Modelo")
           ax.set_xlabel("X")
           ax.set_ylabel("Y")
           ax.legend()
           ax.grid(True)
           plot_placeholder.pyplot(fig)


           # Atualiza as estatísticas
           stats_placeholder.text(f"Época: {epoch + 1}/{epochs} | Perda (Loss): {loss:.4f}")


           time.sleep(0.01)  # Pequena pausa para a interface renderizar


       plt.close(fig)  # Libera a memória da figura


       # Salva o modelo e os parâmetros finais se o treinamento não foi interrompido
       if st.session_state.training_in_progress:
           # ALTERAÇÃO: Salva apenas os pesos, que são mais seguros para o session_state
           st.session_state.model_weights = model.get_weights()
           weights, bias = model.layers[0].get_weights()
           st.session_state.final_params = {'w': weights[0][0], 'b': bias[0]}
           st.success("Treinamento concluído com sucesso!")


   except Exception as e:
       st.error(f"Ocorreu um erro durante o treinamento: {e}")


   finally:
       # Finaliza o estado de treinamento
       st.session_state.training_in_progress = False
       time.sleep(1)
       st.rerun()


# --- Seção de Resultados e Predição ---
if st.session_state.final_params:
   st.subheader("3. Resultados")


   params = st.session_state.final_params
   w = params['w']
   b = params['b']


   st.markdown("A rede neural encontrou a seguinte equação:")
   st.latex(f"y = {w:.4f}x + {b:.4f}")


   st.info(
       f"Isso significa que, para cada unidade que `x` aumenta, `y` tende a mudar em `{w:.4f}`, começando de um valor base de `{b:.4f}` quando `x` é zero.")


   st.subheader("4. Faça uma Nova Predição")


   pred_container = st.container(border=True)
   with pred_container:
       new_x = st.number_input("Digite um novo valor para X e veja a predição do modelo:", value=None,
                               placeholder="Digite um número...")


       if new_x is not None:
           # ALTERAÇÃO: Reconstrói o modelo e carrega os pesos salvos
           # Isso garante que o modelo esteja sempre em um estado "construído" válido
           model = build_and_compile_model(activation_function, learning_rate)
           model.set_weights(st.session_state.model_weights)


           # PREPARAÇÃO CORRETA DA ENTRADA
           input_data = np.array([float(new_x)]).reshape(1, -1)


           # A predição agora funciona com o formato correto
           prediction = model.predict(input_data, verbose=0)


           # Extrai o valor previsto e o exibe na tela
           predicted_y = prediction[0][0]
           st.markdown(f"### Para **X = `{new_x}`**, o valor previsto de **Y** é **`{predicted_y:.4f}`**")


# Botão para limpar tudo e recomeçar
if not st.session_state.data.empty or st.session_state.final_params:
   if st.button("Limpar Dados e Recomeçar"):
       for key in st.session_state.keys():
           del st.session_state[key]
       st.rerun()



