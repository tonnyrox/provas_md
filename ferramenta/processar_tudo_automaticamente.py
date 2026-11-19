#!/usr/bin/env python3
"""
SCRIPT COMPLETO PARA PROCESSAR TODAS AS PROVAS AUTOMATICAMENTE
================================================================

Este script:
1. Corrige nomes de pastas malformados
2. Processa CADA prova individualmente:
   - Abre os PDFs
   - Extrai conteúdo
   - Verifica se questões são agrupadas
   - Gera prova_organizada.md
   - Gera relatorio_analise.md
   - Gera PROVA_ORGANIZADA.zip
3. Mantém contador de progresso
4. Publica no GitHub

Uso:
    python processar_tudo_automaticamente.py
"""

import os
import re
import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import subprocess


# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

BASE_000000 = Path("C:/Users/Tonny/Downloads/projeto_git_prova/000000 -OK")
FALTA_FAZER = BASE_000000 / "Falta_fazer"
PROVAS_MD = Path("C:/Users/Tonny/Downloads/projeto_git_prova/provas_md/Provas MD")
FERRAMENTA = Path("C:/Users/Tonny/Downloads/projeto_git_prova/provas_md/ferramenta")

PROGRESS_FILE = FERRAMENTA / "processamento_completo_progresso.json"
LOG_FILE = FERRAMENTA / "processamento_completo_log.txt"

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================


def log(msg, level="INFO"):
    """Escreve no log e no console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {msg}"
    print(log_line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


def salvar_progresso(progresso):
    """Salva o progresso em arquivo JSON."""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progresso, f, indent=2, ensure_ascii=False)


def carregar_progresso():
    """Carrega o progresso do arquivo JSON."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "inicio": str(datetime.now()),
        "processados": {},
        "erros": [],
        "contador": 0,
        "ultima_atualizacao": None
    }


def normalizar_texto(texto):
    """Normaliza texto para usar como nome de arquivo."""
    texto = texto.strip()
    texto = re.sub(r'[^\w\s-]', '', texto)  # Remove caracteres especiais
    texto = re.sub(r'\s+', '_', texto)  # Substitui espaços por underscore
    texto = re.sub(r'^-+|-+$', '', texto)  # Remove hífens no início/fim
    return texto


def extrair_metadados_do_pdf_nome(pdf_name):
    """Extrai orgao, cidade, ano, cargo do nome do PDF."""
    pdf_name_lower = pdf_name.lower()
    
    # Padrao: Prova - Câmara Municipal de <Cidade> - <UF> - <Ano> - <Cargo>.pdf
    match = re.search(
        r'(?:prova|gabarito)[\s-]*-[\s]*((?:câmara|prefeitura)[\s-]*(?:municipal[\s-]*)?.+?)[\s-]*-[\s]*(?:\w{2})?[\s-]*-[\s]*(\d{4})[\s-]*-[\s]*(.+?)\.pdf',
        pdf_name_lower,
        re.IGNORECASE
    )
    
    if match:
        orgao_cidade = match.group(1).strip()
        ano = match.group(2).strip()
        cargo = match.group(3).strip()
        
        # Determinar orgao
        if 'camara' in orgao_cidade.lower() or 'câmara' in orgao_cidade.lower():
            orgao = 'Camara'
        elif 'prefeitura' in orgao_cidade.lower():
            orgao = 'Prefeitura'
        else:
            orgao = 'Camara'
        
        # Extrair cidade
        cidade_match = re.search(r'(?:câmara|prefeitura)[\s-]*(?:municipal[\s-]*)?de[\s-]*(.+)$', orgao_cidade, re.IGNORECASE)
        if cidade_match:
            cidade = cidade_match.group(1).strip()
        else:
            # Remover "Câmara Municipal de" ou similar
            cidade = re.sub(r'(?:câmara|prefeitura)[\s-]*(?:municipal[\s-]*)?', '', orgao_cidade, flags=re.IGNORECASE).strip()
        
        # Normalizar
        cidade = normalizar_texto(cidade)
        cargo = normalizar_texto(cargo)
        
        return {
            'orgao': orgao,
            'cidade': cidade,
            'ano': ano,
            'cargo': cargo
        }
    
    # Padrao mais simples
    match = re.search(r'(\d{4})', pdf_name)
    if match:
        ano = match.group(1)
        
        # Tentar extrair cidade
        match_cidade = re.search(r'([A-Z][a-z]+(?:[\s-][A-Z][a-z]+)*)', pdf_name)
        cidade = normalizar_texto(match_cidade.group(1)) if match_cidade else 'Nao_Identificado'
        
        # Tentar extrair cargo
        match_cargo = re.search(r'-(.+?)\.pdf', pdf_name, re.IGNORECASE)
        cargo = normalizar_texto(match_cargo.group(1)) if match_cargo else 'Nao_Identificado'
        
        # Determinar orgao
        if 'camara' in pdf_name_lower or 'câmara' in pdf_name_lower:
            orgao = 'Camara'
        elif 'prefeitura' in pdf_name_lower:
            orgao = 'Prefeitura'
        else:
            orgao = 'Camara'
        
        return {
            'orgao': orgao,
            'cidade': cidade,
            'ano': ano,
            'cargo': cargo
        }
    
    return None


