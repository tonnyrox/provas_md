# -*- coding: utf-8 -*-
"""Auditor estrutural de TODAS as provas publicadas em `Provas MD/` (v3).

Uso:
    python auditor_estrutural.py                    # audita o acervo inteiro
    python auditor_estrutural.py --prova Camara_X   # audita provas cujo nome contenha o texto
    python auditor_estrutural.py --raiz "C:\\...\\Provas MD" --saida achados.txt

Checagens por prova:
 1. Seções 1–4 presentes no `prova_organizada.md`.
 2. Numeração única 1..N das questões e coerência com a seção 1.
 3. Uma linha de gabarito por questão (✅ resposta / ⚠️ ANULADA / ⚠️ oficial não disponível).
 4. Grupos: `Questões relacionadas` coerente com o cabeçalho (expandindo intervalos
    legítimos do tipo '01 a 10'); cada questão do grupo com material de apoio;
    materiais do grupo ~idênticos (AVISO se similaridade < 0.92).
 5. Imagens: referência dentro do bloco refletida em 'Referências visuais' (e vice-versa).
 6. Marcadores de truncamento conhecidos ('responda as .', 'de N a .').
 7. Vazamento de rótulo de disciplina (MATEMÁTICA, CONHECIMENTOS ESPECÍFICOS, ...)
    dentro da cauda das alternativas — causa típica: offset de extração entre blocos.

Notas de diagnóstico (lições da auditoria completa de 2026):
 - 'Questões relacionadas' pode vir como intervalo ('01 a 10.') ou lista ('01, 02, ... e 10.')
 — ambos são válidos; o intervalo é expandido antes da comparação.
 - Materiais deliberadamente diferentes entre questões do MESMO grupo (ex.: Florânia 2007,
 onde a q4 usa a lista de afirmativas I–IV e não o texto principal) geram AVISO, não ERRO —
 conferir com o PDF original antes de qualquer alteração.

Saída: por prova, lista de (ERRO | AVISO, mensagem). Provas limpas não aparecem.
"""
from __future__ import annotations

import argparse
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

Q_HEAD = re.compile(r"^####\s*QUEST[ÃA]O\s*0*(\d{1,3})", re.M)
GAB_LINHA = re.compile(r"^(?:✅|⚠️)\s*\*\*Gabarito:", re.M)
GRUPO_H = re.compile(r"^###\s*GRUPO\s*(\d+)\s*[—–-]\s*(.+)$", re.M)
REL_Q = re.compile(r"\*\*Quest[õo]es relacionadas:\*\*([^\n]*)")
TRUNC_PATTERNS = [
    (re.compile(r"responda[s]?\s+(?:as|às)\s*\.\s*$", re.M), "truncamento 'responda as .'"),
    (re.compile(r"quest[õo]es\s+de\s+\d{1,3}\s+a\s+\.\s*$", re.M), "truncamento 'de N a .'"),
]
VAZ_RE = re.compile(r"NOÇÕES DE INFORM|CONHECIMENTOS ESPEC[ÍI]FICOS|L[ÍI]NGUA PORTUGUESA|MATEM[ÁA]TICA")


def normaliza(s: str) -> str:
    return re.sub(r"[\s\-–—]+", " ", s).strip().lower()


def bloco_questao(txt: str, m: re.Match) -> str:
    proximo = re.search(r"^(?:####|## |###\s*(?:Transcri[çc][ãa]o|Gabarito|GRUPO\b))", txt[m.end():], re.M)
    fim = m.end() + proximo.start() if proximo else len(txt)
    return txt[m.end():fim]


def material_do(bloco: str) -> str:
    m = re.search(r"\*\*\s*(?:Material de apoio|Texto-base)", bloco, re.I)
    if not m:
        return ""
    fim_label = bloco.find("**", m.end())
    if fim_label < 0:
        return ""
    nl = bloco.find("\n", fim_label + 2)
    if nl < 0:
        return ""
    rest = bloco[nl + 1:]
    paras = re.search(r"\n\*\*(?:Enunciado|Refer|Gabarito|Material|Texto-base)", rest)
    sep = re.search(r"^---\s*$", rest, re.M)
    cortes = [x.start() for x in (paras, sep) if x]
    corte = min(cortes) if cortes else len(rest)
    return normaliza(rest[:corte])


