"""Testes de segurança do serviço de Inventário: token, permissões e validação de entrada."""
from datetime import datetime, timedelta, timezone

import jwt

from app import config
from tests.conftest import fazer_token

ATIVO = {"patrimonio": "PAT-9", "tipo": "outro", "descricao": "X", "setor": "TI"}


def test_rotas_exigem_login(cliente):
    for metodo, rota in [("get", "/ativos"), ("get", "/ativos/1"), ("post", "/ativos")]:
        assert getattr(cliente, metodo)(rota).status_code == 401, rota


def test_saude_nao_exige_login(cliente):
    r = cliente.get("/saude")
    assert r.status_code == 200 and r.json()["servico"] == "inventario"


def test_token_adulterado(cliente, contas):
    h = {"Authorization": contas["ana"]["Authorization"] + "x"}
    assert cliente.get("/ativos", headers=h).status_code == 401


def test_token_assinado_com_outro_segredo(cliente):
    falso = fazer_token(1, "admin", segredo="segredo-de-outra-pessoa-com-mais-de-32-caracteres")
    assert cliente.get("/ativos", headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_token_sem_assinatura_alg_none(cliente):
    agora = datetime.now(timezone.utc)
    falso = jwt.encode({"sub": "1", "perfil": "admin", "iss": config.JWT_EMISSOR, "iat": agora,
                        "exp": agora + timedelta(hours=1)}, None, algorithm="none")
    assert cliente.get("/ativos", headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_token_expirado(cliente):
    antigo = datetime.now(timezone.utc) - timedelta(hours=2)
    vencido = jwt.encode({"sub": "2", "perfil": "solicitante", "iss": config.JWT_EMISSOR, "iat": antigo,
                          "exp": antigo + timedelta(minutes=5)}, config.JWT_SEGREDO, algorithm="HS256")
    assert cliente.get("/ativos", headers={"Authorization": f"Bearer {vencido}"}).status_code == 401


def test_token_sem_perfil_ou_com_perfil_inventado(cliente):
    agora = datetime.now(timezone.utc)
    base = {"sub": "1", "iss": config.JWT_EMISSOR, "iat": agora, "exp": agora + timedelta(hours=1)}
    for extra in ({}, {"perfil": "superadmin"}):
        token = jwt.encode({**base, **extra}, config.JWT_SEGREDO, algorithm="HS256")
        assert cliente.get("/ativos", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_solicitante_nao_cadastra_ativo(cliente, contas):
    assert cliente.post("/ativos", headers=contas["ana"], json=ATIVO).status_code == 403


def test_campo_extra_e_recusado(cliente, contas):
    assert cliente.post("/ativos", headers=contas["carla"], json={**ATIVO, "id": 5}).status_code == 422


def test_requisicao_grande_demais(cliente, contas):
    corpo = '{"descricao": "' + "x" * 70000 + '"}'
    r = cliente.post("/ativos", headers={**contas["carla"], "Content-Type": "application/json"}, content=corpo)
    assert r.status_code == 413


def test_cabecalhos_de_seguranca(cliente):
    r = cliente.get("/saude")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"


def test_servico_nao_sobe_sem_segredo():
    import importlib
    import os
    import pytest
    original = os.environ["JWT_SEGREDO"]
    os.environ["JWT_SEGREDO"] = "curto"
    try:
        with pytest.raises(RuntimeError):
            importlib.reload(config)
    finally:
        os.environ["JWT_SEGREDO"] = original
        importlib.reload(config)
