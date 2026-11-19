# 🎯 Fluxo de Trabalho — Manutenção do Acervo de Provas

Este documento descreve o **fluxo de trabalho padrão** para:
1. Adicionar novas provas ao acervo
2. Manter a qualidade das provas existentes
3. Corrigir problemas identificados
4. Auditar o acervo periodicamente

---

## 📥 1. RECEBIMENTO E PREPARAÇÃO

### 1.1. Receber os PDFs
- Verifique se o PDF está íntegro (número de páginas correto)
- Identifique: Instituição, Cidade, Ano, Cargo
- Crie pasta no formato: `Camara_<Cidade>_<Ano>_<Cargo>`

### 1.2. Verificar duplicidade
Antes de processar, verifique se a prova já existe:
```bash
cd Provas MD
# Verificar se pasta já existe
ls | grep -i "Camara_<Cidade>_<Ano>"
```

**REGRA**: Nunca processe uma prova que já exista sem verificar se é uma nova versão/ano!

---

## 📝 2. EXTRAÇÃO E ORGANIZAÇÃO

### 2.1. Extrair o conteúdo
Use o **PROMPT_EXTRACAO.md** para orientar a IA na extração:
- 100% do conteúdo original
- Questões agrupadas com material repetido
- Imagens extraídas e referenciadas
- Gabarito por questão

### 2.2. Estrutura obrigatória
```
Camara_<Cidade>_<Ano>_<Cargo>/
├── prova_organizada.md    # Prova completa
├── relatorio_analise.md   # Análise da estrutura
├── PROVA_ORGANIZADA.zip   # ZIP com os arquivos
└── imagens/              # Só se houver imagens
    ├── imagem_001.jpg
    └── imagem_002.png
```

### 2.3. Nomenclatura de imagens
- **Formato**: `imagem_00N.ext` (3 dígitos, sequencial)
- **Referência**: `![Imagem](imagens/imagem_001.jpg)`
- **Regra**: Mesma imagem em várias questões = mesmo arquivo, referências repetidas

---

## ✅ 3. VALIDAÇÃO ANTES DA PUBLICAÇÃO

### 3.1. Validar prova específica
```bash
python ferramenta/validar_prova.py --pasta "Provas MD/Camara_<Cidade>_<Ano>_<Cargo>"
```

O validador verifica:
- ✅ Estrutura de arquivos
- ✅ Formato do markdown
- ✅ Questões autossuficientes
- ✅ Imagens referenciadas
- ✅ ZIP contendo os arquivos corretos

### 3.2. Corrigir problemas comuns

**Problema**: ZIP sem arquivos
```bash
python ferramenta/corrigir_zips.py
```

**Problema**: Resíduos de numeração de página
```bash
python ferramenta/limpar_residuos_pagina.py
```

---

## 🔍 4. AUDITORIA PERIÓDICA

### 4.1. Auditoria completa do acervo
```bash
python ferramenta/auditor_completo.py
```

Este script verifica **TODAS** as 122 provas:
- Estrutura de pastas
- Arquivos obrigatórios
- Questões agrupadas
- Imagens referenciadas
- ZIPs corretos
- Resíduos de formatação

### 4.2. Interpretação dos resultados

| Status | Ação |
|--------|------|
| ✅ **OK** | Nada a fazer |
| ⚠️ **AVISO** | Verificar manualmente (normalmente resíduos de formatação) |
| ❌ **ERRO** | Corrigir obrigatoriamente |

### 4.3. Ações após auditoria

1. **Provas com ERRO**: Corrigir imediatamente
2. **Provas com AVISO**: Verificar manualmente
3. **Provas OK**: Manter monitoramento

---

## 🛠️ 5. MANUTENÇÃO E CORREÇÕES

### 5.1. Corrigir ZIPs
```bash
python ferramenta/corrigir_zips.py
```
Regenera ZIPs das provas com problemas.

### 5.2. Limpar resíduos de página
```bash
python ferramenta/limpar_residuos_pagina.py
```
Remove numeração de página do PDF que ficou no markdown.

### 5.3. Auditoria estrutural
```bash
python ferramenta/auditor_estrutural.py
```
Verifica apenas a estrutura do markdown (sem verificar ZIPs e imagens).

