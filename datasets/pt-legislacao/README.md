# pt-legislacao — Legislação Brasileira

Leis, códigos, estatutos, decretos e resoluções **federais consolidados**, coletados
do [Planalto](https://www.planalto.gov.br/ccivil_03/) e do **TSE**, estruturados por
artigo (cabeçalho de citação por artigo) e chunkados (1800/200) para RAG.

- **Documentos:** 230  ·  **Chunks:** 15498  ·  **~19 MB**
- **Licença:** domínio público (textos legais — Lei 9.610/1998, art. 8º)

## Coleções (`raw/` = 1 doc/linha · `processed/` = 1 chunk/linha)

| Arquivo | Conteúdo |
|---|---|
| `federal` | 160 normas federais — códigos, estatutos, leis ordinárias e complementares |
| `militar` | 32 — direito militar (CPM, CPPM, Estatuto dos Militares, Justiça Militar, disciplinares) |
| `eleitoral` | 23 — leis eleitorais + 14 resoluções do TSE para as **Eleições 2026** |
| `essencial` | 5 — CF/88, Código Civil, CDC, CLT |
| `licitacoes` | 5 — Nova Lei de Licitações (14.133) e correlatos |
| `rs` | 5 — legislação estadual do Rio Grande do Sul |

## Formato

```jsonc
// raw/<colecao>.jsonl     — uma norma por linha
{"id":"lei-federal-000","titulo":"Codigo Civil (Lei 10.406-2002)","texto":"..."}
// processed/<colecao>.chunks.jsonl  — um trecho por linha
{"doc_id":"lei-federal-000","chunk_seq":0,"text":"Código Civil · Art. 1º · ..."}
```

Coletor: [`coleta/coletar_planalto.py`](../../coleta/coletar_planalto.py).
