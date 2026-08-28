# Doutor da Roça

Chatbot de WhatsApp que identifica pragas do milho por foto e responde, em linguagem simples, o que é e o que fazer — priorizando as opções mais baratas.

Projeto UPX — Engenharia de Computação, Facens · 2º semestre de 2026

**Integrantes:** Matheus Cravo Purcena Gonçalves · Rafael Henrique dos Reis · Samuel de Moraes Delgado · Victor Rodrigues de Oliveira · Vitor Benavides Pitaluga

---

## O problema

João Batista, 54 anos, planta milho e hortaliças em ~8 ha na região de Sorocaba. Ele perde safra porque não identifica a praga a tempo e não tem dinheiro para pagar visita de agrônomo. O que ele quer é simples: tirar uma foto, mandar num número de WhatsApp e receber uma resposta rápida sobre o que é e como resolver sem gastar muito.

A ficha completa da persona está em [`docs/01-persona.md`](docs/01-persona.md).

## Como funciona

```
foto no WhatsApp → webhook → fila → CNN classifica a praga
                                  ↓
                    roteador de confiança (alta / dúvida / não sei)
                                  ↓
                    RAG busca o manejo em base curada (Embrapa, Epagri, CATI)
                                  ↓
                    LLM apenas REDIGE em linguagem simples → resposta
```

O princípio de projeto é **separar quem decide de quem escreve**: a CNN decide qual é a praga (decisão fechada e mensurável), o RAG busca o manejo em documento técnico curado, e o LLM só traduz o texto para o português do produtor. Nenhum componente generativo escolhe a praga nem inventa produto.

Detalhes em [`docs/02-arquitetura.md`](docs/02-arquitetura.md).

## Escopo

**Cultura:** milho (única, por decisão de escopo do semestre).

**Classes do classificador:**

| Classe | Por que entra |
|---|---|
| `lagarta_cartucho` | Praga nº 1 para quem planta sem semente Bt |
| `lagarta_espiga` | Decisiva para milho verde de feira |
| `vaquinha` | Espécie brasileira, dano visual inconfundível |
| `milho_sadio` | Classe negativa — permite responder "não tem nada aqui" |

Rejeição não é classe treinada: é limiar de confiança. Se o modelo não tem certeza, o bot diz que não sabe e encaminha para a Casa da Agricultura.

**A cigarrinha-do-milho fica fora do classificador de propósito.** É a praga de maior prejuízo do país (R$ 33,6 bi/ano), mas tem 46 fotos públicas no mundo, o sintoma aparece 30 dias depois da infecção e não existe nível de controle. Ela é tratada por regra de calendário, não por imagem. A justificativa está em [`docs/03-panorama-pragas.md`](docs/03-panorama-pragas.md).

**Fora de escopo neste semestre:** previsão climática, drones, app mobile nativo, outras culturas.

## Estrutura

```
docs/
├── 01-persona.md           Ficha da persona e alinhamento de expectativas
├── 02-arquitetura.md       Requisitos, componentes, dados, riscos, cronograma
├── 03-panorama-pragas.md   Embasamento: ocorrência, perdas, níveis de controle
└── 04-guia-dataset.md      Passo a passo para montar o dataset de fotos
kb/
└── fichas-pragas-milho.md  Base de conhecimento que alimenta o RAG
scripts/
├── 01_baixar_gbif.py       Baixa fotos de campo com licença redistribuível
├── 02_limpar_duplicatas.py Remove duplicata, borrão, imagem pequena/corrompida
└── 03_dividir_treino_teste.py  Split por observação, sem vazamento
```

## Como rodar os scripts de dataset

```bash
pip install -r requirements.txt

python scripts/01_baixar_gbif.py --teste          # 5 fotos por classe, para conferir
python scripts/01_baixar_gbif.py --max-por-classe 600

python scripts/02_limpar_duplicatas.py --dir dados/bruto            # simula
python scripts/02_limpar_duplicatas.py --dir dados/bruto --aplicar  # move

python scripts/03_dividir_treino_teste.py
```

O passo a passo completo, com o protocolo de foto para a visita ao produtor, está em [`docs/04-guia-dataset.md`](docs/04-guia-dataset.md).

## Regras do projeto

**Nunca comitar imagens.** A pasta `dados/` está no `.gitignore`. Fotos de terceiros têm licença individual e o repositório não é o lugar delas — o arquivo `dados/creditos.csv` é que registra licença e autor de cada uma.

**Nunca prescrever agrotóxico.** O receituário agronômico é exigência legal no Brasil. O sistema recomenda manejo cultural e biológico livremente; para controle químico, encaminha para a Casa da Agricultura. Isso é decisão consciente de projeto, não limitação técnica.

**Errar para o lado do "não sei".** Dizer "é vaquinha" quando é lagarta faz o produtor comprar o produto errado e perder a lavoura assim mesmo. Dizer "não sei" custa uma ida à Casa da Agricultura. O limiar de confiança é calibrado para ser conservador.

**Reportar os dois números de acurácia.** Um em imagem pública (condição fácil) e outro em foto real de lavoura. A queda entre os dois é resultado, não fracasso.

## Créditos e licença

O conteúdo técnico das fichas em `kb/` é sintetizado a partir de publicações da **Embrapa**, **Epagri**, **Incaper** e **CATI**, com as fontes citadas ao final de cada ficha. Os fatos agronômicos pertencem a essas instituições; a organização e a redação simplificada são deste projeto.

- Código (`scripts/`): licença MIT, ver [`LICENSE`](LICENSE)
- Documentação (`docs/`, `kb/`): CC BY 4.0 — use citando

As imagens baixadas pelos scripts **não** são cobertas por essas licenças: cada foto tem a sua, registrada em `dados/creditos.csv`.
