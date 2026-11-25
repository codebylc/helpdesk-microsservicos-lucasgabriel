def test_admin_cria_usuario(cliente, contas):
    r = cliente.post("/usuarios", headers=contas["admin"]["headers"],
                     json={"nome": "Davi", "email": "davi@x.com", "perfil": "tecnico", "senha": "Forte1234"})
    assert r.status_code == 201
    assert "senha" not in r.json() and "senha_hash" not in r.json()


def test_email_repetido_e_recusado(cliente, contas):
    dados = {"nome": "Ana 2", "email": "ANA@x.com", "perfil": "solicitante", "senha": "Forte1234"}
    assert cliente.post("/usuarios", headers=contas["admin"]["headers"], json=dados).status_code == 422


def test_usuario_inexistente(cliente, contas):
    assert cliente.get("/usuarios/99", headers=contas["ana"]["headers"]).status_code == 404


def test_lista_publica_nao_mostra_email(cliente, contas):
    lista = cliente.get("/usuarios", headers=contas["ana"]["headers"]).json()
    assert lista and all("email" not in u for u in lista)


def test_obter_usuario_devolve_perfil_para_o_servico_de_chamados(cliente, contas):
    """O serviço de Chamados usa GET /usuarios/{id} para conferir se o técnico existe e é técnico."""
    r = cliente.get(f"/usuarios/{contas['carla']['id']}", headers=contas["ana"]["headers"])
    assert r.status_code == 200
    assert r.json() == {"id": contas["carla"]["id"], "nome": "Carla", "perfil": "tecnico"}


def test_login_devolve_token_com_perfil(cliente, contas):
    import jwt
    from app import config
    token = contas["carla"]["headers"]["Authorization"].split()[1]
    dados = jwt.decode(token, config.JWT_SEGREDO, algorithms=["HS256"], issuer=config.JWT_EMISSOR)
    assert dados["perfil"] == "tecnico" and dados["sub"] == str(contas["carla"]["id"])
