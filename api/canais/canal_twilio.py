"""Adaptador do Twilio WhatsApp Sandbox.

NAO TESTADO CONTRA CONTA REAL AINDA — escrito a partir da documentacao
publica do Twilio (formato de webhook e SDK oficial). Quando alguem do
grupo criar a conta sandbox, testar este arquivo primeiro antes de
confiar nele. Preencha TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN e
TWILIO_WHATSAPP_FROM no .env.

O Twilio manda o webhook como formulario (application/x-www-form-urlencoded),
nao JSON: From="whatsapp:+55...", Body="...", MessageSid="...",
NumMedia="0"|"1"|..., MediaUrl0, MediaContentType0.

Usa o SDK oficial (pacote `twilio` no PyPI) tanto pra validar a assinatura
quanto pra mandar a resposta — nunca biblioteca nao-oficial (Baileys,
venom-bot etc.), que quebra os termos de uso e derruba o numero."""

from fastapi import HTTPException, Request
from twilio.request_validator import RequestValidator
from twilio.rest import Client

from api.canais.base import CanalAdapter
from api.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM
from api.modelos import Mensagem


class CanalTwilio(CanalAdapter):
    def __init__(self):
        self._validador = RequestValidator(TWILIO_AUTH_TOKEN)
        self._cliente = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    async def verificar(self, request: Request):
        return {"ok": True, "canal": "twilio"}

    async def receber(self, request: Request) -> Mensagem | None:
        form = await request.form()
        dados = dict(form)

        assinatura = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        if not self._validador.validate(url, dados, assinatura):
            raise HTTPException(status_code=403, detail="assinatura Twilio invalida")

        num_media = int(dados.get("NumMedia", "0") or "0")
        midia_url = dados.get("MediaUrl0") if num_media > 0 else None

        return Mensagem(
            wa_message_id=dados["MessageSid"],
            remetente=dados["From"].removeprefix("whatsapp:"),
            tipo="imagem" if midia_url else "texto",
            texto=dados.get("Body") or None,
            midia_url=midia_url,
        )

    async def enviar(self, destinatario: str, texto: str) -> None:
        self._cliente.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{destinatario}",
            body=texto,
        )
