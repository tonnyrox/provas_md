#!/usr/bin/env python3
"""
Script para processar TODOS os IDs que ainda não estão no GitHub
E extrair o conteúdo real dos PDFs para os markdowns
"""

import os
import re
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Caminhos
BASE_LOCAL = Path(r"C:\Users\Tonny\Downloads\projeto_git_prova\000000 -OK")
FALTA_FAZER = BASE_LOCAL / "Falta_fazer"
BASE_GITHUB = Path(r"C:\Users\Tonny\Downloads\projeto_git_prova\provas_md\Provas MD")

# IDs já no GitHub
github_pastas = set(p.name for p in BASE_GITHUB.iterdir() if p.is_dir())

# Duplicidades conhecidas
DUPLICIDADES = {114: 113}

def extrair_texto_pdf(pdf_path):
    """Extrair texto de um PDF"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        texto = ""
        for page in reader.pages:
            if page.extract_text():
                texto += page.extract_text() + "\n\n"
        return texto.strip()
    except Exception as e:
        logger.error(f"Erro extraindo texto de {pdf_path}: {e}")
        return None

def identificar_prova_por_pdf(pasta_id):
    """Identificar prova a partir dos PDFs"""
    pdfs = list(pasta_id.glob('*.pdf'))
    if not pdfs:
        return None
    
    # Tentar ler o IDENTIFICACAO.txt
    ident_file = pasta_id / "IDENTIFICACAO.txt"
    if ident_file.exists():
        try:
            with open(ident_file, 'r', encoding='utf-8', errors='ignore') as f:
                conteudo = f.read()
            
            # Procurar por Prova: e Gabarito:
            prova_match = re.search(r'Prova:\s*(.+)', conteudo)
            if prova_match:
                prova_nome = prova_match.group(1).strip()
                return padronizar_nome(prova_nome)
        except:
            pass
    
    # Tentar extrair do nome do PDF
    for pdf in pdfs:
        nome = pdf.name
        # Remover Prova - , Gabarito - 
        nome = re.sub(r'(Prova|Gabarito)\s*-?\s*', '', nome, flags=re.IGNORECASE)
        nome = re.sub(r'\.pdf$', '', nome, flags=re.IGNORECASE)
        
        # Extrair ano
        anos = re.findall(r'\b(19|20)\d{2}\b', nome)
        ano = anos[0] if anos else '0000'
        
        # Tentar identificar orgão, cidade, cargo
        orgao = 'Camara'
        if 'prefeitura' in nome.lower():
            orgao = 'Prefeitura'
        elif 'camara' in nome.lower() or 'câmara' in nome.lower():
            orgao = 'Camara'
        
        # Limpar nome
        nome = re.sub(r'\s+', ' ', nome).strip()
        nome = re.sub(r'[^\w\s-]', '', nome)
        
        return padronizar_nome(f"{orgao}_{nome}_{ano}")
    
    return None

def padronizar_nome(nome):
    """Padronizar nome da pasta"""
    # Remover anos duplicados
    nome = re.sub(r'(_20\d{2}){2,}', r'\1', nome)
    nome = re.sub(r'(_19\d{2}){2,}', r'\1', nome)
    
    # Remover preposições
    nome = re.sub(r'_de_|_do_|_da_|_das_|_dos_|_em_|_a_|_o_|_para_', '_', nome)
    
    # Remover caracteres especiais
    nome = re.sub(r'[^\w-]', '', nome)
    
    # Remover underscores consecutivos
    nome = re.sub(r'__+', '_', nome)
    nome = nome.strip('_')
    
    # Capitalizar
    partes = nome.split('_')
    partes_cap = []
    lowercase_words = {'de', 'do', 'da', 'das', 'dos', 'em', 'a', 'o', 'e', 'ou'}
    for p in partes:
        if p and p.lower() in lowercase_words:
            partes_cap.append(p.lower())
        else:
            partes_cap.append(p.capitalize())
    
    return '_'.join(partes_cap)

def extrair_questoes(texto):
    """Extrair questões do texto (simplificado)"""
    # Esta é uma versão simplificada
    # Idealmente, precisaria de um parser mais sofisticado
    
    # Procurar por padrões como "01)", "1.", "Questão 1", etc.
    pattern = r'(\d{1,3})[\.\)]\s*([A-Z\n]|[^\n]+)'
    
    questoes = []
    for match in re.finditer(pattern, texto):
        num = match.group(1)
        texto_questao = match.group(2).strip()
        questoes.append((num, texto_questao))
    
    return questoes

def criar_prova_organizada(pasta_id, nome_pasta, texto_prova):
    """Criar arquivo prova_organizada.md com conteúdo real"""
    
    # Extrair metadados
    metadados = {
        'instituição': 'Câmara Municipal',
        'cidade': 'Desconhecida',
        'ano': '0000',
        'cargo': 'Desconhecido',
        'banca': 'N/I',
        'data': 'N/I'
    }
    
    # Tentar extrair do texto
    if texto_prova:
        # Procurar por padroes
        cidade_match = re.search(r'[Cc]âmara [Mm]unicipal de ([A-Z][^\n]+)', texto_prova)
        if cidade_match:
            metadados['cidade'] = cidade_match.group(1)
            metadados['instituição'] = 'Câmara Municipal'
        
        ano_match = re.findall(r'\b(19|20)\d{2}\b', texto_prova)
        if ano_match:
            metadados['ano'] = ano_match[0]
    
    # Criar conteúdo
    conteudo = f"""# {nome_pasta}

