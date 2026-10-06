"""Transcript em página HTML protegida por senha.

O conteúdo do ticket é criptografado (AES-256-GCM, chave derivada da senha por PBKDF2-SHA256)
e embutido num único arquivo .html. A página só mostra a conversa depois que a senha correta
é digitada; a descriptografia acontece no navegador (Web Crypto API), sem servidor.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import os
import secrets
from datetime import timezone
from pathlib import Path

import discord
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

log = logging.getLogger("operacao_brasil")

ITERACOES = 310_000
LIMITE_IMAGEM = 3 * 1024 * 1024       # por imagem
LIMITE_TOTAL_IMAGENS = 6 * 1024 * 1024  # o arquivo final precisa caber no limite de upload do Discord
TIPOS_IMAGEM = ("image/png", "image/jpeg", "image/gif", "image/webp")
MODELO = Path(__file__).resolve().parent / "modelos" / "transcript.html"
ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sem 0/O e 1/I


def gerar_senha() -> str:
    return "-".join("".join(secrets.choice(ALFABETO) for _ in range(4)) for _ in range(4))


def criptografar(dados: dict, senha: str) -> dict:
    sal = os.urandom(16)
    iv = os.urandom(12)
    chave = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal, ITERACOES, dklen=32)
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ct = AESGCM(chave).encrypt(iv, texto, None)
    b64 = lambda b: base64.b64encode(b).decode("ascii")  # noqa: E731
    return {"v": 1, "iter": ITERACOES, "salt": b64(sal), "iv": b64(iv), "ct": b64(ct)}


def descriptografar(pacote: dict, senha: str) -> dict:
    """Usado nos testes para garantir que o navegador conseguirá abrir."""
    d = lambda s: base64.b64decode(s)  # noqa: E731
    chave = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), d(pacote["salt"]), pacote["iter"], dklen=32)
    return json.loads(AESGCM(chave).decrypt(d(pacote["iv"]), d(pacote["ct"]), None))


def montar_html(numero: int, pacote: dict) -> str:
    modelo = MODELO.read_text(encoding="utf-8")
    return (modelo.replace("__NUMERO__", f"{numero:04d}")
                  .replace("__PACOTE__", json.dumps(pacote)))


def _embed_dict(e: discord.Embed) -> dict:
    return {
        "titulo": e.title or "", "descricao": e.description or "", "url": e.url or "",
        "cor": f"#{e.color.value:06x}" if e.color else "#38bdf8",
        "autor": e.author.name if e.author and e.author.name else "",
        "campos": [{"nome": f.name, "valor": f.value, "inline": bool(f.inline)} for f in e.fields],
        "rodape": e.footer.text if e.footer and e.footer.text else "",
    }


async def coletar(canal: discord.TextChannel, ticket: dict, cabecalho: dict) -> dict:
    """Lê o histórico do canal. Imagens pequenas são embutidas; outros arquivos aparecem só pelo nome."""
    mensagens, pessoas = [], {}
    gasto = 0
    async for m in canal.history(limit=None, oldest_first=True):
        a = m.author
        pessoas[str(a.id)] = {"nome": getattr(a, "display_name", a.name), "usuario": a.name, "bot": a.bot,
                              "avatar": a.display_avatar.replace(size=64, static_format="png").url}
        for u in m.mentions:
            pessoas.setdefault(str(u.id), {"nome": getattr(u, "display_name", u.name), "usuario": u.name,
                                           "bot": u.bot, "avatar": ""})
        anexos = []
        for at in m.attachments:
            item = {"nome": at.filename, "tamanho": at.size, "tipo": at.content_type or ""}
            if (at.content_type or "").split(";")[0] in TIPOS_IMAGEM and at.size <= LIMITE_IMAGEM \
                    and gasto + at.size <= LIMITE_TOTAL_IMAGENS:
                try:
                    bruto = await at.read()
                    item["dados"] = f"data:{at.content_type.split(';')[0]};base64," + base64.b64encode(bruto).decode()
                    gasto += at.size
                except discord.HTTPException:
                    item["aviso"] = "imagem indisponível"
            elif (at.content_type or "").startswith("image/"):
                item["aviso"] = "imagem não incluída (limite de tamanho)"
            anexos.append(item)
        mensagens.append({
            "autor": str(a.id), "data": m.created_at.astimezone(timezone.utc).isoformat(),
            "editada": m.edited_at.astimezone(timezone.utc).isoformat() if m.edited_at else "",
            "texto": m.content or "", "embeds": [_embed_dict(e) for e in m.embeds], "anexos": anexos,
        })
    return {"cabecalho": cabecalho, "pessoas": pessoas, "mensagens": mensagens}


async def gerar(canal: discord.TextChannel, ticket: dict, cabecalho: dict) -> tuple[bytes, str]:
    """Retorna (bytes do .html protegido, senha)."""
    senha = gerar_senha()
    dados = await coletar(canal, ticket, cabecalho)
    return montar_html(ticket["id"], criptografar(dados, senha)).encode("utf-8"), senha


def arquivo(html: bytes, numero: int) -> discord.File:
    """Um discord.File só pode ser enviado uma vez: crie um novo para cada destino."""
    return discord.File(io.BytesIO(html), filename=f"transcript-{numero:04d}.html")
