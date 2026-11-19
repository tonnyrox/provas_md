#!/usr/bin/env python3
"""
Script para processar APENAS os IDs que realmente não estão no GitHub
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
        logger.warning(f"Aviso: não foi possível extrair texto de {pdf_path.name}: {e}")
        return None

def padronizar_nome(nome):
    """Padronizar nome removendo caracteres especiais e normalizando"""
    # Remover .pdf
    nome = re.sub(r'\.pdf$', '', nome, flags=re.IGNORECASE)
    
    # Remover Prova -, Gabarito -, etc.
    nome = re.sub(r'(Prova|Gabarito|Concurso)\s*-?\s*', '', nome, flags=re.IGNORECASE)
    
    # Remover caracteres não alfanuméricos (manter apenas letras, números, underscore, hífen)
    nome = re.sub(r'[^\w\s-]', ' ', nome)
    
    # Substituir espaços por underscore
    nome = re.sub(r'\s+', '_', nome).strip('_')
    
    # Remover anos duplicados
    nome = re.sub(r'(_20\d{2}){2,}', r'\1', nome)
    nome = re.sub(r'(_19\d{2}){2,}', r'\1', nome)
    
    # Remover preposições isoladas
    nome = re.sub(r'_de_|_do_|_da_|_das_|_dos_|_em_|_a_|_o_|_para_|_por_', '_', nome)
    
    # Remover underscores consecutivos
    nome = re.sub(r'__+', '_', nome)
    nome = nome.strip('_')
    
    # Capitalizar corretamente
    partes = nome.split('_')
    partes_cap = []
    lowercase_words = {'de', 'do', 'da', 'das', 'dos', 'em', 'a', 'o', 'e', 'ou', 'i', 'ii', 'iii', 'iv', 'v'}
    for p in partes:
        if p and p.lower() in lowercase_words:
            partes_cap.append(p.lower())
        else:
            partes_cap.append(p.capitalize())
    
    return '_'.join(partes_cap)

def gerar_nome_unico(base_name, github_pastas):
    """Gerar nome único que não existe no GitHub"""
    if base_name not in github_pastas:
        return base_name
    
    # Adicionar sufixo
    i = 1
    while True:
        novo_nome = f"{base_name}_{i}"
        if novo_nome not in github_pastas:
            return novo_nome
        i += 1

def identificar_prova(pasta_id):
    """Identificar prova a partir dos PDFs ou IDENTIFICACAO.txt"""
    
    # Tentar ler IDENTIFICACAO.txt
    ident_file = pasta_id / "IDENTIFICACAO.txt"
    if ident_file.exists():
        try:
            with open(ident_file, 'r', encoding='utf-8', errors='ignore') as f:
                conteudo = f.read()
            
            # Procurar por Prova:
            prova_match = re.search(r'Prova:\s*(.+)', conteudo, re.IGNORECASE)
            if prova_match:
                return padronizar_nome(prova_match.group(1).strip())
        except:
            pass
    
    # Extrair do nome do PDF (não gabarito)
    pdfs = list(pasta_id.glob('*.pdf'))
    for pdf in pdfs:
        if 'gabarito' not in pdf.name.lower():
            return padronizar_nome(pdf.name)
    
    # Se só tiver gabarito, usar ele
    if pdfs:
        return padronizar_nome(pdfs[0].name)
    
    return None

def gerar_prova_organizada(nome_pasta, texto, pasta_id):
    """Gerar conteúdo para prova_organizada.md"""
    
    # Extrair metadados
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
        elif re.search(r'[Pp]refeitura', texto):
            metadados['instituição'] = 'Prefeitura'
        
        # Extrair cargo
        cargos = re.findall(r'(Agente|Administrativo|Técnico|Analista|Assistente|Fiscal|Legislativo)', texto)
        if cargos:
            metadados['cargo'] = cargos[0]
    
    # Extrair do nome da pasta
    if 'Camara' in nome_pasta or 'Câmara' in nome_pasta:
        metadados['instituição'] = 'Câmara Municipal'
    elif 'Prefeitura' in nome_pasta:
        metadados['instituição'] = 'Prefeitura'
    
    # Extrair ano do nome
    anos = re.findall(r'_(\d{4})_', nome_pasta)
    if anos:
        metadados['ano'] = anos[0]
    
    # Criar conteúdo
    conteudo = f"""# {nome_pasta}

## Identificação

- **Instituição**: {metadados['instituição']}
- **Cidade**: {metadados['cidade']}
- **Ano**: {metadados['ano']}
- **Cargo**: {metadados['cargo']}
- **Banca**: {metadados['banca']}
- **Data**: {metadados['data']}
- **Número de Questões**: {metadados['num_questoes']}

## Conteúdo da Prova

"""
    
    if texto and texto != "Conteúdo não extraído":
        # Adicionar trecho do texto (primeiros 2000 caracteres)
        trecho = texto[:2000]
        conteudo += f"{trecho}...\n\n"
    else:
        conteudo += "*(Conteúdo será extraído posteriormente)*\n\n"
    
    conteudo += """## Observações

