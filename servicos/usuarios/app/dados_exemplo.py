"""Usuários de exemplo (só para aula). Em produção, rode com DADOS_EXEMPLO=0.

A ordem de criação é fixa: os ids 1 a 5 (admin, ana, bruno, carla, diego) são
usados pelos dados de exemplo do serviço de Chamados.
"""
import os

from sqlalchemy.orm import Session

from app.usuarios import servico as usuarios
from app.usuarios.esquemas import UsuarioCriar

SENHA = os.getenv("SENHA_EXEMPLO", "Helpdesk2026")


def carregar(db: Session) -> None:
    if usuarios.listar(db):
        return
    for nome, email, perfil in [
        ("Admin TI", "admin@empresa.com", "admin"),
        ("Ana Souza", "ana@empresa.com", "solicitante"),
        ("Bruno Lima", "bruno@empresa.com", "solicitante"),
        ("Carla Dias", "carla@empresa.com", "tecnico"),
        ("Diego Rocha", "diego@empresa.com", "tecnico"),
    ]:
        usuarios.criar(db, UsuarioCriar(nome=nome, email=email, perfil=perfil, senha=SENHA))
