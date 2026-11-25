import os

# Definidos antes de importar o app (o serviço lê isto ao iniciar)
os.environ.setdefault("JWT_SEGREDO", "segredo-somente-para-testes-com-mais-de-32-caracteres")
os.environ["DADOS_EXEMPLO"] = "0"
os.environ["USUARIOS_URL"] = "http://usuarios.test"
os.environ["INVENTARIO_URL"] = "http://inventario.test"

from datetime import datetime, timedelta, timezone

import httpx
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import clientes, config
from app.database import Base, get_db
from app.main import app

USUARIOS = {
    1: {"id": 1, "nome": "Admin", "perfil": "admin"},
    2: {"id": 2, "nome": "Ana", "perfil": "solicitante"},
    3: {"id": 3, "nome": "Bia", "perfil": "solicitante"},
    4: {"id": 4, "nome": "Carla", "perfil": "tecnico"},
}
ATIVOS = {1: {"id": 1, "patrimonio": "PAT-1", "tipo": "computador", "descricao": "Desktop", "setor": "TI"}}


def fazer_token(usuario_id: int, perfil: str, segredo: str | None = None, **extra) -> str:
    agora = datetime.now(timezone.utc)
    dados = {"sub": str(usuario_id), "perfil": perfil, "iss": config.JWT_EMISSOR, "iat": agora,
             "exp": agora + timedelta(hours=1), **extra}
    return jwt.encode(dados, segredo or config.JWT_SEGREDO, algorithm="HS256")


class OutrosServicos:
    """Faz de conta de Usuários e Inventário. Permite "derrubar" cada um e ver o que chegou."""

    def __init__(self):
        self.fora: set[str] = set()       # {"usuarios", "inventario"}
        self.lento: set[str] = set()      # respondem com timeout
        self.chamadas: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.chamadas.append(request)
        nome = "usuarios" if request.url.host == "usuarios.test" else "inventario"
        if nome in self.fora:
            raise httpx.ConnectError("conexão recusada", request=request)
        if nome in self.lento:
            raise httpx.ReadTimeout("demorou demais", request=request)
        if not request.headers.get("authorization", "").startswith("Bearer "):
            return httpx.Response(401, json={"detail": "Faça login para continuar."})
        tabela = USUARIOS if nome == "usuarios" else ATIVOS
        item = tabela.get(int(request.url.path.rsplit("/", 1)[1]))
        return httpx.Response(200, json=item) if item else httpx.Response(404, json={"detail": "não encontrado"})


@pytest.fixture
def servicos(monkeypatch):
    falso = OutrosServicos()
    monkeypatch.setattr(clientes, "_cliente", httpx.Client(transport=httpx.MockTransport(falso)))
    return falso


@pytest.fixture
def cliente(servicos):
    """Banco novo, em memória, para cada teste."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def db_de_teste():
        db = Sessao()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = db_de_teste
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def contas():
    def cab(i, perfil):
        return {"headers": {"Authorization": f"Bearer {fazer_token(i, perfil)}"}, "id": i}
    return {"admin": cab(1, "admin"), "ana": cab(2, "solicitante"), "bia": cab(3, "solicitante"), "carla": cab(4, "tecnico")}


def abrir(cliente, contas, quem="ana", prioridade="alta", **extra):
    dados = {"titulo": "PC não liga", "descricao": "Nada acontece", "prioridade": prioridade, **extra}
    return cliente.post("/chamados", headers=contas[quem]["headers"], json=dados)
