# 📚 provas_md — Provas de concursos públicos organizadas em Markdown

Repositório central de provas de concursos públicos (Câmaras e Prefeituras Municipais brasileiras), extraídas integralmente de PDFs e reorganizadas em Markdown, com questões autossuficientes e material de apoio repetido em cada questão.

## Estrutura

```
provas_md/
├── Provas MD/      ← TODAS as provas (um diretório único, sem duplicação)
│   └── Camara_<Cidade>_<Ano>_<Cargo>/
│       ├── prova_organizada.md
│       ├── relatorio_analise.md
│       ├── PROVA_ORGANIZADA.zip
│       └── imagens/            (somente quando há imagens de conteúdo)
│           └── imagem_001.jpg ...
└── ferramenta/     ← ferramenta + instruções para organizar novas provas
    ├── INSTRUCOES.md        ← manual completo passo a passo (LEIA PRIMEIRO)
    ├── PROMPT_EXTRACAO.md   ← prompt oficial para extração com IA
    ├── GARGALOS_E_SOLUCOES.md ← manual de campo: problemas reais e soluções
    ├── validar_prova.py     ← validador automático do padrão (rodar antes de publicar)
    ├── exemplo_builder_ocr.py ← template para provas escaneadas (OCR)
    ├── README.md            ← visão técnica da ferramenta
    └── organizador_provas.py
```

## O padrão (resumo)

- **Pasta da prova:** `<Origem>_<Cidade>_<Ano>_<Cargo>` (ex.: `Camara_Brusque_2024_Agente_Administrativo_Recepcao`).
- **Arquivos obrigatórios:** `prova_organizada.md` + `relatorio_analise.md` + `PROVA_ORGANIZADA.zip`; imagens em `imagens/imagem_00N.ext` com referências relativas.
- **Conteúdo:** 100% integral — nada é resumido, omitido ou simplificado.
- **Questões agrupadas:** o texto/imagem compartilhado é repetido integralmente dentro de **cada** questão do grupo, para que cada questão funcione isoladamente.
- **Estrutura do Markdown:** `1. Análise geral da prova` → `2. Questões agrupadas` → `3. Questões independentes` → `4. Observações e limitações da extração`.

## Como adicionar novas provas

Siga o manual completo em **[ferramenta/INSTRUCOES.md](ferramenta/INSTRUCOES.md)**: ele cobre desde a preparação dos PDFs até a publicação, incluindo o checklist de conferência obrigatório. Para provas complexas, use o prompt de extração em **[ferramenta/PROMPT_EXTRACAO.md](ferramenta/PROMPT_EXTRACAO.md)** e consulte o manual de campo **[ferramenta/GARGALOS_E_SOLUCOES.md](ferramenta/GARGALOS_E_SOLUCOES.md)** (problemas reais já resolvidos, com provas de referência).

### Ferramentas de validação e manutenção

| Ferramenta | Descrição | Uso |
|------------|-----------|-----|
| `validar_prova.py` | Valida o padrão de uma prova específica | `python ferramenta/validar_prova.py --pasta "Provas MD"` |
| `auditor_estrutural.py` | Audita a estrutura de todas as provas | `python ferramenta/auditor_estrutural.py` |
| `auditor_completo.py` | Auditoria completa (estrutura + arquivos + imagens + ZIPs) | `python ferramenta/auditor_completo.py` |
| `corrigir_zips.py` | Regenera ZIPs com problemas | `python ferramenta/corrigir_zips.py` |
| `limpar_residuos_pagina.py` | Remove resíduos de numeração de página do PDF | `python ferramenta/limpar_residuos_pagina.py` |

### Fluxo de trabalho recomendado

1. **Antes de publicar**: Rode `validar_prova.py` para verificar a prova específica
2. **Auditoria periódica**: Execute `auditor_completo.py` para verificar todo o acervo
3. **Correções automáticas**: Use `corrigir_zips.py` e `limpar_residuos_pagina.py` para problemas comuns
4. **Verificação manual**: Confira as provas com avisos geradas pela auditoria

## Status do Acervo

- **Total de provas**: 122
- **Provas OK**: 112/122 (91.8%)
- **Provas com avisos**: 10/122 (8.2%) - resíduos de formatação sem impacto funcional
- **Provas com erros**: 0

🎯 **Objetivo**: Manter 100% das provas no padrão, com todas as questões autossuficientes, imagens corretamente referenciadas e sem omissões.
