"""Nomes, referências, tipos e carrinhos (semantica.py)."""
import pytest

from conftest import compilar, recusar

PRODUTOS = "produto camiseta = R$ 49,90;\nproduto caneca = R$ 29,90;\n"


# ---------- nomes ----------

def test_produto_duplicado():
    e = recusar("produto a = R$ 1,00;\nproduto a = R$ 2,00;\ncalcular;")
    assert "já foi declarado" in e.mensagem and (e.linha, e.coluna) == (2, 9)


def test_regra_com_nome_de_produto():
    e = recusar(PRODUTOS + "regra caneca { quando total >= R$ 1,00 entao frete R$ 0,00; } calcular;")
    assert "já foi declarado (produto" in e.mensagem


def test_frete_padrao_duplicado():
    e = recusar("frete = R$ 1,00; frete = R$ 2,00; calcular;")
    assert "mais de uma vez" in e.mensagem


# ---------- referências ----------

def test_produto_nao_declarado_na_regra():
    e = recusar(PRODUTOS + "regra r { quando qtd(camisa) >= 1 entao desconto 5%; } calcular;")
    assert "'camisa' não foi declarado" in e.mensagem


def test_produto_nao_declarado_no_carrinho():
    e = recusar(PRODUTOS + "carrinho { bone x 1; } calcular;")
    assert "'bone' não foi declarado" in e.mensagem


def test_produto_usado_antes_de_declarar():
    e = recusar("regra r { quando qtd(p) >= 1 entao desconto 5%; }\nproduto p = R$ 1,00;\ncalcular;")
    assert "antes de ser declarado" in e.mensagem


def test_regra_usada_como_produto():
    e = recusar(PRODUTOS + "regra r { quando qtd(r) >= 1 entao desconto 5%; } calcular;")
    assert "não um produto" in e.mensagem


# ---------- tipos ----------

@pytest.mark.parametrize("condicao, trecho", [
    ("total >= R$ 50,00 + qtd(caneca)", "somar dinheiro com inteiro"),
    ("total >= R$ 1,00 * R$ 2,00", "multiplicar dinheiro por dinheiro"),
    ("qtd(caneca) >= 10 / R$ 1,00", "dividir por dinheiro"),
    ("total >= 3", "comparação entre dinheiro e inteiro"),
    ("total >= 10%", "percentual só pode aparecer"),
])
def test_erros_de_tipo(condicao, trecho):
    e = recusar(PRODUTOS + f"regra r {{ quando {condicao} entao frete R$ 0,00; }} calcular;")
    assert trecho in e.mensagem


def test_expressoes_bem_tipadas_sao_aceitas():
    compilar(PRODUTOS + "regra r { quando total - R$ 10,00 >= R$ 2,00 * qtd(caneca) / 2 "
                        "entao frete R$ 0,00; } calcular;")


def test_preco_nao_pode_depender_do_carrinho():
    assert "não pode usar qtd" in recusar("produto p = total; calcular;").mensagem


def test_preco_tem_que_ser_dinheiro():
    assert "deve ser dinheiro" in recusar("produto p = 3; calcular;").mensagem


def test_preco_negativo():
    assert "negativo" in recusar("produto p = R$ 1,00 - R$ 2,00; calcular;").mensagem


def test_divisao_por_zero_constante():
    e = recusar("produto p = R$ 1,00 / 0; calcular;")
    assert e.fase == "semantico" and "divisão por zero" in e.mensagem


# ---------- carrinhos ----------

def test_item_repetido_no_carrinho():
    e = recusar(PRODUTOS + "carrinho { caneca x 1; caneca x 2; } calcular;")
    assert "duas vezes" in e.mensagem


def test_mesmo_produto_em_carrinhos_diferentes_e_aceito():
    compilar(PRODUTOS + "carrinho a { caneca x 1; } carrinho b { caneca x 2; } calcular;")


def test_quantidade_zero():
    assert "zero" in recusar(PRODUTOS + "carrinho { caneca x 0; } calcular;").mensagem
