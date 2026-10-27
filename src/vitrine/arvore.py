"""AST da Vitrine. Dinheiro em centavos (int), percentual em int."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass


@dataclass(frozen=True, order=True)
class Pos:
    linha: int
    coluna: int


# ---------- expressões ----------

@dataclass
class Numero:
    valor: int
    pos: Pos


@dataclass
class Dinheiro:
    centavos: int
    pos: Pos


@dataclass
class Percentual:
    valor: int
    pos: Pos


@dataclass
class Total:
    pos: Pos


@dataclass
class Qtd:
    produto: str
    pos: Pos


@dataclass
class Binaria:
    op: str          # "+", "-", "*", "/"
    esq: "Expr"
    dir: "Expr"
    pos: Pos


Expr = Numero | Dinheiro | Percentual | Total | Qtd | Binaria


@dataclass
class Condicao:
    esq: Expr
    op: str          # ">=", "<=", "==", ">", "<"
    dir: Expr
    pos: Pos


# ---------- ações ----------

@dataclass
class AcaoDesconto:
    percentual: int
    produto: str | None   # None = todos os produtos
    pos: Pos


@dataclass
class AcaoFrete:
    centavos: int
    pos: Pos


Acao = AcaoDesconto | AcaoFrete


# ---------- declarações ----------

@dataclass
class Produto:
    nome: str
    preco: Expr
    pos: Pos


@dataclass
class Regra:
    nome: str
    condicao: Condicao
    acao: Acao
    pos: Pos


@dataclass
class FretePadrao:
    centavos: int
    pos: Pos


@dataclass
class Item:
    produto: str
    quantidade: int
    pos: Pos


@dataclass
class Carrinho:
    nome: str | None
    itens: list[Item]
    pos: Pos


@dataclass
class Programa:
    produtos: list[Produto] = field(default_factory=list)
    regras: list[Regra] = field(default_factory=list)
    fretes: list[FretePadrao] = field(default_factory=list)
    carrinhos: list[Carrinho] = field(default_factory=list)


def imprimir(no, nivel: int = 0) -> str:
    """AST indentada, para `--ast`."""
    pad = "  " * nivel
    if isinstance(no, list):
        return "\n".join(imprimir(x, nivel) for x in no)
    if not is_dataclass(no):
        return f"{pad}{no!r}"
    campos = [f for f in fields(no) if f.name != "pos"]
    simples = [f"{f.name}={getattr(no, f.name)!r}" for f in campos
               if not is_dataclass(getattr(no, f.name)) and not isinstance(getattr(no, f.name), list)]
    pos = f"  @{no.pos.linha}:{no.pos.coluna}" if hasattr(no, "pos") else ""
    linhas = [f"{pad}{type(no).__name__}({', '.join(simples)}){pos}"]
    for f in campos:
        valor = getattr(no, f.name)
        if is_dataclass(valor):
            linhas.append(f"{pad}  {f.name}:")
            linhas.append(imprimir(valor, nivel + 2))
        elif isinstance(valor, list) and valor:
            linhas.append(f"{pad}  {f.name}:")
            linhas.append(imprimir(valor, nivel + 2))
    return "\n".join(linhas)
