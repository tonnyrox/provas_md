#!/usr/bin/env python3
"""
Verificar quais pastas estão completas
"""

import os
from pathlib import Path

BASE = Path(r"C:\Users\Tonny\Downloads\projeto_git_prova\provas_md\Provas MD")

def main():
    completas = []
    incompletas = []
    
    for pasta in sorted(BASE.iterdir()):
        if not pasta.is_dir():
            continue
        
        files = list(pasta.iterdir())
        
        tem_md = 'prova_organizada.md' in [f.name for f in files]
        tem_relatorio = 'relatorio_analise.md' in [f.name for f in files]
        tem_zip = any(f.name.endswith('_ORGANIZADA.zip') or f.name == 'PROVA_ORGANIZADA.zip' for f in files)
        tem_pdf = any(f.name.lower().endswith('.pdf') for f in files)
        
        if tem_md and tem_relatorio and tem_zip:
            completas.append(pasta.name)
        else:
            status = []
            if not tem_md: status.append('sem MD')
            if not tem_relatorio: status.append('sem relatorio')
            if not tem_zip: status.append('sem ZIP')
            if not tem_pdf: status.append('sem PDF')
            incompletas.append((pasta.name, status))
    
    print(f"Pastas completas: {len(completas)}")
    print(f"Pastas incompletas: {len(incompletas)}")
    print(f"Total: {len(completas) + len(incompletas)}")
    
    if incompletas:
        print(f"\nIncompletas:")
        for pasta, status in incompletas[:30]:
            print(f"  {pasta}: {', '.join(status)}")
        if len(incompletas) > 30:
            print(f"  ... e {len(incompletas) - 30} mais")
    
    # Salvar lista completa
    with open(BASE / "lista_completas.txt", 'w', encoding='utf-8') as f:
        f.write("Pastas completas:\n")
        for p in completas:
            f.write(f"  - {p}\n")
        
        f.write("\nPastas incompletas:\n")
        for p, s in incompletas:
            f.write(f"  - {p}: {', '.join(s)}\n")
    
    print(f"\nLista salva em {BASE / 'lista_completas.txt'}")

if __name__ == "__main__":
    main()
