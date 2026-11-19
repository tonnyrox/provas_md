#!/usr/bin/env python3
"""
Script para processar APENAS as pastas que NÃO foram publicadas
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
DUPLICIDADES = {
    114: 113,  # 114 ID é duplicidade de 113 ID
}

def init():
    """Inicializar lista de pastas já publicadas"""
    global PUBLICADAS
    PUBLICADAS = set()
    if BASE_GITHUB.exists():
        PUBLICADAS = set(f.name for f in BASE_GITHUB.iterdir() if f.is_dir())
    logger.info(f"Pastas já publicadas: {len(PUBLICADAS)}")

def ja_publicado(pasta_id):
    """
    Verificar se uma pasta já foi publicada
    """
    # Verificar se tem IDENTIFICACAO.txt com status PUBLICADA
    ident_file = pasta_id / "IDENTIFICACAO.txt"
    if ident_file.exists():
        with open(ident_file, 'r', encoding='utf-8', errors='ignore') as f:
            conteudo = f.read()
        
        # Procurar por patterns que indicam publicação
        if 'PUBLICADA' in conteudo or 'publicada' in conteudo:
            # Extrair o nome da pasta publicada
            match = re.search(r'Pasta publicada.*: (\w+)', conteudo)
            if match:
                nome_publicado = match.group(1)
                if nome_publicado in PUBLICADAS:
                    return True, nome_publicado
    
    return False, None

def extrair_info_do_pdf(pdf_path):
    """
    Extrair informações do nome do PDF
    """
    nome = pdf_path.name.replace('.pdf', '')
    
    # Remover prefixos
    for prefix in ['Prova - ', 'Gabarito - ', 'Prova_', 'Gabarito_']:
        if nome.startswith(prefix):
            nome = nome[len(prefix):]
    
    # Tentar identificar ano
    anos = re.findall(r'\b(19|20)\d{2}\b', nome)
    ano = anos[0] if anos else '0000'
    
    # Tentar identificar tipo (Câmara, Prefeitura, etc.)
    orgao = 'Outros'
    if 'Câmara' in nome or 'Camara' in nome:
        orgao = 'Camara'
    elif 'Prefeitura' in nome:
        orgao = 'Prefeitura'
    
    # Tentar identificar cidade e cargo
    # Remover ano para processar o resto
    nome_sem_ano = re.sub(r'\b(19|20)\d{2}\b', '', nome)
    
    # Padronizar
    nome_sem_ano = re.sub(r'\s+', ' ', nome_sem_ano).strip()
    
    return {
        'nome': nome,
        'ano': ano,
        'orgao': orgao,
        'restante': nome_sem_ano
    }

def padronizar_nome(metadados):
    """
    Gerar nome padronizado para a pasta
    """
    orgao = metadados.get('orgao', 'Outros')
    restante = metadados.get('restante', '')
    ano = metadados.get('ano', '0000')
    
    # Limpar
    restante = re.sub(r'\s+', ' ', restante).strip()
    restante = restante.replace(' de ', '_').replace(' do ', '_').replace(' da ', '_')
    restante = restante.replace(' -- ', '_').replace('--', '_').replace(' - ', '_')
    restante = restante.replace(' ', '_')
    
    # Remover caracteres especiais
    restante = re.sub(r'[^\w-]', '', restante)
    
    # Separar cidade e cargo
    # Para simplificar, vamos usar o padrão: Orgao_Cidade_Ano_Cargo
    # Vamos assumir que o cargo é a última parte
    
    # Remover palavras que são cargos
    cargos = ['Agente', 'Administrativo', 'Legislativo', 'Tecnico', 'Auxiliar', 
              'Assistente', 'Fiscal', 'Inspector', 'Controlador', 'Coordenador',
              'Supervisor', 'Vigia', 'Zelador', 'Motorista', 'Professor',
              'Enfermeiro', 'Medico', 'Advogado', 'Contador', 'Analista',
              'Em', 'Comunicacao', 'Social', 'Jornalismo']
    
    partes = restante.split('_')
    partes_limpo = []
    for p in partes:
        if p and p not in ['', 'Em', 'Da', 'De', 'Do', 'Das', 'Dos']:
            partes_limpo.append(p)
    
    # Se tiver poucas partes, manter todas
    if len(partes_limpo) <= 3:
        nome = f"{orgao}_{'_'.join(partes_limpo)}_{ano}"
    else:
        # Assumir que o cargo é as últimas 2-3 palavras
        cidade = '_'.join(partes_limpo[:-2])
        cargo = '_'.join(partes_limpo[-2:])
        nome = f"{orgao}_{cidade}_{ano}_{cargo}"
    
    # Limpar
    nome = re.sub(r'__+', '_', nome)
    nome = re.sub(r'_-_|-_', '_', nome)
    nome = nome.strip('_')
    
    return nome

def copiar_pdfs(pasta_origem, pasta_destino):
    """Copiar todos os PDFs"""
    pasta_destino.mkdir(parents=True, exist_ok=True)
    
    pdfs = list(pasta_origem.glob('*.pdf'))
    if not pdfs:
        return False
    
    for pdf in pdfs:
        try:
            shutil.copy2(str(pdf), str(pasta_destino / pdf.name))
        except Exception as e:
            logger.error(f"Erro copiando {pdf.name}: {e}")
            return False
    
    return True

def criar_zip(pasta):
    """Criar ZIP"""
    zip_path = pasta.parent / f"{pasta.name}_ORGANIZADA.zip"
    
    try:
        with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in pasta.iterdir():
                if file.is_file():
                    zipf.write(str(file), file.name)
        return True
    except Exception as e:
        logger.error(f"Erro criando ZIP: {e}")
        return False

def processar_pasta(pasta_id):
    """Processar uma pasta"""
    logger.info(f"\nProcessando: {pasta_id.name}")
    
    # Verificar se é duplicidade
    id_num = pasta_id.name.split(' ID')[0].strip()
    if id_num.isdigit() and int(id_num) in DUPLICIDADES:
        logger.info(f"⏭️  Duplicidade, pulando")
        return None
    
    # Verificar se já foi publicada
    publicado, nome_publicado = ja_publicado(pasta_id)
    if publicado:
        logger.info(f"⏭️  Já publicada como {nome_publicado}, pulando")
        return None
    
    # Extrair informações dos PDFs
    pdfs = list(pasta_id.glob('*.pdf'))
    if not pdfs:
        logger.error(f"❌ Sem PDFs")
        return None
    
    # Usar o primeiro PDF para extrair info
    metadados = extrair_info_do_pdf(pdfs[0])
    
    # Se houver IDENTIFICACAO.txt, tentar extrair mais info
    ident_file = pasta_id / "IDENTIFICACAO.txt"
    if ident_file.exists():
        with open(ident_file, 'r', encoding='utf-8', errors='ignore') as f:
            conteudo = f.read()
        
        # Tentar extrair identificação manual
        # Exemplo: "PDFs: Gabarito - Câmara Municipal de Cornélio Procópio – Paraná - 2012 - Agente Administrativo.pdf"
        match = re.search(r'Câmara Municipal de ([^-]+)[^0-9]*(\d{4})[^A-Z]*([A-Z][^\.]+)', conteudo)
        if match:
            cidade = match.group(1).strip().replace(' ', '_')
            ano = match.group(2)
            cargo = match.group(3).strip().replace(' ', '_')
            metadados = {
                'orgao': 'Camara',
                'cidade': cidade,
                'ano': ano,
                'cargo': cargo,
                'restante': f"{cidade}_{ano}_{cargo}"
            }
    
    # Gerar nome padronizado
    nome_pasta = padronizar_nome(metadados)
    
    if not nome_pasta:
        logger.error(f"❌ Não foi possível gerar nome")
        return None
    
    # Verificar se nome já existe
    pasta_destino = BASE_GITHUB / nome_pasta
    if pasta_destino.exists():
        # Tentar nome alternativo
        base_nome = nome_pasta.rsplit('_', 1)[0] if '_' in nome_pasta else nome_pasta
        for i in range(1, 10):
            novo_nome = f"{base_nome}_{i}"
            pasta_destino = BASE_GITHUB / novo_nome
            if not pasta_destino.exists():
                nome_pasta = novo_nome
                break
        else:
            logger.error(f"❌ Não foi possível encontrar nome único")
            return None
    
    logger.info(f"Pasta destino: {nome_pasta}")
    
    # Criar estrutura
    pasta_destino.mkdir(parents=True, exist_ok=True)
    pasta_imagens = pasta_destino / "imagens"
    pasta_imagens.mkdir(exist_ok=True)
    
    # Copiar PDFs
    if not copiar_pdfs(pasta_id, pasta_destino):
        logger.error(f"❌ Falha ao copiar PDFs")
        return None
    
    # Criar prova_organizada.md
    md_conteudo = f"""# {nome_pasta}

