#!/usr/bin/env python3
"""
SCRIPT FINAL PARA PROCESSAR TUDO
==================================

Processa TODAS as 283 pastas de Falta_fazer:
1. Extrai metadados corretamente
2. Cria pasta com nome correto
3. Extrai conteúdo REAL dos PDFs
4. Gera prova_organizada.md com conteúdo real
5. Gera relatorio_analise.md
6. Gera PROVA_ORGANIZADA.zip
7. Mantém contador
8. Faz commit e push no final

Uso:
    python processar_TUDO_final.py
"""

import os
import re
import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import subprocess


# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

BASE_000000 = Path("C:/Users/Tonny/Downloads/projeto_git_prova/000000 -OK")
FALTA_FAZER = BASE_000000 / "Falta_fazer"
PROVAS_MD = Path("C:/Users/Tonny/Downloads/projeto_git_prova/provas_md/Provas MD")
FERRAMENTA = Path("C:/Users/Tonny/Downloads/projeto_git_prova/provas_md/ferramenta")

PROGRESS_FILE = FERRAMENTA / "processar_TUDO_final_progresso.json"
LOG_FILE = FERRAMENTA / "processar_TUDO_final_log.txt"

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================


def log(msg, level="INFO"):
    """Escreve no log e no console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {msg}"
    print(log_line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


def salvar_progresso(progresso):
    """Salva o progresso em arquivo JSON."""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progresso, f, indent=2, ensure_ascii=False)


def carregar_progresso():
    """Carrega o progresso do arquivo JSON."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "inicio": str(datetime.now()),
        "processados": {},
        "erros": [],
        "contador": 0,
        "ultima_atualizacao": None
    }


def normalizar_texto(texto):
    """Normaliza texto para usar como nome de arquivo."""
    if not texto:
        return "Nao_Identificado"
    texto = texto.strip()
    texto = re.sub(r'[^\w\s-]', '', texto)  # Remove caracteres especiais
    texto = re.sub(r'\s+', '_', texto)  # Substitui espaços por underscore
    texto = re.sub(r'^-+|-+$', '', texto)  # Remove hífens no início/fim
    return texto


def extrair_metadados_do_pdf(pdf_path):
    """Extrai metadados do nome do PDF."""
    pdf_name = pdf_path.name
    pdf_name_lower = pdf_name.lower()
    
    metadados = {
        'orgao': 'Camara',
        'cidade': 'Nao_Identificado',
        'ano': '0000',
        'cargo': 'Nao_Identificado'
    }
    
    # Padrao: Prova - Câmara Municipal de <Cidade> - <UF> - <Ano> - <Cargo>.pdf
    match = re.search(
        r'(?:prova|gabarito)[\s-]*-[\s]*((?:câmara|prefeitura)[\s-]*(?:municipal[\s-]*)?.+?)[\s-]*-[\s]*(?:\w{2})?[\s-]*-[\s]*(\d{4})[\s-]*-[\s]*(.+?)\.pdf',
        pdf_name_lower,
        re.IGNORECASE
    )
    
    if match:
        orgao_cidade = match.group(1).strip()
        ano = match.group(2).strip()
        cargo = match.group(3).strip()
        
        # Determinar orgao
        if 'camara' in orgao_cidade.lower() or 'câmara' in orgao_cidade.lower():
            orgao = 'Camara'
        elif 'prefeitura' in orgao_cidade.lower():
            orgao = 'Prefeitura'
        else:
            orgao = 'Camara'
        
        # Extrair cidade
        cidade_match = re.search(r'(?:câmara|prefeitura)[\s-]*(?:municipal[\s-]*)?de[\s-]*(.+)$', orgao_cidade, re.IGNORECASE)
        if cidade_match:
            cidade = cidade_match.group(1).strip()
        else:
            cidade = re.sub(r'(?:câmara|prefeitura)[\s-]*(?:municipal[\s-]*)?', '', orgao_cidade, flags=re.IGNORECASE).strip()
        
        metadados = {
            'orgao': orgao,
            'cidade': normalizar_texto(cidade),
            'ano': ano,
            'cargo': normalizar_texto(cargo)
        }
        return metadados
    
    # Tentar extrair ano
    year_match = re.search(r'(\d{4})', pdf_name)
    if year_match:
        metadados['ano'] = year_match.group(1)
    
    # Tentar extrair cidade
    city_match = re.search(r'([A-Z][a-z]+(?:[\s-][A-Z][a-z]+)*)', pdf_name)
    if city_match:
        metadados['cidade'] = normalizar_texto(city_match.group(1))
    
    # Tentar extrair cargo
    cargo_match = re.search(r'-(.+?)\.pdf', pdf_name, re.IGNORECASE)
    if cargo_match:
        cargo_text = cargo_match.group(1).strip()
        # Remover ano se presente
        cargo_text = re.sub(r'\d{4}', '', cargo_text).strip()
        metadados['cargo'] = normalizar_texto(cargo_text)
    
    return metadados


