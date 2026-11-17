# 📋 INSTRUÇÕES COMPLETAS — Como organizar e subir provas neste repositório

> **Leia este arquivo inteiro antes de começar.** Ele explica, passo a passo, como transformar PDFs de provas em pastas organizadas no padrão deste repositório e como publicá-las. Seguindo estas instruções, qualquer pessoa (ou IA) produz um resultado idêntico ao das provas já existentes em `Provas MD/`.

---

## PARTE 1 — O PADRÃO OBRIGATÓRIO

### 1.1. Onde as provas ficam

Todas as provas ficam em **um único diretório**: `Provas MD/`. Nada deve ser criado fora dele (a única exceção é a pasta `ferramenta/`).

### 1.2. Nome da pasta da prova

Formato fixo: **`<Origem>_<Cidade>_<Ano>_<Cargo>`**

- **Origem**: `Camara` (Câmera Municipal) ou `Prefeitura` (Prefeitura/conjunto de órgãos).
- **Cidade**: nome sem acentos, espaços por `_` (ex.: `Sao_Jose_dos_Pinhais`).
- **Ano**: 4 dígitos (ex.: `2024`). Se o ano não existir no documento, não invente.
- **Cargo**: nome do cargo, espaços por `_` (ex.: `Agente_Administrativo`, `Analista_de_Sistemas_Junior`).

Exemplos reais deste repositório:

```
Camara_Brusque_2024_Agente_Administrativo_Recepcao
Camara_Sao_Jose_dos_Pinhais_2016_Analista_de_Sistema_Junior
Prefeitura_Bom_Jesus_e_Camara_Sao_Tome_2022_Agente_Administrativo
```

### 1.3. Arquivos obrigatórios dentro da pasta

```
Camara_<Cidade>_<Ano>_<Cargo>/
├── prova_organizada.md        ← OBRIGATÓRIO: prova completa reorganizada
├── relatorio_analise.md       ← OBRIGATÓRIO: análise da estrutura + tabela de relacionamentos
├── PROVA_ORGANIZADA.zip       ← OBRIGATÓRIO: zip com os 2 arquivos acima + imagens/
└── imagens/                   ← SÓ se a prova tiver imagens de conteúdo
    ├── imagem_001.jpg
    ├── imagem_002.png
    └── ...
```

Regras das imagens:

- Nome **sempre** `imagem_00N` (3 dígitos, sequencial: `imagem_001`, `imagem_002`...), mantendo a extensão original (`.jpg`, `.png`).
- No Markdown, referência **relativa**: `![Imagem da questão](imagens/imagem_001.jpg)`.
- A mesma imagem usada em várias questões = **mesmo arquivo físico, referências repetidas** no Markdown. Nunca duplique o arquivo.
- Provas sem imagens de conteúdo ficam **sem** a pasta `imagens/` (uma `imagens/.gitkeep` vazia também é aceitável).
- Logos e marcas d'água repetidos (ex.: logo da banca em todas as páginas, `pcimarkpci`) **não** são imagens de conteúdo — descarte.

### 1.4. Estrutura fixa de `prova_organizada.md`

```markdown
# PROVA — [NOME OU IDENTIFICAÇÃO]

## 1. Análise geral da prova
- Identificação, quantidade total de questões, textos de apoio, imagens,
  gráficos/tabelas, grupos identificados, questões independentes.
- Tabela do gabarito (quando houver).
- Transcrição INTEGRAL da capa/instruções (blockquote).

## 2. Questões agrupadas
### GRUPO 01 — [IDENTIFICAÇÃO DO MATERIAL COMPARTILHADO]
**Questões relacionadas:** 01, 02 e 03.

#### QUESTÃO 01
✅ **Gabarito: X** (origem do gabarito)
**Material de apoio:**
(texto-base INTEGRAL — repetido em cada questão do grupo)
**Enunciado:**
(conteúdo integral)
**Alternativas:**
A) ...
B) ...
C) ...
D) ...
E) ...
**Referências visuais:**
![Imagem da questão](imagens/imagem_001.jpg)

## 3. Questões independentes
(mesma estrutura interna, uma questão após a outra)

## 4. Observações e limitações da extração
```

### 1.5. Regras de conteúdo (INEGOCIÁVEIS)

