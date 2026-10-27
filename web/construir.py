"""Monta o site estático em _site/ (usado localmente e pela Action do Pages).

    python web/construir.py            # só monta
    python web/construir.py --servir   # monta e abre em http://localhost:8000
"""

import json
import shutil
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "_site"


def construir():
    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    DESTINO.mkdir()
    for nome in ("index.html", "estilo.css", "app.js", "ponte.py"):
        shutil.copy(RAIZ / "web" / nome, DESTINO / nome)

    pacote = RAIZ / "src" / "vitrine"
    (DESTINO / "vitrine").mkdir()
    arquivos = sorted(p.name for p in pacote.iterdir() if p.suffix in (".py", ".lark"))
    for nome in arquivos:
        shutil.copy(pacote / nome, DESTINO / "vitrine" / nome)

    exemplos = []
    for grupo in ("validos", "invalidos"):
        (DESTINO / "exemplos" / grupo).mkdir(parents=True)
        for p in sorted((RAIZ / "exemplos" / grupo).glob("*.vitrine")):
            shutil.copy(p, DESTINO / "exemplos" / grupo / p.name)
            exemplos.append({"grupo": grupo, "nome": p.stem, "caminho": f"exemplos/{grupo}/{p.name}"})

    manifesto = {"pacote": arquivos, "exemplos": exemplos}
    (DESTINO / "manifest.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    print(f"site montado em {DESTINO}")


def servir(porta: int = 8000):
    handler = partial(SimpleHTTPRequestHandler, directory=str(DESTINO))
    print(f"abra http://localhost:{porta}  (Ctrl+C para parar)")
    ThreadingHTTPServer(("localhost", porta), handler).serve_forever()


if __name__ == "__main__":
    construir()
    if "--servir" in sys.argv:
        servir()
