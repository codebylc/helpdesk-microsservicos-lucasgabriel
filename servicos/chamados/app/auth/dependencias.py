"""Dependências do FastAPI para exigir login e perfil.

Diferença para o monólito: aqui não existe tabela de usuários. A identidade e o
perfil vêm do próprio token (stateless). Ganho: o serviço funciona mesmo com
Usuários fora do ar. Custo: se um usuário for desativado, o token dele continua
valendo até expirar (TOKEN_MINUTOS).
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth import tokens
from app.auth.tokens import Identidade

esquema = HTTPBearer(auto_error=False)

NAO_AUTENTICADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Faça login para continuar.",
    headers={"WWW-Authenticate": "Bearer"},
)


def usuario_atual(credenciais: HTTPAuthorizationCredentials | None = Depends(esquema)) -> Identidade:
    if credenciais is None or credenciais.scheme.lower() != "bearer":
        raise NAO_AUTENTICADO
    try:
        return tokens.ler(credenciais.credentials)
    except tokens.TokenInvalido:
        raise NAO_AUTENTICADO


def exigir_perfil(*perfis: str):
    """Libera a rota só para os perfis informados."""
    def verificar(usuario: Identidade = Depends(usuario_atual)) -> Identidade:
        if usuario.perfil not in perfis:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não tem permissão para esta ação.")
        return usuario
    return verificar
