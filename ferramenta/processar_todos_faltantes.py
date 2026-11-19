#!/usr/bin/env python3
"""
Script para processar TODOS os IDs que ainda não estão no GitHub
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

# Duplicidades conhecidas
DUPLICIDADES = {114: 113}

# Pastas já no GitHub
github_pastas = set(p.name for p in BASE_GITHUB.iterdir() if p.is_dir())

def extrair_texto_pdf(pdf_path):
    """Extrair texto de um PDF"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        texto = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                texto += page_text + "\n\n"
        return texto.strip()
    except Exception as e:
        logger.error(f"Erro extraindo texto de {pdf_path}: {e}")
        return None

def padronizar_nome_da_prova(pasta_id):
    """Padronizar nome da prova a partir da pasta ID"""
    
    # Verificar se tem IDENTIFICACAO.txt
    ident_file = pasta_id / "IDENTIFICACAO.txt"
    if ident_file.exists():
        try:
            with open(ident_file, 'r', encoding='utf-8', errors='ignore') as f:
                conteudo = f.read()
            
            # Procurar por Prova:
            prova_match = re.search(r'Prova:\s*(.+)', conteudo, re.IGNORECASE)
            if prova_match:
                nome = prova_match.group(1).strip()
                # Limpar
                nome = re.sub(r'\s+', ' ', nome)
                return padronizar_nome(nome)
        except:
            pass
    
    # Extrair do nome do PDF
    pdfs = list(pasta_id.glob('*.pdf'))
    for pdf in pdfs:
        if 'gabarito' not in pdf.name.lower():
            return padronizar_nome(pdf.name)
    
    # Se não encontrar, usar o nome da pasta
    return padronizar_nome(pasta_id.name)

def padronizar_nome(nome):
    """Padronizar nome"""
    # Remover .pdf
    nome = re.sub(r'\.pdf$', '', nome, flags=re.IGNORECASE)
    
    # Remover Prova -, Gabarito -, etc.
    nome = re.sub(r'(Prova|Gabarito|Concurso|Prefeitura|Câmara|Camara)\s*-?\s*', '', nome, flags=re.IGNORECASE)
    
    # Remover --, __, etc.
    nome = re.sub(r'--+|__+', '_', nome)
    nome = re.sub(r'[^\w-]', '_', nome)
    
    # Remover anos duplicados
    nome = re.sub(r'(_20\d{2}){2,}', r'\1', nome)
    nome = re.sub(r'(_19\d{2}){2,}', r'\1', nome)
    
    # Remover preposições isoladas
    nome = re.sub(r'_de_|_do_|_da_|_das_|_dos_|_em_|_a_|_o_|_para_|_por_', '_', nome)
    
    # Limpar
    nome = re.sub(r'\s+', '_', nome).strip('_')
    nome = re.sub(r'__+', '_', nome)
    
    # Capitalizar
    partes = nome.split('_')
    partes_cap = []
    lowercase_words = {'de', 'do', 'da', 'das', 'dos', 'em', 'a', 'o', 'e', 'ou', 'i', 'ii', 'iii', 'iv', 'v'}
    for p in partes:
        if p and p.lower() in lowercase_words:
            partes_cap.append(p.lower())
        else:
            partes_cap.append(p.capitalize())
    
    return '_'.join(partes_cap)

