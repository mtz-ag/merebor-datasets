#!/usr/bin/env python3
"""coletar_planalto — coleta a legislacao federal compilada do Planalto e gera
os corpus .md prontos para o `mrb_alma.py build` (substitui o coletar_cf88).

Ferramenta de FABRICA (roda com internet). A maquina do cliente nunca ve isto.

Chunking juridico: cada artigo vira um ou mais blocos de ate BLOCO_CHARS,
cortados em fronteira de inciso/paragrafo, cada bloco prefixado com cabecalho
de citacao ("Código Civil · Art. 421 · Dos Contratos em Geral"). Blocos sao
separados por linha em branco — a regua generica do mrb_alma (1.800/200)
agrupa blocos vizinhos sem nunca fatiar um artigo no meio.

Uso:
  python3 coletar_planalto.py --out-base ../corpus            # tudo (57 normas)
  python3 coletar_planalto.py --out-base ../corpus --so cf88  # uma norma
  python3 coletar_planalto.py --out-base ../corpus --cache /tmp/planalto-cache

Gera dois corpus, um por pacote:
  ../corpus/br-essencial/           CF/88 + ADCT, Codigo Civil, CDC, CLT
  ../corpus/br-legislacao-federal/  demais codigos, estatutos e leis (sem repetir
                                    o essencial — os pacotes instalam lado a lado)
"""

import argparse
import re
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://www.planalto.gov.br/ccivil_03"

# menor que o CHUNK_CHARS do mrb_alma (1.800) para sobrar espaco pro cabecalho
# e permitir agrupamento de artigos curtos vizinhos
BLOCO_CHARS = 1500

# notas de remissao que so fazem sentido com hiperlink — removidas do corpus.
# Notas de emenda ("Redacao dada...", "Incluido...", "Revogado...") ficam:
# sao curtas e juridicamente relevantes para citacao.
NOTAS_DESCARTAR = re.compile(
    r"\(\s*(Vide[^)]*|Regulamento[^)]*|Produção de efeito[^)]*)\)", re.IGNORECASE
)

