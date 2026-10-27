"""Fases léxica e sintática (checkpoint de 10/11)."""
import pytest

from vitrine import arvore as a
from vitrine import parser
from vitrine.erros import ErroVitrine
from vitrine.expressoes import avaliar


def test_dinheiro_vira_centavos():
    assert parser.ler_dinheiro("R$ 49,90") == 4990
    assert parser.ler_dinheiro("R$0,05") == 5


def test_precedencia_multiplicacao_antes_da_soma():
    prog = parser.analisar("produto p = R$ 10,00 + R$ 2,00 * 3; calcular;")
    preco = prog.produtos[0].preco
    assert isinstance(preco, a.Binaria) and preco.op == "+"
    assert isinstance(preco.dir, a.Binaria) and preco.dir.op == "*"
    assert avaliar(preco) == 1600          # R$ 16,00, não R$ 36,00


def test_parenteses_mudam_a_precedencia():
    prog = parser.analisar("produto p = (R$ 10,00 + R$ 2,00) * 3; calcular;")
    assert avaliar(prog.produtos[0].preco) == 3600


def test_soma_associa_a_esquerda():
    prog = parser.analisar("produto p = R$ 10,00 - R$ 3,00 - R$ 2,00; calcular;")
    assert avaliar(prog.produtos[0].preco) == 500     # (10-3)-2, não 10-(3-2)


def test_palavra_chave_dentro_de_nome_e_nome():
    prog = parser.analisar("produto produtox = R$ 1,00; calcular;")
    assert prog.produtos[0].nome == "produtox"


def test_comentario_e_ignorado():
    prog = parser.analisar("# nada aqui\nproduto p = R$ 1,00; # fim\ncalcular;")
    assert len(prog.produtos) == 1


def test_carrinho_opcional_e_com_nome():
    assert parser.analisar("calcular;").carrinhos == []
    prog = parser.analisar("produto p = R$ 1,00; carrinho c1 { p x 2; } calcular;")
    assert prog.carrinhos[0].nome == "c1"
    assert prog.carrinhos[0].itens[0].quantidade == 2


def test_posicoes_na_ast():
    prog = parser.analisar("\n  produto p = R$ 1,00;\ncalcular;")
    assert prog.produtos[0].pos == a.Pos(2, 11)


@pytest.mark.parametrize("texto, fase, linha, coluna", [
    ("produto p = R$ 1,00\ncalcular;", "sintatico", 2, 1),     # faltou ;
    ("produto p = R$ 1,0; calcular;", "lexico", 1, 13),         # centavos com 1 dígito
    ("produto P = R$ 1,00; calcular;", "lexico", 1, 9),         # maiúscula
    ("regra r { quando total entao frete R$ 0,00; } calcular;", "sintatico", 1, 24),
    ("produto p = R$ 1,00;", "sintatico", 1, 21),               # faltou calcular
])
def test_erros_com_linha_e_coluna(texto, fase, linha, coluna):
    with pytest.raises(ErroVitrine) as info:
        parser.analisar(texto)
    e = info.value
    assert (e.fase, e.linha, e.coluna) == (fase, linha, coluna)


def test_arvore_sintatica_impressa():
    saida = parser.arvore_sintatica("produto p = R$ 1,00; calcular;")
    assert "decl_produto" in saida and "R$ 1,00" in saida
