FROM python:3.12-slim

WORKDIR /app

COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY api/ ./api/
COPY pipeline/ ./pipeline/
COPY kb/ ./kb/
# checkpoints/ e' gitignored (peso treinado, ver .gitignore) mas precisa
# estar no disco local antes do build — rode scripts/05_treinar_cnn.py
# primeiro. Isto funciona pra rodar local/apresentacao; deploy de verdade
# deveria buscar o modelo de um Release/registro de artefatos, nao copiar
# do disco de quem builda.
COPY checkpoints/modelo.onnx checkpoints/classes.json ./checkpoints/

EXPOSE 8000
# --proxy-headers: sem isso, request.url.scheme sempre vem "http" (a
# conexao real entre o proxy — ngrok, ou Render/Railway em produzao — e o
# uvicorn e' HTTP puro), mesmo quando o Twilio assinou a URL como https.
# A validacao de assinatura em canal_twilio.py compara a URL exata, entao
# sem isso ela SEMPRE falha com 403 atras de qualquer proxy reverso.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips=*"]
