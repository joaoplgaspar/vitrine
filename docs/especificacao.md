# Vitrine — Especificação da linguagem

> Versão 2 (27/10). Substitui a versão de 20/10. As mudanças estão listadas na
> seção 9 e cada uma tem um motivo.

## 1. Propósito e público

Vitrine é uma linguagem declarativa para descrever **catálogos, carrinhos e
regras de promoção** de lojas virtuais. O público é quem configura promoções
(lojista, time de marketing, desenvolvedor de e-commerce), não quem programa
sistemas.

A tese: **promoção é código, e conflito entre promoções é erro de compilação.**
Como a linguagem de condições é fechada (só quantidades, total e constantes),
o compilador consegue analisar o conjunto inteiro de regras e recusar
combinações sem sentido **para qualquer carrinho possível**, antes de existir
uma venda. Numa biblioteca Python, a condição de uma regra seria uma função
arbitrária, e uma função arbitrária não pode ser analisada assim. É essa
restrição que torna a verificação possível.

## 2. Programa de exemplo, comentado

```
# promocao_outubro.vitrine                    (1) comentário: vai até o fim da linha
produto camiseta = R$ 49,90;                  (2) declara um produto e seu preço
produto caneca   = R$ 29,90;                  (3) outro produto
frete = R$ 15,00;                             (4) frete padrão (se omitido, R$ 0,00)

regra leve3 {                                 (5) declara a regra "leve3"
    quando qtd(camiseta) >= 3                 (6) condição: 3 ou mais camisetas
    entao desconto 20% em camiseta;           (7) ação: 20% nas camisetas
}

regra frete_gratis {                          (8)
    quando total >= R$ 150,00                 (9) total = subtotal ANTES dos descontos
    entao frete R$ 0,00;                      (10) ação: troca o frete
}

carrinho { camiseta x 3; caneca x 1; }        (11) um carrinho: produto x quantidade
calcular;                                     (12) fim: calcula e imprime os recibos
```

Saída (`python -m vitrine exemplos/validos/promocao_outubro.vitrine`):

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

## 3. Gramática (EBNF)

```ebnf
programa     = { declaracao } , { carrinho } , "calcular" , ";" ;
declaracao   = decl_produto | decl_regra | decl_frete ;
decl_produto = "produto" , IDENT , "=" , expressao , ";" ;
decl_frete   = "frete" , "=" , DINHEIRO , ";" ;
decl_regra   = "regra" , IDENT , "{" , "quando" , condicao ,
               "entao" , acao , ";" , "}" ;
condicao     = expressao , COMPARADOR , expressao ;
expressao    = termo , { ( "+" | "-" ) , termo } ;
termo        = fator , { ( "*" | "/" ) , fator } ;
fator        = NUMERO | DINHEIRO | PERCENTUAL | "total"
             | "qtd" , "(" , IDENT , ")" | "(" , expressao , ")" ;
acao         = "desconto" , PERCENTUAL , [ "em" , IDENT ]
             | "frete" , DINHEIRO ;
carrinho     = "carrinho" , [ IDENT ] , "{" , { item } , "}" ;
item         = IDENT , "x" , NUMERO , ";" ;
```

**Precedência**, codificada na cadeia `expressao > termo > fator`: parênteses e
`qtd()` ligam mais forte, depois `*` e `/`, depois `+` e `-`, todos associando à
esquerda. Comparadores só existem em condições (não há `a >= b >= c`). Assim
`R$ 10,00 + R$ 2,00 * 3` vale R$ 16,00, e `R$ 10,00 - R$ 3,00 - R$ 2,00` vale R$ 5,00.

A implementação está em `src/vitrine/grammar.lark` (mesma gramática, sintaxe do Lark).

## 4. Tokens

| Categoria | Padrão | Exemplos |
|---|---|---|
| Palavras-chave | `produto regra quando entao carrinho calcular desconto frete em qtd total x` | |
| Identificador | `[a-z_][a-z0-9_]*` (que não seja palavra-chave) | `camiseta`, `leve3` |
| Dinheiro | `R$`, espaço opcional, `\d+,\d\d` | `R$ 49,90`, `R$0,05` |
| Percentual | `\d+%` | `20%` |
| Número | `\d+` | `3` |
| Comparador | `>= <= == > <` | |
| Operadores | `+ - * /` | |
| Símbolos | `= ; { } ( )` | |
| Comentário | `#` até o fim da linha (ignorado) | |

