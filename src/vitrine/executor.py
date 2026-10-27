"""Execução: calcula o recibo de cada carrinho (especificação, seção 7)."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import arvore as a
from .expressoes import avaliar, comparar, dividir, formatar_dinheiro
from .semantica import ProgramaVerificado


@dataclass
class Linha:
    produto: str
    quantidade: int
    preco: int
    subtotal: int
    percentual: int = 0
    desconto: int = 0
    regras: list[str] = field(default_factory=list)


@dataclass
class Recibo:
    carrinho: str | None
    linhas: list[Linha]
    subtotal: int
    descontos: int
    frete: int
    regra_frete: str | None
    total: int
    regras_aplicadas: list[str]


def calcular_carrinho(vp: ProgramaVerificado, carrinho: a.Carrinho) -> Recibo:
    quantidades = {item.produto: item.quantidade for item in carrinho.itens}
    linhas = [Linha(p, q, vp.precos[p], q * vp.precos[p]) for p, q in quantidades.items()]
    subtotal = sum(l.subtotal for l in linhas)

    def qtd(produto: str) -> int:
        return quantidades.get(produto, 0)

    # todas as condições usam o subtotal, então a ordem das regras não importa
    aplicadas = []
    for regra in vp.programa.regras:
        c = regra.condicao
        x = avaliar(c.esq, qtd, subtotal)
        y = avaliar(c.dir, qtd, subtotal)
        if comparar(c.op, x, y):
            aplicadas.append(regra)

    for linha in linhas:
        for regra in aplicadas:
            acao = regra.acao
            if isinstance(acao, a.AcaoDesconto) and acao.produto in (None, linha.produto):
                linha.percentual += acao.percentual
                linha.regras.append(regra.nome)
        assert linha.percentual <= 100
        linha.desconto = dividir(linha.subtotal * linha.percentual, 100)

    fretes = [r for r in aplicadas if isinstance(r.acao, a.AcaoFrete)]
    assert len({r.acao.centavos for r in fretes}) <= 1
    frete = fretes[0].acao.centavos if fretes else vp.frete_padrao
    regra_frete = ", ".join(r.nome for r in fretes) or None

    # condição verdadeira não basta: desconto em produto ausente não tem efeito
    com_efeito = {nome for l in linhas for nome in l.regras} | {r.nome for r in fretes}
    descontos = sum(l.desconto for l in linhas)
    return Recibo(carrinho.nome, linhas, subtotal, descontos, frete, regra_frete,
                  subtotal - descontos + frete,
                  [r.nome for r in aplicadas if r.nome in com_efeito])


def executar(vp: ProgramaVerificado) -> list[Recibo]:
    return [calcular_carrinho(vp, c) for c in vp.programa.carrinhos]


def formatar_recibo(r: Recibo) -> str:
    largura = 44
    def linha(esq: str, valor: int) -> str:
        dinheiro = formatar_dinheiro(valor)
        return f"{esq}{dinheiro:>{largura - len(esq)}}"

    titulo = f" recibo: {r.carrinho} " if r.carrinho else " recibo "
    out = [titulo.center(largura, "=")]
    for l in r.linhas:
        out.append(linha(f"{l.produto:<14}{l.quantidade:>3} x {formatar_dinheiro(l.preco):<12}", l.subtotal))
    out.append("-" * largura)
    out.append(linha("subtotal", r.subtotal))
    for l in r.linhas:
        if l.desconto:
            out.append(linha(f"desconto {l.percentual}% em {l.produto}", -l.desconto))
    out.append(linha(f"frete ({r.regra_frete})" if r.regra_frete else "frete", r.frete))
    out.append(linha("TOTAL", r.total))
    out.append("-" * largura)
    out.append("regras aplicadas: " + (", ".join(r.regras_aplicadas) or "nenhuma"))
    return "\n".join(out)