def gerar_prova_organizada(nome_pasta, texto, pasta_id):
    """Gerar conteúdo para prova_organizada.md"""
    
    # Tentar extrair metadados do texto
    metadados = {
        'instituição': 'Câmara Municipal',
        'cidade': 'Desconhecida',
        'ano': '0000',
        'cargo': 'Desconhecido',
        'banca': 'N/I',
        'data': 'N/I',
        'num_questoes': '0'
    }
    
    if texto:
        # Extrair ano
        anos = re.findall(r'\b(19|20)\d{2}\b', texto)
        if anos:
            metadados['ano'] = anos[0]
        
        # Extrair cidade
        cidades = re.findall(r'[Cc]âmara [Mm]unicipal de ([A-ZÂ-Ú][a-zã-ú]+(?: [a-zã-ú]+)*)', texto)
        if cidades:
            metadados['cidade'] = cidades[0]
        
        # Extrair cargo
        cargos = re.findall(r'Agente ([A-Z][a-z]+)|([A-Z][a-z]+) do Legislativo', texto)
        if cargos:
            metadados['cargo'] = cargos[0][0] or cargos[0][1]
    
    # Extrair do nome da pasta
    if 'Camara' in nome_pasta:
        metadados['instituição'] = 'Câmara Municipal'
    elif 'Prefeitura' in nome_pasta:
        metadados['instituição'] = 'Prefeitura'
    
    # Extrair ano do nome
    anos = re.findall(r'_(\d{4})_', nome_pasta)
    if anos:
        metadados['ano'] = anos[0]
    
    conteudo = f"""# {nome_pasta}

## Identificação

- **Instituição**: {metadados['instituição']}
- **Cidade**: {metadados['cidade']}
- **Ano**: {metadados['ano']}
- **Cargo**: {metadados['cargo']}
- **Banca**: {metadados['banca']}
- **Data**: {metadados['data']}
- **Número de Questões**: {metadados['num_questoes']}

## Instruções

"""
    
    # Adicionar trecho do texto
    if texto:
        trecho = texto[:1000]  # Primeiros 1000 caracteres
        conteudo += f"{trecho}...\n\n"
    else:
        conteudo += "Conteúdo não disponível\n\n"
    
    conteudo += """## Questões

*(A ser extraídas)*

---

*Processado em: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "*"
    
    return conteudo

def processar_id(pasta_id):
    """Processar um ID"""
    logger.info(f"\nProcessando: {pasta_id.name}")
    
    # Verificar se é duplicidade
    id_num = pasta_id.name.split(' ID')[0].strip()
    if id_num.isdigit() and int(id_num) in DUPLICIDADES:
        logger.info(f"⏭️  {pasta_id.name} é duplicidade, pulando")
        return None
    
    # Gerar nome padronizado
    nome_pasta = padronizar_nome_da_prova(pasta_id)
    if not nome_pasta:
        nome_pasta = padronizar_nome(pasta_id.name)
    
    logger.info(f"Nome: {nome_pasta}")
    
    # Verificar se já existe
    if nome_pasta in github_pastas:
        logger.info(f"⏭️  {nome_pasta} já existe, pulando")
        return None
    
    # Criar pasta de destino
    pasta_destino = BASE_GITHUB / nome_pasta
    pasta_destino.mkdir(parents=True, exist_ok=True)
    pasta_imagens = pasta_destino / "imagens"
    pasta_imagens.mkdir(exist_ok=True)
    
    # Extrair texto
    pdfs = list(pasta_id.glob('*.pdf'))
    texto_completo = ""
    for pdf in pdfs:
        if not ('gabarito' in pdf.name.lower() or 'IDENTIFICACAO' in pdf.name):
            texto = extrair_texto_pdf(pdf)
            if texto:
                texto_completo += f"\n\n--- {pdf.name} ---\n\n{texto}\n\n"
    
    if not texto_completo:
        texto_completo = "Conteúdo não extraído"
    
    # Criar prova_organizada.md
    md_conteudo = gerar_prova_organizada(nome_pasta, texto_completo, pasta_id)
    with open(pasta_destino / "prova_organizada.md", 'w', encoding='utf-8') as f:
        f.write(md_conteudo)
    logger.info(f"✅ prova_organizada.md criado")
    
    # Criar relatorio_analise.md
    relatorio = f"""# Relatório de Análise - {nome_pasta}

## Informações Básicas

- **ID Original**: {pasta_id.name}
- **Pasta Local**: {pasta_id}
- **Arquivos**: {len(pdfs)} PDF(s)
- **Conteúdo Extraído**: {'Sim' if texto_completo != 'Conteúdo não extraído' else 'Não'}

## Verificação de Duplicidade

