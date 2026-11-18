#!/usr/bin/env python3
"""
Organizador de Provas em PDF -> Markdown (padrão do repositório provas_md)

Lê todos os PDFs de uma pasta (pareando automaticamente "Prova" + "Gabarito"
pelo nome do arquivo), extrai texto e imagens, detecta as questões e os
textos-base agrupados e gera, para cada prova, uma pasta EXATAMENTE no padrão
do repositório:

    Camara_<Cidade>_<Ano>_<Cargo>/
    ├── prova_organizada.md
    ├── relatorio_analise.md
    ├── PROVA_ORGANIZADA.zip
    └── imagens/
        ├── imagem_001.jpg
        └── ...

Regras do padrão aplicadas pela ferramenta:
  - Nada é resumido ou omitido: todo o texto extraído do PDF vai para o .md.
  - Cada questão é autossuficiente: o texto-base compartilhado é repetido
    integralmente dentro de cada questão do grupo.
  - Imagens nomeadas imagem_001, imagem_002... referenciadas relativamente
    (mesmo arquivo físico, referências repetidas em cada questão).
  - Estrutura fixa: 1. Análise geral / 2. Questões agrupadas /
    3. Questões independentes / 4. Observações e limitações da extração.

Uso:
    pip install pymupdf
    python organizador_provas.py --pasta ./pdfs --saida ./saida

Opcional:
    --nome "Camara_Brusque_2024_Agente_Administrativo"   (força o nome da pasta)
    --repo /caminho/clone/provas_md                      (copia p/ "Provas MD")
"""

import argparse
import hashlib
import re
import shutil
import sys
import unicodedata
import zipfile
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF não encontrado. Instale com:  pip install pymupdf")

QUESTAO_HEAD_RE = re.compile(
    r"^\s*(?:\*\*)?\s*quest[\u00e3a]o\s*[-\u2013\u2014:.]?\s*(\d{1,3})\s*\)?\s*(?:\*\*)?\s*$",
    re.IGNORECASE,
)
QUESTAO_HEAD_INLINE_RE = re.compile(
    r"^\s*(?:\*\*)?\s*quest[\u00e3a]o\s*[-\u2013\u2014:.]?\s*(\d{1,3})\s*\)?\s*[-\u2013\u2014:.]?\s*(?:\*\*)?\s*(\S.*)$",
    re.IGNORECASE,
)
QUESTAO_HEAD_ORDINAL_RE = re.compile(
    r"^\s*(?:\*\*)?\s*(\d{1,3})\s*[\u00aa\u00ba\u00b0o]\s+quest[\u00e3a]o\s*(?:\*\*)?\s*$",
    re.IGNORECASE,
)
QUESTAO_NUM_SOZINHO_RE = re.compile(
    r"^\s*(?:\*\*)?\s*(\d{1,3})\s*[\.\)-]\s*(?:\*\*)?\s*$"
)
QUESTAO_NUM_RE = re.compile(r"^\s*(?:\*\*)?\s*(\d{1,3})\s*[\.\)-]\s*\**\s*(.+)")
ALT_RE = re.compile(r"^\s*\(?\s*([A-Ea-e])\s*[).:]\s*(.*)$")

TEXTO_BASE_RES = [
    re.compile(
        r"o\s+texto\s+seguinte(?:s)?\s+servir[\u00e1a]\s+de\s+base[^.]*?quest[\u00f5o]es\s+(?:de\s+)?n[u00fa]?[\u00bao\u00b0]?\s*(?:meros?\s*)?(\d{1,3})\s*(?:a|\u00e0|at\u00e9|e)\s*(\d{1,3})",
        re.IGNORECASE,
    ),
    re.compile(
        r"texto\s+(?:para|para\s+as)\s+quest[\u00f5o]es\s+(?:de\s+)?n[u00fa]?[\u00bao\u00b0]?\s*(?:meros?\s*)?(\d{1,3})\s*(?:a|\u00e0|at\u00e9|e)\s*(\d{1,3})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:utilize|leia|considere)\s+o\s+texto\s+(?:abaixo|a\s+seguir)[^.]*?quest[\u00f5o]es\s+(?:de\s+)?n[u00fa]?[\u00bao\u00b0]?\s*(?:meros?\s*)?(\d{1,3})\s*(?:a|\u00e0|at\u00e9|e)\s*(\d{1,3})",
        re.IGNORECASE,
    ),
    re.compile(
        r"quest[\u00f5o]es\s+(?:de\s+)?n[u00fa]?[\u00bao\u00b0]?\s*(?:meros?\s*)?(\d{1,3})\s*(?:a|\u00e0|at\u00e9)\s*(\d{1,3})\s+referem-se",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:responder|respondem?|destinadas?)[^.]{0,40}?quest[\u00f5o]es\s+(?:de\s+)?n[u00fa]?[\u00bao\u00b0]?\s*(?:meros?\s*)?(\d{1,3})\s*(?:a|\u00e0|at\u00e9|e)\s*(\d{1,3})",
        re.IGNORECASE,
    ),
    re.compile(
        r"o\s+texto\s+seguinte(?:s)?\s+servir[\u00e1a]\s+de\s+base[^.]*?quest[\u00e3a]o\s+(\d{1,3})",
        re.IGNORECASE,
    ),
    re.compile(
        r"quest[\u00f5o]es\s+(?:de\s+)?(\d{1,3})\s*(?:a|\u00e0|at\u00e9|e)\s*(\d{1,3})",
        re.IGNORECASE,
    ),
]

GABARITO_PAR_RE = re.compile(r"(?<![\d.])(\d{1,3})\s*[-\u2013\u2014:.|\s]+\(?([A-Ea-e])\)?(?=[\s,;)\]]|$)")
ANULADA_RE = re.compile(r"(?<![\d.])(\d{1,3})\s*[-\u2013\u2014:.|\s]+ANULAD[AO]", re.IGNORECASE)
ANULADA_HASH_RE = re.compile(r"(?<![\d.])(\d{1,3})\s*[-\u2013\u2014:.|\s]+#+(?=[\s,;)\]]|$)")
ANULADA_X_RE = re.compile(r"(?<![\d.])(\d{1,3})\s*[-\u2013\u2014:.|\s]+X(?=[\s,;)\]]|$)")
VF_RE = re.compile(r"(?<![\d.])(\d{1,3})\s*[-\u2013\u2014:.|\s]+([VFvf])(?=[\s,;)\]]|$)")
NUM_SOZINHO_RE = re.compile(r"^[\s.|]*((?:\d{1,3}[\s.|]+)*\d{1,3})[\s.|]*$")
LETRA_SOZINHA_RE = re.compile(r"^[\s.|A-Ea-e]+$")
CARGO_LINHA_RE = re.compile(
    r"^\s*(?:CARGO\s*[\u2013\u2014\-]?\s*)?([A-Z\u00c0-\u00dc][A-Z\u00c0-\u00dc \t]{3,60})\s*$",
    re.MULTILINE,
)
CARGO_LINHA_COMPLETA_RE = re.compile(
    r"^\s*(?:N[\u00edi]VEL\s+\w+\s*[-\u2013\u2014]?\s*)?.?\s*CARGO\s*[:\u2013\u2014\-]\s*([^\n]{3,80})$",
    re.MULTILINE | re.IGNORECASE,
)
CARGO_PROVA_RE = re.compile(
    r"cargo\s*[:\s]\s*([\d]+(?:[\.,]\d+)?)\s*[-\u2013\u2014]?\s*([^\n]{0,80})",
    re.IGNORECASE,
)
CABECALHO_BLOCO_RE = re.compile(r"^(\d+(?:[\.,]\d+)?)\s*[-\u2013\u2014]\s*(.+)$", re.MULTILINE)

