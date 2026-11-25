"""Configurações do serviço de Inventário (variáveis de ambiente)."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./inventario.db")

# Mesmo segredo do serviço de Usuários: é assim que este serviço confere que o
# token foi mesmo emitido por ele. Obrigatório (sem ele o serviço não sobe).
JWT_SEGREDO = os.getenv("JWT_SEGREDO", "")
if len(JWT_SEGREDO) < 32:
    raise RuntimeError("Defina JWT_SEGREDO (mínimo 32 caracteres) no arquivo .env.")

JWT_ALGORITMO = "HS256"
JWT_EMISSOR = "helpdesk-ti"

TAMANHO_MAXIMO_REQUISICAO = 64 * 1024
DOCS_ATIVA = os.getenv("DOCS", "1") == "1"