`python -m vitrine arquivo --tokens` mostra a saída da fase léxica.

## 5. Tipos

Três tipos: **inteiro**, **dinheiro** (guardado em centavos inteiros) e
**percentual** (só aceito como argumento de `desconto`).

| Operação | Resultado |
|---|---|
| dinheiro `+` / `-` dinheiro | dinheiro |
| dinheiro `*` inteiro, inteiro `*` dinheiro | dinheiro |
| dinheiro `/` inteiro | dinheiro |
| inteiro `op` inteiro | inteiro |
| dinheiro `+`/`-` inteiro | **erro** |
| dinheiro `*` dinheiro, qualquer `/` dinheiro | **erro** |
| percentual em qualquer expressão | **erro** |
| comparação entre tipos diferentes | **erro** |

`qtd(p)` é inteiro; `total` é dinheiro. Toda divisão arredonda **meio para
cima** (afastando do zero): `7 / 2 = 4`. Não existe ponto flutuante.

**Escopo.** Há um único escopo global: produtos, regras e carrinhos nomeados
compartilham o mesmo espaço de nomes, e um nome não pode ser declarado duas
vezes. Um produto precisa ser declarado **antes** de ser usado. Dentro de um
carrinho, cada produto aparece no máximo uma vez; o mesmo produto pode estar em
carrinhos diferentes.

## 6. Verificação semântica

O compilador recusa programas sintaticamente corretos, sempre com
`erro semantico [arquivo:linha:coluna]`. Roda na ordem abaixo e para no
primeiro erro.

1. **Nomes**: nome duplicado; frete padrão declarado mais de uma vez.
2. **Referências**: produto não declarado, declarado depois do uso, ou nome que é de uma regra.
3. **Tipos**: tabela da seção 5. O preço de um produto é uma expressão
   **constante** (sem `qtd`/`total`), do tipo dinheiro e não negativa.
4. **Carrinhos**: produto repetido no mesmo carrinho; quantidade zero.
5. **Regra morta**: condição que nunca é verdadeira (`total < R$ 0,00`), ou
   desconto em `p` que só vale quando não há `p` no carrinho (`qtd(p) < 1`).
6. **Conflito de desconto** *(verificação central)*: para cada produto, a soma
   dos percentuais das regras que **podem se aplicar juntas** não pode passar de 100%.
7. **Conflito de frete**: duas regras que podem se aplicar juntas não podem
   definir fretes diferentes.

### "Podem se aplicar juntas"

Cada condição da forma `qtd(p) op constante` ou `total op constante` (em
qualquer ordem) vira uma **faixa** de valores possíveis. Um conjunto de regras é
**viável** se as faixas de cada variável se cruzam **e** se a faixa do total é
compatível com as quantidades: `total = Σ qtd(p) × preço(p)`. Por exemplo, com
`qtd(camiseta) >= 3`, o total é no mínimo R$ 149,70.

Condições de outras formas (`qtd(a) + qtd(b) >= 3`, `qtd(a) * 2 >= 10`) são
tratadas como **sempre possíveis**. A análise é conservadora: nunca aceita um
conflito real, mas pode recusar um programa correto (seção 8).

### Programa aceito × programa recusado

Aceito: as faixas são exclusivas (60% + 70% nunca valem juntas).
```
produto caneca = R$ 29,90;
regra poucas { quando qtd(caneca) <= 2 entao desconto 60% em caneca; }
regra muitas { quando qtd(caneca) >= 3 entao desconto 70% em caneca; }
calcular;
```

Recusado (`exemplos/invalidos/conflito_120.vitrine`):
```
produto camiseta = R$ 49,90;
regra promo_a { quando qtd(camiseta) >= 2
                entao desconto 60% em camiseta; }
regra promo_b { quando total >= R$ 80,00
                entao desconto 60% em camiseta; }
```
```
erro semantico [conflito_120.vitrine:7:23]
   descontos acumulados em 'camiseta' chegam a 120%
   quando promo_a e promo_b se aplicam juntas
```

