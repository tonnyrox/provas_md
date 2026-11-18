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
| PDF vetorial sem camada de texto (OCR página inteira) | `Camara_Contagem_2022_Analista_Tecnico_Analista_de_Sistemas` |
| Gabarito multi-blocos por código de cargo (FUNDEP/UFMG) | `Camara_Contagem_2022_Analista_Tecnico_Analista_de_Sistemas` |
| Ano impossível no nome do arquivo ("2030") | `Camara_Conde_2022_Nivel_Fundamental_Completo` |
| Mesmo concurso, provas por cargo distintas | `Camara_Conselheiro_Lafaiete_2018_Agente_Legislativo` + `Camara_Conselheiro_Lafaiete_2018_Analista_de_Sistemas` |
| Redação em seção dedicada (seção 4) | `Camara_Contagem_2022_Analista_Tecnico_Analista_de_Sistemas` |

---

## Caso 10 — Lote 4: novos formatos e melhorias na ferramenta (2025)

Aprendizados do lote 4 (Bom Princípio, Bonito de Minas, Brusque, Caeté, Camaragibe, Campina Grande, Campo Mourão, Canaã dos Carajás, Candiota, Capanema, Carangola 1992/2008), já incorporados ao [`organizador_provas.py`](organizador_provas.py):

1. **`parear_pdfs` sem gabarito na pasta** — variável `cg` não definida quando não existia nenhum PDF de gabarito → `UnboundLocalError`. Corrigido (inicialização antes do loop). **Sintoma:** crash ao processar pasta só com provas.
2. **Gabarito colunar com marcação `N`/`X`** (FURB/Brusque): linhas `NN: A` / `NN: X` (X = anulada). Novo parser `parsear_gabarito_colunas` + regex `ANULADA_X_RE`.
3. **Gabarito vertical multi-coluna** (números e letras em colunas separadas, vários pares por linha, dígitos fatiados "3"+"5" = 35): novo parser `parsear_gabarito_vertical` usando coordenadas de palavras (`page.get_text("words")`), com fusão de dígitos por proximidade (< 7pt) e limiar de confiança de 60%.
4. **Cabeçalhos alternativos de questão** agora detectados automaticamente: `14ª QUESTÃO` (ordinal), `Questão 01 - enunciado na mesma linha` (inline) e `NN)` sozinho na linha (exigindo alternativas no bloco para não pegar listas da capa).
5. **Imagens descartáveis filtradas automaticamente**: fundo de página inteira (> 85% da área) e marca d'água repetida em ≥ 60% das páginas com altura < 150px (ex.: `pcimarkpci`) não viram mais `imagem_XXX.png` órfãs.
6. **Layout em duas colunas**: nova flag `--colunas 2` reordena os blocos de texto (coluna esquerda inteira antes da direita) para provas tipo jornal.
7. **Recorrência entre concursos da mesma cidade** (ex.: Carangola 1992 ≈ 50% das questões reaproveitadas em 2008): NÃO é duplicidade — registra a ocorrência na seção "Recorrência histórica" dos dois `relatorio_analise.md` e mantém as duas provas integralmente.
8. **`validar_prova.py`** agora aceita linha de gabarito `🚫 **Gabarito: ANULADA**` além de ✅/⚠️.

Referências novas no apêndice: `Camara_Brusque_2024_Agente_Administrativo_Recepcao` (gabarito `NN: X`), `Camara_Carangola_1992_Agente_Administrativo_I` + `Camara_Carangola_2008_Agente_Administrativo_I` (recorrência entre concursos).

## Caso 11 — Lote 6: cabeçalhos com hífen e número "sozinho" com ponto (2026)

Aprendizados do lote 6 (Bonito de Minas 2009, Caucaia 2010/2016/2024, Caçapava 2015/2025, Cerro Corá 2020), já incorporados ao [`organizador_provas.py`](organizador_provas.py):