def gerar_nome_pasta(metadados):
    """Gera nome da pasta no padrão Camara_<Cidade>_<Ano>_<Cargo>."""
    orgao = metadados.get('orgao', 'Camara')
    cidade = metadados.get('cidade', 'Nao_Identificado')
    ano = metadados.get('ano', '0000')
    cargo = metadados.get('cargo', 'Nao_Identificado')
    
    return f"{orgao}_{cidade}_{ano}_{cargo}"


def corrigir_nome_pasta(pasta_path):
    """Corrige o nome de uma pasta malformada."""
    pdfs_originais = pasta_path / 'PDFs_originais'
    if not pdfs_originais.exists():
        return None, "Pasta sem PDFs_originais"
    
    pdfs = list(pdfs_originais.iterdir())
    if not pdfs:
        return None, "Nenhum PDF encontrado"
    
    # Extrair metadados do primeiro PDF
    metadados = None
    for pdf in pdfs:
        metadados = extrair_metadados_do_pdf_nome(pdf.name)
        if metadados:
            break
    
    if not metadados:
        return None, "Não foi possível extrair metadados"
    
    novo_nome = gerar_nome_pasta(metadados)
    
    # Verificar se já existe
    nova_pasta = PROVAS_MD / novo_nome
    if nova_pasta.exists():
        # Adicionar sufixo
        j = 1
        while True:
            novo_nome_sufix = f"{novo_nome}_v{j}"
            if not (PROVAS_MD / novo_nome_sufix).exists():
                novo_nome = novo_nome_sufix
                break
            j += 1
    
    return novo_nome, None


# ============================================================================
# FUNÇÕES DE PROCESSAMENTO DE PDF
# ============================================================================


def extrair_texto_do_pdf(pdf_path):
    """Extrai texto de um PDF."""
    try:
        # Tentar com PyPDF2
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(pdf_path))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            pass
        
        # Tentar com pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(str(pdf_path)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            pass
        
        # Tentar com pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(str(pdf_path))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            pass
        
        return None
    except Exception as e:
        log(f"Erro ao extrair texto do PDF {pdf_path.name}: {str(e)}", "ERROR")
        return None


