# Vitrine

**A linguagem onde promoção vira código.** Declare produtos, regras de promoção
e carrinhos. O compilador recusa conjuntos de regras contraditórios (descontos
que passam de 100%, fretes conflitantes, regras que nunca valem) **antes** de
existir uma venda, e calcula o recibo ao centavo.

Projeto e Implementação de Compiladores — UNASP, 2026/2.
João Pedro Gaspar · Juliard Martins · Nathan Kevyn · Lucas Nogueira · Kauê Pablo

## Instalação

Requer Python 3.10+.

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate      Linux/macOS:  source .venv/bin/activate
pip install -e ".[dev]"
```

## Uso

```bash
python -m vitrine exemplos/validos/promocao_outubro.vitrine             # compila e imprime o recibo
python -m vitrine exemplos/invalidos/conflito_120.vitrine               # recusado, com linha:coluna
python -m vitrine arquivo.vitrine --tokens | --arvore | --ast | --verificar
```

```
================== recibo ==================
camiseta        3 x R$ 49,90       R$ 149,70
caneca          1 x R$ 29,90        R$ 29,90
--------------------------------------------
subtotal                           R$ 179,60
desconto 20% em camiseta           -R$ 29,94
frete (frete_gratis)                 R$ 0,00
TOTAL                              R$ 149,66
--------------------------------------------
regras aplicadas: leve3, frete_gratis
```

```
erro semantico [conflito_120.vitrine:7:23]
   descontos acumulados em 'camiseta' chegam a 120%
   quando promo_a e promo_b se aplicam juntas
```

## Testes e avaliação

```bash
pytest                       # testes unitários + ponta a ponta dos exemplos
python avaliacao/rodar.py    # avaliação da verificação semântica (opção B)
```

A CI (`.github/workflows/testes.yml`) roda os testes a cada push.

## Estrutura

```
docs/especificacao.md    especificação da linguagem
src/vitrine/             grammar.lark, parser, arvore, semantica, conflitos, expressoes, executor, cli
exemplos/validos/        3+ programas que rodam, com a saída esperada (.saida)
exemplos/invalidos/      programas que devem ser recusados
tests/                   pytest
avaliacao/               casos rotulados + script de medição
```

## Divisão de trabalho

| Integrante | Frente |
|---|---|
| João Pedro Gaspar | gramática, parser, AST |
| Juliard Martins | semântica: nomes, referências, tipos (`semantica.py`) |
| Nathan Kevyn | conflitos entre regras (`conflitos.py`); erros |
| Lucas Nogueira | executor e CLI |
| Kauê Pablo | testes, exemplos, avaliação |
