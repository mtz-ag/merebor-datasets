# Contribuindo Datasets

Guia pra adicionar e treinar novos datasets em português.

## Estrutura de um dataset

```
datasets/
├── <dataset-id>/
│   ├── manifesto.json          # Metadados
│   ├── README.md               # Documentação
│   ├── raw/                    # Dados brutos (coletados)
│   │   └── <fonte>.jsonl       # Ou CSV, TXT, etc.
│   ├── processed/              # Dados processados
│   │   ├── chunks.jsonl        # Trechos (1 por linha)
│   │   └── embeddings.f32      # Vetores (bge-m3, dim 1024)
│   └── metadata/
│       ├── schema.json
│       └── stats.json
```

## Pipeline: Coleta → Chunk → Embed → Salvar

### 1. Coleta (raw)

Script `coleta/coletar_<dataset>.py`:
```python
# Exemplo: Wikipedia PT
# coletar_wikipedia_pt.py --tema historia --out raw/wikipedia.jsonl
```

Formato esperado:
```json
{"id": "wikipedia-historia-001", "titulo": "...", "texto": "...", "fonte": "Wikipedia PT"}
```

### 2. Processamento (chunking)

```bash
python pipeline.py chunk \
  --input raw/wikipedia.jsonl \
  --output processed/chunks.jsonl \
  --chunk-size 1800 \
  --overlap 200
```

Saída:
```json
{"doc_id": "wikipedia-historia-001", "chunk_seq": 0, "text": "...", "tipo": "historia"}
```

### 3. Embedding

```bash
python pipeline.py embed \
  --input processed/chunks.jsonl \
  --output processed/embeddings.f32 \
  --model bge-m3 \
  --batch-size 32
```

Saída: vetores float32 (1024-dim) em ordem de chunks.jsonl

### 4. Metadados

`manifesto.json`:
```json
{
  "id": "pt-historia",
  "nome": "História do Brasil",
  "versao": "2026.06",
  "fonte": "Wikipedia PT",
  "docs": 120,
  "chunks": 3847,
  "embedding_model": "bge-m3",
  "embedding_dim": 1024,
  "tamanho_mb": 15,
  "idioma": "pt",
  "temas": ["historia", "brasil", "politica"],
  "atualizacao": "2026-06-13",
  "licenca": "CC-BY-SA"
}
```

## Exemplo: Adicionar novo dataset

```bash
# 1. Criar pasta
mkdir -p datasets/pt-literatura/{raw,processed,metadata}

# 2. Coletar (você faz)
python coleta/coletar_literatura_pt.py --out datasets/pt-literatura/raw/

# 3. Processar (pipeline automático)
python pipeline.py full \
  --dataset datasets/pt-literatura \
  --chunk-size 1800

# 4. Submeter PR ou fazer push
git add datasets/pt-literatura/
git commit -m "feat(datasets): pt-literatura - autores brasileiros"
git push origin main
```

## Datasets sugeridos (PT)

- **pt-historia** — História do Brasil (Wikipedia)
- **pt-literatura** — Clássicos brasileiros (Wikisource)
- **pt-wikipedia** — Visão geral PT (todos os artigos)
- **pt-noticias** — Corpus de notícias (G1, Folha via APIs)
- **pt-legislacao** — Leis federais em português (Planalto)
- **pt-corpus** — NILC corpus (Universidade de São Carlos)

## Checklist

- [ ] Dados brutos coletados e validados
- [ ] `manifesto.json` preenchido
- [ ] Chunks processados (1.8k chars, overlap 200)
- [ ] Embeddings gerados (bge-m3)
- [ ] `README.md` com descrição
- [ ] `schema.json` com campos
- [ ] `stats.json` com contagem
- [ ] Validação: `python validate.py datasets/<id>/`

## Suporte

Dúvidas? Abra uma issue em github.com/mtz-ag/merebor-datasets

