# PROMPT — EXTRAÇÃO, ANÁLISE E ORGANIZAÇÃO INTEGRAL DE PROVAS

> **Como usar este arquivo:** envie este prompt INTEIRO para a IA, junto com os PDFs da prova (prova + gabarito, se houver). Ele é o método oficial usado nas provas organizadas manualmente deste repositório. O resultado deve seguir o padrão descrito em [`INSTRUCOES.md`](INSTRUCOES.md) — Parte 1.

---

## OBJETIVO PRINCIPAL

Analise a prova original por completo, extraia absolutamente todo o seu conteúdo e gere uma nova versão organizada, estruturada e fiel ao documento original: todas as questões, textos de apoio, enunciados, alternativas, imagens, gráficos, tabelas, fórmulas e demais elementos. Identifique como as questões se relacionam (textos, imagens e materiais compartilhados). O resultado deve permitir que cada questão seja consultada e utilizada individualmente.

**A entrega final é uma pasta contendo `prova_organizada.md`, `relatorio_analise.md`, `imagens/` e o `PROVA_ORGANIZADA.zip`.**

---

## 1. REGRA ABSOLUTA: NÃO RESUMIR, NÃO OMITIR E NÃO REDUZIR NENHUM CONTEÚDO

**É EXPRESSAMENTE PROIBIDO RESUMIR, SIMPLIFICAR, ENCURTAR, ADAPTAR OU OMITIR QUALQUER CONTEÚDO DA PROVA ORIGINAL.**

Aplica-se a todos os elementos: textos de apoio (independente do tamanho), enunciados completos, todas as alternativas A–E, parágrafos, citações e trechos de documentos, imagens/gráficos/tabelas/diagramas, fórmulas e expressões, dados numéricos/porcentagens/unidades, notas de rodapé, legendas e títulos, instruções gerais e específicas, situações-problema.

Proibido: resumir textos; substituir parágrafos por explicações; retirar informações "secundárias"; encurtar enunciados ou alternativas; usar expressões como "texto conforme original" ou "demais informações omitidas"; substituir imagens por descrições resumidas; eliminar repetições do original; modificar palavras, números, datas ou valores; apresentar só os pontos principais.

Texto com várias páginas = reproduzir integralmente. Parte ilegível = registrar exatamente onde está o problema; nunca inventar ou completar.

## 2. EXTRAÇÃO COMPLETA DA PROVA

Leia e analise todas as páginas. Extraia todas as questões, respeitando numeração e estrutura original: número original, enunciado completo, texto de apoio integral, todas as alternativas, imagens/gráficos/tabelas relacionados, fórmulas e informações complementares. Preserve a ordem original. Não elimine questões repetitivas. Preserve o formato de questões discursivas, de verdadeiro/falso ou sem alternativas.

## 3. IDENTIFICAÇÃO DE QUESTÕES AGRUPADAS

Antes de organizar, identifique questões vinculadas a um mesmo material: textos compartilhados, imagens usadas por várias questões, gráficos/tabelas compartilhados, estudos de caso, situações-problema com várias perguntas, documentos de base. Ex.: "Grupo 01 — Texto de referência compartilhado pelas questões 01, 02 e 03".

## 4. REGRA ABSOLUTA: CADA QUESTÃO DEVE CONTER SEU PRÓPRIO CONTEXTO COMPLETO

**É obrigatório reproduzir novamente o material completo dentro de cada questão correspondente** — texto, imagem, gráfico, tabela, situação-problema, fórmula. Não deixe o material apenas na primeira questão do grupo. Vale para todas as disciplinas. Se a questão depender de texto E imagem, os dois aparecem novamente nela.

**Teste obrigatório de independência:** cada questão extraída isoladamente e enviada a outra IA (sem acesso ao resto) deve conter tudo o que é preciso para respondê-la. Se for preciso voltar a outra questão/página/grupo, a organização está incompleta.

## 5. EXTRAÇÃO E ORGANIZAÇÃO DAS IMAGENS

Extraia todas as imagens de conteúdo: fotografias, gráficos, tabelas em imagem, ilustrações, diagramas, mapas, figuras geométricas, imagens de textos de interpretação. Preserve qualidade e legibilidade; não corte nem modifique conteúdo; salve cada imagem individualmente.

