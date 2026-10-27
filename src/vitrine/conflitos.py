"""Análise de conflitos entre regras: regra morta, descontos acima de 100% e
fretes contraditórios."""

from __future__ import annotations

from dataclasses import dataclass

from . import arvore as a
from .erros import erro_semantico
from .expressoes import avaliar, comparar, contem_variavel, formatar_dinheiro


@dataclass(frozen=True)
class Faixa:
    """Intervalo fechado de inteiros. maximo None = sem limite."""
    minimo: int
    maximo: int | None

    def cruzar(self, outra: Faixa) -> Faixa | None:
        lo = max(self.minimo, outra.minimo)
        if self.maximo is None:
            hi = outra.maximo
        elif outra.maximo is None:
            hi = self.maximo
        else:
            hi = min(self.maximo, outra.maximo)
        if hi is not None and lo > hi:
            return None
        return Faixa(lo, hi)


TUDO = Faixa(0, None)

# chave "total" ou "qtd:<produto>" -> faixa; {} = nenhuma restrição conhecida
Restricao = dict[str, Faixa]

_INVERTE = {">=": "<=", "<=": ">=", ">": "<", "<": ">", "==": "=="}


def _faixa(op: str, c: int) -> Faixa | None:
    """Inteiros x >= 0 tais que `x op c`."""
    match op:
        case ">=":
            f = Faixa(c, None)
        case ">":
            f = Faixa(c + 1, None)
        case "<=":
            f = Faixa(0, c) if c >= 0 else None
        case "<":
            f = Faixa(0, c - 1) if c >= 1 else None
        case _:
            f = Faixa(c, c) if c >= 0 else None
    return f.cruzar(TUDO) if f else None


class AnaliseConflitos:
    def __init__(self, programa: a.Programa, precos: dict[str, int]):
        self.p = programa
        self.precos = precos
        self.restricoes: dict[str, Restricao] = {}

    def verificar(self) -> dict[str, Restricao]:
        self._regras_mortas()
        self._conflito_desconto()
        self._conflito_frete()
        return self.restricoes

    def _restricao(self, c: a.Condicao) -> Restricao | None:
        """None = a condição nunca é verdadeira."""
        esq_var, dir_var = contem_variavel(c.esq), contem_variavel(c.dir)
        if not esq_var and not dir_var:
            x, y = avaliar(c.esq, fase="semantico"), avaliar(c.dir, fase="semantico")
            return {} if comparar(c.op, x, y) else None
        if isinstance(c.esq, (a.Qtd, a.Total)) and not dir_var:
            var, op, const = c.esq, c.op, c.dir
        elif isinstance(c.dir, (a.Qtd, a.Total)) and not esq_var:
            var, op, const = c.dir, _INVERTE[c.op], c.esq
        else:
            # forma não analisável (ex.: qtd(a) + qtd(b) >= 3): assume que pode valer sempre
            return {}
        faixa = _faixa(op, avaliar(const, fase="semantico"))
        if faixa is None:
            return None
        chave = "total" if isinstance(var, a.Total) else f"qtd:{var.produto}"
        return {chave: faixa}

    def _viavel(self, restricoes: list[Restricao]) -> bool:
        """Existe algum carrinho que satisfaz todas as restrições?
        Conservador: pode responder sim quando o exato seria não."""
        caixa: dict[str, Faixa] = {}
        for r in restricoes:
            for chave, faixa in r.items():
                cruzada = caixa.get(chave, TUDO).cruzar(faixa)
                if cruzada is None:
                    return False
                caixa[chave] = cruzada

        # o total é limitado pelas quantidades: total = soma de qtd(p) * preço(p)
        minimo, maximo = 0, 0
        for produto, preco in self.precos.items():
            f = caixa.get(f"qtd:{produto}", TUDO)
            minimo += f.minimo * preco
            if preco and maximo is not None:
                maximo = None if f.maximo is None else maximo + f.maximo * preco
        return caixa.get("total", TUDO).cruzar(Faixa(minimo, maximo)) is not None

    def _regras_mortas(self):
        for regra in self.p.regras:
            r = self._restricao(regra.condicao)
            if r is None or not self._viavel([r]):
                raise erro_semantico(
                    regra.condicao.pos, f"a condição da regra '{regra.nome}' nunca é verdadeira")
            acao = regra.acao
            if isinstance(acao, a.AcaoDesconto) and acao.produto:
                faixa = r.get(f"qtd:{acao.produto}")
                if faixa is not None and faixa.maximo == 0:
                    raise erro_semantico(
                        acao.pos, f"a regra '{regra.nome}' nunca tem efeito: o desconto em "
                                  f"'{acao.produto}' só vale quando não há '{acao.produto}' no carrinho")
            self.restricoes[regra.nome] = r

    def _pior_combinacao(self, regras: list[a.Regra]) -> tuple[int, list[a.Regra]]:
        """Maior soma de descontos entre regras que podem valer juntas."""
        regras = sorted(regras, key=lambda r: -r.acao.percentual)
        melhor: tuple[int, list[a.Regra]] = (0, [])

        def buscar(i: int, escolhidas: list[a.Regra], soma: int, restante: int):
            nonlocal melhor
            if soma > melhor[0]:
                melhor = (soma, list(escolhidas))
            if i == len(regras) or soma + restante <= melhor[0]:
                return
            regra = regras[i]
            pct = regra.acao.percentual
            escolhidas.append(regra)
            # se já é inviável, nenhum conjunto maior será: corta o ramo
            if self._viavel([self.restricoes[x.nome] for x in escolhidas]):
                buscar(i + 1, escolhidas, soma + pct, restante - pct)
            escolhidas.pop()
            buscar(i + 1, escolhidas, soma, restante - pct)

        buscar(0, [], 0, sum(r.acao.percentual for r in regras))
        return melhor

    def _conflito_desconto(self):
        descontos = [r for r in self.p.regras if isinstance(r.acao, a.AcaoDesconto)]
        for produto in self.p.produtos:
            alvo = [r for r in descontos if r.acao.produto in (None, produto.nome)]
            soma, conjunto = self._pior_combinacao(alvo)
            if soma <= 100:
                continue
            conjunto.sort(key=lambda r: r.pos)
            ultima = conjunto[-1]
            if len(conjunto) == 1:
                raise erro_semantico(
                    ultima.acao.pos, f"desconto de {soma}% em '{produto.nome}' passa de 100%")
            nomes = ", ".join(r.nome for r in conjunto[:-1]) + f" e {ultima.nome}"
            raise erro_semantico(
                ultima.acao.pos,
                f"descontos acumulados em '{produto.nome}' chegam a {soma}%\n"
                f"   quando {nomes} se aplicam juntas")

    def _conflito_frete(self):
        fretes = [r for r in self.p.regras if isinstance(r.acao, a.AcaoFrete)]
        for j, rj in enumerate(fretes):
            for ri in fretes[:j]:
                if ri.acao.centavos == rj.acao.centavos:
                    continue
                if self._viavel([self.restricoes[ri.nome], self.restricoes[rj.nome]]):
                    raise erro_semantico(
                        rj.acao.pos,
                        f"fretes contraditórios: '{ri.nome}' define {formatar_dinheiro(ri.acao.centavos)} "
                        f"e '{rj.nome}' define {formatar_dinheiro(rj.acao.centavos)}\n"
                        f"   e as duas podem se aplicar juntas")
