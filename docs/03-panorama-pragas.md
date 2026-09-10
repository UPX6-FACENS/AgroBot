# Panorama de pragas do milho — embasamento do projeto

**Projeto UPX "Doutor da Roça" · Facens · agosto de 2026**
Cultura fixada para o MVP: **milho**. Persona: João Batista, 54 anos, pequeno produtor de hortaliças e milho na região de Sorocaba.

Este documento é o embasamento do relatório e a justificativa das escolhas de projeto. As fichas de manejo (o conteúdo que o bot responde) estão em `kb/fichas-pragas-milho.md`.

---

## 1. O ranking nacional não vale para o João — e isso é uma descoberta do trabalho

Existem dois rankings diferentes de pragas do milho, e confundir os dois é o erro mais provável deste projeto.

**Ranking por prejuízo agregado no Brasil (o que sai na imprensa):**

1. **Cigarrinha-do-milho** (*Dalbulus maidis*) e os enfezamentos que ela transmite
2. Lagarta-do-cartucho (*Spodoptera frugiperda*)
3. Percevejo-barriga-verde (*Dichelops* spp.)
4. Lagarta-da-espiga (*Helicoverpa* spp.)

**Ranking para quem planta 5–10 ha sem semente Bt e sem trator:**

1. **Lagarta-do-cartucho** — sem Bt, ele enfrenta 100% da pressão da praga
2. **Cigarrinha** — mas sem defesa individual possível (ver §4)
3. **Lagarta-da-espiga e mosca-da-espiga** — decisivas se o destino for milho verde de feira
4. **Lagarta-elasmo** — perda de estande, cara em área pequena
5. Vaquinha / larva-alfinete
6. Cigarrinha-das-pastagens, se o milho fizer divisa com braquiária

A inversão acontece porque as duas maiores defesas do produtor tecnificado — **semente Bt** e **tratamento industrial de semente** — são exatamente o que o pequeno produtor não tem. O Bt contém a lagarta na própria planta; o tratamento de semente protege os primeiros ~18 dias, que é a janela crítica da cigarrinha e dos percevejos.

> **Para o relatório:** o Censo Agropecuário 2017 mostra que a agricultura familiar é 77% dos estabelecimentos, mas só ~20% recebiam orientação técnica. Quem mais precisa de critério de decisão é quem menos tem acesso a ele. É exatamente o buraco que o projeto tenta preencher.

---

## 2. Números de perda (todos com fonte)

### Cigarrinha-do-milho — o maior número do setor

Estudo **CNA + Embrapa + Epagri**, publicado em **abril de 2026** na revista *Crop Protection*:

| Indicador | Valor |
|---|---|
| Prejuízo acumulado (safras 2020/21 a 2023/24) | **US$ 25,8 bilhões** (~R$ 133 bi) |
| Prejuízo anual | **US$ 6,5 bi / R$ 33,6 bi** |
| Redução média de produção | **22,7%** |
| Volume perdido | **31,8 milhões de toneladas/ano** |
| Produtores relatando impacto relevante | **79,4%** |
| Aumento no custo de aplicação de inseticida (2020/21 → 2023/24) | **+19%**, passando de US$ 9/ha |
| Perda em cultivar suscetível sob alta infecção | **mais de 70%** |

### Lagarta-do-cartucho

| Fonte | Perda de produtividade |
|---|---|
| Embrapa, Circular Técnica 208 | **34% a 52%** |
| Incaper, Boletim Técnico nº 6 | **17% a 38,7%** |
| Revista Cultivar | **20% a 50%**; até **60%** em milho doce |

### Demais

| Praga | Perda | Fonte |
|---|---|---|
| *Diatraea saccharalis* | 21% a 27% | Embrapa CT 208 |
| *Dichelops furcatus* | 11,5% por percevejo/metro; 50% a 7,25 percevejos/m | Chiaradia et al., 2016 |
| *Leptoglossus zonatus* | 15% | Epagri BT 170 |
| *Deois flavopicta* | 4 cigarrinhas/planta podem matar a planta (até 17 dias) | Embrapa |

