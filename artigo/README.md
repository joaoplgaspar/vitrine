# Artigo

Template ACM `sigconf`, 4 a 6 páginas sem as referências (−1 ponto por página a mais).

## Como compilar

No Overleaf: **New Project → Upload Project**, enviar esta pasta `artigo/`
compactada em .zip, e compilar com pdfLaTeX (o BibTeX roda sozinho). A classe
`acmart` já vem instalada no Overleaf.

Para manter o histórico no GitHub: cada um edita o arquivo da sua seção
**aqui no repositório**, com commit no próprio nome, e alguém reenvia o .zip
para o Overleaf quando quiser ver o PDF.

## Quem escreve o quê

| Arquivo | Dono | Espaço |
|---|---|---|
| `secoes/01-introducao.tex` | todos | ~0,75 pág. |
| `secoes/02-linguagem.tex` | João Pedro + Nathan (decisões) | ~1,25 |
| `secoes/03a-lexico-sintatico.tex` | João Pedro | ~0,25 |
| `secoes/03b-semantica.tex` | Juliard | ~0,25 |
| `secoes/03c-conflitos.tex` | Nathan | ~0,5 |
| `secoes/03d-execucao.tex` | Lucas | ~0,25 |
| `secoes/04-avaliacao.tex` | Kauê | ~1,5 (maior peso) |
| `secoes/05-limitacoes.tex` | Juliard | ~0,5 |
| `secoes/06-conclusao.tex` | todos | 1 parágrafo |
| `secoes/07-uso-de-ia.tex` | todos | obrigatório |
| `secoes/apendice-reproducao.tex` | Lucas | |

Cada arquivo tem, em comentários (`%`), o que o enunciado exige naquela seção e
os dados que já existem. Apaguem os comentários conforme forem escrevendo.

## Datas

24/11 rascunho (obrigatório) · 01/12 revisão por pares · 12/12 versão final