IMG_RE = re.compile(r"!\[[^\]]*\]\((imagens/[^)]+)\)")
LARGURA_MIN_IMG = 150
ALTURA_MIN_IMG = 80
IMG_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


def extrair_pdf(pdf_path: Path, pasta_imagens: Path, colunas: int = 1) -> str:
    """Extrai um PDF para Markdown cru (texto + imagens intercaladas).

    colunas=2 reordena os blocos de texto de páginas em duas colunas
    (esquerda inteira antes da direita), corrigindo provas com layout
    jornal onde a leitura natural embaralha as questões.
    """
    doc = fitz.open(pdf_path)
    partes: list[str] = []
    contador_imgs = 0
    hashes_vistos: set[str] = set()

    area_por_hash: dict[str, int] = {}
    total_paginas = max(1, len(doc))
    pre_scan: list[tuple[str, float]] = []
    for pagina in doc:
        area_pagina = abs(pagina.rect)
        for bloco in pagina.get_text("dict")["blocks"]:
            if bloco["type"] == 1 and bloco.get("image"):
                resumo = hashlib.md5(bloco["image"]).hexdigest()
                pre_scan.append((resumo, (bloco.get("width", 0) * bloco.get("height", 0)) / max(1.0, area_pagina)))
    for resumo, _ in pre_scan:
        area_por_hash[resumo] = area_por_hash.get(resumo, 0) + 1
    
    def imagem_descartavel(resumo: str, largura: int, altura: int, area_pagina: float) -> bool:
        area_frac = (largura * altura) / max(1.0, area_pagina)
        if area_frac > 0.85:
            return True
        ocorrencias = area_por_hash.get(resumo, 0)
        if ocorrencias >= max(3, total_paginas * 0.6) and altura < 150:
            return True
        return False

    for num_pagina, pagina in enumerate(doc, start=1):
        partes.append(f"\n\n<!-- pagina {num_pagina} -->\n")
        area_pagina = abs(pagina.rect)
        dados = pagina.get_text("dict")
        blocos = list(dados["blocks"])
        if colunas == 2:
            meio = pagina.rect.width / 2
            texto_esq = [b for b in blocos if b["type"] == 0 and b["bbox"][0] < meio]
            texto_dir = [b for b in blocos if b["type"] == 0 and b["bbox"][0] >= meio]
            visuais = [b for b in blocos if b["type"] == 1]
            blocos = texto_esq + texto_dir + visuais
        for bloco in blocos:
            if bloco["type"] == 0:
                texto = "\n".join(
                    "".join(span["text"] for span in linha["spans"]).strip()
                    for linha in bloco["lines"]
                ).strip()
                if texto:
                    partes.append(texto)
            elif bloco["type"] == 1:
                conteudo_img = bloco.get("image", b"")
                if not conteudo_img:
                    continue
                if (
                    bloco.get("width", 0) < LARGURA_MIN_IMG
                    or bloco.get("height", 0) < ALTURA_MIN_IMG
                ):
                    continue
                resumo = hashlib.md5(conteudo_img).hexdigest()
                if resumo in hashes_vistos:
                    continue
                if imagem_descartavel(resumo, bloco.get("width", 0), bloco.get("height", 0), area_pagina):
                    continue
                hashes_vistos.add(resumo)
                contador_imgs += 1
                ext = bloco.get("ext", "png")
                if ext == "jpeg":
                    ext = "jpg"
                nome = f"imagem_{contador_imgs:03d}.{ext}"
                destino = pasta_imagens / nome
                destino.write_bytes(bloco["image"])
                partes.append(f"\n\n![Imagem da questão](imagens/{nome})\n")

    doc.close()
    return "\n".join(partes)


def detectar_questoes(cru: str) -> tuple[list[dict], list[str]]:
    """Separa o Markdown cru em questões.

    Levanta todos os candidatos a início de questão (cabeçalho "QUESTÃO NN"
    ou número seguido de "."/"))"/"-" ou número + separador sozinho na linha
    (enunciado embaixo), e escolhe a cadeia sequencial 1, 2, 3...
    que contém mais questões com alternativas (desempate: cadeia mais longa).
    Assim, itens numerados da capa/instruções não são confundidos com questões.

    Retorna (questões, conteúdo prévio = capa/instruções).
    """
    linhas = cru.split("\n")
    candidatos: list[tuple[int, int]] = []
    for i, linha in enumerate(linhas):
        m = QUESTAO_HEAD_RE.match(linha)
        if not m:
            m_ord = QUESTAO_HEAD_ORDINAL_RE.match(linha)
            if m_ord:
                m = m_ord
            elif QUESTAO_HEAD_INLINE_RE.match(linha):
                m = QUESTAO_HEAD_INLINE_RE.match(linha)
            elif QUESTAO_NUM_SOZINHO_RE.match(linha):
                m = QUESTAO_NUM_SOZINHO_RE.match(linha)
        if not m:
            m2 = QUESTAO_NUM_RE.match(linha)
            m = m2 if m2 else None
        if m:
            candidatos.append((i, int(m.group(1))))

    filtrados: list[tuple[int, int]] = []
    for idx, (i, num) in enumerate(candidatos):
        if (
            QUESTAO_HEAD_RE.match(linhas[i])
            or QUESTAO_HEAD_ORDINAL_RE.match(linhas[i])
            or QUESTAO_HEAD_INLINE_RE.match(linhas[i])
        ):
            filtrados.append((i, num))
            continue
        fim_cand = candidatos[idx + 1][0] if idx + 1 < len(candidatos) else len(linhas)
        if any(ALT_RE.match(l) for l in linhas[i:fim_cand]):
            filtrados.append((i, num))

    def melhor_cadeia(
        lista: list[tuple[int, int]],
    ) -> tuple[list[int], tuple[int, int] | None]:
        def cadeia_a_partir(j: int) -> list[int]:
            seq = [j]
            ultima = lista[j][1]
            for k in range(j + 1, len(lista)):
                num = lista[k][1]
                if num == ultima + 1 and num <= 400:
                    seq.append(k)
                    ultima = num
            return seq

        def pontuar(seq: list[int]) -> tuple[int, int]:
            com_alt = 0
            for pos, k in enumerate(seq):
                inicio = lista[k][0]
                fim = lista[seq[pos + 1]][0] if pos + 1 < len(seq) else len(linhas)
                if any(ALT_RE.match(l) for l in linhas[inicio:fim]):
                    com_alt += 1
            return (com_alt, len(seq))

        melhor_seq: list[int] = []
        melhor_score: tuple[int, int] | None = None
        for j in range(len(lista)):
            seq = cadeia_a_partir(j)
            score = pontuar(seq)
            if melhor_score is None or score > melhor_score:
                melhor_score = score
                melhor_seq = seq
        return melhor_seq, melhor_score

    seq_a, score_a = melhor_cadeia(candidatos)
    seq_b, score_b = melhor_cadeia(filtrados)
    if score_b is not None and (score_a is None or score_b > score_a):
        candidatos = filtrados
        melhor_seq = seq_b
    else:
        melhor_seq = seq_a

    if not melhor_seq:
        return [], list(linhas)

    questoes: list[dict] = []
    for pos, k in enumerate(melhor_seq):
        inicio = candidatos[k][0]
        fim = (
            candidatos[melhor_seq[pos + 1]][0]
            if pos + 1 < len(melhor_seq)
            else len(linhas)
        )
        questoes.append({"numero": candidatos[k][1], "linhas": linhas[inicio:fim]})
    return questoes, list(linhas[: candidatos[melhor_seq[0]][0]])


