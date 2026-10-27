"""python -m vitrine arquivo.vitrine [--tokens | --arvore | --ast | --verificar]

Saída: 0 = ok, 1 = programa recusado, 2 = erro de uso.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import arvore, parser
from .erros import ErroVitrine
from .executor import executar, formatar_recibo
from .semantica import verificar


def compilar_e_rodar(texto: str) -> str:
    vp = verificar(parser.analisar(texto))
    recibos = executar(vp)
    if not recibos:
        return "regras válidas (nenhum carrinho para calcular)"
    return "\n\n".join(formatar_recibo(r) for r in recibos)


def main(argv: list[str] | None = None) -> int:
    # o console do Windows não usa UTF-8 por padrão
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(prog="vitrine", description="Compilador da linguagem Vitrine")
    ap.add_argument("arquivo")
    modo = ap.add_mutually_exclusive_group()
    for opcao in ("--tokens", "--arvore", "--ast", "--verificar"):
        modo.add_argument(opcao, action="store_true")
    args = ap.parse_args(argv)

    caminho = Path(args.arquivo)
    try:
        texto = caminho.read_text(encoding="utf-8")
    except OSError as e:
        print(f"não consegui ler {caminho}: {e.strerror}", file=sys.stderr)
        return 2

    try:
        if args.tokens:
            for t in parser.tokens(texto):
                print(f"{t.line:>3}:{t.column:<3} {t.type:<12} {t.value}")
        elif args.arvore:
            print(parser.arvore_sintatica(texto))
        elif args.ast:
            print(arvore.imprimir(parser.analisar(texto)))
        elif args.verificar:
            verificar(parser.analisar(texto))
            print("ok: programa aceito")
        else:
            print(compilar_e_rodar(texto))
    except ErroVitrine as e:
        print(e.formatar(caminho.name), file=sys.stderr)
        return 1
    return 0
