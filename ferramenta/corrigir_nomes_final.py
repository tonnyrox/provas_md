#!/usr/bin/env python3
"""
Script final para corrigir TODOS os nomes de pastas
"""

import re
from pathlib import Path

BASE = Path(r"C:\Users\Tonny\Downloads\projeto_git_prova\provas_md\Provas MD")

def padronizar_nome_final(nome):
    """
    Padronizar nome final
    """
    # Converter para lowercase
    nome = nome.lower()
    
    # Remover anos duplicados
    nome = re.sub(r'(_20\d{2}){2,}', r'\1', nome)
    nome = re.sub(r'(_19\d{2}){2,}', r'\1', nome)
    
    # Remover "_v1", "_v2", etc.
    nome = re.sub(r'_v\d+$', '', nome)
    
    # Remover números soltos no final
    nome = re.sub(r'_\d+$', '', nome)
    
    # Remover "_-" ou "--"
    nome = re.sub(r'_-_|--|_\-_', '_', nome)
    
    # Remover preposições isoladas
    nome = re.sub(r'_de_|_do_|_da_|_das_|_dos_|_em_|_a_|_o_|_para_|_por_', '_', nome)
    
    # Remover espaços
    nome = re.sub(r'\s+', '_', nome)
    
    # Remover underscores consecutivos
    nome = re.sub(r'__+', '_', nome)
    
    # Remover underscore no início ou final
    nome = nome.strip('_')
    
    # Capitalizar corretamente
    partes = nome.split('_')
    partes_capitalizadas = []
    
    lowercase_words = {'de', 'do', 'da', 'das', 'dos', 'em', 'a', 'o', 'as', 'os', 
                      'para', 'por', 'com', 'sem', 'na', 'no', 'nas', 'nos',
                      'e', 'ou', 'outras', 'i', 'ii', 'iii', 'iv', 'v', 'vi',
                      '20', '40h'}
    
    for parte in partes:
        if not parte:
            continue
        if parte in lowercase_words:
            partes_capitalizadas.append(parte)
        else:
            # Capitalizar
            partes_capitalizadas.append(parte.capitalize())
    
    nome = '_'.join(partes_capitalizadas)
    
    # Remover underscores consecutivos
    nome = re.sub(r'__+', '_', nome)
    nome = nome.strip('_')
    
    return nome

def main():
    print("="*80)
    print("CORRIGINDO NOMES FINAIS")
    print("="*80)
    
    renomeados = []
    
    for pasta in sorted(BASE.iterdir()):
        if not pasta.is_dir():
            continue
        
        novo_nome = padronizar_nome_final(pasta.name)
        
        if novo_nome != pasta.name:
            pasta_nova = pasta.parent / novo_nome
            
            if pasta_nova.exists():
                print(f"⚠️  {novo_nome} já existe, pulando {pasta.name}")
                continue
            
            try:
                pasta.rename(pasta_nova)
                renomeados.append((pasta.name, novo_nome))
                print(f"✅ {pasta.name} -> {novo_nome}")
            except Exception as e:
                print(f"❌ Erro renomeando {pasta.name}: {e}")
    
    print(f"\n{'='*80}")
    print("RESUMO")
    print("="*80)
    print(f"Total renomeados: {len(renomeados)}")
    
    if renomeados:
        print(f"\nRenomeados:")
        for antigo, novo in renomeados:
            print(f"  {antigo} -> {novo}")

if __name__ == "__main__":
    main()