MARCA_DAGUA_RES = [
    re.compile(r"^pcimarkpci\b", re.IGNORECASE),
    re.compile(r"^www\.pciconcursos\.com\.br$", re.IGNORECASE),
]
SECAO_FAIXA_RE = re.compile(
    r"^[A-Z\u00c0-\u00dc][A-Z\u00c0-\u00dc ]{2,50}\s+(?:DE\s+)?\d{1,3}\s+(?:A|a|\u00e0)\s+\d{1,3}$"
)

SECOES_REMOVIDAS: list[str] = []


def limpar_corpo(linhas: list[str], e_pre: bool = False) -> list[str]:
    mescladas: list[str] = []
    for s in linhas:
        if mescladas and (s.startswith("\xa0") or s.startswith(" \xa0")):
            mescladas[-1] += " " + s.strip()
        else:
            mescladas.append(s)
    linhas = mescladas
    limpas = []
    for s in linhas:
        t = s.strip()
        if not t:
            limpas.append("")
            continue
        if t.startswith("<!-- pagina"):
            continue
        if t == "---":
            continue
        if re.fullmatch(r"\d{1,3}", t):
            continue
        if any(r.match(t) for r in MARCA_DAGUA_RES):
            continue
        if not e_pre and SECAO_FAIXA_RE.match(t):
            if t not in SECOES_REMOVIDAS:
                SECOES_REMOVIDAS.append(t)
            continue
        limpas.append(re.sub(r"[ \t\xa0\r]+", " ", s.rstrip()))
    while limpas and not limpas[0].strip():
        limpas.pop(0)
    while limpas and not limpas[-1].strip():
        limpas.pop()
    return limpas


def separar_alternativas(corpo: list[str]) -> tuple[list[str], list[tuple[str, str]]]:
    """Divide o corpo da questão em (enunciado, alternativas A-E)."""
    alts: list[tuple[str, str]] = []
    idx_primeira = None
    letra_esperada = 0
    for i, s in enumerate(corpo):
        t = s.strip()
        m = ALT_RE.match(t)
        if m and ord(m.group(1).upper()) - ord("A") == letra_esperada:
            if letra_esperada == 0:
                idx_primeira = i
            alts.append((m.group(1).upper(), m.group(2).strip()))
            letra_esperada += 1
        elif alts and t and not m:
            antiga = alts[-1][1]
            alts[-1] = (alts[-1][0], (antiga + "\n" + t).strip())
        elif alts and m:
            break
    if len(alts) < 2 or idx_primeira is None:
        return corpo, []
    enunciado = corpo[:idx_primeira]
    while enunciado and not enunciado[-1].strip():
        enunciado.pop()
    return enunciado, alts


def detectar_grupos(questoes: list[dict], pre: list[str]) -> dict[int, tuple[int, int, str]]:
    """Detecta avisos de texto-base; retorna {questao: (ini, fim, corpo_do_texto)}."""
    grupos: dict[int, tuple[int, int, str]] = {}
    num_por_indice = {i: q["numero"] for i, q in enumerate(questoes)}

    # anúncio no conteúdo prévio (capa/instruções): o texto-base é o que vem depois
    pre_linhas = limpar_corpo(pre, e_pre=True)
    if pre_linhas:
        plano = "\n".join(pre_linhas)
        achado = None
        for rex in TEXTO_BASE_RES:
            m = rex.search(plano)
            if m:
                achado = m
                break
        if achado:
            trecho_pre = re.sub(r"\s+", " ", achado.group(0)).strip().lower()
            linha_origem_pre = next(
                (
                    l
                    for l in pre_linhas
                    if trecho_pre in re.sub(r"\s+", " ", l).strip().lower()
                ),
                None,
            )
            if linha_origem_pre is not None and not re.search(
                r"[a-z\u00e0-\u00fc]", linha_origem_pre
            ):
                achado = None
        if achado:
            ini = int(achado.group(1))
            fim = int(achado.group(2)) if achado.lastindex and achado.lastindex >= 2 else ini
            if 0 <= fim - ini <= 40:
                pos_fim = plano.find("\n", achado.end())
                corpo = plano[pos_fim + 1:].strip() if pos_fim != -1 else ""
                if corpo:
                    for num in range(ini, fim + 1):
                        grupos[num] = (ini, fim, corpo)

    # anúncio dentro de seções de questão (antes da 1a questão do grupo)
    for i, q in enumerate(questoes):
        conteudo = re.sub(r"\s+", " ", "\n".join(q["linhas"]))
        aviso = None
        for rex in TEXTO_BASE_RES:
            m = rex.search(conteudo)
            if m:
                aviso = m
                break
        if not aviso:
            continue
        trecho = re.sub(r"\s+", " ", aviso.group(0)).strip().lower()
        linha_origem = next(
            (
                l
                for l in q["linhas"]
                if trecho in re.sub(r"\s+", " ", l).strip().lower()
            ),
            None,
        )
        if linha_origem is not None and not re.search(r"[a-z\u00e0-\u00fc]", linha_origem):
            continue
        ini = int(aviso.group(1))
        fim = int(aviso.group(2)) if aviso.lastindex and aviso.lastindex >= 2 else ini
        if fim < ini or fim - ini > 40:
            continue
        proxima = None
        for j in range(i + 1, len(questoes)):
            if num_por_indice[j] == ini:
                proxima = j
                break
        if proxima is None:
            continue
        corpo = "\n".join(limpar_corpo(questoes[i]["linhas"])).strip()
        corpo = re.sub(re.escape(aviso.group(0)), "", corpo, count=1, flags=re.IGNORECASE).strip()
        if not corpo:
            continue
        for num in range(ini, fim + 1):
            grupos[num] = (ini, fim, corpo)
    return grupos


def parsear_gabarito_grade(texto_bloco: str, total_questoes: int) -> dict[int, str]:
    """Interpreta gabaritos em grade: linha(s) de números seguida(s) da coluna de letras.

    Formatos cobertos: números um por linha ou vários por linha ("01 02 03..."),
    letras uma por linha ou várias por linha, com "nula"/"ANULADA".
    """
    numeros: list[int] = []
    letras: list[str] = []
    esperado = 1
    for linha in texto_bloco.splitlines():
        t = linha.replace("\xa0", " ").strip()
        if not t or "/" in t or "N\u00ba" in t or "N\u00b0" in t:
            continue
        if NUM_SOZINHO_RE.match(t):
            for tok in re.findall(r"\d{1,3}", t):
                if int(tok) == esperado:
                    numeros.append(int(tok))
                    esperado += 1
            continue
        if re.fullmatch(r"[\s.|]*nula[\s.|]*", t, re.IGNORECASE):
            letras.append("ANULADA")
            continue
        if LETRA_SOZINHA_RE.match(t):
            letras.extend(ch.upper() for ch in re.findall(r"[A-Ea-e]", t))

    if not numeros or len(numeros) != len(letras):
        return {}
    if numeros != list(range(1, len(numeros) + 1)):
        return {}
    respostas = {n: l for n, l in zip(numeros, letras)}
    if len(respostas) < max(3, total_questoes * 0.6):
        return {}
    return {n: respostas[n] for n in sorted(respostas) if 1 <= n <= total_questoes}


