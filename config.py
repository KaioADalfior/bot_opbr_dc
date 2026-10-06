"""Configuração do projeto: lê variáveis do arquivo .env (nunca do código-fonte)."""
from __future__ import annotations

import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    print("Dependências ausentes. Ative o ambiente virtual e execute: python -m pip install -r requirements.txt")
    sys.exit(2)

RAIZ = Path(__file__).resolve().parent
PASTA_LOGS = RAIZ / "logs"
PASTA_RELATORIOS = RAIZ / "relatorios"
PASTA_ESTADO = RAIZ / "estado"

NOME_ESPERADO_PADRAO = "Ghost Recon Brasil"


@dataclass
class Configuracao:
    token: str
    guild_id: str
    nome_esperado: str
    application_id: str


def carregar() -> Configuracao:
    load_dotenv(RAIZ / ".env")
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    guild_id = os.getenv("DISCORD_GUILD_ID", "").strip()
    nome = os.getenv("DISCORD_GUILD_NAME", NOME_ESPERADO_PADRAO).strip()
    app_id = os.getenv("DISCORD_APPLICATION_ID", "").strip()
    return Configuracao(token, guild_id, nome, app_id)


def validar_basico(cfg: Configuracao, precisa_token: bool = True) -> list[str]:
    erros = []
    if precisa_token and not cfg.token:
        erros.append("DISCORD_BOT_TOKEN não definido no arquivo .env")
    if precisa_token and cfg.token and cfg.token.count(".") < 2:
        erros.append("DISCORD_BOT_TOKEN não parece um token de bot válido (copie novamente no Portal)")
    if not re.fullmatch(r"\d{17,20}", cfg.guild_id or ""):
        erros.append("DISCORD_GUILD_ID ausente ou inválido (deve ter 17 a 20 dígitos)")
    return erros


class _OcultarSegredos(logging.Filter):
    """Remove qualquer coisa parecida com token de bot das mensagens de log."""
    PADRAO = re.compile(r"[\w-]{20,}\.[\w-]{5,}\.[\w-]{20,}")

    def __init__(self, token: str = ""):
        super().__init__()
        self.token = token

    def filter(self, record):
        msg = record.getMessage()
        if self.token:
            msg = msg.replace(self.token, "***TOKEN-OCULTO***")
        msg = self.PADRAO.sub("***TOKEN-OCULTO***", msg)
        record.msg, record.args = msg, ()
        return True


def configurar_log(comando: str, token: str = "") -> Path:
    PASTA_LOGS.mkdir(exist_ok=True)
    caminho = PASTA_LOGS / f"{datetime.now():%Y%m%d-%H%M%S}-{comando}.log"
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raiz = logging.getLogger()
    for h in list(raiz.handlers):
        h.close()
        raiz.removeHandler(h)
    raiz.setLevel(logging.INFO)
    filtro = _OcultarSegredos(token)
    arquivo = logging.FileHandler(caminho, encoding="utf-8")
    arquivo.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s"))
    arquivo.addFilter(filtro)
    tela = logging.StreamHandler(sys.stdout)
    tela.setFormatter(logging.Formatter("%(message)s"))
    tela.addFilter(filtro)
    raiz.addHandler(arquivo)
    raiz.addHandler(tela)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return caminho


def fechar_log() -> None:
    """Fecha os arquivos de log (no Windows, arquivo aberto não pode ser apagado/movido)."""
    raiz = logging.getLogger()
    for h in list(raiz.handlers):
        h.close()
        raiz.removeHandler(h)