Nomenclatura: `imagem_001.png`, `imagem_002.png`... (extensão conforme o arquivo extraído). Referência relativa no Markdown: `![Imagem da questão](imagens/imagem_001.png)`. Se a mesma imagem serve a várias questões, repita a referência em cada uma (mesmo arquivo físico, sem duplicar). Descarte apenas logos/marcas d'água repetidos.

## 6. ESTRUTURA DO ARQUIVO `prova_organizada.md`

```
# PROVA — [NOME OU IDENTIFICAÇÃO]

## 1. Análise geral da prova
(identificação; totais de questões, textos de apoio, imagens, gráficos/tabelas,
grupos e questões independentes; quais questões compartilham materiais;
observações sobre a estrutura; transcrição integral da capa/instruções)

## 2. Questões agrupadas
### GRUPO 01 — [IDENTIFICAÇÃO DO MATERIAL COMPARTILHADO]
**Questões relacionadas:** 01, 02 e 03.
#### QUESTÃO 01
**Material de apoio:** (texto completo / imagem correspondente)
**Enunciado:** (conteúdo integral)
**Alternativas:** A) ... B) ... C) ... D) ... E) ...
**Referências visuais:** (imagens correspondentes)
#### QUESTÃO 02 / 03 → material de apoio repetido INTEGRALMENTE em cada uma

## 3. Questões independentes
(enunciado, alternativas e todos os elementos de cada questão)

## 4. Observações e limitações da extração
(trechos ilegíveis, imagens ausentes, dificuldades — nunca para substituir conteúdo)
```

Quando houver gabarito oficial, inclua também `✅ **Gabarito: X** (origem)` logo após o título de cada questão, a tabela do gabarito na seção 1, `⚠️ **Gabarito: ANULADA**` para anuladas e `⚠️ **Gabarito: oficial não disponível**` quando não houver.

## 7. ARQUIVO `relatorio_analise.md`

Análise detalhada da estrutura original: quantidade de questões, todos os agrupamentos, textos/imagens/gráficos/tabelas compartilhados, questões independentes, relação entre cada questão e seu material, problemas encontrados, informações ilegíveis ou ausentes. Inclua a tabela de relacionamentos:

| Material compartilhado | Questões vinculadas | Tipo |
|---|---|---|
| Texto 01 | 01, 02 e 03 | Texto |
| Imagem 01 | 04 e 05 | Imagem |
| Gráfico 01 | 06, 07 e 08 | Gráfico |

Os dados da tabela refletem exclusivamente o que foi identificado na prova original.

## 8. CONFERÊNCIA E VALIDAÇÃO FINAL

Antes de entregar, compare a nova versão com o original e verifique: todas as páginas analisadas; todas as questões extraídas; numeração original preservada; enunciados completos; todas as alternativas preservadas; nada resumido/omitido/simplificado; todas as imagens extraídas; agrupamentos corretos; textos compartilhados repetidos integralmente em cada questão; imagens compartilhadas em todas as questões correspondentes; todos os caminhos de imagem funcionando; sem referências a arquivos inexistentes; estrutura do Markdown correta.

Apenas reorganizar é permitido. Reduzir não é. Se houver divergência, corrija antes de entregar. Provas extensas: trabalhe em etapas com arquivos intermediários, mas só considere concluído quando todas as páginas e questões forem processadas. Não finalize antecipadamente por limite de tamanho ou conveniência.

## 9. ENTREGA OBRIGATÓRIA

Pasta (e ZIP no padrão do repositório):

```
Camara_<Cidade>_<Ano>_<Cargo>/
├── prova_organizada.md
├── relatorio_analise.md
├── PROVA_ORGANIZADA.zip
└── imagens/
    ├── imagem_001.png
    ├── imagem_002.png
    └── ...
```

**ATENÇÃO: NÃO ENTREGUE APENAS UMA TRANSCRIÇÃO NO CHAT, UMA EXPLICAÇÃO OU UMA AMOSTRA DO RESULTADO.** Gere efetivamente os arquivos. Se houver limitação técnica, informe claramente o que não foi possível executar. Nunca apresente extração parcial como prova completa.

**REGRA DEFINITIVA: A PROVA ORIGINAL DEVE SER PRESERVADA NA ÍNTEGRA. A ORGANIZAÇÃO PODE SER MODIFICADA, MAS O CONTEÚDO JAMAIS DEVE SER RESUMIDO, REDUZIDO, ADAPTADO OU OMITIDO.**