1. **NÃO resumir, omitir, simplificar, encurtar ou adaptar NADA.** Enunciados, alternativas A–E (todas as que existirem), textos de apoio completos, fórmulas, tabelas, notas de rodapé, instruções da capa: tudo 100%.
2. **Cada questão é autossuficiente**: o material compartilhado (texto, imagem, tabela, situação-problema) aparece **repetido integralmente dentro de cada questão** do grupo. Teste: se uma questão for lida isoladamente por outra IA, ela deve ter tudo o que precisa. **Toda imagem extraída deve estar referenciada dentro da(s) questão(ões) que a usam** — imagem salva em `imagens/` mas sem referência no Markdown é bug (o validador acusa como "imagem órfã").
3. Gabarito por questão: `✅ **Gabarito: X** (gabarito oficial pareado)`; anulada: `⚠️ **Gabarito: ANULADA**` (também quando o gabarito oficial usa `#` ou `X`); V/F: `✅ **Gabarito: V**`; sem gabarito: `⚠️ **Gabarito: oficial não disponível**`.
4. Numeração original preservada; ordem original preservada; nada de "texto conforme original" ou "demais informações omitidas".
5. Se algo estiver ilegível, registre **onde** está o problema na seção 4 — nunca invente conteúdo.

### 1.6. Estrutura de `relatorio_analise.md`

```markdown
# Relatório de análise — [NOME DA PROVA]

## Resumo
- Questões identificadas, grupos, questões agrupadas, independentes,
  imagens extraídas, situação do gabarito.

| Material compartilhado | Questões vinculadas | Tipo |
|---|---|---|
| Texto-base compartilhado (questões 01 a 10) | 01, 02, ..., 10 | Texto |
| Imagem 01 (tirinha) | 09 | Imagem |
```

A tabela deve refletir **exclusivamente** o que existe na prova.

---

## PARTE 2 — PASSO A PASSO COM A FERRAMENTA

### Passo 1 — Preparar os PDFs

1. Crie uma pasta de trabalho, ex.: `C:\provas\pdfs`.
2. Coloque nela os PDFs: a **prova** e, se tiver, o **gabarito**.
   - O pareamento é automático pela semelhança do nome (`Prova - ...` ↔ `Gabarito - ...`). Mantenha os nomes dos arquivos pareados.
   - Se o gabarito tiver vários cargos, a ferramenta escolhe o bloco do cargo declarado na capa da prova (ex.: `CARGO: 2.03 - CERIMONIALISTA`).
3. Confira se o PDF da prova tem **texto selecionável** (abra e tente selecionar com o mouse):
   - ✅ Tem texto → siga para o Passo 2.
   - ❌ Não tem (escaneado) → faça OCR antes:
     ```
     pip install ocrmypdf
     ocrmypdf prova_escaneada.pdf prova.pdf
     ```

### Passo 2 — Instalar a ferramenta (uma vez só)

1. Instale o Python: https://www.python.org/downloads/ (marque **"Add Python to PATH"**).
2. No Prompt de Comando (Windows) ou Terminal:
   ```
   pip install pymupdf
   ```

### Passo 3 — Rodar a ferramenta

```
python organizador_provas.py --pasta C:\provas\pdfs --saida C:\provas\saida
```

- Várias provas na mesma pasta: ela processa todas, cada uma na sua subpasta.
- Uma prova só: force o nome correto da pasta (recomendado):
  ```
  python organizador_provas.py --pasta C:\provas\pdfs --saida C:\provas\saida --nome Camara_Cidade_2024_Cargo
  ```
- Se você clonou o repositório, pode copiar direto para `Provas MD/`:
  ```
  python organizador_provas.py --pasta C:\provas\pdfs --saida C:\provas\saida --repo C:\caminho\do\provas_md
  ```

### Passo 4 — Conferir a saída (CHECKLIST OBRIGATÓRIO)

Primeiro, rode o **validador automático** (incluído nesta pasta):

```
python validar_prova.py --pasta C:\provas\saida
```

Ele verifica arquivos obrigatórios, seções do Markdown, numeração das questões, alternativas, gabaritos e referências de imagens. **Saída sem "ERROS" é pré-requisito para publicar.** Depois, confira manualmente:

