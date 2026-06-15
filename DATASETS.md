# Catálogo de Datasets — Merebor

## posts-instagram
**Status:** ✅ Pronto  
**Tamanho:** 56.8k posts, 236 MB (alma)  
**Cobertura:** RS+SP, 840 veículos, 2026  
**Tipo:** Monitoramento de imprensa  
**Acesso:** Proprietário (mobiliza.me)  
**Frequência:** Mensal  

```bash
# JSONL pré-chunkado (1 post = 1 trecho)
posts-instagram/posts-instagram.jsonl.gz

# Metadados
posts-instagram/manifest.json
posts-instagram/README.md
```

## pt-legislacao
**Status:** ✅ Pronto
**Tamanho:** 230 documentos, 15.498 chunks (~20 MB)
**Cobertura:** federal geral (160), direito militar (32), direito eleitoral/Eleições 2026 (23), essencial CF/Civil/CDC/CLT (5), licitações (5), RS (5)
**Tipo:** Legislação consolidada (Planalto + TSE)
**Acesso:** Domínio público (Lei 9.610/1998, art. 8º)
**Frequência:** sob demanda (Planalto compilado)

```bash
datasets/pt-legislacao/raw/<colecao>.jsonl              # 1 norma/linha
datasets/pt-legislacao/processed/<colecao>.chunks.jsonl # 1 trecho/linha
datasets/pt-legislacao/manifesto.json
```
Coletor: `coleta/coletar_planalto.py`

### legislacao — próximas fontes (planejamento)
- **LexML** — descoberta automatizada de toda a legislação (ver `PLANO-LEIS` no repo merebor)
- **Dados Abertos Câmara/Senado** — votações, projetos de lei
- **STF/STJ** — jurisprudência (quando APIs forem públicas)

## politica (em planejamento)
- **Serenata de Amor** — gastos públicos de parlamentares
- **Eleições TSE** — dados eleitorais (já em merebor)

## linguagem (em planejamento)
- **NILC Corpus** — corpus PT-BR (Universidade de São Carlos)
- **Corpus do Português** — textos históricos e modernos

---

**Meta:** Treinar almas (RAG) do Merebor com dados de qualidade, públicos e proprietários.
