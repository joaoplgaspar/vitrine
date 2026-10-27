"""Análise semântica: nomes, referências, tipos e carrinhos.
Os conflitos entre regras ficam em conflitos.py."""

from __future__ import annotations

from dataclasses import dataclass

from . import arvore as a
from .conflitos import AnaliseConflitos, Restricao
from .erros import erro_semantico
from .expressoes import avaliar, contem_variavel, formatar_dinheiro


@dataclass
class ProgramaVerificado:
    programa: a.Programa
    precos: dict[str, int]
    frete_padrao: int
    restricoes: dict[str, Restricao]


class Verificador:
    def __init__(self, programa: a.Programa):
        self.p = programa
        self.nomes: dict[str, tuple[str, a.Pos]] = {}
        self.precos: dict[str, int] = {}

    def verificar(self) -> ProgramaVerificado:
        self._nomes()
        self._precos()
        for regra in self.p.regras:
            self._regra(regra)
        self._carrinhos()
        restricoes = AnaliseConflitos(self.p, self.precos).verificar()
        frete = self.p.fretes[0].centavos if self.p.fretes else 0
        return ProgramaVerificado(self.p, self.precos, frete, restricoes)

    def _nomes(self):
        # produtos, regras e carrinhos dividem o mesmo escopo global
        decls = [(x.pos, "produto", x.nome) for x in self.p.produtos]
        decls += [(x.pos, "regra", x.nome) for x in self.p.regras]
        decls += [(x.pos, "carrinho", x.nome) for x in self.p.carrinhos if x.nome]
        for pos, tipo, nome in sorted(decls):
            if nome in self.nomes:
                tipo_ant, pos_ant = self.nomes[nome]
                raise erro_semantico(
                    pos, f"'{nome}' já foi declarado ({tipo_ant}, linha {pos_ant.linha})")
            self.nomes[nome] = (tipo, pos)
        if len(self.p.fretes) > 1:
            raise erro_semantico(
                self.p.fretes[1].pos,
                f"frete padrão declarado mais de uma vez (primeiro na linha {self.p.fretes[0].pos.linha})")

    def _produto(self, nome: str, pos: a.Pos):
        if nome not in self.nomes:
            raise erro_semantico(pos, f"produto '{nome}' não foi declarado")
        tipo, pos_decl = self.nomes[nome]
        if tipo != "produto":
            raise erro_semantico(pos, f"'{nome}' é um(a) {tipo}, não um produto")
        if pos < pos_decl:
            raise erro_semantico(
                pos, f"produto '{nome}' usado antes de ser declarado (linha {pos_decl.linha})")

    def _tipo(self, e: a.Expr) -> str:
        match e:
            case a.Numero():
                return "inteiro"
            case a.Dinheiro() | a.Total():
                return "dinheiro"
            case a.Percentual():
                raise erro_semantico(e.pos, "percentual só pode aparecer em 'desconto'")
            case a.Qtd():
                self._produto(e.produto, e.pos)
                return "inteiro"
            case a.Binaria(op=op, esq=esq, dir=dir_, pos=pos):
                te, td = self._tipo(esq), self._tipo(dir_)
                if op in "+-":
                    if te != td:
                        verbo = "somar" if op == "+" else "subtrair"
                        raise erro_semantico(pos, f"não dá para {verbo} {te} com {td}")
                    return te
                if op == "*":
                    if te == td == "dinheiro":
                        raise erro_semantico(pos, "não dá para multiplicar dinheiro por dinheiro")
                    return "dinheiro" if "dinheiro" in (te, td) else "inteiro"
                if td == "dinheiro":
                    raise erro_semantico(pos, "não dá para dividir por dinheiro")
                return te
        raise TypeError(f"nó desconhecido: {e!r}")

    def _precos(self):
        for prod in self.p.produtos:
            if contem_variavel(prod.preco):
                raise erro_semantico(
                    prod.preco.pos, f"preço de '{prod.nome}' não pode usar qtd() nem total")
            tipo = self._tipo(prod.preco)
            if tipo != "dinheiro":
                raise erro_semantico(
                    prod.preco.pos, f"preço de '{prod.nome}' deve ser dinheiro, não {tipo}")
            valor = avaliar(prod.preco, fase="semantico")
            if valor < 0:
                raise erro_semantico(
                    prod.preco.pos, f"preço de '{prod.nome}' ficou negativo ({formatar_dinheiro(valor)})")
            self.precos[prod.nome] = valor

    def _regra(self, regra: a.Regra):
        c = regra.condicao
        te, td = self._tipo(c.esq), self._tipo(c.dir)
        if te != td:
            raise erro_semantico(c.pos, f"comparação entre {te} e {td}")
        acao = regra.acao
        if isinstance(acao, a.AcaoDesconto):
            if acao.produto is not None:
                self._produto(acao.produto, acao.pos)
            if acao.percentual == 0:
                raise erro_semantico(acao.pos, "desconto de 0% não tem efeito")

    def _carrinhos(self):
        for carrinho in self.p.carrinhos:
            vistos: dict[str, a.Pos] = {}
            for item in carrinho.itens:
                self._produto(item.produto, item.pos)
                if item.produto in vistos:
                    raise erro_semantico(
                        item.pos, f"'{item.produto}' aparece duas vezes no mesmo carrinho "
                                  f"(linha {vistos[item.produto].linha})")
                if item.quantidade == 0:
                    raise erro_semantico(item.pos, f"quantidade de '{item.produto}' é zero")
                vistos[item.produto] = item.pos


def verificar(programa: a.Programa) -> ProgramaVerificado:
    return Verificador(programa).verificar()