**Não encontrado:** custo de controle por hectare por praga, consolidado e atualizado. O único dado publicado é o custo de aplicação contra cigarrinha (> US$ 9/ha) e a referência metodológica de R$ 80/ha usada no cálculo de nível de dano econômico do *Dichelops* (Epagri, 2016 — desatualizada como valor absoluto).

---

## 3. Calendário de ocorrência em São Paulo

**Safra de verão:** semeadura de setembro a dezembro, colheita de fevereiro a abril.
**Safrinha:** pelo Zarc, em SP o plantio vai do fim de dezembro ao início de março (Avaré, Paranapanema, São Carlos, Manduri como referências).

| Praga | Verão | Safrinha | Diferença |
|---|---|---|---|
| **Cigarrinha** | população baixa (~1/planta de maio a fevereiro) | **pico em março e abril — de 1 para mais de 10 insetos por cartucho** | Diferença brutal. Plantio tardio emerge no pico populacional |
| **Lagarta-do-cartucho** | importante | pressão maior | Na safrinha o limiar recomendado é o mais rigoroso (10%) |
| **Lagarta-elasmo** | menor | maior | Explode em veranico; ligada a calor e seca |
| **Percevejo-barriga-verde** | menor | maior | Migra da soja colhida para o milho recém-emergido |
| **Pulgão-do-milho** | secundário | maior | Ganhou importância com a safrinha |
| **Cigarrinha-das-pastagens** | pico dez–fev | comum | "Rara na primeira safra" (Embrapa CT 175) |

**Regra que emerge dos dados:** em SP, **quanto mais tarde se planta a safrinha, pior**. Plantio de janeiro escapa parcialmente; plantio de março pega o pico da cigarrinha e o período seco que favorece elasmo e pulgão ao mesmo tempo.

> **Uso no produto:** isso é uma regra de calendário, não de imagem. O bot pode alertar o João no momento do plantio — sem ele precisar fotografar nada. Ver §4 e §6.

---

## 4. Níveis de controle — a tecnologia mais barata que existe

Este é o achado mais aproveitável do levantamento. Existe critério **numérico, objetivo e gratuito** para decidir se trata ou não, e ele funciona melhor em área pequena do que em área grande, porque dá para caminhar a lavoura inteira.

| Praga | Nível de controle | Fonte |
|---|---|---|
| Lagarta-do-cartucho, até 30 dias após emergência | **20% das plantas com raspagem** | Epagri BT 170 |
| Lagarta-do-cartucho, dos 30 aos 60 dias | **10% das plantas atacadas** | Epagri BT 170 |
| Lagarta-do-cartucho na safrinha | **10% como padrão, inclusive na fase inicial** | Revista Cultivar |
| Lagarta-do-cartucho, plantas cortadas | **2% a 3% — intervir imediatamente** | Revista Cultivar |
| Lagarta-elasmo | **mais de 5% das plantas** com lagarta | Epagri BT 170 |
| Percevejo-barriga-verde (*D. furcatus*) | **0,5 percevejo por metro de linha** | Epagri BT 170 |
| Vaquinha / larva-alfinete | **3,5 larvas por planta** ou 20 larvas/m² | Epagri BT 170 |
| Pulgão-do-milho | **>100 pulgões em ≥50% das plantas** até o pré-florescimento | Epagri BT 170 |
| Lagarta-da-espiga, broca-da-cana, lagarta-rosca | **não estabelecidos** — lacuna real da pesquisa, não da busca | Epagri BT 170 |

### A cigarrinha é o contraexemplo — e isso é decisivo para a arquitetura

**Não existe nível de controle para *Dalbulus maidis*, e não é lacuna de pesquisa: é consequência da biologia.** O dano não vem da alimentação do inseto, vem dos patógenos que ele inocula — **uma única cigarrinha infectiva pode inutilizar uma planta**. O sintoma só aparece ~30 dias depois da infecção, quando não há mais o que fazer.

Consequência para o projeto: **a cigarrinha não pode ser tratada por foto.** Não há sinal visual precoce para fotografar. A lógica correta é preventiva e por janela fenológica (proteger de VE até ~V5), e as medidas que funcionam — eliminar milho tiguera, sincronizar épocas de plantio, monitorar em conjunto — são **coletivas e regionais**, fora do alcance individual de quem tem 8 ha cercado por lavouras de terceiros.

