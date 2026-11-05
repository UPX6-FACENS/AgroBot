"""O UNICO lugar do sistema que chama um LLM — e ele so REDIGE, nunca
decide (ver docs/02-arquitetura.md secao 5). A praga ja foi escolhida
pela CNN antes disto rodar; o LLM so traduz o texto ja recuperado da KB
pra linguagem simples, dentro de regras fixas.

Chamado so nos casos com conteudo tecnico de verdade pra resumir (rota
"direto" e "duvida" com praga identificada). Os casos triviais (porteiro
reprovou a foto, rota "humano", milho_sadio) ficam com resposta fixa em
pipeline/resposta.py — sem custo de API e sem risco de alucinacao onde
nao precisa.

Tambem roda aqui o "porteiro de assunto" (foto_e_do_assunto): antes da
CNN, o Claude so responde SIM/NAO pra "isso e' milho ou inseto?". A CNN
so conhece 4 classes e SEMPRE escolhe uma delas — um print de tela ou uma
selfie viravam "vaquinha com alta confianca". O porteiro nao escolhe
praga nenhuma; quem decide a praga continua sendo a CNN."""

import base64
import io
import logging

import anthropic
from PIL import Image

logger = logging.getLogger(__name__)

MODELO = "claude-haiku-4-5"

# O aviso legal (nao e' receita) e a pergunta de feedback NAO ficam a cargo
# do LLM — sao anexados sempre por codigo em resposta.py. E' um requisito
# legal (ver docs/02-arquitetura.md secao 7), entao nao pode depender do
# modelo "lembrar" de escrever em toda resposta.
RODAPE_FIXO = (
    "\n\n⚠️ Isso é uma ajuda, não é receita. Para veneno, é preciso receituário agronômico."
    "\n\nAcertei? 👍 👎"
)

SYSTEM_PROMPT = """Você é o redator de respostas do "Doutor da Roça", chatbot de \
WhatsApp que ajuda pequeno produtor de milho a identificar praga por foto.

Você NUNCA decide qual é a praga — um classificador de imagem já decidiu isso \
antes de você. Você só traduz o texto técnico fornecido para uma mensagem \
simples de WhatsApp.

Regras obrigatórias, sem exceção:
1. Use EXCLUSIVAMENTE as informações do texto fornecido abaixo. Se a \
informação não estiver lá, diga que não sabe — nunca invente.
2. Máximo 70 palavras. Frases curtas, sem jargão técnico sem explicar.
3. NUNCA escreva número de dose ou nome de produto químico específico. Para \
controle químico, diga só que existe e que exige receituário agronômico.
4. Se houver mais de uma opção de manejo, liste da mais barata para a mais \
cara.
5. NÃO escreva aviso legal nem pergunta de feedback no final — isso é \
adicionado automaticamente depois de você. Termine seu texto no conteúdo.
6. No máximo 2 emojis no total. Sem cabeçalho, sem lista com emoji numerado \
(1️⃣2️⃣3️⃣) — para listar passos, use "1.", "2." simples.
7. Formatação é a do WhatsApp, não markdown comum: negrito é *um asterisco* \
(nunca **dois**), itálico é _um underline_. Não existe cabeçalho (#).
8. Responda só com a mensagem final, sem nenhum comentário sobre a tarefa."""


def redigir(*, classe_nome: str, confianca_pct: int, rota: str,
            como_reconhecer_o_dano: str, manejo_ordenado_por_custo: str) -> str:
    """rota: "direto" (o modelo tem confianca alta) ou "duvida" (confianca
    media — a mensagem deve pedir confirmacao em vez de afirmar)."""
    instrucao_rota = (
        "O classificador tem confiança ALTA. Afirme o diagnóstico e oriente o manejo."
        if rota == "direto" else
        "O classificador tem confiança MÉDIA (não tem certeza). Diga que PODE ser essa "
        "praga, peça outra foto mais nítida pra confirmar, e já adiante o primeiro sinal "
        "de dano pra o produtor comparar."
    )

    mensagem_usuario = f"""Praga identificada: {classe_nome}
Confiança do classificador: {confianca_pct}%
Rota: {instrucao_rota}

Texto técnico sobre o dano (fonte: ficha curada):
{como_reconhecer_o_dano}

Texto técnico sobre manejo, já do mais barato pro mais caro (fonte: ficha curada):
{manejo_ordenado_por_custo}

Escreva a mensagem de WhatsApp agora."""

    client = anthropic.Anthropic()
    resposta = client.messages.create(
        model=MODELO,
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": mensagem_usuario}],
    )
    return resposta.content[0].text.strip() + RODAPE_FIXO


PROMPT_ASSUNTO = """Esta foto foi enviada a um chatbot de agricultura que identifica pragas.
Responda SIM se aparecer na foto QUALQUER um destes, mesmo pequeno, de perto,
desfocado ou segurado na mão: planta, folha, espiga, lavoura, raiz, lagarta,
besouro, inseto, ou dano/furo em planta ou fruto.
Responda NAO somente quando claramente não há planta nem inseto nenhum:
prints de tela, pessoas/selfies, documentos, texto, objetos, animais
domésticos, paisagem urbana.
Na dúvida, responda SIM.
Responda só uma palavra: SIM ou NAO."""

MENSAGEM_FORA_DO_ASSUNTO = (
    "🤔 Não encontrei planta de milho nem inseto nessa foto.\n\n"
    "Manda uma foto bem de perto da folha, da espiga ou do bicho "
    "que está atacando o milho 📷"
)


def foto_e_do_assunto(imagem: Image.Image) -> bool:
    """True se a foto parece milho/inseto. Em caso de erro na API, deixa
    passar (True) — melhor cair no fluxo normal (que ainda tem o roteador
    de confianca) do que travar o bot inteiro sem internet."""
    copia = imagem.convert("RGB")
    copia.thumbnail((768, 768))  # foto menor = menos tokens e mais rapido
    buffer = io.BytesIO()
    copia.save(buffer, format="JPEG", quality=85)
    dados = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")

    try:
        resposta = anthropic.Anthropic().messages.create(
            model=MODELO,
            max_tokens=5,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": dados}},
                    {"type": "text", "text": PROMPT_ASSUNTO},
                ],
            }],
        )
    except anthropic.APIError:
        logger.exception("porteiro de assunto falhou — deixando a foto passar")
        return True

    texto = next((b.text for b in resposta.content if b.type == "text"), "").strip().upper()
    return not texto.startswith("NAO") and not texto.startswith("NÃO")