ANULADA_TOKENS = {"N", "X", "*", "#", "ANULADA", "ANULAD", "ANUL", "NULA", "NULO"}


def parsear_gabarito_vertical(
    palavras: list[tuple[float, float, float, float, str]], total_questoes: int
) -> dict[int, str]:
    """Interpreta gabaritos em colunas verticais usando coordenadas das palavras.

    Formato típico: duas colunas lado a lado ("1  A", "2  C", ...) renderizadas
    como palavras separadas na mesma linha, inclusive com múltiplos pares por
    linha e números fatiados em dígitos ("3" "5" para "35").
    """
    if not palavras:
        return {}
    palavras = [tuple(w[:5]) for w in palavras]
    ordenadas = sorted(palavras, key=lambda w: (round(w[1], 1), w[0]))
    linhas: list[list[tuple[float, float, float, float, str]]] = []
    atual: list[tuple[float, float, float, float, str]] = []
    y_atual: float | None = None
    for w in ordenadas:
        if y_atual is None or abs(w[1] - y_atual) <= 4.0:
            atual.append(w)
            y_atual = w[1] if y_atual is None else y_atual
        else:
            linhas.append(atual)
            atual = [w]
            y_atual = w[1]
    if atual:
        linhas.append(atual)

    respostas: dict[int, str] = {}
    for linha in linhas:
        tokens = sorted(linha, key=lambda w: w[0])
        numeros: list[tuple[float, int]] = []
        letras: list[tuple[float, str]] = []
        for idx, (x0, _y0, x1, _x1b, tok) in enumerate(tokens):
            limpo = tok.strip(".:-")
            if re.fullmatch(r"\d{1,3}", limpo):
                anterior = tokens[idx - 1] if idx > 0 else None
                anterior_limpo = anterior[4].strip(".:-") if anterior else ""
                gap = x0 - anterior[2] if anterior else 999.0
                if (
                    numeros
                    and re.fullmatch(r"\d{1,3}", anterior_limpo)
                    and gap < 7.0
                ):
                    x_anterior, n_anterior = numeros[-1]
                    numeros[-1] = (x_anterior, n_anterior * 10 ** len(limpo) + int(limpo))
                else:
                    numeros.append((x0, int(limpo)))
            elif re.fullmatch(r"[A-Ea-e]", limpo):
                letras.append((x0, limpo.upper()))
            elif limpo.upper() in ANULADA_TOKENS:
                letras.append((x0, "ANULADA"))
        if not numeros or not letras or len(numeros) != len(letras):
            continue
        if [n for _x, n in numeros] != sorted(n for _x, n in numeros):
            continue
        for (_nx, num), (_lx, letra) in zip(numeros, letras):
            if 1 <= num <= total_questoes and num not in respostas:
                respostas[num] = letra
    cobertas = sum(1 for n in range(1, total_questoes + 1) if n in respostas)
    if cobertas < max(3, total_questoes * 0.6):
        return {}
    return {n: respostas[n] for n in sorted(respostas)}


def parsear_gabarito_colunas(texto_bloco: str, total_questoes: int) -> dict[int, str]:
    """Interpreta gabaritos em grade colunar com marcação N/X (número + letra por linha).

    Formato típico (FURB e similares):
        01: A
        02: X        (X = anulada)
    """
    respostas: dict[int, str] = {}
    for linha in texto_bloco.splitlines():
        t = linha.replace("\xa0", " ").strip()
        m = re.match(r"^(\d{1,3})\s*[-\u2013\u2014:.|]?\s*([A-Ea-eXx*#]|ANULAD[AO]|NULA)\s*$", t)
        if not m:
            continue
        num = int(m.group(1))
        val = m.group(2).upper()
        if not (1 <= num <= total_questoes):
            continue
        if val in {"X", "*", "#", "ANULADA", "ANULADO", "NULA", "NULO"}:
            respostas[num] = "ANULADA"
        else:
            respostas[num] = val
    cobertas = sum(1 for n in range(1, total_questoes + 1) if n in respostas)
    if cobertas < max(3, total_questoes * 0.6):
        return {}
    return {n: respostas[n] for n in sorted(respostas)}


def normalizar_cargo(nome: str) -> str:
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", nome.lower())).strip()


def extrair_cargo_da_prova(cru_prova: str) -> str:
    cru_prova = cru_prova.replace("\xa0", " ").replace("\r", " ").replace("\t", " ")
    m = CARGO_PROVA_RE.search(cru_prova)
    if m:
        bruto = (m.group(2) or "").strip() or m.group(1)
    else:
        m2 = re.search(
            r"^\s*cargo\s*[:\u2013\u2014\-]?\s*([A-Za-z\u00c0-\u00dc][^\n]{2,60})$",
            cru_prova,
            re.MULTILINE | re.IGNORECASE,
        )
        bruto = m2.group(1).strip() if m2 else ""
    primeira = re.split(r"[\n\r]", bruto)[0]
    primeira = re.sub(r"^[\d]+(?:[\.,]\d+)?[\s\u2013\u2014\-]+", "", primeira).strip()
    if primeira:
        return primeira
    for linha in cru_prova.splitlines():
        t = linha.replace("\xa0", " ").strip()
        if not re.fullmatch(r"[A-Z\u00c0-\u00dc][A-Z\u00c0-\u00dc \t]{3,60}", t):
            continue
        if re.search(
            r"GABARITO|CONCURSO|C\u00c2MARA|C\u00c3MARA|PREFEITURA|EDITAL|INSTRU\u00c7\u00d5ES|CADERNO|PROVA|N\u00cdVEL|EST\u00c2NCIA|MUNICIPAL|ESTADO|BOLETIM|QUEST\u00d5ES|WWW|REALIZA\u00c7\u00c3O",
            t,
        ):
            continue
        return t
    return ""


TIPO_PROVA_RE = re.compile(r"TIPO\s*(\d+)", re.IGNORECASE)
ROTULO_CARGO_RE = re.compile(
    r"^\s*([A-Z]{2,10})\s*[\u2013\u2014-]\s*([A-Z\u00c0-\u00dc][A-Z\u00c0-\u00dc\s/]{2,60})\s*$",
    re.MULTILINE,
)
PALAVRAS_COMUNS_CARGO = {
    "lingua", "portugues", "matematica", "conhecimentos", "gerais",
    "especificos", "texto", "atualidades", "informatica", "questoes",
    "gabarito", "definitivo", "preliminar", "prova", "candidato",
    "manha", "tarde", "noite", "turno",
}


def so_palavras_comuns(nome: str) -> bool:
    tokens = set(nome.split())
    return bool(tokens) and tokens <= PALAVRAS_COMUNS_CARGO


def canon_cargo(nome: str) -> str:
    return " ".join(sorted(nome.split()))


