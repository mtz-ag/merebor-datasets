# pt-ia — Inteligência Artificial (PT-BR)

Conhecimento de IA em portugues para RAG: fundamentos, historia, aprendizado de
maquina/profundo, redes neurais, LLMs e PLN, visao, etica, pioneiros e ferramentas.

- **Documentos:** 60  ·  **Chunks:** 1045  ·  **~1 MB**
- **Fonte:** Wikipedia PT  ·  **Licenca:** CC BY-SA 3.0 (atribuicao exigida)

## Como expandir (fontes legitimas)

- **arXiv** — artigos cientificos de IA (open-access; cs.AI, cs.LG, cs.CL).
- **Stanford AI Index**, papers e blogs open-source, documentacao tecnica.
- **Governanca** (ja em `pt-ia-governanca`): EBIA, Marco Legal da IA PL 2338, Lei de Goias.

> NAO usar livros protegidos por direito autoral (ex.: PDFs do Scribd) — nao podem
> ser redistribuidos nas almas do Merebor (violacao de direito autoral).

## Formato

```jsonc
// raw/wikipedia.jsonl              — um artigo por linha
{"id":"ia-000","titulo":"Inteligencia artificial","texto":"..."}
// processed/wikipedia.chunks.jsonl — um trecho por linha
{"doc_id":"ia-000","chunk_seq":0,"text":"..."}
```

Coletor: `coleta/coletar_ia.py`.
