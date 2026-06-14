# pt-historia: História do Brasil

Conhecimento de história do Brasil para almas Merebor.

## Fontes planejadas

- Wikipedia PT (história)
- Wikisource PT (obras históricas)
- Câmara/Senado (dados legislativos históricos)

## Como usar

```bash
# 1. Colocar dados em raw/
mkdir -p datasets/pt-historia/{raw,processed,metadata}
cp seus-dados.jsonl datasets/pt-historia/raw/

# 2. Rodar pipeline
python3 pipeline.py full --dataset datasets/pt-historia

# 3. Commit
git add datasets/pt-historia/
git commit -m "feat: pt-historia - historia do brasil"
git push origin main
```

## Campos esperados (raw)

```json
{
  "id": "wiki-001",
  "titulo": "Independência do Brasil",
  "texto": "Em 1822...",
  "fonte": "Wikipedia PT",
  "tipo": "história"
}
```

---

Após pipeline, chunks são salvos em `processed/chunks.jsonl` (1.8k chars, overlap 200).
