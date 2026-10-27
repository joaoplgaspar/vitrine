"""Léxico e sintático (Lark) e construção da AST."""

from __future__ import annotations

from pathlib import Path

from lark import Lark, Token, Transformer, v_args
from lark.exceptions import UnexpectedCharacters, UnexpectedToken
from lark.lexer import PatternStr

from . import arvore as a
from .erros import ErroVitrine

_GRAMATICA = (Path(__file__).parent / "grammar.lark").read_text(encoding="utf-8")
_LARK = Lark(_GRAMATICA, start="programa", parser="lalr", propagate_positions=True)

_NOMES_TERMINAIS = {
    "IDENT": "um nome",
    "NUMERO": "um número inteiro",
    "DINHEIRO": "um valor em dinheiro (ex.: R$ 10,00)",
    "PERCENTUAL": "um percentual (ex.: 20%)",
    "COMPARADOR": "um comparador (>=, <=, ==, >, <)",
    "OP_SOMA": "+ ou -",
    "OP_MULT": "* ou /",
    "$END": "fim do arquivo",
}


def _pos(meta_ou_token) -> a.Pos:
    return a.Pos(meta_ou_token.line, meta_ou_token.column)


def ler_dinheiro(texto: str) -> int:
    """'R$ 49,90' -> 4990"""
    reais, centavos = texto[2:].strip().split(",")
    return int(reais) * 100 + int(centavos)


@v_args(meta=True)
class Construtor(Transformer):
    def numero(self, meta, filhos):
        return a.Numero(int(filhos[0]), _pos(meta))

    def dinheiro(self, meta, filhos):
        return a.Dinheiro(ler_dinheiro(filhos[0]), _pos(meta))

    def percentual(self, meta, filhos):
        return a.Percentual(int(filhos[0][:-1]), _pos(meta))

    def total(self, meta, filhos):
        return a.Total(_pos(meta))

    def qtd(self, meta, filhos):
        return a.Qtd(str(filhos[0]), _pos(meta))

    def binaria(self, meta, filhos):
        esq, op, dir_ = filhos
        return a.Binaria(str(op), esq, dir_, _pos(op))

    def condicao(self, meta, filhos):
        esq, op, dir_ = filhos
        return a.Condicao(esq, str(op), dir_, _pos(op))

    def acao_desconto(self, meta, filhos):
        pct, produto = filhos
        return a.AcaoDesconto(int(pct[:-1]), str(produto) if produto else None, _pos(meta))

    def acao_frete(self, meta, filhos):
        return a.AcaoFrete(ler_dinheiro(filhos[0]), _pos(meta))

    def decl_produto(self, meta, filhos):
        nome, preco = filhos
        return a.Produto(str(nome), preco, _pos(nome))

    def decl_frete(self, meta, filhos):
        return a.FretePadrao(ler_dinheiro(filhos[0]), _pos(meta))

    def decl_regra(self, meta, filhos):
        nome, condicao, acao = filhos
        return a.Regra(str(nome), condicao, acao, _pos(nome))

    def item(self, meta, filhos):
        produto, qtd = filhos
        return a.Item(str(produto), int(qtd), _pos(produto))

    def carrinho(self, meta, filhos):
        nome, *itens = filhos
        return a.Carrinho(str(nome) if nome else None, itens, _pos(meta))

    def programa(self, meta, filhos):
        prog = a.Programa()
        for no in filhos:
            match no:
                case a.Produto():
                    prog.produtos.append(no)
                case a.Regra():
                    prog.regras.append(no)
                case a.FretePadrao():
                    prog.fretes.append(no)
                case a.Carrinho():
                    prog.carrinhos.append(no)
        return prog


def _descrever_esperado(nomes) -> str:
    legiveis = []
    for nome in sorted(nomes):
        if nome in _NOMES_TERMINAIS:
            legiveis.append(_NOMES_TERMINAIS[nome])
            continue
        padrao = _LARK.get_terminal(nome).pattern
        legiveis.append(f"'{padrao.value}'" if isinstance(padrao, PatternStr) else nome)
    return ", ".join(legiveis)


def _traduzir_erro(e: Exception, texto: str) -> ErroVitrine:
    if isinstance(e, UnexpectedCharacters):
        return ErroVitrine("lexico", e.line, e.column,
                           f"caractere inesperado {texto[e.pos_in_stream]!r}")
    assert isinstance(e, UnexpectedToken)
    tok: Token = e.token
    if tok.type == "$END":
        linhas = texto.splitlines() or [""]
        linha, coluna = len(linhas), len(linhas[-1]) + 1
        encontrado = "fim do arquivo"
    else:
        linha, coluna = tok.line, tok.column
        encontrado = repr(str(tok))
    # e.expected inclui tokens de estados LALR fundidos; e.accepts é o conjunto real
    esperado = e.accepts or e.expected
    return ErroVitrine("sintatico", linha, coluna,
                       f"encontrado {encontrado}; esperado: {_descrever_esperado(esperado)}")


def analisar(texto: str) -> a.Programa:
    try:
        arvore_lark = _LARK.parse(texto)
    except (UnexpectedCharacters, UnexpectedToken) as e:
        raise _traduzir_erro(e, texto) from None
    return Construtor().transform(arvore_lark)


def arvore_sintatica(texto: str) -> str:
    try:
        return _LARK.parse(texto).pretty()
    except (UnexpectedCharacters, UnexpectedToken) as e:
        raise _traduzir_erro(e, texto) from None


def tokens(texto: str) -> list[Token]:
    try:
        return list(_LARK.lex(texto))
    except UnexpectedCharacters as e:
        raise _traduzir_erro(e, texto) from None
