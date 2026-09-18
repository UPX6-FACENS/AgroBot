"""Interface que todo canal (teste, Twilio, Meta) implementa. main.py so
fala com isto — nunca com o formato de payload de um provedor especifico.
Ver docs/02-arquitetura.md secao 6: "Abstraia o canal atras de uma
interface... trocar um pelo outro vira mudanca de configuracao"."""

from abc import ABC, abstractmethod

from fastapi import Request

from api.modelos import Mensagem


class CanalAdapter(ABC):
    @abstractmethod
    async def verificar(self, request: Request):
        """Handshake do GET /webhook. So a Meta usa isso de verdade
        (hub.challenge); os outros canais podem so devolver 200 OK."""

    @abstractmethod
    async def receber(self, request: Request) -> Mensagem | None:
        """Converte o payload cru do provedor em Mensagem. Devolve None
        quando o payload nao e' mensagem de usuario (ex.: confirmacao de
        entrega, status update) — nesses casos so respondemos 200 e
        ignoramos, sem processar nada."""

    @abstractmethod
    async def enviar(self, destinatario: str, texto: str) -> None:
        """Manda `texto` de volta para `destinatario` pelo canal."""
