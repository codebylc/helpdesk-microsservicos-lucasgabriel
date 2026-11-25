"""Validação dos tokens JWT emitidos pelo serviço de Usuários."""
from dataclasses import dataclass

import jwt

from app.config import JWT_ALGORITMO, JWT_EMISSOR, JWT_SEGREDO

PERFIS = ("solicitante", "tecnico", "admin")


class TokenInvalido(Exception):
    pass


@dataclass(frozen=True)
class Identidade:
    """Quem está chamando, segundo o token (sem consultar nenhum banco)."""
    id: int
    perfil: str


def ler(token: str) -> Identidade:
    try:
        dados = jwt.decode(
            token, JWT_SEGREDO, algorithms=[JWT_ALGORITMO], issuer=JWT_EMISSOR,
            options={"require": ["exp", "iat", "sub", "iss", "perfil"]},
        )
        perfil = dados["perfil"]
        if perfil not in PERFIS:
            raise TokenInvalido()
        return Identidade(id=int(dados["sub"]), perfil=perfil)
    except (jwt.PyJWTError, ValueError) as erro:
        raise TokenInvalido() from erro