---

## 5. Acontecimentos recentes (2024–2026)

**Resistência da cigarrinha a inseticidas (ESALQ/USP, 2025).** Trabalho de Dias et al. em *Pest Management Science* documentou resistência a piretroides (bifentrina, lambda-cialotrina) e neonicotinoides (imidacloprido, acetamiprido), com **resistência cruzada superior a 200 vezes** entre grupos químicos diferentes e razão de resistência ao imidacloprido de 1.397 a 8.871 vezes. Boa notícia: a resistência é **instável** — sem pressão de inseticida caiu de 1.397 para 105 vezes ao longo das gerações, ou seja, rotação de grupos e janelas sem aplicação revertem parte do problema. O IRAC-BR publicou boletim técnico específico.

O detalhe amargo: o manejo oficialmente recomendado da cigarrinha é calendarizado e preventivo — exatamente o padrão de uso que mais seleciona resistência.

**Resistência da lagarta-do-cartucho ao milho Bt.** Tese da UFV (2019) documentou resistência a Cry1A.105 + Cry2Ab em populações brasileiras de campo, com herança recessiva e — o dado mais preocupante — populações de 2017 que mantiveram a resistência **estável por 12 gerações sem pressão de seleção e sem custo adaptativo**, indicando fixação genética. Relatos de campo da safrinha 2025 no Cerrado descrevem infestação mesmo em híbridos Bt e **6 a 7 aplicações de inseticida** em algumas áreas.

*Ressalva honesta:* não localizamos alerta oficial de órgão governamental declarando quebra formal de resistência de um evento Bt específico. O que existe é literatura revisada por pares mais relatos da imprensa técnica. Não localizamos estudo documentando resistência de campo a **Vip3Aa** no milho no Brasil — é o ativo que resta.

**Ações regulatórias.** O Paraná tornou obrigatória a eliminação do milho tiguera (Portaria Adapar 133/2023), com campanha estadual coordenada. Santa Catarina mantém o **Monitora Milho SC** (Epagri), com boletins públicos ao longo da safra — o monitoramento público mais estruturado do país. Em São Paulo encontramos apenas material informativo da CDA-SP (2022); **não localizamos portaria estadual instituindo vazio sanitário ou eliminação compulsória de tiguera** — vale confirmar direto na CDA-SP.

**O conceito de "ponte verde".** Todas as recomendações oficiais convergem para o mesmo ponto: *Dalbulus maidis* não sobrevive sem milho vivo. A sucessão milho verão → safrinha → tiguera → verão mantém vetor e patógeno o ano inteiro. A CNA registra que uma perda de colheita considerada aceitável (**1,5 saca/ha**) já basta para gerar população relevante de plantas voluntárias.

---

## 6. O que isso muda no projeto — três decisões

### Decisão 1: as classes do classificador não são as pragas mais importantes

São as pragas que (a) o produtor consegue fotografar, (b) têm sinal visual precoce, e (c) têm imagem pública suficiente para treinar. Cruzando os três critérios com o levantamento de imagens (ver [`04-guia-dataset.md`](04-guia-dataset.md)):

| Praga | Importa para o João? | Tem sinal visual precoce? | Tem imagem pública? | Entra? |
|---|---|---|---|---|
| Lagarta-do-cartucho | Sim, nº 1 | Sim, e muito característico | Milhares | ✅ **Sim** |
| Lagarta-da-espiga | Sim, para milho verde | Sim, na espiga | Milhares | ✅ **Sim** |
| Vaquinha (adulto) | Média | Sim, furo redondo na folha | ~500–2.500 | ✅ **Sim** |
| Lagarta-elasmo | Sim | Sim, "coração morto" | ~950 | ⚠️ Opcional |
| **Cigarrinha** | **Sim, nº 1 do país** | **Não — sintoma 30 dias tarde** | **46 fotos no mundo** | ❌ **Não** |
| Percevejo-barriga-verde | Média | Sim | ~14 fotos | ❌ Não |
| Broca-da-cana | Baixa | Não (dentro do colmo) | 7 fotos | ❌ Não |

### Decisão 2: a cigarrinha entra por outro caminho — e isso vira o diferencial do trabalho

