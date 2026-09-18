"""API do "Doutor da Roça" — webhook que recebe foto/texto do WhatsApp e
responde com o diagnostico (CNN + busca estruturada na KB + LLM que so
redige, ver pipeline/diagnostico.py).

O pipeline inteiro leva uns 3s (a chamada ao LLM domina isso — a CNN
sozinha e' ~2ms). Isso estoura o "responda 200 OK em <1s" que Twilio/Meta
exigem, entao nos canais de verdade o processamento roda em background
(FastAPI BackgroundTasks) e o webhook responde na hora; so o canal de
teste fica sincrono, pra dar pra ver a resposta no mesmo curl (ver
CanalAdapter.RESPONDER_SINCRONO). BackgroundTasks nao e' fila durável —
se a API cair no meio, o job se perde, sem retry. Trocar por Redis/RQ
antes de qualquer uso com volume de verdade (Semana 6-8 do cronograma).

Trocar de canal e' so mudar CANAL_ATIVO no .env — nenhum codigo daqui
sabe se esta falando com Twilio, Meta ou o canal de teste local."""

from io import BytesIO

import httpx
from fastapi import BackgroundTasks, FastAPI, Request
from PIL import Image

from api.canais.canal_meta import CanalMeta
from api.canais.canal_teste import CanalTeste
from api.canais.canal_twilio import CanalTwilio
from api.config import CANAL_ATIVO
from api.modelos import Mensagem
from pipeline.diagnostico import diagnosticar

CANAIS = {"teste": CanalTeste, "twilio": CanalTwilio, "meta": CanalMeta}

app = FastAPI(title="Doutor da Roça — webhook")
canal = CANAIS[CANAL_ATIVO]()

# Dedup por wa_message_id — a Meta reenvia o webhook se nao receber 200 OK
# rapido, e isso duplica a resposta pro produtor se nao filtrarmos (ver
# docs/02-arquitetura.md secao 6). Isto e' MVP em memoria: some se a API
# reiniciar. Antes de produzir de verdade, trocar por UNIQUE no Postgres
# (tabela `mensagem`, coluna `wa_message_id`, ja desenhada em docs/02 secao 8).
_mensagens_vistas: set[str] = set()


@app.get("/saude")
async def saude():
    return {"status": "ok", "canal": CANAL_ATIVO}


@app.get("/webhook")
async def verificar_webhook(request: Request):
    """So a Meta usa isto de verdade (handshake hub.challenge)."""
    return await canal.verificar(request)


@app.post("/webhook")
async def receber_webhook(request: Request, background_tasks: BackgroundTasks):
    mensagem = await canal.receber(request)
    if mensagem is None:
        return {"ok": True}  # status update (entregue/lido), nao mensagem de usuario

    if mensagem.wa_message_id in _mensagens_vistas:
        return {"ok": True, "duplicada": True}
    _mensagens_vistas.add(mensagem.wa_message_id)

    if canal.RESPONDER_SINCRONO:
        resposta = await _responder(mensagem)
        await canal.enviar(mensagem.remetente, resposta)
        corpo = {"ok": True}
        if hasattr(canal, "ultima_resposta"):
            corpo["resposta"] = canal.ultima_resposta
        return corpo

    background_tasks.add_task(_processar_em_background, mensagem)
    return {"ok": True, "processando": True}


async def _processar_em_background(mensagem: Mensagem) -> None:
    resposta = await _responder(mensagem)
    await canal.enviar(mensagem.remetente, resposta)


async def _obter_imagem(midia_url: str) -> Image.Image:
    if midia_url.startswith("http"):
        async with httpx.AsyncClient() as client:
            r = await client.get(midia_url, timeout=15)
            r.raise_for_status()
        return Image.open(BytesIO(r.content))
    return Image.open(midia_url)  # caminho local — so pra testar sem hospedar a foto


async def _responder(mensagem: Mensagem) -> str:
    """Foto -> porteiro de qualidade -> CNN -> roteador de confianca ->
    resposta (ver pipeline/diagnostico.py). Texto sem foto so orienta a
    mandar uma."""
    if mensagem.tipo != "imagem":
        return "Oi! Manda uma foto da praga ou da folha que você quer identificar."

    if not mensagem.midia_url:
        return "Não recebi nenhuma foto anexada. Pode mandar de novo?"

    try:
        imagem = await _obter_imagem(mensagem.midia_url)
    except Exception:
        return "Não consegui abrir sua foto. Pode mandar de novo?"

    return diagnosticar(imagem)
