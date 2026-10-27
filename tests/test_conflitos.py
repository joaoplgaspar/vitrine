"""Conflitos entre regras: regra morta, descontos e fretes."""
import pytest

from conftest import compilar, recusar

PRODUTOS = "produto camiseta = R$ 49,90;\nproduto caneca = R$ 29,90;\n"


# ---------- regra morta / sem efeito ----------

@pytest.mark.parametrize("condicao", ["qtd(caneca) < 0", "total < R$ 0,00", "R$ 1,00 > R$ 2,00"])
def test_condicao_impossivel(condicao):
    e = recusar(PRODUTOS + f"regra r {{ quando {condicao} entao frete R$ 0,00; }} calcular;")
    assert "nunca é verdadeira" in e.mensagem


def test_desconto_que_nunca_tem_efeito():
    e = recusar(PRODUTOS + "regra r { quando qtd(caneca) < 1 entao desconto 50% em caneca; } calcular;")
    assert "nunca tem efeito" in e.mensagem


# ---------- conflito de desconto (o requisito 6) ----------

def test_conflito_120_do_dossie():
    e = recusar(PRODUTOS +
                "regra promo_a { quando qtd(camiseta) >= 2 entao desconto 60% em camiseta; }\n"
                "regra promo_b { quando total >= R$ 80,00 entao desconto 60% em camiseta; }\n"
                "calcular;")
    assert "chegam a 120%" in e.mensagem and "promo_a e promo_b" in e.mensagem
    assert e.linha == 4                    # aponta para a regra que fecha o conflito


def test_desconto_unico_acima_de_100():
    e = recusar(PRODUTOS + "regra r { quando total >= R$ 0,00 entao desconto 150% em caneca; } calcular;")
    assert "passa de 100%" in e.mensagem


def test_desconto_geral_entra_na_soma_de_cada_produto():
    e = recusar(PRODUTOS +
                "regra geral { quando total >= R$ 10,00 entao desconto 50%; }\n"
                "regra cam   { quando qtd(camiseta) >= 1 entao desconto 60% em camiseta; }\n"
                "calcular;")
    assert "'camiseta' chegam a 110%" in e.mensagem


def test_exatamente_100_e_aceito():
    compilar(PRODUTOS +
             "regra a { quando qtd(caneca) >= 1 entao desconto 60% em caneca; }\n"
             "regra b { quando qtd(caneca) >= 2 entao desconto 40% em caneca; }\n"
             "calcular;")


def test_faixas_de_quantidade_exclusivas_sao_aceitas():
    compilar(PRODUTOS +
             "regra poucas { quando qtd(caneca) <= 2 entao desconto 60% em caneca; }\n"
             "regra muitas { quando qtd(caneca) >= 3 entao desconto 70% em caneca; }\n"
             "calcular;")


def test_faixas_de_total_exclusivas_sao_aceitas():
    compilar(PRODUTOS +
             "regra a { quando total < R$ 100,00 entao desconto 60% em caneca; }\n"
             "regra b { quando total >= R$ 100,00 entao desconto 70% em caneca; }\n"
             "calcular;")


def test_acoplamento_quantidade_e_total():
    # 3 camisetas custam no mínimo R$ 149,70: não existe carrinho com as duas.
    compilar(PRODUTOS +
             "regra a { quando qtd(camiseta) >= 3 entao desconto 60% em camiseta; }\n"
             "regra b { quando total < R$ 100,00 entao desconto 60% em camiseta; }\n"
             "calcular;")


def test_condicao_nao_analisavel_e_tratada_como_sempre_possivel():
    # A análise não entende qtd(a) + qtd(b): assume o pior (pode valer com qualquer outra).
    e = recusar(PRODUTOS +
                "regra a { quando qtd(camiseta) + qtd(caneca) >= 100 entao desconto 60% em caneca; }\n"
                "regra b { quando qtd(caneca) <= 1 entao desconto 60% em caneca; }\n"
                "calcular;")
    assert "120%" in e.mensagem


def test_pior_combinacao_ignora_pares_impossiveis():
    # a+b = 90 (ok), a+c = 90 (ok), b+c seria 100 mas é impossível,
    # a+b+c seria 140 mas também. O maior conjunto viável é 90 -> aceito.
    compilar(PRODUTOS +
             "regra a { quando qtd(caneca) >= 1 entao desconto 40% em caneca; }\n"
             "regra b { quando qtd(caneca) >= 5 entao desconto 50% em caneca; }\n"
             "regra c { quando qtd(caneca) <= 3 entao desconto 50% em caneca; }\n"
             "calcular;")


def test_pior_combinacao_com_tres_regras():
    e = recusar(PRODUTOS +
                "regra a { quando qtd(caneca) >= 1 entao desconto 40% em caneca; }\n"
                "regra b { quando qtd(caneca) >= 2 entao desconto 30% em caneca; }\n"
                "regra c { quando total >= R$ 50,00 entao desconto 31% em caneca; }\n"
                "calcular;")
    assert "101%" in e.mensagem and "a, b e c" in e.mensagem


# ---------- conflito de frete ----------

def test_fretes_diferentes_que_podem_valer_juntos():
    e = recusar(PRODUTOS +
                "regra f1 { quando total >= R$ 100,00 entao frete R$ 0,00; }\n"
                "regra f2 { quando qtd(caneca) >= 2 entao frete R$ 9,90; }\n"
                "calcular;")
    assert "fretes contraditórios" in e.mensagem


def test_fretes_em_faixas_exclusivas_sao_aceitos():
    compilar(PRODUTOS +
             "regra f1 { quando total >= R$ 100,00 entao frete R$ 0,00; }\n"
             "regra f2 { quando total < R$ 30,00 entao frete R$ 14,90; }\n"
             "calcular;")


def test_fretes_iguais_nao_conflitam():
    compilar(PRODUTOS +
             "regra f1 { quando total >= R$ 100,00 entao frete R$ 0,00; }\n"
             "regra f2 { quando qtd(caneca) >= 2 entao frete R$ 0,00; }\n"
             "calcular;")
