"""Checagem da instalação, sem conectar ao Discord: python -m bot verificar

Use antes de ligar o bot (no PC ou na VPS). Confere Python, dependências, bot/.env, arquivos,
pasta de dados, conteúdo das mensagens (limites do Discord), porta e cloudflared.
"""
from __future__ import annotations

import os
import re
import socket
import sqlite3
import sys
from importlib import metadata
from pathlib import Path

PASTA = Path(__file__).resolve().parent
OK, AVISO, FALHA = "OK", "AVISO", "FALHA"


def _versao(pacote: str) -> str | None:
    try:
        return metadata.version(pacote)
    except metadata.PackageNotFoundError:
        return None


def _num(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def checar_conteudo() -> list[str]:
    """Erros de conteúdo que o Discord recusaria (limites de embed, canais inexistentes)."""
    from . import conteudo as K
    erros = []
    for chave, blocos in K.MENSAGENS.items():
        if chave not in K.CANAIS:
            erros.append(f"mensagem '{chave}' sem canal em CANAIS")
            continue
        total = 0
        if len(blocos) > 9:
            erros.append(f"{chave}: mais de 9 blocos")
        for b in blocos:
            textos = [b.get("titulo") or "", b.get("texto") or ""]
            if len(b.get("titulo") or "") > 256:
                erros.append(f"{chave}: título com mais de 256 caracteres")
            if len(b.get("texto") or "") > 4096:
                erros.append(f"{chave}: texto com mais de 4096 caracteres")
            campos = b.get("campos", [])
            if len(campos) > 25:
                erros.append(f"{chave}: mais de 25 campos")
            for nome, valor, _ in campos:
                if len(nome) > 256 or len(valor) > 1024:
                    erros.append(f"{chave}: campo '{nome[:30]}' grande demais")
                textos += [nome, valor]
            for t in textos:
                for ref in re.findall(r"\{c:([a-z0-9_]+)\}", t):
                    if ref not in K.CANAIS:
                        erros.append(f"{chave}: referência a canal inexistente {{c:{ref}}}")
            total += sum(len(t) for t in textos) + len(K.RODAPE)
        if total > 5800:   # limite do Discord: 6000 caracteres somando todos os embeds da mensagem
            erros.append(f"{chave}: mensagem com {total} caracteres (limite 6000)")
    return erros


def executar() -> int:
    linhas: list[tuple[str, str, str]] = []

    def add(st, nome, det=""):
        linhas.append((st, nome, det))

    # Python e dependências
    v = sys.version_info
    add(OK if v >= (3, 11) else FALHA, "Python 3.11 ou mais novo", f"{v.major}.{v.minor}.{v.micro}")
    for pacote, minimo in (("discord.py", "2.6"), ("aiohttp", "3.9"), ("cryptography", "42"),
                           ("python-dotenv", "1.0")):
        ver = _versao(pacote)
        if ver is None:
            add(FALHA, f"Pacote {pacote}", "não instalado: python -m pip install -r bot/requirements.txt")
        else:
            add(OK if _num(ver) >= _num(minimo) else FALHA, f"Pacote {pacote}", ver)

    # Configuração: bot/.env (PC) ou variáveis de ambiente (Easypanel/Docker; elas têm prioridade)
    from dotenv import dotenv_values
    env = PASTA / ".env"
    valores = {**(dotenv_values(env) if env.is_file() else {}),
               **{k: v for k, v in os.environ.items() if k.isupper()}}
    origem = "bot/.env" if env.is_file() else "variáveis de ambiente"
    token = (valores.get("BOT_TOKEN") or "").strip()
    if not token and not env.is_file():
        add(FALHA, "Configuração", "sem bot/.env e sem variáveis de ambiente: copie bot/.env.example para bot/.env "
                                   "(PC) ou preencha a aba Environment (Easypanel)")
    else:
        add(OK, "Configuração", origem)
        add(OK if token.count(".") == 2 and len(token) > 50 else FALHA, "BOT_TOKEN", "formato válido (não exibido)"
            if token.count(".") == 2 else "vazio ou incompleto")
        gid = (valores.get("GUILD_ID") or "").strip()
        add(OK if re.fullmatch(r"\d{17,20}", gid) else FALHA, "GUILD_ID", gid or "vazio")
        if (valores.get("MEMBERS_INTENT", "1") or "1").strip() == "1":
            add(AVISO, "SERVER MEMBERS INTENT", "confirme que está LIGADA no Portal do Desenvolvedor (aba Bot)")
        raiz_env = PASTA.parent / ".env"
        if token and raiz_env.is_file() and token in raiz_env.read_text(encoding="utf-8", errors="ignore"):
            add(AVISO, "Token repetido no .env da raiz", "o token do bot está também no .env do configurador")

    # Arquivos
    from . import conteudo as K
    assets = PASTA / "assets"
    esperados = ["painel_squads.png", "painel_vip.png", "painel_denuncia.png", "painel_mods.png",
                 "squad_breakpoint.png", "squad_wildlands.png", "squad_r6.png",
                 *[f"canal_{c}.png" for c in K.MENSAGENS if c not in K.CANAIS_DE_PAINEL]]
    faltam = [a for a in esperados if not (assets / a).is_file()]
    add(OK if not faltam else AVISO, "Banners (bot/assets)", f"{len(esperados)} imagens" if not faltam
        else f"faltando: {', '.join(faltam)} (os embeds saem sem imagem)")
    add(OK if (PASTA / "modelos" / "transcript.html").is_file() else FALHA, "Modelo do transcript")

    # Conteúdo
    erros = checar_conteudo()
    add(OK if not erros else FALHA, "Mensagens dos canais (limites do Discord)",
        f"{len(K.MENSAGENS)} canais" if not erros else "; ".join(erros))

    # Dados
    dados = PASTA / "dados"
    try:
        dados.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(dados / "operacao_brasil.sqlite3")
        con.execute("PRAGMA integrity_check").fetchone()
        con.close()
        add(OK, "Banco de dados (bot/dados)", str(dados))
    except (OSError, sqlite3.Error) as e:
        add(FALHA, "Banco de dados (bot/dados)", str(e))

    # Web / túnel
    cfg = valores
    if (cfg.get("WEB_ATIVO", "1") or "1").strip() == "1":
        porta = int(cfg.get("WEB_PORTA", "8088") or 8088)
        with socket.socket() as s:
            livre = s.connect_ex(("127.0.0.1", porta)) != 0
        add(OK if livre else AVISO, f"Porta {porta} dos transcripts", "livre" if livre
            else "em uso (o bot já está rodando? só pode haver uma instância)")
        if not (cfg.get("URL_PUBLICA") or "").strip():
            if (cfg.get("WEB_TUNEL", "cloudflared") or "").strip().lower() == "cloudflared":
                from .web import ServidorTranscripts
                exe = ServidorTranscripts._achar_cloudflared()
                add(OK if exe else AVISO, "cloudflared (link dos transcripts)", exe or
                    "não encontrado: winget install --id Cloudflare.cloudflared (sem ele, vão como anexo)")
            else:
                add(AVISO, "Link dos transcripts", "sem URL_PUBLICA e sem túnel: transcripts irão como anexo")
        else:
            add(OK, "URL pública dos transcripts", cfg["URL_PUBLICA"])

    # Saída
    largura = max(len(n) for _, n, _ in linhas) + 2
    icone = {OK: "✅", AVISO: "⚠️ ", FALHA: "❌"}
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    print("\n  Operação Brasil — checagem da instalação\n")
    for st, nome, det in linhas:
        print(f"  {icone[st]} {nome.ljust(largura)} {det}")
    falhas = sum(1 for st, _, _ in linhas if st == FALHA)
    avisos = sum(1 for st, _, _ in linhas if st == AVISO)
    print(f"\n  Resultado: {len(linhas) - falhas - avisos} ok · {avisos} aviso(s) · {falhas} falha(s)")
    print("  " + ("Tudo certo para ligar: python -m bot" if not falhas else "Corrija as falhas antes de ligar o bot."))
    print("  Depois de ligar, use /servidor verificar no Discord para conferir o servidor.\n")
    return 1 if falhas else 0


if __name__ == "__main__":
    os.chdir(PASTA.parent)
    sys.exit(executar())
