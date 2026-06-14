#!/usr/bin/env python3
"""Coleta leis federais do Planalto (textos públicos)."""

import json
import re
import urllib.request
from urllib.parse import quote

LEIS = {
    "Constituição Federal 1988": "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm",
    "Código Civil": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm",
    "Código Penal": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm",
}

print("📜 Coletando legislação PT...")
dados = []

for nome, url in LEIS.items():
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MereborBot"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode('utf-8', errors='ignore')
        
        # Limpar HTML básico
        texto = re.sub(r'<[^>]+>', ' ', html)
        texto = re.sub(r'[ \t]+', ' ', texto)
        
        if len(texto) > 1000:
            dados.append({
                'id': f"lei-{len(dados)+1:03d}",
                'titulo': nome,
                'texto': texto[:8000],  # primeiros 8k chars
                'fonte': "Planalto.gov.br",
                'tipo': 'legislacao'
            })
            print(f"  ✅ {nome}")
    except Exception as e:
        print(f"  ⚠️  {nome}: {e}")

out = "datasets/pt-legislacao/raw/planalto.jsonl"
with open(out, 'w', encoding='utf-8') as f:
    for d in dados:
        f.write(json.dumps(d, ensure_ascii=False) + '\n')

print(f"✅ {len(dados)} leis em {out}")