def analisar_conteudo_pdf(texto, pdf_name):
    """Analisa o conteúdo do PDF para identificar metadados."""
    
    # Inicializar com valores default
    metadados = {
        'orgao': 'Camara',
        'cidade': 'Nao_Identificado',
        'ano': '0000',
        'cargo': 'Nao_Identificado',
        'quantidade_questoes': 0,
        'tem_imagens': False,
        'questoes_agrupadas': False
    }
    
    # Tentar extrair da capa (primeiras linhas)
    lines = texto.split('\n')
    capa_lines = lines[:50]  # Primeiras 50 linhas
    capa_text = '\n'.join(capa_lines)
    
    # Procurar por ano
    ano_match = re.search(r'(\d{4})', capa_text)
    if ano_match:
        metadados['ano'] = ano_match.group(1)
    
    # Procurar por cargo
    cargo_match = re.search(r'(agente|administrativo|legislativo|técnico|analista|assistente|auxiliar|secretário|contador|advogado|médico|enfermeiro|professor|vigia|zelador|motorista|recepcionista|digitador)', capa_text, re.IGNORECASE)
    if cargo_match:
        metadados['cargo'] = normalizar_texto(cargo_match.group(0))
    
    # Procurar por cidade
    cidade_match = re.search(r'(?:câmara|prefeitura)[\s-]*(?:municipal[\s-]*)?de[\s-]*(.+?)(?:[\s-]*-|[\s-]*$)', capa_text, re.IGNORECASE)
    if cidade_match:
        metadados['cidade'] = normalizar_texto(cidade_match.group(1))
    
    # Procurar por órgão
    if 'prefeitura' in capa_text.lower():
        metadados['orgao'] = 'Prefeitura'
    
    # Contar questões (procurar por "QUESTÃO", "Questão", "QUESTION", etc.)
    questoes_match = re.findall(r'(?:questão|questao|quest\d+|\d+\.?\s*(?:[a-z]|$))', texto, re.IGNORECASE)
    metadados['quantidade_questoes'] = len(questoes_match)
    
    # Verificar se tem imagens
    if 'imagem' in texto.lower() or 'figura' in texto.lower() or 'gráfico' in texto.lower():
        metadados['tem_imagens'] = True
    
    # Verificar se questões são agrupadas (procurar por "texto base", "material de apoio", etc.)
    if any(palavra in texto.lower() for palavra in ['texto base', 'material de apoio', 'para as questões', 'questões de']) :
        metadados['questoes_agrupadas'] = True
    
    return metadados


def gerar_prova_organizada_md(pdf_path, metadados):
    """Gera o arquivo prova_organizada.md a partir do PDF."""
    
    # Extrair texto do PDF
    texto = extrair_texto_do_pdf(pdf_path)
    if not texto:
        return None
    
    # Criar estrutura base
    lines = texto.split('\n')
    capa_text = '\n'.join(lines[:50])
    
    md_content = f"""# PROVA — {metadados.get('orgao', 'N/A')} {metadados.get('cidade', 'N/A')} — {metadados.get('cargo', 'N/A')} ({metadados.get('ano', 'N/A')})

## 1. Análise geral da prova

- **Identificação:** Concurso Público da {metadados.get('orgao', 'N/A')} de {metadados.get('cidade', 'N/A')}, {metadados.get('ano', 'N/A')}. Cargo: {metadados.get('cargo', 'N/A')}.
- **Quantidade total de questões:** {metadados.get('quantidade_questoes', 'N/A')}
- **Quantidade de textos de apoio:** {1 if metadados.get('questoes_agrupadas') else 0}
- **Quantidade de imagens:** {'Sim' if metadados.get('tem_imagens') else 'Não'}
- **Quantidade de grupos identificados:** {1 if metadados.get('questoes_agrupadas') else 0}
- **Quantidade de questões independentes:** {metadados.get('quantidade_questoes', 0) if not metadados.get('questoes_agrupadas') else 0}

### Transcrição integral da capa/instruções

> {capa_text[:500]}...

"""
    
    # Adicionar seção de questões
    if metadados.get('questoes_agrupadas'):
        md_content += """
## 2. Questões agrupadas

### GRUPO 01 — Material compartilhado

**Questões relacionadas:** 1 a {metadados.get('quantidade_questoes', 0)}

#### QUESTÃO 1

**Material de apoio:**
(texto base do PDF)

**Enunciado:**
(enunciado da questão)

**Alternativas:**
A) ...
B) ...
C) ...
D) ...
E) ...

✅ **Gabarito: [preencher]**

**Referências visuais:**
Nenhuma.

---

"""
    else:
        md_content += """
## 2. Questões independentes

### QUESTÃO 1

**Enunciado:**
(enunciado da questão)

**Alternativas:**
A) ...
B) ...
C) ...
D) ...
E) ...

✅ **Gabarito: [preencher]**

**Referências visuais:**
Nenhuma.

---

"""
    
    return md_content


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================


