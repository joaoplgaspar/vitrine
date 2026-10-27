import pytest

from vitrine import parser
from vitrine.erros import ErroVitrine
from vitrine.semantica import verificar


def compilar(texto: str):
    """Léxico + sintático + semântica. Devolve o ProgramaVerificado."""
    return verificar(parser.analisar(texto))


def recusar(texto: str) -> ErroVitrine:
    """Garante que o programa é recusado e devolve o erro para inspeção."""
    with pytest.raises(ErroVitrine) as info:
        compilar(texto)
    return info.value
