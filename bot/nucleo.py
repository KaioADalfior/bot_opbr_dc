"""Funções de apoio que dependem do Discord: localizar cargos/canais, permissões e logs."""
from __future__ import annotations

import io
import logging
from datetime import timezone

import discord

from . import regras, textos
from .config import Config
from .db import Banco

log = logging.getLogger("operacao_brasil")

PERM_PARTICIPANTE = dict(view_channel=True, send_messages=True, attach_files=True, embed_links=True,
                         read_message_history=True)
PERM_BOT_CANAL = dict(view_channel=True, send_messages=True, attach_files=True, embed_links=True,
                      read_message_history=True)


def overwrite_seguro(g: discord.Guild, ow: discord.PermissionOverwrite) -> discord.PermissionOverwrite:
    """O Discord só deixa um bot liberar permissões que ele mesmo tem. Tira do pedido as liberações que o bot
    não tem (isso nunca dá mais acesso a ninguém). Os bloqueios são mantidos como estão."""
    meus = g.me.guild_permissions
    if meus.administrator:
        return ow
    permitir, negar = ow.pair()
    return discord.PermissionOverwrite.from_pair(discord.Permissions(permitir.value & meus.value), negar)


class Nucleo:
    def __init__(self, bot: discord.Client, cfg: Config, banco: Banco):
        self.bot = bot
        self.cfg = cfg
        self.db = banco
        self.web = None  # ServidorTranscripts (opcional)

    # -- localizar --------------------------------------------------------------
    @property
    def guild(self) -> discord.Guild | None:
        return self.bot.get_guild(self.cfg.guild_id)

    def canal(self, chave: str) -> discord.TextChannel | None:
        g = self.guild
        if g is None:
            return None
        valor = self.cfg.canais[chave]
        if valor.isdigit():
            ch = g.get_channel(int(valor))
            return ch if isinstance(ch, discord.TextChannel) else None
        alvo = regras.slug(valor)
        alvo_sa = regras.sem_acentos(alvo)
        for ch in g.text_channels:
            s = regras.slug(ch.name)
            if s == alvo or regras.sem_acentos(s) == alvo_sa:
                return ch
        return None

    def cargos_equipe(self) -> list[discord.Role]:
        g = self.guild
        if g is None:
            return []
        if self.cfg.ids_cargos_equipe:
            return [r for r in (g.get_role(i) for i in self.cfg.ids_cargos_equipe) if r]
        nomes = {regras.sem_acentos(n) for n in self.cfg.cargos_equipe}
        return [r for r in g.roles if regras.sem_acentos(regras.slug(r.name)) in nomes]

    def eh_equipe(self, membro: discord.abc.User) -> bool:
        if not isinstance(membro, discord.Member):
            return False
        if membro.guild.owner_id == membro.id or membro.guild_permissions.administrator:
            return True
        ids = {r.id for r in self.cargos_equipe()}
        return any(r.id in ids for r in membro.roles)

    async def membro(self, user_id: int) -> discord.Member | None:
        g = self.guild
        if g is None:
            return None
        m = g.get_member(user_id)
        if m:
            return m
        try:
            return await g.fetch_member(user_id)
        except discord.HTTPException:
            return None

    # -- preparação ------------------------------------------------------------
    async def categoria_tickets(self) -> discord.CategoryChannel:
        g = self.guild
        alvo = regras.slug(self.cfg.nome_categoria_tickets)
        for c in g.categories:
            if regras.slug(c.name) == alvo:
                return c
        overwrites = {g.default_role: discord.PermissionOverwrite(view_channel=False),
                      g.self_role: discord.PermissionOverwrite(**PERM_BOT_CANAL)}
        for r in self.cargos_equipe():
            overwrites[r] = discord.PermissionOverwrite(**PERM_PARTICIPANTE)
        cat = await g.create_category(self.cfg.nome_categoria_tickets, overwrites=overwrites,
                                      reason="Operação Brasil: categoria privada de tickets")
        log.info("Categoria de tickets criada: %s", cat.name)
        return cat

    async def garantir_acesso_bot(self):
        """Dá ao cargo do bot acesso aos canais que ele usa (somente leitura para membros)."""
        g = self.guild
        for chave in ("denuncias", "publicar_mod", "mods_publicados", "logs", "relatorios"):
            ch = self.canal(chave)
            if ch is None:
                log.warning("Canal '%s' não encontrado (configure em bot/.env).", self.cfg.canais[chave])
                continue
            atual = ch.overwrites_for(g.self_role)
            if all(getattr(atual, k) is True for k in PERM_BOT_CANAL):
                continue
            try:
                await ch.set_permissions(g.self_role, reason="Operação Brasil: acesso do bot", **PERM_BOT_CANAL)
                log.info("Acesso do bot garantido em #%s", ch.name)
            except discord.Forbidden:
                log.warning("Sem acesso a #%s (canal privado). Dê acesso manualmente: Editar canal > Permissões > "
                            "adicionar o cargo '%s' com Ver canal, Enviar mensagens, Inserir links, Anexar "
                            "arquivos e Ver histórico.", ch.name, g.self_role.name)

    # -- auditoria -------------------------------------------------------------
    async def registrar(self, ticket: dict | None, ator: discord.abc.User | int, acao: str,
                        detalhe: str = "", cor: int = textos.COR):
        ator_id = ator if isinstance(ator, int) else ator.id
        tid = ticket["id"] if ticket else None
        self.db.registrar(tid, ator_id, acao, detalhe)
        ch = self.canal("logs")
        if ch is None:
            return
        tipos = {"denuncia": ("🚨", "Atendimento"), "mod": ("📦", "Envio de mod"),
                 "contribuicao": ("💎", "Contribuição")}
        icone, rotulo = tipos.get(ticket["tipo"], ("🎫", "Ticket")) if ticket else ("🛰️", "Sistema")
        emb = discord.Embed(title=f"{icone} {acao}", description=detalhe[:3500] or None, color=cor,
                            timestamp=discord.utils.utcnow())
        emb.set_author(name=f"REGISTRO • {rotulo.upper()}")
        if ticket:
            emb.add_field(name="🎫 Ticket", value=f"`#{ticket['id']:04d}` · {rotulo}", inline=True)
            if ticket.get("canal_id"):
                emb.add_field(name="📍 Canal", value=f"<#{ticket['canal_id']}>", inline=True)
        emb.add_field(name="👤 Por", value=f"<@{ator_id}>", inline=True)
        emb.set_footer(text="Operação Brasil • registro automático")
        try:
            await ch.send(embed=emb, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException as e:
            log.warning("Falha ao registrar no canal de logs: %s", e)

    async def transcricao(self, canal: discord.TextChannel, ticket: dict) -> discord.File:
        linhas = [f"Transcrição do ticket #{ticket['id']:04d} ({ticket['tipo']}) — canal #{canal.name}",
                  f"Autor: {ticket['autor_id']}", ""]
        if not self.cfg.conteudo_mensagens:
            linhas.append("(Intent 'Message Content' desativada: textos de membros podem aparecer vazios.)\n")
        async for m in canal.history(limit=None, oldest_first=True):
            hora = m.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            texto = m.content or ""
            for e in m.embeds:
                texto += f"\n[embed] {e.title or ''} {e.description or ''}"
            for a in m.attachments:
                texto += f"\n[anexo] {a.filename} {a.url}"
            linhas.append(f"[{hora}] {m.author} ({m.author.id}): {texto}")
        return discord.File(io.BytesIO("\n".join(linhas).encode("utf-8")),
                            filename=f"ticket-{ticket['id']:04d}.txt")