## 7. Execução

Para cada carrinho, em ordem:

1. `subtotal = Σ quantidade × preço`.
2. Cada condição é avaliada com `total = subtotal`, **antes** de qualquer
   desconto. Por isso a ordem das regras não muda o resultado.
3. **Descontos não se compõem**: os percentuais que atingem um produto são
   somados e aplicados uma vez sobre `preço × quantidade`, arredondando para o
   centavo (meio para cima). `desconto X%` sem `em` atinge todos os produtos.
4. Frete = o valor da regra de frete que se aplicou, ou o frete padrão.
5. `TOTAL = subtotal − descontos + frete`. O recibo lista as regras que tiveram efeito.

Sem carrinhos, `calcular;` só verifica as regras.

## 8. Limitações conhecidas

| Limitação | Causa |
|---|---|
| Falso positivo com condições fora da forma `var op constante` (ex.: `qtd(a) * 2 >= 10`) | a análise não normaliza expressões; trata como "sempre possível" |
| Falso positivo quando o total exato é inatingível (ex.: `total == R$ 50,00` com preços 49,90 e 29,90) | o acoplamento usa intervalos e ignora que quantidades são inteiras |
| Regra sem efeito por acoplamento não é detectada (`total < R$ 40,00` com desconto em produto de R$ 49,90) | a verificação 5 só olha `qtd(p)` direto |
| Uma condição por regra; sem `e`/`ou` | escopo; `e` exigiria interseção de faixas por regra, `ou` união |
| Busca exponencial no número de regras que atingem um produto | é um problema de clique máximo; com podas, fica instantâneo para dezenas de regras |
| Para no primeiro erro | simplicidade; erros em cascata ficariam confusos |
| Sem separador de milhar, percentual só inteiro, nomes só ASCII minúsculo; `x` é reservado | tokens mínimos |
| Em alguns estados do parser LALR a lista "esperado" é incompleta (após `total` não cita `*` e `/`) | o Lark calcula o conjunto aceito por simulação a partir do estado atual |
| O invariante "≤ 100%" é fraco: plataformas reais já limitam o preço a zero | ver seção 10 |

## 9. Mudanças em relação à versão de 20/10

| Mudança | Motivo |
|---|---|
| `total` = subtotal antes dos descontos; ordem das regras irrelevante | na versão anterior, o resultado do exemplo canônico dependia de uma regra não definida (R$ 179,60 antes do desconto, R$ 149,66 depois; `frete_gratis` usa R$ 150,00) |
| `frete = R$ X;` (frete padrão) | sem frete base, `frete R$ 0,00` não tinha efeito |
| Arredondamento definido | 15% de R$ 49,90 = 748,5 centavos |
| `desconto X%` sem `em` = todos os produtos, e entra na soma de cada um | não estava definido |
| Algoritmo de "podem se aplicar juntas" | não estava definido; a soma ingênua recusa faixas exclusivas |
| Verificações novas: conflito de frete, regra morta, item repetido | frete contraditório é a "contradição" do enunciado em sentido estrito |
| Preço como expressão constante | dá uso real à precedência de operadores |
| Zero ou mais carrinhos, com nome opcional | a verificação vale para todos os carrinhos, não para o do arquivo |

## 10. Construções consideradas e não incluídas

1. **Condições compostas (`e` / `ou`).** Promoções reais usam, mas `ou`
   transforma cada regra numa união de faixas e torna a análise de conflito
   combinatória. Ficou como limitação declarada.
2. **Descontos compostos** (20% sobre o já descontado). Com composição, nenhuma
   soma passa de 100% e a verificação 6 ficaria vazia. Escolhemos descontos
   aditivos sobre o preço original, que são previsíveis para o lojista. A
   alternativa honesta para descontos compostos seria um **piso de margem**
   (`produto p = R$ 49,90 custo R$ 20,00;`), que vale para qualquer forma de compor.
3. **Desconto em valor fixo** (`desconto R$ 10,00`). Exige conhecer o preço
   para saber se passa do valor do item, e mistura duas unidades na mesma soma.
   Possível extensão.
4. *(Fora do escopo por enunciado)*: funções, módulos, exceções, closures, inferência de tipos.
