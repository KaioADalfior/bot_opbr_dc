"""Bot "Operação Brasil" — execução: python -m bot   (dentro da pasta server-ghost)."""
from __future__ import annotations

import base64
import logging
import sys
from logging.handlers import RotatingFileHandler

import discord
from discord.ext import commands

from . import config as config_mod
from .cogs import servidor, squads, tickets, vip
from .db import Banco
from .nucleo import Nucleo
from .web import ServidorTranscripts

from .permissoes import PERMISSOES

# O bot não toca áudio: desliga os avisos de bibliotecas de voz (PyNaCl/davey) que não são necessárias.
discord.VoiceClient.warn_nacl = False
if hasattr(discord.VoiceClient, "warn_dave"):
    discord.VoiceClient.warn_dave = False


def configurar_log(pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    arq = RotatingFileHandler(pasta / "bot.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    arq.setFormatter(fmt)
    tela = logging.StreamHandler(sys.stdout)
    tela.setFormatter(fmt)
    raiz = logging.getLogger()
    raiz.setLevel(logging.INFO)
    raiz.addHandler(arq)
    raiz.addHandler(tela)
    logging.getLogger("discord.http").setLevel(logging.WARNING)


class OperacaoBrasil(commands.Bot):
    def __init__(self, cfg: config_mod.Config):
        intents = discord.Intents.none()
        intents.guilds = True
        intents.guild_messages = True
        intents.voice_states = True            # saber quem está nas calls dos squads
        intents.members = cfg.intent_membros    # saber quem impulsiona o servidor (booster = VIP)
        intents.message_content = cfg.conteudo_mensagens   # só para as transcrições dos tickets
        super().__init__(command_prefix=commands.when_mentioned, intents=intents,
                         allowed_mentions=discord.AllowedMentions.none(), help_command=None)
        self.cfg = cfg
        self.nucleo = Nucleo(self, cfg, Banco(cfg.banco))
        self._preparado = False
        self.cog_tickets = None
        self.cog_squads = None
        self.cog_vip = None
        self.cog_servidor = None

    async def setup_hook(self):
        if self.cfg.web_ativo:
            srv = ServidorTranscripts(self.cfg.banco.parent / "transcripts", self.cfg.web_host, self.cfg.web_porta,
                                      self.cfg.url_publica, self.cfg.web_tunel, self.cfg.transcript_dias)
            try:
                await srv.iniciar()
                self.nucleo.web = srv
            except OSError as e:
                logging.error("Não foi possível iniciar o servidor de transcripts (porta %s): %s",
                              self.cfg.web_porta, e)
        self.cog_tickets = await tickets.setup(self, self.nucleo)
        self.cog_squads = await squads.setup(self, self.nucleo)
        self.cog_vip = await vip.setup(self, self.nucleo)
        self.cog_servidor = await servidor.setup(self, self.nucleo)
        guild = discord.Object(self.cfg.guild_id)
        sincronizados = await self.tree.sync(guild=guild)
        logging.info("Comandos sincronizados no servidor: %s", [c.name for c in sincronizados])

    async def close(self):
        if self.nucleo.web:
            await self.nucleo.web.parar()
        await super().close()

    async def on_ready(self):
        log = logging.getLogger("operacao_brasil")
        log.info("Conectado como %s (%s)", self.user, self.user.id)
        if self._preparado:
            return
        g = self.get_guild(self.cfg.guild_id)
        if g is None:
            url = discord.utils.oauth_url(self.user.id, permissions=PERMISSOES, guild=discord.Object(self.cfg.guild_id),
                                          scopes=("bot", "applications.commands"))
            log.error("O bot não está no servidor %s. Autorize com: %s", self.cfg.guild_id, url)
            return
        faltando = [p for p, v in PERMISSOES if v and not getattr(g.me.guild_permissions, p)]
        if faltando:
            log.error("Permissões faltando no servidor: %s", faltando)
        if g.me.guild_permissions.administrator:
            log.warning("O bot está com Administrador; recomendado usar só as permissões mínimas.")
        erros = 0
        for nome, cog in (("tickets e painéis", self.cog_tickets), ("squads", self.cog_squads),
                          ("VIP", self.cog_vip), ("mensagens dos canais", self.cog_servidor)):
            try:
                await cog.preparar()
                log.info("Pronto: %s.", nome)
            except Exception as e:  # noqa: BLE001 — um módulo com problema não derruba os outros
                erros += 1
                log.exception("Falha ao preparar %s: %s", nome, e)
        if erros:
            log.warning("Operação Brasil online com %d módulo(s) com problema. Veja os erros acima e use "
                        "/servidor verificar no Discord.", erros)
        else:
            log.info("✅ Operação Brasil online e sem erros. Use /servidor verificar para o relatório completo.")
        self._preparado = True


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "verificar":
        from .preflight import executar
        sys.exit(executar())
    cfg = config_mod.carregar()
    configurar_log(cfg.banco.parent)
    if len(sys.argv) > 1 and sys.argv[1] == "convite":
        # A 1ª parte do token de bot é o ID do bot (= Application ID) em base64.
        parte = cfg.token.split(".")[0]
        app_id = base64.b64decode(parte + "=" * (-len(parte) % 4)).decode()
        print("Abra este link, confira o servidor e clique em Autorizar:\n")
        print(f"https://discord.com/oauth2/authorize?client_id={app_id}&scope=bot+applications.commands"
              f"&permissions={PERMISSOES.value}&guild_id={cfg.guild_id}&disable_guild_select=true")
        return
    bot = OperacaoBrasil(cfg)
    try:
        bot.run(cfg.token, log_handler=None)
    except discord.PrivilegedIntentsRequired:
        print("\nERRO: no Portal do Desenvolvedor (aba Bot > Privileged Gateway Intents), ative "
              "'SERVER MEMBERS INTENT' e 'MESSAGE CONTENT INTENT' e salve.\n"
              "(Ou desligue em bot/.env: MEMBERS_INTENT=0 desativa o VIP automático dos boosters; "
              "MESSAGE_CONTENT_INTENT=0 deixa os transcripts sem o texto das mensagens.)")
    except discord.LoginFailure:
        print("\nERRO: token inválido. Gere um novo em Portal do Desenvolvedor > Bot > Reset Token.")


if __name__ == "__main__":
    main()