1. **Número + hífen** (formato antigo, ex. Bonito de Minas 2009): enunciados do tipo `01- Nesta tirinha...`, `39-Para abrir o menu...` (inclusive sem espaço depois do hífen) e separador hífen sozinho na linha não eram reconhecidos — só `.` e `)` eram. `QUESTAO_NUM_RE` e `QUESTAO_NUM_SOZINHO_RE` agora aceitam `-` como separador. **Proteção:** instruções numeradas da capa (`01-`, `02-`...) não viram questões porque o gate exige alternativas no bloco e a cadeia sequencial escolhida é a que contém mais questões com alternativas (40 > 6, no caso de Bonito de Minas).
2. **Número + ponto sozinho na linha** (enunciado começa na linha de baixo, ex. Caucaia 2024/2010): `Questão 1.` em uma linha e o texto na seguinte fazia as questões iniciais não serem detectadas → `KeyError` no `montar_prova`. `QUESTAO_NUM_SOZINHO_RE` agora aceita também `.` (antes só `)`).
3. **Material preliminar é parte do material de apoio**: frase introdutória do texto-base (ex. "Leia o texto para responder às questões de 1 a 9." em Caucaia 2024) pode cair na seção de capa por estar antes do texto. Regra de auditoria: ela precisa aparecer **na capinha do GRUPO e dentro do material de apoio de cada questão do grupo** (autossuficiência — PROMPT MESTRE §10).
4. **Imagem referenciada pode cair no bloco da questão seguinte** (ex. tirinha de Bonito de Minas 2009 extraída antes do cabeçalho `01-`): na auditoria, mover a referência para a questão que a cita no enunciado e registrar como conteúdo de `Referências visuais`.
5. **Números fantasmas entre colunas** (Caçapava 2015 numeração dupla): números soltos que vazam de outra coluna (`04`, `49`, `50`) são numeração, não enunciado — garantir que os regex + cadeia seqüencial não os elevem a questões (prova real: transcrição manual conferida).
6. **Frações empilhadas/expressões visuais** (Caçapava 2015): linearizar fielmente (ex. `12/40`) e registrar a decisão nas Observações — não omitir nem "corrigir".
7. **Gabarito multi-cargo em 2+ páginas** (Caucaia 2016/2024): ler o PDF oficial inteiro, identificar o bloco do cargo da prova (por cabeçalho), preencher só esse bloco e registrar no relatório quais blocos foram ignorados; questões `NULA`/`X` → `⚠️ **Gabarito: ANULADA**`.
8. **Prova sem gabarito** (Caucaia 2010, Bonito de Minas 2009 — onde o PDF "gabarito" é cópia da prova): registrar `Gabarito: **não disponível**` — nunca inventar respostas.

Referências novas no apêndice: `Camara_Bonito_de_Minas_2009` (hífen + imagem fora de posição), `Camara_Caucaia_2024_Agente_Administrativo_do_Legislativo` (intro do grupo + gabarito multi-cargo), `Camara_Caucaia_2016_Agente_Administrativo` (gabarito 3 páginas/multi-nível), `Camara_Caucaia_2010_Agente_Administrativo` (sem gabarito), `Camara_Cacapava_2015_Agente_Administrativo` (números fantasma + frações + capa com caixa de exemplo).

## Caso 12 — Lote 7: PDF vetorial sem camada de texto, duas colunas que cruzam e gabarito multi-blocos por código de cargo (2026)

Aprendizados do lote 7 (Chapecó 2025/2007, Clevelândia 2011 I/II e 2017, Conde 2022, Conselheiro Lafaiete 2018 ×2, Contagem 2022):

