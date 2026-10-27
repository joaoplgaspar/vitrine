"""Avaliação, opção B do enunciado: a verificação semântica funciona?

Cada arquivo em avaliacao/casos/ começa com uma linha de gabarito:
    # esperado: aceita
    # esperado: recusa <categoria>
onde <categoria> é conflito_desconto, conflito_frete ou regra_morta.

O script compila cada caso, compara com o gabarito e conta:
    detectado     — esperava recusa daquela categoria e o compilador recusou por ela
    outro motivo  — esperava recusa, mas o compilador recusou por OUTRA razão
    escape        — esperava recusa e o compilador aceitou
    falso positivo— esperava aceitar e o compilador recusou
    aceito ok     — esperava aceitar e aceitou

Uso:  python avaliacao/rodar.py          (imprime a tabela e grava resultados.md)
"""

from __future__ import annotations

import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

from vitrine import parser
from vitrine.erros import ErroVitrine
from vitrine.semantica import verificar

CASOS = Path(__file__).parent / "casos"

# Como reconhecer, pela mensagem, qual verificação recusou o programa.
ASSINATURAS = {
    "conflito_desconto": ("descontos acumulados", "passa de 100%"),
    "conflito_frete": ("fretes contraditórios",),
    "regra_morta": ("nunca é verdadeira", "nunca tem efeito"),
}


def gabarito(texto: str) -> tuple[str, str | None]:
    # [ \t]* e não \s*: \s também casa a quebra de linha e leria a linha seguinte
    m = re.match(r"#[ \t]*esperado:[ \t]*(aceita|recusa)[ \t]*(\w+)?", texto)
    if not m:
        raise ValueError("primeira linha precisa ser '# esperado: ...'")
    return m.group(1), m.group(2)


def categoria_do_erro(e: ErroVitrine) -> str:
    for cat, trechos in ASSINATURAS.items():
        if any(t in e.mensagem for t in trechos):
            return cat
    return "outra"


def classificar(arquivo: Path) -> dict:
    texto = arquivo.read_text(encoding="utf-8")
    esperado, cat_esperada = gabarito(texto)
    inicio = time.perf_counter()
    try:
        verificar(parser.analisar(texto))
        obtido, cat_obtida, msg = "aceita", None, ""
    except ErroVitrine as e:
        obtido, cat_obtida, msg = "recusa", categoria_do_erro(e), e.mensagem.splitlines()[0]
    ms = (time.perf_counter() - inicio) * 1000

    if esperado == "recusa":
        if obtido == "aceita":
            resultado = "escape"
        elif cat_obtida == cat_esperada:
            resultado = "detectado"
        else:
            resultado = "outro motivo"
    else:
        resultado = "aceito ok" if obtido == "aceita" else "falso positivo"
    return dict(caso=arquivo.stem, esperado=cat_esperada or "aceita",
                resultado=resultado, mensagem=msg, ms=ms)


def main() -> int:
    linhas = [classificar(f) for f in sorted(CASOS.glob("*.vitrine"))]
    por_categoria: dict[str, Counter] = defaultdict(Counter)
    for l in linhas:
        por_categoria[l["esperado"]][l["resultado"]] += 1

    colunas = ["detectado", "outro motivo", "escape", "falso positivo", "aceito ok"]
    out = ["# Resultados da avaliação (opção B)", "",
           f"{len(linhas)} casos em `avaliacao/casos/`.", "",
           "| categoria esperada | casos | " + " | ".join(colunas) + " |",
           "|---|---:|" + "---:|" * len(colunas)]
    for cat in sorted(por_categoria):
        c = por_categoria[cat]
        out.append(f"| {cat} | {sum(c.values())} | " + " | ".join(str(c[k]) for k in colunas) + " |")
    total = Counter(l["resultado"] for l in linhas)
    out.append(f"| **total** | **{len(linhas)}** | " + " | ".join(f"**{total[k]}**" for k in colunas) + " |")

    recusas = [l for l in linhas if l["esperado"] != "aceita"]
    controles = [l for l in linhas if l["esperado"] == "aceita"]
    if recusas:
        out.append(f"\nTaxa de detecção: {total['detectado']}/{len(recusas)} "
                   f"({100 * total['detectado'] / len(recusas):.0f}%)")
    if controles:
        out.append(f"Taxa de falso positivo: {total['falso positivo']}/{len(controles)} "
                   f"({100 * total['falso positivo'] / len(controles):.0f}%)")
    out.append(f"Tempo médio de verificação: {sum(l['ms'] for l in linhas) / len(linhas):.2f} ms")

    out += ["", "## Caso a caso", "", "| caso | esperado | resultado | mensagem |", "|---|---|---|---|"]
    for l in linhas:
        marca = "" if l["resultado"] in ("detectado", "aceito ok") else " ⚠"
        out.append(f"| {l['caso']} | {l['esperado']} | {l['resultado']}{marca} | {l['mensagem']} |")

    texto = "\n".join(out)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(texto)
    (Path(__file__).parent / "resultados.md").write_text(texto + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
