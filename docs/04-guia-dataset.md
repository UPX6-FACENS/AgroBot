# Passo a passo — montar o dataset de fotos de pragas do milho

**Projeto UPX "Doutor da Roça" · Facens**
Objetivo: sair de zero para um dataset treinável, com licença limpa, em ~3 semanas.

---

## Antes de começar: o levantamento mudou o plano

Fizemos a varredura das fontes públicas. Três achados que precisam ser digeridos antes de qualquer linha de código:

**1. Não existe dataset pronto de pragas brasileiras do milho.** Nenhuma fonte pública tem classe rotulada para cigarrinha (*Dalbulus maidis*), percevejo-barriga-verde (*Dichelops*) ou broca-da-cana (*Diatraea*). O que existe em abundância é lagarta-do-cartucho, porque virou problema global depois que invadiu a África em 2016.

**2. A disponibilidade por espécie é absurdamente desigual.** Contagens medidas ao vivo na API do GBIF (ocorrências com foto, agosto/2026):

| Praga | Fotos no GBIF | 300 imagens é viável? |
|---|---|---|
| Lagarta-do-cartucho (*S. frugiperda*) | 7.911 | ✅ Fácil |
| Lagarta-da-espiga (*Helicoverpa*) | 12.577 + 21.955 | ✅ Fácil |
| Vaquinha (*D. speciosa*) | 2.522 | ✅ Viável |
| Lagarta-elasmo (*E. lignosella*) | 1.010 | ✅ Viável |
| Pulgão-do-milho (*R. maidis*) | 3.388, **mas só 92 de campo** | ⚠️ Difícil |
| **Cigarrinha (*D. maidis*)** | **46 no mundo inteiro** | ❌ Inviável |
| Percevejo-barriga-verde | ~14 | ❌ Inviável |
| Broca-da-cana | **7** | ❌ Inviável |

**3. A praga nº 1 do Brasil é justamente a que a visão computacional não resolve.** A cigarrinha tem 46 fotos públicas, o sintoma dela aparece 30 dias depois da infecção, e não existe nível de controle porque um único inseto infectivo já inutiliza a planta. Ela sai do classificador e entra por regra de calendário — ver `pesquisa-panorama-pragas-milho.md`, §6.

### Decisão de classes (fechar na reunião desta semana)

```
0. lagarta_cartucho     ← nº 1 para o pequeno produtor, milhares de fotos
1. lagarta_espiga       ← decisiva para milho verde de feira, milhares de fotos
2. vaquinha             ← espécie brasileira, dano visual inconfundível
3. milho_sadio          ← classe negativa, obrigatória
   (+ rejeição por limiar de confiança, não é classe treinada)
```

`lagarta_elasmo` fica como **classe 4 opcional**, se sobrar tempo depois que as quatro primeiras estiverem funcionando. Não comece com cinco.

> **Por que `milho_sadio` é obrigatória:** sem ela, o modelo é obrigado a escolher uma praga para toda foto que chegar — inclusive para a foto de uma planta perfeitamente boa. Com ela, "não tem nada aqui" vira uma resposta possível.

---

## Fase 0 — Preparar o terreno (1 hora, uma pessoa)

- [ ] Criar a pasta do dataset **fora** do repositório de código, ou adicionar `dados/` ao `.gitignore`. Imagem em repositório Git é dor de cabeça garantida.
- [ ] `pip install requests tqdm pillow imagehash opencv-python-headless`
- [ ] Copiar os três scripts de `scripts/` para o repositório.
- [ ] Criar a estrutura:

```
dados/
├── bruto/              # fotos públicas baixadas
│   ├── lagarta_cartucho/
│   ├── lagarta_espiga/
│   ├── vaquinha/
│   └── milho_sadio/
├── bruto_campo/        # fotos que VOCÊS tiraram — nunca misturar com bruto/
│   └── (mesmas classes)
├── descartado/         # o que o script 02 rejeitou, com o motivo
├── split/              # saída do script 03, é o que alimenta o treino
└── creditos.csv        # licença e autor de cada foto — o arquivo mais importante
```

> **`creditos.csv` não é burocracia.** Se a banca perguntar "vocês podiam usar essas imagens?", ele é a resposta. Reconstruir depois é inviável. Ele é gerado automaticamente pelo script 01 — só não apague.

---

## Fase 1 — Baixar a base pública (meio dia, uma pessoa)

