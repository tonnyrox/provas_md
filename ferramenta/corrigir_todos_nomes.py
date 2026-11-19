#!/usr/bin/env python3
"""
Script para corrigir TODOS os nomes de pastas
Inclui correção de:
- Anos duplicados
- Nomes incompletos
- Preposições
- Padronização completa
"""

import os
import re
from pathlib import Path

BASE_GITHUB = Path(r"C:\Users\Tonny\Downloads\projeto_git_prova\provas_md\Provas MD")

def padronizar_nome_completo(nome):
    """
    Padronizar nome completamente
    """
    # Converter para lowercase e depois title case (mas manter siglas)
    # Primeiro, converter tudo para lowercase
    nome = nome.lower()
    
    # Remover anos duplicados (pattern: _ano_ano_)
    nome = re.sub(r'(_20\d{2}){2,}', r'\1', nome)
    nome = re.sub(r'(_19\d{2}){2,}', r'\1', nome)
    
    # Remover números soltos no final (como _1, _2, _2018 no final)
    # Mas manter anos que são parte do nome
    # Se terminar com _ano, remover apenas se for duplicado
    
    # Remover patterns como "_de_", "_do_", "_da_", etc.
    nome = re.sub(r'_de_|_do_|_da_|_das_|_dos_|_em_|_para_|_a_|_o_', '_', nome)
    
    # Remover espacios duplicados
    nome = re.sub(r'\s+', '_', nome)
    
    # Remover underscores consecutivos
    nome = re.sub(r'__+', '_', nome)
    
    # Remover underscore no início ou final
    nome = nome.strip('_')
    
    # Capitalizar corretamente
    # Separar por underscore e capitalizar cada parte
    partes = nome.split('_')
    partes_capitalizadas = []
    
    for parte in partes:
        if not parte:
            continue
        
        # Palavras que devem ficar em lowercase
        lowercase_words = ['de', 'do', 'da', 'das', 'dos', 'em', 'a', 'o', 'as', 'os', 
                          'para', 'por', 'com', 'sem', 'na', 'no', 'nas', 'nos',
                          'e', 'ou', 'outras']
        
        if parte in lowercase_words:
            partes_capitalizadas.append(parte)
        else:
            # Capitalizar: primeira letra maiúscula, resto minúsculo
            # Mas manter siglas como UNESCO, CNPJ, etc.
            if parte.isupper() and len(parte) <= 5:
                partes_capitalizadas.append(parte)
            else:
                partes_capitalizadas.append(parte.capitalize())
    
    nome = '_'.join(partes_capitalizadas)
    
    # Remover underscores consecutivos novamente
    nome = re.sub(r'__+', '_', nome)
    nome = nome.strip('_')
    
    return nome

def verificar_nome(nome):
    """
    Verificar se nome precisa de correção
    """
    padronizado = padronizar_nome_completo(nome)
    
    # Verificar se tem problemas
    problemas = []
    
    # Anos duplicados
    anos = re.findall(r'_20\d{2}_', nome)
    if len(anos) > 1:
        problemas.append("anos duplicados")
    
    # Nomes muito curtos
    if len(nome.split('_')) < 4:
        problemas.append("nome curto")
    
    # Termina com "_de", "_em", etc.
    if re.search(r'_(de|do|da|das|dos|em|para)$', nome, re.IGNORECASE):
        problemas.append("termina com preposição")
    
    # Tem números soltos no final
    if re.search(r'_\d+$', nome):
        problemas.append("número solto no final")
    
    return padronizado, problemas

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
        return True
    except Exception as e:
        print(f"❌ Erro renomeando {pasta_antiga.name}: {e}")
        return False

def main():
    """Função principal"""
    print("="*80)
    print("CORRIGINDO TODOS OS NOMES DE PASTAS")
    print("="*80)
    
    pastas = sorted(BASE_GITHUB.iterdir())
    renomeados = []
    pulados = []
    
    for pasta in pastas:
        if not pasta.is_dir():
            continue
        
        nome_antigo = pasta.name
        novo_nome, problemas = verificar_nome(nome_antigo)
        
        if problemas:
            print(f"\n{pasta.name} -> {novo_nome}")
            print(f"  Problemas: {', '.join(problemas)}")
            
            if renomear_pasta(pasta, novo_nome):
                renomeados.append((nome_antigo, novo_nome))
                print(f"  ✅ Renomeado")
            else:
                pulados.append((nome_antigo, novo_nome))
                print(f"  ⚠️  Pulado")
    
    print("\n" + "="*80)
    print("RESUMO")
    print("="*80)
    print(f"Total corrigidos: {len(renomeados)}")
    print(f"Pulados: {len(pulados)}")
    
    if renomeados:
        print("\nCorrigidos:")
        for antigo, novo in renomeados[:30]:
            print(f"  {antigo} -> {novo}")
        if len(renomeados) > 30:
            print(f"  ... e {len(renomeados) - 30} mais")
    
    if pulados:
        print("\nPulados (já existem):")
        for antigo, novo in pulados[:10]:
            print(f"  {antigo} -> {novo}")
        if len(pulados) > 10:
            print(f"  ... e {len(pulados) - 10} mais")

if __name__ == "__main__":
    main()
