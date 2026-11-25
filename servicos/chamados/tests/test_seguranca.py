"""Testes de segurança do serviço de Chamados: token, permissões e validação de entrada."""
from datetime import datetime, timedelta, timezone

import jwt

from app import config
from tests.conftest import abrir, fazer_token


def test_rotas_exigem_login(cliente):
    for metodo, rota in [("get", "/chamados"), ("post", "/chamados"), ("get", "/chamados/painel"),
                         ("get", "/chamados/1"), ("get", "/notificacoes")]:
        assert getattr(cliente, metodo)(rota).status_code == 401, rota


def test_saude_nao_exige_login(cliente):
    r = cliente.get("/saude")
    assert r.status_code == 200 and r.json()["servico"] == "chamados"


def test_token_adulterado(cliente, contas):
    h = {"Authorization": contas["ana"]["headers"]["Authorization"] + "x"}
    assert cliente.get("/chamados", headers=h).status_code == 401


def test_token_assinado_com_outro_segredo(cliente):
    falso = fazer_token(1, "admin", segredo="segredo-de-outra-pessoa-com-mais-de-32-caracteres")
    assert cliente.get("/chamados", headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_token_sem_assinatura_alg_none(cliente):
    agora = datetime.now(timezone.utc)
    falso = jwt.encode({"sub": "1", "perfil": "admin", "iss": config.JWT_EMISSOR, "iat": agora,
                        "exp": agora + timedelta(hours=1)}, None, algorithm="none")
    assert cliente.get("/chamados", headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_token_expirado(cliente):
    antigo = datetime.now(timezone.utc) - timedelta(hours=2)
    vencido = jwt.encode({"sub": "2", "perfil": "solicitante", "iss": config.JWT_EMISSOR, "iat": antigo,
                          "exp": antigo + timedelta(minutes=5)}, config.JWT_SEGREDO, algorithm="HS256")
    assert cliente.get("/chamados", headers={"Authorization": f"Bearer {vencido}"}).status_code == 401


def test_token_com_perfil_inventado(cliente):
    token = fazer_token(2, "superadmin")
    assert cliente.get("/chamados", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_solicitante_nao_ve_chamado_de_outra_pessoa(cliente, contas):
    cid = abrir(cliente, contas).json()["id"]
    assert cliente.get(f"/chamados/{cid}", headers=contas["bia"]["headers"]).status_code == 404
    assert cliente.get("/chamados", headers=contas["bia"]["headers"]).json() == []


def test_solicitante_nao_atribui_nem_resolve(cliente, contas):
    cid = abrir(cliente, contas).json()["id"]
    h = contas["ana"]["headers"]
    assert cliente.patch(f"/chamados/{cid}/atribuir", headers=h, json={"tecnico_id": 4}).status_code == 403
    assert cliente.patch(f"/chamados/{cid}/status", headers=h, json={"status": "em_atendimento"}).status_code == 403


def test_nao_da_para_abrir_chamado_em_nome_de_outro(cliente, contas):
    assert abrir(cliente, contas, solicitante_id=3).status_code == 422


def test_nao_da_para_comentar_em_nome_de_outro(cliente, contas):
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.post(f"/chamados/{cid}/comentarios", headers=contas["ana"]["headers"], json={"texto": "oi", "autor_id": 4})
    assert r.status_code == 422


def test_notificacoes_sao_so_do_proprio_usuario(cliente, contas):
    abrir(cliente, contas)
    assert cliente.get("/notificacoes", headers=contas["bia"]["headers"]).json() == []


def test_titulo_grande_demais(cliente, contas):
    assert abrir(cliente, contas, titulo="x" * 500).status_code == 422


def test_requisicao_grande_demais(cliente, contas):
    corpo = '{"titulo": "' + "x" * 70000 + '"}'
    r = cliente.post("/chamados", headers={**contas["ana"]["headers"], "Content-Type": "application/json"}, content=corpo)
    assert r.status_code == 413


def test_texto_com_html_e_guardado_como_texto(cliente, contas):
    r = abrir(cliente, contas, titulo="<script>alert(1)</script>")
    assert r.status_code == 201 and r.json()["titulo"] == "<script>alert(1)</script>"


def test_cabecalhos_de_seguranca(cliente):
    r = cliente.get("/saude")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"


def test_token_nao_aparece_no_repr_da_identidade():
    from app.auth.tokens import Identidade
    assert "segredo-token" not in repr(Identidade(id=1, perfil="admin", token="segredo-token"))


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
