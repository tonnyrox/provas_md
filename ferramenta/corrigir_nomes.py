#!/usr/bin/env python3
"""
Script para corrigir nomes de pastas mal formadas
"""

import os
import re
import shutil
from pathlib import Path

BASE_GITHUB = Path(r"C:\Users\Tonny\Downloads\projeto_git_prova\provas_md\Provas MD")

def padronizar_nome(nome):
    """
    Padronizar nome da pasta
    """
    # Remover anos duplicados
    # Pattern: Orgao_Cidade_Ano_Cargo_Ano ou Orgao_Cidade_Ano_Ano_Cargo
    nome = re.sub(r'(_20\d{2}){2,}', r'\1', nome)
    nome = re.sub(r'(_19\d{2}){2,}', r'\1', nome)
    
    # Remover números soltos no final
    nome = re.sub(r'_\d+$', '', nome)
    
    # Remover "_1", "_2", etc. no final
    nome = re.sub(r'_\d+$', '', nome)
    
    # Remover "de", "do", "da", "em" como palavras separadas
    nome = re.sub(r'_de_|_do_|_da_|_das_|_dos_|_em_|_para_', '_', nome)
    
    # Remover spaces que possam ter sido criados
    nome = re.sub(r'\s+', '_', nome)
    
    # Remover underscores consecutivos
    nome = re.sub(r'__+', '_', nome)
    
    # Remover underscore no início ou final
    nome = nome.strip('_')
    
    return nome

def renomear_pasta(pasta_antiga, novo_nome):
    """
    Renomear pasta
    """
    pasta_nova = pasta_antiga.parent / novo_nome
    
    if pasta_nova.exists():
        print(f"⚠️  {novo_nome} já existe, pulando {pasta_antiga.name}")
        return False
    
    try:
        pasta_antiga.rename(pasta_nova)
        print(f"✅ Renomeado: {pasta_antiga.name} -> {novo_nome}")
        return True
    except Exception as e:
        print(f"❌ Erro renomeando {pasta_antiga.name}: {e}")
        return False

def main():
    """Função principal"""
    print("="*80)
    print("CORRIGINDO NOMES DE PASTAS")
    print("="*80)
    
    pastas = sorted(BASE_GITHUB.iterdir())
    renomeados = []
    erros = []
    
    for pasta in pastas:
        if not pasta.is_dir():
            continue
        
        novo_nome = padronizar_nome(pasta.name)
        
        if novo_nome != pasta.name:
            if renomear_pasta(pasta, novo_nome):
                renomeados.append((pasta.name, novo_nome))
            else:
                erros.append(pasta.name)
    
    print("\n" + "="*80)
    print("RESUMO")
    print("="*80)
    print(f"Total renomeados: {len(renomeados)}")
    print(f"Erros: {len(erros)}")
    
    if renomeados:
        print("\nRenomeados:")
        for antigo, novo in renomeados[:20]:
            print(f"  {antigo} -> {novo}")
        if len(renomeados) > 20:
            print(f"  ... e {len(renomeados) - 20} mais")
    
    if erros:
        print("\nErros:")
        for e in erros[:10]:
            print(f"  {e}")
        if len(erros) > 10:
            print(f"  ... e {len(erros) - 10} mais")

if __name__ == "__main__":
    main()
