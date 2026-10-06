"""VIP: concessão pela equipe (tickets de contribuição) e VIP automático para quem impulsiona o servidor."""
from __future__ import annotations

import logging

import discord
from discord.ext import commands, tasks

from .. import regras, textos
from ..nucleo import Nucleo

log = logging.getLogger("operacao_brasil")


def cargo_vip(n: Nucleo) -> discord.Role | None:
    g = n.guild
    if g is None:
        return None
    alvo = n.cfg.cargo_vip
    if alvo.isdigit():
        return g.get_role(int(alvo))
    alvo = regras.sem_acentos(alvo.casefold())
    for r in g.roles:
        if regras.sem_acentos(regras.slug(r.name)) == alvo:
            return r
    return None


def problema_cargo(n: Nucleo) -> str | None:
    """Explica por que o bot não consegue dar o cargo VIP (ou None se está tudo certo)."""
    g = n.guild
    r = cargo_vip(n)
    if r is None:
        return f"Cargo VIP não encontrado (procurei por '{n.cfg.cargo_vip}'; ajuste CARGO_VIP em bot/.env)."
    if not g.me.guild_permissions.manage_roles:
        return "O bot não tem a permissão Gerenciar cargos."
    if g.me.top_role <= r:
        return (f"O cargo do bot ({g.me.top_role.name}) precisa ficar ACIMA de '{r.name}' em "
                "Configurações do Servidor > Cargos.")
    return None


def eh_booster(m: discord.Member) -> bool:
    return m.premium_since is not None


async def dar_vip(n: Nucleo, membro: discord.Member, origem: str, por: int | None = None,
                  ticket_id: int | None = None) -> str | None:
    """Dá o cargo VIP. Retorna uma mensagem de erro, ou None se deu certo."""
    erro = problema_cargo(n)
    if erro:
        return erro
    r = cargo_vip(n)
    try:
        if r not in membro.roles:
            await membro.add_roles(r, reason=f"VIP ({origem})" + (f" por {por}" if por else ""))
    except discord.HTTPException as e:
        return f"O Discord recusou: {e}"
    n.db.salvar_vip(membro.id, origem, por, ticket_id)
    return None


async def tirar_vip(n: Nucleo, membro: discord.Member, motivo: str) -> str | None:
    erro = problema_cargo(n)
    if erro:
        return erro
    r = cargo_vip(n)
    try:
        if r in membro.roles:
            await membro.remove_roles(r, reason=motivo)
    except discord.HTTPException as e:
        return f"O Discord recusou: {e}"
    n.db.remover_vip(membro.id)
    return None


class Vip(commands.Cog):
    def __init__(self, bot: commands.Bot, n: Nucleo):
        self.bot, self.n = bot, n

    async def preparar(self):
        erro = problema_cargo(self.n)
        if erro:
            log.error("VIP: %s", erro)
            return
        if not self.n.cfg.boost_vip:
            return
        if not self.bot.intents.members:
            log.warning("VIP automático para boosters desligado: ative 'SERVER MEMBERS INTENT' no Portal e use "
                        "MEMBERS_INTENT=1 em bot/.env.")
            return
        await self.sincronizar()
        if not self.sincronia.is_running():
            self.sincronia.start()

    async def sincronizar(self) -> tuple[int, int]:
        """Garante VIP para todos os boosters e tira de quem só tinha VIP por boost e parou de impulsionar."""
        g = self.n.guild
        if g is None or problema_cargo(self.n):
            return 0, 0
        dados, tirados = 0, 0
        for m in g.premium_subscribers:
            if cargo_vip(self.n) not in m.roles or not self.n.db.vip(m.id):
                if await dar_vip(self.n, m, "boost") is None:
                    dados += 1
        for v in self.n.db.vips("boost"):
            m = g.get_member(v["user_id"])
            if m is None:
                self.n.db.remover_vip(v["user_id"])       # saiu do servidor
                continue
            if not eh_booster(m):
                if await tirar_vip(self.n, m, "Parou de impulsionar o servidor") is None:
                    tirados += 1
        if dados or tirados:
            log.info("VIP por boost sincronizado: +%d / -%d", dados, tirados)
        return dados, tirados

    @tasks.loop(hours=6)
    async def sincronia(self):
        await self.sincronizar()

    @sincronia.before_loop
    async def _antes(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_member_update(self, antes: discord.Member, depois: discord.Member):
        if not self.n.cfg.boost_vip or depois.guild.id != self.n.cfg.guild_id:
            return
        if not eh_booster(antes) and eh_booster(depois):
            erro = await dar_vip(self.n, depois, "boost")
            if erro:
                log.warning("Não foi possível dar VIP ao booster %s: %s", depois, erro)
                return
            log.info("%s impulsionou o servidor: VIP concedido.", depois)
            await self.n.registrar(None, self.bot.user.id, "VIP por impulso",
                                   f"{depois.mention} impulsionou o servidor e recebeu VIP.", textos.COR_OK)
            await self._agradecer(depois)
        elif eh_booster(antes) and not eh_booster(depois):
            v = self.n.db.vip(depois.id)
            if v and v["origem"] == "boost":
                await tirar_vip(self.n, depois, "Parou de impulsionar o servidor")
                log.info("%s parou de impulsionar: VIP removido.", depois)
                await self.n.registrar(None, self.bot.user.id, "VIP por impulso encerrado",
                                       f"{depois.mention} parou de impulsionar; VIP removido.")

    async def _agradecer(self, membro: discord.Member):
        ch = self.n.canal("vips")
        if ch is None:
            return
        emb = discord.Embed(
            title="💎 Novo VIP!",
            description=(f"{membro.mention} **impulsionou o servidor** e agora é **VIP**.\n"
                         "Obrigado por fortalecer a Operação Brasil! 🇧🇷"),
            color=0xF47FFF)
        emb.set_thumbnail(url=membro.display_avatar.url)
        try:
            await ch.send(embed=emb, allowed_mentions=discord.AllowedMentions(users=[membro]))
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot, n: Nucleo) -> Vip:
    c = Vip(bot, n)
    await bot.add_cog(c, guild=discord.Object(n.cfg.guild_id))
    return c
