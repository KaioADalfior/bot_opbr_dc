"""Configuração do bot (lida de bot/.env)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PASTA = Path(__file__).resolve().parent


def _ids(valor: str) -> list[int]:
    return [int(x) for x in re.findall(r"\d{17,20}", valor or "")]


@dataclass
class Config:
    token: str
    guild_id: int
    conteudo_mensagens: bool
    inatividade_dias: int
    max_denuncias: int
    max_mods: int
    banco: Path
    # Nomes (sem emoji) usados para localizar cargos e canais; podem ser trocados por IDs no .env
    cargos_equipe: list[str] = field(default_factory=lambda: ["líder fundador", "administração", "moderador"])
    ids_cargos_equipe: list[int] = field(default_factory=list)
    canais: dict[str, str] = field(default_factory=dict)
    nome_categoria_tickets: str = "╭─── 🎫 Tickets"
    web_ativo: bool = True
    web_host: str = "127.0.0.1"
    web_porta: int = 8088
    url_publica: str = ""
    web_tunel: str = "cloudflared"
    transcript_dias: int = 30
    nome_canal_abrir_squad: str = "🎯｜abrir-squad"
    nome_categoria_squads: str = "╭─── 🎮 Squads Ativos"
    nome_canal_contribuicao: str = "💎｜contribuição"
    cargo_vip: str = "vip"
    boost_vip: bool = True
    intent_membros: bool = True
    max_contribuicoes: int = 1
    squad_vazio_min: int = 10
    squad_max: int = 25
    squad_travar_canal: bool = True


def carregar() -> Config:
    load_dotenv(PASTA / ".env")
    token = os.getenv("BOT_TOKEN", "").strip()
    gid = os.getenv("GUILD_ID", "").strip()
    if not token or token.count(".") < 2:
        raise SystemExit("ERRO: defina BOT_TOKEN em bot/.env (token do bot Operação Brasil).")
    if not re.fullmatch(r"\d{17,20}", gid):
        raise SystemExit("ERRO: defina GUILD_ID em bot/.env (ID do servidor).")
    return Config(
        token=token,
        guild_id=int(gid),
        conteudo_mensagens=os.getenv("MESSAGE_CONTENT_INTENT", "1").strip() == "1",
        inatividade_dias=int(os.getenv("TICKET_INATIVIDADE_DIAS", "7")),
        max_denuncias=int(os.getenv("MAX_DENUNCIAS_ABERTAS", "1")),
        max_mods=int(os.getenv("MAX_MODS_ABERTOS", "2")),
        banco=PASTA / "dados" / "operacao_brasil.sqlite3",
        web_ativo=os.getenv("WEB_ATIVO", "1").strip() == "1",
        web_host=os.getenv("WEB_HOST", "127.0.0.1").strip(),
        web_porta=int(os.getenv("WEB_PORTA", "8088")),
        url_publica=os.getenv("URL_PUBLICA", "").strip(),
        web_tunel=os.getenv("WEB_TUNEL", "cloudflared").strip().lower(),
        transcript_dias=int(os.getenv("TRANSCRIPT_DIAS", "30")),
        cargo_vip=os.getenv("CARGO_VIP", "vip").strip(),
        boost_vip=os.getenv("BOOST_DA_VIP", "1").strip() == "1",
        intent_membros=os.getenv("MEMBERS_INTENT", "1").strip() == "1",
        max_contribuicoes=int(os.getenv("MAX_CONTRIBUICOES_ABERTAS", "1")),
        squad_vazio_min=max(2, int(os.getenv("SQUAD_VAZIO_MIN", "10"))),
        squad_max=int(os.getenv("SQUAD_MAX", "25")),
        squad_travar_canal=os.getenv("SQUAD_TRAVAR_CANAL", "1").strip() == "1",
        ids_cargos_equipe=_ids(os.getenv("IDS_CARGOS_EQUIPE", "")),
        canais={
            "denuncias": os.getenv("CANAL_DENUNCIAS", "denúncias"),
            "publicar_mod": os.getenv("CANAL_PUBLICAR_MOD", "publicar-mod"),
            "mods_publicados": os.getenv("CANAL_MODS_PUBLICADOS", "mods-publicados"),
            "regras_mods": os.getenv("CANAL_REGRAS_MODS", "regras-para-mods"),
            "logs": os.getenv("CANAL_LOGS", "logs-de-moderação"),
            "relatorios": os.getenv("CANAL_RELATORIOS", "relatórios"),
            "squad_partida": os.getenv("CANAL_SQUAD_PARTIDA", "squad-partida"),
            "abrir_squad": os.getenv("CANAL_ABRIR_SQUAD", "abrir-squad"),
            "contribuicao": os.getenv("CANAL_CONTRIBUICAO", "contribuição"),
            "vips": os.getenv("CANAL_VIPS", "vips"),
        },
    )
