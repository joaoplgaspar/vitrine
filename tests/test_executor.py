"""Execução: cálculo do recibo e arredondamento."""
import pytest

from conftest import compilar
from vitrine.executor import executar
from vitrine.expressoes import dividir, formatar_dinheiro

CANONICO = """
produto camiseta = R$ 49,90;
produto caneca = R$ 29,90;
frete = R$ 15,00;
regra leve3 { quando qtd(camiseta) >= 3 entao desconto 20% em camiseta; }
regra frete_gratis { quando total >= R$ 150,00 entao frete R$ 0,00; }
carrinho { camiseta x 3; caneca x 1; }
calcular;
"""


@pytest.mark.parametrize("n, d, esperado", [
    (7, 2, 4), (5, 2, 3), (4, 3, 1), (2994, 1, 2994),
    (7485, 10, 749),      # 748,5 centavos -> 749 (meio para cima)
    (-7, 2, -4),          # afasta do zero também no negativo
])
def test_dividir_arredonda_meio_para_cima(n, d, esperado):
    assert dividir(n, d) == esperado


@pytest.mark.parametrize("centavos, texto", [
    (4990, "R$ 49,90"), (5, "R$ 0,05"), (123456, "R$ 1.234,56"), (-2994, "-R$ 29,94"),
])
def test_formatar_dinheiro(centavos, texto):
    assert formatar_dinheiro(centavos) == texto


def test_exemplo_canonico_bate_ao_centavo():
    [r] = executar(compilar(CANONICO))
    assert r.subtotal == 17960
    assert r.descontos == 2994
    assert r.frete == 0              # total ANTES do desconto (179,60) >= 150
    assert r.total == 14966
    assert r.regras_aplicadas == ["leve3", "frete_gratis"]


def test_ordem_das_regras_nao_muda_o_resultado():
    invertido = CANONICO.replace(
        "regra leve3 { quando qtd(camiseta) >= 3 entao desconto 20% em camiseta; }\n", ""
    ).replace("carrinho", "regra leve3 { quando qtd(camiseta) >= 3 entao desconto 20% em camiseta; }\ncarrinho")
    [a] = executar(compilar(CANONICO))
    [b] = executar(compilar(invertido))
    assert a.total == b.total and a.frete == b.frete


def test_frete_padrao_quando_nenhuma_regra_de_frete_vale():
    [r] = executar(compilar(CANONICO.replace("camiseta x 3; caneca x 1;", "caneca x 1;")))
    assert r.frete == 1500 and r.total == 2990 + 1500


def test_sem_frete_padrao_o_frete_e_zero():
    [r] = executar(compilar("produto p = R$ 10,00; carrinho { p x 1; } calcular;"))
    assert r.frete == 0 and r.total == 1000


def test_descontos_nao_se_compoem():
    # 30% + 20% sobre o preço original = 50%, não 1 - 0,7*0,8 = 44%.
    [r] = executar(compilar(
        "produto p = R$ 100,00;"
        "regra a { quando qtd(p) >= 1 entao desconto 30% em p; }"
        "regra b { quando qtd(p) >= 1 entao desconto 20%; }"
        "carrinho { p x 1; } calcular;"))
    assert r.descontos == 5000


def test_regra_sem_efeito_nao_aparece_no_recibo():
    [r] = executar(compilar(
        "produto p = R$ 10,00; produto q = R$ 5,00;"
        "regra rp { quando total >= R$ 0,00 entao desconto 10% em p; }"
        "carrinho { q x 1; } calcular;"))
    assert r.regras_aplicadas == []


def test_divisao_por_zero_em_execucao():
    from vitrine.erros import ErroVitrine
    vp = compilar("produto p = R$ 10,00;"
                  "regra r { quando total / qtd(p) >= R$ 1,00 entao frete R$ 0,00; }"
                  "carrinho { } calcular;")
    with pytest.raises(ErroVitrine) as info:
        executar(vp)
    assert info.value.fase == "execucao"
