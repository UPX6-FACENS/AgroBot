"""Modelo comum de mensagem — todo canal (teste, Twilio, Meta) converte o
payload cru dele para isto. O resto do sistema nunca ve o formato do
provedor, so este modelo."""

from dataclasses import dataclass


@dataclass
class Mensagem:
    wa_message_id: str
    remetente: str
    tipo: str  # "texto" | "imagem" | "audio"
    texto: str | None = None
    midia_url: str | None = None
