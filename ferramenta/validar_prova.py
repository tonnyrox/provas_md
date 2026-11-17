#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validador automático do padrão de provas do repositório.

Uso:
    python validar_prova.py --pasta "Provas MD"          # valida todas as provas
    python validar_prova.py --pasta "Provas MD/Camara_X_2024_Cargo"   # valida uma prova

O que verifica (por pasta de prova):
  1. Arquivos obrigatórios: prova_organizada.md, relatorio_analise.md, PROVA_ORGANIZADA.zip.
  2. Seções obrigatórias do prova_organizada.md (1. Análise geral ... 4. Observações).
  3. Numeração das questões: sequência completa de 01 a N, sem faltas nem duplicatas
     (verificada DENTRO de cada seção: agrupadas e independentes podem intercalar).
  4. Alternativas: cada questão objetiva precisa de pelo menos A–D no formato "A)".
  5. Gabaritos: quantidade de linhas de gabarito deve ser igual ao número de questões
     (0 também é aceito = prova sem gabarito; divergência vira AVISO, pois questões
     discursivas têm bloco próprio com "não se aplica"). Gabarito PARCIAL (algumas
     questões com resposta e outras sem) também vira AVISO com a lista das faltantes.
  6. Imagens: toda referência ![...](imagens/...) deve apontar para arquivo existente.
  7. Imagens órfãs: arquivo em imagens/ que nenhuma questão referencia (ERRO — ou é
     conteúdo perdido, como a tirinha de Piracicaba Q08-09, ou lixo a remover).
  8. Grupos: imagem presente no material compartilhado do grupo deve aparecer em
     TODAS as questões relacionadas (regra de autossuficiência).
  9. Questão que cita "tira/figura/gráfico/imagem abaixo ou a seguir" sem nenhuma
     referência de imagem gera AVISO (possível imagem perdida na extração).

