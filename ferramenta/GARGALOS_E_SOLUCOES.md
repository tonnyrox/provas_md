# 🧯 GARGALOS E SOLUÇÕES — Manual de campo para quem organiza as provas

> **Para quem é:** para o humano OU para o agente de IA que processa os PDFs. Aqui estão os problemas **reais** que já apareceram neste repositório e a solução testada para cada um. Objetivo: acertar de primeira, sem precisar de revisão posterior.
>
> **Leia junto:** [`INSTRUCOES.md`](INSTRUCOES.md) (padrão + passo a passo) e [`PROMPT_EXTRACAO.md`](PROMPT_EXTRACAO.md) (prompt de extração integral). Ao terminar qualquer prova, rode [`validar_prova.py`](validar_prova.py).

---

## 0. Fluxo de decisão (comece aqui)

```
PDF da prova
 ├─ Tem texto selecionável?
 │   ├─ SIM → python organizador_provas.py --pasta <pdfs> --saida <dir> --nome <Nome_Padrao>
 │   │        → validar_prova.py → conferir checklist → publicar
 │   └─ NÃO (escaneado) → OCR (Caso 1) → builder (exemplo_builder_ocr.py) → validar → publicar
 └─ Casos especiais: gabarito multi-cargo (Caso 3), metadados errados no nome (Caso 5),
    questões anuladas/discursivas (Caso 6), prova em formato antigo (Caso 7)
```

**Regra de ouro:** a ferramenta automática resolve a maioria; quando não resolve, NÃO publique "quase certo" — use o builder/IA e depois **valide**. Nunca invente conteúdo para preencher lacuna; registre na seção 4.

---

## Caso 1 — PDF escaneado (sem texto selecionável)

**Sintoma:** `organizador_provas.py` reporta "nenhuma questão detectada" ou o texto sai vazio/ilegível.

**Solução (pipeline OCR):**
1. Rode OCR no PDF (ex.: `ocrmypdf entrada.pdf saida.pdf`) ou use a ferramenta de OCR da sua sessão de IA.
2. Transcreva a prova página a página a partir do resultado do OCR (transcript).
3. Monte a prova com o builder: veja **[`exemplo_builder_ocr.py`](exemplo_builder_ocr.py)** — template pronto que importa `organizador_provas` como biblioteca e chama `montar_prova(..., via_ocr=True)`. O parâmetro `via_ocr=True` troca a 1ª observação da prova para "Conteúdo extraído via OCR de PDF escaneado (imagem), transcrito integralmente e conferido contra o original."
4. Capa transcrita INTEGRALMENTE (instruções + grade de respostas, se houver).
5. Valide com `validar_prova.py` e faça a **conferência de cobertura** (Caso 8).

**Provas reais feitas assim:** Barra Bonita 2012, Serra 2014, Abaetetuba 2018 (2 cargos).

---

## Caso 2 — Sujeira do texto extraído (PDF com texto)

A extração literal do PDF traz lixo que NÃO é conteúdo da prova. Filtre antes de montar:

| Lixo típico | Exemplo real | Solução |
|---|---|---|
| Marca d'água de site | `pcimarkpci ...`, `www.pciconcursos.com.br` | Descartar linha (a ferramenta já filtra `MARCA_DAGUA_RES`) |
| Cabeçalho/rodapé repetido | "CONCURSO PÚBLICO – CÂMARA MUNICIPAL DA SERRA/ES", "Cargo: ...", "Prova aplicada em ...", `- N -` (numeração de página) | Descartar em TODAS as páginas |
| Títulos de seção da banca | `LÍNGUA PORTUGUESA`, `CONHECIMENTOS ESPECÍFICOS`, `RASCUNHO` | Descartar do corpo; registrar a estrutura dos blocos na seção 1 |
| Linhas mescladas | Duas questões numa linha só (Barra Bonita Q34–37) | Separar com regex antes de detectar questões; conferir depois |
| Alternativa colada no enunciado | `...por dispensa de licitação. A) mandar...` | Dividir com `re.split(r"\s+(?=[B-E]\)\s)", linha)` |
| Alternativas fora de ordem | Transcript emite A, C, B, D (Serra Q13/Q17/Q29) | Reordenar por letra ao reconstruir |
| Texto justificado palavra-por-linha | Alto Paraíso: `B.` / `A` / `potencial` / `prejudicialidade`... | Manter o fluxo do original (não inventar espaçamento) |
| Capitulares decorativas | Piracicaba: `ocê recebeu` (= "Você recebeu") | Registrar na seção 4, reproduzir conforme o fluxo |
| `\xa0` (espaço não separável) e `\t` | Comum em provas antigas | Normalizar para espaço simples |