### 1.1 GBIF — a espinha dorsal

Comece por aqui. É API pública, sem chave, sem conta, com licença declarada por registro.

```bash
python scripts/01_baixar_gbif.py --teste          # 5 por classe, confere se funciona
# olhe as fotos baixadas com os próprios olhos
python scripts/01_baixar_gbif.py --max-por-classe 600
```

Dois detalhes do script que **não devem ser mexidos**:

- `basisOfRecord=HUMAN_OBSERVATION` — sem esse filtro, 94% do que vem de pulgão é espécime de museu montado em alfinete, fundo branco. O modelo aprenderia o fundo branco.
- Resolução do `taxonKey` pela API em vez de nome fixo — `Elasmopalpus lignosellus` retorna **zero** resultados no GBIF; o nome aceito é `lignosella`. Chutar nome científico é como o dataset silenciosamente vem vazio.

O filtro de licença está em `CC0_1_0` e `CC_BY_4_0`. Se faltar volume e vocês decidirem **não publicar** o dataset, dá para acrescentar `CC_BY_NC_4_0` e o volume mais que quintuplica — mas aí o dataset não pode ir para o GitHub. Decidam isso conscientemente e escrevam a decisão no relatório.

### 1.2 KaraAgro AI Maize — o reforço de lagarta-do-cartucho

[Harvard Dataverse, DOI 10.7910/DVN/CXUMDS](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/CXUMDS)

16.552 imagens de campo com bounding box, da Universidade de Gana, com classes separadas de **larva, ovo, frass (excremento) e dano de lagarta-do-cartucho** — exatamente os quatro sinais que o produtor fotografa. A licença aparece como **CC0** (domínio público) na ficha de terceiros; **confirmem na página do Dataverse antes de usar**, porque não conseguimos abrir a fonte primária.

Como aproveitar: recortem as imagens pelas caixas de anotação para gerar fotos centradas no inseto, no mesmo estilo das do GBIF. Sem o recorte, as duas fontes têm enquadramento muito diferente e o modelo aprende a distinguir fonte, não praga.

### 1.3 Roboflow Universe — caixas prontas, se quiserem

