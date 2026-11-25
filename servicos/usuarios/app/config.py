"""Configurações do serviço de Usuários (variáveis de ambiente)."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./usuarios.db")

# Decisão de arquitetura: no monólito, um JWT_SEGREDO ausente gerava um segredo
# aleatório. Em microsserviços isso quebraria tudo (cada serviço teria um segredo
# diferente e nenhum aceitaria o token do outro). Por isso o segredo agora é
# OBRIGATÓRIO e igual em todos os serviços; sem ele o serviço nem sobe.
JWT_SEGREDO = os.getenv("JWT_SEGREDO", "")
if len(JWT_SEGREDO) < 32:
    raise RuntimeError("Defina JWT_SEGREDO (mínimo 32 caracteres) no arquivo .env.")

JWT_ALGORITMO = "HS256"
JWT_EMISSOR = "helpdesk-ti"
TOKEN_MINUTOS = int(os.getenv("TOKEN_MINUTOS", "60"))

LOGIN_MAX_FALHAS = int(os.getenv("LOGIN_MAX_FALHAS", "5"))
LOGIN_JANELA_SEGUNDOS = int(os.getenv("LOGIN_JANELA_SEGUNDOS", "300"))

TAMANHO_MAXIMO_REQUISICAO = 64 * 1024
DOCS_ATIVA = os.getenv("DOCS", "1") == "1"
