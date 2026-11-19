#!/usr/bin/env python3
"""
Criar ZIPs para pastas que têm prova_organizada.md e relatorio_analise.md mas não têm ZIP
"""

import zipfile
from pathlib import Path

BASE = Path(r"C:\Users\Tonny\Downloads\projeto_git_prova\provas_md\Provas MD")

def main():
    print("="*80)
    print("CRIANDO ZIPs FALTANTES")
    print("="*80)
    
    criados = []
    erros = []
    
    for pasta in sorted(BASE.iterdir()):
        if not pasta.is_dir():
            continue
        
        files = list(pasta.iterdir())
        
        tem_md = any(f.name == 'prova_organizada.md' for f in files)
        tem_relatorio = any(f.name == 'relatorio_analise.md' for f in files)
        tem_zip = any(f.name.endswith('_ORGANIZADA.zip') or f.name == 'PROVA_ORGANIZADA.zip' for f in files)
        
        if tem_md and tem_relatorio and not tem_zip:
            # Criar ZIP
            zip_path = pasta / 'PROVA_ORGANIZADA.zip'
            try:
                with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file in files:
                        if file.is_file():
                            zipf.write(str(file), file.name)
                criados.append(pasta.name)
                print(f"✅ ZIP criado: {pasta.name}")
            except Exception as e:
                erros.append((pasta.name, str(e)))
                print(f"❌ Erro em {pasta.name}: {e}")
    
    print(f"\n{'='*80}")
    print("RESUMO")
    print("="*80)
    print(f"Total ZIPs criados: {len(criados)}")
    print(f"Erros: {len(erros)}")
    
    if criados:
        print(f"\nCriados:")
        for p in criados[:30]:
            print(f"  {p}")
        if len(criados) > 30:
            print(f"  ... e {len(criados) - 30} mais")
    
    if erros:
        print(f"\nErros:")
        for p, e in erros[:10]:
            print(f"  {p}: {e}")
        if len(erros) > 10:
            print(f"  ... e {len(erros) - 10} mais")

if __name__ == "__main__":
    main()
