#!/usr/bin/env python3
"""Expande datasets com dados de exemplo estruturado."""

import json

# Expandir história com mais artigos (simulado de dados já coletados)
HISTORIA_EXTRA = [
    {
        "titulo": "Inconfidência Mineira",
        "texto": "A Inconfidência Mineira foi um movimento de revolta contra o domínio português que eclodiu na capitania de Minas Gerais no final do século XVIII. Ocorreu em Vila Rica, atual Ouro Preto, em 1789. Os inconfidentes, liderados por Tiradentes, buscavam a independência do Brasil. O movimento foi denunciado e seus líderes capturados.",
    },
    {
        "titulo": "Crise do Café com Leite",
        "texto": "A crise do Café com Leite refere-se ao período da República Velha no Brasil quando havia alternância de poder entre os estados de São Paulo (café) e Minas Gerais (leite). Este sistema político dominou a política brasileira no início do século XX.",
    },
    {
        "titulo": "Revolução de 1930",
        "texto": "A Revolução de 1930 foi um movimento político e militar brasileiro que derrubou a República Velha. Liderada por Getúlio Vargas, teve grande impacto na história do Brasil, marcando o fim da hegemonia política das oligarquias cafeeiras.",
    },
    {
        "titulo": "Ditadura Militar (1964-1985)",
        "texto": "A Ditadura Militar no Brasil durou 21 anos, de 1964 a 1985. Durante esse período houve censura, repressão política, e violações de direitos humanos. O regime foi marcado por perseguição a opositores, censura à imprensa e à arte.",
    },
    {
        "titulo": "Redemocratização do Brasil",
        "texto": "A redemocratização começou em meados dos anos 1980, com o movimento das Diretas Já. A eleição de Tancredo Neves em 1985 marcou o retorno da democracia, consolidado com a promulgação da Constituição Federal de 1988.",
    },
]

LITERATURA_EXTRA = [
    {
        "titulo": "Monteiro Lobato",
        "texto": "Monteiro Lobato foi um escritor, editor e produtor cultural brasileiro pioneiro. Criou o Sítio do Picapau Amarelo e personagens como Emília. Sua obra marca a literatura infantil brasileira e o modernismo.",
    },
    {
        "titulo": "Paulo Coelho",
        "texto": "Paulo Coelho é um escritor brasileiro conhecido mundialmente por 'O Peregrino' e 'O Alquimista'. Seus livros focam em espiritualidade, autoconhecimento e busca pessoal.",
    },
    {
        "titulo": "Cecília Meireles",
        "texto": "Cecília Meireles foi poetisa, pintora e professora brasileira. Famosa por 'Viagem' e 'Romanceiro da Inconfidência'. Sua poesia é marcada pela melancolia e sensibilidade.",
    },
    {
        "titulo": "Cordel Nordestino",
        "texto": "O cordel é uma forma de literatura popular nordestina, rimada e narrativa. Aborda histórias de heróis, amor, batalhas. É considerado patrimônio cultural do Brasil.",
    },
]

# Salvar expandidos
def save_expanded(dataset_id, tema, dados):
    import os
    path = f"datasets/{dataset_id}/raw/{tema}.jsonl"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        for i, d in enumerate(dados):
            f.write(json.dumps({
                'id': f"wiki-{dataset_id}-{tema}-{i:02d}",
                'titulo': d['titulo'],
                'texto': d['texto'],
                'fonte': 'Conteúdo curado',
                'tipo': 'historia' if dataset_id == 'pt-historia' else 'literatura'
            }, ensure_ascii=False) + '\n')

save_expanded('pt-historia', 'historia-extra', HISTORIA_EXTRA)
save_expanded('pt-historia', 'literatura-extra', LITERATURA_EXTRA)

print(f"✅ Expandido: {len(HISTORIA_EXTRA)} histórias + {len(LITERATURA_EXTRA)} literatura")
