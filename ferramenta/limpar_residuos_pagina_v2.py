#!/usr/bin/env python3
"""
Script V2 para remover resíduos de numeração de página do PDF.
Versão mais agressiva que remove:
- Página X
- Page X
- Página X de Y
- Page X of Y
- Qualquer variação com ou sem formatação > 
"""

import re
from pathlib import Path


def limpar_residuos_pagina_v2(arquivo_md: Path) -> bool:
    """Remove resíduos de paginação de um arquivo markdown."""
    with open(arquivo_md, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Padrões mais agressivos
    padroes = [
        # Página X (com ou sem formatação)
        r'(?:^|\n)(?:>\s*)?Página\s+\d+(?:\s+de\s+\d+)?\s*(?:\n|$)',
        r'(?:^|\n)(?:>\s*)?Page\s+\d+(?:\s+of\s+\d+)?\s*(?:\n|$)',
        # Apenas o número em linha separada (com > ou sem)
        r'(?:^|\n)(?:>\s*)?\d+\s*(?:\n|$)',
        # Linhas com apenas "Página" ou "Page"
        r'(?:^|\n)(?:>\s*)?(?:Página|Page)\s*(?:\n|$)',
    ]
    
    for padrao in padroes:
        content = re.sub(padrao, '\n', content, flags=re.MULTILINE | re.IGNORECASE)
    
    # Remover linhas com apenas > 
    content = re.sub(r'^>\s*$', '', content, flags=re.MULTILINE)
    
    # Remover múltiplas linhas vazias
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Remover espaços em branco no início de linhas que começaram com > Página
    content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)
    
    if content != original:
        with open(arquivo_md, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    repo_path = Path("C:/Users/Tonny/Downloads/projeto_git_prova/provas_md/Provas MD")
    
    # Todas as provas
    provas_com_aviso = [
        "Camara_Alto_Paraiso_2024_Agente_Administrativo",
        "Camara_Americana_2024_Analista_de_Comunicacao",
        "Camara_Araraquara_2016_Assistente_de_Cerimonial",
        "Camara_Araripina_2020_Agente_Administrativo_Grupo_02",
        "Camara_Araripina_2024_Agente_Administrativo",
        "Camara_Cacapava_2025_Agente_Administrativo",
        "Camara_Calumbi_2024_Agente_Administrativo",
        "Camara_Caroebe_2014_Nivel_Fundamental",
        "Camara_Caroebe_2014_Nivel_Medio",
        "Camara_Clevelandia_2011_Agente_Administrativo_I",
        "Camara_Clevelandia_2011_Agente_Administrativo_II",
        "Camara_Ouro_Preto_do_Oeste_2024_Agente_Administrativo",
        "Camara_Sao_Luiz_do_Paraitinga_2015_Analista_de_Comunicacao"
    ]
    
    print("=" * 80)
    print("LIMPANDO RESÍDUOS DE NUMERAÇÃO DE PÁGINA - VERSÃO 2")
    print("=" * 80)
    
    limpas = 0
    sem_alteracao = 0
    
    for prova_nome in provas_com_aviso:
        pasta = repo_path / prova_nome
        arquivo_md = pasta / "prova_organizada.md"
        
        if arquivo_md.exists():
            if limpar_residuos_pagina_v2(arquivo_md):
                print(f"✅ {prova_nome}: resíduos removidos")
                limpas += 1
                
                # Regenerar o ZIP
                import zipfile
                zip_path = pasta / "PROVA_ORGANIZADA.zip"
                if zip_path.exists():
                    zip_path.unlink()
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                    z.write(arquivo_md, "prova_organizada.md")
                    relatorio = pasta / "relatorio_analise.md"
                    if relatorio.exists():
                        z.write(relatorio, "relatorio_analise.md")
                    pasta_imagens = pasta / "imagens"
                    if pasta_imagens.exists():
                        for img in pasta_imagens.iterdir():
                            if img.is_file():
                                z.write(img, f"imagens/{img.name}")
                
                print(f"   ✅ ZIP regenerado")
            else:
                print(f"⚪ {prova_nome}: sem resíduos encontrados ou já limpo")
                sem_alteracao += 1
        else:
            print(f"❌ {prova_nome}: arquivo não encontrado")
    
    print("\n" + "=" * 80)
    print("RESUMO")
    print("=" * 80)
    print(f"✅ Provas limpas: {limpas}/{len(provas_com_aviso)}")
    print(f"⚪ Sem alteração: {sem_alteracao}/{len(provas_com_aviso)}")


if __name__ == "__main__":
    main()
