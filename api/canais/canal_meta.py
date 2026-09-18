"""Adaptador da Meta WhatsApp Cloud API.

NAO TESTADO CONTRA CONTA REAL AINDA — escrito a partir da documentacao
publica da Graph API (formato de webhook, validacao HMAC, envio de
mensagem). Testar assim que a verificacao do Business Manager sair.
Preencha META_VERIFY_TOKEN, META_APP_SECRET, META_ACCESS_TOKEN e
META_PHONE_NUMBER_ID no .env.

Dois detalhes que o guia de arquitetura avisa que costumam quebrar o
projeto:
1. O GET /webhook e' o handshake de verificacao (hub.mode/hub.verify_token/
   hub.challenge) — sem responder isso certo, a Meta nunca ativa o webhook.
2. A midia (foto) NAO vem no payload — vem so um `id`. Baixar de verdade
   exige uma segunda chamada (media_url + download com o Bearer token).
   Isso fica pro worker fazer (ver docs/02-arquitetura.md, passo 1 do
   pipeline), entao aqui so guardamos o id em midia_url por enquanto."""

import hashlib
import hmac

import httpx
from fastapi import HTTPException, Request

from api.canais.base import CanalAdapter
from api.config import META_ACCESS_TOKEN, META_APP_SECRET, META_PHONE_NUMBER_ID, META_VERIFY_TOKEN
from api.modelos import Mensagem

GRAPH_URL = "https://graph.facebook.com/v20.0"


class CanalMeta(CanalAdapter):
    async def verificar(self, request: Request):
        modo = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        desafio = request.query_params.get("hub.challenge")

        if modo == "subscribe" and token == META_VERIFY_TOKEN:
            return int(desafio)
        raise HTTPException(status_code=403, detail="verify_token invalido")

    async def receber(self, request: Request) -> Mensagem | None:
        corpo_bruto = await request.body()
        assinatura = request.headers.get("X-Hub-Signature-256", "")
        if not self._assinatura_valida(corpo_bruto, assinatura):
            raise HTTPException(status_code=403, detail="assinatura Meta invalida")

        payload = await request.json()
        try:
            valor = payload["entry"][0]["changes"][0]["value"]
            msgs = valor.get("messages")
            if not msgs:
                return None  # status update (entregue/lido), nao mensagem de usuario
            msg = msgs[0]
        except (KeyError, IndexError):
            return None

        tipo_meta = msg.get("type")
        if tipo_meta == "image":
            return Mensagem(
                wa_message_id=msg["id"],
                remetente=msg["from"],
                tipo="imagem",
                midia_url=msg["image"]["id"],  # e' um ID, nao URL — ver docstring
            )
        return Mensagem(
            wa_message_id=msg["id"],
            remetente=msg["from"],
            tipo="texto",
            texto=msg.get("text", {}).get("body"),
        )

    async def enviar(self, destinatario: str, texto: str) -> None:
        url = f"{GRAPH_URL}/{META_PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {META_ACCESS_TOKEN}"}
        corpo = {
            "messaging_product": "whatsapp",
            "to": destinatario,
            "type": "text",
            "text": {"body": texto},
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=corpo, headers=headers, timeout=10)
            r.raise_for_status()

    @staticmethod
    def _assinatura_valida(corpo_bruto: bytes, assinatura_recebida: str) -> bool:
        if not assinatura_recebida.startswith("sha256="):
            return False
        esperada = hmac.new(META_APP_SECRET.encode(), corpo_bruto, hashlib.sha256).hexdigest()
        return hmac.compare_digest(f"sha256={esperada}", assinatura_recebida)
