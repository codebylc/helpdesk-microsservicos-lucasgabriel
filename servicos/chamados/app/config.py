"""Configurações do serviço de Chamados (variáveis de ambiente)."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chamados.db")

JWT_SEGREDO = os.getenv("JWT_SEGREDO", "")
if len(JWT_SEGREDO) < 32:
    raise RuntimeError("Defina JWT_SEGREDO (mínimo 32 caracteres) no arquivo .env.")

JWT_ALGORITMO = "HS256"
JWT_EMISSOR = "helpdesk-ti"

# Endereços dos outros serviços. No Docker Compose, o nome do serviço vira o endereço.
USUARIOS_URL = os.getenv("USUARIOS_URL", "http://usuarios:8000").rstrip("/")
INVENTARIO_URL = os.getenv("INVENTARIO_URL", "http://inventario:8000").rstrip("/")

# Tempo limite das chamadas entre serviços: sem isso, um serviço lento travaria este também
TIMEOUT_SEGUNDOS = float(os.getenv("TIMEOUT_SEGUNDOS", "3"))
TIMEOUT_CONEXAO_SEGUNDOS = float(os.getenv("TIMEOUT_CONEXAO_SEGUNDOS", "1"))

TAMANHO_MAXIMO_REQUISICAO = 64 * 1024
DOCS_ATIVA = os.getenv("DOCS", "1") == "1"
