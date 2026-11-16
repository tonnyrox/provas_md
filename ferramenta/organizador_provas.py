#!/usr/bin/env python3
"""
Organizador de Provas em PDF -> Markdown

Lê todos os PDFs de uma pasta, extrai texto e imagens, detecta as questões
e os textos-base agrupados ("O texto seguinte servirá de base para responder
às questões X a Y") e gera um .md organizado por prova, repetindo o texto-base
antes de cada questão vinculada a ele.

Uso:
    pip install pymupdf
    python organizador_provas.py --pasta ./pdfs --saida ./saida

Opcional (publicar no GitHub automaticamente):
    python organizador_provas.py --pasta ./pdfs --saida ./saida --repo /caminho/clone/provas_md
"""

import argparse
import hashlib
import re
import shutil
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF não encontrado. Instale com:  pip install pymupdf")


QUESTAO_RE = re.compile(
    r"(?im)^\s*quest[ãa]o\s*[-–—:]?\s*(\d{2,3})\s*\)?\s*$"
)

TEXTO_BASE_RE = re.compile(
    r"o\s+texto\s+seguinte(?:s)?\s+servir[áa]\s+de\s+base[^.]*?"
    r"quest[õo]es\s+(?:de\s+)?(\d{1,3})\s*(?:a|à|até|e)\s*(\d{1,3})",
    re.IGNORECASE,
)

TEXTO_BASE_UNICO_RE = re.compile(
    r"o\s+texto\s+seguinte(?:s)?\s+servir[áa]\s+de\s+base[^.]*?quest[ãa]o\s+(\d{1,3})",
    re.IGNORECASE,
)

LARGURA_MIN_IMG = 150
ALTURA_MIN_IMG = 100

IMG_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


def limpar_linha(linha: str) -> str:
    linha = linha.rstrip()
    return linha


def extrair_pdf(pdf_path: Path, pasta_imagens: Path) -> str:
    """Extrai um PDF para Markdown cru (texto + imagens intercaladas)."""
    doc = fitz.open(pdf_path)
    partes: list[str] = [f"# {pdf_path.stem}\n"]
    contador_imgs = 0
    hashes_vistos: set[str] = set()

    for num_pagina, pagina in enumerate(doc, start=1):
        partes.append(f"\n\n<!-- pagina {num_pagina} -->\n")
        dados = pagina.get_text("dict")
        for bloco in dados["blocks"]:
            if bloco["type"] == 0:
                texto = "\n".join(
                    "".join(span["text"] for span in linha["spans"]).strip()
                    for linha in bloco["lines"]
                ).strip()
                if texto:
                    partes.append(texto)
            elif bloco["type"] == 1:
                if (
                    bloco.get("width", 0) < LARGURA_MIN_IMG
                    or bloco.get("height", 0) < ALTURA_MIN_IMG
                ):
                    continue
                conteudo_img = bloco.get("image", b"")
                resumo = hashlib.md5(conteudo_img).hexdigest()
                if resumo in hashes_vistos:
                    continue
                hashes_vistos.add(resumo)
                contador_imgs += 1
                ext = bloco.get("ext", "png")
                nome = f"pag{num_pagina:03d}_img{contador_imgs:03d}.{ext}"
                destino = pasta_imagens / nome
                destino.write_bytes(bloco["image"])
                partes.append(f"\n\n![imagem da página {num_pagina}](imagens/{nome})\n")

    doc.close()
    return "\n".join(partes)