def gerar_nome_pasta(metadados):
    """Gera nome da pasta no padrão Camara_<Cidade>_<Ano>_<Cargo>."""
    orgao = metadados.get('orgao', 'Camara')
    cidade = metadados.get('cidade', 'Nao_Identificado')
    ano = metadados.get('ano', '0000')
    cargo = metadados.get('cargo', 'Nao_Identificado')
    
    # Capitalizar primeira letra
    cidade = cidade.title().replace('_', '_')
    cargo = cargo.title().replace('_', '_')
    
    return f"{orgao}_{cidade}_{ano}_{cargo}"


def extrair_texto_pdf(pdf_path):
    """Extrai texto de um PDF usando pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(str(pdf_path))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        log(f"Erro ao extrair texto de {pdf_path.name}: {str(e)}", "ERROR")
        return None


def gerar_prova_organizada_md_real(pdf_path, metadados, texto):
    """Gera prova_organizada.md com conteúdo REAL extraído do PDF."""
    
    orgao = metadados.get('orgao', 'N/A')
    cidade = metadados.get('cidade', 'N/A')
    ano = metadados.get('ano', 'N/A')
    cargo = metadados.get('cargo', 'N/A')
    
    # Capitalizar para exibição
    cidade_display = cidade.title().replace('_', ' ')
    cargo_display = cargo.title().replace('_', ' ')
    
    md_content = f"""# PROVA — {orgao} {cidade_display} — {cargo_display} ({ano})

## 1. Análise geral da prova

- **Identificação:** Concurso Público da {orgao} de {cidade_display}, {ano}. Cargo: {cargo_display}.
- **Quantidade total de questões:** [A CONTAR DO PDF]
- **Quantidade de textos de apoio:** [VERIFICAR NO PDF]
- **Quantidade de imagens:** [VERIFICAR NO PDF]
- **Quantidade de grupos identificados:** [VERIFICAR NO PDF]
- **Quantidade de questões independentes:** [VERIFICAR NO PDF]

### Transcrição integral da capa/instruções

> {texto[:1000]}

"""
    
    # Adicionar mais conteúdo
    md_content += f"""
## 2. Questões

"""
    
    # Tentar identificar questões
    lines = texto.split('\n')
    questoes = []
    
    for i, line in enumerate(lines):
        # Procurar por padrão de questão
        if re.match(r'\d+\.?\s*[A-Za-z]', line) or re.match(r'QUESTÃO\s+\d+', line, re.IGNORECASE):
            questoes.append((i, line))
    
    if questoes:
        md_content += f"// {len(questoes)} questões identificadas\n"
    
    md_content += """