def selecionar_bloco_gabarito(
    texto_gab: str, cru_prova: str, total_questoes: int
) -> tuple[str, str]:
    """Seleciona o bloco do cargo correto em gabaritos com v\u00e1rios cargos.

    Retorna (texto_do_bloco_ou_completo, observa\u00e7\u00e3o).
    """
    blocos = list(CABECALHO_BLOCO_RE.finditer(texto_gab))
    linhas_cargo = list(CARGO_LINHA_RE.finditer(texto_gab))
    linhas_completas = list(CARGO_LINHA_COMPLETA_RE.finditer(texto_gab))
    rotulos = list(ROTULO_CARGO_RE.finditer(texto_gab))
    if (
        len(blocos) <= 1
        and len(linhas_cargo) <= 1
        and len(linhas_completas) <= 1
        and len(rotulos) <= 1
    ):
        return texto_gab, ""

    candidatos: list[tuple[int, int, str, str]] = []
    for i, b in enumerate(blocos):
        fim = blocos[i + 1].start() if i + 1 < len(blocos) else len(texto_gab)
        rotulo = f"cargo {b.group(1)} - {b.group(2).strip()}"
        candidatos.append((b.start(), fim, normalizar_cargo(b.group(2)), rotulo))
    for i, b in enumerate(linhas_completas):
        fim = len(texto_gab)
        for prox in linhas_completas[i + 1:]:
            if prox.start() > b.end():
                fim = prox.start()
                break
        rotulo = f"cargo {b.group(1).strip()}"
        nome_bruto = b.group(1).strip()
        if "/" in nome_bruto:
            nome_bruto = " ".join(p.strip() for p in sorted(nome_bruto.split("/")))
        candidatos.append((b.start(), fim, normalizar_cargo(nome_bruto), rotulo))
    for i, b in enumerate(linhas_cargo):
        nome = normalizar_cargo(b.group(1))
        if so_palavras_comuns(nome):
            continue
        fim = len(texto_gab)
        for prox in linhas_cargo[i + 1:]:
            if prox.start() > b.end() and not so_palavras_comuns(
                normalizar_cargo(prox.group(1))
            ):
                fim = prox.start()
                break
        for outro in [*linhas_completas, *blocos]:
            if b.start() < outro.start() < fim:
                fim = min(fim, outro.start())
                break
        rotulo = f"cargo {b.group(1).strip()}"
        candidatos.append((b.start(), fim, nome, rotulo))
    for i, b in enumerate(rotulos):
        fim = len(texto_gab)
        for prox in rotulos:
            if prox.start() > b.end():
                fim = prox.start()
                break
        rotulo = f"cargo {b.group(1).strip()} - {b.group(2).strip()}"
        candidatos.append((b.start(), fim, normalizar_cargo(b.group(2)), rotulo))

    candidatos.sort(key=lambda c: c[0])
    if not candidatos:
        return texto_gab, ""

    m_tipo = TIPO_PROVA_RE.search(cru_prova)
    tipo_prova = m_tipo.group(1) if m_tipo else ""

    def com_tipo(texto: str) -> bool:
        if not tipo_prova:
            return False
        m = TIPO_PROVA_RE.search(texto)
        return bool(m and m.group(1) == tipo_prova)

    def casa(a: str, b: str) -> bool:
        if not a or not b:
            return False
        if a in b or b in a:
            return True
        ca, cb = canon_cargo(a), canon_cargo(b)
        return bool(ca and cb and (ca in cb or cb in ca))

    alvo = normalizar_cargo(extrair_cargo_da_prova(cru_prova))
    if alvo and so_palavras_comuns(alvo):
        alvo = ""
    if alvo:
        casados = [c for c in candidatos if casa(alvo, c[2])]
        for c in casados:
            if com_tipo(texto_gab[c[0]:c[1]]):
                return texto_gab[c[0]:c[1]], c[3]
        if casados:
            return texto_gab[casados[0][0]:casados[0][1]], casados[0][3]

    plano_prova = normalizar_cargo(re.sub(r"\s+", " ", cru_prova))
    por_texto = [
        c
        for c in candidatos
        if len(c[2]) >= 8
        and not so_palavras_comuns(c[2])
        and c[2] in plano_prova
        and len(parsear_gabarito(texto_gab[c[0]:c[1]], total_questoes))
        >= total_questoes * 0.9
    ]
    for c in por_texto:
        if com_tipo(texto_gab[c[0]:c[1]]):
            return texto_gab[c[0]:c[1]], c[3]
    if por_texto:
        c = por_texto[0]
        return texto_gab[c[0]:c[1]], c[3]

    completos = []
    for c in candidatos:
        r = parsear_gabarito(texto_gab[c[0]:c[1]], total_questoes)
        if len(r) == total_questoes:
            completos.append(c)
    if len(completos) == 1:
        c = completos[0]
        return (
            texto_gab[c[0]:c[1]],
            f"{c[3]} (identificado pela quantidade de quest\u00f5es)",
        )
    if completos:
        tokens_prova = set(plano_prova.split())
        melhor, melhor_score = None, 0
        for c in completos:
            score = sum(1 for t in set(c[2].split()) if t in tokens_prova)
            if score > melhor_score:
                melhor, melhor_score = c, score
        if melhor is not None and melhor_score > 0:
            rotulo = melhor[3]
            if com_tipo(texto_gab[melhor[0]:melhor[1]]):
                rotulo += " \u2014 tipo compat\u00edvel com a prova"
            return texto_gab[melhor[0]:melhor[1]], rotulo
        return "", (
            "Gabarito cont\u00e9m v\u00e1rios blocos compat\u00edveis em quantidade de quest\u00f5es "
            "e nenhum cargo p\u00f4de ser associado com seguran\u00e7a \u00e0 prova; gabarito n\u00e3o "
            "preenchido automaticamente."
        )
    return "", (
        "Gabarito cont\u00e9m v\u00e1rios cargos e nenhum corresponde ao cargo identificado "
        "na prova; gabarito n\u00e3o preenchido automaticamente."
    )



def parsear_gabarito(texto_cru: str, total_questoes: int) -> dict[int, str]:
    """Extrai pares questão->letra do texto do PDF de gabarito.

    Tenta o formato inline ("01 B 02 D..." / "1: B"), depois o formato em grade
    (números e letras em linhas separadas). Só aceita resultados confiáveis.
    """
    def confiavel(respostas: dict[int, str]) -> bool:
        if len(respostas) < max(3, total_questoes * 0.6):
            return False
        cobertas = sum(1 for n in range(1, total_questoes + 1) if n in respostas)
        return cobertas >= total_questoes * 0.6

    texto = re.sub(r"\s+", " ", texto_cru)
    respostas: dict[int, str] = {}
    for m in ANULADA_RE.finditer(texto):
        num = int(m.group(1))
        if 1 <= num <= total_questoes:
            respostas[num] = "ANULADA"
    for m in ANULADA_HASH_RE.finditer(texto):
        num = int(m.group(1))
        if 1 <= num <= total_questoes:
            respostas[num] = "ANULADA"
    for m in ANULADA_X_RE.finditer(texto):
        num = int(m.group(1))
        if 1 <= num <= total_questoes:
            respostas[num] = "ANULADA"
    for m in GABARITO_PAR_RE.finditer(texto):
        num = int(m.group(1))
        letra = m.group(2).upper()
        if 1 <= num <= total_questoes and num not in respostas:
            respostas[num] = letra
    for m in VF_RE.finditer(texto):
        num = int(m.group(1))
        letra = m.group(2).upper()
        if 1 <= num <= total_questoes and num not in respostas:
            respostas[num] = letra

    if confiavel(respostas):
        return {n: respostas[n] for n in sorted(respostas)}

    grade = parsear_gabarito_grade(texto_cru, total_questoes)
    if grade:
        return grade
    return {}