Códigos de saída: 0 = tudo OK (avisos permitidos); 1 = há erros que impedem a publicação.
"""

import argparse
import os
import re
import sys

SECAO1 = "## 1. Análise geral da prova"
SECAO2 = "## 2. Questões agrupadas"
SECAO3 = "## 3. Questões independentes"
SECAO4 = "## 4. Observações e limitações da extração"

Q_RE = re.compile(r"^#### QUESTÃO (\d+)$", re.M)
GAB_RE = re.compile(r"^(?:✅|⚠️|🚫) \*\*Gabarito", re.M)
IMG_RE = re.compile(r"!\[[^\]]*\]\((imagens/[^)]+)\)")
GRUPO_RE = re.compile(r"^### GRUPO \d+ — (.*)$", re.M)
REL_RE = re.compile(r"\*\*Questões relacionadas:\*\*\s*([0-9,\s e]+)")
CITA_FIGURA_RE = re.compile(
    r"(leia a tira|analisa ndo a tira|analisando a tira|conforme a figura"
    r"|figura abaixo|imagem abaixo|gráfico abaixo|tabela abaixo)", re.I)


def validar_pasta(pasta):
    erros, avisos = [], []
    md_path = os.path.join(pasta, "prova_organizada.md")
    if not os.path.isfile(md_path):
        return [f"prova_organizada.md ausente"], []
    md = open(md_path, encoding="utf-8").read()

    for f in ("relatorio_analise.md", "PROVA_ORGANIZADA.zip"):
        if not os.path.exists(os.path.join(pasta, f)):
            erros.append(f"{f} ausente")

    for sec in (SECAO1, SECAO2, SECAO3, SECAO4):
        if sec not in md:
            erros.append(f"seção ausente: {sec}")
    if erros:
        return erros, avisos

    def secao(ini, fim):
        return md.split(ini)[1].split(fim)[0]

    s2 = secao(SECAO2, SECAO3)
    s3 = secao(SECAO3, SECAO4)
    n2 = [int(x) for x in Q_RE.findall(s2)]
    n3 = [int(x) for x in Q_RE.findall(s3)]
    todas = n2 + n3
    if not todas:
        erros.append("nenhuma questão no formato '#### QUESTÃO NN'")
    else:
        falta = sorted(set(range(1, max(todas) + 1)) - set(todas))
        dup = sorted({x for x in todas if todas.count(x) > 1})
        if falta:
            erros.append(f"numeração com faltas: {falta[:8]}")
        if dup:
            erros.append(f"numeração duplicada: {dup[:8]}")
        if n3 != sorted(n3):
            erros.append("questões independentes fora de ordem numérica")

    blocos = re.split(r"^#### QUESTÃO \d+$", md, flags=re.M)[1:]
    for i, b in enumerate(blocos, 1):
        b_q = re.split(r"^---\s*$", b, maxsplit=1, flags=re.M)[0]
        letras = sorted(set(re.findall(r"^([A-E])\)", b_q, re.M)))
        if 0 < len(letras) < 4:
            erros.append(f"questão {i:02d}: alternativas incompletas {letras}")

    qtd = len(todas)
    gab = len(GAB_RE.findall(md))
    if qtd and gab not in (0, qtd):
        avisos.append(
            f"linhas de gabarito ({gab}) != questões ({qtd})"
            " — confira se são questões discursivas com bloco próprio"
        )

    for ref in sorted(set(IMG_RE.findall(md))):
        if not os.path.exists(os.path.join(pasta, ref)):
            erros.append(f"referência de imagem quebrada: {ref}")

    img_dir = os.path.join(pasta, "imagens")
    if os.path.isdir(img_dir):
        usadas = set(IMG_RE.findall(md))
        for nome in sorted(os.listdir(img_dir)):
            if nome == ".gitkeep":
                continue
            ref = f"imagens/{nome}"
            if ref not in usadas:
                erros.append(
                    f"imagem órfã (extraída mas nunca referenciada): {ref}"
                    " — ou é conteúdo de questão perdido, ou deve ser removida"
                )

    for g in GRUPO_RE.finditer(md):
        gdesc = g.group(1).strip()[:50]
        ini = g.end()
        prox = GRUPO_RE.search(md, ini)
        seg = md[ini:prox.start() if prox else len(md)]
        mrel = REL_RE.search(seg)
        if not mrel:
            erros.append(f"grupo sem 'Questões relacionadas': {gdesc}")
            continue
        qs = [int(x) for x in re.findall(r"\d+", mrel.group(1))]
        primeiro = min((q for q in qs if q in todas), default=None)
        if primeiro is None:
            continue
        corte = seg.find(f"#### QUESTÃO {primeiro:02d}")
        prox_q = re.search(r"^#### QUESTÃO \d+$", seg[mrel.end():], re.M)
        if corte == -1 or (prox_q and mrel.end() + prox_q.start() < corte):
            continue
        mat_grupo = seg[mrel.end():corte]
        imgs_grupo = set(IMG_RE.findall(mat_grupo))
        if not imgs_grupo:
            continue
        for q in qs:
            pos = md.find(f"#### QUESTÃO {q:02d}")
            if pos == -1:
                erros.append(f"grupo ({gdesc}) cita questão {q} inexistente")
                continue
            fim_q = md.find("#### QUESTÃO", pos + 1)
            bloco = md[pos:fim_q if fim_q != -1 else len(md)]
            faltam = imgs_grupo - set(IMG_RE.findall(bloco))
            if faltam:
                erros.append(
                    f"grupo ({gdesc}) questão {q:02d} sem imagem do material "
                    f"compartilhado: {sorted(faltam)}"
                )

    if gab:
        blocos = re.split(r"^#### QUESTÃO \d+$", md, flags=re.M)[1:]
        sem = [i for i, b in enumerate(blocos, 1) if not GAB_RE.search(b)]
        if sem and len(sem) < len(blocos):
            avisos.append(
                f"gabarito parcial — questões sem resposta: {sem[:15]}"
                " (verifique se o PDF de gabarito não foi lido pela metade)"
            )

    for i, b in enumerate(re.split(r"^#### QUESTÃO \d+$", md, flags=re.M)[1:], 1):
        b_q = re.split(r"^---\s*$", b, maxsplit=1, flags=re.M)[0]
        if CITA_FIGURA_RE.search(b_q) and "imagens/" not in b_q and "| --- |" not in b_q:
            avisos.append(
                f"questão {i:02d} cita tira/figura/gráfico mas não tem referência "
                "de imagem — confira se a figura foi extraída"
            )

    return erros, avisos


def main():
    ap = argparse.ArgumentParser(description="Valida o padrão das provas do repositório.")
    ap.add_argument("--pasta", required=True, help='Pasta "Provas MD" ou uma pasta de prova')
    args = ap.parse_args()

    alvos = []
    if os.path.isfile(os.path.join(args.pasta, "prova_organizada.md")):
        alvos.append(args.pasta)
    else:
        for nome in sorted(os.listdir(args.pasta)):
            p = os.path.join(args.pasta, nome)
            if os.path.isdir(p) and os.path.isfile(os.path.join(p, "prova_organizada.md")):
                alvos.append(p)

    if not alvos:
        print(f"Nenhuma prova encontrada em: {args.pasta}")
        return 1

    falhou = False
    for pasta in alvos:
        erros, avisos = validar_pasta(pasta)
        nome = os.path.basename(pasta.rstrip("/\\"))
        status = "OK" if not erros else "ERROS"
        print(f"{nome}: {status}")
        for e in erros:
            falhou = True
            print(f"   ✗ {e}")
        for a in avisos:
            print(f"   ⚠ {a}")
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