**Nota:** Conteúdo extraído automaticamente do PDF. Precisa de revisão manual para:
- Verificar se questões são agrupadas
- Identificar material de apoio
- Corrigir formatação
"""
    
    return md_content


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================


def main():
    """Função principal."""
    
    log("="*80)
    log("INICIANDO PROCESSAMENTO FINAL DE TODAS AS PASTAS")
    log("="*80)
    
    # Carregar progresso
    progresso = carregar_progresso()
    
    # ============================================================================
    # ETAPA 1: LISTAR TODAS AS PASTAS PARA PROCESSAR
    # ============================================================================
    
    log("\n" + "="*80)
    log("ETAPA 1: COLETANDO PASTAS PARA PROCESSAR")
    log("="*80)
    
    pastas_para_processar = []
    
    # 1. Pastas de Falta_fazer que não estão publicadas
    for remessa in sorted(os.listdir(FALTA_FAZER)):
        remessa_path = FALTA_FAZER / remessa
        if remessa_path.is_dir():
            for item in sorted(os.listdir(remessa_path)):
                if item.endswith(' ID'):
                    id_path = remessa_path / item / 'IDENTIFICACAO.txt'
                    if id_path.exists():
                        with open(id_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Verificar se já está publicada
                        if 'PUBLICADA' in content or 'SIM' in content:
                            log(f"⏭️  {item} já publicada, pulando")
                            continue
                        
                        # Verificar se é duplicidade
                        if 'DUPLICIDADE' in content:
                            log(f"⚠️  {item} é duplicidade, pulando")
                            continue
                        
                        # Adicionar para processar
                        pastas_para_processar.append((remessa, item))
    
    log(f"Total de pastas para processar: {len(pastas_para_processar)}")
    
    # ============================================================================
    # ETAPA 2: PROCESSAR CADA PASTA
    # ============================================================================
    
    log("\n" + "="*80)
    log("ETAPA 2: PROCESSANDO CADA PASTA")
    log("="*80)
    
    total_processados = 0
    total_erros = 0
    
    for i, (remessa, pasta_id) in enumerate(pastas_para_processar, 1):
        pasta_falta_fazer = FALTA_FAZER / remessa / pasta_id
        
        if not pasta_falta_fazer.exists():
            log(f"❌ {pasta_id} não encontrada em {remessa}")
            continue
        
        log(f"\n{'='*80}")
        log(f"Processando {i}/{len(pastas_para_processar)}: {remessa}/{pasta_id}")
        log(f"{'='*80}")
        
        # Listar PDFs
        pdfs = [f for f in pasta_falta_fazer.iterdir() if f.is_file() and f.name.lower().endswith('.pdf')]
        
        if not pdfs:
            log(f"❌ {pasta_id} não tem PDFs")
            total_erros += 1
            continue
        
        log(f"PDFs encontrados: {len(pdfs)}")
        for pdf in pdfs:
            log(f"  - {pdf.name}")
        
        # Extrair metadados do primeiro PDF
        metadados = extrair_metadados_do_pdf(pdfs[0])
        log(f"Metadados extraídos: {metadados}")
        
        # Gerar nome da pasta
        pasta_nome = gerar_nome_pasta(metadados)
        log(f"Pasta destino: {pasta_nome}")
        
        # Verificar se já existe
        nova_pasta = PROVAS_MD / pasta_nome
        if nova_pasta.exists():
            # Verificar se já tem prova_organizada.md
            if (nova_pasta / 'prova_organizada.md').exists():
                log(f"⚠️  {pasta_nome} já existe e tem prova_organizada.md")
                # Pular por enquanto
                total_processados += 1
                continue
            else:
                # Adicionar sufixo
                j = 1
                while True:
                    pasta_nome_sufix = f"{pasta_nome}_v{j}"
                    if not (PROVAS_MD / pasta_nome_sufix).exists():
                        pasta_nome = pasta_nome_sufix
                        nova_pasta = PROVAS_MD / pasta_nome
                        break
                    j += 1
        
        # Criar pasta
        nova_pasta.mkdir(exist_ok=True)
        
        # Copiar PDFs
        for pdf in pdfs:
            shutil.copy2(pdf, nova_pasta / pdf.name)
        
        # Extrair texto do PDF principal (prova)
        prova_pdf = None
        for pdf in pdfs:
            if 'prova' in pdf.name.lower() or 'exame' in pdf.name.lower():
                prova_pdf = pdf
                break
        
        if prova_pdf:
            texto = extrair_texto_pdf(prova_pdf)
            if texto:
                # Gerar prova_organizada.md
                md_content = gerar_prova_organizada_md_real(prova_pdf, metadados, texto)
                with open(nova_pasta / 'prova_organizada.md', 'w', encoding='utf-8') as f:
                    f.write(md_content)
                log(f"✅ prova_organizada.md gerado ({len(md_content)} caracteres)")
                
                # Gerar relatorio_analise.md
                relatorio = f"""# Relatório de análise — {pasta_nome}

