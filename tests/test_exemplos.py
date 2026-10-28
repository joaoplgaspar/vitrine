"""Testes de ponta a ponta sobre os arquivos de exemplos/.

- validos/X.vitrine   : a saída do CLI tem que ser idêntica a validos/X.saida
- invalidos/X.vitrine : o CLI tem que recusar (código 1) com erro posicionado

Para atualizar um .saida depois de mudar o formato do recibo de propósito:
    python -m vitrine exemplos/validos/X.vitrine > exemplos/validos/X.saida
"""
from pathlib import Path

import pytest

from vitrine.cli import main

EXEMPLOS = Path(__file__).parent.parent / "exemplos"
VALIDOS = sorted((EXEMPLOS / "validos").glob("*.vitrine"))
INVALIDOS = sorted((EXEMPLOS / "invalidos").glob("*.vitrine"))


def test_tem_pelo_menos_tres_exemplos_validos():
    assert len(VALIDOS) >= 3        # exigência da entrega de 08/12


@pytest.mark.parametrize("arquivo", VALIDOS, ids=lambda p: p.stem)
def test_exemplo_valido_gera_recibo_esperado(arquivo, capsys):
    assert main([str(arquivo)]) == 0
    esperado = arquivo.with_suffix(".saida").read_text(encoding="utf-8")
    assert capsys.readouterr().out == esperado


@pytest.mark.parametrize("arquivo", INVALIDOS, ids=lambda p: p.stem)
def test_exemplo_invalido_e_recusado_com_posicao(arquivo, capsys):
    assert main([str(arquivo)]) == 1
    erro = capsys.readouterr().err
    assert erro.startswith(f"erro semantico [{arquivo.name}:")


def test_arquivo_inexistente(capsys):
    assert main(["nao_existe.vitrine"]) == 2


def test_saida_em_arquivo(tmp_path):
    destino = tmp_path / "recibo.txt"
    assert main([str(VALIDOS[0]), "--saida", str(destino)]) == 0
    assert destino.read_text(encoding="utf-8") == VALIDOS[0].with_suffix(".saida").read_text(encoding="utf-8")
