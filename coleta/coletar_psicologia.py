#!/usr/bin/env python3
"""Coleta artigos de PSICOLOGIA da Wikipedia PT (CC BY-SA 3.0) e gera o dataset
pt-psicologia (raw/*.jsonl + processed/*.chunks.jsonl).

Fonte 100% legitima: Wikipedia PT (CC BY-SA, atribuicao no manifesto). Para
expandir depois com fontes abertas: SciELO/PePSIC (periodicos CC), Codigo de
Etica do CFP (oficial) e classicos em DOMINIO PUBLICO (Freud — falecido 1939,
ja e DP no Brasil; William James; Wundt). NUNCA livros protegidos (Scribd etc.).

Uso:  python3 coleta/coletar_psicologia.py
"""
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

CHUNK_CHARS, OVERLAP = 1800, 200

# ~70 temas curados: escolas, autores, conceitos, transtornos, terapias, aplicada
TEMAS = [
    # escolas e abordagens
    "Psicologia", "Psicanálise", "Behaviorismo", "Psicologia cognitiva",
    "Psicologia humanista", "Psicologia analítica", "Terapia cognitivo-comportamental",
    "Psicologia positiva", "Psicologia social", "Neuropsicologia",
    "Psicologia do desenvolvimento", "Gestalt-terapia", "Psicologia experimental",
    "Psicologia evolutiva", "Psicofisiologia", "Psicometria",
    # autores
    "Sigmund Freud", "Carl Gustav Jung", "Jean Piaget", "Lev Vygotsky",
    "Burrhus Frederic Skinner", "Carl Rogers", "Abraham Maslow", "Ivan Pavlov",
    "William James", "Wilhelm Wundt", "Alfred Adler", "Melanie Klein",
    "Erik Erikson", "John Bowlby", "Aaron Beck", "Albert Ellis", "Viktor Frankl",
    "Daniel Kahneman", "Nise da Silveira",
    # conceitos
    "Inconsciente", "Ego", "Id, ego e superego", "Mecanismo de defesa",
    "Condicionamento clássico", "Condicionamento operante", "Reforço",
    "Teoria do apego", "Inteligência", "Quociente de inteligência", "Memória",
    "Aprendizagem", "Motivação", "Emoção", "Percepção", "Cognição",
    "Personalidade", "Hierarquia de necessidades de Maslow", "Dissonância cognitiva",
    "Resiliência (psicologia)", "Empatia", "Autoestima", "Viés cognitivo",
    "Estresse", "Luto",
    # transtornos
    "Transtorno de ansiedade", "Transtorno depressivo maior", "Transtorno bipolar",
    "Esquizofrenia", "Transtorno do espectro autista",
    "Transtorno do déficit de atenção com hiperatividade",
    "Transtorno obsessivo-compulsivo", "Transtorno de estresse pós-traumático",
    "Transtorno da personalidade borderline", "Síndrome do pânico", "Fobia",
    "Transtorno alimentar", "Anorexia nervosa", "Bulimia", "Psicopatia",
    "Transtorno de personalidade",
    # clinica e aplicada
    "Psicoterapia", "Psicofarmacologia", "DSM-5",
    "Classificação Internacional de Doenças", "Psicologia organizacional",
    "Psicologia escolar", "Psicologia jurídica", "Psicologia do esporte",
    "Psicologia da saúde", "Teste psicológico", "Conselho Federal de Psicologia",
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


UA = "MereborDatasets/1.0 (https://github.com/mtz-ag/merebor-datasets; factory@merebor)"


def wiki_api(titulo: str) -> dict | None:
    base = "https://pt.wikipedia.org/w/api.php"
    url = (f"{base}?action=query&titles={quote(titulo)}&prop=extracts"
           "&explaintext=1&redirects=1&format=json")
    for tentativa in range(4):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            for _, page in data["query"]["pages"].items():
                txt = page.get("extract", "")
                if len(txt) > 500:
                    return {"titulo": page.get("title", titulo), "texto": txt}
            return None
        except urllib.error.HTTPError as exc:
            if exc.code == 429:  # rate limit — recua e tenta de novo
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
    out = Path(__file__).resolve().parent.parent / "datasets" / "pt-psicologia"
    (out / "raw").mkdir(parents=True, exist_ok=True)
    (out / "processed").mkdir(parents=True, exist_ok=True)
    docs, nc, nb = [], 0, 0
    with open(out / "processed" / "wikipedia.chunks.jsonl", "w", encoding="utf-8") as fc:
        for tema in TEMAS:
            art = wiki_api(tema)
            time.sleep(1.0)
            if not art:
                continue
            did = f"psi-{len(docs):03d}"
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
    Path("/tmp/psi_totais.json").write_text(json.dumps({"docs": len(docs), "chunks": nc, "bytes": nb}))


if __name__ == "__main__":
    main()
