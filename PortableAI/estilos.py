def mensagem_operacao_cancelada() -> None:
    estilo = f"<div style='text-align: right;'><span style='color: red; font-family: Segoe UI; font-size: 18px;'>Operação cancelada pelo usuário</span></div><br><br>"
    return estilo


def html_base() -> str:
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

        /* ESTILO PARA TABELAS */
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            font-size: 14px;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        th {
            background-color: #f2f2f2;
            color: #333;
            font-weight: bold;
            text-align: left;
            padding: 10px;
            border: 1px solid #ddd;
        }
        td {
            padding: 8px 10px;
            border: 1px solid #ddd;
            text-align: left;
            color: #444;
        }
        tr:nth-child(even) {
            background-color: #fafafa;
        }
        tr:hover {
            background-color: #f1f1f1;
        }

        h1, h2, h3, h4 {
            margin-top: 15px;
            margin-bottom: 8px;
            color: #2c3e50;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 4px;
            font-family: Consolas, monospace;
            font-size: 0.9em;
        }
        pre {
            background-color: #f8f8f8;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #eee;
            overflow-x: auto;
        }
        blockquote {
            border-left: 4px solid #ccc;
            margin: 10px 0;
            padding-left: 10px;
            color: #666;
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
            max-width: 85%;
            font-size: 16px;
            text-align: left;
            line-height: 1.6;
        }

        .bot-wrapper { justify-content: flex-start; }
        .bot { background: #e6e6e6; }

        .user-wrapper { justify-content: flex-end; }
        .user { background: #dcf8c6; }

        /* --- ANIMAÇÃO DE DIGITANDO (TRÊS PONTINHOS) - ESSENCIAL --- */
        .typing {
            display: flex;
            align-items: center;
            column-gap: 4px;
            height: 24px;
            padding: 0 5px; /* Espaço extra */
        }
        .dot {
            width: 8px;
            height: 8px;
            background-color: #555; /* Cor mais escura para visibilidade */
            border-radius: 50%;
            animation: typing 1s infinite alternate;
        }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0% { transform: translateY(0); opacity: 0.4; }
            100% { transform: translateY(-5px); opacity: 1; }
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
               padding: 5px 10px; /* Padding ajustado para visual melhor */
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
    # ALTERADO PARA QLineEdit E AJUSTADO PARA COR DE FUNDO UNIFORME
    estilo = """
           QLineEdit {
               font-family: Segoe UI;
               font-size: 12px;
               background-color: #DEE6EE; 
               color: #333;
               border: none;
               padding: 0px 10px;
               border-radius: 17px; /* Arredondamento para formato de pílula (metade da altura de 35px) */
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