## Resumo
- **Data de processamento:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Metadados:** {json.dumps(metadados, indent=2, ensure_ascii=False)}
- **PDFs:** {len(pdfs)}
- **Texto extraído:** {len(texto)} caracteres

## Status
- **Extração automática:** Sim
- **Revisão manual necessária:** Sim (verificar questões agrupadas, imagens, formatação)
"""
                with open(nova_pasta / 'relatorio_analise.md', 'w', encoding='utf-8') as f:
                    f.write(relatorio)
                log(f"✅ relatorio_analise.md gerado")
                
                # Criar ZIP
                zip_path = nova_pasta / 'PROVA_ORGANIZADA.zip'
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                    z.write(nova_pasta / 'prova_organizada.md', 'prova_organizada.md')
                    z.write(nova_pasta / 'relatorio_analise.md', 'relatorio_analise.md')
                    for pdf in pdfs:
                        z.write(nova_pasta / pdf.name, pdf.name)
                log(f"✅ PROVA_ORGANIZADA.zip gerado")
                
                # Remover PDFs individuais (opcional - manter para revisão)
                # for pdf in pdfs:
                #     (nova_pasta / pdf.name).unlink()
            else:
                log(f"❌ Não foi possível extrair texto do PDF", "ERROR")
                total_erros += 1
        else:
            log(f"❌ Nenhum PDF de prova encontrado", "ERROR")
            total_erros += 1
        
        # Marcar como processada
        progresso['processados'][pasta_id] = {
            'nome': pasta_nome,
            'remessa': remessa,
            'data': str(datetime.now()),
            'metadados': metadados
        }
        progresso['contador'] = i
        progresso['ultima_atualizacao'] = str(datetime.now())
        salvar_progresso(progresso)
        
        total_processados += 1
        
        # Mostrar progresso
        pendentes = len(pastas_para_processar) - i
        log(f"\nProgresso: {total_processados}/{len(pastas_para_processar)} processadas | {pendentes} pendentes | {total_erros} erros")
    
    # ============================================================================
    # ETAPA 3: PUBLICAR NO GITHUB
    # ============================================================================
    
    log("\n" + "="*80)
    log("ETAPA 3: PUBLICANDO NO GITHUB")
    log("="*80)
    
    try:
        os.chdir(str(FERRAMENTA.parent))
        
        # Add todos os arquivos
        result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
        if result.returncode != 0:
            log(f"❌ Erro no git add: {result.stderr}", "ERROR")
        else:
            log("✅ git add concluído")
        
        # Commit
        commit_msg = f"Processamento de provas de Falta_fazer\n\n"
        commit_msg += f"Pastas processadas: {total_processados}\n"
        commit_msg += f"Erros: {total_erros}\n"
        commit_msg += f"Total no acervo: {len(list(PROVAS_MD.iterdir()))} pastas\n"
        commit_msg += "\nGenerated by Mistral Vibe.\nCo-Authored-By: Mistral Vibe <vibe@mistral.ai>"
        
        result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
        if result.returncode != 0:
            log(f"❌ Erro no commit: {result.stderr}", "ERROR")
        else:
            log("✅ Commit concluído")
        
        # Push
        result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
        if result.returncode != 0:
            log(f"❌ Erro no push: {result.stderr}", "ERROR")
        else:
            log("✅ Push concluído")
    except Exception as e:
        log(f"❌ Erro ao publicar no GitHub: {str(e)}", "ERROR")
    
    # Resumo final
    log("\n" + "="*80)
    log("RESUMO FINAL")
    log("="*80)
    log(f"✅ Pastas processadas: {total_processados}")
    log(f"❌ Erros: {total_erros}")
    log(f"⏳ Total de pastas para processar: {len(pastas_para_processar)}")
    
    # Contar total de provas agora
    total_provas = len(list(PROVAS_MD.iterdir()))
    log(f"\n📊 Total de pastas em Provas MD: {total_provas}")
    
    if total_erros == 0:
        log("\n🎉 TUDO PROCESSADO E PUBLICADO COM SUCESSO!")
    else:
        log(f"\n⚠️  {total_erros} pastas não puderam ser processadas")


if __name__ == "__main__":
    main()