1. **PDF vetorial sem camada de texto** (`Camara_Contagem_2022_Analista_Tecnico_Analista_de_Sistemas`): a leitura nativa (`get_text`) devolve ~133 caracteres/página (só numerações e marcas) pois o conteúdo é vetorial com fontes sem mapa de caracteres. **Solução:** renderizar as páginas inteiras com PyMuPDF em 200–300 dpi e passar OCR (página inteira, não por coluna). Neste cenário o pipeline padrão do `organizador_provas.py` não produce nada — a prova precisa ser construída por transcrição assistida, questão por questão.
2. **Duas colunas com frases cruzando colunas**: em Contagem 2022 as frases quebram no meio e continuam na coluna oposta (e às vezes na página seguinte). OCR por coluna fragmenta o texto (metade da frase em cada arquivo); OCR de **página inteira** preserva a ordem de leitura. Regra: quando suspeitar de frase cortada (linha termina sem pontuação/sintaxe), re-OCR a página inteira antes de reconstruir manualmente.
3. **Pontos incertos → tripla conferência**: toda leitura divergente entre OCRs foi resolvida com recorte em 300 dpi (`page.get_pixmap(clip=Rect(...))`) da região exata + segunda e terceira leituras (mistral-ocr × easyocr × tesseract). Nunca "adivinhar" a palavra: recortar e reler. Exemplos resolvidos assim: "étnico-identitárias", "improbidade administrativa", "independentemente de convocaç\u00e3o", "Procuradoria da Câmara... Comp\u00f5e".
4. **Gabarito multi-blocos por código de cargo** (FUNDEP/UFMG, Contagem 2022): o PDF oficial traz vários cargos por página (blocos lado a lado), com colunas distintas por código (101–312) e por fase (PRÉ/ PÓS-RECURSOS). Extrair a coluna exata do cargo pelo **código numérico em coordenadas x** (render + recorte da faixa de coluna) e registrar no relatório qual coluna/bloco foi usado. Preferir o gabarito **PÓS-RECURSOS** quando existirem as duas versões.
5. **ANULADA no meio do gabarito**: a questão anulada recebe literalmente `**ANULADA**` na tabela e `✅ **Gabarito: ANULADA**` na questão (já suportado pelo `validar_prova.py`), com nota nas Observações apontando a fonte oficial.
6. **Duplicidade entre remessas com nomes diferentes** (`Camara_Conde_2022_Nivel_Fundamental_Completo`): dois PDFs rotulados "Conde - PB - 2030" eram concessões antigas do mesmo gabarito oficial do Conde 2022 (ano impossível no nome do arquivo). Prova única processada; a data/ano real vem do conteúdo da capa, não do nome do arquivo.
7. **Regra absoluta de imagem inline** (Lote 7 como um todo): cada questão que usa uma imagem carrega a referência `![Imagem da quest\u00e3o](imagens/imagem_XXX.png)` dentro de si (material de apoio e/ou Referências visuais), lendo o enunciado para confirmar o vínculo; imagens decorativas (logos, marca d'água) continuam descartadas. No resto do banco as fotos/capas das provas também foram verificadas questão a questão na decisão de agrupamento.

Referências novas no apêndice: `Camara_Contagem_2022_Analista_Tecnico_Analista_de_Sistemas` (PDF vetorial + 2 colunas + gabarito multi-blocos + ANULADA), `Camara_Conde_2022_Nivel_Fundamental_Completo` (ano errado no nome do arquivo — 2030), `Camara_Conselheiro_Lafaiete_2018_Agente_Legislativo` e `Camara_Conselheiro_Lafaiete_2018_Analista_de_Sistemas` (mesmo concurso, cargos diferentes — provas distintas).

## Caso 13 — Pente fino do banco completo: ícones/figuras de GUI perdidos na extração (2026)

Auditoria das 101 provas publicadas com `validar_prova.py` reforcedido + comparação por questão. Achados e correções:

1. **Ícones de interface (GUI) inline se perdem discretamente** (`Camara_Chapeco_2007_Analista_de_Comunicacao`): o texto extraível descreve a pergunta, mas o ícone citado no meio do enunciado ("...clica-se no botão .", "...representado pela figura ,") não vira `imagem_XXX.png` e passa despercebido porque o enunciado continua coeso. **Como detectar:** (a) frase terminando em " ." ou " ," logo após palavras-chave (ícone/figura/botão); (b) **alternativas idênticas ou vazias** (ex.: `A) F5`, `B) F5`, `D) F5` — na verdade cada alternativa era ícone + atalho); (c) alternativas inteiramente em branco; (d) `get_image_info`/`get_drawings` da página versus referências do md.
2. **Figuras vetoriais desenhadas como milhares de linhas de 1px** (Chapecó 2007, Q48/Q49): não constam como imagem raster — são `get_drawings`. **Solução:** renderizar por recorte (`get_pixmap(clip=Rect)`) em 300 dpi, que captura raster + vetor + texto de uma vez. Verificar o conteúdo por OCR do recorte antes de numerá-la.
3. **Procedimento aplicado (regra absoluta de imagem inline em auditoria):** para cada questão corrigida, a referência entra em duas camadas, sempre na posição que o ícone ocupa no original: (a) inline, dentro do enunciado ou da alternativa em que o ícone aparece; e (b) repetida no bloco `Referências visuais` da mesma questão. Em `Camara_Chapeco_2007_Analista_de_Comunicacao` foram recuperadas 20 imagens (`imagem_003` a `imagem_022`) nas questões 12, 13, 14, 44, 47, 48 e 49.
4. **Quando o PDF original não está mais disponível:** registrar como limitação nas Observações da prova e marcar o relatório como **CONCLUÍDA COM RESSALVAS** (realizado em `Camara_Belo_Jardim_2015_Agente_Administrativo` Q16 — planilha do Excel perdida — e `Camara_Sao_Jose_de_Mipibu_2020_Assistente_de_Cerimonial` Q22 — esquema da mesa de honra preservado só em texto). Nunca recriar a figura "de cabeça": inventar conteúdo é violação do PROMPT MESTRE.
5. **Validador reforçado** (`validar_prova.py`):
   - aviso de "cita figura sem imagem" agora cobre `figura/imagem/gráfico acima`, `pelo ícone`, `clica-se no botão`, `qual dos ícones`, `charge/desenho/esquema abaixo` — mas só dentro de `**Enunciado:**` (o material de apoio com "botão esquerdo do mouse" não gera falso positivo);
   - tabelas reproduzidas inline em Markdown (`|---|`) não contam como figura faltante;
   - padrão com proposta de redação aceito: seção 4 = "## 4. Redação" e Observações em "## 5. Observações e limitações da extração".
6. **Bullets de template desatualizados**: conferir que "Gabarito oficial não disponível — nenhuma resposta foi preenchida" nas Observações nunca coexista com gabaritos ✅ preenchidos nas questões (bug encontrado e corrigido na Chapecó 2007).

Referência de auditoria completa: `Camara_Chapeco_2007_Analista_de_Comunicacao` (20 ícones/figuras recuperados).
