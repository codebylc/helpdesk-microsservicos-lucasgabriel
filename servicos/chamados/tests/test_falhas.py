"""Novo em microsserviços: o que acontece quando OUTRO serviço cai ou demora."""
from tests.conftest import abrir


def test_token_do_usuario_e_repassado_ao_outro_servico(cliente, contas, servicos):
    abrir(cliente, contas, ativo_id=1)
    chamada = servicos.chamadas[-1]
    assert chamada.url.path == "/ativos/1"
    assert chamada.headers["authorization"] == contas["ana"]["headers"]["Authorization"]


def test_inventario_fora_do_ar_da_503_com_mensagem_clara(cliente, contas, servicos):
    servicos.fora.add("inventario")
    r = abrir(cliente, contas, ativo_id=1)
    assert r.status_code == 503
    assert "Inventário" in r.json()["detail"] and r.headers["retry-after"] == "5"


def test_inventario_lento_da_503_por_timeout(cliente, contas, servicos):
    servicos.lento.add("inventario")
    assert abrir(cliente, contas, ativo_id=1).status_code == 503


def test_inventario_fora_nao_derruba_o_resto(cliente, contas, servicos):
    cid = abrir(cliente, contas).json()["id"]
    servicos.fora.add("inventario")
    h = contas["carla"]["headers"]
    assert abrir(cliente, contas).status_code == 201          # chamado SEM equipamento continua abrindo
    assert cliente.get("/chamados", headers=h).status_code == 200
    assert cliente.get("/chamados/painel", headers=h).status_code == 200
    assert cliente.post(f"/chamados/{cid}/comentarios", headers=h, json={"texto": "ok"}).status_code == 201
    assert cliente.get("/saude").status_code == 200


def test_usuarios_fora_do_ar_impede_so_a_atribuicao(cliente, contas, servicos):
    cid = abrir(cliente, contas).json()["id"]
    servicos.fora.add("usuarios")
    h = contas["carla"]["headers"]
    r = cliente.patch(f"/chamados/{cid}/atribuir", headers=h, json={"tecnico_id": 4})
    assert r.status_code == 503 and "Usuários" in r.json()["detail"]
    assert cliente.get(f"/chamados/{cid}", headers=h).json()["status"] == "aberto"  # nada foi alterado
    assert cliente.get("/chamados", headers=h).status_code == 200


def test_servico_volta_e_tudo_funciona_de_novo(cliente, contas, servicos):
    servicos.fora.add("inventario")
    assert abrir(cliente, contas, ativo_id=1).status_code == 503
    servicos.fora.clear()
    assert abrir(cliente, contas, ativo_id=1).status_code == 201


def test_outro_servico_recusando_o_token_da_401(cliente, contas, servicos, monkeypatch):
    import httpx
    from app import clientes
    monkeypatch.setattr(clientes, "_cliente", httpx.Client(transport=httpx.MockTransport(
        lambda req: httpx.Response(401, json={"detail": "x"}))))
    assert abrir(cliente, contas, ativo_id=1).status_code == 401


def test_erro_5xx_do_outro_servico_vira_503(cliente, contas, monkeypatch):
    import httpx
    from app import clientes
    monkeypatch.setattr(clientes, "_cliente", httpx.Client(transport=httpx.MockTransport(
        lambda req: httpx.Response(500, json={"detail": "boom"}))))
    assert abrir(cliente, contas, ativo_id=1).status_code == 503
