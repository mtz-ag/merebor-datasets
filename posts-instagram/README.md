# Posts de Instagram — Imprensa Brasileira

**56.8 mil posts** de 840 veículos de imprensa (RS+SP, 2026)

## Estrutura

- `posts-instagram.jsonl.gz` — Comprimido (JSONL, 1 post por linha)
- `manifest.json` — Metadados (veículos, datas, sentimento)
- `schema.json` — Definição de campos

## Campos

```json
{
  "doc": "CORREIO DO POVO",
  "text": "CORREIO DO POVO · Porto Alegre/RS · 2026-05-23\nA Polícia Civil..."
}
```

- **doc**: Nome do veículo (fonte citável)
- **text**: Cabeçalho (veículo·cidade·data) + legenda

## Processamento

- Filtrado: sem link-dump (util_chars < 40)
- Deduplicado: por hash de legenda
- Estados: RS (44k) + SP (27k) → 56.8k total

## Licença

Proprietário — mobiliza.me. Não redistribuir publicamente.

## Uso

```python
import json, gzip
with gzip.open('posts-instagram.jsonl.gz') as f:
    for line in f:
        post = json.loads(line)
        print(post['doc'], post['text'][:80])
```