def limpar_marcador(enunciado: list[str], numero: int) -> list[str]:
    if not enunciado:
        return enunciado
    primeira = enunciado[0].strip()
    m_head = QUESTAO_HEAD_RE.match(primeira)
    m_ord = QUESTAO_HEAD_ORDINAL_RE.match(primeira)
    m_inline = QUESTAO_HEAD_INLINE_RE.match(primeira)
    m_num = re.match(
        rf"^\s*(?:\*\*)?\s*0?{numero}\s*[\.\)]\s*\**\s*(.*)$", primeira
    )
    if (m_head and int(m_head.group(1)) == numero) or (
        m_ord and int(m_ord.group(1)) == numero
    ):
        enunciado = enunciado[1:]
    elif m_inline and int(m_inline.group(1)) == numero:
        resto = m_inline.group(2).strip(" -\u2013\u2014:.")
        enunciado = ([resto] if resto else []) + enunciado[1:]
    elif m_num:
        resto = m_num.group(1).strip()
        enunciado = ([resto] if resto else []) + enunciado[1:]
    while enunciado and not enunciado[0].strip():
        enunciado.pop(0)
    return enunciado


def coletar_imagens_do_bloco(enunciado: list[str]) -> list[str]:
    texto = "\n".join(enunciado)
    vistos: list[str] = []
    for caminho in IMG_RE.findall(texto):
        if caminho not in vistos:
            vistos.append(caminho)
    return vistos


def renderizar_questao(
    numero: int,
    enunciado: list[str],
    alts: list[tuple[str, str]],
    material: str | None,
    gabarito: str | None,
    origem_gabarito: str,
) -> str:
    partes = [f"#### QUESTÃO {numero:02d}", ""]
    if gabarito:
        if gabarito == "ANULADA":
            partes.append("⚠️ **Gabarito: ANULADA**")
        else:
            partes.append(f"✅ **Gabarito: {gabarito}** ({origem_gabarito})")
        partes.append("")
    if material:
        partes.append("**Material de apoio:**")
        partes.append("")
        partes.append(material)
        partes.append("")
    partes.append("**Enunciado:**")
    partes.append("")
    partes.extend(enunciado)
    partes.append("")
    if alts:
        partes.append("**Alternativas:**")
        partes.append("")
        for letra, conteudo in alts:
            partes.append(f"{letra}) {conteudo}")
        partes.append("")
    imagens = coletar_imagens_do_bloco(enunciado)
    partes.append("**Referências visuais:**")
    partes.append("")
    if imagens:
        for caminho in imagens:
            partes.append(f"![Imagem da questão]({caminho})")
            partes.append("")
    else:
        partes.append("Nenhuma.")
        partes.append("")
    partes.append("---")
    partes.append("")
    return "\n".join(partes)


def montar_prova(
    nome: str,
    pre: list[str],
    questoes: list[dict],
    grupos: dict[int, tuple[int, int, str]],
    gabarito: dict[int, str],
    origem_gabarito: str,
    total_imagens: int = 0,
    observacoes_extras: list[str] | None = None,
    via_ocr: bool = False,
    pos_texto: list[str] | None = None,
) -> tuple[str, str]:
    num_para_q = {q["numero"]: q for q in questoes}
    nums_grupos: dict[tuple[int, int], list[int]] = {}
    for num, (ini, fim, _) in sorted(grupos.items()):
        nums_grupos.setdefault((ini, fim), []).append(num)

    total = len(questoes)
    nums_agrupadas = sorted({n for ns in nums_grupos.values() for n in ns})
    nums_independentes = [q["numero"] for q in questoes if q["numero"] not in grupos]
    todas_imagens = sorted(
        {c for q in questoes for c in coletar_imagens_do_bloco(limpar_corpo(q["linhas"]))}
    )
    n_imagens_prova = max(total_imagens, len(todas_imagens))

    md: list[str] = [f"# PROVA — {nome}", ""]
    md.append("## 1. Análise geral da prova")
    md.append("")
    md.append(f"- **Identificação:** {nome}")
    md.append(f"- **Quantidade total de questões:** {total}")
    md.append(f"- **Quantidade de textos de apoio (grupos):** {len(nums_grupos)}")
    md.append(f"- **Quantidade de imagens:** {n_imagens_prova}")
    md.append("- **Quantidade de gráficos e tabelas:** incluídos nas imagens e no texto extraído, quando presentes no PDF original")
    md.append(f"- **Quantidade de grupos identificados:** {len(nums_grupos)}")
    md.append(f"- **Quantidade de questões independentes:** {len(nums_independentes)}")
    if nums_grupos:
        detalhes = "; ".join(
            f"texto-base das questões {ini:02d} a {fim:02d} → questões {', '.join(f'{n:02d}' for n in ns)}"
            for (ini, fim), ns in sorted(nums_grupos.items())
        )
        md.append(f"- **Questões que compartilham materiais:** {detalhes}")
    else:
        md.append("- **Questões que compartilham materiais:** nenhuma identificada automaticamente")
    md.append("")

    if pre:
        md.append("### Transcrição integral da capa/instruções (conforme extraída do PDF)")
        md.append("")
        md.append("> [!NOTE]")
        md.append("> Conteúdo integral das páginas anteriores à primeira questão, sem cortes.")
        md.append("")
        for linha in limpar_corpo(pre):
            md.append(f"> {linha}" if linha.strip() else ">")
        md.append("")

    if gabarito:
        md.append("### Gabarito")
        md.append("")
        for inicio in range(1, total + 1, 5):
            faixa = range(inicio, min(inicio + 5, total + 1))
            cab = "| Questão | " + " | ".join(f"{n:02d}" for n in faixa) + " |"
            sep = "|---|" + "---|" * len(faixa)
            val = "| Resposta | " + " | ".join(
                gabarito.get(n, "—") for n in faixa
            ) + " |"
            md.append(cab)
            md.append(sep)
            md.append(val)
            md.append("")

    md.append("## 2. Questões agrupadas")
    md.append("")
    if not nums_grupos:
        md.append("Nenhum grupo de questões compartilhando material foi identificado automaticamente nesta prova.")
        md.append("")
    for gi, ((ini, fim), ns) in enumerate(sorted(nums_grupos.items()), start=1):
        _, _, corpo_texto = grupos[ns[0]]
        md.append(f"### GRUPO {gi:02d} — Texto-base compartilhado pelas questões {ini:02d} a {fim:02d}")
        md.append("")
        md.append("**Questões relacionadas:** " + ", ".join(f"{n:02d}" for n in ns) + ".")
        md.append("")
        for n in ns:
            q = num_para_q[n]
            enunciado, alts = separar_alternativas(limpar_corpo(q["linhas"]))
            enunciado = limpar_marcador(enunciado, n)
            md.append(
                renderizar_questao(
                    n, enunciado, alts, corpo_texto,
                    gabarito.get(n), origem_gabarito,
                )
            )

    md.append("## 3. Questões independentes")
    md.append("")
    for n in nums_independentes:
        q = num_para_q[n]
        enunciado, alts = separar_alternativas(limpar_corpo(q["linhas"]))
        enunciado = limpar_marcador(enunciado, n)
        md.append(
            renderizar_questao(
                n, enunciado, alts, None, gabarito.get(n), origem_gabarito
            )
        )

    if pos_texto:
        pos_limpas = limpar_corpo(pos_texto)
        if pos_limpas:
            md.append("### Transcrição integral das páginas finais (após a última questão)")
            md.append("")
            md.append("> [!NOTE]")
            md.append(
                "> Conteúdo integral das páginas seguintes à última questão "
                "(ex.: prova discursiva, temas, folhas de rascunho), sem cortes."
            )
            md.append("")
            for linha in pos_limpas:
                md.append(f"> {linha}" if linha.strip() else ">")
            md.append("")

    md.append("## 4. Observações e limitações da extração")
    md.append("")
    global SECOES_REMOVIDAS
    obs = [
        (
            "Conteúdo extraído via OCR de PDF escaneado (imagem), transcrito integralmente e conferido contra o original."
            if via_ocr
            else "Extração automática (texto selecionável do PDF via PyMuPDF), sem OCR: PDFs escaneados podem perder texto."
        ),
        "Imagens repetidas (logos/marcas d'água) foram descartadas; as imagens de conteúdo foram salvas em `imagens/` com nomenclatura `imagem_00N`.",
        "A detecção de grupos usa os avisos padrão das bancas (\"o texto seguinte servirá de base...\"). Bancas sem esse aviso podem ter grupos não identificados — o conteúdo, porém, permanece integral.",
        "Se houver divergência entre esta versão e o PDF original, vale o PDF original; corrija manualmente o Markdown.",
    ]
    if gabarito and len(gabarito) < total:
        faltam = [n for n in range(1, total + 1) if n not in gabarito]
        obs.append(
            f"Gabarito incompleto: não foi possível identificar a resposta das questões {', '.join(f'{n:02d}' for n in faltam)} no PDF de gabarito."
        )
    if not gabarito:
        obs.append("Gabarito oficial não disponível/pareado — nenhuma resposta foi preenchida.")
    if pos_texto and limpar_corpo(pos_texto):
        obs.append(
            "O PDF original contém páginas após a última questão objetiva "
            "(prova discursiva e/ou folhas de rascunho); esse conteúdo foi transcrito "
            "integralmente na seção \"Transcrição integral das páginas finais\"."
        )
    if SECOES_REMOVIDAS:
        obs.append(
            "Cabeçalhos de seção do caderno ("
            + ", ".join(f'"{t}"' for t in SECOES_REMOVIDAS)
            + ") foram removidos do corpo das questões por serem divisores estruturais; a numeração e o conteúdo das questões foram preservados."
        )
    SECOES_REMOVIDAS = []
    for extra in observacoes_extras or []:
        obs.append(extra)
    for o in obs:
        md.append(f"- {o}")
    md.append("")
    prova_md = "\n".join(md)

    rel: list[str] = [f"# Relatório de análise — {nome}", ""]
    rel.append("## Resumo")
    rel.append("")
    rel.append(f"- Questões identificadas: **{total}**")
    rel.append(f"- Grupos com material compartilhado: **{len(nums_grupos)}**")
    rel.append(f"- Questões agrupadas: **{len(nums_agrupadas)}**")
    rel.append(f"- Questões independentes: **{len(nums_independentes)}**")
    rel.append(f"- Imagens extraídas: **{n_imagens_prova}**")
    rel.append(f"- Gabarito: **{'preenchido (' + origem_gabarito + ')' if gabarito else 'não disponível'}**")
    rel.append("")
    rel.append("| Material compartilhado | Questões vinculadas | Tipo |")
    rel.append("|---|---|---|")
    if nums_grupos:
        for (ini, fim), ns in sorted(nums_grupos.items()):
            rel.append(
                f"| Texto-base compartilhado (questões {ini:02d} a {fim:02d}) | "
                + ", ".join(f"{n:02d}" for n in ns)
                + " | Texto |"
            )
    else:
        rel.append("| — | — | — |")
    rel.append("")
    relatorio_md = "\n".join(rel)
    return prova_md, relatorio_md