# norma: (id, pacote, arquivo (= fonte citavel no chat), label do cabecalho,
#         caminho no ccivil_03, minimo de artigos esperado)
NORMAS = [
    # ---- br-essencial: o que toda edicao ja chega sabendo --------------------
    ("cf88", "br-essencial", "Constituicao Federal de 1988", "CF/88",
     "constituicao/constituicaocompilado.htm", 250),
    ("codigo-civil", "br-essencial", "Codigo Civil (Lei 10.406-2002)", "Código Civil",
     "leis/2002/l10406compilada.htm", 1800),
    ("cdc", "br-essencial", "Codigo de Defesa do Consumidor (Lei 8.078-1990)", "CDC",
     "leis/l8078compilado.htm", 100),
    ("clt", "br-essencial", "CLT - Consolidacao das Leis do Trabalho (Decreto-Lei 5.452-1943)",
     "CLT", "decreto-lei/del5452compilado.htm", 700),
    # ---- br-legislacao-federal: codigos -------------------------------------
    ("codigo-penal", "br-legislacao-federal", "Codigo Penal (Decreto-Lei 2.848-1940)",
     "Código Penal", "decreto-lei/del2848compilado.htm", 300),
    ("cpc", "br-legislacao-federal", "Codigo de Processo Civil (Lei 13.105-2015)",
     "CPC/2015", "_ato2015-2018/2015/lei/l13105compilada.htm", 950),
    ("cpp", "br-legislacao-federal", "Codigo de Processo Penal (Decreto-Lei 3.689-1941)",
     "CPP", "decreto-lei/del3689compilado.htm", 600),
    ("ctn", "br-legislacao-federal", "Codigo Tributario Nacional (Lei 5.172-1966)",
     "CTN", "leis/l5172compilado.htm", 180),
    ("codigo-eleitoral", "br-legislacao-federal", "Codigo Eleitoral (Lei 4.737-1965)",
     "Código Eleitoral", "leis/l4737compilado.htm", 320),
    ("ctb", "br-legislacao-federal", "Codigo de Transito Brasileiro (Lei 9.503-1997)",
     "CTB", "leis/l9503compilado.htm", 300),
    ("codigo-florestal", "br-legislacao-federal", "Codigo Florestal (Lei 12.651-2012)",
     "Código Florestal", "_ato2011-2014/2012/lei/l12651compilado.htm", 70),
    ("cpm", "br-legislacao-federal", "Codigo Penal Militar (Decreto-Lei 1.001-1969)",
     "CPM", "decreto-lei/del1001compilado.htm", 200),
    ("cppm", "br-legislacao-federal", "Codigo de Processo Penal Militar (Decreto-Lei 1.002-1969)",
     "CPPM", "decreto-lei/del1002compilado.htm", 600),
    ("lindb", "br-legislacao-federal", "LINDB (Decreto-Lei 4.657-1942)", "LINDB",
     "decreto-lei/del4657compilado.htm", 15),
    ("contravencoes", "br-legislacao-federal",
     "Lei das Contravencoes Penais (Decreto-Lei 3.688-1941)", "LCP",
     "decreto-lei/del3688.htm", 50),
    # ---- estatutos -----------------------------------------------------------
    ("eca", "br-legislacao-federal", "ECA - Estatuto da Crianca e do Adolescente (Lei 8.069-1990)",
     "ECA", "leis/l8069compilado.htm", 220),
    ("estatuto-idoso", "br-legislacao-federal", "Estatuto da Pessoa Idosa (Lei 10.741-2003)",
     "Estatuto da Pessoa Idosa", "leis/2003/l10.741compilado.htm", 100),
    ("estatuto-pcd", "br-legislacao-federal",
     "Estatuto da Pessoa com Deficiencia (Lei 13.146-2015)",
     "Estatuto da Pessoa com Deficiência", "_ato2015-2018/2015/lei/l13146.htm", 110),
    ("estatuto-cidade", "br-legislacao-federal", "Estatuto da Cidade (Lei 10.257-2001)",
     "Estatuto da Cidade", "leis/leis_2001/l10257.htm", 45),
    ("desarmamento", "br-legislacao-federal", "Estatuto do Desarmamento (Lei 10.826-2003)",
     "Estatuto do Desarmamento", "leis/2003/l10.826compilado.htm", 30),
    ("igualdade-racial", "br-legislacao-federal",
     "Estatuto da Igualdade Racial (Lei 12.288-2010)", "Estatuto da Igualdade Racial",
     "_ato2007-2010/2010/lei/l12288.htm", 55),
    ("lei-geral-esporte", "br-legislacao-federal", "Lei Geral do Esporte (Lei 14.597-2023)",
     "Lei Geral do Esporte", "_ato2023-2026/2023/lei/l14597.htm", 180),
    ("estatuto-oab", "br-legislacao-federal", "Estatuto da OAB (Lei 8.906-1994)",
     "Estatuto da OAB", "leis/l8906.htm", 70),
    ("servidores-8112", "br-legislacao-federal",
     "Estatuto dos Servidores Federais (Lei 8.112-1990)", "Lei 8.112",
     "leis/l8112cons.htm", 200),
    # ---- leis fundamentais ---------------------------------------------------
    ("lgpd", "br-legislacao-federal", "LGPD (Lei 13.709-2018)", "LGPD",
     "_ato2015-2018/2018/lei/l13709compilado.htm", 55),
    ("marco-civil", "br-legislacao-federal", "Marco Civil da Internet (Lei 12.965-2014)",
     "Marco Civil da Internet", "_ato2011-2014/2014/lei/l12965.htm", 28),
    ("lai", "br-legislacao-federal", "Lei de Acesso a Informacao (Lei 12.527-2011)",
     "LAI", "_ato2011-2014/2011/lei/l12527.htm", 40),
    ("maria-da-penha", "br-legislacao-federal", "Lei Maria da Penha (Lei 11.340-2006)",
     "Lei Maria da Penha", "_ato2004-2006/2006/lei/l11340.htm", 40),
    ("lei-drogas", "br-legislacao-federal", "Lei de Drogas (Lei 11.343-2006)",
     "Lei de Drogas", "_ato2004-2006/2006/lei/l11343.htm", 60),
    ("licitacoes", "br-legislacao-federal",
     "Lei de Licitacoes e Contratos (Lei 14.133-2021)", "Lei de Licitações",
     "_ato2019-2022/2021/lei/l14133.htm", 170),
    ("lrf", "br-legislacao-federal", "Lei de Responsabilidade Fiscal (LC 101-2000)",
     "LRF", "leis/lcp/lcp101.htm", 65),
    ("improbidade", "br-legislacao-federal",
     "Lei de Improbidade Administrativa (Lei 8.429-1992)", "Lei de Improbidade",
     "leis/l8429compilada.htm", 20),
    ("anticorrupcao", "br-legislacao-federal", "Lei Anticorrupcao (Lei 12.846-2013)",
     "Lei Anticorrupção", "_ato2011-2014/2013/lei/l12846.htm", 25),
    ("lep", "br-legislacao-federal", "Lei de Execucao Penal (Lei 7.210-1984)", "LEP",
     "leis/l7210compilado.htm", 180),
    ("juizados", "br-legislacao-federal", "Lei dos Juizados Especiais (Lei 9.099-1995)",
     "Lei 9.099", "leis/l9099.htm", 85),
    ("inquilinato", "br-legislacao-federal", "Lei do Inquilinato (Lei 8.245-1991)",
     "Lei do Inquilinato", "leis/l8245compilado.htm", 80),
    ("falencias", "br-legislacao-federal",
     "Lei de Falencias e Recuperacao de Empresas (Lei 11.101-2005)", "Lei 11.101",
     "_ato2004-2006/2005/lei/l11101.htm", 180),
    ("lei-sa", "br-legislacao-federal", "Lei das Sociedades Anonimas (Lei 6.404-1976)",
     "Lei das S.A.", "leis/l6404compilada.htm", 280),
    ("eleicoes-9504", "br-legislacao-federal", "Lei das Eleicoes (Lei 9.504-1997)",
     "Lei das Eleições", "leis/l9504.htm", 95),
    ("partidos-9096", "br-legislacao-federal", "Lei dos Partidos Politicos (Lei 9.096-1995)",
     "Lei dos Partidos", "leis/l9096compilado.htm", 55),
    ("inelegibilidade-lc64", "br-legislacao-federal", "Lei de Inelegibilidade (LC 64-1990)",
     "LC 64/1990", "leis/lcp/lcp64.htm", 22),
    ("sus-8080", "br-legislacao-federal", "Lei Organica da Saude - SUS (Lei 8.080-1990)",
     "Lei do SUS", "leis/l8080.htm", 45),
    ("ldb", "br-legislacao-federal", "LDB - Diretrizes e Bases da Educacao (Lei 9.394-1996)",
     "LDB", "leis/l9394compilado.htm", 80),
    ("crimes-ambientais", "br-legislacao-federal", "Lei de Crimes Ambientais (Lei 9.605-1998)",
     "Lei de Crimes Ambientais", "leis/l9605.htm", 70),
    ("acao-civil-publica", "br-legislacao-federal", "Lei da Acao Civil Publica (Lei 7.347-1985)",
     "Lei da ACP", "leis/l7347compilada.htm", 18),
    ("mandado-seguranca", "br-legislacao-federal",
     "Lei do Mandado de Seguranca (Lei 12.016-2009)", "Lei do MS",
     "_ato2007-2010/2009/lei/l12016.htm", 22),
    ("lavagem", "br-legislacao-federal", "Lei de Lavagem de Dinheiro (Lei 9.613-1998)",
     "Lei de Lavagem", "leis/l9613compilado.htm", 14),
    ("organizacao-criminosa", "br-legislacao-federal",
     "Lei das Organizacoes Criminosas (Lei 12.850-2013)", "Lei 12.850",
     "_ato2011-2014/2013/lei/l12850.htm", 22),
    ("registros-publicos", "br-legislacao-federal",
     "Lei de Registros Publicos (Lei 6.015-1973)", "Lei de Registros Públicos",
     "leis/l6015compilada.htm", 250),
    ("migracao", "br-legislacao-federal", "Lei de Migracao (Lei 13.445-2017)",
     "Lei de Migração", "_ato2015-2018/2017/lei/l13445.htm", 100),
    ("crimes-hediondos", "br-legislacao-federal", "Lei de Crimes Hediondos (Lei 8.072-1990)",
     "Lei 8.072", "leis/l8072compilada.htm", 10),
    ("desapropriacao", "br-legislacao-federal",
     "Lei de Desapropriacao (Decreto-Lei 3.365-1941)", "DL 3.365",
     "decreto-lei/del3365compilado.htm", 20),
    ("execucao-fiscal", "br-legislacao-federal", "Lei de Execucao Fiscal (Lei 6.830-1980)",
     "LEF", "leis/l6830.htm", 35),
    ("arbitragem", "br-legislacao-federal", "Lei de Arbitragem (Lei 9.307-1996)",
     "Lei de Arbitragem", "leis/l9307.htm", 40),
    ("habeas-data", "br-legislacao-federal", "Lei do Habeas Data (Lei 9.507-1997)",
     "Lei do Habeas Data", "leis/l9507.htm", 15),
    ("acao-popular", "br-legislacao-federal", "Lei da Acao Popular (Lei 4.717-1965)",
     "Lei da Ação Popular", "leis/l4717.htm", 18),
    ("previdencia-beneficios", "br-legislacao-federal",
     "Previdencia - Planos de Beneficios (Lei 8.213-1991)", "Lei 8.213",
     "leis/l8213compilado.htm", 90),
    ("previdencia-custeio", "br-legislacao-federal",
     "Previdencia - Custeio (Lei 8.212-1991)", "Lei 8.212",
     "leis/l8212compilado.htm", 80),
    ("mandado-injuncao", "br-legislacao-federal",
     "Lei do Mandado de Injuncao (Lei 13.300-2016)", "Lei do MI",
     "_ato2015-2018/2016/lei/l13300.htm", 12),
    # --- 2a leva (jun/2026): mais leis federais -------------------------------
    ("direitos-autorais", "br-legislacao-federal", "Lei de Direitos Autorais (Lei 9.610-1998)",
     "Lei de Direitos Autorais", "leis/l9610.htm", 60),
    ("propriedade-industrial", "br-legislacao-federal", "Lei de Propriedade Industrial (Lei 9.279-1996)",
     "LPI", "leis/l9279.htm", 130),
    ("software", "br-legislacao-federal", "Lei do Software (Lei 9.609-1998)",
     "Lei do Software", "leis/l9609.htm", 8),
    ("telecomunicacoes", "br-legislacao-federal", "Lei Geral de Telecomunicacoes (Lei 9.472-1997)",
     "LGT", "leis/l9472.htm", 120),
    ("desporto-pele", "br-legislacao-federal", "Lei Pele - Desporto (Lei 9.615-1998)",
     "Lei Pelé", "leis/l9615consol.htm", 50),
    ("estatuto-torcedor", "br-legislacao-federal", "Estatuto de Defesa do Torcedor (Lei 10.671-2003)",
     "Estatuto do Torcedor", "leis/2003/l10.671.htm", 15),
    ("planos-saude", "br-legislacao-federal", "Lei dos Planos de Saude (Lei 9.656-1998)",
     "Lei dos Planos de Saúde", "leis/l9656.htm", 18),
    ("recursos-hidricos", "br-legislacao-federal", "Politica Nacional de Recursos Hidricos (Lei 9.433-1997)",
     "Lei das Águas", "leis/l9433.htm", 30),
    ("saneamento", "br-legislacao-federal", "Marco do Saneamento Basico (Lei 11.445-2007)",
     "Lei do Saneamento", "_ato2007-2010/2007/lei/l11445.htm", 30),
    ("mobilidade-urbana", "br-legislacao-federal", "Politica Nacional de Mobilidade Urbana (Lei 12.587-2012)",
     "Lei de Mobilidade Urbana", "_ato2011-2014/2012/lei/l12587.htm", 16),
    ("biosseguranca", "br-legislacao-federal", "Lei de Biosseguranca (Lei 11.105-2005)",
     "Lei de Biossegurança", "_ato2004-2006/2005/lei/l11105.htm", 22),
    ("estatuto-indio", "br-legislacao-federal", "Estatuto do Indio (Lei 6.001-1973)",
     "Estatuto do Índio", "leis/l6001.htm", 35),
    ("greve", "br-legislacao-federal", "Lei de Greve (Lei 7.783-1989)",
     "Lei de Greve", "leis/l7783.htm", 10),
    ("estagio", "br-legislacao-federal", "Lei do Estagio (Lei 11.788-2008)",
     "Lei do Estágio", "_ato2007-2010/2008/lei/l11788.htm", 12),
    ("simples-nacional", "br-legislacao-federal", "Estatuto da Microempresa e Simples Nacional (LC 123-2006)",
     "LC 123 (Simples Nacional)", "leis/lcp/lcp123.htm", 45),
    ("lei-kandir", "br-legislacao-federal", "Lei Kandir - ICMS (LC 87-1996)",
     "Lei Kandir (LC 87)", "leis/lcp/lcp87.htm", 20),
    ("estatais", "br-legislacao-federal", "Lei das Estatais (Lei 13.303-2016)",
     "Lei das Estatais", "_ato2015-2018/2016/lei/l13303.htm", 55),
    ("estatuto-juventude", "br-legislacao-federal", "Estatuto da Juventude (Lei 12.852-2013)",
     "Estatuto da Juventude", "_ato2011-2014/2013/lei/l12852.htm", 28),
    ("cotas-universidades", "br-legislacao-federal", "Lei de Cotas nas Universidades (Lei 12.711-2012)",
     "Lei de Cotas", "_ato2011-2014/2012/lei/l12711.htm", 6),
    ("antiterrorismo", "br-legislacao-federal", "Lei Antiterrorismo (Lei 13.260-2016)",
     "Lei Antiterrorismo", "_ato2015-2018/2016/lei/l13260.htm", 12),
    ("crimes-tributarios", "br-legislacao-federal", "Crimes contra a Ordem Tributaria (Lei 8.137-1990)",
     "Lei 8.137 (crimes tributários)", "leis/l8137.htm", 16),
    ("aeronautica", "br-legislacao-federal", "Codigo Brasileiro de Aeronautica (Lei 7.565-1986)",
     "CBA", "leis/l7565.htm", 200),
    ("direito-financeiro", "br-legislacao-federal", "Normas Gerais de Direito Financeiro (Lei 4.320-1964)",
     "Lei 4.320", "leis/l4320.htm", 50),
    ("estatuto-terra", "br-legislacao-federal", "Estatuto da Terra (Lei 4.504-1964)",
     "Estatuto da Terra", "leis/l4504.htm", 80),
    ("processo-administrativo", "br-legislacao-federal", "Lei do Processo Administrativo Federal (Lei 9.784-1999)",
     "Lei 9.784 (proc. administrativo)", "leis/l9784.htm", 45),
    ("consorcios-publicos", "br-legislacao-federal", "Lei dos Consorcios Publicos (Lei 11.107-2005)",
     "Lei de Consórcios Públicos", "_ato2004-2006/2005/lei/l11107.htm", 15),
    ("rouanet", "br-legislacao-federal", "Lei Rouanet - Incentivo a Cultura (Lei 8.313-1991)",
     "Lei Rouanet", "leis/l8313cons.htm", 14),
    ("abuso-autoridade", "br-legislacao-federal", "Lei de Abuso de Autoridade (Lei 13.869-2019)",
     "Lei de Abuso de Autoridade", "_ato2019-2022/2019/lei/l13869.htm", 30),
    ("defesa-concorrencia", "br-legislacao-federal", "Lei de Defesa da Concorrencia - CADE (Lei 12.529-2011)",
     "Lei do CADE", "_ato2011-2014/2011/lei/l12529.htm", 80),
    ("startups", "br-legislacao-federal", "Marco Legal das Startups (LC 182-2021)",
     "Marco das Startups", "leis/lcp/lcp182.htm", 14),
    ("crimes-financeiros", "br-legislacao-federal", "Crimes contra o Sistema Financeiro Nacional (Lei 7.492-1986)",
     "Lei 7.492 (colarinho branco)", "leis/l7492.htm", 20),
    ("loas", "br-legislacao-federal", "Lei Organica da Assistencia Social - LOAS (Lei 8.742-1993)",
     "LOAS", "leis/l8742.htm", 25),
    ("fgts", "br-legislacao-federal", "Lei do FGTS (Lei 8.036-1990)",
     "Lei do FGTS", "leis/l8036consol.htm", 18),

    # --- 3a leva (jun/2026): completar o federal -----------------------------
    # penal / criminal
    ("tortura", "br-legislacao-federal", "Lei de Tortura (Lei 9.455-1997)",
     "Lei de Tortura", "leis/l9455.htm", 4),
    ("racismo", "br-legislacao-federal", "Lei do Racismo (Lei 7.716-1989)",
     "Lei do Racismo", "leis/l7716.htm", 8),
    ("protecao-testemunha", "br-legislacao-federal",
     "Lei de Protecao a Vitimas e Testemunhas (Lei 9.807-1999)", "Lei 9.807",
     "leis/l9807.htm", 8),
    ("crimes-responsabilidade", "br-legislacao-federal",
     "Lei dos Crimes de Responsabilidade (Lei 1.079-1950)", "Lei 1.079",
     "leis/l1079.htm", 25),
    ("crimes-prefeitos", "br-legislacao-federal",
     "Crimes de Responsabilidade de Prefeitos (Decreto-Lei 201-1967)", "DL 201",
     "decreto-lei/del0201.htm", 3),
    ("interceptacao", "br-legislacao-federal",
     "Lei de Interceptacao Telefonica (Lei 9.296-1996)", "Lei 9.296",
     "leis/l9296.htm", 6),
    ("identificacao-criminal", "br-legislacao-federal",
     "Lei de Identificacao Criminal (Lei 12.037-2009)", "Lei 12.037",
     "_ato2007-2010/2009/lei/l12037.htm", 6),
    # constitucional / politico
    ("ficha-limpa", "br-legislacao-federal", "Lei da Ficha Limpa (LC 135-2010)",
     "LC 135 (Ficha Limpa)", "leis/lcp/lcp135.htm", 2),
    ("lc95", "br-legislacao-federal", "Lei de Elaboracao das Leis (LC 95-1998)",
     "LC 95", "leis/lcp/lcp95.htm", 12),
    # tributario / financeiro / empresarial
    ("iss-lc116", "br-legislacao-federal", "Imposto sobre Servicos - ISS (LC 116-2003)",
     "LC 116 (ISS)", "leis/lcp/lcp116.htm", 7),
    ("sigilo-bancario", "br-legislacao-federal",
     "Sigilo de Operacoes Financeiras (LC 105-2001)", "LC 105", "leis/lcp/lcp105.htm", 8),
    # (cheque/Lei 7.357 fora: a pagina do Planalto usa <br>, nao <p> — o parser
    #  extrai 0 artigos; nao vale fork do parser por uma lei. Adicionar via outro
    #  coletor no futuro se necessario.)
    ("protesto", "br-legislacao-federal", "Lei do Protesto de Titulos (Lei 9.492-1997)",
     "Lei do Protesto", "leis/l9492.htm", 25),
    ("duplicatas", "br-legislacao-federal", "Lei das Duplicatas (Lei 5.474-1968)",
     "Lei das Duplicatas", "leis/l5474.htm", 18),
    ("inovacao", "br-legislacao-federal", "Lei de Inovacao - Marco CT&I (Lei 10.973-2004)",
     "Lei de Inovacao", "_ato2004-2006/2004/lei/l10.973.htm", 12),
    ("lei-do-bem", "br-legislacao-federal", "Lei do Bem - Incentivos a Inovacao (Lei 11.196-2005)",
     "Lei do Bem", "_ato2004-2006/2005/lei/l11196.htm", 30),
    ("agencias-reguladoras", "br-legislacao-federal",
     "Lei Geral das Agencias Reguladoras (Lei 13.848-2019)", "Lei 13.848",
     "_ato2019-2022/2019/lei/l13848.htm", 18),
    ("liberdade-economica", "br-legislacao-federal",
     "Lei da Liberdade Economica (Lei 13.874-2019)", "Lei da Liberdade Economica",
     "_ato2019-2022/2019/lei/l13874.htm", 8),
    ("cadastro-positivo", "br-legislacao-federal", "Lei do Cadastro Positivo (Lei 12.414-2011)",
     "Lei 12.414", "_ato2011-2014/2011/lei/l12414.htm", 10),
    ("turismo", "br-legislacao-federal", "Lei Geral do Turismo (Lei 11.771-2008)",
     "Lei do Turismo", "_ato2007-2010/2008/lei/l11771.htm", 25),
    # social / administrativo / saude / educacao
    ("sinase", "br-legislacao-federal", "SINASE - Sistema de Atendimento Socioeducativo (Lei 12.594-2012)",
     "SINASE", "_ato2011-2014/2012/lei/l12594.htm", 40),
    ("cotas-servico-publico", "br-legislacao-federal",
     "Cotas para Negros no Servico Publico (Lei 12.990-2014)", "Lei 12.990",
     "_ato2011-2014/2014/lei/l12990.htm", 3),
    ("guardas-municipais", "br-legislacao-federal",
     "Estatuto Geral das Guardas Municipais (Lei 13.022-2014)", "Lei 13.022",
     "_ato2011-2014/2014/lei/l13022.htm", 10),
    ("susp", "br-legislacao-federal",
     "Politica Nacional de Seguranca Publica - SUSP (Lei 13.675-2018)", "SUSP",
     "_ato2015-2018/2018/lei/l13675.htm", 20),
    ("org-sociais", "br-legislacao-federal", "Lei das Organizacoes Sociais (Lei 9.637-1998)",
     "Lei das OS", "leis/l9637.htm", 15),
    ("oscip", "br-legislacao-federal", "Lei das OSCIP (Lei 9.790-1999)",
     "Lei das OSCIP", "leis/l9790.htm", 12),
    ("mrosc", "br-legislacao-federal", "Marco Regulatorio das Organizacoes da Sociedade Civil (Lei 13.019-2014)",
     "MROSC", "_ato2011-2014/2014/lei/l13019.htm", 40),
    ("reforma-psiquiatrica", "br-legislacao-federal", "Lei da Reforma Psiquiatrica (Lei 10.216-2001)",
     "Lei 10.216", "leis/leis_2001/l10216.htm", 6),
    ("fundeb", "br-legislacao-federal", "FUNDEB - Financiamento da Educacao Basica (Lei 14.113-2020)",
     "FUNDEB", "_ato2019-2022/2020/lei/l14113.htm", 35),
    ("governo-digital", "br-legislacao-federal", "Lei do Governo Digital (Lei 14.129-2021)",
     "Lei do Governo Digital", "_ato2019-2022/2021/lei/l14129.htm", 35),
    ("juizados-federais", "br-legislacao-federal", "Juizados Especiais Federais (Lei 10.259-2001)",
     "Lei 10.259", "leis/leis_2001/l10259.htm", 15),
    ("henry-borel", "br-legislacao-federal", "Lei Henry Borel - Protecao de Criancas (Lei 14.344-2022)",
     "Lei Henry Borel", "_ato2019-2022/2022/lei/l14344.htm", 20),

    # --- 4a leva (jun/2026): busca profunda — mais leis federais --------------
    # civil / familia
    ("alimentos", "br-legislacao-federal", "Lei de Alimentos (Lei 5.478-1968)",
     "Lei de Alimentos", "leis/l5478.htm", 6),
    ("divorcio", "br-legislacao-federal", "Lei do Divorcio (Lei 6.515-1977)",
     "Lei do Divorcio", "leis/l6515.htm", 8),
    ("alienacao-parental", "br-legislacao-federal", "Lei da Alienacao Parental (Lei 12.318-2010)",
     "Alienacao Parental", "_ato2007-2010/2010/lei/l12318.htm", 5),
    ("guarda-compartilhada", "br-legislacao-federal", "Lei da Guarda Compartilhada (Lei 13.058-2014)",
     "Guarda Compartilhada", "_ato2011-2014/2014/lei/l13058.htm", 2),
    ("adocao", "br-legislacao-federal", "Lei Nacional da Adocao (Lei 12.010-2009)",
     "Lei da Adocao", "_ato2007-2010/2009/lei/l12010.htm", 4),
    # consumidor / digital
    ("superendividamento", "br-legislacao-federal", "Lei do Superendividamento (Lei 14.181-2021)",
     "Superendividamento", "_ato2019-2022/2021/lei/l14181.htm", 6),
    ("carolina-dieckmann", "br-legislacao-federal",
     "Lei Carolina Dieckmann - Crimes Ciberneticos (Lei 12.737-2012)", "Lei 12.737",
     "_ato2011-2014/2012/lei/l12737.htm", 2),
    ("bullying", "br-legislacao-federal", "Lei de Combate ao Bullying (Lei 13.185-2015)",
     "Lei do Bullying", "_ato2015-2018/2015/lei/l13185.htm", 4),
    # penal / economico
    ("economia-popular", "br-legislacao-federal", "Crimes contra a Economia Popular (Lei 1.521-1951)",
     "Lei 1.521", "leis/l1521.htm", 8),
    ("crimes-ordem-economica", "br-legislacao-federal", "Crimes contra a Ordem Economica (Lei 8.176-1991)",
     "Lei 8.176", "leis/l8176.htm", 3),
    # trabalhista
    ("decimo-terceiro", "br-legislacao-federal", "Lei do 13o Salario (Lei 4.090-1962)",
     "Lei do 13o Salario", "leis/l4090.htm", 2),
    ("aviso-previo", "br-legislacao-federal", "Lei do Aviso Previo Proporcional (Lei 12.506-2011)",
     "Aviso Previo", "_ato2011-2014/2011/lei/l12506.htm", 2),
    ("domestico-lc150", "br-legislacao-federal", "Lei do Trabalho Domestico (LC 150-2015)",
     "LC 150", "leis/lcp/lcp150.htm", 25),
    ("terceirizacao", "br-legislacao-federal", "Lei da Terceirizacao (Lei 13.429-2017)",
     "Lei 13.429", "_ato2015-2018/2017/lei/l13429.htm", 6),
    ("seguro-desemprego", "br-legislacao-federal", "Lei do Seguro-Desemprego e FAT (Lei 7.998-1990)",
     "Lei 7.998", "leis/l7998.htm", 15),
    # tributario / empresarial / financeiro
    ("imposto-renda", "br-legislacao-federal", "Lei do Imposto de Renda das Pessoas Fisicas (Lei 7.713-1988)",
     "Lei 7.713 (IRPF)", "leis/l7713.htm", 20),
    ("legislacao-tributaria", "br-legislacao-federal", "Legislacao Tributaria Federal (Lei 9.430-1996)",
     "Lei 9.430", "leis/l9430.htm", 25),
    ("cvm", "br-legislacao-federal", "Lei do Mercado de Valores Mobiliarios - CVM (Lei 6.385-1976)",
     "Lei 6.385 (CVM)", "leis/l6385.htm", 18),
    ("cooperativas", "br-legislacao-federal", "Lei das Cooperativas (Lei 5.764-1971)",
     "Lei das Cooperativas", "leis/l5764.htm", 50),
    ("sistema-financeiro", "br-legislacao-federal", "Lei do Sistema Financeiro Nacional (Lei 4.595-1964)",
     "Lei 4.595", "leis/l4595.htm", 20),
    ("pis-pasep", "br-legislacao-federal", "PIS-PASEP (LC 7-1970)",
     "LC 7 (PIS-PASEP)", "leis/lcp/lcp07.htm", 6),
    # administrativo / publico
    ("concessoes", "br-legislacao-federal", "Lei das Concessoes de Servicos Publicos (Lei 8.987-1995)",
     "Lei 8.987 (Concessoes)", "leis/l8987cons.htm", 25),
    ("ppp", "br-legislacao-federal", "Lei das Parcerias Publico-Privadas (Lei 11.079-2004)",
     "Lei das PPP", "_ato2004-2006/2004/lei/l11079.htm", 18),
    ("transparencia-lc131", "br-legislacao-federal", "Lei da Transparencia Fiscal (LC 131-2009)",
     "LC 131", "leis/lcp/lcp131.htm", 2),
    # ambiental / agrario
    ("pnma", "br-legislacao-federal", "Politica Nacional do Meio Ambiente (Lei 6.938-1981)",
     "PNMA", "leis/l6938.htm", 18),
    ("snuc", "br-legislacao-federal", "SNUC - Unidades de Conservacao (Lei 9.985-2000)",
     "SNUC", "leis/l9985.htm", 25),
    ("mata-atlantica", "br-legislacao-federal", "Lei da Mata Atlantica (Lei 11.428-2006)",
     "Mata Atlantica", "_ato2004-2006/2006/lei/l11428.htm", 25),
    ("residuos-solidos", "br-legislacao-federal", "Politica Nacional de Residuos Solidos (Lei 12.305-2010)",
     "PNRS", "_ato2007-2010/2010/lei/l12305.htm", 25),
    ("florestas-publicas", "br-legislacao-federal", "Lei de Gestao de Florestas Publicas (Lei 11.284-2006)",
     "Lei 11.284", "_ato2004-2006/2006/lei/l11284.htm", 40),
    ("reforma-agraria", "br-legislacao-federal", "Lei da Reforma Agraria (Lei 8.629-1993)",
     "Reforma Agraria", "leis/l8629.htm", 15),
    # saude / educacao
    ("anvisa", "br-legislacao-federal", "Lei da ANVISA - Vigilancia Sanitaria (Lei 9.782-1999)",
     "Lei da ANVISA", "leis/l9782.htm", 3),
    ("genericos", "br-legislacao-federal", "Lei dos Medicamentos Genericos (Lei 9.787-1999)",
     "Lei dos Genericos", "leis/l9787.htm", 2),
    ("antifumo", "br-legislacao-federal", "Lei Antifumo (Lei 9.294-1996)",
     "Lei Antifumo", "leis/l9294.htm", 6),
    ("sus-participacao", "br-legislacao-federal", "Participacao e Transferencias do SUS (Lei 8.142-1990)",
     "Lei 8.142", "leis/l8142.htm", 3),
    ("pne", "br-legislacao-federal", "Plano Nacional de Educacao (Lei 13.005-2014)",
     "PNE", "_ato2011-2014/2014/lei/l13005.htm", 6),
    ("fies", "br-legislacao-federal", "FIES - Financiamento Estudantil (Lei 10.260-2001)",
     "FIES", "leis/leis_2001/l10260.htm", 18),
    ("prouni", "br-legislacao-federal", "PROUNI (Lei 11.096-2005)",
     "PROUNI", "_ato2004-2006/2005/lei/l11096.htm", 12),
    # processual / justica
    ("assistencia-judiciaria", "br-legislacao-federal", "Lei da Assistencia Judiciaria Gratuita (Lei 1.060-1950)",
     "Lei 1.060", "leis/l1060.htm", 6),
    ("juizados-fazenda", "br-legislacao-federal", "Juizados Especiais da Fazenda Publica (Lei 12.153-2009)",
     "Lei 12.153", "_ato2007-2010/2009/lei/l12153.htm", 12),
    # historico
    ("anistia", "br-legislacao-federal", "Lei da Anistia (Lei 6.683-1979)",
     "Lei da Anistia", "leis/l6683.htm", 5),
    # portuario
    ("portos", "br-legislacao-federal", "Lei dos Portos (Lei 12.815-2013)",
     "Lei dos Portos", "_ato2011-2014/2013/lei/l12815.htm", 35),

    # ===== br-licitacoes: treinamento completo de contratos e licitacoes =======
    # Pacote dedicado (instala lado a lado): a Nova Lei + regimes especiais +
    # legado de transicao + decretos que regulamentam a 14.133. Foco Gov/consultoria.
    # 8.666/1993 e 10.520/2002 ficaram de fora: REVOGADAS pela 14.133 (o coletor
    # descarta texto revogado, entao rendem ~0 artigos vigentes). O foco e a lei atual.
    ("lic-14133", "br-licitacoes",
     "Nova Lei de Licitacoes e Contratos (Lei 14.133-2021)", "Lei 14.133/2021",
     "_ato2019-2022/2021/lei/l14133.htm", 150),
    ("lic-estatais", "br-licitacoes",
     "Licitacoes e contratos das estatais (Lei 13.303-2016)", "Lei 13.303/2016 (Estatais)",
     "_ato2015-2018/2016/lei/l13303.htm", 50),
    ("lic-meepp", "br-licitacoes",
     "Tratamento favorecido a ME e EPP em licitacoes (LC 123-2006)", "LC 123/2006 (ME/EPP)",
     "leis/lcp/lcp123.htm", 45),
    ("lic-pregao-eletronico", "br-licitacoes",
     "Pregao eletronico (Decreto 10.024-2019)", "Decreto 10.024/2019",
     "_ato2019-2022/2019/decreto/d10024.htm", 20),
    ("lic-agente", "br-licitacoes",
     "Agente de contratacao e funcoes essenciais (Decreto 11.246-2022)", "Decreto 11.246/2022",
     "_ato2019-2022/2022/decreto/d11246.htm", 10),

    # ===== br-direito-militar: o maximo de legislacao militar federal ==========
    # Pacote tematico dedicado (instala lado a lado). Penal/processual militar +
    # estatuto/carreira + Justica Militar + servico/pensoes/mobilizacao + ensino +
    # disciplinares + arcabouco das forcas auxiliares (PM/CBM e DF). Os regulamentos
    # disciplinares (RDE, R-200, etc.) vem em tabela/anexo: o coletor cai no TEXTO
    # BRUTO automaticamente. CPM/CPPM repetem o br-legislacao-federal de proposito.
    ("mil-cpm", "br-direito-militar", "Codigo Penal Militar (Decreto-Lei 1.001-1969)",
     "CPM", "decreto-lei/del1001compilado.htm", 300),
    ("mil-cppm", "br-direito-militar", "Codigo de Processo Penal Militar (Decreto-Lei 1.002-1969)",
     "CPPM", "decreto-lei/del1002compilado.htm", 600),
    ("mil-estatuto", "br-direito-militar", "Estatuto dos Militares (Lei 6.880-1980)",
     "Estatuto dos Militares", "leis/l6880.htm", 100),
    ("mil-lc97", "br-direito-militar", "Normas Gerais das Forcas Armadas (LC 97-1999)",
     "LC 97", "leis/lcp/lcp97.htm", 20),
    ("mil-servico", "br-direito-militar", "Lei do Servico Militar (Lei 4.375-1964)",
     "Lei do Servico Militar", "leis/l4375.htm", 6),
    ("mil-rlsm", "br-direito-militar", "Regulamento do Servico Militar (Decreto 57.654-1966)",
     "RLSM", "decreto/d57654.htm", 150),
    ("mil-pensoes", "br-direito-militar", "Pensoes Militares (Lei 3.765-1960)",
     "Pensoes Militares", "leis/l3765.htm", 8),
    ("mil-jmu", "br-direito-militar", "Organizacao da Justica Militar da Uniao (Lei 8.457-1992)",
     "Lei da JMU", "leis/l8457.htm", 80),
    ("mil-jmu-stm", "br-direito-militar", "Organizacao da JMU e do STM (Lei 13.774-2018)",
     "Lei 13.774", "_ato2015-2018/2018/lei/L13774.htm", 30),
    ("mil-carreira", "br-direito-militar", "Carreira e Protecao Social dos Militares (Lei 13.954-2019)",
     "Lei 13.954", "_ato2019-2022/2019/lei/l13954.htm", 50),
    ("mil-promocoes", "br-direito-militar", "Promocoes de Oficiais da Ativa (Lei 5.821-1972)",
     "Lei 5.821", "leis/l5821.htm", 2),
    ("mil-crimes-vida", "br-direito-militar", "Crimes Dolosos contra a Vida na Justica Militar (Lei 9.299-1996)",
     "Lei 9.299", "leis/l9299.htm", 2),
    ("mil-competencia-jm", "br-direito-militar", "Competencia da Justica Militar (Lei 13.491-2017)",
     "Lei 13.491", "_ato2015-2018/2017/lei/l13491.htm", 2),
    ("mil-mobilizacao", "br-direito-militar", "Mobilizacao Nacional (Lei 11.631-2007)",
     "Mobilizacao Nacional", "_ato2007-2010/2007/lei/l11631.htm", 8),
    ("mil-ingresso", "br-direito-militar", "Ingresso nas Forcas Armadas (Lei 12.705-2012)",
     "Lei 12.705", "_ato2011-2014/2012/lei/l12705.htm", 6),
    ("mil-ensino-eb", "br-direito-militar", "Ensino no Exercito (Lei 9.786-1999)",
     "Ensino no Exercito", "leis/l9786.htm", 15),
    ("mil-ensino-mb", "br-direito-militar", "Ensino na Marinha (Lei 11.279-2006)",
     "Ensino na Marinha", "_ato2004-2006/2006/lei/l11279.htm", 25),
    ("mil-ensino-fab", "br-direito-militar", "Ensino na Aeronautica (Lei 12.464-2011)",
     "Ensino na Aeronautica", "_ato2011-2014/2011/lei/l12464.htm", 25),
    ("mil-conselho-justif", "br-direito-militar", "Conselho de Justificacao (Lei 5.836-1972)",
     "Conselho de Justificacao", "leis/1970-1979/l5836.htm", 12),
    ("mil-rdaer", "br-direito-militar", "Regulamento Disciplinar da Aeronautica (Decreto 76.322-1975)",
     "RDAER", "decreto/1970-1979/d76322.htm", 40),
    # (continencias/Dec 2.243 fora: pagina rende texto curto demais, .md vazio)
    ("mil-pm-cbm", "br-direito-militar", "Organizacao das Policias Militares e Bombeiros (Decreto-Lei 667-1969)",
     "DL 667", "decreto-lei/del0667.htm", 10),
    ("mil-df", "br-direito-militar", "Militares do Distrito Federal (Lei 12.086-2009)",
     "Lei 12.086", "_ato2007-2010/2009/lei/l12086.htm", 80),
    ("mil-pmdf", "br-direito-militar", "Estatuto da PMDF (Lei 7.289-1984)",
     "Estatuto PMDF", "leis/l7289.htm", 10),
    ("mil-cbmdf", "br-direito-militar", "Estatuto do Corpo de Bombeiros Militar do DF (Lei 7.479-1986)",
     "Estatuto CBMDF", "leis/l7479.htm", 6),
    ("mil-remun-df", "br-direito-militar", "Remuneracao dos Militares do DF (Lei 10.486-2002)",
     "Lei 10.486", "leis/2002/l10486.htm", 40),
    ("mil-remun-fa", "br-direito-militar", "Remuneracao dos Militares das Forcas Armadas (MP 2.215-10-2001)",
     "MP 2.215-10", "mpv/2215-10.htm", 3),
    ("mil-compras-defesa", "br-direito-militar", "Compras de Produtos de Defesa (Lei 12.598-2012)",
     "Lei 12.598", "_ato2011-2014/2012/lei/l12598.htm", 20),
    # --- disciplinares / anexo: caem no TEXTO BRUTO automaticamente ----------
    ("mil-rde", "br-direito-militar", "Regulamento Disciplinar do Exercito (Decreto 4.346-2002)",
     "RDE", "decreto/2002/d4346.htm", 1),
    ("mil-r200", "br-direito-militar", "Regulamento das Policias Militares - R-200 (Decreto 88.777-1983)",
     "R-200", "decreto/d88777.htm", 1),
    ("mil-conselho-disc", "br-direito-militar", "Conselho de Disciplina das Pracas (Decreto 71.500-1972)",
     "Conselho de Disciplina", "decreto/1970-1979/d71500.htm", 1),
    ("mil-assist-religiosa", "br-direito-militar", "Assistencia Religiosa nas Forcas Armadas (Lei 6.923-1981)",
     "Assistencia Religiosa", "leis/l6923.htm", 1),
    ("mil-ex-combatentes", "br-direito-militar", "Direitos dos Ex-Combatentes (Lei 5.315-1967)",
     "Ex-Combatentes", "leis/l5315.htm", 1),

    # ===== br-direito-eleitoral: direito eleitoral completo (atualizado 2026) ===
    # Leis-nucleo CONSOLIDADAS (ja incluem as emendas das minirreformas) + leis
    # substantivas autonomas. As resolucoes do TSE para 2026 entram no pacote pela
    # copia do corpus/br-eleicoes-2026 (coletor proprio: coletar_tse.py). Leis
    # puramente emendadoras (12.034, 13.165, 13.488) ficam de fora — redundantes
    # com os textos compilados.
    ("ele-codigo", "br-direito-eleitoral", "Codigo Eleitoral (Lei 4.737-1965)",
     "Codigo Eleitoral", "leis/l4737compilado.htm", 300),
    ("ele-eleicoes", "br-direito-eleitoral", "Lei das Eleicoes (Lei 9.504-1997)",
     "Lei das Eleicoes", "leis/l9504.htm", 80),
    ("ele-partidos", "br-direito-eleitoral", "Lei dos Partidos Politicos (Lei 9.096-1995)",
     "Lei dos Partidos", "leis/l9096compilado.htm", 50),
    ("ele-inelegibilidade", "br-direito-eleitoral", "Lei de Inelegibilidade (LC 64-1990)",
     "LC 64", "leis/lcp/lcp64.htm", 18),
    ("ele-ficha-limpa", "br-direito-eleitoral", "Lei da Ficha Limpa (LC 135-2010)",
     "Ficha Limpa", "leis/lcp/lcp135.htm", 2),
    ("ele-captacao", "br-direito-eleitoral", "Captacao Ilicita de Sufragio (Lei 9.840-1999)",
     "Lei 9.840", "leis/l9840.htm", 4),
    ("ele-transporte", "br-direito-eleitoral", "Transporte e Alimentacao de Eleitores (Lei 6.091-1974)",
     "Lei 6.091", "leis/l6091.htm", 1),
    ("ele-violencia-mulher", "br-direito-eleitoral", "Violencia Politica contra a Mulher (Lei 14.192-2021)",
     "Lei 14.192", "_ato2019-2022/2021/lei/l14192.htm", 8),
    ("ele-lc78", "br-direito-eleitoral", "Numero de Deputados por Estado (LC 78-1993)",
     "LC 78", "leis/lcp/lcp78.htm", 3),
]


