# RELATÓRIO DE ANÁLISE — CÂMARA MUNICIPAL DE CURITIBA (PR) — ANALISTA DE SISTEMAS (2007, Instituto OPET)

## 1. Identificação

- **Órgão:** Câmara Municipal de Curitiba — PR (confirmado pelo logotipo da capa e pelo conteúdo das questões 12 e 36)
- **Banca:** Instituto OPET — Educação e Cidadania
- **Cargo:** Analista de Sistemas
- **Ano:** 2007 (concurso realizado em 02/12/2007)
- **Documentos processados:** prova (14 páginas, 60 questões) e gabarito oficial (2 páginas, tabela "ANALISTA DE SISTEMAS / Gabarito")
- **Observação:** o nome dos arquivos enviados mencionava "AC", sigla incorreta; a prova é de Curitiba/PR

## 2. Composição

| Item | Quantidade |
|---|---|
| Questões identificadas | 60 (numeração original 1–60 preservada) |
| Alternativas por questão | 5 (A–E), exceto questões anuladas (mantidas com suas alternativas) |
| Textos de apoio | 1 |
| Imagens | 1 |
| Gráficos e tabelas | 2 tabelas |
| Grupos identificados | 1 |
| Questões independentes | 55 |
| Questões anuladas no gabarito | 13 |

## 3. Agrupamentos identificados

| Material compartilhado | Questões vinculadas | Tipo |
|---|---|---|
| Texto "Fita verde no cabelo" (João Guimarães Rosa, "Ave, palavra", Ed. José Olympio) | 01, 02, 03, 04 e 05 | Texto |
| Figura da topologia de rede (conexões T1/T3) | 59 | Imagem (uso exclusivo) |
| Tabela modelo entidade-relacionamento (Pedido/Item/Produto) | 51 | Tabela (uso exclusivo) |
| Tabela Item_NF (normalização) | 53 | Tabela (uso exclusivo) |

- **GRUPO 01:** o conto "Fita verde no cabelo" foi transcrito integralmente e **repetido dentro de cada uma das questões 01–05** (regra de autossuficiência).
- As questões 51, 53 e 59 utilizam materiais exclusivos, portanto são classificadas como independentes com material próprio embutido.

## 4. Imagens, gráficos e tabelas

| Elemento | Localização | Questão | Arquivo/tratamento |
|---|---|---|---|
| Topologia de rede (T1/T3) | Página 14 | 59 | `imagens/imagem_001.jpg`, exibida no enunciado e em "Referências visuais" |
| Modelo ER (Pedido/Item/Produto) | Página 12 | 51 | Tabela Markdown reconstruída |
| Tabela Item_NF | Página 13 | 53 | Tabela Markdown reconstruída |
| Logotipos da capa (Câmara de Curitiba e Instituto OPET) | Página 1 | — | Não são conteúdo de questão; não incluídos em `imagens/` |

## 5. Questões independentes

Questões 06 a 60 (exceto as pertencentes ao GRUPO 01), cada uma com enunciado, alternativas e eventuais códigos-fonte/tabelas/figuras embutidos na própria questão:

06–10, 11, 12, 13, 14, 15, 16–38, 39–58, 59, 60.

## 6. Gabarito aplicado

Gabarito oficial — tabela única "ANALISTA DE SISTEMAS / Gabarito" (arquivo de 2 páginas; questão 60 na página 2):

| Questão | Resposta | Questão | Resposta | Questão | Resposta | Questão | Resposta | Questão | Resposta |
|---|---|---|---|---|---|---|---|---|---|
| 01 | B | 02 | B | 03 | D | 04 | C | 05 | D |
| 06 | D | 07 | E | 08 | ANULADA | 09 | A | 10 | C |
| 11 | ANULADA | 12 | B | 13 | A | 14 | D | 15 | ANULADA |
| 16 | B | 17 | B | 18 | D | 19 | E | 20 | C |
| 21 | E | 22 | D | 23 | ANULADA | 24 | C | 25 | ANULADA |
| 26 | C | 27 | A | 28 | ANULADA | 29 | ANULADA | 30 | ANULADA |
| 31 | D | 32 | ANULADA | 33 | ANULADA | 34 | A | 35 | B |
| 36 | B | 37 | C | 38 | B | 39 | A | 40 | ANULADA |
| 41 | ANULADA | 42 | C | 43 | C | 44 | B | 45 | E |
| 46 | E | 47 | A | 48 | D | 49 | B | 50 | C |
| 51 | ANULADA | 52 | C | 53 | B | 54 | D | 55 | D |
| 56 | B | 57 | C | 58 | B | 59 | B | 60 | E |

## 7. Correspondência prova × gabarito

- 60 questões na prova × 60 respostas no gabarito — correspondência 1:1 confirmada.
- 13 questões ANULADAS: 08, 11, 15, 23, 25, 28, 29, 30, 32, 33, 40, 41, 51.
- A questão 15 repete a questão 11; ambas anuladas — coerente.

## 8. Problemas encontrados na extração

1. **Artefato do documento original:** questões 28 e 30 contêm a expressão "Erro! A referência de hiperlink não é válida" (campo Word quebrado no PDF original) — preservada fielmente.
2. **Ruídos de OCR** (preservados sem correção): Q41 "affirmar"; Q42 "segunte", "APALAVRA-CHAVE", "aPALAVRA chave"; Q52 "ar quovo", "localizo", "especified", "execuçao"; Q53 "Estaabela"; Q55 "html><body>" (sem "<" inicial), "págin".
3. **Rótulo de alternativa duplicado pelo OCR** na questão 40 (dois "b)") — consolidado em uma única alternativa B, sem perda de conteúdo.
4. **Códigos-fonte:** preservados integralmente; a quebra de linhas do OCR foi mantida e os blocos foram apenas envoltos em fences Markdown.
5. **Nenhuma página, questão, alternativa, tabela ou figura foi omitida.**
