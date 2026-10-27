from __future__ import annotations


class ErroVitrine(Exception):
    """fase: "lexico", "sintatico", "semantico" ou "execucao"."""

    def __init__(self, fase: str, linha: int, coluna: int, mensagem: str):
        super().__init__(mensagem)
        self.fase = fase
        self.linha = linha
        self.coluna = coluna
        self.mensagem = mensagem

    def formatar(self, arquivo: str) -> str:
        return f"erro {self.fase} [{arquivo}:{self.linha}:{self.coluna}]\n   {self.mensagem}"


def erro_semantico(pos, mensagem: str) -> ErroVitrine:
    return ErroVitrine("semantico", pos.linha, pos.coluna, mensagem)


def erro_execucao(pos, mensagem: str) -> ErroVitrine:
    return ErroVitrine("execucao", pos.linha, pos.coluna, mensagem)
