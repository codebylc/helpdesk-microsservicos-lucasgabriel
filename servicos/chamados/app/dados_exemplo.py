"""Chamados de exemplo (só para aula). Em produção, rode com DADOS_EXEMPLO=0.

Decisão: os dados são gravados DIRETO no banco deste serviço, sem chamar Usuários
nem Inventário. Assim o Chamados sobe mesmo se os outros ainda não estiverem prontos.
Os ids usados (usuários 2=Ana, 3=Bruno, 4=Carla; ativos 1 e 2) são os dos dados de
exemplo dos outros dois serviços.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.chamados import repositorio
from app.chamados.modelos import Chamado
from app.chamados.servico import calcular_prazo
from app.notificacoes import servico as notificacoes

ANA, BRUNO, CARLA = 2, 3, 4


def _novo(db: Session, titulo: str, descricao: str, prioridade: str, solicitante_id: int, ativo_id: int | None) -> Chamado:
    agora = datetime.now()
    chamado = repositorio.salvar(db, Chamado(
        titulo=titulo, descricao=descricao, prioridade=prioridade, status="aberto",
        solicitante_id=solicitante_id, ativo_id=ativo_id, criado_em=agora,
        prazo_sla=calcular_prazo(prioridade, agora),
    ))
    notificacoes.notificar(
        db, "ChamadoAberto", solicitante_id,
        f"Seu chamado #{chamado.id} foi aberto. Prazo: {chamado.prazo_sla:%d/%m %H:%M}.",
    )
    return chamado


def carregar(db: Session) -> None:
    if repositorio.listar(db):
        return
    c1 = _novo(db, "Computador não liga", "Apertei o botão e nada acontece.", "alta", ANA, 1)
    _novo(db, "Impressora atolando papel", "Atola a cada 3 folhas.", "media", BRUNO, 2)
    _novo(db, "Acesso ao sistema de RH", "Preciso de acesso para a nova estagiária.", "baixa", BRUNO, None)
    c1.tecnico_id, c1.status = CARLA, "em_atendimento"
    repositorio.salvar(db, c1)
    notificacoes.notificar(db, "ChamadoAtribuido", CARLA, f"O chamado #{c1.id} foi atribuído a você.")
