#!/usr/bin/env python3
"""Coleta artigos da Wikipedia PT — história, literatura, linguagem."""

import json
import re
import time
import urllib.request
from urllib.parse import quote

def wiki_api(titles: list[str], lang: str = "pt") -> list[dict]:
    """Busca artigos da Wikipedia via API."""
    results = []
    base = f"https://{lang}.wikipedia.org/w/api.php"
    
    for title in titles:
        try:
            url = f"{base}?action=query&titles={quote(title)}&prop=extracts&explaintext=1&format=json"
            req = urllib.request.Request(url, headers={"User-Agent": "MereborBot/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            
            for pid, page in data['query']['pages'].items():
                if 'extract' in page and len(page['extract']) > 500:
                    results.append({
                        'id': f"wiki-pt-{len(results)+1:04d}",
                        'titulo': page.get('title', title),
                        'texto': page['extract'],
                        'fonte': f"Wikipedia PT ({title})",
                        'tipo': 'história'
                    })
            time.sleep(0.3)
        except Exception as e:
            print(f"⚠️  {title}: {e}")
    
    return results

# Temas a coletar
HISTORIA = [
    "Independência do Brasil",
    "Proclamação da República",
    "Império Brasileiro",
    "Era Vargas",
    "Ditadura Militar Brasileira",
    "Inconfidência Mineira",
    "Abolição da Escravidão no Brasil",
    "Coronelismo",
    "Getúlio Vargas",
    "Dom Pedro I",
    "Tiradentes",
    "Diretas Já",
    "Constituição Brasileira de 1988",
]

LITERATURA = [
    "Machado de Assis",
    "Aluísio Azevedo",
    "José de Alencar",
    "Clarice Lispector",
    "Carlos Drummond de Andrade",
    "Fernando Pessoa",
    "Jorge Amado",
    "Literatura Brasileira",
    "Modernismo no Brasil",
    "Romantismo Brasileiro",
]

LINGUAGEM = [
    "Língua Portuguesa",
    "Português Brasileiro",
    "Gramática Portuguesa",
    "Sintaxe",
    "Morfologia (Linguística)",
    "Semântica",
]

print("📚 Coletando Wikipedia PT...")
dados = []
dados.extend(wiki_api(HISTORIA[:5]))  # 5 história
print(f"  ✅ {len(dados)} artigos coletados")
dados.extend(wiki_api(LITERATURA[:5]))
print(f"  ✅ {len(dados)} artigos coletados")
dados.extend(wiki_api(LINGUAGEM[:3]))
print(f"  ✅ {len(dados)} artigos coletados")

# Salvar
out = "datasets/pt-historia/raw/wikipedia.jsonl"
with open(out, 'w', encoding='utf-8') as f:
    for d in dados:
        f.write(json.dumps(d, ensure_ascii=False) + '\n')

print(f"\n✅ {len(dados)} artigos salvos em {out}")
