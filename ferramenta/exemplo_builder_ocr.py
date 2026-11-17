#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Template de builder para provas que exigem OCR (PDF escaneado).

QUANDO USAR: quando o PDF da prova NÃO tem texto selecionável e a ferramenta
principal (`organizador_provas.py`) não detecta questões mesmo após OCR.

COMO FUNCIONA: você (ou a IA) transcreve o PDF via OCR, monta em memória a
capa (`pre`), as questões, os grupos e o gabarito, e chama `montar_prova()`
da ferramenta — que gera o resultado EXATAMENTE no padrão do repositório
(prova_organizada.md + relatorio_analise.md + ZIP).

Este arquivo é um TEMPLATE: substitua os trechos marcados com <<<...>>>.

Fluxo completo documentado em GARGALOS_E_SOLUCOES.md (Caso 1).
"""

import os
import re
import shutil
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import organizador_provas as op  # noqa: E402

# <<< CAMINHOS: ajuste para o seu caso >>>
TRANSCRIPT_PROVA = "/caminho/do/transcript_ocr_da_prova.md"
TRANSCRIPT_GABARITO = "/caminho/do/transcript_ocr_do_gabarito.md"
IMAGENS_EXTRAIDAS = "/caminho/da/pasta/de/imagens/do/ocr"  # pode ser None
PASTA_SAIDA = "/caminho/da/saida"
NOME_PROVA = "Camara_Cidade_2024_Cargo"

# <<< CAPA: transcreva a página 1 INTEGRALMENTE (instruções, grade de respostas etc.) >>>
PRE = [
    "> [!NOTE]",
    "> **Transcrição integral da capa e das instruções da prova.**",
    ">",
    "> (linha 1 da capa)",
    "> (linha 2 da capa)",
    # ...
]

# <<< GABARITO: transcreva a grade do cargo correto >>>
GABARITO = {
    # 1: "B", 2: "D", ...
}
ORIGEM_GABARITO = "gabarito oficial — <página/bloco do cargo no PDF de gabarito>"

# <<< GRUPOS: {primeira_questao: (inicio, fim, texto_base_integral)} >>>
# O texto-base informado aqui é repetido automaticamente dentro de CADA
# questão do intervalo. Deixe {} se a prova não tiver grupos.
GRUPOS = {}

# <<< MAPA DE IMAGENS: nome extraído pelo OCR -> número final >>>
# Descarte logos, marcas d'água, rascunhos e imagens vazias/de capa.
IMGMAP = {
    # "page-0003-image-0001": 1,   -> vira imagens/imagem_001.jpg
    # "page-0003-image-0002": 2,   -> vira imagens/imagem_002.jpg
}

# <<< OBSERVAÇÕES EXTRAS para a seção 4 (limitações, retificações etc.) >>>
OBS_EXTRAS = [
    # "A questão 11 tem resposta retificada para A no gabarito oficial definitivo.",
]


def paginas(transcript_path):
    """Divide o transcript OCR em páginas (marcador '--- Page N ---')."""
    texto = open(transcript_path, encoding="utf-8").read()
    partes = re.split(r"^--- Page \d+ ---$", texto, flags=re.M)
    return [p for p in partes if p.strip()]


def ref_imagem(marcador_ocr):
    """Converte o marcador '[Extracted image: page-XXXX-image-YYYY]' do transcript
    na referência final 'imagens/imagem_00N.ext', ou None se a imagem foi descartada."""
    m = re.search(r"page-(\d+)-image-(\d+)", marcador_ocr or "")
    if not m:
        return None
    chave = f"page-{m.group(1)}-image-{m.group(2)}"
    if chave not in IMGMAP:
        return None  # imagem descartada (logo, rascunho, capa)
    origem = os.path.join(IMAGENS_EXTRAIDAS, f"{chave}.jpg")
    if not os.path.exists(origem):
        origem = os.path.join(IMAGENS_EXTRAIDAS, f"{chave}.png")
    return origem, IMGMAP[chave]


def construir_questoes():
    """<<< ADAPTAR: percorra as páginas do transcript, separe cada questão e
    devolva a lista no formato abaixo. Dicas comuns:

    - Normalizar alternativas: 'A. texto' -> 'A) texto' (a ferramenta aceita os
      dois, mas o padrão de saída é 'A)').
    - Alternativas coladas na mesma linha do enunciado: dividir com
      re.split(r"\\s+(?=[B-E]\\)\\s)", linha).
    - Cabeçalhos/rodapés repetidos (nome do concurso, cargo, data, '- N -'):
      descartar de todas as páginas antes de detectar as questões.
    - Detectar as questões pela CADEIA ESPERADA (1, 2, 3, ...): aceitar um
      candidato só se o número for o próximo esperado — isso evita pegar
      números soltos de listas e rascunhos.
    """
    raise NotImplementedError


def finalizar(pre, questoes, grupos, gabarito, origem_gab, obs):
    pasta = os.path.join(PASTA_SAIDA, NOME_PROVA)
    os.makedirs(pasta, exist_ok=True)
    n_imgs = max(IMGMAP.values(), default=0)
    prova_md, rel_md = op.montar_prova(
        NOME_PROVA, pre, questoes, grupos, gabarito, origem_gab,
        total_imagens=n_imgs, observacoes_extras=obs, via_ocr=True,
    )
    open(os.path.join(pasta, "prova_organizada.md"), "w", encoding="utf-8").write(prova_md)
    open(os.path.join(pasta, "relatorio_analise.md"), "w", encoding="utf-8").write(rel_md)
    if IMAGENS_EXTRAIDAS:
        idir = os.path.join(pasta, "imagens")
        os.makedirs(idir, exist_ok=True)
        for chave, num in IMGMAP.items():
            for ext in (".jpg", ".png"):
                src = os.path.join(IMAGENS_EXTRAIDAS, chave + ext)
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(idir, f"imagem_{num:03d}{ext}"))
                    break
    zpath = os.path.join(pasta, "PROVA_ORGANIZADA.zip")
    if os.path.exists(zpath):
        os.remove(zpath)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in ("prova_organizada.md", "relatorio_analise.md"):
            z.write(os.path.join(pasta, f), f)
        idir = os.path.join(pasta, "imagens")
        if os.path.isdir(idir):
            for f in sorted(os.listdir(idir)):
                z.write(os.path.join(idir, f), f"imagens/{f}")
    print(f"OK: {pasta}")


if __name__ == "__main__":
    questoes = construir_questoes()
    finalizar(PRE, questoes, GRUPOS, GABARITO, ORIGEM_GABARITO, OBS_EXTRAS)
