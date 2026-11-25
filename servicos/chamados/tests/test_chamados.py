from datetime import datetime

from tests.conftest import abrir


def test_abrir_calcula_sla_e_notifica(cliente, contas):
    r = abrir(cliente, contas, prioridade="critica", ativo_id=1)
    assert r.status_code == 201
    c = r.json()
    assert c["solicitante_id"] == contas["ana"]["id"]
    horas = (datetime.fromisoformat(c["prazo_sla"]) - datetime.fromisoformat(c["criado_em"])).total_seconds() / 3600
    assert round(horas) == 4
    avisos = cliente.get("/notificacoes", headers=contas["ana"]["headers"]).json()
    assert avisos[0]["tipo"] == "ChamadoAberto"


def test_abrir_com_ativo_inexistente(cliente, contas):
    assert abrir(cliente, contas, ativo_id=999).status_code == 404


def test_atribuir_muda_status_e_avisa_tecnico(cliente, contas):
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.patch(f"/chamados/{cid}/atribuir", headers=contas["carla"]["headers"], json={"tecnico_id": 4})
    assert r.json()["status"] == "em_atendimento"
    avisos = cliente.get("/notificacoes", headers=contas["carla"]["headers"]).json()
    assert avisos[0]["tipo"] == "ChamadoAtribuido"


def test_so_tecnico_pode_ser_atribuido(cliente, contas):
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.patch(f"/chamados/{cid}/atribuir", headers=contas["carla"]["headers"], json={"tecnico_id": 2})
    assert r.status_code == 422


def test_atribuir_a_usuario_inexistente(cliente, contas):
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.patch(f"/chamados/{cid}/atribuir", headers=contas["carla"]["headers"], json={"tecnico_id": 99})
    assert r.status_code == 404


def test_fluxo_completo_de_status(cliente, contas):
    cid = abrir(cliente, contas).json()["id"]
    tec = contas["carla"]["headers"]
    cliente.patch(f"/chamados/{cid}/atribuir", headers=tec, json={"tecnico_id": 4})
    assert cliente.patch(f"/chamados/{cid}/status", headers=tec, json={"status": "resolvido"}).status_code == 200
    r = cliente.patch(f"/chamados/{cid}/status", headers=contas["ana"]["headers"], json={"status": "fechado"})
    assert r.json()["status"] == "fechado"


def test_transicao_invalida(cliente, contas):
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.patch(f"/chamados/{cid}/status", headers=contas["carla"]["headers"], json={"status": "fechado"})
    assert r.status_code == 422


def test_iniciar_atendimento_sem_tecnico(cliente, contas):
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.patch(f"/chamados/{cid}/status", headers=contas["carla"]["headers"], json={"status": "em_atendimento"})
    assert r.status_code == 422


def test_comentar_usa_o_usuario_logado(cliente, contas):
    cid = abrir(cliente, contas).json()["id"]
    r = cliente.post(f"/chamados/{cid}/comentarios", headers=contas["carla"]["headers"], json={"texto": "Verificando a fonte."})
    assert r.status_code == 201 and r.json()["autor_id"] == 4
    assert len(cliente.get(f"/chamados/{cid}", headers=contas["ana"]["headers"]).json()["comentarios"]) == 1


def test_painel(cliente, contas):
    abrir(cliente, contas)
    abrir(cliente, contas, prioridade="baixa")
    p = cliente.get("/chamados/painel", headers=contas["carla"]["headers"]).json()
    assert p["total"] == 2 and p["por_status"] == {"aberto": 2}