- [Maize Pest](https://universe.roboflow.com/526/maize-pest) — 2.311 imagens, CC BY 4.0
- [Detection of Fall Armyworm Infestation](https://universe.roboflow.com/baltazar-mu/detection-of-fall-armyworm-infestation-with-deep-learning) — ~4,5k, CC BY 4.0, com estágios FAW_Day1/2/3

Exige conta gratuita e API key. Ressalva honesta: são uploads de alunos e parte do conteúdo é recorte de Google Imagens relicenciado indevidamente. Trate como CC-BY *declarada*, não *garantida*, e prefira usar como complemento.

### 1.4 Bugwood / IPM Images — o tapa-buraco

[ipmimages.org](https://www.ipmimages.org) — 332 mil imagens, acervo de extensionistas e entomologistas, rótulo de espécie confiável. É a única fonte com cobertura fotográfica real das espécies raras. A licença é **por imagem** (CC-BY 3.0 US ou CC-BY-NC 3.0 US) e cada foto exige a linha de crédito `Nome, Instituição, Bugwood.org`. Uso acadêmico com crédito está claramente permitido; **redistribuição em massa não é segura**. Baixem manualmente algumas centenas, anotando o crédito.

### 1.5 O que NÃO usar

| Fonte | Por quê |
|---|---|
| **PlantVillage** | Só doença foliar, nenhum inseto. E as fotos são folha destacada sobre fundo cinza uniforme — existe artigo publicado sobre o viés desse dataset (*"Uncovering bias in the PlantVillage dataset"*). Use como contraexemplo no relatório, não como dado. |
| **IP102** | Nenhuma das nossas espécies aparece nominalmente. O "Army worm" dele é provavelmente *Mythimna separata*, praga chinesa. Além disso a licença é "free for academic usage" — termo próprio, **não autoriza redistribuição**. |
| **Google Imagens / raspagem** | Sem licença rastreável. Não use, mesmo que "todo mundo usa". |
| **Zindi/Makerere FAW** | Licença não declarada. |

---

## Fase 2 — Limpar (2 horas, uma pessoa)

```bash
python scripts/02_limpar_duplicatas.py --dir dados/bruto             # simula
python scripts/02_limpar_duplicatas.py --dir dados/bruto --aplicar   # move
```

O script remove imagem corrompida, menor que 224 px, borrada (variância do Laplaciano) e duplicata (hash perceptual). Nada é apagado — vai para `dados/descartado/<motivo>/`.

**Depois de rodar, abram `dados/descartado/borrada/` e olhem.** Se tiver foto boa lá, o limiar está severo demais; se sobrou foto ruim no dataset, está frouxo. Esse limiar depois vira o "porteiro de qualidade" do bot, que decide se pede outra foto ao João — então calibrar aqui já é trabalho adiantado.

### Curadoria manual — a parte chata que ninguém pula

Depois do script, **alguém precisa olhar foto por foto**. Duas pessoas, duas horas cada, com uma regra simples: *"se eu, olhando essa foto, não conseguiria dizer qual é a praga, o modelo também não vai"*.

Descartem: desenho e ilustração, mariposa morta em parede branca, foto de armadilha luminosa, inseto ocupando menos de ~5% do quadro, e qualquer coisa em que a identificação dependa de saber o contexto e não de ver o bicho.

> **Regra que vale ouro: nunca misture fundo de laboratório com foto de campo dentro da mesma classe.** Se a classe A tem muita foto de estúdio e a B só de campo, o modelo aprende a distinguir fundo. É o erro do PlantVillage e é fácil de cometer sem perceber.

---

## Fase 3 — Fotografar em campo (a visita ao João)

**Esta fase é o diferencial do trabalho de vocês.** Todo mundo baixa dataset público; quase ninguém traz foto real da lavoura da persona. 50 fotos tiradas com o celular do João no sol das 11h valem mais, para a defesa, que 500 de laboratório.

### Antes de ir

- [ ] Termo de consentimento impresso, para uso das fotos no trabalho acadêmico (LGPD)
- [ ] Cartelas impressas com as pragas-alvo, para mostrar e ele reconhecer
- [ ] Régua ou moeda de R$ 1 para dar escala em algumas fotos
- [ ] Saco plástico e pote, se ele deixar coletar um exemplar
- [ ] Bateria carregada e espaço no celular
- [ ] Combinado de horário: **manhã cedo ou fim de tarde**, quando a luz não estoura o branco. Mas tirem algumas ao meio-dia também — é quando ele vai fotografar de verdade.

### Protocolo de foto (colar no grupo do WhatsApp)

Para **cada** ocorrência encontrada, tirar **5 fotos**:

1. **Contexto** — a planta inteira, de pé, mostrando onde está o problema
2. **Média distância** — a folha ou o cartucho, ocupando o quadro
3. **Perto** — o inseto ou o dano, o mais perto que o celular focar
4. **Perto com escala** — a mesma cena com a moeda ao lado
5. **Ângulo diferente** — a mesma cena de outro lado ou com outra luz

E variar de propósito, porque a foto do João vai ser assim:

- [ ] algumas com sol forte, sombra dura
- [ ] algumas nubladas ou na sombra
- [ ] algumas com a folha molhada de orvalho
- [ ] algumas tremidas ou desfocadas — **guardem essas**, elas testam o porteiro de qualidade
- [ ] algumas com fundo bagunçado (mato, terra, outra planta atrás)
- [ ] algumas de plantas sadias, para a classe `milho_sadio`

### Nomear na hora

`classe_data_local_numero.jpg` → `lagarta_cartucho_2026-09-12_joao_007.jpg`

Se ficar para depois, ninguém lembra o que era. Se houver dúvida sobre a identificação, o nome vai com `_DUVIDA` e alguém confirma depois com a Casa da Agricultura — **foto com rótulo errado é pior que foto faltando**.

### Onde as fotos de campo vão

Em `dados/bruto_campo/`, **nunca** em `dados/bruto/`. Elas têm destino diferente na fase 4.

> **Se o João topar, o melhor caminho é ele mesmo fotografar** — pelo celular dele, do jeito dele, e mandar no WhatsApp. Isso resolve duas coisas de uma vez: gera dado com a distribuição real de entrada do sistema, e já testa se ele consegue e quer usar o fluxo.

### Plano B para as classes raras

Se faltar imagem de alguma classe, escrevam pedindo autorização:

- **Embrapa Milho e Sorgo** (Sete Lagoas/MG) — o banco de imagens deles tem *Dalbulus maidis*, *Spodoptera* e outras, em português. A licença não é pública, mas pedido acadêmico de graduação costuma ser deferido. É um e-mail curto.
- **Prof. Díbio Borges (UnB)** — o grupo dele publicou *"A Deep Learning Model for Recognition of Pest Insects in Maize Plantations"* (IEEE SMC 2019) com dataset de campo de pragas do milho **que nunca foi publicado**. Vale pedir.

Mandem os dois e-mails **na semana 2**, não na semana 8 — resposta institucional demora.

---

## Fase 4 — Dividir sem vazamento (30 minutos)

```bash
python scripts/03_dividir_treino_teste.py
```

Duas regras que o script implementa e que precisam ser entendidas, não só executadas:

**1. Split por observação, não por foto.** Uma observação do iNaturalist tem de 2 a 5 fotos do mesmo inseto, tiradas no mesmo minuto. Se duas caem em treino e teste, o modelo já viu a resposta. Por isso o script agrupa pelo prefixo do nome do arquivo, que é a chave da ocorrência.

**2. Toda foto de campo vai para o teste.** Nenhuma entra no treino. Isso dá dois números:

| Conjunto | O que mede |
|---|---|
| `teste` | acurácia em imagem pública, condição fácil |
| `teste_campo` | **acurácia em foto real de lavoura — o número que importa** |

Esperem uma queda significativa entre um e outro. **Isso não é fracasso, é o achado do trabalho.** Reportem os dois e expliquem a queda (fundo, luz, escala, distância). Um trabalho que mostra a queda e a explica vale mais que um que reporta só o número bonito — e a banca sabe disso.

---

## Fase 5 — Aumentar os dados (dentro do treino)

Augmentation entra no `DataLoader`, não em arquivo no disco — e **só no treino**, nunca em validação ou teste.

Transformações que fazem sentido aqui, porque simulam a foto ruim que vai chegar:

- rotação até ±30°, flip horizontal
- brilho e contraste ±30% (sol forte × sombra)
- desfoque gaussiano leve (mão trêmula)
- recorte aleatório 80–100% (distância variável)
- ruído leve (câmera ruim, pouca luz)

O que **não** fazer: flip vertical (planta não fica de cabeça para baixo) e distorção de cor agressiva (a cor da lagarta é informação — verde clara quando nova, escura quando grande).

---

## Fase 6 — Checklist antes de treinar

- [ ] Pelo menos 250 imagens por classe após limpeza
- [ ] Nenhuma classe com mais que ~3× a menor (senão use class weights)
- [ ] `creditos.csv` completo, com licença e autor de cada foto
- [ ] Fundo de laboratório e fundo de campo não misturados dentro da mesma classe
- [ ] Split feito por observação, verificado à mão em uma classe
- [ ] Fotos de campo **só** em `teste_campo`
- [ ] Alguém que não montou o dataset olhou 50 imagens aleatórias e concordou com os rótulos
- [ ] As fotos borradas de propósito estão guardadas para testar o porteiro de qualidade
- [ ] Uma pasta `exemplos_dificeis/` com os casos que confundem até vocês — é o que vai virar a seção de análise de erro

---

## Cronograma desta frente

| Semana | O quê | Quem |
|---|---|---|
| 1 | Fase 0 e 1.1 (GBIF rodando). E-mails para Embrapa e UnB **enviados** | 1 pessoa |
| 2 | **Visita ao João** + fase 3. KaraAgro baixado e recortado | Todos na visita, 1 no KaraAgro |
| 3 | Fase 2 (limpeza + curadoria manual a quatro olhos) e fase 4 | 2 pessoas |
| 4 | Primeiro treino, matriz de confusão, análise de erro | 1 pessoa |

Se a semana 4 fechar com matriz de confusão em mãos, mesmo feia, a frente de dados está no prazo. Matriz feia na semana 4 é ótimo — significa que sobram 8 semanas para melhorar.

---

## Os cinco erros que matam este tipo de projeto

1. **Deixar o `creditos.csv` para depois.** Não tem depois.
2. **Misturar fundo de estúdio com foto de campo.** O modelo aprende o fundo e a acurácia mente.
3. **Split por foto em vez de por observação.** Acurácia inflada que desaba em campo.
4. **Começar com muitas classes.** Três classes boas batem cinco ruins, e classe nova é fácil de acrescentar.
5. **Não ir a campo.** Sem foto real, vocês não têm como saber se o modelo funciona — e a banca vai perguntar exatamente isso.
