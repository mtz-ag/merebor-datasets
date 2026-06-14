# Roadmap — merebor-datasets

## Fase 1 ✅ (Junho 2026)
- [x] **pt-historia** — 21 docs, 176 chunks
  - Wikipedia PT: história Brasil, literatura, linguagem
  - Dados curados: histórias complementares, literatura adicional
  - Status: **publicável** → alma `br-historia-brasil` v1.1

## Fase 2 (Junho-Julho 2026)
- [ ] **pt-noticias** — corpus político 2024-2026
  - G1, Folha, Valor, El País Brasil
  - Estratégia: crawl via search API, JSON parse, chunk por parágrafo
  
- [ ] **pt-legislacao** — consolidação de leis federais
  - Planalto (GET limpo para CT consolidado)
  - ~150 leis estimadas
  - Estratégia: coletar direto do Planalto via GET, parse HTML simples
  - Target: alma `br-legislacao-federal` v1.0 atualizada

## Fase 3 (Julho-Agosto)
- [ ] **pt-corpus** — corpus linguístico NILC (Universidade de São Carlos)
  - Domínio público, 1M+ tokens
  - Uso: linguagem natural, análise sintática

- [ ] **pt-jurisprudencia** — decisões STF e TSE
  - Portal e-SAJ do STF
  - Res. TSE de 2022-2026
  - Target: alma `br-jurisprudencia` (novo)

- [ ] **pt-academia** — papers, artigos, dissertações
  - SciELO
  - Biblioteca Digital de Teses e Dissertações (BDTD)
  - Target: alma `br-academia` (novo)

## Fase 4 (Agosto-Setembro)
- [ ] **pt-redes-sociais** (anônimo) — análise de sentimento, temas
- [ ] **pt-midia-estadual** — notícias de portais estaduais
- [ ] **pt-economia** — dados e notícias econômicos consolidados

---

## Dados de Exemplo

Cada dataset começa com **manifesto.json** e **README.md** no início, ainda que vazio:

```json
{
  "id": "pt-xyz",
  "nome": "Descrição",
  "status": "planejamento",
  "documentos": 0,
  "chunks": 0
}
```

Depois, adicionar os coletores em `coleta/coletar_xyz.py` e rodar pipeline:

```bash
python3 coleta/coletar_xyz.py  # gera raw/*.jsonl
python3 pipeline.py full --dataset datasets/pt-xyz  # gera processed/*.chunks.jsonl
```

Atualizar o manifesto com stats reais e commitar.

---

## Critérios de Aceitação

- [x] Pipeline funciona end-to-end
- [x] Dados reais em pt-historia
- [x] Estrutura pronta para expansão (novos datasets como templates)
- [ ] Integração com mtz-ag/merebor releases (publicar almas)
- [ ] Documentação de cada dataset publicada
