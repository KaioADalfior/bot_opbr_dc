"""Mensagens fixas dos canais e verificação completa do servidor.

/servidor publicar   — publica/atualiza as mensagens de todos os canais e remove as antigas do bot de configuração
/servidor verificar  — confere canais, permissões, painéis, mensagens, cargos, intents e transcripts
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from .. import conteudo as K
from .. import regras, textos
from ..nucleo import Nucleo, overwrite_seguro

log = logging.getLogger("operacao_brasil")

ASSETS = Path(__file__).resolve().parents[1] / "assets"
RAIZ = Path(__file__).resolve().parents[2]
_MARCADOR = re.compile(r"\{c:([a-z0-9_]+)\}")
PERM_BOT_TEXTO = dict(view_channel=True, send_messages=True, embed_links=True, attach_files=True,
                      read_message_history=True)


# ---------------------------------------------------------------------------
# Localizar canais e montar mensagens
# ---------------------------------------------------------------------------
def localizar(g: discord.Guild, chave: str) -> discord.abc.GuildChannel | None:
    """Acha o canal pelo nome (ignorando emoji/separador), preferindo a categoria esperada."""
    if chave not in K.CANAIS:
        return None
    nome, cat, tipo, _ = K.CANAIS[chave]
    alvo = regras.sem_acentos(regras.slug(nome))
    cat_alvo = regras.sem_acentos(regras.slug(K.CATEGORIAS[cat][0]))
    classe = discord.VoiceChannel if tipo == "voz" else discord.TextChannel
    achados = [c for c in g.channels if isinstance(c, classe) and regras.sem_acentos(regras.slug(c.name)) == alvo]
    for c in achados:
        if c.category and regras.sem_acentos(regras.slug(c.category.name)) == cat_alvo:
            return c
    return achados[0] if achados else None


def renderizar(texto: str, g: discord.Guild | None) -> str:
    def troca(m: re.Match) -> str:
        ch = localizar(g, m.group(1)) if g else None
        if ch is not None:
            return f"<#{ch.id}>"
        nome = K.CANAIS.get(m.group(1), (m.group(1),))[0]
        return f"**#{regras.slug(nome)}**"
    return _MARCADOR.sub(troca, texto or "")


def banner_de(chave: str) -> Path | None:
    arq = ASSETS / f"canal_{chave}.png"
    return arq if arq.is_file() else None


def montar(chave: str, g: discord.Guild | None) -> tuple[list[discord.Embed], list[discord.File], str]:
    """Embeds + arquivos + hash (para saber se a mensagem publicada está desatualizada)."""
    _, cat, _, _ = K.CANAIS[chave]
    cor = K.CATEGORIAS[cat][1]
    blocos = K.MENSAGENS[chave]
    embeds: list[discord.Embed] = []
    arquivos: list[discord.File] = []
    banner = banner_de(chave)
    if banner:
        topo = discord.Embed(color=cor)
        topo.set_image(url=f"attachment://{banner.name}")
        embeds.append(topo)
        arquivos.append(discord.File(banner, filename=banner.name))
    renderizado = []
    for i, b in enumerate(blocos):
        emb = discord.Embed(title=b.get("titulo"), description=renderizar(b.get("texto"), g) or None, color=cor)
        if i == 0:
            emb.set_author(name="GHOST RECON® | OPERAÇÃO BRASIL")
        campos = [(n, renderizar(v, g), inl) for n, v, inl in b.get("campos", [])]
        for n, v, inl in campos:
            emb.add_field(name=n, value=v[:1024], inline=inl)
        if i == len(blocos) - 1:
            emb.set_footer(text=K.RODAPE)
        embeds.append(emb)
        renderizado.append([b.get("titulo"), emb.description, campos])
    digest = hashlib.sha256(json.dumps([renderizado, cor], ensure_ascii=False).encode())
    if banner:
        digest.update(banner.read_bytes())
    return embeds, arquivos, digest.hexdigest()[:16]


def ids_do_configurador(gid: int) -> dict[str, list[int]]:
    """IDs das mensagens publicadas pelo antigo bot de configuração (estado/estado-<servidor>.json)."""
    arq = RAIZ / "estado" / f"estado-{gid}.json"
    try:
        dados = json.loads(arq.read_text(encoding="utf-8"))
        return {k: [int(x) for x in v] for k, v in dados.get("mensagens", {}).items()}
    except (OSError, ValueError):
        return {}


# ---------------------------------------------------------------------------
# Plano de publicação
# ---------------------------------------------------------------------------
@dataclass
class Item:
    acao: str            # publicar | atualizar | ok | apagar | falta_canal | sem_permissao
    chave: str
    canal: discord.abc.GuildChannel | None = None
    msg_id: int | None = None
    detalhe: str = ""


@dataclass
class Plano:
    itens: list[Item] = field(default_factory=list)

    def de(self, *acoes) -> list[Item]:
        return [i for i in self.itens if i.acao in acoes]


async def planejar(bot: commands.Bot, n: Nucleo) -> Plano:
    g = n.guild
    p = Plano()
    antigos = ids_do_configurador(g.id)
    for chave, (nome, _cat, tipo, _fixar) in K.CANAIS.items():
        if tipo == "voz":
            continue
        ch = localizar(g, chave)
        if ch is None:
            if chave in K.MENSAGENS:
                p.itens.append(Item("falta_canal", chave, detalhe=nome))
            continue
        perms = ch.permissions_for(g.me)
        # Mensagens antigas do bot de configuração
        if perms.view_channel and perms.read_message_history:
            ids_antigos = set(antigos.get(chave, []))
            try:
                async for m in ch.history(limit=60):
                    if m.author.id == g.me.id or not m.author.bot:
                        continue
                    titulos = {e.title for e in m.embeds if e.title}
                    if m.id in ids_antigos or titulos & K.TITULOS_LEGADOS:
                        p.itens.append(Item("apagar", chave, ch, m.id, next(iter(titulos), "mensagem antiga")))
            except discord.HTTPException:
                pass
        if chave not in K.MENSAGENS or chave in K.CANAIS_DE_PAINEL:
            continue
        if not (perms.view_channel and perms.send_messages and perms.embed_links and perms.attach_files):
            p.itens.append(Item("sem_permissao", chave, ch, detalhe="o bot precisa ver, enviar, inserir links e "
                                                                    "anexar arquivos"))
            continue
        _, _, h = montar(chave, g)
        salvo = n.db.mensagem_canal(chave)
        if salvo and salvo["canal_id"] == ch.id:
            try:
                await ch.fetch_message(salvo["msg_id"])
                p.itens.append(Item("ok" if salvo["hash"] == h else "atualizar", chave, ch, salvo["msg_id"]))
                continue
            except discord.NotFound:
                pass
            except discord.HTTPException as e:
                p.itens.append(Item("sem_permissao", chave, ch, detalhe=str(e)))
                continue
        p.itens.append(Item("publicar", chave, ch))
    return p


async def garantir_acesso(n: Nucleo) -> list[str]:
    """Dá ao cargo do bot acesso de escrita nos canais onde ele publica mensagens fixas."""
    g = n.guild
    avisos = []
    for chave in K.MENSAGENS:
        ch = localizar(g, chave)
        if ch is None or chave in K.CANAIS_DE_PAINEL:
            continue
        perms = ch.permissions_for(g.me)
        if all(getattr(perms, k) for k in PERM_BOT_TEXTO):
            continue
        try:
            await ch.set_permissions(g.self_role, reason="Operação Brasil: mensagens fixas",
                                     overwrite=overwrite_seguro(g, discord.PermissionOverwrite(**PERM_BOT_TEXTO)))
            log.info("Acesso do bot garantido em #%s", ch.name)
        except discord.HTTPException:
            avisos.append(f"#{ch.name}: adicione o cargo **{g.self_role.name}** nas permissões do canal "
                          "(Ver canal, Enviar mensagens, Inserir links, Anexar arquivos, Ver histórico).")
    return avisos


async def executar(n: Nucleo, plano: Plano, apagar_antigas: bool = True) -> list[str]:
    """Executa o plano. Retorna a lista de problemas."""
    g = n.guild
    problemas = []
    for it in plano.de("publicar", "atualizar"):
        embeds, arquivos, h = montar(it.chave, g)
        try:
            if it.acao == "atualizar":
                await it.canal.get_partial_message(it.msg_id).edit(embeds=embeds, attachments=arquivos)
                msg_id = it.msg_id
            else:
                msg = await it.canal.send(embeds=embeds, files=arquivos,
                                          allowed_mentions=discord.AllowedMentions.none())
                msg_id = msg.id
                if K.CANAIS[it.chave][3]:
                    try:
                        await msg.pin(reason="Mensagem fixa do canal")
                    except discord.HTTPException:
                        pass
            n.db.salvar_mensagem_canal(it.chave, it.canal.id, msg_id, h)
            log.info("Mensagem de #%s %s", it.canal.name, "atualizada" if it.acao == "atualizar" else "publicada")
        except discord.HTTPException as e:
            problemas.append(f"#{it.canal.name}: {e}")
            log.warning("Falha na mensagem de #%s: %s", it.canal.name, e)
    if apagar_antigas:
        for it in plano.de("apagar"):
            try:
                await it.canal.get_partial_message(it.msg_id).delete()
                log.info("Mensagem antiga removida de #%s (%s)", it.canal.name, it.detalhe)
            except discord.Forbidden:
                problemas.append(f"#{it.canal.name}: sem permissão para apagar a mensagem antiga "
                                 "(o bot precisa de 'Gerenciar mensagens')")
            except discord.NotFound:
                pass
            except discord.HTTPException as e:
                problemas.append(f"#{it.canal.name}: {e}")
    return problemas


def resumo_plano(p: Plano) -> discord.Embed:
    emb = discord.Embed(title="📝 Mensagens dos canais", color=textos.COR)
    def lista(itens, fmt):  # noqa: E306
        txt = "\n".join(fmt(i) for i in itens[:15]) + (f"\n… e mais {len(itens) - 15}" if len(itens) > 15 else "")
        return txt[:1024] or "—"
    for rot, acoes, fmt in (
        ("🆕 Publicar", ("publicar",), lambda i: f"<#{i.canal.id}>"),
        ("✏️ Atualizar", ("atualizar",), lambda i: f"<#{i.canal.id}>"),
        ("🗑️ Remover (antigas do Configurador)", ("apagar",), lambda i: f"<#{i.canal.id}> · {i.detalhe[:40]}"),
        ("⚠️ Sem permissão", ("sem_permissao",), lambda i: f"<#{i.canal.id}> · {i.detalhe[:60]}"),
        ("❌ Canal não encontrado", ("falta_canal",), lambda i: i.detalhe),
    ):
        itens = p.de(*acoes)
        if itens:
            emb.add_field(name=f"{rot} ({len(itens)})", value=lista(itens, fmt), inline=False)
    ok = len(p.de("ok"))
    emb.description = f"✅ **{ok}** canal(is) já estão em dia."
    return emb


# ---------------------------------------------------------------------------
# Verificação completa
# ---------------------------------------------------------------------------
@dataclass
class Checagem:
    status: str   # ok | aviso | falha
    nome: str
    detalhe: str = ""


ICONE = {"ok": "✅", "aviso": "⚠️", "falha": "❌"}


async def verificar(bot: commands.Bot, n: Nucleo) -> list[Checagem]:
    from . import squads as SQ
    from . import vip as V
    from ..permissoes import PERMISSOES
    g = n.guild
    r: list[Checagem] = []

    def add(ok: bool | None, nome: str, detalhe: str = "", aviso: bool = False):
        r.append(Checagem("ok" if ok else ("aviso" if aviso else "falha"), nome, detalhe))

    # 1. Estrutura
    faltando = [K.CANAIS[c][0] for c in K.CANAIS if localizar(g, c) is None]
    add(not faltando, "Canais da estrutura", f"Faltando: {', '.join(faltando)}" if faltando
        else f"{len(K.CANAIS)} canais encontrados")
    cats, salas, _ = SQ.salas_antigas(g)
    add(not salas and not cats, "Salas fixas antigas removidas",
        f"Ainda existem {len(salas)} calls; use /squads remover-salas" if (salas or cats) else "", aviso=True)

    # 2. Bot: permissões, hierarquia e intents
    p = g.me.guild_permissions
    falta = [k for k, v in PERMISSOES if v and not getattr(p, k)]
    add(not falta, "Permissões do bot no servidor",
        f"Faltando: {', '.join(falta)}. Rode `python -m bot convite` e autorize de novo." if falta else "")
    add(not p.administrator, "Bot sem Administrador (recomendado)", "O bot está com Administrador.", aviso=True)
    erro_vip = V.problema_cargo(n)
    add(erro_vip is None, "Cargo do bot acima do 💎 VIP", erro_vip or "")
    add(bot.intents.members, "Intent de membros (VIP de boosters)", "" if bot.intents.members else
        "Ligue SERVER MEMBERS INTENT no Portal e use MEMBERS_INTENT=1.", aviso=True)
    add(bot.intents.message_content, "Intent de conteúdo (transcripts completos)", "" if bot.intents.message_content
        else "Transcripts sem o texto dos membros.", aviso=True)

    # 3. Canais onde o bot publica
    sem_acesso = []
    for chave in [*K.MENSAGENS, "contribuicao", "abrir_squad"]:
        ch = localizar(g, chave)
        if ch is None:
            continue
        pm = ch.permissions_for(g.me)
        if not (pm.view_channel and pm.send_messages and pm.embed_links):
            sem_acesso.append(f"#{ch.name}")
    add(not sem_acesso, "Bot consegue publicar nos canais", "Sem acesso: " + ", ".join(sem_acesso)
        if sem_acesso else "")

    # 4. Canais só de botões
    abertos = []
    for chave in ("abrir_squad", "squad_partida", "contribuicao"):
        ch = localizar(g, chave)
        if ch is not None and ch.permissions_for(g.default_role).send_messages:
            abertos.append(f"#{ch.name}")
    add(not abertos, "Canais de painel sem digitação de membros", "Membros podem escrever em: " + ", ".join(abertos)
        if abertos else "", aviso=True)

    # 5. Painéis
    paineis = {"denuncia": "denuncias", "mod": "publicar_mod", "contribuicao": "contribuicao",
               "squad": "abrir_squad", "squad_aviso": "squad_partida"}
    ruins = []
    for chave, canal in paineis.items():
        salvo = n.db.painel(chave)
        ch = localizar(g, canal)
        if not salvo or ch is None or salvo["canal_id"] != ch.id:
            ruins.append(chave)
            continue
        try:
            await ch.fetch_message(salvo["msg_id"])
        except discord.HTTPException:
            ruins.append(chave)
    add(not ruins, "Painéis publicados", "Faltando: " + ", ".join(ruins) +
        " (reinicie o bot ou use /tickets paineis e /squads painel)" if ruins else f"{len(paineis)} painéis")

    # 6. Mensagens fixas
    plano = await planejar(bot, n)
    pend = plano.de("publicar", "atualizar")
    add(not pend, "Mensagens fixas dos canais", f"{len(pend)} para publicar/atualizar: use /servidor publicar"
        if pend else f"{len(plano.de('ok'))} canais em dia")
    antigas = plano.de("apagar")
    add(not antigas, "Mensagens antigas do Configurador removidas",
        f"{len(antigas)} ainda nos canais: use /servidor publicar" if antigas else "", aviso=True)
    sp = plano.de("sem_permissao")
    if sp:
        add(False, "Acesso aos canais de mensagens fixas", ", ".join(f"#{i.canal.name}" for i in sp))

    # 7. Transcripts e squads
    web = n.web
    add(web is not None and bool(web.url_publica), "Link público dos transcripts",
        web.url_publica if web and web.url_publica else "Sem link: transcripts irão como arquivo anexo.",
        aviso=True)
    ativos = n.db.squads_ativos()
    orfaos = [s["id"] for s in ativos if not s.get("voz_id") or g.get_channel(s["voz_id"]) is None]
    add(not orfaos, "Squads ativos consistentes", f"Squads sem call: {orfaos}" if orfaos
        else f"{len(ativos)} squad(s) ativo(s)", aviso=True)
    if bot.intents.members and erro_vip is None:
        sem_vip = [m for m in g.premium_subscribers if V.cargo_vip(n) not in m.roles]
        add(not sem_vip, "Boosters com VIP", f"{len(sem_vip)} booster(s) sem VIP" if sem_vip
            else f"{len(g.premium_subscribers)} booster(s)")
    return r


def embed_verificacao(checks: list[Checagem]) -> discord.Embed:
    falhas = sum(1 for c in checks if c.status == "falha")
    avisos = sum(1 for c in checks if c.status == "aviso")
    cor = textos.COR_ERRO if falhas else (textos.COR_ALERTA if avisos else textos.COR_OK)
    emb = discord.Embed(title="🛰️ Verificação do servidor", color=cor, timestamp=datetime.now(timezone.utc))
    emb.description = (f"**{len(checks) - falhas - avisos}** ok · **{avisos}** aviso(s) · **{falhas}** falha(s)\n\n"
                       + "\n".join(f"{ICONE[c.status]} **{c.nome}**" + (f"\n-# {c.detalhe[:180]}" if c.detalhe
                                                                        and c.status != "ok" else "")
                                   for c in checks))[:4000]
    emb.set_footer(text="Relatório completo salvo em bot/dados/relatorios")
    return emb


def salvar_relatorio(checks: list[Checagem], pasta: Path) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    agora = datetime.now()
    arq = pasta / f"verificar-{agora:%Y%m%d-%H%M%S}.md"
    linhas = [f"# Verificação do servidor — {agora:%d/%m/%Y %H:%M}", "", "| | Item | Detalhe |", "|---|---|---|"]
    linhas += [f"| {ICONE[c.status]} | {c.nome} | {c.detalhe.replace('|', '/')} |" for c in checks]
    arq.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return arq


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------
class Confirmar(discord.ui.View):
    def __init__(self, autor_id: int):
        super().__init__(timeout=180)
        self.autor_id = autor_id
        self.ok: bool | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.autor_id

    @discord.ui.button(label="Publicar agora", emoji="🚀", style=discord.ButtonStyle.success)
    async def sim(self, interaction: discord.Interaction, _b):
        self.ok = True
        await interaction.response.edit_message(content="⏳ Publicando…", view=None)
        self.stop()

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def nao(self, interaction: discord.Interaction, _b):
        self.ok = False
        await interaction.response.edit_message(content="Nada foi alterado.", embed=None, view=None)
        self.stop()


class Servidor(commands.Cog):
    grupo = app_commands.Group(name="servidor", description="Mensagens e verificação do servidor",
                               default_permissions=discord.Permissions(manage_guild=True), guild_only=True)

    def __init__(self, bot: commands.Bot, n: Nucleo):
        self.bot, self.n = bot, n

    async def preparar(self):
        """No início: mantém atualizadas as mensagens já publicadas pelo bot (não cria nem apaga nada)."""
        for aviso in await garantir_acesso(self.n):
            log.warning("Mensagens: %s", re.sub(r"\*\*", "", aviso))
        plano = await planejar(self.bot, self.n)
        atualizar = [i for i in plano.de("atualizar")]
        if atualizar:
            await executar(self.n, Plano(atualizar), apagar_antigas=False)
        pend, antigas = plano.de("publicar"), plano.de("apagar")
        if pend or antigas:
            log.warning("Mensagens: %d canal(is) sem a mensagem nova e %d mensagem(ns) antiga(s). "
                        "Use /servidor publicar no Discord.", len(pend), len(antigas))
        else:
            log.info("Mensagens dos canais em dia (%d).", len(plano.de("ok")))

    @grupo.command(name="publicar", description="Publica/atualiza as mensagens de todos os canais")
    @app_commands.describe(simular="Só mostra o que seria feito, sem alterar nada")
    async def cmd_publicar(self, interaction: discord.Interaction, simular: bool = False):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await garantir_acesso(self.n)
        plano = await planejar(self.bot, self.n)
        emb = resumo_plano(plano)
        if simular or not plano.de("publicar", "atualizar", "apagar"):
            emb.set_footer(text="Simulação: nada foi alterado." if simular else "Nada a fazer.")
            await interaction.followup.send(embed=emb, ephemeral=True)
            return
        v = Confirmar(interaction.user.id)
        await interaction.followup.send(embed=emb, view=v, ephemeral=True)
        await v.wait()
        if not v.ok:
            return
        problemas = await executar(self.n, plano)
        await self.n.registrar(None, interaction.user, "Mensagens dos canais publicadas",
                               f"{len(plano.de('publicar'))} publicadas, {len(plano.de('atualizar'))} atualizadas, "
                               f"{len(plano.de('apagar'))} antigas removidas.")
        fim = discord.Embed(title="✅ Mensagens publicadas", color=textos.COR_OK if not problemas else textos.COR_ALERTA,
                            description=(f"🆕 {len(plano.de('publicar'))} publicadas · ✏️ {len(plano.de('atualizar'))} "
                                         f"atualizadas · 🗑️ {len(plano.de('apagar'))} antigas removidas"))
        if problemas:
            fim.add_field(name="⚠️ Problemas", value="\n".join(problemas)[:1024], inline=False)
        await interaction.edit_original_response(content=None, embed=fim, view=None)

    @grupo.command(name="verificar", description="Confere canais, permissões, painéis e mensagens")
    async def cmd_verificar(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        checks = await verificar(self.bot, self.n)
        arq = salvar_relatorio(checks, self.n.cfg.banco.parent / "relatorios")
        log.info("Verificação salva em %s", arq)
        await interaction.followup.send(embed=embed_verificacao(checks), ephemeral=True)


async def setup(bot: commands.Bot, n: Nucleo) -> Servidor:
    c = Servidor(bot, n)
    await bot.add_cog(c, guild=discord.Object(n.cfg.guild_id))
    return c
