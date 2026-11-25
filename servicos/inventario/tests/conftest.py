import os

# O serviço exige JWT_SEGREDO; nos testes usamos um valor fixo (definido antes de importar o app)
os.environ.setdefault("JWT_SEGREDO", "segredo-somente-para-testes-com-mais-de-32-caracteres")
os.environ["DADOS_EXEMPLO"] = "0"

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import config
from app.database import Base, get_db
from app.main import app


def fazer_token(usuario_id: int, perfil: str, segredo: str | None = None, **extra) -> str:
    """Gera um token como o serviço de Usuários geraria (aqui não existe login)."""
    agora = datetime.now(timezone.utc)
    dados = {"sub": str(usuario_id), "perfil": perfil, "iss": config.JWT_EMISSOR, "iat": agora,
             "exp": agora + timedelta(hours=1), **extra}
    return jwt.encode(dados, segredo or config.JWT_SEGREDO, algorithm="HS256")


@pytest.fixture
def cliente():
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
    return {
        "admin": {"Authorization": f"Bearer {fazer_token(1, 'admin')}"},
        "ana": {"Authorization": f"Bearer {fazer_token(2, 'solicitante')}"},
        "carla": {"Authorization": f"Bearer {fazer_token(4, 'tecnico')}"},
    }
