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
     discursivas têm bloco próprio com "não se aplica").
  6. Imagens: toda referência ![...](imagens/...) deve apontar para arquivo existente.

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
GAB_RE = re.compile(r"^(?:✅|⚠️) \*\*Gabarito:", re.M)
IMG_RE = re.compile(r"!\[[^\]]*\]\((imagens/[^)]+)\)")


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
