# 🛠️ Ferramenta: Organizador de Provas (PDF → Markdown no padrão do repositório)

> **📖 DOCUMENTAÇÃO DESTA PASTA (leia nesta ordem):**
>
> 1. **[INSTRUCOES.md](INSTRUCOES.md)** — manual completo passo a passo: o padrão obrigatório das provas, como preparar os PDFs, rodar a ferramenta, conferir a saída (checklist), publicar no repositório e o que fazer quando a ferramenta não bastar.
> 2. **[PROMPT_EXTRACAO.md](PROMPT_EXTRACAO.md)** — o prompt oficial de extração integral, para usar com IA em provas complexas (escaneadas, agrupamentos não declarados, muitas imagens).
> 3. **[GARGALOS_E_SOLUCOES.md](GARGALOS_E_SOLUCOES.md)** — manual de campo com TODOS os problemas reais já resolvidos neste repositório (PDF escaneado/OCR, marcas d'água, gabaritos multi-cargo, metadados errados no nome do arquivo, questões anuladas/discursivas, imagens, validação) e as provas de referência de cada caso.
> 4. **[validar_prova.py](validar_prova.py)** — validador automático do padrão. Rodar SEMPRE antes de publicar: `python validar_prova.py --pasta "Provas MD"`.
> 5. **[exemplo_builder_ocr.py](exemplo_builder_ocr.py)** — template de código para montar provas a partir de OCR (PDF escaneado) usando a ferramenta como biblioteca.
> 6. **[README.md](README.md)** (este arquivo) — visão técnica da ferramenta.

> Quem for processar e subir provas deve seguir **obrigatoriamente** o padrão descrito na Parte 1 do `INSTRUCOES.md` — assim todas as pastas de `Provas MD/` ficam idênticas, independentemente de quem organizou.

Automatiza em lote a organização de provas: lê os PDFs de uma pasta (pareando automaticamente **Prova + Gabarito** pelo nome do arquivo), extrai texto e imagens, detecta as questões e os **textos-base agrupados**, e gera cada prova **exatamente no padrão de `Provas MD/`**.

---

## 📐 O PADRÃO DO REPOSITÓRIO (regra para humanos e IAs)

Toda prova deste repositório — feita manualmente ou por esta ferramenta — deve seguir **obrigatoriamente** esta estrutura:

### 1. Pasta da prova

Nome no formato `<Origem>_<Cidade>_<Ano>_<Cargo>`, com iniciais maiúsculas e separador `_`:

```
Camara_Brusque_2024_Agente_Administrativo_Recepcao/
Prefeitura_Bom_Jesus_e_Camara_Sao_Tome_2022_Agente_Administrativo/
```

### 2. Arquivos obrigatórios dentro da pasta

```
Camara_<Cidade>_<Ano>_<Cargo>/
├── prova_organizada.md        ← prova completa reorganizada
├── relatorio_analise.md       ← análise da estrutura e tabela de relacionamentos
├── PROVA_ORGANIZADA.zip       ← zip contendo os 2 arquivos + imagens/
└── imagens/                   ← somente se a prova tiver imagens de conteúdo
    ├── imagem_001.jpg
    ├── imagem_002.png
    └── ...
```

- Nomenclatura de imagens **sempre** `imagem_00N` (3 dígitos, sequencial), mantendo a extensão original (`.jpg`, `.png`...).
- Referência relativa no Markdown: `![Imagem da questão](imagens/imagem_001.jpg)`.
- A mesma imagem pode ser referenciada em várias questões (não duplicar o arquivo físico).
- Provas sem imagens de conteúdo ficam **sem** a pasta `imagens/` (uma `imagens/.gitkeep` vazia também é aceitável).

### 3. Estrutura fixa de `prova_organizada.md`

```markdown
# PROVA — [NOME OU IDENTIFICAÇÃO]

## 1. Análise geral da prova
   (identificação, totais de questões/textos/imagens/grupos, gabarito em tabela
    e a transcrição INTEGRAL da capa/instruções)

## 2. Questões agrupadas
### GRUPO 01 — [IDENTIFICAÇÃO DO MATERIAL COMPARTILHADO]
**Questões relacionadas:** 01, 02 e 03.
#### QUESTÃO 01
✅ **Gabarito: X** (quando houver gabarito oficial)
**Material de apoio:**      ← texto-base INTEGRAL, repetido em CADA questão do grupo
**Enunciado:**              ← conteúdo integral
**Alternativas:**           ← A) ... B) ... C) ... D) ... E) ... (todas as que existirem)
**Referências visuais:**    ← imagens da questão ou "Nenhuma."

## 3. Questões independentes
#### QUESTÃO NN  (mesma estrutura interna, sem material compartilhado)

## 4. Observações e limitações da extração
```

### 4. Regras de conteúdo (inegociáveis)

- **NÃO resumir, omitir, simplificar ou reduzir nada**: enunciados, alternativas, textos de apoio, fórmulas, tabelas, notas de rodapé e instruções da capa são reproduzidos 100%.
- **Cada questão é autossuficiente**: o material compartilhado (texto, imagem, tabela) é repetido integralmente dentro de cada questão do grupo — outra IA deve conseguir responder cada questão isoladamente.
- Gabarito oficial por questão: `✅ **Gabarito: X** (origem)`; questão anulada: `⚠️ **Gabarito: ANULADA**`; sem gabarito: `⚠️ **Gabarito: oficial não disponível**`.
- `relatorio_analise.md` termina com a tabela de relacionamentos:

  | Material compartilhado | Questões vinculadas | Tipo |
  |---|---|---|
  | Texto-base compartilhado (questões 01 a 10) | 01, 02, ..., 10 | Texto |

---

## ✅ Validação automática (obrigatória antes de publicar)

```
python validar_prova.py --pasta "Provas MD"            # valida todas as provas
python validar_prova.py --pasta "Provas MD/Camara_X_2024_Cargo"   # valida uma prova
```

Verifica: arquivos obrigatórios, seções do Markdown, numeração sequencial das questões, alternativas, consistência de gabaritos e referências de imagens. Saída 0 = pode publicar.

## ✅ O que a ferramenta faz

- Lê **todos os PDFs** de uma pasta de uma vez.
- **Pareia automaticamente** cada `Prova ...` com o seu `Gabarito ...` pela semelhança do nome.
- Em gabaritos com **vários cargos**, seleciona o bloco do cargo declarado na capa da prova (ex.: `CARGO: 2.03 - CERIMONIALISTA`) ou pelo **rótulo de cargo do próprio gabarito** (ex.: `MED - AGENTE ADMINISTRATIVO`).
- Parseia gabaritos com respostas **A–E, V/F (verdadeiro/falso), `#`/`X` (anulada)** — cada formato vira o indicativo correto por questão.
- Extrai o **texto** na ordem original e as **imagens de conteúdo** (descarta logos/marcas d'água repetidos), salvando como `imagens/imagem_00N.ext`.
- Detecta as questões (`Questão NN` / `NN.`) com filtro sequencial e separa **enunciado × alternativas** (A–E, maiúsculas ou minúsculas).
- Detecta avisos de texto-base ("o texto seguinte servirá de base...", "leia o texto abaixo para responder as questões de nº 01 à 10", "texto para as questões X a Y"...) e **repete o texto integralmente em cada questão do grupo**.
- Aceita o parâmetro `pos_texto` na `montar_prova` para transcrever **páginas finais após a última questão objetiva** (prova discursiva, rascunho, folha de texto) numa seção própria — sem contaminar a última questão (Belo Horizonte 2023).
- Gera `prova_organizada.md`, `relatorio_analise.md` (com a tabela de relacionamentos) e `PROVA_ORGANIZADA.zip` no padrão acima.

## 📥 Como instalar (uma vez só)

1. Instale o **Python**: https://www.python.org/downloads/ (marque **"Add Python to PATH"**).
2. No Prompt de Comando (Windows) ou Terminal (Mac/Linux):
   ```
   pip install pymupdf
   ```
3. Baixe este repositório (**Code → Download ZIP**) e descompacte.

## ▶️ Como usar

1. Coloque os PDFs numa pasta, por exemplo `C:\provas\pdfs` (pode mandar prova e gabarito juntos — o pareamento é automático).
2. Dentro da pasta `ferramenta`, rode:
   ```
   python organizador_provas.py --pasta C:\provas\pdfs --saida C:\provas\saida
   ```
   Para forçar o nome da pasta no padrão (recomendado quando é uma prova só):
   ```
   python organizador_provas.py --pasta C:\provas\pdfs --saida C:\provas\saida --nome Camara_Cidade_2024_Cargo
   ```
3. O resultado já sai no padrão do repositório, com ZIP pronto.
4. **(Opcional) Publicar direto no GitHub** — se você clonou este repositório:
   ```
   python organizador_provas.py --pasta C:\provas\pdfs --saida C:\provas\saida --repo C:\caminho\do\provas_md
   cd C:\caminho\do\provas_md
   git add -A
   git commit -m "Novas provas organizadas"
   git push
   ```

## ⚠️ Limitações importantes

- **PDFs escaneados** (sem texto selecionável) não funcionam com a ferramenta direta — faça OCR e monte com o builder template [`exemplo_builder_ocr.py`](exemplo_builder_ocr.py); o pipeline completo está no [`GARGALOS_E_SOLUCOES.md`](GARGALOS_E_SOLUCOES.md) (Caso 1).
- A extração é automática e literal: **sem a análise fina de uma revisão humana/IA** (vincular imagem à questão certa quando o aviso não existe, corrigir quebras de linha, conferir gabarito duvidoso). A detecção de grupos depende dos avisos padrão das bancas.
- Gabaritos em formatos muito incomuns podem não ser interpretados com confiança — nesse caso a ferramenta **não inventa respostas**: deixa sem gabarito e registra a limitação.

## 🧪 Testada com

- Câmara de Vereadores de Esteja/SC 2002 (Origem) — 25/25 questões, gabarito oficial 100% interpretado.
- Câmara de Votorantim/SP 2016 (FURB) — 40/40 questões, grupo do Hino de Votorantim (Q1–10) detectado com material repetido, gabarito do cargo 2.03 (Cerimonialista) selecionado automaticamente entre 6+ cargos do gabarito.
- PDF escaneado (sem texto) — tratado sem falha, com limitação registrada no relatório.

## 💡 Fluxo recomendado para lotes grandes

1. Rode a ferramenta no seu PC → tudo gerado em minutos, já no padrão.
2. Publique no repositório `provas_md` (pasta `Provas MD/`).
3. Para o **acabamento fino** de provas específicas (agrupamentos não declarados, imagens vinculadas, conferência integral contra o PDF), envie os PDFs para uma sessão de IA seguindo o PROMPT de extração integral — o resultado manual deve seguir **exatamente** o padrão descrito na seção "O PADRÃO DO REPOSITÓRIO" acima.
