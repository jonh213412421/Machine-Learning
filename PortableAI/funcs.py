import os
import json
import re
import shutil  # Necessário para copiar o modelo
from datetime import datetime
from PyQt6.QtWidgets import QFileDialog

# Tenta importar pypdf para leitura de PDFs
try:
    from pypdf import PdfReader

    TEM_PYPDF = True
except ImportError:
    TEM_PYPDF = False


def listar_modelos():
    """Lista os arquivos .gguf na pasta Llama/Modelos"""
    caminho_modelos = os.path.join(os.getcwd(), "Llama", "Modelos")
    if not os.path.exists(caminho_modelos):
        os.makedirs(caminho_modelos)

    arquivos = [f for f in os.listdir(caminho_modelos) if f.endswith(".gguf")]
    return arquivos


def selecionar_modelo(nome_modelo):
    """Lógica para selecionar/configurar modelo (placeholder)"""
    pass


def adicionar_modelo_gguf():
    """Abre diálogo para selecionar e copiar um modelo .gguf para a pasta do sistema"""
    # Filtra apenas arquivos GGUF
    caminho_origem, _ = QFileDialog.getOpenFileName(None, "Selecionar Modelo GGUF", "",
                                                    "GGUF Files (*.gguf);;All Files (*)")

    if caminho_origem:
        try:
            # Define a pasta de destino
            pasta_destino = os.path.join(os.getcwd(), "Llama", "Modelos")
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)

            nome_arquivo = os.path.basename(caminho_origem)
            caminho_destino = os.path.join(pasta_destino, nome_arquivo)

            # Verifica se já existe para não sobrescrever sem querer (opcional)
            if os.path.exists(caminho_destino):
                print(f"O modelo {nome_arquivo} já existe na pasta.")
                return nome_arquivo  # Retorna o nome para selecionar ele na lista

            # Copia o arquivo (pode demorar um pouco dependendo do tamanho)
            shutil.copy2(caminho_origem, caminho_destino)
            return nome_arquivo

        except Exception as e:
            print(f"Erro ao copiar modelo: {e}")
            return None
    return None


def carregar_arquivo():
    """Abre diálogo para selecionar arquivo de texto ou PDF"""
    # Filtro atualizado para aceitar PDF e TXT
    filtros = "Arquivos de Texto e PDF (*.txt *.pdf);;Arquivos de Texto (*.txt);;PDF (*.pdf);;Todos os Arquivos (*)"
    caminho, _ = QFileDialog.getOpenFileName(None, "Abrir Arquivo", "", filtros)

    if caminho:
        nome = os.path.basename(caminho)
        dados = ""

        try:
            # Lógica para PDF
            if caminho.lower().endswith('.pdf'):
                if not TEM_PYPDF:
                    # Retorna um aviso no nome se a lib faltar
                    return "Erro: instale 'pip install pypdf'", ""

                reader = PdfReader(caminho)
                texto_paginas = []
                for page in reader.pages:
                    texto_extraido = page.extract_text()
                    if texto_extraido:
                        texto_paginas.append(texto_extraido)
                dados = "\n".join(texto_paginas)

            # Lógica para TXT e outros
            else:
                with open(caminho, 'r', encoding='utf-8') as f:
                    dados = f.read()

            return nome, dados

        except Exception as e:
            return f"Erro: {str(e)}", ""

    return None, None


# --- FUNÇÕES DE CONVERSA ---

def garantir_pasta_conversas():
    path = os.path.join(os.getcwd(), "data", "conversas")
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def listar_conversas():
    """Lista arquivos .json na pasta de conversas, ordenados por modificação"""
    path = garantir_pasta_conversas()
    arquivos = [f for f in os.listdir(path) if f.endswith(".json")]
    arquivos.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)), reverse=True)
    return arquivos


def gerar_nome_conversa(primeira_mensagem):
    """Gera um nome de arquivo seguro baseado na primeira mensagem"""
    resumo = primeira_mensagem[:30]
    nome_seguro = re.sub(r'[\\/*?:"<>|]', "", resumo)
    nome_seguro = nome_seguro.strip().replace(" ", "_")

    if not nome_seguro:
        nome_seguro = "conversa_sem_titulo"

    return f"{nome_seguro}.json"


def salvar_conversa_json(historico, nome_arquivo=None):
    """Salva o histórico (lista de dicts) em um arquivo JSON"""
    path = garantir_pasta_conversas()

    if not nome_arquivo:
        if len(historico) > 0:
            primeira_msg = next((m['content'] for m in historico if m['role'] == 'user'), "Nova Conversa")
            nome_arquivo = gerar_nome_conversa(primeira_msg)
        else:
            return None

    caminho_completo = os.path.join(path, nome_arquivo)

    with open(caminho_completo, 'w', encoding='utf-8') as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

    return nome_arquivo


def ler_conversa_json(nome_arquivo):
    """Lê um arquivo JSON e retorna a lista de mensagens"""
    path = garantir_pasta_conversas()
    caminho_completo = os.path.join(path, nome_arquivo)

    if os.path.exists(caminho_completo):
        try:
            with open(caminho_completo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def excluir_conversa(nome_arquivo):
    """Exclui permanentemente um arquivo de conversa"""
    path = garantir_pasta_conversas()
    caminho_completo = os.path.join(path, nome_arquivo)

    if os.path.exists(caminho_completo):
        try:
            os.remove(caminho_completo)
            return True
        except OSError as e:
            print(f"Erro ao excluir: {e}")
            return False
    return False