**Formatos de alternativa aceitos:** `A)`, `A.`, `A:`, `(A)` — a ferramenta normaliza tudo para `A)` na saída. Alternativas com mais de 4 letras (A–E) são normais; **menos de 4 em prova objetiva indica problema de detecção** (exceção: provas de V/F, ver Caso 6).

---

## Caso 3 — Gabaritos

| Situação | Como resolver |
|---|---|
| **Multi-cargo** (gabarito com páginas de vários cargos) | Selecionar o bloco da página do cargo da prova. A ferramenta acha o cargo pela capa (`CARGO: 2.03 - ...`) **ou por rótulo de cargo no gabarito** (`FUN - AUXILIAR...`, `MED - AGENTE ADMINISTRATIVO` — Bezerros 2025). Se não achar, identifique manualmente e extraia só o bloco correto (ex.: Votorantim 2016 — cargo 2.03 Cerimonialista entre 6+ cargos; Abaetetuba 2018 — página do cargo no gabarito multi-cargo). |
| **Gabarito lido pela metade** (tabela com várias colunas de questões) | CONFERIR se TODAS as questões receberam resposta. Caso real: Catas Altas da Noruega 2010 — a tabela tinha 4 colunas (Português 01–10, Matemática 11–20, Específica Agente Legislativo 21–40, Específica Secretário 21–40) e só as duas últimas foram capturadas; as questões 01–20 ficaram sem gabarito até a auditoria refazer o OCR da página e inserir as 20 respostas faltantes. Sintoma: `validar_prova.py` emite "gabarito parcial — questões sem resposta". |
| **Questões V/F no gabarito** (respostas `V`/`F` em vez de A–E) | A ferramenta aceita: a passada A–E roda primeiro e a passada V/F preenche só os números que ficaram sem resposta (Belo Jardim 2015 Q10 = V). |
| **Retificação no próprio gabarito** | Usar a resposta retificada e registrar: `✅ **Gabarito: A** (gabarito oficial definitivo — Tipo 1 (Cor Branca))` + observação "questão 11 tem resposta retificada para A no gabarito oficial" (Abaetetuba 2018 Administrador). |
| **Gabarito indisponível** (PDF de gabarito só tem instruções, ou não veio) | NÃO inventar. Prova fica sem linhas de gabarito; registrar na seção 4: "Gabarito oficial não disponível: o PDF de gabarito contém apenas instruções, sem grade de respostas" (Serra 2014; Brusque 2024 — divulgado apenas no site da banca). |
| **Preliminar × definitivo** | Citar a origem exata na linha de gabarito: "(gabarito oficial preliminar — Instituto ADM&TEC)". |
| **Prova e gabarito com nomes genéricos** (`prova.pdf` / `gabarito.pdf`) | Identificar cidade/ano/cargo pela CAPA e pelo conteúdo, nunca pelo nome do arquivo (Alvorada 2008: identificado FAURGS pela capa). |
| **Tipos de prova (Cor Branca, Tipo 1...)** | Usar o tipo correspondente e citar na origem: "Tipo 1 (Cor Branca)" (Barbacena 2022 — TIPO 4 – AZUL; a ferramenta seleciona o bloco do tipo correto). |
| **Marcador `#` no gabarito** (questão anulada) | Gabaritos oficiais usam `#` para anulada; a ferramenta converte para `⚠️ **Gabarito: ANULADA**` (Barbacena 2022 Q7, Bom Jesus do Itabapoana 2010 Q6 = `X`). |

**Nunca:** preencher gabarito "deduzindo" respostas, usar gabarito de outro cargo, ou omitir a origem.

---

## Caso 4 — Imagens

