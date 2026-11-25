"""Equipamentos de exemplo (só para aula). Em produção, rode com DADOS_EXEMPLO=0.

Os ids 1 a 3 são usados pelos chamados de exemplo do serviço de Chamados.
"""
from sqlalchemy.orm import Session

from app.inventario import servico as inventario
from app.inventario.esquemas import AtivoCriar


def carregar(db: Session) -> None:
    if inventario.listar(db):
        return
    inventario.criar(db, AtivoCriar(patrimonio="PAT-0001", tipo="computador", descricao="Desktop Dell OptiPlex", setor="Financeiro"))
    inventario.criar(db, AtivoCriar(patrimonio="PAT-0002", tipo="impressora", descricao="Impressora HP LaserJet", setor="RH"))
    inventario.criar(db, AtivoCriar(patrimonio="PAT-0003", tipo="notebook", descricao="Notebook Lenovo ThinkPad", setor="TI"))
