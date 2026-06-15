#!/usr/bin/env python3
"""Coleta artigos sobre FREUD e PSICANALISE da Wikipedia PT (CC BY-SA 3.0) e gera
o dataset freud-br (raw/*.jsonl + processed/*.chunks.jsonl).

NOTA DE DIREITO AUTORAL: a OBRA ORIGINAL de Freud (falecido 1939) e dominio
publico. Mas TRADUCOES tem direito autoral proprio (do tradutor). Para incluir as
PALAVRAS de Freud em PT, usar so traducoes realmente em DP (tradutor +70 anos) ou
traduzir os originais alemao/ingles DP. NUNCA edicoes protegidas (Imago,
Companhia das Letras, Biblioteca Nueva/Numhauser) nem ePubs piratas (Scribd).
Esta base usa Wikipedia PT (conhecimento SOBRE Freud e a psicanalise).

Uso:  python3 coleta/coletar_freud.py
"""
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

CHUNK_CHARS, OVERLAP = 1800, 200
UA = "MereborDatasets/1.0 (https://github.com/mtz-ag/merebor-datasets; factory@merebor)"

TEMAS = [
    # vida e obra
    "Sigmund Freud", "Psicanálise", "História da psicanálise", "Anna Freud",
    # obras principais (artigos da Wikipedia)
    "A Interpretação dos Sonhos", "Três Ensaios sobre a Teoria da Sexualidade",
    "Totem e Tabu", "O Mal-Estar na Civilização", "Psicopatologia da Vida Cotidiana",
    "Além do Princípio do Prazer", "O Ego e o Id", "O Futuro de uma Ilusão",
    "Cinco Lições de Psicanálise", "Os Chistes e Sua Relação com o Inconsciente",
    "Luto e Melancolia", "Moisés e o Monoteísmo", "O Eu e o Isso",
    # conceitos centrais
    "Inconsciente", "Id, ego e superego", "Complexo de Édipo", "Complexo de Electra",
    "Pulsão", "Libido", "Recalque", "Mecanismo de defesa", "Transferência (psicanálise)",
    "Sonho", "Associação livre", "Ato falho", "Narcisismo", "Pulsão de morte",
    "Princípio do prazer", "Princípio de realidade", "Sublimação (psicologia)",
    "Desenvolvimento psicossexual", "Angústia", "Histeria", "Neurose", "Trauma psíquico",
    "Interpretação", "Catarse", "Censura (psicanálise)", "Fixação (psicologia)",
    "Regressão (psicologia)", "Projeção (psicologia)", "Repressão (psicologia)",
    # discipulos, dissidentes e escolas
    "Carl Gustav Jung", "Jacques Lacan", "Melanie Klein", "Sándor Ferenczi",
    "Wilhelm Reich", "Donald Winnicott", "Alfred Adler", "Karen Horney",
    "Psicanálise lacaniana", "Psicologia analítica", "Psicologia do ego",
    "Relações objetais",
]


def chunk_text(text: str) -> list[str]:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, atual = [], ""
    for p in paras:
        if len(atual) + len(p) + 2 <= CHUNK_CHARS:
            atual = f"{atual}\n\n{p}" if atual else p
            continue
        if atual:
            chunks.append(atual)
            atual = atual[-OVERLAP:] + "\n\n" + p if OVERLAP else p
        while len(atual) > CHUNK_CHARS:
            chunks.append(atual[:CHUNK_CHARS])
            atual = atual[CHUNK_CHARS - OVERLAP:]
    if atual.strip():
        chunks.append(atual)
    return chunks


def wiki_api(titulo: str) -> dict | None:
    base = "https://pt.wikipedia.org/w/api.php"
    url = (f"{base}?action=query&titles={quote(titulo)}&prop=extracts"
           "&explaintext=1&redirects=1&format=json")
    for tentativa in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            for _, page in data["query"]["pages"].items():
                txt = page.get("extract", "")
                if len(txt) > 400:
                    return {"titulo": page.get("title", titulo), "texto": txt}
            return None
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                time.sleep(3 * (tentativa + 1))
                continue
            print(f"  ! {titulo}: {exc}")
            return None
        except Exception as exc:
            print(f"  ! {titulo}: {exc}")
            return None
    print(f"  ! {titulo}: 429 persistente")
    return None


def main():
    out = Path(__file__).resolve().parent.parent / "datasets" / "freud-br"
    (out / "raw").mkdir(parents=True, exist_ok=True)
    (out / "processed").mkdir(parents=True, exist_ok=True)
    docs, nc, nb = [], 0, 0
    with open(out / "processed" / "wikipedia.chunks.jsonl", "w", encoding="utf-8") as fc:
        for tema in TEMAS:
            art = wiki_api(tema)
            time.sleep(1.0)
            if not art:
                continue
            did = f"freud-{len(docs):03d}"
            docs.append({"id": did, "titulo": art["titulo"], "texto": art["texto"]})
            nb += len(art["texto"].encode())
            for j, ch in enumerate(chunk_text(art["texto"])):
                fc.write(json.dumps({"doc_id": did, "chunk_seq": j, "text": ch},
                                    ensure_ascii=False) + "\n")
                nc += 1
            print(f"  ok {art['titulo']}")
    with open(out / "raw" / "wikipedia.jsonl", "w", encoding="utf-8") as fr:
        for d in docs:
            fr.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"\n{len(docs)} artigos, {nc} chunks, {nb // 1024} KB")
    Path("/tmp/freud_totais.json").write_text(json.dumps({"docs": len(docs), "chunks": nc, "bytes": nb}))


if __name__ == "__main__":
    main()
