"""Ponte entre a página e o compilador: roda no Pyodide, devolve JSON."""

import json

from vitrine import arvore, parser
from vitrine.cli import compilar_e_rodar
from vitrine.erros import ErroVitrine


def rodar(texto: str, modo: str) -> str:
    try:
        if modo == "tokens":
            saida = "\n".join(f"{t.line:>3}:{t.column:<3} {t.type:<12} {t.value}"
                              for t in parser.tokens(texto))
        elif modo == "arvore":
            saida = parser.arvore_sintatica(texto)
        elif modo == "ast":
            saida = arvore.imprimir(parser.analisar(texto))
        else:
            saida = compilar_e_rodar(texto)
        return json.dumps({"ok": True, "saida": saida})
    except ErroVitrine as e:
        return json.dumps({"ok": False, "fase": e.fase, "linha": e.linha, "coluna": e.coluna,
                           "saida": e.formatar("programa.vitrine")})
    except Exception as e:  # bug do compilador, não do programa
        return json.dumps({"ok": False, "fase": "interno", "linha": 0, "coluna": 0,
                           "saida": f"erro interno do compilador: {e!r}"})