def auditar(pasta: Path) -> list[tuple[str, str]]:
    achados: list[tuple[str, str]] = []
    md_path = pasta / "prova_organizada.md"
    if not md_path.exists():
        return [("ERRO", "prova_organizada.md ausente")]
    txt = md_path.read_text(encoding="utf-8")

    for marc, nome in [("## 1.", "secao 1 (analise geral)"),
                       ("## 2.", "secao 2 (agrupadas)"),
                       ("## 3.", "secao 3 (independentes)"),
                       ("## 4.", "secao 4 (observacoes)")]:
        if marc not in txt:
            achados.append(("ERRO", f"falta {nome}"))

    iter_all = list(Q_HEAD.finditer(txt))
    blocos: dict[int, str] = {}
    duplicados: set[int] = set()
    for m in iter_all:
        qn = int(m.group(1))
        if qn in blocos:
            duplicados.add(qn)
        blocos[qn] = bloco_questao(txt, m)
    n_q = len(blocos)

    esperado_m = re.search(r"\*\*Quantidade total de quest[õo]es:\*\*\s*(\d+)", txt)
    if esperado_m and int(esperado_m.group(1)) != n_q:
        achados.append(("ERRO", f"secao 1 diz {esperado_m.group(1)} questoes, mas ha {n_q} numeros distintos"))
    if sorted(blocos) != list(range(1, n_q + 1)):
        achados.append(("ERRO", f"numeracao nao e 1..{n_q} completa: {sorted(blocos)[:12]}..."))
    if duplicados:
        achados.append(("ERRO", f"questoes com bloco repetido: {sorted(duplicados)}"))

    sem_gab = []
    for qn, bloco in blocos.items():
        if not GAB_LINHA.search(bloco) and not re.search(r"Gabarito oficial:\s*n(?:ã|a)o dispon[íi]vel", bloco):
            sem_gab.append(qn)
    if sem_gab:
        achados.append(("ERRO", f"questoes sem linha de gabarito: {sem_gab[:20]}"))

    for gm in GRUPO_H.finditer(txt):
        gnum, gdesc = gm.group(1), gm.group(2)
        contexto = txt[gm.end():gm.end() + 600]
        rel = REL_Q.search(contexto)
        faixa_m = re.search(r"quest[õo]es\s+0*(\d{1,3})\s+a\s+0*(\d{1,3})", gdesc)
        if rel:
            crud = rel.group(1)
            faixa_rel = re.search(r"0*(\d{1,3})\s*a\s*0*(\d{1,3})", crud)
            if faixa_rel and re.fullmatch(r"[^,\n]*0*\d{1,3}\s*a\s*0*\d{1,3}[^,\n]*", crud.strip()):
                rel_nums = list(range(int(faixa_rel.group(1)), int(faixa_rel.group(2)) + 1))
            else:
                rel_nums = [int(x) for x in re.findall(r"\d+", crud)]
        elif faixa_m:
            rel_nums = list(range(int(faixa_m.group(1)), int(faixa_m.group(2)) + 1))
        else:
            achados.append(("ERRO", f"grupo {gnum} sem 'Questoes relacionadas' nem faixa no cabecalho"))
            continue
        if faixa_m:
            a, b = int(faixa_m.group(1)), int(faixa_m.group(2))
            if sorted(set(rel_nums)) != list(range(a, b + 1)):
                achados.append(("ERRO", f"grupo {gnum}: cabecalho diz {a} a {b}, relacionadas = {sorted(set(rel_nums))}"))
        sem_mat = [qn for qn in rel_nums if len(material_do(blocos.get(qn, ""))) < 40]
        if sem_mat:
            achados.append(("ERRO", f"grupo {gnum}: questoes {sem_mat} sem material de apoio no bloco"))
        mats = {qn: material_do(blocos[qn]) for qn in rel_nums if qn in blocos and material_do(blocos[qn])}
        ids = sorted(mats)
        for i in range(1, len(ids)):
            r = SequenceMatcher(None, mats[ids[i - 1]][:400], mats[ids[i]][:400]).ratio()
            if r < 0.92:
                achados.append(("AVISO", f"grupo {gnum}: material da questao {ids[i]} difere da {ids[i-1]} (similaridade {r:.2f})"))
                break

    for qn, bloco in blocos.items():
        refs_no_bloco = set(re.findall(r"!\[[^\]]*\]\((imagens/[^)]+)\)", bloco))
        ref_m = re.search(r"\*\*Refer[êe]ncias visuais:\*\*(.*?)(?=\n---|\n####|\Z)", bloco, re.S)
        if not refs_no_bloco:
            continue
        if ref_m and re.match(r"^\s*Nenhuma\.?\s*$", ref_m.group(1).strip()):
            achados.append(("ERRO", f"q{qn:02d}: referencia imagem {sorted(refs_no_bloco)} mas Referencias visuais diz 'Nenhuma.'"))
        elif ref_m:
            listadas = set(re.findall(r"imagens/[\w.\-]+", ref_m.group(1)))
            faltam = refs_no_bloco - listadas
            if faltam:
                achados.append(("AVISO", f"q{qn:02d}: imagem(s) {sorted(faltam)} nao listada(s) em Referencias visuais"))

    for rx, msg in TRUNC_PATTERNS:
        if rx.search(txt):
            achados.append(("AVISO", msg))

    for qn, bloco in blocos.items():
        ma = bloco.find("**Alternativas:**")
        if ma < 0:
            continue
        cauda = bloco[ma:]
        for linha in cauda.split("\n"):
            s = linha.strip()
            if not s or s.startswith((">", "|", "#", "-", "####")):
                continue
            m0 = VAZ_RE.search(s)
            if m0:
                achados.append(("ERRO", f"q{qn:02d}: vazamento de disciplina na cauda das alternativas: {s[:90]}"))
    return achados


def main() -> int:
    ap = argparse.ArgumentParser(description="Auditor estrutural do acervo Provas MD")
    ap.add_argument("--raiz", default=str(Path(__file__).resolve().parent.parent / "Provas MD"),
                    help="pasta com as pastas das provas (padrao: ../Provas MD)")
    ap.add_argument("--prova", action="append", default=[],
                    help="filtra por substring do nome da pasta (repetivel)")
    ap.add_argument("--saida", default="", help="grava o relatorio completo neste arquivo")
    args = ap.parse_args()

    raiz = Path(args.raiz)
    problemas = 0
    total = 0
    saida = []
    for pasta in sorted(raiz.iterdir()):
        if not pasta.is_dir():
            continue
        if args.prova and not any(f in pasta.name for f in args.prova):
            continue
        total += 1
        achados = auditar(pasta)
        if achados:
            problemas += 1
            saida.append(f"== {pasta.name}")
            for sev, msg in achados:
                saida.append(f"   [{sev}] {msg}")
    resumo = f"provas auditadas: {total}; com achados: {problemas}"
    saida.append(resumo)
    rel = "\n".join(saida)
    if args.saida:
        Path(args.saida).write_text(rel, encoding="utf-8")
    print(rel)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
