"""Canal de teste — nao depende de conta nenhuma (nem Twilio, nem Meta).
Existe pra provar o fluxo de ida-e-volta do webhook (a porta de saida da
Semana 1 do cronograma) sem precisar esperar verificacao de conta.

Uso (com a API rodando local ou via docker compose):

    curl -X POST http://localhost:8000/webhook \
      -H "Content-Type: application/json" \
      -d '{"remetente": "5511999999999", "tipo": "imagem", "midia_url": "http://x/foto.jpg"}'

A resposta do bot vem no corpo da propria requisicao HTTP (so pra teste —
Twilio e Meta respondem via chamada separada a API deles, nao no corpo do
webhook, porque o webhook precisa devolver 200 OK rapido demais pra
carregar a resposta real quando o processamento for lento)."""

import uuid

from fastapi import Request

from api.canais.base import CanalAdapter
from api.modelos import Mensagem


class CanalTeste(CanalAdapter):
    def __init__(self):
        self.ultima_resposta: str | None = None

    async def verificar(self, request: Request):
        return {"ok": True, "canal": "teste"}

    async def receber(self, request: Request) -> Mensagem | None:
        corpo = await request.json()
        return Mensagem(
            wa_message_id=corpo.get("wa_message_id") or str(uuid.uuid4()),
            remetente=corpo.get("remetente", "produtor-teste"),
            tipo=corpo.get("tipo", "texto"),
            texto=corpo.get("texto"),
            midia_url=corpo.get("midia_url"),
        )

    async def enviar(self, destinatario: str, texto: str) -> None:
        self.ultima_resposta = texto