def organizar(markdown_cru: str) -> str:
    """Detecta questões e textos-base; repete o texto-base nas questões vinculadas."""
    linhas = markdown_cru.split("\n")

    secoes: list[dict] = []
    atual: dict | None = {"titulo": None, "linhas": []}
    secoes.append(atual)

    ultima_questao = 0
    for linha in linhas:
        m = QUESTAO_RE.match(linha)
        numero = int(m.group(1)) if m else None
        if numero and numero == ultima_questao + 1:
            atual = {"titulo": f"Questão {numero:02d}", "linhas": [linha]}
            secoes.append(atual)
            ultima_questao = numero
        else:
            atual["linhas"].append(linha)

    # localizar textos-base declarados e seu conteúdo (do aviso até a 1a questão vinculada)
    texto_base_por_questao: dict[int, str] = {}
    idx_questao = {
        i: int(re.match(r"Questão (\d+)", s["titulo"]).group(1))
        for i, s in enumerate(secoes)
        if s["titulo"]
    }

    for i, secao in enumerate(secoes):
        conteudo = re.sub(r"\s+", " ", "\n".join(secao["linhas"]))
        m = TEXTO_BASE_RE.search(conteudo) or TEXTO_BASE_UNICO_RE.search(conteudo)
        if not m:
            continue
        ini = int(m.group(1))
        fim = int(m.group(2)) if m.lastindex and m.lastindex >= 2 else ini
        # o texto-base é tudo entre o aviso e a próxima seção de questão
        proxima = None
        for j in range(i + 1, len(secoes)):
            if j in idx_questao:
                proxima = j
                break
        corpo = "\n".join(
            secoes[k]["linhas"] for k in range(i + 1, proxima or len(secoes))
        ).strip()
        aviso = m.group(0)
        for q in range(ini, fim + 1):
            texto_base_por_questao[q] = (
                f"> 🔗 **Questão agrupada — texto-base das questões {ini} a {fim}.**\n"
                f"> {aviso}\n\n{corpo}\n\n---\n"
            )

    saida: list[str] = ["# Prova organizada\n"]
    for secao in secoes:
        if not secao["titulo"]:
            cabecalho = "\n".join(secao["linhas"]).strip()
            if cabecalho:
                saida.append(cabecalho + "\n")
            continue

        numero = int(re.match(r"Questão (\d+)", secao["titulo"]).group(1))
        corpo = "\n".join(secao["linhas"]).strip()
        saida.append(f"\n---\n\n## {secao['titulo']}\n")
        if numero in texto_base_por_questao:
            saida.append(texto_base_por_questao[numero])
        saida.append(corpo + "\n")

    return "\n".join(saida)


def processar(pasta_pdfs: Path, pasta_saida: Path, repo: Path | None) -> None:
    pdfs = sorted(pasta_pdfs.glob("*.pdf")) + sorted(pasta_pdfs.glob("*.PDF"))
    if not pdfs:
        sys.exit(f"Nenhum PDF encontrado em {pasta_pdfs}")

    for pdf in pdfs:
        slug = re.sub(r"[^\w\-]+", "_", pdf.stem).strip("_")
        pasta_prova = pasta_saida / slug
        pasta_imagens = pasta_prova / "imagens"
        pasta_imagens.mkdir(parents=True, exist_ok=True)

        print(f"[{slug}] extraindo...")
        cru = extrair_pdf(pdf, pasta_imagens)
        organizado = organizar(cru)
        (pasta_prova / f"{slug}.md").write_text(organizado, encoding="utf-8")
        n_imgs = len([a for a in pasta_imagens.iterdir() if a.suffix.lower() in IMG_EXTS])
        print(f"[{slug}] ok -> {pasta_prova / (slug + '.md')} ({n_imgs} imagens)")

    if repo:
        destino = repo / "Provas MD"
        destino.mkdir(exist_ok=True)
        for pasta_prova in pasta_saida.iterdir():
            if pasta_prova.is_dir():
                alvo = destino / pasta_prova.name
                if alvo.exists():
                    shutil.rmtree(alvo)
                shutil.copytree(pasta_prova, alvo)
        print(f"\nConteúdo copiado para {destino}. Para publicar:")
        print(f"  cd {repo} && git add -A && git commit -m 'Nova prova organizada' && git push")


def main() -> None:
    parser = argparse.ArgumentParser(description="Organiza provas em PDF para Markdown")
    parser.add_argument("--pasta", required=True, help="Pasta com os PDFs")
    parser.add_argument("--saida", default="saida", help="Pasta de saída dos .md")
    parser.add_argument("--repo", help="Caminho do clone de provas_md para copiar o resultado")
    args = parser.parse_args()

    pasta_pdfs = Path(args.pasta).expanduser().resolve()
    pasta_saida = Path(args.saida).expanduser().resolve()
    repo = Path(args.repo).expanduser().resolve() if args.repo else None
    processar(pasta_pdfs, pasta_saida, repo)


if __name__ == "__main__":
    main()