- **Descartar:** logos da banca (capa e repetidos nas páginas), marcas d'água, folhas de rascunho, imagens vazias ou em branco, brasão da capa. A ferramenta já descarta imagens vazias e as que só aparecem na capa.
- **Manter:** gráficos, tabelas em imagem, tirinhas, ilustrações, mapas, figuras geométricas — tudo que é conteúdo de questão.
- **Renumerar:** salvar como `imagem_001`, `imagem_002`... na ordem das questões, atualizando as referências no Markdown (a ferramenta faz isso com `renomear_imagens`).
- **Mesma imagem em várias questões:** um arquivo físico, referências repetidas.
- **Imagem dentro de tabela/questão complexa:** identificar a qual questão pertence lendo o contexto da página (Serra 2014: tabela + 3 gráficos da Q24; Abaetetuba Agente: 2 gráficos pizza da Q11).
- **Imagem não extraível** (ícone decorativo vetorial pequeno): registrar na seção 4 (Serra 2014 Q12).
- **Figuras vetoriais** (não são "imagens" no PDF): recortar a região da página em alta resolução e salvar como imagem (Piracicaba 2019: Q19, Q29, Q30, Q41...).
- **Imagem extraída mas nunca referenciada = BUG GRAVE:** se `validar_prova.py` acusar imagem órfã, descubra a qual questão ela pertence e insira a referência. Caso real: Piracicaba 2019 — a tirinha "O melhor de Calvin" (base das questões 08 e 09, que dizem "Leia a tira...") estava salva em `imagens/` mas sem referência dentro das questões; corrigido inserindo `![...](imagens/imagem_001.png)` no material de apoio das duas questões e no cabeçalho do grupo.
- **Gráfico em camada separada do PDF não capturado:** a extração por página pode perder imagens cujo xref não é único da página. Caso real: Americana 2024 Q11 — o gráfico de barras ("antecedência de compra de ingressos de cinema") estava no xref 66 da página 4, entre as duas partes do enunciado; recuperado com `pymupdf.Pixmap(doc, xref)`, verificado visualmente e inserido como `imagem_004.png`.
- **Logo salvo por engano como se fosse conteúdo:** se a imagem órfã for logo/marca d'água (Araripina 2024 — logo do Instituto igeduc; Calumbi 2024 — marca do site), remova o arquivo, atualize a seção 1 e registre na seção 4.

---

## Caso 5 — Metadados errados no NOME do arquivo

O nome do arquivo é só uma dica. **Confira sempre capa + gabarito:**

| Caso real | Nome do arquivo dizia | Correto (capa/gabarito) |
|---|---|---|
| Americana 2024 | "Contador" | **Analista de Comunicação** |
| Altônia | "2023" | **2024** (gabarito é de 2024) |
| Acaraú 2009 | "Agente" | **Agente Administrativo** (cargo do gabarito) |

Se o nome do arquivo conflitar com o documento, vale o documento — e registre a correção no commit/relatório.

---

## Caso 6 — Questões especiais

- **Anulada:** `⚠️ **Gabarito: ANULADA**` + manter a questão inteira no lugar original (Acaraú 2009 Q18; Alvorada 2008 Q15; marcadores `#` ou `X` no gabarito oficial viram ANULADA — Barbacena 2022 Q7, Bom Jesus do Itabapoana 2010 Q6).
- **Verdadeiro/Falso (sem alternativas A–E):** preservar o formato original ("Julgue o item... V ou F"), gabarito pode ser V/F/C/E (Araripina 2024, São José do Egito 2024 — 100 questões de itens).
- **Discursiva / Produção Escrita / Redação:** `⚠️ **Gabarito: não se aplica — questão discursiva**`, bloco próprio com `####` (Itaiópolis 2024: 4 questões de Produção Escrita) ou seção própria (`### REDAÇÃO`, Piracicaba 2019). Manter orientações da banca integralmente (contagem de linhas, rascunho etc.).
- **Afirmativas I, II, III dentro do enunciado:** não são grupo — ficam dentro do enunciado da própria questão (padrão FURB — Brusque 2024).
- **Texto fragmentado palavra por palavra** (camada de texto quebrada no PDF): o enunciado sai como `Um\n\nanalista\n\nestá...` e as alternativas podem ficar incompletas ou sumir. Reconstruir a questão a partir do PDF original e registrar na seção 4 (Bezerros 2025 Q10 e Q20 — a Q20 tinha perdido TODAS as alternativas; Barbacena 2022 Q45 — tinha perdido 2 dos 4 grupos de itens V/F e as alternativas finais A–D).
- **Páginas finais após a última questão objetiva** (prova discursiva, rascunho, folha de texto): NÃO deixar que virem parte da última questão. A `montar_prova` tem o parâmetro `pos_texto`: transcreve essas páginas íntegras numa seção própria ("### Transcrição integral das páginas finais (após a última questão)") entre as seções 3 e 4 (Belo Horizonte 2023 — PROVA DISCURSIVA após a Q60).

---

## Caso 7 — Prova antiga em formato fora do padrão

Se encontrar pasta de prova com formato diferente (títulos `# PROVA ORGANIZADA —`, questões `## Questão NN`, sem as 4 seções — ex.: Arcoverde 2016 e Brusque 2024 antes da padronização):