## Identificação

- **Instituição**: {metadados.get('orgao', 'N/I')}
- **Cidade**: {metadados.get('cidade', 'N/I')}
- **Ano**: {metadados.get('ano', 'N/I')}
- **Cargo**: {metadados.get('cargo', 'N/I')}
- **Banca**: N/I
- **Data**: N/I
- **Número de Questões**: 0 (a ser preenchido)

## Observações

- Prova em processamento
- Arquivos originais copiados
- Aguardando extração de conteúdo

## Arquivos

"""
    
    for pdf in pdfs:
        md_conteudo += f"\n- [{pdf.name}]({pdf.name})\n"
    
    md_conteudo += f"""
---

*Processado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    with open(pasta_destino / "prova_organizada.md", 'w', encoding='utf-8') as f:
        f.write(md_conteudo)
    logger.info(f"✅ prova_organizada.md criado")
    
    # Criar relatorio_analise.md
    relatorio = f"""# Relatório de Análise - {nome_pasta}

## Informações Básicas

- **ID Original**: {pasta_id.name}
- **Arquivos Encontrados**: {len(pdfs)} PDF(s)
- **Pasta Local**: {pasta_id}

## Verificação de Duplicidade

- [ ] Prova já cadastrada no GitHub
- [ ] Duplicidade confirmada
- [x] Nova prova a ser processada

## Próximos Passos

1. [ ] Extrair texto completo dos PDFs
2. [ ] Identificar e classificar todas as questões
3. [ ] Verificar duplicidade de conteúdo
4. [ ] Organizar imagens e materiais de apoio
5. [ ] Gerar arquivos finais padronizados

---

*Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    with open(pasta_destino / "relatorio_analise.md", 'w', encoding='utf-8') as f:
        f.write(relatorio)
    logger.info(f"✅ relatorio_analise.md criado")
    
    # Copiar outros arquivos (exceto PDFs)
    for file in pasta_id.iterdir():
        if file.is_file() and not file.name.lower().endswith('.pdf'):
            try:
                shutil.copy2(str(file), str(pasta_destino / file.name))
            except:
                pass
    
    # Criar ZIP
    if criar_zip(pasta_destino):
        logger.info(f"✅ PROVA_ORGANIZADA.zip criado")
    else:
        logger.warning(f"⚠️  Falha ao criar ZIP")
    
    logger.info(f"✅ {pasta_id.name} processada com sucesso!")
    return nome_pasta

def main():
    """Função principal"""
    logger.info("="*80)
    logger.info("INICIANDO PROCESSAMENTO DE PASTAS NÃO PUBLICADAS")
    logger.info("="*80)
    
    init()
    
    # Coletar pastas
    pastas_para_processar = []
    
    logger.info("\n" + "="*80)
    logger.info("ETAPA 1: COLETANDO PASTAS")
    logger.info("="*80)
    
    for remessa in sorted(FALTA_FAZER.iterdir()):
        if not remessa.is_dir():
            continue
        
        for pasta_id in sorted(remessa.iterdir()):
            if not pasta_id.is_dir():
                continue
            
            # Verificar se tem PDF
            pdfs = list(pasta_id.glob('*.pdf'))
            if not pdfs:
                continue
            
            # Verificar se já foi publicada
            publicado, _ = ja_publicado(pasta_id)
            if publicado:
                continue
            
            pastas_para_processar.append(pasta_id)
    
    logger.info(f"Pastas NÃO publicadas para processar: {len(pastas_para_processar)}")
    
    # Processar
    processadas = []
    erros = []
    
    logger.info("\n" + "="*80)
    logger.info("ETAPA 2: PROCESSANDO")
    logger.info("="*80)
    
    for i, pasta in enumerate(pastas_para_processar, 1):
        try:
            resultado = processar_pasta(pasta)
            if resultado:
                processadas.append(resultado)
            else:
                erros.append(pasta.name)
            
            pendentes = len(pastas_para_processar) - i
            logger.info(f"\nProgresso: {i}/{len(pastas_para_processar)} | {pendentes} pendentes | {len(erros)} erros")
            
        except Exception as e:
            logger.error(f"❌ Erro processando {pasta.name}: {e}")
            erros.append(pasta.name)
    
    # Resumo
    logger.info("\n" + "="*80)
    logger.info("RESUMO FINAL")
    logger.info("="*80)
    logger.info(f"Total não publicadas: {len(pastas_para_processar)}")
    logger.info(f"Processadas: {len(processadas)}")
    logger.info(f"Erros: {len(erros)}")
    
    if processadas:
        logger.info(f"\nPastas criadas:")
        for p in processadas[:20]:  # Mostrar primeiras 20
            logger.info(f"  - {p}")
        if len(processadas) > 20:
            logger.info(f"  ... e {len(processadas) - 20} mais")
    
    if erros:
        logger.info(f"\nErros:")
        for e in erros[:10]:
            logger.info(f"  - {e}")
        if len(erros) > 10:
            logger.info(f"  ... e {len(erros) - 10} mais")
    
    # Salvar log
    with open(BASE_GITHUB / "log_processamento_nao_publicados.txt", 'w', encoding='utf-8') as f:
        f.write(f"Processamento em: {datetime.now()}\n\n")
        f.write(f"Total não publicadas: {len(pastas_para_processar)}\n")
        f.write(f"Processadas: {len(processadas)}\n")
        f.write(f"Erros: {len(erros)}\n\n")
        f.write("Processadas:\n")
        for p in processadas:
            f.write(f"  - {p}\n")
        f.write("\nErros:\n")
        for e in erros:
            f.write(f"  - {e}\n")
    
    logger.info(f"\n✅ Concluído! Log em {BASE_GITHUB / 'log_processamento_nao_publicados.txt'}")

if __name__ == "__main__":
    main()