Já que ela não pode ser diagnosticada por foto, o bot a trata por **regra de calendário**: quando o João avisar que plantou (uma mensagem, uma data), o sistema abre a janela crítica VE–V5 e o alerta nos dias certos, sem depender de nenhuma imagem.

Isso é arquiteturalmente interessante e vale destacar na banca: **o sistema tem duas lógicas de decisão opostas rodando lado a lado** — uma reativa e visual (a CNN, acionada pela foto) e uma proativa e temporal (a regra de janela, acionada pelo calendário). A praga nº 1 do país é justamente a que a visão computacional não resolve, e reconhecer isso é mais valioso do que fingir que resolve.

### Decisão 3: o nível de controle vira funcionalidade, não só texto

O critério "20% das plantas com raspagem" é uma tecnologia gratuita que cabe numa conversa de WhatsApp. Depois de identificar a lagarta-do-cartucho, o bot pode conduzir a amostragem:

> *"Caminhe em zigue-zague e olhe 10 plantas em 10 pontos diferentes. Quantas estavam com a folha raspada? Me manda só o número."*
> → João responde "18"
> → *"18 de 100 é menos que 20. Ainda não compensa tratar. Olhe de novo em 3 dias."*

Custo computacional: zero. Valor para o produtor: substitui a pulverização por calendário — que gasta produto e seleciona resistência — por pulverização por decisão. E resolve, dentro do escopo, o problema que o João descreveu: ele não sabe **quando** agir.

---

## 7. Lacunas declaradas

Registro do que procuramos e não encontramos, para não induzir a erro no relatório:

1. Custo de controle por hectare por praga, consolidado e atualizado.
2. Dados de perda por praga específicos do estado de São Paulo (o IEA/SAA-SP traz área, produção e produtividade, sem desagregar por praga).
3. Portaria de vazio sanitário do milho em São Paulo — existe no Paraná, não localizada em SP.
4. Níveis de controle para *Helicoverpa*, *Diatraea*, *Agrotis* e *Leptoglossus* em milho — a Epagri declara explicitamente que não estão estabelecidos.
5. Alerta oficial de quebra de resistência a evento Bt específico (2024–2026).
6. Estudo documentando resistência de campo a Vip3Aa no milho no Brasil.
7. Levantamento estadual sistemático do Instituto Biológico ou do IAC sobre pragas do milho em SP.

---

## Fontes

