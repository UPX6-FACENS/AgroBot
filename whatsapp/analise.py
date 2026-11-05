"""Ponte entre o webhook da Evolution e o pipeline de diagnóstico real
(pasta pipeline/ na raiz do repositório — a mesma usada por api/).

Contrato mantido do mock antigo:
    analisar_foto(imagem_base64) -> {"texto": str, "diagnostico": {"praga", "confianca"} | None}

Fluxo: porteiro de qualidade -> CNN (ONNX) -> roteador de confiança
(>=0.80 direto | 0.50-0.79 dúvida | <0.50 Casa da Agricultura) -> ficha da
KB -> Claude só redige. O aviso legal e o "Acertei? 👍 👎" já vêm no texto
(pipeline/llm.py, RODAPE_FIXO), então não adicionamos rodapé aqui.
"""

import base64
import io
import logging
import sys
from pathlib import Path

from PIL import Image

# O webhook roda de dentro de whatsapp/ (uvicorn main:app), mas pipeline/,
# kb/ e checkpoints/ ficam na raiz do repo — coloca a raiz no import path.
RAIZ_REPO = Path(__file__).resolve().parent.parent
if str(RAIZ_REPO) not in sys.path:
    sys.path.insert(0, str(RAIZ_REPO))

from pipeline import porteiro
from pipeline.modelo import classificar
from pipeline.resposta import montar_resposta
from pipeline.roteador import decidir_rota

logger = logging.getLogger(__name__)


def _decodificar(imagem_base64: str) -> Image.Image:
    # A Evolution às vezes manda "data:image/jpeg;base64,..." — tira o prefixo
    if imagem_base64.startswith("data:") and "," in imagem_base64:
        imagem_base64 = imagem_base64.split(",", 1)[1]
    return Image.open(io.BytesIO(base64.b64decode(imagem_base64))).convert("RGB")


def analisar_foto(imagem_base64: str) -> dict:
    imagem = _decodificar(imagem_base64)

    ok, motivo = porteiro.verificar(imagem)
    if not ok:
        logger.info("foto reprovada no porteiro: %s", motivo)
        return {"texto": porteiro.MENSAGEM_POR_MOTIVO[motivo], "diagnostico": None}

    classe, confianca = classificar(imagem)
    rota = decidir_rota(confianca)
    logger.info("classificacao: %s (%d%%) | rota=%s", classe, round(confianca * 100), rota)

    texto = montar_resposta(classe, confianca)

    # Só guarda diagnóstico (pro 👍/👎) quando o bot arriscou uma resposta
    diagnostico = None if rota == "humano" else {"praga": classe, "confianca": round(confianca, 4)}
    return {"texto": texto, "diagnostico": diagnostico}
