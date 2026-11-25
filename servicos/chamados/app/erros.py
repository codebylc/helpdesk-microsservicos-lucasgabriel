"""Erros de negócio e de comunicação entre serviços."""


class NaoEncontrado(Exception):
    """O recurso pedido não existe (ou o usuário não pode vê-lo)."""


class RegraDeNegocio(Exception):
    """A operação viola uma regra do sistema."""


class SemPermissao(Exception):
    """O usuário está logado, mas não pode fazer esta operação."""


class ServicoIndisponivel(Exception):
    """Outro serviço (Usuários ou Inventário) não respondeu a tempo ou está fora do ar.

    Novo em relação ao monólito: ali uma chamada de função nunca "ficava fora do ar".
    """

    def __init__(self, servico: str):
        super().__init__(servico)
        self.servico = servico