---

## 📊 6. VERIFICAÇÃO MANUAL (AMOSTRAL)

### 6.1. O que verificar manualmente

Para cada prova, especialmente as com avisos:

1. **Questões agrupadas**: 
   - Material compartilhado (texto/imagem) está repetido em CADA questão?
   - Cada questão funciona isoladamente?

2. **Imagens**:
   - Todas as imagens referenciadas existem em `imagens/`?
   - Imagens estão com nome padronizado (`imagem_00N.ext`)?
   - Mesma imagem em várias questões = mesmo arquivo físico?

3. **ZIP**:
   - Contém `prova_organizada.md`?
   - Contém `relatorio_analise.md`?
   - Contém pasta `imagens/` (se aplicável)?

4. **Conteúdo**:
   - Nenhum resumo ou omissão?
   - Gabarito por questão está marcado?
   - Instruções da capa estão transcritas?

### 6.2. Checklist de verificação manual

- [ ] Abrir `prova_organizada.md` em um editor de markdown
- [ ] Verificar seção "2. Questões agrupadas"
- [ ] Verificar seção "3. Questões independentes"
- [ ] Confirmar que cada questão tem todo o material necessário
- [ ] Abrir ZIP e verificar arquivos
- [ ] Abrir pasta `imagens/` e contar arquivos

---

## 📈 7. STATUS ATUAL DO ACERVO

| Métrica | Valor | Status |
|---------|-------|--------|
| Total de provas | 122 | ✅ |
| Provas OK | 112 | ✅ (91.8%) |
| Provas com avisos | 10 | ⚠️ (8.2%) |
| Provas com erros | 0 | ✅ |
| Imagens totais | 679 | ✅ |

**Provas com avisos** (resíduos de formatação, sem impacto funcional):
- Camara_Alto_Paraiso_2024_Agente_Administrativo
- Camara_Americana_2024_Analista_de_Comunicacao
- Camara_Araraquara_2016_Assistente_de_Cerimonial
- Camara_Araripina_2020_Agente_Administrativo_Grupo_02
- Camara_Araripina_2024_Agente_Administrativo
- Camara_Calumbi_2024_Agente_Administrativo
- Camara_Ouro_Preto_do_Oeste_2024_Agente_Administrativo
- Camara_Sao_Luiz_do_Paraitinga_2015_Analista_de_Comunicacao

**Status**: 🟡 **QUASE PERFEITO** - Apenas avisos de formatação

---

## 🎯 8. OBJETIVO FINAL

Manter **100%** das provas no padrão:
- ✅ Estrutura correta
- ✅ Questões autossuficientes
- ✅ Imagens corretamente referenciadas
- ✅ ZIPs completos
- ✅ Sem omissões ou resumos
- ✅ Pronto para uso público

---

## 📚 9. DOCUMENTAÇÃO DE REFERÊNCIA

| Documento | Descrição |
|-----------|-----------|
| [INSTRUCOES.md](INSTRUCOES.md) | Manual completo de organization |
| [PROMPT_EXTRACAO.md](PROMPT_EXTRACAO.md) | Prompt oficial para extração com IA |
| [GARGALOS_E_SOLUCOES.md](GARGALOS_E_SOLUCOES.md) | Problemas reais e soluções |
| [validar_prova.py](validar_prova.py) | Validador de provas |
| [auditor_estrutural.py](auditor_estrutural.py) | Auditor de estrutura |
| [auditor_completo.py](auditor_completo.py) | Auditor completo do acervo |
| [corrigir_zips.py](corrigir_zips.py) | Corretor de ZIPs |
| [limpar_residuos_pagina.py](limpar_residuos_pagina.py) | Limpador de resíduos |

---

## ✨ 10. BOAS PRÁTICAS

1. **Sempre valide antes de publicar**
2. **Execute auditoria completa periodicamente**
3. **Corrija erros imediatamente**
4. **Documente problemas e soluções**
5. **Mantenha o padrão consistente**
6. **Nunca resuma ou omita conteúdo**
7. **Sempre faça backup antes de correções em lote**

---

**Versão**: 1.0  
**Última atualização**: 2024  
**Responsável**: Gestor do Acervo de Provas