def parear_pdfs(pdfs: list[Path]) -> list[tuple[Path, Path | None]]:
    """Pareia Prova + Gabarito pela semelhança do nome (sem os prefixos)."""
    def chave(p: Path) -> str:
        nome = re.sub(r"^[A-Za-z0-9]{6,10}-", "", p.stem)
        nome = re.sub(r"(?i)^(prova|gabarito)\s*[-\u2013\u2014:]?\s*", "", nome)
        nome = re.sub(r"(?i)\s*gabarito\s*[-\u2013\u2014:]?\s*", " ", nome)
        return re.sub(r"[^a-z0-9]", "", nome.lower())

    provas = [p for p in pdfs if not re.search(r"(?i)gabarito", p.stem)]
    gabas = [p for p in pdfs if re.search(r"(?i)gabarito", p.stem)]
    pares: list[tuple[Path, Path | None]] = []
    usados: set[Path] = set()
    for prova in provas:
        cp = chave(prova)
        cg = ""
        melhor = None
        melhor_score = 0
        for gaba in gabas:
            if gaba in usados:
                continue
            cg = chave(gaba)
            comum = sum(1 for i in range(0, min(len(cp), len(cg)), 4) if cp[i:i+4] == cg[i:i+4])
            if comum > melhor_score:
                melhor_score = comum
                melhor = gaba
        if melhor is None and not cp and not cg and gabas:
            melhor = gabas[0]
            melhor_score = 1
        if melhor and melhor_score >= 1:
            usados.add(melhor)
            pares.append((prova, melhor))
        else:
            pares.append((prova, None))
    return pares


def nome_pasta(prova: Path, nome_forcado: str | None) -> str:
    nome = nome_forcado
    if not nome:
        nome = re.sub(r"^[A-Za-z0-9]{6,10}-", "", prova.stem)
        nome = re.sub(r"(?i)^(prova|gabarito)\s*[-\u2013\u2014:]?\s*", "", nome)
        nome = re.sub(r"\s*-\s*", "_", nome)
        nome = re.sub(r"[^\w\- ]+", "_", nome).strip().replace(" ", "_")
        nome = re.sub(r"_+", "_", nome).strip("_") or "Prova_Sem_Nome"
    return nome


def renomear_imagens(
    pasta_imagens: Path,
    questoes: list[dict],
    pre: list[str],
    grupos: dict[int, tuple[int, int, str]],
) -> None:
    """Renomeia imagens/ para imagem_001, imagem_002... e atualiza referências."""
    existentes = sorted(
        (a for a in pasta_imagens.iterdir() if a.suffix.lower() in IMG_EXTS),
        key=lambda a: a.name,
    )
    mapa: dict[str, str] = {}
    for i, antigo in enumerate(existentes, start=1):
        novo = f"imagem_{i:03d}{antigo.suffix.lower()}"
        if antigo.name == novo:
            continue
        if antigo.suffix.lower() != Path(novo).suffix.lower():
            novo = f"imagem_{i:03d}{antigo.suffix.lower()}"
        mapa[antigo.name] = novo
    if not mapa:
        return
    for antigo, novo in mapa.items():
        (pasta_imagens / antigo).rename(pasta_imagens / (novo + ".tmp"))
    for antigo, novo in mapa.items():
        (pasta_imagens / (novo + ".tmp")).rename(pasta_imagens / novo)

    def atualizar(texto: str) -> str:
        for antigo, novo in mapa.items():
            texto = texto.replace(f"imagens/{antigo}", f"imagens/{novo}")
        return texto

    for q in questoes:
        q["linhas"] = [atualizar(l) for l in q["linhas"]]
    pre[:] = [atualizar(l) for l in pre]
    for chave, (ini, fim, corpo) in list(grupos.items()):
        grupos[chave] = (ini, fim, atualizar(corpo))