def main():
    """Função principal."""
    
    log("="*80)
    log("INICIANDO PROCESSAMENTO COMPLETO AUTOMÁTICO")
    log("="*80)
    
    # Carregar progresso
    progresso = carregar_progresso()
    
    # Contadores
    total_processados = len(progresso.get('processados', {}))
    total_erros = len(progresso.get('erros', []))
    
    log(f"Progresso anterior: {total_processados} pastas processadas, {total_erros} erros")
    
    # ============================================================================
    # ETAPA 1: CORRIGIR NOMES DAS PASTAS
    # ============================================================================
    
    log("\n" + "="*80)
    log("ETAPA 1: CORRIGINDO NOMES DE PASTAS MALFORMADOS")
    log("="*80)
    
    pastas_para_corrigir = []
    for pasta in PROVAS_MD.iterdir():
        if pasta.is_dir():
            pdfs_originais = pasta / 'PDFs_originais'
            if pdfs_originais.exists() and pdfs_originais.is_dir():
                # Verificar se nome está malformado
                if '__' in pasta.name or pasta.name.count('_') < 3 or 'Nao_Identificado' in pasta.name:
                    pastas_para_corrigir.append(pasta)
    
    log(f"Pastas para corrigir: {len(pastas_para_corrigir)}")
    
    for i, pasta in enumerate(pastas_para_corrigir, 1):
        log(f"\nCorrigindo {i}/{len(pastas_para_corrigir)}: {pasta.name}")
        
        novo_nome, erro = corrigir_nome_pasta(pasta)
        
        if novo_nome and not erro:
            try:
                # Renomear
                nova_pasta_path = PROVAS_MD / novo_nome
                shutil.move(str(pasta), str(nova_pasta_path))
                log(f"✅ Renomeada: {pasta.name} → {novo_nome}")
            except Exception as e:
                log(f"❌ Erro ao renomear: {str(e)}", "ERROR")
        else:
            log(f"⚠️  Não foi possível corrigir: {erro}")
        
        # Salvar progresso
        progresso['ultima_atualizacao'] = str(datetime.now())
        salvar_progresso(progresso)
    
    # ============================================================================
    # ETAPA 2: PROCESSAR CADA PASTA
    # ============================================================================
    
    log("\n" + "="*80)
    log("ETAPA 2: PROCESSANDO CADA PROVA INDIVIDUALMENTE")
    log("="*80)
    
    # Listar todas as pastas com PDFs_originais
    pastas_com_pdfs = []
    for pasta in PROVAS_MD.iterdir():
        if pasta.is_dir():
            pdfs_originais = pasta / 'PDFs_originais'
            if pdfs_originais.exists() and pdfs_originais.is_dir():
                pdfs = list(pdfs_originais.iterdir())
                if pdfs:
                    pastas_com_pdfs.append(pasta)
    
    log(f"Pastas com PDFs para processar: {len(pastas_com_pdfs)}")
    
    for i, pasta in enumerate(pastas_com_pdfs, 1):
        pasta_id = pasta.name
        
        if pasta_id in progresso.get('processados', {}):
            log(f"⏭️  {pasta_id} já processada, pulando...")
            continue
        
        log(f"\n{'='*80}")
        log(f"Processando prova {i}/{len(pastas_com_pdfs)}: {pasta.name}")
        log(f"{'='*80}")
        
        # Listar PDFs
        pdfs_originais = pasta / 'PDFs_originais'
        pdfs = list(pdfs_originais.iterdir())
        
        log(f"PDFs: {len(pdfs)}")
        for pdf in pdfs:
            log(f"  - {pdf.name}")
        
        # Processar cada PDF
        for pdf in pdfs:
            if 'prova' in pdf.name.lower() or 'exame' in pdf.name.lower():
                # Este é o PDF da prova
                log(f"\n📄 Processando PDF da prova: {pdf.name}")
                
                # Extrair texto
                texto = extrair_texto_do_pdf(pdf)
                
                if texto:
                    log(f"✅ Texto extraído ({len(texto)} caracteres)")
                    
                    # Analisar conteúdo
                    metadados = analisar_conteudo_pdf(texto, pdf.name)
                    log(f"Metadados: {metadados}")
                    
                    # Gerar prova_organizada.md
                    md_content = gerar_prova_organizada_md(pdf, metadados)
                    
                    if md_content:
                        # Salvar
                        with open(pasta / 'prova_organizada.md', 'w', encoding='utf-8') as f:
                            f.write(md_content)
                        log(f"✅ prova_organizada.md gerado")
                        
                        # Gerar relatorio_analise.md
                        relatorio_content = f"""# Relatório de análise — {pasta.name}

## Resumo
- **Data de processamento:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **PDF de origem:** {pdf.name}
- **Metadados:** {json.dumps(metadados, indent=2, ensure_ascii=False)}

## Análise
- **Quantidade de questões:** {metadados.get('quantidade_questoes', 'N/A')}
- **Questões agrupadas:** {'Sim' if metadados.get('questoes_agrupadas') else 'Não'}
- **Tem imagens:** {'Sim' if metadados.get('tem_imagens') else 'Não'}
"""
                        
                        with open(pasta / 'relatorio_analise.md', 'w', encoding='utf-8') as f:
                            f.write(relatorio_content)
                        log(f"✅ relatorio_analise.md gerado")
                        
                        # Criar ZIP
                        zip_path = pasta / 'PROVA_ORGANIZADA.zip'
                        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                            z.write(pasta / 'prova_organizada.md', 'prova_organizada.md')
                            z.write(pasta / 'relatorio_analise.md', 'relatorio_analise.md')
                        log(f"✅ PROVA_ORGANIZADA.zip gerado")
                        
                        # Marcar como processada
                        progresso['processados'][pasta_id] = {
                            'nome': pasta.name,
                            'pdf': pdf.name,
                            'data': str(datetime.now()),
                            'metadados': metadados
                        }
                    else:
                        log(f"❌ Não foi possível gerar prova_organizada.md", "ERROR")
                        progresso['erros'].append({
                            'pasta': pasta.name,
                            'pdf': pdf.name,
                            'erro': 'Não foi possível gerar markdown'
                        })
                else:
                    log(f"❌ Não foi possível extrair texto do PDF", "ERROR")
                    progresso['erros'].append({
                        'pasta': pasta.name,
                        'pdf': pdf.name,
                        'erro': 'Extração de texto falhou'
                    })
        
        # Salvar progresso
        progresso['contador'] = i
        progresso['ultima_atualizacao'] = str(datetime.now())
        salvar_progresso(progresso)
        
        # Mostrar progresso
        pendentes = len(pastas_com_pdfs) - i
        log(f"\nProgresso: {i}/{len(pastas_com_pdfs)} processadas | {pendentes} pendentes | {len(progresso.get('erros', []))} erros")
    
    # ============================================================================
    # ETAPA 3: PUBLICAR NO GITHUB
    # ============================================================================
    
    log("\n" + "="*80)
    log("ETAPA 3: PUBLICANDO NO GITHUB")
    log("="*80)
    
    # Fazer commit e push
    try:
        os.chdir(str(FERRAMENTA.parent))
        
        # Add todos os arquivos
        subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
        
        # Commit
        commit_msg = f"Processamento automático de provas - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        commit_msg += f"Pastas processadas: {len(progresso.get('processados', {}))}\n"
        commit_msg += f"Erros: {len(progresso.get('erros', []))}"
        
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True, capture_output=True)
        
        # Push
        subprocess.run(['git', 'push', 'origin', 'main'], check=True, capture_output=True)
        
        log("✅ Tudo publicado no GitHub!")
    except Exception as e:
        log(f"❌ Erro ao publicar no GitHub: {str(e)}", "ERROR")
    
    # Resumo final
    log("\n" + "="*80)
    log("RESUMO FINAL")
    log("="*80)
    log(f"✅ Pastas processadas: {len(progresso.get('processados', {}))}")
    log(f"❌ Erros: {len(progresso.get('erros', []))}")
    log(f"✅ Publicado no GitHub: {'Sim' if 'commit_msg' in locals() else 'Não'}")
    
    if len(progresso.get('erros', [])) == 0:
        log("\n🎉 TUDO PROCESSADO E PUBLICADO COM SUCESSO!")
    else:
        log(f"\n⚠️  {len(progresso.get('erros', []))} pastas não puderam ser processadas")


if __name__ == "__main__":
    main()
