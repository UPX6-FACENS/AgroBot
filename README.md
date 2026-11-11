# Agrobot

Chatbot de WhatsApp que identifica pragas do milho por foto e responde, em linguagem simples, o que é e o que fazer — priorizando as opções mais baratas.

Projeto UPX — Engenharia de Computação, Facens · 2º semestre de 2026

**Integrantes:** Matheus Gonçalves Purcena Cravo · Murilo Antunes Garcia · Rafael Henrique dos Reis · Samuel de Moraes Delgado (líder) · Victor de Oliveira Rodrigues · Vitor Benavides Pitaluga

**Orientador:** Prof. Lucas Monteiro

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

| Classe | Por que entra | Dataset atual (pós-limpeza) |
|---|---|---|
| `lagarta_cartucho` | Praga nº 1 para quem planta sem semente Bt | 2.943 (GBIF larva + KaraAgro AI Maize) |
| `lagarta_espiga` | Decisiva para milho verde de feira | 351 (GBIF, incl. licença CC BY-NC p/ uso local) |
| `vaquinha` | Espécie brasileira, dano visual inconfundível | 458 (GBIF) |
| `milho_sadio` | Classe negativa — permite responder "não tem nada aqui" | 627 (KaraAgro AI Maize, fotos de campo rotuladas "healthy") |

São **quatro classes** treinadas hoje. `lagarta_elasmo` (*Elasmopalpus lignosella*) foi avaliada e **descartada por falta de dado real**, não por suposição: o GBIF não tem nenhuma foto de larva dela com licença aberta (mesmo testando com licença CC BY-NC ampliada), e a única fonte alternativa encontrada (anotação de estágio de vida da API do iNaturalist) rendeu só 17 imagens utilizáveis — abaixo de qualquer limiar de treino confiável. Isso já satisfaz o critério de corte que o grupo tinha combinado ("se não tiver dado, a classe sai") — só que a decisão veio antes da matriz de confusão da semana 4, na fase de coleta mesmo. Fica documentada em `docs/04-guia-dataset.md` e pode ser revisitada se aparecer mais volume (ex.: fotos de campo reais).

`milho_sadio` não tinha fonte pública direta — resolvida com o **KaraAgro AI Maize** (Harvard Dataverse, DOI 10.7910/DVN/CXUMDS, CC BY): a categoria "healthy" do dataset são fotos de campo de milharal saudável já rotuladas, sem precisar da rota original (ocorrências de *Zea mays* no GBIF + curadoria manual pesada).

Rejeição não é classe treinada: é limiar de confiança. Se o modelo não tem certeza, o bot diz que não sabe e encaminha para a Casa da Agricultura.

**A cigarrinha-do-milho fica fora do classificador de propósito.** É a praga de maior prejuízo do país (R$ 33,6 bi/ano), mas tem 46 fotos públicas no mundo, o sintoma aparece 30 dias depois da infecção e não existe nível de controle. Ela é tratada por regra de calendário, não por imagem. A justificativa está em [`docs/03-panorama-pragas.md`](docs/03-panorama-pragas.md).

**Fora de escopo neste semestre:** previsão climática, drones, app mobile nativo, outras culturas.

## Resultados (conjunto de teste, 710 fotos que o treino nunca viu)

| Métrica | Valor |
|---|---|
| Acurácia geral | **86,3%** (chutar sempre a classe maior daria 65,4%) |
| F1-macro (métrica principal) | **81,4%** |
| Respostas diretas (confiança ≥ 80%) | 77,5% das fotos, com **93,1%** de acerto |
| Erros do modelo segurados pelo roteador | **60,8%** viram "manda outra foto" em vez de recomendação errada |
| Tempo do modelo (CPU, sem LLM) | ~8 ms por foto · modelo ONNX de 16,8 MB |

Gerado por `python scripts/06_relatorio_validacao.py` (tudo calculado na hora a partir do modelo e dos dados).

## Estrutura