- Prova processada automaticamente
- Aguardando revisão manual

---

*Processado em: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "*"
    
    return conteudo

def processar_id(pasta_id):
    """Processar um ID"""
    logger.info(f"\nProcessando: {pasta_id.name}")
    
    # Verificar se é duplicidade
    id_num = pasta_id.name.split(' ID')[0].strip()
    if id_num.isdigit() and int(id_num) in DUPLICIDADES:
        logger.info(f"⏭️  {pasta_id.name} é duplicidade de {DUPLICIDADES[int(id_num)]} ID, pulando")
        return None
    
    # Identificar nome da prova
    nome_base = identificar_prova(pasta_id)
    if not nome_base:
        nome_base = padronizar_nome(pasta_id.name)
    
    # Gerar nome único
    nome_pasta = gerar_nome_unico(nome_base, github_pastas)
    logger.info(f"Nome: {nome_pasta}")
    
    # Atualizar lista de pastas no GitHub (para evitar duplicatas no mesmo lote)
    github_pastas.add(nome_pasta)
    
    # Criar pasta de destino
    pasta_destino = BASE_GITHUB / nome_pasta
    pasta_destino.mkdir(parents=True, exist_ok=True)
    pasta_imagens = pasta_destino / "imagens"
    pasta_imagens.mkdir(exist_ok=True)
    
    # Extrair texto de todos os PDFs (exceto gabarito)
    pdfs = list(pasta_id.glob('*.pdf'))
    texto_completo = ""
    
    for pdf in pdfs:
        if 'gabarito' in pdf.name.lower():
            continue  # Pular gabaritos
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
- **Arquivos Processados**: {len(pdfs)} PDF(s)
- **Conteúdo Extraído**: {'Sim' if texto_completo != 'Conteúdo não extraído' else 'Não'}

## Verificação de Duplicidade

- [ ] Prova já cadastrada
- [ ] Duplicidade confirmada
- [x] Nova prova processada

## Próximos Passos

1. [x] Extração automática de conteúdo
2. [ ] Revisão manual do conteúdo
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
    
    logger.info(f"✅ {pasta_id.name} processado com sucesso!")
    return nome_pasta

def main():
    """Função principal"""
    logger.info("="*80)
    logger.info("PROCESSANDO IDS FALTANTES (CORRETO)")
    logger.info("="*80)
    
    # Coletar IDs com PDFs
    ids_com_pdf = []
    
    # IDs no nível raiz
    for item in sorted(BASE_LOCAL.iterdir()):
        if item.is_dir() and 'ID' in item.name:
            pdfs = list(item.glob('*.pdf'))
            if pdfs:
                ids_com_pdf.append(item)
    
    # IDs em Falta_fazer
    for remessa in sorted(FALTA_FAZER.iterdir()):
        if remessa.is_dir() and remessa.name.startswith('remessa_'):
            for id_folder in sorted(remessa.iterdir()):
                if id_folder.is_dir():
                    pdfs = list(id_folder.glob('*.pdf'))
                    if pdfs:
                        ids_com_pdf.append(id_folder)
    
    logger.info(f"Total de IDs com PDFs: {len(ids_com_pdf)}")
    
    # Processar todos
    processadas = []
    erros = []
    
    for i, pasta_id in enumerate(ids_com_pdf, 1):
        try:
            resultado = processar_id(pasta_id)
            if resultado:
                processadas.append(resultado)
            else:
                erros.append(pasta_id.name)
            
            pendentes = len(ids_com_pdf) - i
            logger.info(f"\nProgresso: {i}/{len(ids_com_pdf)} | {pendentes} pendentes | {len(erros)} erros")
            
            # Mostrar amostra das processadas
            if i % 10 == 0:
                logger.info(f"\nÚltimas 5 processadas: {processadas[-5:]}")
            
        except Exception as e:
            logger.error(f"❌ Erro processando {pasta_id.name}: {e}")
            erros.append(pasta_id.name)
    
    # Resumo final
    logger.info("\n" + "="*80)
    logger.info("RESUMO FINAL")
    logger.info("="*80)
    logger.info(f"Total de IDs: {len(ids_com_pdf)}")
    logger.info(f"Processadas: {len(processadas)}")
    logger.info(f"Erros: {len(erros)}")
    
    # Salvar resultados
    with open(BASE_GITHUB / "resumo_processamento.txt", 'w', encoding='utf-8') as f:
        f.write(f"Processamento em: {datetime.now()}\n\n")
        f.write(f"Total: {len(ids_com_pdf)}\n")
        f.write(f"Processadas: {len(processadas)}\n")
        f.write(f"Erros: {len(erros)}\n\n")
        f.write("Processadas:\n")
        for p in processadas:
            f.write(f"  - {p}\n")
        f.write("\nErros:\n")
        for e in erros:
            f.write(f"  - {e}\n")
    
    logger.info(f"\n✅ Processamento concluído! Resumo salvo em {BASE_GITHUB / 'resumo_processamento.txt'}")

if __name__ == "__main__":
    main()