## Identificação

- **Instituição**: {metadados['instituição']}
- **Cidade**: {metadados['cidade']}
- **Ano**: {metadados['ano']}
- **Cargo**: {metadados['cargo']}
- **Banca**: {metadados['banca']}
- **Data**: {metadados['data']}
- **Número de Questões**: 0

## Instruções

{texto_prova[:500]}...

## Questões

"""
    
    # Adicionar questões (simplificado)
    questoes = extrair_questoes(texto_prova)
    for num, texto in questoes[:10]:  # Primeiras 10 para teste
        conteudo += f"\n### Questão {num}\n\n{texto}\n\n---\n"
    
    conteudo += f"""
---

*Processado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Extração automática de conteúdo*"""
    
    return conteudo

def processar_um_id(pasta_id):
    """Processar um único ID"""
    logger.info(f"\nProcessando: {pasta_id.name}")
    
    # Verificar se é duplicidade
    id_num = pasta_id.name.split(' ID')[0].strip()
    if id_num.isdigit() and int(id_num) in DUPLICIDADES:
        logger.info(f"⏭️  {pasta_id.name} é duplicidade, pulando")
        return None
    
    # Identificar nome da prova
    nome_pasta = identificar_prova_por_pdf(pasta_id)
    if not nome_pasta:
        logger.error(f"❌ Não foi possível identificar {pasta_id.name}")
        return None
    
    logger.info(f"Nome: {nome_pasta}")
    
    # Verificar se já existe no GitHub
    if nome_pasta in github_pastas:
        logger.info(f"⏭️  {nome_pasta} já existe, pulando")
        return None
    
    # Extrair texto do PDF
    pdfs = list(pasta_id.glob('*.pdf'))
    if not pdfs:
        logger.error(f"❌ Sem PDFs em {pasta_id.name}")
        return None
    
    # Usar o primeiro PDF que não é gabarito
    pdf_prova = None
    for pdf in pdfs:
        if 'gabarito' not in pdf.name.lower():
            pdf_prova = pdf
            break
    
    if not pdf_prova:
        pdf_prova = pdfs[0]  # Usar o primeiro
    
    texto = extrair_texto_pdf(pdf_prova)
    
    if not texto:
        logger.warning(f"⚠️  Não foi possível extrair texto de {pdf_prova.name}")
        # Usar template padrao
        texto = "Conteúdo não extraído automaticamente"
    
    # Criar pasta de destino
    pasta_destino = BASE_GITHUB / nome_pasta
    pasta_destino.mkdir(parents=True, exist_ok=True)
    pasta_imagens = pasta_destino / "imagens"
    pasta_imagens.mkdir(exist_ok=True)
    
    # Criar prova_organizada.md
    md_conteudo = criar_prova_organizada(pasta_id, nome_pasta, texto)
    with open(pasta_destino / "prova_organizada.md", 'w', encoding='utf-8') as f:
        f.write(md_conteudo)
    logger.info(f"✅ prova_organizada.md criado")
    
    # Criar relatorio_analise.md
    relatorio = f"""# Relatório de Análise - {nome_pasta}