1. Reestruture para o padrão (seções 1–4, `#### QUESTÃO NN`, `A)`, material de apoio rotulado, relatório com tabela de relacionamentos).
2. **Conferência de integridade obrigatória:** compare linha a linha o conteúdo das questões da versão antiga × nova (normalizando `- (A) x` → `A) x`). Resultado esperado: **0 linhas de conteúdo perdidas**. Metadados da análise antiga podem ser reescritos nas seções 1/4.
3. Regenere o ZIP.

---

## Caso 8 — Validação obrigatória antes de publicar

1. **Validação estrutural automática:**
   ```
   python validar_prova.py --pasta "Provas MD"            # todas as provas
   python validar_prova.py --pasta "Provas MD/Camara_X"   # uma prova
   ```
   Erros = não publique. Avisos = confira se são os casos legítimos (discursivas).
   O validador também acusa: **imagem órfã** (extraída e nunca referenciada — ERRO), **imagem do material compartilhado do grupo que não aparece em todas as questões do grupo** (ERRO), **gabarito parcial** (algumas questões com resposta e outras sem — AVISO) e **questão que cita tira/figura/gráfico sem referência de imagem** (AVISO).
2. **Conferência de cobertura (IA):** compare o `prova_organizada.md` com o transcript/PDF original linha a linha; cada linha "faltando" precisa ser classificada como (a) falsa divergência explicável (cabeçalho descartado, formato normalizado, linha mesclada dividida) ou (b) perda real → corrigir. Meta: **zero perdas reais**.
3. **Checklist do `INSTRUCOES.md` (Passo 4)** — conte questões, confira alternativas, gabarito, imagens e capa.

---

## Caso 9 — Publicação

- Tudo dentro de `Provas MD/`, commit direto na `main`, mensagem em português descrevendo as provas adicionadas e as correções.
- Antes do commit: `git status` para garantir que só entrou o que devia; apagar `ferramenta/__pycache__/` se aparecer.
- Nunca criar pastas paralelas (`provas/`, `novas_provas/`) nem branches para prova nova — o padrão é commit direto na `main`.

---

## Apêndice — Provas de referência por tipo de situação

| Situação | Prova de referência em `Provas MD/` |
|---|---|
| OCR + builder | `Camara_Barra_Bonita_2012_Agente_Administrativo`, `Camara_Serra_2014_Agente_Legislativo` |
| Grupo grande (10 questões) | `Camara_Abaetetuba_2018_Agente_Legislativo` |
| V/F em itens (100 questões) | `Camara_Araripina_2024_Agente_Administrativo` |
| Discursivas + objetivas | `Camara_Itaiopolis_2024_Agente_Legislativo`, `Camara_Piracicaba_2019_Agente_Legislativo` |
| Sem gabarito | `Camara_Serra_2014_Agente_Legislativo`, `Camara_Brusque_2024_Agente_Administrativo_Recepcao` |
| Multi-cargo no gabarito | `Camara_Votorantim_2016_Cerimonialista`, `Camara_Abaetetuba_2018_Administrador` |
| Anulada | `Camara_Acarau_2009_Agente_Administrativo` (Q18), `Camara_Alvorada_2008_Agente_Administrativo` (Q15) |
| Imagens (tirinha/gráfico) | `Camara_Brusque_2024_Agente_Administrativo_Recepcao`, `Camara_Americana_2024_Analista_de_Comunicacao` |
| Alternativas "A." | `Camara_Alto_Paraiso_2024_Agente_Administrativo` |
| Gabarito por rótulo de cargo (`MED - ...`, `FUN - ...`) | `Camara_Bezerros_2025_Agente_Administrativo` |
| V/F no gabarito (resposta `V`) | `Camara_Belo_Jardim_2015_Agente_Administrativo` (Q10) |
| `#` = anulada no gabarito | `Camara_Barbacena_2022_Agente_Administrativo` (Q7) |
| Páginas finais/discursiva via `pos_texto` | `Camara_Belo_Horizonte_2023_Administrador` |
| Gabarito lido pela metade (colunas 01–10/11–20 perdidas) | `Camara_Catas_Altas_da_Noruega_2010_Agente_Legislativo` (corrigido em auditoria) |
| Imagem órfã = bug (tirinha sem ref nas questões) | `Camara_Piracicaba_2019_Agente_Legislativo` (Q08–09, corrigido) |
| Texto fragmentado palavra por palavra | `Camara_Bezerros_2025_Agente_Administrativo` (Q10/Q20 reconstruídas) |