- [ ] Prova já cadastrada
- [ ] Duplicidade confirmada
- [x] Nova prova

## Próximos Passos

1. [x] Extração de conteúdo
2. [ ] Revisão manual
3. [ ] Correção de formatação
4. [ ] Validação final

---

*Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    with open(pasta_destino / "relatorio_analise.md", 'w', encoding='utf-8') as f:
        f.write(relatorio)
    logger.info(f"✅ relatorio_analise.md criado")
    
    # Criar PROVA_ORGANIZADA.zip (NÃO incluir PDFs, apenas markdowns)
    zip_path = pasta_destino / "PROVA_ORGANIZADA.zip"
    with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(str(pasta_destino / "prova_organizada.md"), "prova_organizada.md")
        zipf.write(str(pasta_destino / "relatorio_analise.md"), "relatorio_analise.md")
    logger.info(f"✅ PROVA_ORGANIZADA.zip criado")
    
    # Copiar IDENTIFICACAO.txt se existir
    ident_file = pasta_id / "IDENTIFICACAO.txt"
    if ident_file.exists():
        try:
            shutil.copy2(str(ident_file), str(pasta_destino / "IDENTIFICACAO.txt"))
        except:
            pass
    
    logger.info(f"✅ {pasta_id.name} processado!")
    return nome_pasta

def main():
    """Função principal"""
    global github_pastas
    
    logger.info("="*80)
    logger.info("PROCESSANDO TODOS OS IDs FALTANTES")
    logger.info("="*80)
    
    # Coletar IDs para processar
    ids_para_processar = []
    
    # IDs no nível raiz
    for item in sorted(BASE_LOCAL.iterdir()):
        if item.is_dir() and 'ID' in item.name:
            pdfs = list(item.glob('*.pdf'))
            if pdfs:
                ids_para_processar.append(item)
    
    # IDs em Falta_fazer
    for remessa in sorted(FALTA_FAZER.iterdir()):
        if remessa.is_dir() and remessa.name.startswith('remessa_'):
            for id_folder in sorted(remessa.iterdir()):
                if id_folder.is_dir():
                    pdfs = list(id_folder.glob('*.pdf'))
                    if pdfs:
                        ids_para_processar.append(id_folder)
    
    logger.info(f"Total de IDs para processar: {len(ids_para_processar)}")
    
    # Processar em lotes de 50
    processadas = []
    erros = []
    LOTE_SIZE = 50
    
    for i in range(0, len(ids_para_processar), LOTE_SIZE):
        lote = ids_para_processar[i:i+LOTE_SIZE]
        logger.info(f"\n{'='*80}")
        logger.info(f"PROCESSANDO LOTE {i//LOTE_SIZE + 1}: {len(lote)} IDs")
        logger.info(f"{'='*80}")
        
        for j, pasta_id in enumerate(lote, 1):
            try:
                resultado = processar_id(pasta_id)
                if resultado:
                    processadas.append(resultado)
                else:
                    erros.append(pasta_id.name)
                
                pendentes_no_lote = len(lote) - j
                total_pendentes = len(ids_para_processar) - (i + j)
                logger.info(f"Progresso: {j}/{len(lote)} no lote | {total_pendentes} total pendentes | {len(erros)} erros")
                
            except Exception as e:
                logger.error(f"❌ Erro processando {pasta_id.name}: {e}")
                erros.append(pasta_id.name)
    
    # Resumo final
    logger.info("\n" + "="*80)
    logger.info("RESUMO FINAL")
    logger.info("="*80)
    logger.info(f"Total de IDs: {len(ids_para_processar)}")
    logger.info(f"Processadas: {len(processadas)}")
    logger.info(f"Erros: {len(erros)}")
    
    if processadas:
        logger.info(f"\nPastas criadas:")
        for p in processadas[:30]:
            logger.info(f"  - {p}")
        if len(processadas) > 30:
            logger.info(f"  ... e {len(processadas) - 30} mais")

if __name__ == "__main__":
    main()
