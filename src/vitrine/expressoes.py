"""Avaliação de expressões. Todos os valores são int (centavos ou unidades)."""

from __future__ import annotations

from typing import Callable

from . import arvore as a
from .erros import ErroVitrine


def dividir(numerador: int, denominador: int) -> int:
    """Divisão inteira arredondando meio para cima, afastando do zero (7 / 2 = 4)."""
    sinal = -1 if (numerador < 0) != (denominador < 0) else 1
    n, d = abs(numerador), abs(denominador)
    return sinal * ((2 * n + d) // (2 * d))


def contem_variavel(e: a.Expr) -> bool:
    match e:
        case a.Qtd() | a.Total():
            return True
        case a.Binaria(esq=esq, dir=dir_):
            return contem_variavel(esq) or contem_variavel(dir_)
        case _:
            return False


def avaliar(e: a.Expr, qtd: Callable[[str], int] | None = None,
            total: int | None = None, fase: str = "execucao") -> int:
    """Sem qtd/total, avalia como expressão constante (usado para os preços)."""
    match e:
        case a.Numero(valor=v) | a.Percentual(valor=v):
            return v
        case a.Dinheiro(centavos=c):
            return c
        case a.Total():
            assert total is not None
            return total
        case a.Qtd(produto=p):
            assert qtd is not None
            return qtd(p)
        case a.Binaria(op=op, esq=esq, dir=dir_, pos=pos):
            x = avaliar(esq, qtd, total, fase)
            y = avaliar(dir_, qtd, total, fase)
            if op == "+":
                return x + y
            if op == "-":
                return x - y
            if op == "*":
                return x * y
            if y == 0:
                raise ErroVitrine(fase, pos.linha, pos.coluna, "divisão por zero")
            return dividir(x, y)
    raise TypeError(f"nó desconhecido: {e!r}")


def formatar_dinheiro(centavos: int) -> str:
    """4990 -> 'R$ 49,90', 123456 -> 'R$ 1.234,56'"""
    sinal = "-" if centavos < 0 else ""
    reais, cents = divmod(abs(centavos), 100)
    return f"{sinal}R$ {reais:,}".replace(",", ".") + f",{cents:02d}"


def comparar(op: str, x: int, y: int) -> bool:
    return {">=": x >= y, "<=": x <= y, "==": x == y, ">": x > y, "<": x < y}[op]