**Embrapa**
- [Manejo Integrado de Pragas na Cultura do Milho — Circular Técnica 208](https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1017489/1/circ208.pdf)
- [Insetos sugadores em milho Bt — Circular Técnica 175](https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/945323/1/circ175.pdf)
- [Controle de Pragas no Cultivo do Milho Verde — Cap. 8](https://www.alice.cnptia.embrapa.br/alice/bitstream/doc/487233/1/Controlepragas.pdf)
- [Bioecologia e controle de Spodoptera frugiperda em milho — Documentos 344](https://www.infoteca.cnptia.embrapa.br/bitstream/doc/935552/1/Documento344.pdf)
- [Flutuação populacional de Dalbulus maidis no CNPMS](https://ainfo.cnptia.embrapa.br/digital/bitstream/item/41320/1/Monitoramento-mosca.pdf)
- [Cigarrinha e enfezamentos do milho desafiam produtores](https://www.embrapa.br/en/busca-de-noticias/-/noticia/65316124/cigarrinha-e-enfezamentos-do-milho-desafiam-produtores-que-devem-seguir-recomendacoes-de-manejo)

**Estudo de perdas da cigarrinha (CNA / Embrapa / Epagri, *Crop Protection*, 2026)**
- [CNA, Embrapa e Epagri estimam perdas de US$ 25,8 bilhões](https://www.cnabrasil.org.br/noticias/cna-embrapa-e-epagri-estimam-perdas-de-us-25-8-bilhoes-provocadas-pela-cigarrinha-do-milho)
- [Praga do milho provoca prejuízo de R$ 33,6 bilhões por ano — Agência Brasil, 07/04/2026](https://agenciabrasil.ebc.com.br/economia/noticia/2026-04/principal-praga-do-milho-provoca-prejuizo-de-r-336-bilhoes-por-ano)
- [Manejo do milho tiguera para reduzir danos da cigarrinha — CNA](https://www.cnabrasil.org.br/noticias/manejo-do-milho-tiguera-para-reduzir-danos-da-cigarrinha-do-milho)

**Epagri — níveis de controle e monitoramento**
- [Pragas e Doenças do Milho — Boletim Técnico nº 170](https://ciram.epagri.sc.gov.br/ciram_arquivos/agroconnect/boletins/BT_PragasDoencasMilho.pdf)
- [Nível de dano econômico de Dichelops furcatus em milho — Chiaradia et al., 2016](https://publicacoes.epagri.sc.gov.br/rac/article/download/93/29)
- [Programa Monitora Milho SC](https://www.epagri.sc.gov.br/monitoramento-da-cigarrinha-do-milho/)

**Resistência**
- [Bifenthrin resistance in Dalbulus maidis — Dias et al., *Pest Management Science*, 2025](https://scijournals.onlinelibrary.wiley.com/doi/10.1002/ps.8848)
- [Boletim IRAC Brasil sobre resistência de Dalbulus maidis](https://irac-online.org/new-technical-bulletin-on-the-evolution-of-resistance-of-dalbulus-maidis-from-itrac-brazil/)
- [Resistência ao milho Bt Cry1A.105 + Cry2Ab em Spodoptera frugiperda — UFV, 2019](https://locus.ufv.br/items/662c80dd-833f-4587-bcb9-033a5b75f929/full)
- [Cross-crop resistance of Spodoptera frugiperda selected on Bt maize — *Scientific Reports*](https://www.nature.com/articles/s41598-020-67339-1)

**Panorama 2025–2026**
- [Lagartas desafiam milho safrinha 2025 no Cerrado — Portal do Agronegócio, 06/03/2026](https://www.portaldoagronegocio.com.br/agricultura/pragas-e-doencas/noticias/lagartas-desafiam-milho-safrinha-2025-no-cerrado-e-alertam-para-risco-de-quebra-de-resistencia-bt)
- [Agrodefesa (GO) orienta produtores sobre os enfezamentos](https://goias.gov.br/agrodefesa/agrodefesa-orienta-produtores-sobre-acoes-para-diminuir-a-incidencia-dos-enfezamentos-transmitidos-pela-cigarrinha-do-milho/)

**São Paulo**
- [Enfezamentos do milho — Defesa Agropecuária SP, informativo nº 011 (2022)](https://www.defesa.agricultura.sp.gov.br/informativo/defesa-agrosp-no-011-julho2022/enfezamentos-do-milho/)
- [Zarc — melhor período para plantar milho safrinha em SP](https://www.agrolink.com.br/noticias/saiba-o-momento-de-plantar-milho-safrinha-em-sp_436885.html)
- [CATI — Coordenadoria de Assistência Técnica Integral](https://agricultura.sp.gov.br/cati/)

**Pequena escala / agricultura familiar**
- [Manejo da lagarta-do-cartucho — Incaper, Boletim Técnico nº 6](https://biblioteca.incaper.es.gov.br/digital/bitstream/123456789/4192/1/Boletim-Tecnico-N6.pdf)
- [Resistência de milho crioulo à lagarta-do-cartucho — UFMT, Cadernos de Agroecologia](https://cadernos.aba-agroecologia.org.br/cadernos/article/download/6974/5100/30039)
- [Nim e Bt subsp. aizawai no manejo da lagarta-do-cartucho — Ciência Rural / SciELO](https://www.scielo.br/j/cr/a/bctL8YQ5CdrbBdskG3DK94t/?lang=pt)
- [Controle biológico de pragas e técnicas alternativas — Embrapa, 2021](https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1133548/1/Controle-biolo769gico-de-pragas-2021.pdf)

**Revista Cultivar**
- [Monitoramento e controle da cigarrinha Dalbulus maidis](https://revistacultivar.com.br/artigos/monitoramento-e-controle-da-cigarrinha-dalbulus-maidis-na-cultura-do-milho)
- [Cartuchos no alvo: estratégias de manejo da lagarta do cartucho](https://revistacultivar.com.br/artigos/cartuchos-no-alvo-estrategias-de-manejo-da-lagarta-do-cartucho-no-milho)
