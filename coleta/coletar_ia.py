#!/usr/bin/env python3
"""Coleta artigos de INTELIGENCIA ARTIFICIAL da Wikipedia PT (CC BY-SA 3.0) e gera
o dataset pt-ia (raw/*.jsonl + processed/*.chunks.jsonl).

Fonte 100% legitima: Wikipedia PT (CC BY-SA, atribuicao no manifesto). Expansao
aberta: arXiv (papers open-access), Stanford AI Index, documentacao open-source,
EBIA/PL 2338 (ja em pt-ia-governanca). NUNCA livros protegidos (Scribd etc.) —
nao podem ser redistribuidos nas almas.

Uso:  python3 coleta/coletar_ia.py
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
    # fundamentos e historia
    "Inteligência artificial", "História da inteligência artificial",
    "Teste de Turing", "Inteligência artificial geral", "Filosofia da inteligência artificial",
    "Singularidade tecnológica", "Inverno da inteligência artificial",
    # aprendizado de maquina
    "Aprendizado de máquina", "Aprendizado profundo", "Aprendizado supervisionado",
    "Aprendizado não supervisionado", "Aprendizado por reforço",
    "Aprendizagem por reforço profunda", "Aprendizado semissupervisionado",
    "Aprendizado de máquina automático", "Aprendizado por transferência",
    "Sobreajuste", "Validação cruzada", "Regularização (matemática)",
    # redes neurais e arquiteturas
    "Rede neural artificial", "Perceptron", "Perceptron multicamadas",
    "Rede neural convolucional", "Rede neural recorrente", "Memória de longo prazo",
    "Transformador (aprendizado de máquina)", "Mecanismo de atenção",
    "Retropropagação", "Gradiente descendente", "Função de ativação",
    "Rede generativa adversarial", "Autocodificador", "Modelo de difusão",
    # llms e nlp
    "Grande modelo de linguagem", "Processamento de linguagem natural",
    "Modelo de linguagem", "GPT-3", "GPT-4", "ChatGPT", "BERT (modelo de linguagem)",
    "Word embedding", "Tokenização", "Geração de texto",
    # visao, fala, dados
    "Visão computacional", "Reconhecimento facial", "Reconhecimento de fala",
    "Reconhecimento óptico de caracteres", "Mineração de dados", "Ciência de dados",
    "Big data", "Conjunto de dados",
    # tecnicas classicas
    "Sistema especialista", "Lógica difusa", "Algoritmo genético",
    "Árvore de decisão", "Máquina de vetores de suporte", "Agrupamento (computação)",
    "Algoritmo de busca", "Agente inteligente",
    # aplicacoes
    "Veículo autônomo", "AlphaGo", "Deep Blue", "Robótica", "Internet das coisas",
    "Carro autônomo", "Sistema de recomendação",
    # etica e sociedade
    "Ética da inteligência artificial", "Viés algorítmico", "Explicabilidade",
    "Alucinação (inteligência artificial)", "Alinhamento de inteligência artificial",
    # pioneiros
    "Alan Turing", "John McCarthy (cientista da computação)", "Marvin Minsky",
    "Geoffrey Hinton", "Yann LeCun", "Yoshua Bengio", "Andrew Ng",
    # ferramentas
    "TensorFlow", "PyTorch", "Tensor",
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
                if len(txt) > 500:
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
    out = Path(__file__).resolve().parent.parent / "datasets" / "pt-ia"
    (out / "raw").mkdir(parents=True, exist_ok=True)
    (out / "processed").mkdir(parents=True, exist_ok=True)
    docs, nc, nb = [], 0, 0
    with open(out / "processed" / "wikipedia.chunks.jsonl", "w", encoding="utf-8") as fc:
        for tema in TEMAS:
            art = wiki_api(tema)
            time.sleep(1.0)
            if not art:
                continue
            did = f"ia-{len(docs):03d}"
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
    Path("/tmp/ia_totais.json").write_text(json.dumps({"docs": len(docs), "chunks": nc, "bytes": nb}))


if __name__ == "__main__":
    main()
