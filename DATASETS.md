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

## pt-psicologia
**Status:** ✅ Pronto
**Tamanho:** 85 documentos, 1.281 chunks (~2 MB)
**Cobertura:** escolas, autores, conceitos, transtornos, terapias e psicologia aplicada
**Tipo:** Conhecimento de psicologia (Wikipedia PT)
**Acesso:** CC BY-SA 3.0 (atribuição exigida)

```bash
datasets/pt-psicologia/raw/wikipedia.jsonl
datasets/pt-psicologia/processed/wikipedia.chunks.jsonl
```
Coletor: `coleta/coletar_psicologia.py` · Expansão: SciELO/PePSIC, CFP, clássicos em domínio público

## pt-historia
**Status:** ✅ Pronto
**Tamanho:** 123 documentos, 6.217 chunks (~8 MB)
**Cobertura:** história do Brasil, literatura clássica, gramática/linguística PT
**Tipo:** Cultura geral (Wikipedia PT)
**Acesso:** CC BY-SA 3.0 (atribuição exigida)

```bash
datasets/pt-historia/raw/historia-brasil.jsonl
datasets/pt-historia/processed/historia-brasil.chunks.jsonl
```

## pt-ia-governanca
**Status:** ✅ Pronto
**Tamanho:** 3 documentos, 188 chunks (~0,3 MB)
**Cobertura:** EBIA (MCTI), Marco Legal da IA (PL 2338/2023), Lei de IA de Goiás (LC 205/2025)
**Tipo:** Política e regulação de IA
**Acesso:** Documentos oficiais (domínio público)

```bash
datasets/pt-ia-governanca/raw/ia-governanca.jsonl
datasets/pt-ia-governanca/processed/ia-governanca.chunks.jsonl
```

## politica (em planejamento)
- **Serenata de Amor** — gastos públicos de parlamentares
- **Eleições TSE** — dados eleitorais (já em merebor)

## linguagem (em planejamento)
- **NILC Corpus** — corpus PT-BR (Universidade de São Carlos)
- **Corpus do Português** — textos históricos e modernos

---

**Meta:** Treinar almas (RAG) do Merebor com dados de qualidade, públicos e proprietários.
