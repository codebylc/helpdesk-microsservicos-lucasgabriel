"""Serviço de Chamados: abertura, atribuição, status, comentários, painel e notificações.

É dono do banco de chamados. Para conferir técnico e equipamento, chama os serviços
de Usuários e de Inventário pela rede (app/clientes.py).
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app import dados_exemplo
from app.chamados.rotas import router as chamados_router
from app.config import DOCS_ATIVA
from app.database import Base, SessionLocal, engine
from app.erros import NaoEncontrado, RegraDeNegocio, SemPermissao, ServicoIndisponivel
from app.notificacoes.rotas import router as notificacoes_router
from app.seguranca_http import CabecalhosDeSeguranca


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    Base.metadata.create_all(engine)
    if os.getenv("DADOS_EXEMPLO", "1") == "1":
        with SessionLocal() as db:
            dados_exemplo.carregar(db)
    yield


app = FastAPI(
    title="HelpDesk TI · Serviço de Chamados", version="3.0.0", lifespan=ciclo_de_vida,
    docs_url="/docs" if DOCS_ATIVA else None, redoc_url=None,
    openapi_url="/openapi.json" if DOCS_ATIVA else None,
)
app.add_middleware(CabecalhosDeSeguranca)
app.include_router(chamados_router)
app.include_router(notificacoes_router)


@app.exception_handler(NaoEncontrado)
def tratar_nao_encontrado(request: Request, erro: NaoEncontrado):
    return JSONResponse(status_code=404, content={"detail": str(erro)})


@app.exception_handler(RegraDeNegocio)
def tratar_regra(request: Request, erro: RegraDeNegocio):
    return JSONResponse(status_code=422, content={"detail": str(erro)})


@app.exception_handler(SemPermissao)
def tratar_sem_permissao(request: Request, erro: SemPermissao):
    return JSONResponse(status_code=403, content={"detail": str(erro)})


@app.exception_handler(IntegrityError)
def tratar_conflito(request: Request, erro: IntegrityError):
    return JSONResponse(status_code=409, content={"detail": "O registro conflita com outro já existente."})


@app.exception_handler(ServicoIndisponivel)
def tratar_servico_indisponivel(request: Request, erro: ServicoIndisponivel):
    """Falha de outro serviço: erro claro (503) em vez de travar ou devolver 500."""
    return JSONResponse(
        status_code=503, headers={"Retry-After": "5"},
        content={"detail": f"O serviço de {erro.servico} está indisponível no momento. Tente novamente em instantes."},
    )


@app.get("/saude", tags=["Saúde"])
def saude():
    return {"servico": "chamados", "status": "ok"}
