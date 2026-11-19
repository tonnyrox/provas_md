#!/usr/bin/env python3
"""
Script para remover pastas incompletas
Mantém apenas pastas com:
- prova_organizada.md
- relatorio_analise.md
- *ORGANIZADA.zip
- pelo menos um PDF
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path(r"C:\Users\Tonny\Downloads\projeto_git_prova\provas_md\Provas MD")

# Tempo limite: pastas modificadas há menos de 2 horas
TEMPO_LIMITE = timedelta(hours=2)

def pasta_esta_completa(pasta):
    """
    Verificar se pasta tem todos os arquivos necessários
    """
    files = list(pasta.iterdir())
    
    tem_md = any(f.name == 'prova_organizada.md' for f in files)
    tem_relatorio = any(f.name == 'relatorio_analise.md' for f in files)
    tem_zip = any(f.name.endswith('_ORGANIZADA.zip') or f.name == 'PROVA_ORGANIZADA.zip' for f in files)
    tem_pdf = any(f.name.lower().endswith('.pdf') for f in files)
    
    return tem_md and tem_relatorio and tem_zip and tem_pdf

def pasta_esta_vazia(pasta):
    """
    Verificar se pasta está vazia ou tem apenas arquivos temporários
    """
    files = list(pasta.iterdir())
    # Considera vazia se não tem PDFs
    return not any(f.name.lower().endswith('.pdf') for f in files)

def main():
    print("="*80)
    print("LIMPANDO PASTAS INCOMPLETAS")
    print("="*80)
    
    removidas = []
    mantidas = []
    
    agora = datetime.now()
    
    for pasta in sorted(BASE.iterdir()):
        if not pasta.is_dir():
            continue
        
        # Verificar se é pasta recente (criada há menos de 2 horas)
        stat = pasta.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        
        e_recente = (agora - mod_time) < TEMPO_LIMITE
        
        if not e_recente:
            mantidas.append(pasta.name)
            continue
        
        # Verificar se está completa
        if pasta_esta_completa(pasta):
            mantidas.append(pasta.name)
            continue
        
        # Verificar se está vazia (sem PDFs)
        if pasta_esta_vazia(pasta):
            try:
                shutil.rmtree(str(pasta))
                removidas.append(pasta.name)
                print(f"✅ Removida (vazia): {pasta.name}")
            except Exception as e:
                print(f"❌ Erro removendo {pasta.name}: {e}")
        else:
            # Tem PDFs mas está incompleta - manter por enquanto
            mantidas.append(pasta.name)
            print(f"⚠️  Mantida (incompleta mas com PDFs): {pasta.name}")
    
    print("\n" + "="*80)
    print("RESUMO")
    print("="*80)
    print(f"Removidas: {len(removidas)}")
    print(f"Mantidas: {len(mantidas)}")
    
    if removidas:
        print(f"\nRemovidas:")
        for p in removidas[:30]:
            print(f"  {p}")
        if len(removidas) > 30:
            print(f"  ... e {len(removidas) - 30} mais")
    
    # Salvar log
    with open(BASE / "log_limpeza.txt", 'w', encoding='utf-8') as f:
        f.write(f"Limpeza em: {agora}\n\n")
        f.write(f"Removidas: {len(removidas)}\n")
        f.write(f"Mantidas: {len(mantidas)}\n\n")
        f.write("Removidas:\n")
        for p in removidas:
            f.write(f"  - {p}\n")
    
    print(f"\n✅ Limpeza concluída! Log em {BASE / 'log_limpeza.txt'}")

if __name__ == "__main__":
    main()