```
whatsapp/                   ★ Bot no WhatsApp (Evolution API) — o que roda na apresentação
├── main.py                 Endpoint /webhook (FastAPI)
├── handlers.py             Filtros (números liberados, grupos, duplicadas) e feedback 👍/👎
├── evolution.py            Chamadas à Evolution API (baixar foto, enviar texto)
├── analise.py              Ponte para o pipeline de diagnóstico abaixo
├── configurar.ps1          Cria a instância e aponta o webhook pro ngrok (1 comando)
└── docker-compose.yml      Evolution API + Postgres + Redis
pipeline/                   Diagnóstico (usado pelo whatsapp/ e pela api/)
├── porteiro.py             Recusa foto borrada/pequena
├── llm.py                  Claude: porteiro de assunto (SIM/NÃO) e redação da resposta
├── modelo.py               CNN (MobileNetV3 em ONNX) — decide a praga
├── roteador.py             Confiança ≥80% direto · 50–80% dúvida · <50% Casa da Agricultura
├── kb.py                   Busca a ficha da praga em kb/
├── resposta.py             Monta a mensagem final (com fallback sem LLM)
└── diagnostico.py          Orquestra tudo
kb/
└── fichas-pragas-milho.md  Base de conhecimento curada (Embrapa, Epagri, CATI)
scripts/                    Dataset, treino e validação (rodar na ordem)
├── 01_baixar_gbif.py           Baixa fotos de campo com licença redistribuível
├── 02_limpar_duplicatas.py     Remove duplicata, borrão, imagem pequena/corrompida
├── 03_dividir_treino_teste.py  Split por observação, sem vazamento
├── 04_recortar_karaagro.py     Recorta o KaraAgro AI Maize por bounding box
├── 05_treinar_cnn.py           Treina o classificador (MobileNetV3, transfer learning)
└── 06_relatorio_validacao.py   Tabelas e gráficos de validação para o relatório
docs/
├── 01-persona.md               Ficha da persona e alinhamento de expectativas
├── 02-arquitetura.md           Requisitos, componentes, dados, riscos, cronograma
├── 03-panorama-pragas.md       Embasamento: ocorrência, perdas, níveis de controle
├── 04-guia-dataset.md          Passo a passo para montar o dataset de fotos
├── 05-guia-apresentacao.pdf    ★ Passo a passo do dia da apresentação
├── gerar_guia_pdf.py           Gera o PDF acima (edite aqui e rode de novo)
├── img/                        ★ Imagens prontas para os slides (resultados, fluxo, prints reais)
└── gerar_imagens_slides.py     Gera as imagens de img/ a partir do modelo e do conjunto de teste
api/                        Alternativa com Twilio/Meta (não usada na demo; canal "teste" roda sem conta)
checkpoints/                Modelo treinado — fora do Git, gerado pelo script 05
dados/                      Fotos do dataset — fora do Git (licença de cada foto em dados/creditos.csv)
```

## Como rodar os scripts de dataset e treino

```bash
pip install -r requirements.txt

python scripts/01_baixar_gbif.py --teste          # 5 fotos por classe, para conferir
python scripts/01_baixar_gbif.py --max-por-classe 600
python scripts/01_baixar_gbif.py --max-por-classe 400 --incluir-nc  # mais volume, so uso local (nao publicar)

python scripts/02_limpar_duplicatas.py --dir dados/bruto            # simula
python scripts/02_limpar_duplicatas.py --dir dados/bruto --aplicar  # move

python scripts/04_recortar_karaagro.py --dir <pasta extraida do KaraAgro>

python scripts/03_dividir_treino_teste.py
python scripts/05_treinar_cnn.py
```

## Como rodar o bot no WhatsApp (demonstração)

A conexão real com o WhatsApp fica em [`whatsapp/`](whatsapp/), via **Evolution API** (não oficial: conecta como aparelho vinculado, pelo QR Code). Ela usa o mesmo pipeline de diagnóstico da raiz (`pipeline/`, `kb/`, `checkpoints/`). O passo a passo completo (Docker, QR Code, ngrok) está em [`whatsapp/README.md`](whatsapp/README.md).

**Dia da apresentação:** siga o [`docs/05-guia-apresentacao.pdf`](docs/05-guia-apresentacao.pdf) — preparar o notebook, ligar o bot, roteiro da demo, desligar e problemas comuns. O `whatsapp/configurar.ps1` cria a instância e aponta o webhook com um comando só.

## Como rodar a API (webhook)

```bash
cp .env.example .env        # CANAL_ATIVO=teste já funciona sem conta nenhuma
docker compose up --build
# ou local, sem Docker:
pip install -r api/requirements.txt
uvicorn api.main:app --reload
```

Testar o ida-e-volta sem precisar de conta no Twilio/Meta:

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"remetente": "5511999999999", "tipo": "imagem", "midia_url": "http://x/foto.jpg"}'
```

Trocar para Twilio ou Meta é só mudar `CANAL_ATIVO` no `.env` e preencher as credenciais — nenhum código muda (ver `api/canais/base.py`).

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
