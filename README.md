# Merebor Datasets

Repositório de datasets em **português** para treinar almas (RAG) do Merebor.

## Estrutura

```
merebor-datasets/
├── datasets/
│   ├── posts-instagram/        (56.8k RS+SP)
│   ├── pt-historia/            (planejado)
│   ├── pt-literatura/          (planejado)
│   └── ...
├── coleta/                      (scripts de coleta)
│   └── coletar_<tema>.py
├── pipeline.py                  (orquestra tudo)
├── CONTRIBUINDO.md              (como adicionar datasets)
└── DATASETS.md                  (catálogo)
```

## Rápido Start

### 1. Adicionar um novo dataset

```bash
# Exemplo: História do Brasil via Wikipedia

# 1.1 Criar estrutura
mkdir -p datasets/pt-historia/{raw,processed,metadata}

# 1.2 Coletar (você faz — copie dados pra raw/)
# Exemplo: raw/wikipedia.jsonl com {"id": "...", "texto": "...", "fonte": "..."}

# 1.3 Processar (pipeline automático)
python3 pipeline.py full --dataset datasets/pt-historia

# 1.4 Salvar
git add datasets/pt-historia/
git commit -m "feat(datasets): pt-historia - história do brasil via wikipedia"
git push origin main
```

### 2. Coloca embeddings (futuro: em cluster)

```bash
# Quando tiver bge-m3 disponível:
python3 pipeline.py embed \
  --input datasets/pt-historia/processed/chunks.jsonl \
  --output datasets/pt-historia/processed/embeddings.f32
```

## Datasets candidatos (PT)

- **pt-historia** — História do Brasil (Wikipedia)
- **pt-literatura** — Clássicos brasileiros (Wikisource)
- **pt-wikipedia** — Cobertura geral PT
- **pt-noticias** — Corpus de notícias (G1, Folha)
- **pt-legislacao** — Leis federais (Planalto)
- **pt-corpus** — NILC corpus (linguagem)
- **posts-instagram** — Monitoramento de imprensa ✅ (em produção)

## Formato esperado (raw)

```json
{"id": "wiki-001", "titulo": "Independencia do Brasil", "texto": "...", "fonte": "Wikipedia PT"}
{"id": "wiki-002", "titulo": "Proclamacao da Republica", "texto": "...", "fonte": "Wikipedia PT"}
```

## Checklist pra dataset pronto

- [ ] Dados brutos em `datasets/<id>/raw/`
- [ ] Pipeline rodou: `python3 pipeline.py full --dataset datasets/<id>/`
- [ ] `manifesto.json` preenchido (nome, versão, source, idioma, temas)
- [ ] `README.md` explicando o dataset
- [ ] `schema.json` com campo schema
- [ ] Commit e push

## Suporte

Dúvidas? Leia `CONTRIBUINDO.md` ou abra uma issue.

---

**Meta:** Conhecimento em português, versionado e reproduzível.
