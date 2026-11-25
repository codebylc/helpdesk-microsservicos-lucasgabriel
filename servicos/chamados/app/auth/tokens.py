"""Validação dos tokens JWT emitidos pelo serviço de Usuários."""
from dataclasses import dataclass, field

import jwt

from app.config import JWT_ALGORITMO, JWT_EMISSOR, JWT_SEGREDO

PERFIS = ("solicitante", "tecnico", "admin")


class TokenInvalido(Exception):
    pass


@dataclass(frozen=True)
class Identidade:
    """Quem está chamando, segundo o token (sem consultar nenhum banco).

    Guarda também o token bruto para REPASSAR aos outros serviços (cabeçalho Authorization).
    """
    id: int
    perfil: str
    token: str = field(repr=False)  # repr=False: o token não vai parar em logs


def ler(token: str) -> Identidade:
    try:
        dados = jwt.decode(
            token, JWT_SEGREDO, algorithms=[JWT_ALGORITMO], issuer=JWT_EMISSOR,
            options={"require": ["exp", "iat", "sub", "iss", "perfil"]},
        )
        perfil = dados["perfil"]
        if perfil not in PERFIS:
            raise TokenInvalido()
        return Identidade(id=int(dados["sub"]), perfil=perfil, token=token)
    except (jwt.PyJWTError, ValueError) as erro:
        raise TokenInvalido() from erro
