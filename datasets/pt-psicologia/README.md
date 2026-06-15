# pt-psicologia — Psicologia (PT-BR)

Conhecimento de psicologia em portugues para RAG: escolas e abordagens, autores,
conceitos, transtornos, terapias e psicologia aplicada.

- **Documentos:** 85  ·  **Chunks:** 1281  ·  **~1 MB**
- **Fonte:** Wikipedia PT  ·  **Licenca:** CC BY-SA 3.0 (atribuicao exigida)

## Cobertura

Escolas (psicanalise, behaviorismo, cognitiva, humanista, analitica, TCC, gestalt,
positiva, social, neuropsicologia, desenvolvimento) · autores (Freud, Jung, Piaget,
Vygotsky, Skinner, Rogers, Maslow, Pavlov, James, Wundt, Adler, Klein, Erikson,
Bowlby, Beck, Ellis, Frankl, Kahneman, Nise da Silveira) · conceitos (inconsciente,
ego/id/superego, condicionamento, apego, inteligencia, memoria, emocao, personalidade,
vieses) · transtornos (ansiedade, depressao, bipolar, esquizofrenia, autismo, TDAH,
TOC, TEPT, borderline, panico, alimentares) · clinica e aplicada (psicoterapia,
psicofarmacologia, DSM-5, CID, organizacional, escolar, juridica, esporte, saude, CFP).

## Como expandir (fontes legitimas)

- **SciELO / PePSIC** — periodicos de psicologia brasileiros (acesso aberto, CC).
- **CFP** — Codigo de Etica do Psicologo e resolucoes (documentos oficiais).
- **Dominio publico** — classicos cujo autor faleceu ha +70 anos (Freud 1939 ja e DP
  no Brasil; William James; Wundt). Fontes: Dominio Publico (MEC), Wikisource.

> NAO usar livros protegidos por direito autoral (ex.: PDFs do Scribd) — violacao
> de direito autoral e dos Termos de Uso; o conteudo nao pode ser redistribuido nas
> almas do Merebor.

## Formato

```jsonc
// raw/wikipedia.jsonl              — um artigo por linha
{"id":"psi-000","titulo":"Psicanalise","texto":"..."}
// processed/wikipedia.chunks.jsonl — um trecho por linha
{"doc_id":"psi-000","chunk_seq":0,"text":"..."}
```

Coletor: `coleta/coletar_psicologia.py`.