## Informações Básicas

- **ID Original**: {pasta_id.name}
- **Pasta Local**: {pasta_id}
- **Arquivos Processados**: {len(pdfs)} PDF(s)
- **Conteúdo Extraído**: {'Sim' if texto else 'Não'}

## Verificação de Duplicidade

- [ ] Prova já cadastrada no GitHub
- [ ] Duplicidade confirmada
- [x] Nova prova processada

## Próximos Passos

1. [x] Extração de conteúdo
2. [ ] Revisão manual do conteúdo extraído
3. [ ] Correção de formatação
4. [ ] Validação final

---

*Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    with open(pasta_destino / "relatorio_analise.md", 'w', encoding='utf-8') as f:
        f.write(relatorio)
    logger.info(f"✅ relatorio_analise.md criado")
    
    # Criar PROVA_ORGANIZADA.zip (SEM os PDFs, apenas os markdowns)
    zip_path = pasta_destino / "PROVA_ORGANIZADA.zip"
    with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Adicionar apenas os markdowns
        zipf.write(str(pasta_destino / "prova_organizada.md"), "prova_organizada.md")
        zipf.write(str(pasta_destino / "relatorio_analise.md"), "relatorio_analise.md")
    logger.info(f"✅ PROVA_ORGANIZADA.zip criado")
    
    # Copiar outros arquivos (IDENTIFICACAO.txt, etc.)
    for file in pasta_id.iterdir():
        if file.is_file() and not file.name.lower().endswith('.pdf'):
            try:
                shutil.copy2(str(file), str(pasta_destino / file.name))
            except:
                pass
    
    logger.info(f"✅ {pasta_id.name} processado!")
    return nome_pasta

def main():
    """Função principal"""
    global github_pastas
    
    logger.info("="*80)
    logger.info("PROCESSANDO IDS FALTANTES")
    logger.info("="*80)
    
    # Coletar IDs não processados
    ids_para_processar = []
    
    # IDs em Falta_fazer
    for remessa in sorted(FALTA_FAZER.iterdir()):
        if remessa.is_dir() and remessa.name.startswith('remessa_'):
            for id_folder in sorted(remessa.iterdir()):
                if id_folder.is_dir():
                    pdfs = list(id_folder.glob('*.pdf'))
                    if pdfs:
                        ids_para_processar.append(id_folder)
    
    # IDs no nível raiz
    for item in sorted(BASE_LOCAL.iterdir()):
        if item.is_dir() and 'ID' in item.name:
            pdfs = list(item.glob('*.pdf'))
            if pdfs:
                ids_para_processar.append(item)
    
    logger.info(f"IDs para processar: {len(ids_para_processar)}")
    
    # Processar cada ID
    processadas = []
    erros = []
    
    for i, pasta_id in enumerate(ids_para_processar, 1):
        try:
            resultado = processar_um_id(pasta_id)
            if resultado:
                processadas.append(resultado)
            else:
                erros.append(pasta_id.name)
            
            pendentes = len(ids_para_processar) - i
            logger.info(f"\nProgresso: {i}/{len(ids_para_processar)} | {pendentes} pendentes | {len(erros)} erros")
            
            # Parar após 50 para teste
            if i >= 50:
                logger.info("\n⚠️  Parando após 50 para teste")
                break
                
        except Exception as e:
            logger.error(f"❌ Erro processando {pasta_id.name}: {e}")
            erros.append(pasta_id.name)
    
    # Resumo
    logger.info("\n" + "="*80)
    logger.info("RESUMO FINAL")
    logger.info("="*80)
    logger.info(f"Processadas: {len(processadas)}")
    logger.info(f"Erros: {len(erros)}")
    
    if processadas:
        logger.info(f"\nProcessadas:")
        for p in processadas:
            logger.info(f"  - {p}")

if __name__ == "__main__":
    main()