class ExtratorBlocos(HTMLParser):
    """Extrai um bloco de texto por <p>, ignorando texto riscado (<strike>/<del>)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocos: list[str] = []
        self._atual: list[str] = []
        self._riscado = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("strike", "del", "s"):
            self._riscado += 1
        elif tag == "p":
            self._fecha()

    def handle_endtag(self, tag):
        if tag in ("strike", "del", "s") and self._riscado:
            self._riscado -= 1
        elif tag == "p":
            self._fecha()

    def handle_data(self, data):
        if not self._riscado:
            self._atual.append(data)

    def _fecha(self):
        texto = re.sub(r"\s+", " ", "".join(self._atual)).strip()
        if texto:
            self.blocos.append(texto)
        self._atual = []

    def close(self):
        self._fecha()
        super().close()


ROMANO = r"(?:[IVXLC]+(?:-[A-Z])?|[ÚU]NIC[OA])"
RE_PARTE = re.compile(rf"^(PARTE|LIVRO)\s+(?:{ROMANO}|GERAL|ESPECIAL)", re.IGNORECASE)
RE_TITULO = re.compile(rf"^T[ÍI]TULO\s+{ROMANO}", re.IGNORECASE)
RE_CAPITULO = re.compile(rf"^CAP[ÍI]TULO\s+{ROMANO}", re.IGNORECASE)
RE_SECAO = re.compile(rf"^(Se[çc][ãa]o|Subse[çc][ãa]o)\s+{ROMANO}", re.IGNORECASE)
# numeros altos vem com ponto de milhar ("Art. 1.028"); ordinal pode vir solto ("Art. 5 o")
RE_ARTIGO = re.compile(r"^Art\.?\s*(\d{1,3}(?:\.\d{3})*)(?:\s*[ºo°.])?\s*(-\s*[A-Z])?", re.IGNORECASE)
RE_ADCT = re.compile(r"ATO DAS DISPOSI[ÇC][ÕO]ES CONSTITUCIONAIS TRANSIT[ÓO]RIAS")
RE_SO_MAIUSCULAS = re.compile(r"^[A-ZÀ-Ü0-9ºª\s,.\-–—()§]+$")
# assinatura final ("Brasilia, 5 de outubro de 1988") — dali em diante e ruido
RE_FIM = re.compile(r"^(Bras[íi]lia|Rio de Janeiro),?\s.*\bde\s+\d{4}")
RE_RUIDO = re.compile(r"Este texto n[ãa]o substitui", re.IGNORECASE)

MINUSCULAS = {"e", "de", "da", "do", "das", "dos", "a", "o", "as", "os", "em", "para"}


def _titulo_pt(texto: str) -> str:
    palavras = texto.lower().split()
    return " ".join(
        p if i > 0 and p in MINUSCULAS else p.capitalize() for i, p in enumerate(palavras)
    )


def _limpa(texto: str) -> str:
    texto = NOTAS_DESCARTAR.sub("", texto)
    return re.sub(r"\s+", " ", texto).strip()


class Artigo:
    def __init__(self, numero: int, rotulo: str, contexto: str):
        self.numero = numero
        self.rotulo = rotulo  # "5º", "103-A", "1.028"
        self.contexto = contexto  # descricao do titulo/capitulo vigente
        self.unidades: list[str] = []  # caput, incisos, paragrafos, alineas


def estruturar(blocos: list[str], com_adct: bool) -> tuple[list[Artigo], list[Artigo], str]:
    """Separa preambulo (so CF), artigos do corpo e artigos do ADCT (so CF)."""
    corpo: list[Artigo] = []
    adct: list[Artigo] = []
    preambulo = ""
    destino = corpo
    artigo: Artigo | None = None
    titulo_desc = ""
    capitulo_desc = ""
    aguardando_desc = None

    for bruto in blocos:
        texto = _limpa(bruto)
        if not texto or RE_RUIDO.search(texto):
            continue

        if com_adct and RE_ADCT.search(texto):
            destino = adct
            artigo = None
            titulo_desc = capitulo_desc = ""
            aguardando_desc = None
            continue

        # assinatura final: para de anexar ao ultimo artigo (no ADCT da CF a
        # assinatura do corpo vem ANTES do ADCT, que rearma via RE_ADCT acima)
        if RE_FIM.match(texto) and artigo is not None:
            artigo = None
            continue

        if texto.upper().startswith("PREÂMBULO") or texto.upper().startswith("PREAMBULO"):
            aguardando_desc = "preambulo"
            continue
        if aguardando_desc == "preambulo":
            preambulo = texto
            aguardando_desc = None
            continue

        # cabecalho estrutural — a descricao pode vir na MESMA linha
        # ("CAPÍTULO ÚNICO Disposições Gerais") ou no <p> seguinte
        m_h = RE_PARTE.match(texto) or RE_TITULO.match(texto)
        if m_h:
            resto = texto[m_h.end():].strip(" -–—.")
            titulo_desc = _titulo_pt(resto) if resto.isupper() else resto
            capitulo_desc = ""
            aguardando_desc = None if resto else "titulo"
            continue
        m_h = RE_CAPITULO.match(texto)
        if m_h:
            resto = texto[m_h.end():].strip(" -–—.")
            capitulo_desc = _titulo_pt(resto) if resto.isupper() else resto
            aguardando_desc = None if resto else "capitulo"
            continue
        if RE_SECAO.match(texto):
            aguardando_desc = "secao"
            continue

        m = RE_ARTIGO.match(texto)
        if m and len(texto) > 12:  # evita ancoras vazias tipo "Art. 5º" soltas
            numero = int(m.group(1).replace(".", ""))
            rotulo = m.group(1) if "." in m.group(1) else (f"{numero}º" if numero < 10 else str(numero))
            if m.group(2):
                rotulo += "-" + m.group(2)[-1].upper()
            contexto = capitulo_desc or titulo_desc
            artigo = Artigo(numero, rotulo, contexto)
            artigo.unidades.append(texto)
            destino.append(artigo)
            aguardando_desc = None
            continue

        # linha de descricao logo apos TITULO/CAPITULO/Secao
        if aguardando_desc in ("titulo", "capitulo", "secao"):
            if RE_SO_MAIUSCULAS.match(texto) or texto.istitle() or texto[0].isupper():
                desc = _titulo_pt(texto) if texto.isupper() else texto
                if aguardando_desc == "titulo":
                    titulo_desc = desc
                elif aguardando_desc == "capitulo":
                    capitulo_desc = desc
                aguardando_desc = None
                continue
            aguardando_desc = None

        if artigo is not None:
            artigo.unidades.append(texto)

    return corpo, adct, preambulo


def render(artigos: list[Artigo], fonte: str) -> str:
    """Gera os blocos finais com cabecalho de citacao, <= BLOCO_CHARS cada."""
    saida: list[str] = []
    for art in artigos:
        cab = f"{fonte} · Art. {art.rotulo}"
        if art.contexto:
            cab += f" · {art.contexto}"

        bloco: list[str] = []
        tamanho = 0
        parte = 0
        for unidade in art.unidades:
            if bloco and tamanho + len(unidade) > BLOCO_CHARS:
                head = cab if parte == 0 else f"{cab} (continuação)"
                saida.append(head + "\n" + "\n".join(bloco))
                parte += 1
                bloco, tamanho = [], 0
            bloco.append(unidade)
            tamanho += len(unidade) + 1
        if bloco:
            head = cab if parte == 0 else f"{cab} (continuação)"
            saida.append(head + "\n" + "\n".join(bloco))
    return "\n\n".join(saida) + "\n"


def baixar(caminho: str, cache: Path) -> str:
    destino = cache / caminho.replace("/", "__")
    if destino.exists():
        raw = destino.read_bytes()
    else:
        req = urllib.request.Request(
            f"{BASE}/{caminho}", headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read()
        cache.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(raw)
        time.sleep(0.5)  # educacao com o servidor do Planalto
    # paginas do Planalto variam: windows-1252 (maioria), utf-16 com BOM
    # (ex.: Lei 11.340) e utf-8
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    if raw[:3] == b"\xef\xbb\xbf":
        return raw.decode("utf-8-sig", errors="replace")
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return raw.decode("windows-1252", errors="replace")


def texto_bruto(blocos: list[str]) -> str:
    """Fallback: texto integral limpo, para normas onde o parser por artigo falha
    (regulamentos disciplinares em tabela/anexo — ex.: RDE, R-200). Sem cabecalho
    de citacao por artigo; a atribuicao vem do nome do arquivo (a fonte citavel).
    O mrb_alma chunka por tamanho (1800/200)."""
    linhas = []
    for b in blocos:
        t = _limpa(b)
        if t and not RE_RUIDO.search(t):
            linhas.append(t)
    return "\n\n".join(linhas)


def coletar(norma, out_base: Path, cache: Path) -> tuple[int, list[str]]:
    nid, pacote, arquivo, label, caminho, minimo = norma
    html = baixar(caminho, cache)
    parser = ExtratorBlocos()
    parser.feed(html)
    parser.close()

    corpo, adct, preambulo = estruturar(parser.blocos, com_adct=(nid == "cf88"))
    avisos = []
    out = out_base / pacote
    out.mkdir(parents=True, exist_ok=True)

    # fallback de texto bruto: parser por artigo nao pegou (pagina em tabela/anexo)
    # mas ha texto substancial — preserva o conteudo em vez de perder a norma.
    if len(corpo) + len(adct) < 4:
        bruto = texto_bruto(parser.blocos)
        if len(bruto) > 6000:
            (out / f"{arquivo}.md").write_text(
                f"{label} — texto integral\n\n{bruto}\n", encoding="utf-8"
            )
            avisos.append(f"{nid}: TEXTO BRUTO ({len(bruto)} chars) — parser por artigo nao se aplica")
            return max(1, len(bruto) // 1500), avisos

    if len(corpo) < minimo:
        avisos.append(f"{nid}: {len(corpo)} artigos extraidos (< minimo {minimo})")

    doc = render(corpo, label)
    if preambulo:
        doc = f"{arquivo} · Preâmbulo\n{preambulo}\n\n{doc}"
    (out / f"{arquivo}.md").write_text(doc, encoding="utf-8")

    n = len(corpo)
    if adct:
        (out / f"{arquivo} - ADCT.md").write_text(render(adct, f"{label} ADCT"), encoding="utf-8")
        n += len(adct)
    return n, avisos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-base", required=True, help="pasta base dos corpus (ex.: ../corpus)")
    ap.add_argument("--so", help="coleta so uma norma (id do catalogo)")
    ap.add_argument("--pack", help="coleta so as normas de um pacote (ex.: br-licitacoes)")
    ap.add_argument("--cache", default="/tmp/planalto-cache", help="cache dos HTML baixados")
    ap.add_argument("--ignorar-minimos", action="store_true",
                    help="nao falha quando uma norma vier abaixo do minimo esperado")
    args = ap.parse_args()

    normas = [
        n for n in NORMAS
        if (not args.so or n[0] == args.so) and (not args.pack or n[1] == args.pack)
    ]
    if not normas:
        raise SystemExit(f"ERRO: nenhuma norma para so={args.so} pack={args.pack}")

    out_base, cache = Path(args.out_base), Path(args.cache)
    problemas: list[str] = []
    total = 0
    for norma in normas:
        try:
            n, avisos = coletar(norma, out_base, cache)
        except Exception as exc:  # noqa: BLE001 — relatorio no fim
            problemas.append(f"{norma[0]}: {exc}")
            print(f"  ERRO  {norma[0]}: {exc}")
            continue
        problemas.extend(avisos)
        total += n
        flag = " !!" if avisos else ""
        print(f"  {norma[0]:<24} {n:>5} artigos{flag}")

    print(f"\n{len(normas)} norma(s), {total} artigos no total")
    if problemas:
        print("\nPROBLEMAS:")
        for p in problemas:
            print(f"  - {p}")
        if not args.ignorar_minimos:
            raise SystemExit("Coleta abaixo do esperado — o Planalto mudou o HTML? "
                             "Confira antes de empacotar (ou use --ignorar-minimos).")


if __name__ == "__main__":
    main()