def processar_prova(
    prova: Path,
    gabarito: Path | None,
    pasta_saida: Path,
    nome_forcado: str | None,
    colunas: int = 1,
) -> Path:
    nome = nome_pasta(prova, nome_forcado)
    pasta_prova = pasta_saida / nome
    pasta_imagens = pasta_prova / "imagens"
    if pasta_prova.exists():
        shutil.rmtree(pasta_prova)
    pasta_imagens.mkdir(parents=True)

    print(f"[{nome}] extraindo {prova.name}...")
    cru = extrair_pdf(prova, pasta_imagens, colunas)
    questoes, pre = detectar_questoes(cru)
    if not questoes:
        print(f"[{nome}] ⚠️ nenhuma questão detectada — PDF provavelmente escaneado (precisa de OCR).")
        (pasta_prova / "prova_organizada.md").write_text(cru, encoding="utf-8")
        (pasta_prova / "relatorio_analise.md").write_text(
            f"# Relatório de análise — {nome}\n\n"
            "⚠️ Nenhuma questão foi detectada automaticamente: o PDF provavelmente é "
            "escaneado (sem texto selecionável) e precisa de OCR antes de ser processado "
            "por esta ferramenta. O texto bruto extraído foi mantido em `prova_organizada.md`.\n",
            encoding="utf-8",
        )
    else:
        grupos = detectar_grupos(questoes, pre)

        # Descarta imagens que só aparecem na capa (logos/brasões) e
        # renumera as restantes como imagem_001, imagem_002...
        grupo_corpos = "\n".join(g[2] for g in grupos.values())
        referenciadas = set(IMG_RE.findall(grupo_corpos)) | {
            c for q in questoes for c in coletar_imagens_do_bloco(q["linhas"])
        }
        pre_texto = "\n".join(pre)
        for cam in sorted(set(IMG_RE.findall(pre_texto))):
            if cam in referenciadas:
                continue
            arquivo = pasta_imagens / Path(cam).name
            if arquivo.exists():
                arquivo.unlink()
            pre_texto = "\n".join(l for l in pre_texto.split("\n") if cam not in l)
        pre = pre_texto.split("\n")
        renomear_imagens(pasta_imagens, questoes, pre, grupos)

        gabarito_map: dict[int, str] = {}
        origem = ""
        observacoes_gabarito: list[str] = []
        if gabarito is not None:
            print(f"[{nome}] pareado com gabarito: {gabarito.name}")
            doc = fitz.open(gabarito)
            texto_gab = "\n".join(p.get_text() for p in doc)
            palavras_gab = [tuple(w[:5]) for p in doc for w in p.get_text("words")]
            doc.close()
            texto_gab, obs_gab = selecionar_bloco_gabarito(texto_gab, cru, len(questoes))
            gabarito_map = parsear_gabarito(texto_gab, len(questoes)) if texto_gab else {}
            if not gabarito_map:
                gabarito_map = parsear_gabarito_colunas(texto_gab, len(questoes)) if texto_gab else {}
            if not gabarito_map:
                gabarito_map = parsear_gabarito_vertical(palavras_gab, len(questoes))
            if gabarito_map:
                print(f"[{nome}] gabarito interpretado: {len(gabarito_map)} respostas")
            if gabarito_map:
                origem = f"gabarito oficial pareado{(' — ' + obs_gab) if obs_gab else ''}"
            else:
                print(f"[{nome}] ⚠️ gabarito pareado mas não interpretado com confiança.")
                if obs_gab:
                    observacoes_gabarito.append(obs_gab)
        n_imgs = len([a for a in pasta_imagens.iterdir() if a.suffix.lower() in IMG_EXTS])
        prova_md, relatorio_md = montar_prova(
            nome, pre, questoes, grupos, gabarito_map, origem, n_imgs, observacoes_gabarito
        )
        (pasta_prova / "prova_organizada.md").write_text(prova_md, encoding="utf-8")
        (pasta_prova / "relatorio_analise.md").write_text(relatorio_md, encoding="utf-8")
        print(
            f"[{nome}] ok: {len(questoes)} questões, {len(grupos)} questões agrupadas, "
            f"{n_imgs} imagens, gabarito {'sim' if gabarito_map else 'não'}"
        )

    with zipfile.ZipFile(pasta_prova / "PROVA_ORGANIZADA.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.write(pasta_prova / "prova_organizada.md", "prova_organizada.md")
        z.write(pasta_prova / "relatorio_analise.md", "relatorio_analise.md")
        for img in sorted(pasta_imagens.iterdir()):
            if img.suffix.lower() in IMG_EXTS:
                z.write(img, f"imagens/{img.name}")
    print(f"[{nome}] ZIP gerado: {pasta_prova / 'PROVA_ORGANIZADA.zip'}")
    return pasta_prova


def processar(
    pasta_pdfs: Path,
    pasta_saida: Path,
    repo: Path | None,
    nome: str | None,
    colunas: int = 1,
) -> None:
    # Windows: glob é case-insensitive — dedupe para não processar cada PDF duas vezes
    pdfs = sorted({p for p in pasta_pdfs.iterdir() if p.suffix.lower() == ".pdf"})
    if not pdfs:
        sys.exit(f"Nenhum PDF encontrado em {pasta_pdfs}")

    pasta_saida.mkdir(parents=True, exist_ok=True)
    pares = parear_pdfs(pdfs)
    if len(pares) == 1:
        processar_prova(pares[0][0], pares[0][1], pasta_saida, nome, colunas)
    else:
        if nome:
            print("⚠️ --nome ignorado: há várias provas na pasta; o nome vem do arquivo.")
        for prova, gabarito in pares:
            processar_prova(prova, gabarito, pasta_saida, None, colunas)

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
        print(f"  cd {repo} && git add -A && git commit -m 'Novas provas organizadas' && git push")


def main() -> None:
    parser = argparse.ArgumentParser(description="Organiza provas em PDF para Markdown (padrão provas_md)")
    parser.add_argument("--pasta", required=True, help="Pasta com os PDFs")
    parser.add_argument("--saida", default="saida", help="Pasta de saída das provas")
    parser.add_argument("--nome", help="Nome da pasta da prova (padrão: Camara_<Cidade>_<Ano>_<Cargo>)")
    parser.add_argument("--repo", help="Caminho do clone de provas_md para copiar o resultado")
    parser.add_argument(
        "--colunas",
        type=int,
        choices=[1, 2],
        default=1,
        help="Layout do PDF: 1 = coluna única (padrão), 2 = duas colunas",
    )
    args = parser.parse_args()

    pasta_pdfs = Path(args.pasta).expanduser().resolve()
    pasta_saida = Path(args.saida).expanduser().resolve()
    repo = Path(args.repo).expanduser().resolve() if args.repo else None
    processar(pasta_pdfs, pasta_saida, repo, args.nome, args.colunas)


if __name__ == "__main__":
    main()
