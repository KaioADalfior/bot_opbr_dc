# Bot Operação Brasil — imagem para Easypanel / Docker
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=America/Sao_Paulo \
    WEB_HOST=0.0.0.0 \
    WEB_TUNEL=

WORKDIR /app
COPY bot/requirements.txt bot/requirements.txt
RUN pip install -r bot/requirements.txt

COPY bot/ bot/
# Usuário sem privilégios (UID 1000). A pasta de dados fica num volume/bind mount.
RUN useradd -u 1000 -m operacao && mkdir -p bot/dados && chown -R operacao:operacao bot/dados
USER operacao

# Porta dos transcripts (o Easypanel publica com HTTPS no seu domínio)
EXPOSE 8088
CMD ["python", "-m", "bot"]
