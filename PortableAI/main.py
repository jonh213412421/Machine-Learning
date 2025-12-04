import sys
import os
import re
import markdown

# Configuração gráfica
os.environ['QT_OPENGL'] = 'angle'

import json
import funcs
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QEvent
from PyQt6.QtGui import QIcon, QFont, QShortcut, QKeySequence, QColor
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QTextEdit, \
    QFrame, QSlider, QGraphicsDropShadowEffect
from PyQt6.QtWebEngineWidgets import QWebEngineView
import janelas
import estilos
from threads import PromptThread, CarregarArquivoThread


class ChatHandler:
    def __init__(self):
        self.bot_container_id = None
        self.div_bot_criada = False
        self.j = 0
        self.chat_tela = None
        self.chat_botao = None
        self.orig_dir = ""

    def habilitar_botao_prompt(self, botao_prompt: bool):
        if self.chat_botao and botao_prompt:
            self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
            self.chat_botao.setEnabled(True)

    def formatar_texto(self, texto: str) -> str:
        # Limpeza de artefatos
        texto = re.sub(r'^(#+)([^ \n])', r'\1 \2', texto, flags=re.MULTILINE)
        texto = re.sub(r'-{2,}#{2,}', '\n\n', texto)
        try:
            html = markdown.markdown(texto, extensions=['tables', 'fenced_code', 'nl2br'])
            return html
        except Exception as e:
            print(f"Erro markdown: {e}")
            return texto

    def mostrar_digitando(self):
        if not self.chat_tela: return

        # Cria ou recria os pontinhos no final do chat
        js = """
        (function() {
            var chat = document.getElementById('chat');
            var old = document.getElementById('typing_indicator');
            if (old) old.remove();

            var wrapper = document.createElement('div');
            wrapper.id = 'typing_indicator';
            wrapper.className = 'msg-wrapper bot-wrapper';

            var msg = document.createElement('div');
            msg.className = 'msg bot';
            msg.innerHTML = '<div class="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';

            wrapper.appendChild(msg);
            chat.appendChild(wrapper);
            window.scrollTo(0, document.body.scrollHeight);
        })();
        """
        self.chat_tela.page().runJavaScript(js)

    def esconder_digitando(self):
        if not self.chat_tela: return
        js = "var el = document.getElementById('typing_indicator'); if(el) el.remove();"
        self.chat_tela.page().runJavaScript(js)

    # --- NOVO MÉTODO: Adiciona avisos do sistema (ex: cancelamento) em div separada ---
    def adicionar_aviso(self, html_aviso: str):
        if not self.chat_tela: return

        js_content = json.dumps(html_aviso)
        js = f"""
        (function() {{
            var chat = document.getElementById('chat');
            var div = document.createElement('div');
            div.style.width = '100%';
            div.style.marginBottom = '10px';
            div.innerHTML = {js_content};

            // Remove typing se existir antes de adicionar o aviso
            var typing = document.getElementById('typing_indicator');
            if(typing) typing.remove();

            chat.appendChild(div);
            window.scrollTo(0, document.body.scrollHeight);
        }})();
        """
        self.chat_tela.page().runJavaScript(js)

    def adicionar_html(self, texto: str, remetente: str, raw_html: bool = False, streaming: bool = False) -> None:
        if not self.chat_tela: return

        # 1. Preparação do conteúdo
        if raw_html:
            texto_final = texto
        else:
            if remetente == 'user' or streaming:
                texto_final = (texto.replace("&", "&amp;")
                               .replace("<", "&lt;")
                               .replace(">", "&gt;"))
                texto_final = texto_final.replace("\n", "<br>")
            else:
                texto_final = self.formatar_texto(texto)

        js_content = json.dumps(texto_final)

        # 2. Scripts auxiliares
        js_scroll = "window.scrollTo(0, document.body.scrollHeight);"

        js_mathjax = ""
        if not streaming and remetente == 'bot':
            js_mathjax = "if(window.MathJax && typeof msg_div !== 'undefined') { MathJax.typesetPromise([msg_div]).then(() => " + js_scroll + "); }"

        # 3. Lógica de Inserção
        if remetente == 'user':
            wrapper_id = f"msg_{self.j}"
            wrapper_class = "user-wrapper"
            msg_class = "user"
            self.div_bot_criada = False
            self.j += 1

            # Insere ANTES dos pontinhos (se existirem), ou no final (se null)
            js = f"""
            (function() {{
                var chat = document.getElementById('chat');
                var wrapper = document.createElement('div');
                wrapper.id = '{wrapper_id}';
                wrapper.className = '{wrapper_class} msg-wrapper';
                var msg = document.createElement('div');
                msg.className = '{msg_class} msg';
                msg.innerHTML = {js_content}; 
                wrapper.appendChild(msg);

                var typing = document.getElementById('typing_indicator');
                if (typing) {{
                    chat.insertBefore(wrapper, typing);
                }} else {{
                    chat.appendChild(wrapper);
                }}

                {js_scroll}
            }})();
            """

        else:  # BOT
            if not self.div_bot_criada:
                # Criar nova bolha
                wrapper_id = f"msg_{self.j}"
                self.div_bot_criada = True
                self.j += 1

                js = f"""
                (function() {{
                    var chat = document.getElementById('chat');
                    var wrapper = document.createElement('div');
                    wrapper.id = '{wrapper_id}';
                    wrapper.className = 'bot-wrapper msg-wrapper';
                    var msg = document.createElement('div');
                    msg.className = 'bot msg';
                    var msg_div = msg;
                    msg.innerHTML = {js_content};
                    wrapper.appendChild(msg);

                    // Adiciona msg ao chat (antes dos pontinhos se houver)
                    var typing = document.getElementById('typing_indicator');
                    if (typing) {{
                        chat.insertBefore(wrapper, typing);
                    }} else {{
                        chat.appendChild(wrapper);
                    }}

                    {js_mathjax}
                    if (!window.MathJax) {{ {js_scroll} }}
                }})();
                """
            else:
                # Atualizar bolha existente
                prev_id = f"msg_{self.j - 1}"

                js = f"""
                (function() {{
                    var wrapper = document.getElementById('{prev_id}');
                    if (wrapper) {{
                        var msg_div = wrapper.querySelector('.bot');
                        msg_div.innerHTML = {js_content};

                        // Garante que os pontinhos continuam no final
                        var chat = document.getElementById('chat');
                        var typing = document.getElementById('typing_indicator');
                        if (typing && chat.lastElementChild !== typing) {{
                            chat.appendChild(typing);
                        }}

                        {js_mathjax}
                        if (!window.MathJax) {{ {js_scroll} }}
                    }}
                }})();
                """

        self.chat_tela.page().runJavaScript(js)

    def limpar_chat(self):
        self.j = 0
        self.div_bot_criada = False
        if self.chat_tela:
            self.chat_tela.page().runJavaScript("document.getElementById('chat').innerHTML = '';")


