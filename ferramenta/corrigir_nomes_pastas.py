#!/usr/bin/env python3
"""
Script para corrigir os nomes das pastas criadas com nomes errados.

Este script:
1. Identifica pastas com nomes malformados (ex: Camara__1992_)
2. Extrai os metadados corretamente dos PDFs
3. Renomeia as pastas para o padrão correto
4. Mantém contador de progresso
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime


PROVAS_MD = Path("C:/Users/Tonny/Downloads/projeto_git_prova/provas_md/Provas MD")
LOG_FILE = Path("correcao_nomes_log.txt")


def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {msg}"
    print(log_line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


def extrair_metadados_do_pdf(pdf_name):
    """Extrai orgao, cidade, ano, cargo do nome do PDF."""
    pdf_name_lower = pdf_name.lower()
    
    # Padrao 1: "Prova - Cámara Municipal de <Cidade> - <UF> - <Ano> - <Cargo>.pdf"
    match = re.search(
        r'(?:prova|gabarito)[\s-]*-[\s]*((?:câmara|prefeitura)[\s-]*(?:municipal[\s-]*)?.+?)[\s-]*-[\s]*(?:\w{2})?[\s-]*-[\s]*(\d{4})[\s-]*-[\s]*(.+?)\.pdf',
        pdf_name_lower,
        re.IGNORECASE
    )
    
    if match:
        orgao_cidade = match.group(1).strip()
        ano = match.group(2).strip()
        cargo = match.group(3).strip()
        
        # Determinar se é Camara ou Prefeitura
        if 'camara' in orgao_cidade.lower() or 'câmara' in orgao_cidade.lower():
            orgao = 'Camara'
        elif 'prefeitura' in orgao_cidade.lower():
            orgao = 'Prefeitura'
        else:
            orgao = 'Camara'  # Default
        
        # Extrair cidade (remover "Câmara Municipal de" ou "Prefeitura Municipal de")
        cidade_match = re.search(r'(?:câmara|prefeitura)[\s-]*(?:municipal[\s-]*)?de[\s-]*(.+)$', orgao_cidade, re.IGNORECASE)
        if cidade_match:
            cidade = cidade_match.group(1).strip()
        else:
            cidade = orgao_cidade.replace('Câmara', '').replace('Prefeitura', '').replace('Municipal', '').strip()
        
        # Normalizar
        cidade = re.sub(r'[^\w\s-]', '', cidade).strip().replace(' ', '_')
        cargo = re.sub(r'[^\w\s-]', '', cargo).strip().replace(' ', '_')
        
        return {
            'orgao': orgao,
            'cidade': cidade,
            'ano': ano,
            'cargo': cargo
        }
    
    # Padrao 2: "Prova - <Cidade> - <Ano> - <Cargo>.pdf"
    match = re.search(
        r'(?:prova|gabarito)[\s-]*-[\s]*(.+?)[\s-]*-[\s]*(\d{4})[\s-]*-[\s]*(.+?)\.pdf',
        pdf_name_lower,
        re.IGNORECASE
    )
    
    if match:
        cidade = match.group(1).strip()
        ano = match.group(2).strip()
        cargo = match.group(3).strip()
        
        # Tentar determinar orgao
        if 'camara' in pdf_name_lower or 'câmara' in pdf_name_lower:
            orgao = 'Camara'
        elif 'prefeitura' in pdf_name_lower:
            orgao = 'Prefeitura'
        else:
            orgao = 'Camara'
        
        # Normalizar
        cidade = re.sub(r'[^\w\s-]', '', cidade).strip().replace(' ', '_')
        cargo = re.sub(r'[^\w\s-]', '', cargo).strip().replace(' ', '_')
        
        return {
            'orgao': orgao,
            'cidade': cidade,
            'ano': ano,
            'cargo': cargo
        }
    
    # Padrao 3: mais simples
    match = re.search(r'(\d{4})', pdf_name)
    if match:
        ano = match.group(1)
        # Tentar extrair cidade
        match_cidade = re.search(r'([A-Z][a-z]+(?:[\s-][A-Z][a-z]+)*)', pdf_name)
        cidade = match_cidade.group(1).replace(' ', '_') if match_cidade else 'Nao_Identificado'
        
        return {
            'orgao': 'Camara',
            'cidade': cidade,
            'ano': ano,
            'cargo': 'Nao_Identificado'
        }
    
    return None


def gerar_nome_pasta(metadados):
    """Gera nome da pasta no padrao Camara_<Cidade>_<Ano>_<Cargo>."""
    orgao = metadados.get('orgao', 'Camara')
    cidade = metadados.get('cidade', 'Nao_Identificado')
    ano = metadados.get('ano', '0000')
    cargo = metadados.get('cargo', 'Nao_Identificado')
    
    return f"{orgao}_{cidade}_{ano}_{cargo}"


def main():
    log("="*80)
    log("INICIANDO CORREÇÃO DE NOMES DE PASTAS")
    log("="*80)
    
    # Encontrar pastas com nomes malformados
    pastas_para_corrigir = []
    
    for pasta in PROVAS_MD.iterdir():
        if pasta.is_dir():
            # Verificar se tem PDFs_originais
            pdfs_originais = pasta / 'PDFs_originais'
            if pdfs_originais.exists() and pdfs_originais.is_dir():
                pdfs = list(pdfs_originais.iterdir())
                if pdfs:
                    # Verificar se o nome está malformado (ex: Camara__1992_)
                    if '__' in pasta.name or pasta.name.count('_') < 3:
                        pastas_para_corrigir.append(pasta)
    
    log(f"Pastas para corrigir: {len(pastas_para_corrigir)}")
    
    # Processar cada pasta
    corrigidas = 0
    erros = 0
    
    for i, pasta in enumerate(pastas_para_corrigir, 1):
        log(f"\n{'='*80}")
        log(f"Corrigindo pasta {i}/{len(pastas_para_corrigir)}: {pasta.name}")
        log(f"{'='*80}")
        
        # Ler PDFs
        pdfs_originais = pasta / 'PDFs_originais'
        pdfs = list(pdfs_originais.iterdir())
        
        log(f"PDFs encontrados: {len(pdfs)}")
        for pdf in pdfs:
            log(f"  - {pdf.name}")
        
        # Extrair metadados do primeiro PDF
        metadados = None
        for pdf in pdfs:
            metadados = extrair_metadados_do_pdf(pdf.name)
            if metadados:
                break
        
        if metadados:
            novo_nome = gerar_nome_pasta(metadados)
            log(f"Metadados extraídos:")
            log(f"  Orgão: {metadados.get('orgao')}")
            log(f"  Cidade: {metadados.get('cidade')}")
            log(f"  Ano: {metadados.get('ano')}")
            log(f"  Cargo: {metadados.get('cargo')}")
            log(f"Novo nome: {novo_nome}")
            
            # Verificar se novo nome já existe
            nova_pasta = PROVAS_MD / novo_nome
            if nova_pasta.exists():
                log(f"⚠️  Pasta {novo_nome} já existe!")
                # Adicionar sufixo
                j = 1
                while True:
                    novo_nome_sufix = f"{novo_nome}_v{j}"
                    if not (PROVAS_MD / novo_nome_sufix).exists():
                        novo_nome = novo_nome_sufix
                        break
                    j += 1
                log(f"   Usando: {novo_nome}")
            
            # Renomear pasta
            try:
                shutil.move(str(pasta), str(PROVAS_MD / novo_nome))
                log(f"✅ Pasta renomeada: {pasta.name} → {novo_nome}")
                corrigidas += 1
            except Exception as e:
                log(f"❌ Erro ao renomear: {str(e)}", "ERROR")
                erros += 1
        else:
            log(f"⚠️  Não foi possível extrair metadados dos PDFs")
            erros += 1
        
        log(f"\nProgresso: {corrigidas}/{len(pastas_para_corrigir)} corrigidas | {erros} erros")
    
    log("\n" + "="*80)
    log("RESUMO FINAL")
    log("="*80)
    log(f"✅ Pastas corrigidas: {corrigidas}")
    log(f"❌ Erros: {erros}")


if __name__ == "__main__":
    main()
