"""Chamadas HTTP aos outros serviços (Usuários e Inventário).

No monólito isto era `usuarios.servico.obter_tecnico(...)` e `inventario.servico.obter(...)`:
uma chamada de função, que nunca falhava por "rede". Agora pode haver lentidão, queda
e token recusado, então cada chamada tem:
  - timeout (não esperamos para sempre);
  - o token do usuário repassado (o outro serviço confere de novo);
  - falha de rede/5xx traduzida para ServicoIndisponivel (o Chamados responde 503 em vez de travar).
"""
import logging

import httpx
from fastapi import HTTPException, status

from app import config
from app.erros import NaoEncontrado, RegraDeNegocio, ServicoIndisponivel

log = logging.getLogger("chamados.clientes")

_cliente = httpx.Client(timeout=httpx.Timeout(config.TIMEOUT_SEGUNDOS, connect=config.TIMEOUT_CONEXAO_SEGUNDOS))


def _consultar(servico: str, url: str, token: str) -> dict | None:
    """GET autenticado. Devolve o JSON, ou None se o outro serviço respondeu 404."""
    try:
        resposta = _cliente.get(url, headers={"Authorization": f"Bearer {token}"})
    except httpx.TransportError as erro:  # sem conexão, conexão recusada, timeout...
        log.warning("Serviço de %s indisponível (%s): %s", servico, type(erro).__name__, url)
        raise ServicoIndisponivel(servico) from erro

    if resposta.status_code == 200:
        return resposta.json()
    if resposta.status_code == 404:
        return None
    if resposta.status_code in (401, 403):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Faça login para continuar.",
                            headers={"WWW-Authenticate": "Bearer"})
    log.warning("Serviço de %s respondeu %s: %s", servico, resposta.status_code, url)
    raise ServicoIndisponivel(servico)


def verificar_ativo(ativo_id: int, token: str) -> dict:
    dados = _consultar("Inventário", f"{config.INVENTARIO_URL}/ativos/{ativo_id}", token)
    if dados is None:
        raise NaoEncontrado(f"Ativo {ativo_id} não encontrado.")
    return dados


def obter_tecnico(usuario_id: int, token: str) -> dict:
    dados = _consultar("Usuários", f"{config.USUARIOS_URL}/usuarios/{usuario_id}", token)
    if dados is None:
        raise NaoEncontrado(f"Usuário {usuario_id} não encontrado.")
    if dados.get("perfil") != "tecnico":
        raise RegraDeNegocio(f"Usuário {usuario_id} não é técnico.")
    return dados