class MinhaJanela(QWidget):
    def __init__(self):
        super().__init__()
        self.orig_dir = os.getcwd()
        self.thread = None
        self.sidebar_estendida = True
        self.gerando_resposta = False

        self.historico_atual = []
        self.nome_arquivo_atual = None
        self.buffer_resposta_bot = ""
        self.primeiro_chunk_recebido = False

        self.setWindowTitle("PyChatBot")
        self.setFixedSize(1024, 800)
        self.setup_ui()

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress and source is self.chat_prompt:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return super().eventFilter(source, event)
                self.chat_botao.click()
                return True
        return super().eventFilter(source, event)

    def desabilitar_controles(self) -> None:
        self.botao_arquivo.setDisabled(True)
        self.botao_modelo.setDisabled(True)
        self.slider_temp.setDisabled(True)

    def habilitar_controles(self) -> None:
        self.botao_arquivo.setDisabled(False)
        self.botao_modelo.setDisabled(False)
        if self.thread is None or not self.thread.isRunning():
            self.slider_temp.setDisabled(False)

    def receber_parte_resposta(self, texto: str, remetente: str):
        if remetente == 'bot':
            self.buffer_resposta_bot += texto
            # Atualiza a div existente do bot
            self.chat_handler.adicionar_html(self.buffer_resposta_bot, remetente, streaming=True)
        else:
            pass

    def on_resposta_finalizada(self) -> None:
        self.gerando_resposta = False
        # Esconde pontinhos só no final
        self.chat_handler.esconder_digitando()

        self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
        self.habilitar_controles()

        if self.buffer_resposta_bot:
            # Render final (Markdown + MathJax)
            self.chat_handler.adicionar_html(self.buffer_resposta_bot, 'bot', streaming=False)
            self.historico_atual.append({"role": "bot", "content": self.buffer_resposta_bot})
            self.buffer_resposta_bot = ""
            self.salvar_conversa()

    def on_thread_finished(self) -> None:
        if self.gerando_resposta:
            self.gerando_resposta = False
            self.chat_handler.esconder_digitando()
            self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
            self.habilitar_controles()
            if self.buffer_resposta_bot:
                self.historico_atual.append({"role": "bot", "content": self.buffer_resposta_bot})
                self.salvar_conversa()

    def salvar_conversa(self):
        novo_nome = funcs.salvar_conversa_json(self.historico_atual, self.nome_arquivo_atual)
        if novo_nome:
            self.nome_arquivo_atual = novo_nome
            self.atualizar_lista_conversas()

    def nova_conversa(self):
        self.historico_atual = []
        self.nome_arquivo_atual = None
        self.buffer_resposta_bot = ""
        self.chat_handler.limpar_chat()
        self.chat_handler.esconder_digitando()

        if self.thread and self.thread.isRunning():
            self.thread.stop_thread()
            self.thread.wait()
            self.thread.deleteLater()
            self.thread = None

        self.gerando_resposta = False
        self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
        self.habilitar_controles()

    def recuperar_conversa(self, nome_arquivo: str) -> None:
        dados = funcs.ler_conversa_json(nome_arquivo)
        if not dados: return
        self.nova_conversa()
        self.historico_atual = dados
        self.nome_arquivo_atual = nome_arquivo
        for msg in self.historico_atual:
            self.chat_handler.adicionar_html(msg['content'], msg['role'], streaming=False)

    def excluir_conversa(self, nome_arquivo: str) -> None:
        if funcs.excluir_conversa(nome_arquivo):
            if self.nome_arquivo_atual == nome_arquivo:
                self.nova_conversa()
            self.atualizar_lista_conversas()

    def atualizar_lista_conversas(self):
        if hasattr(self, 'layout_lista_conversas'):
            while self.layout_lista_conversas.count():
                item = self.layout_lista_conversas.takeAt(0)
                if item.widget(): item.widget().deleteLater()

            btn_nova = QPushButton("Nova Conversa +")
            btn_nova.setStyleSheet(estilos.estilo_botao_conversa().replace("rgb(180, 180, 180)", "rgb(173, 216, 230)"))
            btn_nova.clicked.connect(self.nova_conversa)
            self.layout_lista_conversas.addWidget(btn_nova)
            self.layout_lista_conversas.addSpacing(5)

            for conversa in funcs.listar_conversas():
                caminho = os.path.join(os.getcwd(), "data", "conversas", conversa)
                texto_botao = conversa.replace(".json", "").replace("_", " ")[:18]
                try:
                    with open(caminho, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                        if dados and len(dados) > 0:
                            texto_botao = dados[0]['content'][:18] + "..."
                except:
                    pass

                container = QWidget()
                layout_h = QHBoxLayout(container)
                layout_h.setContentsMargins(0, 0, 0, 0)
                layout_h.setSpacing(2)

                botao = QPushButton(texto_botao)
                botao.clicked.connect(lambda checked, c=conversa: self.recuperar_conversa(c))
                botao.setStyleSheet(estilos.estilo_botao_conversa())

                btn_del = QPushButton("X")
                btn_del.setFixedSize(20, 30)
                btn_del.setStyleSheet(
                    "QPushButton { background-color: #ff6b6b; color: white; border: none; border-radius: 3px; font-weight: bold; } QPushButton:hover { background-color: #ff4c4c; }")
                btn_del.clicked.connect(lambda checked, c=conversa: self.excluir_conversa(c))

                layout_h.addWidget(botao)
                layout_h.addWidget(btn_del)
                self.layout_lista_conversas.addWidget(container)
            self.layout_lista_conversas.addStretch()

    def setup_ui(self):
        self.chat_handler = ChatHandler()
        self.chat_handler.orig_dir = self.orig_dir

        def click_botao_prompt() -> None:
            # LÓGICA DE CANCELAMENTO
            if self.gerando_resposta:
                if self.thread and self.thread.isRunning():
                    try:
                        self.thread.linha.disconnect()
                        self.thread.sinal_resposta_finalizada.disconnect()
                        self.thread.finished.disconnect()
                    except:
                        pass
                    self.thread.stop_thread()
                    self.thread.wait()
                    self.thread.deleteLater()
                    self.thread = None

                self.gerando_resposta = False
                self.chat_handler.esconder_digitando()
                self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))

                msg_cancel = estilos.mensagem_operacao_cancelada()

                # Renderiza o que já foi gerado (sem misturar com o aviso)
                if self.buffer_resposta_bot:
                    # Renderiza o bot como finalizado (Markdown)
                    self.chat_handler.adicionar_html(self.buffer_resposta_bot, 'bot', streaming=False)

                    self.historico_atual.append({"role": "bot", "content": self.buffer_resposta_bot + " [Cancelado]"})

                # Adiciona o aviso em uma div separada abaixo
                self.chat_handler.adicionar_aviso(msg_cancel)

                self.buffer_resposta_bot = ""
                self.habilitar_controles()
                return

            # LÓGICA DE ENVIO
            texto = self.chat_prompt.toPlainText().strip()
            if not texto: return

            self.gerando_resposta = True
            self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\trabalhando.svg"))
            self.chat_botao.repaint()
            self.desabilitar_controles()

            self.historico_atual.append({"role": "user", "content": texto})
            self.buffer_resposta_bot = ""

            self.chat_handler.adicionar_html(texto, 'user', streaming=False)
            self.chat_handler.mostrar_digitando()

            if self.thread is None or not self.thread.isRunning():
                modelo_selecionado = self.botao_modelo.currentText()
                if not modelo_selecionado:
                    self.chat_tela.setHtml("<h3>Erro: Nenhum modelo selecionado.</h3>")
                    self.gerando_resposta = False
                    self.chat_handler.esconder_digitando()
                    self.chat_botao.setIcon(QIcon(f"{self.orig_dir}\\ícones\\seta_enviar.svg"))
                    self.habilitar_controles()
                    return

                try:
                    temp_val = self.slider_temp.value() / 100.0
                except:
                    temp_val = 0.7

                self.thread = PromptThread(modelo_selecionado, temperature=temp_val, n_experts=0)
                self.thread.linha.connect(self.receber_parte_resposta)
                self.thread.erro.connect(lambda e: print(f"Erro Thread: {e}"))
                self.thread.sinal_resposta_finalizada.connect(self.on_resposta_finalizada)
                self.thread.finished.connect(self.on_thread_finished)
                self.thread.start()

            self.thread.enviar_prompt(texto)
            self.chat_prompt.clear()

        def esconder_mostrar_botao() -> None:
            if self.gerando_resposta:
                self.chat_botao.show()
                return
            text = self.chat_prompt.toPlainText().strip()
            if text:
                self.chat_botao.show()
            else:
                self.chat_botao.hide()

        def carregar_arquivo() -> None:
            try:
                nome_arquivo, dados_arquivo = funcs.carregar_arquivo()
                if nome_arquivo:
                    self.arquivo_carregado.setHtml(nome_arquivo)
                    self.arquivo_carregado.setAlignment(Qt.AlignmentFlag.AlignCenter)
            except Exception as e:
                print(f"Erro ao carregar arquivo: {e}")

        def minimizar_sidebar() -> None:
            width_atual = sidebar.width()
            if self.sidebar_estendida:
                destino = 0
                self.sidebar_estendida = False
                self.chat_prompt.setMinimumWidth(900)
                self.animacao = QPropertyAnimation(self.chat_prompt, b"maximumWidth")
                self.animacao.setDuration(300)
                self.animacao.setStartValue(width_atual)
                self.animacao.setEndValue(destino)
                self.animacao.setEasingCurve(QEasingCurve.Type.InOutBack)
                self.animacao.start()
                maximizador_menu.setIcon(QIcon(f"{self.orig_dir}\\ícones\\expansão_menu.svg"))
            else:
                destino = 200
                self.sidebar_estendida = True
                self.chat_prompt.setMinimumWidth(700)
                self.animacao = QPropertyAnimation(self.chat_prompt, b"maximumWidth")
                self.animacao.setDuration(300)
                self.animacao.setStartValue(width_atual)
                self.animacao.setEndValue(destino)
                self.animacao.setEasingCurve(QEasingCurve.Type.InOutCubic)
                self.animacao.start()
                maximizador_menu.setIcon(QIcon(f"{self.orig_dir}\\ícones\\minimização_menu.svg"))

            self.animacao_sidebar = QPropertyAnimation(sidebar, b"maximumWidth")
            self.animacao_sidebar.setDuration(300)
            self.animacao_sidebar.setStartValue(width_atual)
            self.animacao_sidebar.setEndValue(destino)
            self.animacao_sidebar.setEasingCurve(QEasingCurve.Type.InOutCubic)
            self.animacao_sidebar.start()

        self.chat_tela = QWebEngineView()
        self.chat_tela.setStyleSheet(estilos.estilo_chat_tela())
        self.chat_tela.setMinimumHeight(300)
        self.chat_tela.setMaximumHeight(700)
        self.chat_tela.setHtml(estilos.html_base())
        self.chat_handler.chat_tela = self.chat_tela

        self.prompt_barra = QHBoxLayout()
        self.chat_prompt = QTextEdit()
        self.chat_prompt.setMaximumHeight(40)
        self.chat_prompt.setMinimumWidth(900)
        self.chat_prompt.setFont(QFont("Arial", 12))
        self.chat_prompt.textChanged.connect(esconder_mostrar_botao)
        self.chat_prompt.installEventFilter(self)

        self.chat_prompt.setStyleSheet("""
           QTextEdit {
               color: black;
               background-color: white;
               border: 2px solid #aaa; /* Borda mais evidente */
               border-radius: 10px;
               padding: 8px;
               font-size: 14px;
           }
           QTextEdit:focus {
               border: 2px solid #5c9eff; /* Destaque ao focar */
           }
       """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        self.chat_prompt.setGraphicsEffect(shadow)

        self.chat_botao = QPushButton()
        self.chat_botao.setIcon(QIcon(f"{os.getcwd()}\\ícones\\seta_enviar.svg"))
        self.chat_botao.setMinimumWidth(50)
        self.chat_botao.setMinimumHeight(20)
        self.chat_botao.setMaximumHeight(40)
        self.chat_botao.setStyleSheet(estilos.estilo_chat_botao())
        self.chat_botao.clicked.connect(click_botao_prompt)
        self.chat_botao.setVisible(False)
        self.chat_handler.chat_botao = self.chat_botao

        self.prompt_barra.addWidget(self.chat_prompt, alignment=Qt.AlignmentFlag.AlignLeft, stretch=2)
        self.prompt_barra.addWidget(self.chat_botao, alignment=Qt.AlignmentFlag.AlignLeft, stretch=1)

        self.botao_modelo = QComboBox()
        try:
            modelos = funcs.listar_modelos()
            for modelo in modelos: self.botao_modelo.addItem(modelo)
        except:
            self.botao_modelo.addItem("Nenhum modelo encontrado")

        self.botao_modelo.addItem("Adicionar modelo")

        def ao_trocar_modelo(index):
            texto_atual = self.botao_modelo.currentText()
            if texto_atual == "Adicionar modelo":
                self.botao_modelo.blockSignals(True)
                novo_modelo = funcs.adicionar_modelo_gguf()
                self.botao_modelo.clear()
                modelos_atualizados = funcs.listar_modelos()
                for m in modelos_atualizados: self.botao_modelo.addItem(m)
                self.botao_modelo.addItem("Adicionar modelo")
                if novo_modelo:
                    self.botao_modelo.setCurrentText(novo_modelo)
                    self.nova_conversa()
                else:
                    if self.botao_modelo.count() > 1: self.botao_modelo.setCurrentIndex(0)
                self.botao_modelo.blockSignals(False)
            else:
                self.nova_conversa()

        self.botao_modelo.currentIndexChanged.connect(ao_trocar_modelo)
        self.botao_modelo.setMaximumWidth(600)
        self.botao_modelo.setMinimumWidth(250)
        self.botao_modelo.setMinimumHeight(20)
        self.botao_modelo.setMaximumHeight(40)
        self.botao_modelo.setStyleSheet(estilos.estilo_botao_modelos())

        self.botao_arquivo = QPushButton("Carregar Arquivo")
        self.botao_arquivo.setMaximumWidth(200)
        self.botao_arquivo.setMinimumWidth(100)
        self.botao_arquivo.setMinimumHeight(20)
        self.botao_arquivo.setMaximumHeight(40)
        self.botao_arquivo.setStyleSheet(estilos.estilo_botao_arquivo())
        self.botao_arquivo.clicked.connect(carregar_arquivo)

        self.arquivo_carregado = QTextEdit()
        self.arquivo_carregado.setReadOnly(True)
        self.arquivo_carregado.setHtml("Nenhum arquivo carregado")
        self.arquivo_carregado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.arquivo_carregado.setStyleSheet(estilos.estilo_arquivo_carregado())
        self.arquivo_carregado.setMaximumWidth(200)
        self.arquivo_carregado.setMinimumWidth(100)
        self.arquivo_carregado.setMinimumHeight(20)
        self.arquivo_carregado.setMaximumHeight(40)

        layout_inferior = QHBoxLayout()
        layout_inferior.addWidget(self.botao_modelo)
        layout_inferior.addWidget(self.botao_arquivo)
        layout_inferior.addWidget(self.arquivo_carregado)

        layout_principal_area = QVBoxLayout()
        layout_principal_area.addWidget(self.chat_tela)
        layout_principal_area.addLayout(self.prompt_barra)
        layout_principal_area.addLayout(layout_inferior)

        sidebar = QFrame()
        sidebar.resize(0, 5)
        sidebar.setMaximumWidth(200)
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar.setStyleSheet(estilos.estilo_sidebar())

        menu = QLabel("Menu")
        menu.setAlignment(Qt.AlignmentFlag.AlignCenter)
        menu.setStyleSheet(estilos.estilo_menu())

        layout_sidebar = QVBoxLayout(sidebar)
        layout_sidebar.addWidget(menu)
        layout_sidebar.addSpacing(15)

        lbl_temp = QLabel("Temperatura")
        lbl_temp.setStyleSheet(estilos.estilo_titulo_quantidade_tokens_arquivo())
        layout_sidebar.addWidget(lbl_temp)

        self.slider_temp = QSlider(Qt.Orientation.Horizontal)
        self.slider_temp.setMinimum(0)
        self.slider_temp.setMaximum(500)
        self.slider_temp.setValue(70)

        self.mostrador_temp = QTextEdit()
        self.mostrador_temp.setReadOnly(True)
        self.mostrador_temp.setMaximumHeight(22)
        self.mostrador_temp.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.mostrador_temp.setText("0.70")
        self.mostrador_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mostrador_temp.setStyleSheet(estilos.estilo_mostrar_quantidade_tokens_arquivo())

        def atualizar_temp(valor):
            temp_float = valor / 100.0
            self.mostrador_temp.setText(f"{temp_float:.2f}")
            self.mostrador_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.slider_temp.valueChanged.connect(atualizar_temp)
        layout_sidebar.addWidget(self.slider_temp)
        layout_sidebar.addWidget(self.mostrador_temp)
        layout_sidebar.addSpacing(15)

        quantidade_tokens_arquivo = QVBoxLayout()
        titulo_tokens = QLabel("Limite de Tokens")
        titulo_tokens.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_tokens.setStyleSheet(estilos.estilo_titulo_quantidade_tokens_arquivo())
        titulo_tokens.setMaximumHeight(20)

        slider_tokens = QSlider(Qt.Orientation.Horizontal)
        slider_tokens.setMinimum(2000)
        slider_tokens.setMaximum(64000)
        slider_tokens.setValue(10000)

        mostrador_tokens = QTextEdit()
        mostrador_tokens.setReadOnly(True)
        mostrador_tokens.setMaximumHeight(22)
        mostrador_tokens.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        mostrador_tokens.setText(str(slider_tokens.value()))
        mostrador_tokens.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mostrador_tokens.setStyleSheet(estilos.estilo_mostrar_quantidade_tokens_arquivo())

        slider_tokens.valueChanged.connect(lambda v: mostrador_tokens.setText(str(v)))

        quantidade_tokens_arquivo.addWidget(titulo_tokens)
        quantidade_tokens_arquivo.addWidget(slider_tokens)
        quantidade_tokens_arquivo.addWidget(mostrador_tokens)
        layout_sidebar.addLayout(quantidade_tokens_arquivo)
        layout_sidebar.addSpacing(15)

        sobre = QPushButton("Sobre")
        sobre.setStyleSheet(estilos.estilo_botao_sobre())

        def sobre_pop(tamanho):
            texto_sobre = """
           <p align="justify">
           <b>PyChatBot Portable</b><br><br>
           Este programa foi criado por <b>João Alberto</b> em 2025.<br><br>
           Ele nasceu do meu profundo amor e fascínio por Large Language Models (LLMs). 
           O objetivo deste projeto é tornar essa tecnologia incrível acessível, privada e portátil para todos, 
           permitindo explorar o potencial da IA diretamente do seu computador.
           </p>
           """
            janela = janelas.janela_mensagem(texto_sobre, tamanho)
            janela.exec()

        sobre.clicked.connect(lambda: sobre_pop((480, 300)))
        layout_sidebar.addWidget(sobre)
        layout_sidebar.addWidget(QPushButton("Opção 3"))
        layout_sidebar.addSpacing(15)

        titulo_conversas = QLabel("Histórico")
        titulo_conversas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_conversas.setStyleSheet(estilos.estilo_titulo_conversas())
        layout_sidebar.addWidget(titulo_conversas)
        layout_sidebar.addSpacing(5)

        self.layout_lista_conversas = QVBoxLayout()
        layout_sidebar.addLayout(self.layout_lista_conversas)
        self.atualizar_lista_conversas()

        maximizador_menu = QPushButton()
        minimizar_sidebar()
        maximizador_menu.setIcon(QIcon(f"{self.orig_dir}\\ícones\\expansão_menu.svg"))
        maximizador_menu.clicked.connect(minimizar_sidebar)

        layout_geral = QHBoxLayout()
        layout_geral.addWidget(maximizador_menu, alignment=Qt.AlignmentFlag.AlignTop)
        layout_geral.addWidget(sidebar)
        layout_geral.addLayout(layout_principal_area)

        self.setLayout(layout_geral)
        self.setWindowIcon(QIcon(f"{self.orig_dir}\\ícones\\chatbot.svg"))

        self.atalho_enter = QShortcut(QKeySequence("Return"), self)
        self.atalho_enter.activated.connect(click_botao_prompt)
        self.atalho_enter_num = QShortcut(QKeySequence("Enter"), self)
        self.atalho_enter_num.activated.connect(click_botao_prompt)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = MinhaJanela()
    janela.show()
    sys.exit(app.exec())
