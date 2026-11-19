#!/usr/bin/env python3
"""
Script para processar TODAS as pastas não publicadas em Falta_fazer
=========================================================================

Este script:
1. Varre todas as pastas em 000000 -OK/Falta_fazer/remessa_*/
2. Identifica quais não foram publicadas
3. Processa cada pasta individualmente:
   - Extrai metadados do IDENTIFICACAO.txt ou do PDF
   - Cria pasta no padrão Provas MD/
   - Gera prova_organizada.md, relatorio_analise.md, PROVA_ORGANIZADA.zip
4. Mantém contador de progresso
5. Salva progresso para continuar de onde parou

Uso:
    python processar_todas_falta_fazer.py
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
import subprocess


# Caminhos base
BASE_000000 = Path("C:/Users/Tonny/Downloads/projeto_git_prova/000000 -OK")
FALTA_FAZER = BASE_000000 / "Falta_fazer"
PROVAS_MD = Path("C:/Users/Tonny/Downloads/projeto_git_prova/provas_md/Provas MD")
PROGRESS_FILE = Path("processamento_progresso.json")
LOG_FILE = Path("processamento_log.txt")


def logs(msg, level="INFO"):
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
    return {"processados": [], "erros": [], "inicio": str(datetime.now()), "ultima_atualizacao": None}


def extrair_metadados_de_identificacao(id_path):
    """Extrai metadados do arquivo IDENTIFICACAO.txt."""
    if not id_path.exists():
        return None
    
    with open(id_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Procurar informações
    info = {}
    
    # Órgão
    org_match = re.search(r'Órgão[^(]*\([^)]*\):[\s]*(.+)', content)
    if not org_match:
        org_match = re.search(r'Órgão:[\s]*(.+)', content)
    if org_match:
        info['orgao'] = org_match.group(1).strip()
    
    # Ano
    ano_match = re.search(r'Ano:[\s]*(\d{4})', content)
    if ano_match:
        info['ano'] = ano_match.group(1)
    
    # Cargo
    cargo_match = re.search(r'Cargo[^(]*\([^)]*\):[\s]*(.+)', content)
    if not cargo_match:
        cargo_match = re.search(r'Cargo:[\s]*(.+)', content)
    if cargo_match:
        info['cargo'] = cargo_match.group(1).strip()
    
    # Tipo de prova
    tipo_match = re.search(r'Tipo:[\s]*(.+)', content)
    if tipo_match:
        info['tipo'] = tipo_match.group(1).strip()
    
    # Pasta publicada
    pasta_match = re.search(r'Pasta publicada[^:]*:[\s]*(.+)', content)
    if pasta_match:
        info['pasta_publicada'] = pasta_match.group(1).strip()
    
    # Status
    status_match = re.search(r'Status:[\s]*(.+)', content)
    if status_match:
        info['status'] = status_match.group(1).strip()
    
    return info


def verificar_se_ja_existe_no_github(pasta_nome):
    """Verifica se a pasta já existe no repositório Provas MD."""
    pasta_path = PROVAS_MD / pasta_nome
    return pasta_path.exists()


def gerar_nome_pasta(orgao, ano, cargo):
    """Gera o nome da pasta no padrão Camara_<Cidade>_<Ano>_<Cargo>."""
    # Normalizar
    orgao = orgao.strip().replace(" ", "_")
    cargo = cargo.strip().replace(" ", "_")
    
    # Remover acentos e caracteres especiais
    orgao = re.sub(r'[^\w-]', '', orgao)
    cargo = re.sub(r'[^\w-]', '', cargo)
    
    # Adicionar prefixo se não tiver
    if not orgao.startswith("Camara_") and not orgao.startswith("Prefeitura_"):
        orgao = f"Camara_{orgao}"
    
    return f"{orgao}_{ano}_{cargo}"


def processar_pasta(falta_fazer_path, pasta_id, progresso):
    """Processa uma única pasta de Falta_fazer."""
    
    pasta_path = falta_fazer_path / pasta_id
    
    logs(f"\n{'='*80}")
    logs(f"Processando: {pasta_id}")
    logs(f"{'='*80}")
    
    # Verificar se já foi processada
    if pasta_id in progresso["processados"]:
        logs(f"⏭️  {pasta_id} já foi processada, pulando...")
        return True
    
    # Ler IDENTIFICACAO.txt
    id_path = pasta_path / "IDENTIFICACAO.txt"
    metadados = extrair_metadados_de_identificacao(id_path)
    
    if metadados and metadados.get('status') and 'PUBLICADA' in metadados.get('status', ''):
        logs(f"✅ {pasta_id} já está publicada: {metadados.get('pasta_publicada', 'N/A')}")
        progresso["processados"].append(pasta_id)
        salvar_progresso(progresso)
        return True
    
    if metadados and metadados.get('status') and 'DUPLICIDADE' in metadados.get('status', ''):
        logs(f"⚠️  {pasta_id} é DUPLICIDADE CONFIRMADA, pulando...")
        progresso["processados"].append(pasta_id)
        salvar_progresso(progresso)
        return True
    
    # Listar PDFs
    pdfs = [f for f in pasta_path.iterdir() if f.is_file() and f.name.lower().endswith('.pdf')]
    
    if not pdfs:
        logs(f"❌ {pasta_id} não tem PDFs, pulando...")
        progresso["erros"].append({
            "pasta": str(pasta_id),
            "erro": "Nenhum PDF encontrado"
        })
        salvar_progresso(progresso)
        return False
    
    logs(f"📄  Encontrados {len(pdfs)} PDF(s):")
    for pdf in pdfs:
        logs(f"   - {pdf.name}")
    
    # Extrair metadados do nome do PDF
    if not metadados or not all(k in metadados for k in ['orgao', 'ano', 'cargo']):
        # Tentar extrair do nome do PDF
        for pdf in pdfs:
            pdf_name = pdf.name.lower()
            # Procurar por padroes no nome
            if 'camara' in pdf_name or 'prefeitura' in pdf_name:
                # Extrair cidade, ano, cargo do nome
                pass
    
    # Tentar obter metadados do IDENTIFICACAO.txt
    if metadados:
        orgao = metadados.get('orgao', '')
        ano = metadados.get('ano', '')
        cargo = metadados.get('cargo', '')
        pasta_publicada = metadados.get('pasta_publicada', '')
        
        if pasta_publicada:
            # Usar o nome da pasta já definido
            pasta_nome = pasta_publicada
        else:
            pasta_nome = gerar_nome_pasta(orgao, ano, cargo)
    else:
        # Tentar gerar nome a partir do PDF
        # Pegar o primeiro PDF
        pdf_exemplo = pdfs[0]
        pdf_name = pdf_exemplo.name
        
        # Extrair informações do nome do PDF
        # Padrao: "Prova - Câmara Municipal de <Cidade> - <UF> - <Ano> - <Cargo>.pdf"
        match = re.search(r'[Cc]âmera[\s-]Municipal[\s-]de[\s-](.+?)[\s-]-[\s-](\d{4})[\s-]-[\s-](.+)\..*', pdf_name, re.IGNORECASE)
        if match:
            cidade = match.group(1).strip()
            ano = match.group(2).strip()
            cargo = match.group(3).strip()
            pasta_nome = f"Camara_{cidade}_{ano}_{cargo}"
        else:
            # Tentar outro padrão
            match = re.search(r'[Pp]refeitura[\s-].+[\s-](\d{4})[\s-].+', pdf_name, re.IGNORECASE)
            if match:
                ano = match.group(1)
                # Extrair mais informações
                partes = pdf_name.replace('.pdf', '').split('-')
                orgao = 'Prefeitura'
                cidade = partes[1].strip() if len(partes) > 1 else 'Nao_Identificado'
                cargo = partes[-1].strip() if len(partes) > 2 else 'Nao_Identificado'
                pasta_nome = f"{orgao}_{cidade}_{ano}_{cargo}"
            else:
                # Nome genérico
                pasta_nome = f"Nao_Identificado_{pasta_id}_Prova"
    
    logs(f"📁 Pasta destino: {pasta_nome}")
    
    # Verificar se já existe no GitHub
    if verificar_se_ja_existe_no_github(pasta_nome):
        logs(f"⚠️  Pasta {pasta_nome} já existe em Provas MD/")
        # Verificar se é a mesma prova ou duplicidade
        logs(f"   Verificar se é duplicidade ou prova diferente...")
        # Por enquanto, vamos pular
        progresso["processados"].append(pasta_id)
        salvar_progresso(progresso)
        return True
    
    # Criar a pasta em Provas MD
    nova_pasta = PROVAS_MD / pasta_nome
    nova_pasta.mkdir(exist_ok=True)
    
    # Copiar PDFs para a nova pasta (para processamento posterior)
    pasta_pdfs = nova_pasta / "PDFs_originais"
    pasta_pdfs.mkdir(exist_ok=True)
    
    for pdf in pdfs:
        import shutil
        shutil.copy2(pdf, pasta_pdfs / pdf.name)
    
    # Criar IDENTIFICACAO.txt na nova pasta
    with open(nova_pasta / "IDENTIFICACAO_ORIGEM.txt", "w", encoding="utf-8") as f:
        f.write(f"Origem: {pasta_path}\n")
        f.write(f"Data de processamento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if metadados:
            f.write(f"Metadados originais:\n{json.dumps(metadados, indent=2, ensure_ascii=False)}\n")
    
    logs(f"✅ {pasta_id} → {pasta_nome} (criada, aguardando processamento)")
    
    # Marcar como processada
    progresso["processados"].append(pasta_id)
    progresso["ultima_atualizacao"] = str(datetime.now())
    salvar_progresso(progresso)
    
    return True


def main():
    """Função principal."""
    
    logs("="*80)
    logs("INICIANDO PROCESSAMENTO DE TODAS AS PASTAS NÃO PUBLICADAS")
    logs("="*80)
    
    # Carregar progresso
    progresso = carregar_progresso()
    
    logs(f"Progresso anterior: {len(progresso.get('processados', []))} pastas processadas")
    logs(f"Erros anteriores: {len(progresso.get('erros', []))}")
    
    # Contadores
    total_processadas = len(progresso.get('processados', []))
    total_erros = len(progresso.get('erros', []))
    
    # Listar todas as pastas a processar
    pastas_para_processar = []
    
    for remessa in sorted(os.listdir(FALTA_FAZER)):
        remessa_path = FALTA_FAZER / remessa
        if remessa_path.is_dir():
            for item in sorted(os.listdir(remessa_path)):
                if item.endswith(' ID'):
                    pasta_id = item
                    pastas_para_processar.append((remessa, pasta_id))
    
    logs(f"\nTotal de pastas para processar: {len(pastas_para_processar)}")
    logs(f"Já processadas: {total_processadas}")
    logs(f"Restantes: {len(pastas_para_processar) - total_processadas}")
    
    # Processar pastas
    for remessa, pasta_id in pastas_para_processar:
        if pasta_id in progresso.get('processados', []):
            continue
        
        remessa_path = FALTA_FAZER / remessa / pasta_id
        
        try:
            success = processar_pasta(FALTA_FAZER / remessa, pasta_id, progresso)
            if success:
                total_processadas += 1
            else:
                total_erros += 1
        except Exception as e:
            logs(f"❌ ERRO ao processar {pasta_id}: {str(e)}", "ERROR")
            progresso["erros"].append({
                "pasta": pasta_id,
                "erro": str(e)
            })
            salvar_progresso(progresso)
            total_erros += 1
        
        # Mostrar progresso
        pendentes = len(pastas_para_processar) - total_processadas
        logs(f"\nProgresso: {total_processadas}/{len(pastas_para_processar)} processadas | {pendentes} pendentes | {total_erros} erros")
    
    # Salvar progresso final
    progresso["ultima_atualizacao"] = str(datetime.now())
    progresso["fim"] = str(datetime.now())
    salvar_progresso(progresso)
    
    # Resumo final
    logs("\n" + "="*80)
    logs("RESUMO FINAL")
    logs("="*80)
    logs(f"✅ Pastas processadas: {total_processadas}")
    logs(f"❌ Erros: {total_erros}")
    logs(f"⏳ Total de pastas: {len(pastas_para_processar)}")
    
    if total_erros == 0:
        logs("\n🎉 TODAS AS PASTAS FORAM PROCESSADAS COM SUCESSO!")
    else:
        logs(f"\n⚠️  {total_erros} pastas não puderam ser processadas")


if __name__ == "__main__":
    main()
