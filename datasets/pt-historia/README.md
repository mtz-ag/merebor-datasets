# pt-historia — História, Literatura e Linguagem (PT-BR)

Artigos da **Wikipedia PT** sobre história do Brasil, literatura clássica e
gramática/linguística portuguesa. Base de cultura geral em português para RAG.

- **Documentos:** 123  ·  **Chunks:** 6.217  ·  **~8 MB**
- **Fonte:** Wikipedia PT  ·  **Licença:** CC BY-SA 3.0 (atribuição exigida)

## Formato

```jsonc
// raw/historia-brasil.jsonl              — um artigo por linha
{"id":"hist-000","titulo":"Abolição da escravidão no Brasil (Wikipedia)","texto":"..."}
// processed/historia-brasil.chunks.jsonl — um trecho por linha
{"doc_id":"hist-000","chunk_seq":0,"text":"..."}
```

> Versão 2.0.0: substituiu as coleções menores (wikipedia/historia-extra/
> literatura-extra, 21 docs) pelo corpus completo de **123 documentos**.
> Coletor: `coleta/coletar_wikipedia_pt.py`.
