"""Configuracao via variavel de ambiente. Nunca colocar segredo aqui dentro
— tudo vem do .env (gitignored) ou do ambiente real no deploy.

CANAL_ATIVO decide qual ChannelAdapter o main.py carrega. Trocar de canal
e' so mudar essa variavel, sem tocar em codigo — e' o ponto central do
padrao adaptador descrito em docs/02-arquitetura.md secao 6."""

import os

CANAL_ATIVO = os.getenv("CANAL_ATIVO", "teste")  # teste | twilio | meta

# Meta WhatsApp Cloud API
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN", "")
META_APP_SECRET = os.getenv("META_APP_SECRET", "")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
META_PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID", "")

# Twilio WhatsApp Sandbox
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "")  # ex.: "whatsapp:+14155238886"
