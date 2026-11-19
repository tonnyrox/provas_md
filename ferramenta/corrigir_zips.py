#!/usr/bin/env python3
"""
Script para corrigir os ZIPs das provas que estão com problemas.
Regenera os ZIPs das 4 provas com erros:
- Camara_Belo_Jardim_2015_Agente_Administrativo
- Camara_Cacapava_2015_Agente_Administrativo
- Camara_Chapeco_2025_Analista_de_Comunicacao
- Camara_Clevelandia_2017_Agente_Administrativo_I
"""

import os
import zipfile
from pathlib import Path
import shutil


def criar_zip_corretamente(pasta_prova: Path):
    """Recria o ZIP com os arquivos corretos."""
    print(f"📁 Processando: {pasta_prova.name}")
    
    # Arquivos que DEVEM estar no ZIP
    arquivos_para_zip = []
    
    # Adicionar prova_organizada.md
    prova_md = pasta_prova / "prova_organizada.md"
    if prova_md.exists():
        arquivos_para_zip.append(("prova_organizada.md", prova_md))
    else:
        print(f"  ❌ Arquivo prova_organizada.md não encontrado!")
        return False
    
    # Adicionar relatorio_analise.md
    relatorio_md = pasta_prova / "relatorio_analise.md"
    if relatorio_md.exists():
        arquivos_para_zip.append(("relatorio_analise.md", relatorio_md))
    else:
        print(f"  ❌ Arquivo relatorio_analise.md não encontrado!")
        return False
    
    # Adicionar pasta imagens (se existir)
    pasta_imagens = pasta_prova / "imagens"
    if pasta_imagens.exists() and pasta_imagens.is_dir():
        for img_file in pasta_imagens.iterdir():
            if img_file.is_file():
                arquivos_para_zip.append((f"imagens/{img_file.name}", img_file))
    
    # Criar o ZIP
    zip_path = pasta_prova / "PROVA_ORGANIZADA.zip"
    
    # Remover ZIP antigo se existir
    if zip_path.exists():
        zip_path.unlink()
    
    # Criar novo ZIP
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for arcname, filepath in arquivos_para_zip:
            z.write(filepath, arcname)
    
    # Verificar se o ZIP foi criado corretamente
    with zipfile.ZipFile(zip_path, 'r') as z:
        conteudo = z.namelist()
        print(f"  ✅ ZIP criado com {len(conteudo)} arquivos:")
        for item in conteudo:
            print(f"     - {item}")
    
    return True


def main():
    repo_path = Path("C:/Users/Tonny/Downloads/projeto_git_prova/provas_md/Provas MD")
    
    # Lista das provas com problemas
    provas_com_erro = [
        "Camara_Belo_Jardim_2015_Agente_Administrativo",
        "Camara_Cacapava_2015_Agente_Administrativo",
        "Camara_Chapeco_2025_Analista_de_Comunicacao",
        "Camara_Clevelandia_2017_Agente_Administrativo_I"
    ]
    
    print("=" * 80)
    print("CORRIGINDO ZIPs DAS PROVAS COM ERROS")
    print("=" * 80)
    
    corrigidas = 0
    falhadas = 0
    
    for prova_nome in provas_com_erro:
        pasta = repo_path / prova_nome
        if pasta.exists():
            if criar_zip_corretamente(pasta):
                corrigidas += 1
            else:
                falhadas += 1
        else:
            print(f"❌ Pasta não encontrada: {prova_nome}")
            falhadas += 1
    
    print("\n" + "=" * 80)
    print("RESUMO")
    print("=" * 80)
    print(f"✅ Corrigidas: {corrigidas}/{len(provas_com_erro)}")
    print(f"❌ Falhadas: {falhadas}/{len(provas_com_erro)}")
    
    if falhadas == 0:
        print("\n🎉 Todos os ZIPs foram corrigidos com sucesso!")
    else:
        print(f"\n⚠️  {falhadas} provas não puderam ser corrigidas")


if __name__ == "__main__":
    main()
