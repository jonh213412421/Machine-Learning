def mensagem_operacao_cancelada() -> None:
    estilo = f"<div style='text-align: right;'><span style='color: red; font-family: Segoe UI; font-size: 18px;'>Operação cancelada pelo usuário</span></div><br><br>"
    return estilo


def html_base() -> str:
    # IMPORTANTE: Script do MathJax para renderizar equações matemáticas
    estilo = """
            <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">

        <!-- Configuração do MathJax -->
        <script>
        window.MathJax = {
          tex: {
            inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
            displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
            processEscapes: true
          },
          options: {
            ignoreHtmlClass: 'tex2jax_ignore',
            processHtmlClass: 'tex2jax_process'
          }
        };
        </script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

        <style>
        body {
            font-family: Segoe UI;
            background: #fafafa;
            margin: 0;
            padding: 10px;
            display: flex;
            flex-direction: column;
        }

        /* Cabeçalhos do Markdown convertidos */
        h1, h2, h3 {
            margin-top: 10px;
            margin-bottom: 5px;
            color: #333;
        }

        /* CONTÊINER DA MENSAGEM */
        .msg-wrapper {
            width: 100%;
            display: flex;
            margin: 6px 0;
        }

        /* BOLHA */
        .msg {
            padding: 12px 20px;
            border-radius: 10px;
            max-width: 75%;
            font-size: 16px;
            text-align: justify;
            line-height: 1.5; /* Melhor leitura */
        }

        /* BOT (ESQUERDA) */
        .bot-wrapper {
            justify-content: flex-start;
        }
        .bot {
            background: #e6e6e6;
        }

        /* USER (DIREITA) */
        .user-wrapper {
            justify-content: flex-end;
        }
        .user {
            background: #dcf8c6;
        }
        </style>
        </head>
        <body id="chat"></body>
        </html>
    """
    return estilo


def estilo_chat_tela() -> str:
    estilo = """
           QTextBrowser {
               background-color: #DEE6EE;  
               color: #222222;             
               border: 1px solid #ccc;     
               border-radius: 8px;         
               padding: 8px;               
           }
       """
    return estilo


def estilo_chat_botao() -> str:
    estilo = """
               QPushButton {
                   background-color: rgb(245, 245, 245);
                   border: none;
                   border-radius: 20px;
                   margin: 0px;
                   padding: 0px;
               }
               QPushButton:pressed {
                   background-color: rgb(230, 230, 230);
               }
               QPushButton:hover {
                   background-color: rgb(230, 230, 230);
               }
           """
    return estilo


def estilo_botao_arquivo() -> str:
    estilo = """           
           QPushButton {
               font-family: Segoe UI;
               font-size: 14px;
               background-color: rgb(180, 180, 180); 
               border: none;
               border-radius: 20px;
               margin: 0px;
               padding: 0px;
           }
           QPushButton:pressed {
               background-color: rgb(230, 230, 230);    
                   padding-top: 2px;                       
                   padding-bottom: -2px;
           }
           QPushButton:hover {
               background-color: rgb(150, 150, 150);     
           }
       """
    return estilo


def estilo_prompt_thread(prompt) -> str:
    estilo = f"""
            <div class='msg-wrapper bot-wrapper'>
                <div class='msg user'>{prompt}</div>
            </div>
            """
    return estilo


def estilo_resposta_prompt_thread(linha) -> str:
    estilo = f"""
            <div class='msg-wrapper user-wrapper'>
                <div class='msg bot'>{linha}</div>
            </div>
            """
    return estilo


def estilo_arquivo_carregado() -> str:
    estilo = """
           QTextEdit {
               font-family: Segoe UI;
               font-size: 14px;
               background-color: #DEE6EE; 
               border: none;
               padding: 0px;
               border-radius: 20px;
           }"""
    return estilo


def estilo_sidebar() -> str:
    estilo = """
           QFrame {
               background: qlineargradient(
               x1: 0, y1: 0,
               x2: 0, y2: 1,
               stop: 0 #EFF3F8, 
               stop: 1 #DEE6EE  
       );     
               border-right: 1px solid #333;   
           }
       """
    return estilo


def estilo_menu() -> str:
    estilo = """
           QLabel {
               font-family: Segoe UI;
               color: black;             
               font-weight: bold;          
               font-size: 16px;       
               letter-spacing: 2px;     
               background: transparent;
               border-bottom: 1px solid #333;
               padding-bottom: 5px;
           }
       """
    return estilo


def estilo_titulo_quantidade_tokens_arquivo() -> str:
    estilo = """
           QLabel {
               color: black;            
               font-weight: bold;     
               font-size: 12px;
               letter-spacing: 2px;     
               background: transparent;
               border-bottom: 1px solid #333;
               padding-bottom: 5px;
           }
       """
    return estilo


def estilo_mostrar_quantidade_tokens_arquivo() -> str:
    estilo = """
           QTextEdit {
               color: black;          
               font-weight: bold;   
               font-size: 12px;           
               letter-spacing: 2px;      
               background: transparent;
               border: none;
           }
       """
    return estilo


def estilo_botao_sobre() -> str:
    estilo = """
           QPushButton {
               font-family: Segoe UI;
               font-size: 14px;
               background-color: rgb(180, 180, 180); 
               border: none;
               border-radius: 5px;
               margin: 0px;
               padding: 0px;
           }
           QPushButton:pressed {
               background-color: rgb(230, 230, 230);   
                   padding-top: 2px;    
                   padding-bottom: -2px;
           }
           QPushButton:hover {
               background-color: rgb(150, 150, 150);
           }
       """
    return estilo


def estilo_titulo_conversas() -> str:
    estilo = """
           QLabel {
               color: black;            
               font-weight: bold;
               font-size: 12px;       
               letter-spacing: 2px;        
               background: transparent;
               border-bottom: 1px solid #333;
               padding-bottom: 5px;
           }
       """
    return estilo


def estilo_botao_conversa() -> str:
    estilo = """
               QPushButton {
                   background-color: rgb(180, 180, 180);
                   border: none;
                   border-radius: 3px;
                   margin: 0px;
                   padding: 0px;
                   text-align: center;
                   font-size: 14px;
               }
               QPushButton:pressed {
                   background-color: rgb(230, 230, 230);  
                       padding-top: 2px;                      
                       padding-bottom: -2px;
               }
               QPushButton:hover {
                   background-color: rgb(150, 150, 150);   
               }
           """
    return estilo


def estilo_botao_modelos() -> str:
    estilo = """
       QComboBox {
           font-family: Segoe UI;
           font-size: 14px;
           background-color: rgb(200, 200, 200);
           border: 1px solid #888;
           border-radius: 10px;   
           padding: 5px;
       }

       QComboBox::drop-down {
           border: 0px;
           border-left: 1px solid #888;
           border-top-right-radius: 10px;
           border-bottom-right-radius: 10px;
           width: 30px;
       }

       QComboBox::down-arrow {
       width: 8px;
       height: 8px;
       border: solid #555;
       border-width: 0 2px 2px 0;
       transform: rotate(45deg);
       margin-right: 6px;
       }

       QComboBox::hover {
       background-color: rgb(150, 150, 150);
       }

       QComboBox::pressed {
       background-color: rgb(230, 230, 230);    
       padding-top: 2px;                    
       padding-bottom: -2px;
       }
   """
    return estilo
