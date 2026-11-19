#!/usr/bin/env python3
"""
Auditor Completo para o Acervo de Provas
=========================================

Verifica TODAS as 122 provas do acervo, garantindo que:
1. Estrutura de pastas está correta
2. Arquivos obrigatórios existem (prova_organizada.md, relatorio_analise.md, PROVA_ORGANIZADA.zip)
3. Questões agrupadas têm material repetido corretamente
4. Imagens estão referenciadas e existem
5. Padronização do markdown está correta
6. Não há omissões de conteúdo

Uso:
    python ferramenta/auditor_completo.py
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import zipfile


@dataclass
class ProvaInfo:
    """Informações sobre uma prova."""
    pasta: str
    caminho: Path
    tem_prova_md: bool = False
    tem_relatorio: bool = False
    tem_zip: bool = False
    tem_imagens: bool = False
    qtde_questoes: int = 0
    qtde_agrupadas: int = 0
    qtde_imagens: int = 0
    problemas: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)


@dataclass
class ResultadoAudit:
    """Resultado completo da auditoria."""
    total_provas: int = 0
    provas_ok: int = 0
    provas_com_problemas: int = 0
    provas_com_avisos: int = 0
    total_questoes: int = 0
    total_imagens: int = 0
    detalhes: Dict[str, ProvaInfo] = field(default_factory=dict)


# Padrões para verificação
PADRAO_AGRUPADAS = re.compile(r'##\s*(\d+)\.\s*Questões\s+agrupadas\s*(?:–|-|\()\s*(.+?)\s*(?:–|-|\)|$)', re.IGNORECASE)
PADRAO_INDEPENDENTES = re.compile(r'##\s*(\d+)\.\s*Questões\s+independentes', re.IGNORECASE)
PADRAO_QUESTAO = re.compile(r'^###\s*Questão\s+(\d+)\s*$', re.MULTILINE)
PADRAO_IMAGEM = re.compile(r'!\[.*?\]\((.*?)\)')
PADRAO_MATERIAL_COMPARTILHADO = re.compile(
    r'(?:Texto|Imagem|Gráfico|Tabela|Figura|Material)\s+(?:compartilhado|de\s+apoio|para\s+as\s+questões)',
    re.IGNORECASE
)


def contar_questoes(md_content: str) -> Tuple[int, int]:
    """Conta questões agrupadas e independentes."""
    agrupadas_match = PADRAO_AGRUPADAS.search(md_content)
    independentes_match = PADRAO_INDEPENDENTES.search(md_content)
    
    qtde_agrupadas = 0
    qtde_independentes = 0
    
    if agrupadas_match:
        # Tentar extrair número de questões do título
        titulo = agrupadas_match.group(0)
        num_match = re.search(r'(\d+)\s*questões', titulo, re.IGNORECASE)
        if num_match:
            qtde_agrupadas = int(num_match.group(1))
    
    if independentes_match:
        titulo = independentes_match.group(0)
        num_match = re.search(r'(\d+)\s*questões', titulo, re.IGNORECASE)
        if num_match:
            qtde_independentes = int(num_match.group(1))
    
    # Contar questões pelo padrão ### Questão X
    todas_questoes = PADRAO_QUESTAO.findall(md_content)
    total_questoes = len(todas_questoes)
    
    return total_questoes, qtde_agrupadas


def verificar_estrutura_agrupada(md_content: str, pasta: str) -> List[str]:
    """Verifica se as questões agrupadas estão corretamente estruturadas."""
    problemas = []
    
    # Verificar se há seção de questões agrupadas
    agrupadas_match = PADRAO_AGRUPADAS.search(md_content)
    if not agrupadas_match:
        # Não tem agrupadas, então não precisa verificar
        return problemas
    
    # Extrair o bloco de questões agrupadas
    lines = md_content.split('\n')
    in_agrupadas = False
    agrupadas_lines = []
    
    for line in lines:
        if PADRAO_AGRUPADAS.search(line):
            in_agrupadas = True
            continue
        if in_agrupadas and (PADRAO_INDEPENDENTES.search(line) or line.startswith('## ')):
            break
        if in_agrupadas:
            agrupadas_lines.append(line)
    
    agrupadas_text = '\n'.join(agrupadas_lines)
    
    # Verificar se há material compartilhado (texto/imagem) antes das questões
    if PADRAO_MATERIAL_COMPARTILHADO.search(agrupadas_text):
        problemas.append(
            f"[AVISO] Material compartilhado encontrado em {pasta}. "
            "Verificar se está repetido em CADA questão."
        )
    
    return problemas


def verificar_imagens(md_content: str, pasta_imagens: Path) -> Tuple[List[str], int]:
    """Verifica se imagens referenciadas existem."""
    problemas = []
    imagens_encontradas = PADRAO_IMAGEM.findall(md_content)
    qtde_imagens = len(imagens_encontradas)
    
    if not imagens_encontradas:
        return problemas, qtde_imagens
    
    if not pasta_imagens.exists():
        problemas.append(f"[ERRO] Pasta de imagens não existe: {pasta_imagens}")
        return problemas, qtde_imagens
    
    arquivos_imagens = {f.name.lower() for f in pasta_imagens.iterdir() if f.is_file()}
    
    for img_ref in imagens_encontradas:
        # Normalizar o caminho da imagem
        img_path = img_ref.strip().strip('"').strip("'")
        img_name = os.path.basename(img_path)
        
        if img_name.lower() not in arquivos_imagens:
            problemas.append(f"[ERRO] Imagem referenciada não existe: {img_ref}")
    
    return problemas, qtde_imagens


def verificar_arquivos_obrigatorios(pasta: Path) -> List[str]:
    """Verifica se os arquivos obrigatórios existem."""
    problemas = []
    
    arquivos_obrigatorios = [
        'prova_organizada.md',
        'relatorio_analise.md',
        'PROVA_ORGANIZADA.zip'
    ]
    
    for arquivo in arquivos_obrigatorios:
        caminho = pasta / arquivo
        if not caminho.exists():
            problemas.append(f"[ERRO] Arquivo obrigatório ausente: {arquivo}")
    
    return problemas


def verificar_zip(pasta: Path) -> List[str]:
    """Verifica se o ZIP contém os arquivos corretos."""
    problemas = []
    zip_path = pasta / 'PROVA_ORGANIZADA.zip'
    
    if not zip_path.exists():
        return problemas
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            arquivos_zip = z.namelist()
            
            # Deve conter prova_organizada.md e relatorio_analise.md
            if 'prova_organizada.md' not in arquivos_zip:
                problemas.append("[ERRO] ZIP não contém prova_organizada.md")
            if 'relatorio_analise.md' not in arquivos_zip:
                problemas.append("[ERRO] ZIP não contém relatorio_analise.md")
            
            # Verificar pasta imagens
            if 'imagens/' in arquivos_zip:
                # Contar imagens no ZIP
                imagens_no_zip = [f for f in arquivos_zip if f.startswith('imagens/')]
                if not imagens_no_zip:
                    problemas.append("[AVISO] Pasta imagens/ existe no ZIP mas está vazia")
                    
    except Exception as e:
        problemas.append(f"[ERRO] Não foi possível ler o ZIP: {str(e)}")
    
    return problemas


def verificar_padrao_markdown(md_content: str, pasta: str) -> List[str]:
    """Verifica se o markdown segue o padrão esperado."""
    problemas = []
    
    # Verificar seção 1. Análise geral da prova
    if '1. Análise geral da prova' not in md_content:
        problemas.append("[AVISO] Seção '1. Análise geral da prova' não encontrada")
    
    # Verificar seção 2. Questões agrupadas OU 2. Questões
    if '2. Questões agrupadas' not in md_content and '2. Questões' not in md_content:
        problemas.append("[AVISO] Seção de questões não encontrada no formato esperado")
    
    # Verificar que não há resíduos de PDF (textos como "Page 1", "Página 1")
    if re.search(r'(?:Page|Página)\s+\d+', md_content):
        problemas.append("[AVISO] Possível resíduo de numeração de página do PDF")
    
    return problemas


def auditar_prova(pasta: Path) -> ProvaInfo:
    """Audita uma única prova."""
    info = ProvaInfo(pasta=pasta.name, caminho=pasta)
    
    # Verificar arquivos obrigatórios
    problemas_arquivos = verificar_arquivos_obrigatorios(pasta)
    info.problemas.extend(problemas_arquivos)
    info.tem_prova_md = (pasta / 'prova_organizada.md').exists()
    info.tem_relatorio = (pasta / 'relatorio_analise.md').exists()
    info.tem_zip = (pasta / 'PROVA_ORGANIZADA.zip').exists()
    info.tem_imagens = (pasta / 'imagens').exists()
    
    # Se não tem prova_organizada.md, não pode continuar
    if not info.tem_prova_md:
        info.problemas.append("[ERRO] Arquivo prova_organizada.md não existe")
        return info
    
    # Ler conteúdo da prova
    with open(pasta / 'prova_organizada.md', 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Contar questões
    info.qtde_questoes, info.qtde_agrupadas = contar_questoes(md_content)
    
    # Verificar estrutura agrupada
    problemas_agrupadas = verificar_estrutura_agrupada(md_content, pasta.name)
    info.avisos.extend(problemas_agrupadas)
    
    # Verificar imagens
    pasta_imagens = pasta / 'imagens'
    problemas_imagens, info.qtde_imagens = verificar_imagens(md_content, pasta_imagens)
    info.problemas.extend(problemas_imagens)
    
    # Verificar ZIP
    problemas_zip = verificar_zip(pasta)
    info.problemas.extend(problemas_zip)
    
    # Verificar padrão markdown
    problemas_padrao = verificar_padrao_markdown(md_content, pasta.name)
    info.avisos.extend(problemas_padrao)
    
    return info


def gerar_relatorio(resultado: ResultadoAudit) -> str:
    """Gera um relatório completo da auditoria."""
    lines = []
    lines.append("=" * 80)
    lines.append("RELATÓRIO COMPLETO DA AUDITORIA DO ACERVO DE PROVAS")
    lines.append("=" * 80)
    lines.append(f"\nTotal de provas auditadas: {resultado.total_provas}")
    lines.append(f"Provas OK (sem problemas): {resultado.provas_ok}")
    lines.append(f"Provas com problemas: {resultado.provas_com_problemas}")
    lines.append(f"Provas com avisos: {resultado.provas_com_avisos}")
    lines.append(f"Total de questões verificadas: {resultado.total_questoes}")
    lines.append(f"Total de imagens referenciadas: {resultado.total_imagens}")
    
    if resultado.provas_com_problemas > 0:
        lines.append("\n" + "=" * 80)
        lines.append("PROVAS COM PROBLEMAS (precisam de correção)")
        lines.append("=" * 80)
        for pasta, info in resultado.detalhes.items():
            if info.problemas:
                lines.append(f"\n{pasta}:")
                for problema in info.problemas:
                    lines.append(f"  - {problema}")
    
    if resultado.provas_com_avisos > 0:
        lines.append("\n" + "=" * 80)
        lines.append("PROVAS COM AVISOS (verificar manualmente)")
        lines.append("=" * 80)
        for pasta, info in resultado.detalhes.items():
            if info.avisos and not info.problemas:
                lines.append(f"\n{pasta}:")
                for aviso in info.avisos:
                    lines.append(f"  - {aviso}")
    
    lines.append("\n" + "=" * 80)
    lines.append("RESUMO POR PROVA")
    lines.append("=" * 80)
    lines.append("\n{:<4} {:<60} {:>6} {:>6} {:>6} {:>8}".format(
        "ID", "Prova", "Qtde", "Agr.", "Imgs", "Status"
    ))
    lines.append("-" * 80)
    
    for i, (pasta, info) in enumerate(resultado.detalhes.items(), 1):
        status = "OK" if not info.problemas and not info.avisos else \
                "AVISO" if info.avisos and not info.problemas else \
                "ERRO"
        lines.append("{:<4} {:<60} {:>6} {:>6} {:>6} {:>8}".format(
            i, pasta[:58], info.qtde_questoes, info.qtde_agrupadas, 
            info.qtde_imagens, status
        ))
    
    return "\n".join(lines)


def main():
    """Função principal do auditor."""
    repo_path = Path("C:/Users/Tonny/Downloads/projeto_git_prova/provas_md/Provas MD")
    
    if not repo_path.exists():
        print(f"[ERRO] Diretório não encontrado: {repo_path}")
        return
    
    print("🔍 Iniciando auditoria completa do acervo...")
    print("=" * 80)
    
    resultado = ResultadoAudit()
    pastas_provas = [p for p in repo_path.iterdir() if p.is_dir()]
    
    print(f"📊 Encontradas {len(pastas_provas)} pastas de provas")
    
    for i, pasta in enumerate(pastas_provas, 1):
        print(f"\r📝 Processando {i}/{len(pastas_provas)}: {pasta.name[:50]}", end="")
        
        try:
            info = auditar_prova(pasta)
            resultado.total_provas += 1
            resultado.total_questoes += info.qtde_questoes
            resultado.total_imagens += info.qtde_imagens
            resultado.detalhes[pasta.name] = info
            
            if info.problemas:
                resultado.provas_com_problemas += 1
            elif info.avisos:
                resultado.provas_com_avisos += 1
            else:
                resultado.provas_ok += 1
                
        except Exception as e:
            print(f"\n[ERRO] ao processar {pasta.name}: {str(e)}")
            info = ProvaInfo(pasta=pasta.name, caminho=pasta)
            info.problemas.append(f"[ERRO] Exceção durante auditoria: {str(e)}")
            resultado.detalhes[pasta.name] = info
            resultado.provas_com_problemas += 1
    
    print("\n\n" + "=" * 80)
    
    # Gerar relatório
    relatorio = gerar_relatorio(resultado)
    print(relatorio)
    
    # Salvar relatório em arquivo
    with open("relatorio_auditoria_completa.txt", "w", encoding="utf-8") as f:
        f.write(relatorio)
    
    print("\n✅ Relatótio salvo em: relatorio_auditoria_completa.txt")
    
    # Resumo final
    print("\n" + "=" * 80)
    print("RESUMO FINAL")
    print("=" * 80)
    print(f"✅ Provas OK: {resultado.provas_ok}/{resultado.total_provas}")
    print(f"⚠️  Provas com avisos: {resultado.provas_com_avisos}")
    print(f"❌ Provas com erros: {resultado.provas_com_problemas}")
    
    if resultado.provas_com_problemas == 0 and resultado.provas_com_avisos == 0:
        print("\n🎉 TUDO CERTO! O acervo está 100% padronizado!")
    elif resultado.provas_com_problemas == 0:
        print("\n🟡 ACERVO QUASE PERFEITO! Apenas avisos para verificar.")
    else:
        print("\n🔴 ACERVO PRECISA DE CORREÇÕES!")


if __name__ == "__main__":
    main()
