"""API do "Doutor da Roça" — Semana 1 do cronograma: webhook que recebe
foto/texto do WhatsApp e responde. Ainda sem CNN/RAG (isso entra a partir
da Semana 6-8, ver docs/02-arquitetura.md); por enquanto so prova que o
canal funciona de ponta a ponta.

Trocar de canal e' so mudar CANAL_ATIVO no .env — nenhum codigo daqui
sabe se esta falando com Twilio, Meta ou o canal de teste local."""

from fastapi import FastAPI, Request

from api.canais.canal_meta import CanalMeta
from api.canais.canal_teste import CanalTeste
from api.canais.canal_twilio import CanalTwilio
from api.config import CANAL_ATIVO
from api.modelos import Mensagem

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
async def receber_webhook(request: Request):
    mensagem = await canal.receber(request)
    if mensagem is None:
        return {"ok": True}  # status update (entregue/lido), nao mensagem de usuario

    if mensagem.wa_message_id in _mensagens_vistas:
        return {"ok": True, "duplicada": True}
    _mensagens_vistas.add(mensagem.wa_message_id)

    resposta = _responder(mensagem)
    await canal.enviar(mensagem.remetente, resposta)

    corpo = {"ok": True}
    if hasattr(canal, "ultima_resposta"):
        corpo["resposta"] = canal.ultima_resposta
    return corpo


def _responder(mensagem: Mensagem) -> str:
    """Semana 1: so ecoa que recebeu. A partir da Semana 6 isso vira o
    pipeline real: fila -> porteiro de qualidade -> CNN -> roteador de
    confianca -> RAG -> LLM (ver docs/02-arquitetura.md secao 2)."""
    if mensagem.tipo == "imagem":
        return "Recebi sua foto! 📸 Em breve vou te dizer o que é."
    return "Oi! Manda uma foto da praga ou da folha que você quer identificar."