- [ ] A pasta tem o nome no padrão `<Origem>_<Cidade>_<Ano>_<Cargo>` (se não, renomeie).
- [ ] Contém `prova_organizada.md`, `relatorio_analise.md` e `PROVA_ORGANIZADA.zip`.
- [ ] O número de questões no `.md` é igual ao da prova original (conte os `#### QUESTÃO`).
- [ ] Todas as alternativas de cada questão estão lá (compare algumas questões aleatórias com o PDF).
- [ ] As questões agrupadas têm o texto-base **repetido** dentro de cada uma.
- [ ] As imagens existem em `imagens/` com nome `imagem_00N` e as referências no `.md` apontam para elas (abra o `.md` num visualizador Markdown).
- [ ] O gabarito confere com o PDF de gabarito (confira pelo menos 5 respostas espalhadas).
- [ ] O ZIP contém os 2 arquivos + `imagens/`.
- [ ] Nada foi resumido: leia a capa transcrita e compare com a capa do PDF.

**Se algo falhar, NÃO publique com erro.** Veja a Parte 3.

### Passo 5 — Publicar no repositório

Se você clonou o repositório (https://github.com/tonnyrox/provas_md):

```
cd provas_md
git add -A
git commit -m "Adiciona prova organizada: Camara_<Cidade>_<Ano>_<Cargo>"
git push origin main
```

Se você NÃO usa git: entregue a(s) pasta(s) geradas (com o ZIP dentro) para o dono do repositório fazer o upload via GitHub ("Add file → Upload files", dentro de `Provas MD/`).

---

## PARTE 3 — QUANDO A FERRAMENTA NÃO BASTA

> **🧯 Leia o manual de campo: [`GARGALOS_E_SOLUCOES.md`](GARGALOS_E_SOLUCOES.md)** — ele documenta TODOS os problemas reais já resolvidos neste repositório (PDF escaneado, marcas d'água, linhas mescladas, gabaritos multi-cargo e retificados, gabarito indisponível, metadados errados no nome do arquivo, questões anuladas/discursivas, imagens a descartar, provas fora do padrão) com a solução testada e a prova de referência de cada caso.

A ferramenta é automática e resolve a maioria dos casos, mas pode falhar em:

| Situação | Sintoma | O que fazer |
|---|---|---|
| PDF escaneado | "nenhuma questão detectada" | Faça OCR e monte com o builder template [`exemplo_builder_ocr.py`](exemplo_builder_ocr.py) (detalhes no GARGALOS, Caso 1) |
| Grupo não detectado | Texto-base não repetido nas questões | Corrija manualmente o `.md` seguindo a seção 1.4/1.5 |
| Gabarito não interpretado | "gabarito pareado mas não interpretado" | Preencha o gabarito manualmente comparando com o PDF |
| Vários cargos sem código | Aviso no relatório | Identifique o cargo correto e selecione o bloco no PDF de gabarito |
| Imagem vinculada à questão errada | Imagem fora do lugar | Mova a referência `![...]` para dentro da questão certa |
| Nome do arquivo errado | Cargo/ano do arquivo difere da capa/gabarito | Vale o documento; corrija o nome da pasta (GARGALOS, Caso 5) |

Para provas complexas (muitas imagens, agrupamentos não declarados pela banca, discursivas), use a **IA com o prompt padrão**: o arquivo [`PROMPT_EXTRACAO.md`](PROMPT_EXTRACAO.md) desta pasta contém o prompt completo que deve ser enviado junto com os PDFs. O resultado da IA deve seguir **exatamente** o padrão da Parte 1 deste arquivo e ser validado com [`validar_prova.py`](validar_prova.py) antes de publicar.

---

## PARTE 4 — ERROS COMUNS (NÃO FAÇA ISSO)

- ❌ Criar pastas fora de `Provas MD/` (ex.: `provas/`, `novas_provas/`).
- ❌ Nomes de pasta com acentos, espaços ou minúsculas inconsistentes.
- ❌ Arquivos internos com nomes diferentes do padrão (`Prova_X_ORGANIZADA.md`, `q09_tirinha.jpg`).
- ❌ Texto-base colocado só na primeira questão do grupo.
- ❌ Resumir textos longos "para facilitar".
- ❌ Publicar sem o `relatorio_analise.md` ou sem o ZIP.
- ❌ Duplicar o arquivo de imagem para repetir em várias questões.
- ❌ Inventar gabarito, ano, cargo ou qualquer informação que não esteja no documento.

Em caso de dúvida, abra uma prova existente em `Provas MD/` (ex.: `Camara_Brusque_2024_Agente_Administrativo_Recepcao/`) e copie o formato.
