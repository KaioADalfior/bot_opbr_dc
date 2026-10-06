"""Squads em #squad-partida: painel → assistente → call de voz exclusiva + card com "Eu vou"."""
from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import datetime
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands, tasks

from .. import catalogo as C
from .. import regras, textos
from ..nucleo import Nucleo, overwrite_seguro

log = logging.getLogger("operacao_brasil")

NUCLEO: Nucleo | None = None
COOLDOWN_CRIAR = 60  # segundos entre squads criados pela mesma pessoa

# Permissões que o bot precisa para gerenciar as calls dos squads
PERM_VOZ_INTEGRANTE = dict(view_channel=True, connect=True, speak=True, stream=True, use_voice_activation=True,
                           send_messages=True, read_message_history=True)
PERM_VOZ_BOT = dict(view_channel=True, connect=True, speak=True, stream=True, use_voice_activation=True,
                    send_messages=True, embed_links=True, read_message_history=True,
                    manage_channels=True, move_members=True)
PERM_VOZ_PUBLICO = dict(view_channel=True, connect=False, send_messages=False)  # todos veem; só o squad entra
NECESSARIAS = ("manage_channels", "manage_roles", "connect", "speak", "stream", "use_voice_activation",
               "move_members")


def nucleo() -> Nucleo:
    assert NUCLEO is not None
    return NUCLEO


def cog() -> "Squads":
    return nucleo().bot.get_cog("Squads")


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
_LINK = re.compile(r"(https?://|www\.|discord\.gg|\.com\b|\.gg\b)", re.I)


def limpar_nome(texto: str) -> str | None:
    """Nome do squad: 3 a 24 caracteres, sem links, menções ou símbolos que quebram o nome da call."""
    t = re.sub(r"[@#`*_~|<>\\]", "", texto or "")
    t = re.sub(r"\s+", " ", t).strip()
    if _LINK.search(t) or len(t) < 3:
        return None
    return t[:24]


def limpar_texto(texto: str, limite: int) -> str:
    t = (texto or "").replace("@everyone", "everyone").replace("@here", "here")
    t = re.sub(r"<@[!&]?\d+>", "", t)
    return re.sub(r"[ \t]+", " ", t).strip()[:limite]


def faltando_permissoes(g: discord.Guild) -> list[str]:
    p = g.me.guild_permissions
    if p.administrator:
        return []
    return [n for n in NECESSARIAS if not getattr(p, n)]


def link_canal(gid: int, cid: int) -> str:
    return f"https://discord.com/channels/{gid}/{cid}"


ASSETS = Path(__file__).resolve().parents[1] / "assets"
BARRA = {"breakpoint": "🟦", "wildlands": "🟩", "r6": "🟪"}


def banner(nome: str) -> discord.File | None:
    """Imagem de topo dos embeds (bot/assets). Um discord.File só pode ser enviado uma vez."""
    arq = ASSETS / nome
    return discord.File(arq, filename=nome) if arq.is_file() else None


def _usar_banner(emb: discord.Embed, nome: str) -> discord.Embed:
    if (ASSETS / nome).is_file():
        emb.set_image(url=f"attachment://{nome}")
    return emb


def integrantes(s: dict) -> list[int]:
    return [s["lider_id"], *s["membros"]]


# ---------------------------------------------------------------------------
# Card do squad
# ---------------------------------------------------------------------------
def embed_squad(s: dict, guild: discord.Guild | None) -> discord.Embed:
    jogo = C.JOGOS_SQUAD[s["jogo"]]
    plat = C.PLATAFORMAS_SQUAD.get(s["plataforma"], {"emoji": "🎮", "nome": s["plataforma"]})
    modo = C.MODOS.get(s["jogo"], {}).get(s["modo"], {"emoji": "🎯", "nome": s["modo"]})
    estilo = C.ESTILOS.get(s["estilo"] or "")
    membros = integrantes(s)
    ocupadas, vagas = len(membros), s["vagas"]
    completo = ocupadas >= vagas
    criado = datetime.fromisoformat(s["criado_em"])
    ts = int(criado.timestamp())

    barra = BARRA.get(s["jogo"], "🟦") * ocupadas + "⬛" * (vagas - ocupadas)
    situacao = "🔒 **Esquadrão fechado**" if completo else \
        f"faltam **{vagas - ocupadas}** {'vaga' if vagas - ocupadas == 1 else 'vagas'}"
    ficha = [f"> {jogo['emoji']} **{jogo['curto']}** ‧ {plat['emoji']} {plat['nome']}",
             f"> {modo['emoji']} {modo['nome']}" + (f" ‧ {estilo['emoji']} {estilo['nome']}" if estilo else "")]

    emb = discord.Embed(title=f"{jogo['emoji']}  {s['nome']}",
                        description=f"{barra}  `{ocupadas}/{vagas}` · {situacao}\n\n" + "\n".join(ficha),
                        color=textos.COR_OK if completo else jogo["cor"], timestamp=criado)
    lider = guild.get_member(s["lider_id"]) if guild else None
    emb.set_author(name=f"SQUAD #{s['id']:04d}  •  {'COMPLETO' if completo else 'RECRUTANDO'}",
                   icon_url=lider.display_avatar.url if lider else None)

    emb.add_field(name="👑 Líder", value=f"<@{s['lider_id']}>", inline=True)
    emb.add_field(name="🔊 Call", value=f"<#{s['voz_id']}>" if s.get("voz_id") else "—", inline=True)
    emb.add_field(name="🕐 Aberto", value=f"<t:{ts}:R>", inline=True)
    if s.get("id_jogo"):
        emb.add_field(name="🎮 ID do líder no jogo", value=f"`{s['id_jogo']}`", inline=False)
    if s.get("obs"):
        briefing = "\n".join(f"> {linha}" for linha in s["obs"].replace("`", "'").splitlines() if linha.strip())
        emb.add_field(name="📋 Briefing", value=briefing[:1024] or "—", inline=False)

    na_call = set()
    voz = guild.get_channel(s["voz_id"]) if guild and s.get("voz_id") else None
    if isinstance(voz, discord.VoiceChannel):
        na_call = set(voz.voice_states.keys())
    linhas = []
    for i in range(vagas):
        n = f"`{i + 1:02d}`"
        if i < ocupadas:
            uid = membros[i]
            linhas.append(f"{n} {'👑' if i == 0 else '🎖️'} <@{uid}>{'  🔊' if uid in na_call else ''}")
        else:
            linhas.append(f"{n} ▫️ *vaga livre*")
    emb.add_field(name="🎖️ Esquadrão", value="\n".join(linhas), inline=False)
    _usar_banner(emb, f"squad_{s['jogo']}.png")
    emb.set_footer(text=f"✅ Eu vou para entrar  •  🔊 = na call  •  a call fecha após "
                        f"{nucleo().cfg.squad_vazio_min} min vazia")
    return emb


class BotaoSquad(discord.ui.DynamicItem[discord.ui.Button],
                 template=r"grb:sq:(?P<acao>entrar|sair|encerrar):(?P<sid>\d+)"):
    ROTULOS = {
        "entrar": ("Eu vou", "✅", discord.ButtonStyle.success),
        "sair": ("Sair", "🚪", discord.ButtonStyle.secondary),
        "encerrar": ("Encerrar", "🔒", discord.ButtonStyle.danger),
    }

    def __init__(self, acao: str, sid: int, completo: bool = False):
        rotulo, emoji, estilo = self.ROTULOS[acao]
        desativado = False
        if acao == "entrar" and completo:
            rotulo, desativado = "Esquadrão completo", True
        super().__init__(discord.ui.Button(label=rotulo, emoji=emoji, style=estilo, disabled=desativado,
                                           custom_id=f"grb:sq:{acao}:{sid}"))
        self.acao, self.sid = acao, sid

    @classmethod
    async def from_custom_id(cls, interaction, item, match: re.Match[str], /):
        return cls(match["acao"], int(match["sid"]))

    async def callback(self, interaction: discord.Interaction):
        c = cog()
        await interaction.response.defer(ephemeral=True, thinking=True)
        if self.acao == "entrar":
            await c.entrar(interaction, self.sid)
        elif self.acao == "sair":
            await c.sair(interaction, self.sid)
        else:
            await c.encerrar_por_botao(interaction, self.sid)


def view_squad(s: dict, gid: int) -> discord.ui.View:
    v = discord.ui.View(timeout=None)
    completo = len(integrantes(s)) >= s["vagas"]
    v.add_item(BotaoSquad("entrar", s["id"], completo))
    v.add_item(BotaoSquad("sair", s["id"]))
    if s.get("voz_id"):
        v.add_item(discord.ui.Button(label="Ir para a call", emoji="🔊", url=link_canal(gid, s["voz_id"])))
    v.add_item(BotaoSquad("encerrar", s["id"]))
    return v


# ---------------------------------------------------------------------------
# Assistente (efêmero): jogo, plataforma, modo, estilo → formulário
# ---------------------------------------------------------------------------
def _embed_assistente(esc: dict) -> discord.Embed:
    jogo = C.JOGOS_SQUAD.get(esc["jogo"] or "")
    passos = [
        ("Jogo", C.item(C.JOGOS_SQUAD, esc["jogo"]), esc["jogo"]),
        ("Plataforma", C.item(C.PLATAFORMAS_SQUAD, esc["plataforma"]), esc["plataforma"]),
        ("Modo", C.item(C.MODOS.get(esc["jogo"] or "", {}), esc["modo"]), esc["modo"]),
        ("Estilo", C.item(C.ESTILOS, esc["estilo"]) if esc["estilo"] else "*opcional*", esc["estilo"]),
    ]
    feitos = sum(1 for _, _, v in passos[:3] if v)
    barra = "🟩" * feitos + "⬛" * (3 - feitos)
    linhas = [f"{'✅' if v else '⬜'} **{rot}** ─ {txt if v or rot == 'Estilo' else '*escolha no menu*'}"
              for rot, txt, v in passos]
    emb = discord.Embed(title="🎯 Monte seu esquadrão",
                        description=f"{barra} `{feitos}/3` obrigatórios\n\n" + "\n".join(linhas),
                        color=jogo["cor"] if jogo else textos.COR)
    emb.set_author(name="ABRIR SQUAD  •  PASSO 1 DE 2")
    if jogo:
        emb.add_field(name="👥 Vagas", value=f"Você + **{jogo['vagas'] - 1}** jogadores", inline=True)
        emb.add_field(name="🔊 Call", value="Exclusiva, com o nome do squad", inline=True)
    emb.set_footer(text="Depois clique em ➡️ Continuar para dar o nome ao squad")
    return emb


class AssistenteSquad(discord.ui.View):
    def __init__(self, autor_id: int):
        super().__init__(timeout=600)
        self.autor_id = autor_id
        self.esc: dict = {"jogo": None, "plataforma": None, "modo": None, "estilo": None}
        self.sel_jogo = discord.ui.Select(placeholder="🎮 Escolha o jogo", row=0, options=[
            discord.SelectOption(label=j["nome"], value=k, emoji=j["emoji"], description=j["descricao"])
            for k, j in C.JOGOS_SQUAD.items()])
        self.sel_plat = discord.ui.Select(placeholder="💻 Escolha a plataforma", row=1, options=[
            discord.SelectOption(label=p["nome"], value=k, emoji=p["emoji"], description=p["descricao"])
            for k, p in C.PLATAFORMAS_SQUAD.items()])
        self.sel_modo = discord.ui.Select(placeholder="🎯 Escolha o jogo primeiro", row=2, disabled=True,
                                          options=[discord.SelectOption(label="—", value="_")])
        self.sel_estilo = discord.ui.Select(placeholder="🧩 Estilo de jogo (opcional)", row=3, options=[
            discord.SelectOption(label=e["nome"], value=k, emoji=e["emoji"], description=e["descricao"])
            for k, e in C.ESTILOS.items()])
        self.btn_ok = discord.ui.Button(label="Continuar", emoji="➡️", style=discord.ButtonStyle.success, row=4,
                                        disabled=True)
        self.btn_cancelar = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.secondary, row=4)
        for item, cb in ((self.sel_jogo, self._jogo), (self.sel_plat, self._plat), (self.sel_modo, self._modo),
                         (self.sel_estilo, self._estilo), (self.btn_ok, self._continuar),
                         (self.btn_cancelar, self._cancelar)):
            item.callback = cb
            self.add_item(item)
        self.origem: discord.Interaction | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.autor_id

    def _marcar(self):
        modos = C.MODOS.get(self.esc["jogo"] or "", {})
        if modos:
            self.sel_modo.disabled = False
            self.sel_modo.placeholder = "🎯 O que vocês vão jogar?"
            self.sel_modo.options = [discord.SelectOption(label=m["nome"], value=k, emoji=m["emoji"],
                                                          description=m["descricao"]) for k, m in modos.items()]
        for sel, valor in ((self.sel_jogo, self.esc["jogo"]), (self.sel_plat, self.esc["plataforma"]),
                           (self.sel_modo, self.esc["modo"]), (self.sel_estilo, self.esc["estilo"])):
            for opt in sel.options:
                opt.default = opt.value == valor
        self.btn_ok.disabled = not (self.esc["jogo"] and self.esc["plataforma"] and self.esc["modo"])

    async def _atualizar(self, interaction: discord.Interaction):
        self._marcar()
        await interaction.response.edit_message(embed=_embed_assistente(self.esc), view=self)

    async def _jogo(self, interaction: discord.Interaction):
        novo = self.sel_jogo.values[0]
        if novo != self.esc["jogo"]:
            self.esc["modo"] = None  # os modos mudam conforme o jogo
        self.esc["jogo"] = novo
        await self._atualizar(interaction)

    async def _plat(self, interaction: discord.Interaction):
        self.esc["plataforma"] = self.sel_plat.values[0]
        await self._atualizar(interaction)

    async def _modo(self, interaction: discord.Interaction):
        self.esc["modo"] = self.sel_modo.values[0]
        await self._atualizar(interaction)

    async def _estilo(self, interaction: discord.Interaction):
        self.esc["estilo"] = self.sel_estilo.values[0]
        await self._atualizar(interaction)

    async def _continuar(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ModalSquad(dict(self.esc), self))

    async def _cancelar(self, interaction: discord.Interaction):
        self.stop()
        await interaction.response.edit_message(content="Abertura de squad cancelada.", embed=None, view=None)

    async def concluir(self, texto: str, view: discord.ui.View | None = None):
        self.stop()
        if self.origem is not None:
            try:
                await self.origem.edit_original_response(content=texto, embed=None, view=view)
            except discord.HTTPException:
                pass


class ModalSquad(discord.ui.Modal):
    def __init__(self, esc: dict, assistente: AssistenteSquad | None = None):
        jogo = C.JOGOS_SQUAD[esc["jogo"]]
        super().__init__(title=f"🎮 Abrir squad — {jogo['curto']}"[:45])
        self.esc, self.assistente = esc, assistente
        self.nome = discord.ui.TextInput(label="Nome do squad (vira o nome da call)", min_length=3, max_length=24,
                                         placeholder="Ex.: Fantasmas de Auroa")
        self.id_jogo = discord.ui.TextInput(label="Seu nick/ID no jogo (opcional)", required=False, max_length=32,
                                            placeholder="Ubisoft Connect, PSN ou Gamertag")
        self.obs = discord.ui.TextInput(label="Observações (opcional)", style=discord.TextStyle.paragraph,
                                        required=False, max_length=200,
                                        placeholder="Ex.: dificuldade Extremo, precisa de microfone, "
                                                    "vamos fazer a missão X")
        for i in (self.nome, self.id_jogo, self.obs):
            self.add_item(i)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await cog().criar(interaction, self.esc, self.nome.value, self.id_jogo.value, self.obs.value,
                          self.assistente)


# ---------------------------------------------------------------------------
# Painel fixo em #squad-partida
# ---------------------------------------------------------------------------
class PainelSquadView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Abrir squad", emoji="🎯", style=discord.ButtonStyle.success,
                       custom_id="grb:sq:painel:abrir")
    async def abrir(self, interaction: discord.Interaction, _b: discord.ui.Button):
        erro = cog().pode_criar(interaction.user)
        if erro:
            await interaction.response.send_message(erro, ephemeral=True)
            return
        a = AssistenteSquad(interaction.user.id)
        a._marcar()
        await interaction.response.send_message(embed=_embed_assistente(a.esc), view=a, ephemeral=True)
        a.origem = interaction

    @discord.ui.button(label="Meu squad", emoji="🎧", style=discord.ButtonStyle.secondary,
                       custom_id="grb:sq:painel:meu")
    async def meu(self, interaction: discord.Interaction, _b: discord.ui.Button):
        n = nucleo()
        s = n.db.squad_do_usuario(interaction.user.id)
        if not s:
            await interaction.response.send_message("Você não está em nenhum squad agora. Clique em **Abrir squad** "
                                                    "ou em **✅ Eu vou** no card de alguém.", ephemeral=True)
            return
        v = discord.ui.View()
        if s.get("voz_id"):
            v.add_item(discord.ui.Button(label="Ir para a call", emoji="🔊", url=link_canal(n.guild.id, s["voz_id"])))
        if s.get("msg_id"):
            ch = n.canal("squad_partida")
            if ch:
                v.add_item(discord.ui.Button(label="Ver card", emoji="🃏",
                                             url=f"https://discord.com/channels/{n.guild.id}/{ch.id}/{s['msg_id']}"))
        papel = "líder" if s["lider_id"] == interaction.user.id else "integrante"
        await interaction.response.send_message(f"Você é **{papel}** do squad **{s['nome']}**.", view=v,
                                                ephemeral=True)


def embed_painel(cfg, partida_id: int | None = None) -> discord.Embed:
    partida = f"<#{partida_id}>" if partida_id else "#squad-partida"
    t = textos.PAINEL_SQUAD
    emb = discord.Embed(title=t["titulo"], description=t["intro"], color=textos.COR)
    emb.set_author(name="GHOST RECON® | OPERAÇÃO BRASIL")
    emb.add_field(name="🧭 Como funciona", value=t["passos"].format(partida=partida), inline=False)
    emb.add_field(name="👥 Vagas", value="💀 🌿 Ghost Recon: **4**\n👮 Siege: **5**", inline=True)
    emb.add_field(name="⏱️ Auto-limpeza", value=f"Call vazia por\n**{cfg.squad_vazio_min} min** é apagada", inline=True)
    emb.add_field(name="📌 Limite", value="**1 squad**\npor jogador", inline=True)
    emb.add_field(name="👀 Quer entrar num squad?", value=f"Os squads abertos estão em {partida}. "
                  "É só clicar em **✅ Eu vou** no card.", inline=False)
    _usar_banner(emb, "painel_squads.png")
    emb.set_footer(text="🛡️ As regras do servidor também valem nas calls dos squads")
    return emb


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------
class Squads(commands.Cog):
    grupo = app_commands.Group(name="squads", description="Administração dos squads",
                               default_permissions=discord.Permissions(manage_guild=True), guild_only=True)

    def __init__(self, bot: commands.Bot, n: Nucleo):
        self.bot, self.n = bot, n
        self.locks: dict[int, asyncio.Lock] = {}
        self.vazio_desde: dict[int, float] = {}
        self.ultimo_criado: dict[int, float] = {}
        self._agendados: dict[int, asyncio.Task] = {}

    def lock(self, sid: int) -> asyncio.Lock:
        return self.locks.setdefault(sid, asyncio.Lock())

    # -- preparação ----------------------------------------------------------
    async def preparar(self):
        g = self.n.guild
        falta = faltando_permissoes(g)
        if falta:
            log.error("Squads: o bot precisa das permissões %s. Rode 'python -m bot convite' e autorize de novo.",
                      falta)
        await self.garantir_canal()
        await self.garantir_painel()
        await self.garantir_aviso()
        # Reinício: confere squads que ficaram abertos
        agora = time.time()
        for s in self.n.db.squads_ativos():
            self.vazio_desde.setdefault(s["id"], agora)
        if not self.vigia.is_running():
            self.vigia.start()

    async def garantir_canal(self):
        """#abrir-squad (painel) e #squad-partida (cards): só o bot publica, membros usam os botões."""
        g = self.n.guild
        partida = self.n.canal("squad_partida")
        if partida is None:
            log.warning("Canal '%s' não encontrado (configure CANAL_SQUAD_PARTIDA em bot/.env).",
                        self.n.cfg.canais["squad_partida"])
        abrir = self.n.canal("abrir_squad")
        if abrir is None and partida is not None:
            try:
                abrir = await g.create_text_channel(
                    self.n.cfg.nome_canal_abrir_squad, category=partida.category, position=partida.position,
                    topic="Abra seu squad pelo painel: escolha o jogo, dê um nome e ganhe uma call exclusiva. "
                          "O card vai para o canal de squads.",
                    reason="Operação Brasil: canal para abrir squads")
                log.info("Canal #%s criado.", abrir.name)
            except discord.HTTPException as e:
                log.warning("Não foi possível criar o canal de abrir squad: %s", e)
        for ch, motivo in ((abrir, "painel de squads"), (partida, "cards de squads")):
            if ch is None:
                continue
            try:
                atual = ch.overwrites_for(g.self_role)
                if not (atual.send_messages and atual.embed_links and atual.view_channel):
                    await ch.set_permissions(g.self_role, reason=f"Operação Brasil: {motivo}",
                                             overwrite=overwrite_seguro(g, discord.PermissionOverwrite(
                                                 view_channel=True, send_messages=True, embed_links=True,
                                                 attach_files=True, read_message_history=True,
                                                 pin_messages=True)))
                if self.n.cfg.squad_travar_canal:
                    todos = ch.overwrites_for(g.default_role)
                    if todos.send_messages is not False or todos.create_public_threads is not False:
                        todos.update(send_messages=False, create_public_threads=False, create_private_threads=False)
                        await ch.set_permissions(g.default_role, overwrite=overwrite_seguro(g, todos),
                                                 reason="Operação Brasil: squads são abertos pelo painel")
                        log.info("#%s agora aceita só os botões (membros não digitam).", ch.name)
            except discord.Forbidden:
                log.warning("Sem permissão para ajustar #%s. Dê ao cargo do bot: Ver canal, Enviar mensagens, "
                            "Inserir links e Gerenciar permissões.", ch.name)

    async def garantir_painel(self, forcar: bool = False) -> str:
        ch = self.n.canal("abrir_squad")
        if ch is None:
            return "Canal de abrir squad não encontrado."
        partida = self.n.canal("squad_partida")
        emb, view = embed_painel(self.n.cfg, partida.id if partida else None), PainelSquadView()
        salvo = self.n.db.painel("squad")
        if salvo and salvo["canal_id"] == ch.id and not forcar:
            try:
                msg = await ch.fetch_message(salvo["msg_id"])
                arq = banner("painel_squads.png")
                await msg.edit(embed=emb, view=view, attachments=[arq] if arq else [])
                return f"Painel de squads atualizado em #{ch.name}"
            except discord.NotFound:
                pass
        elif salvo and salvo["canal_id"] != ch.id:
            # O painel mudou de canal: apaga o antigo (mensagem do próprio bot)
            antigo = self.n.guild.get_channel(salvo["canal_id"])
            if antigo is not None:
                try:
                    await antigo.get_partial_message(salvo["msg_id"]).delete()
                except discord.HTTPException:
                    pass
        arq = banner("painel_squads.png")
        msg = await ch.send(embed=emb, view=view, **({"file": arq} if arq else {}))
        try:
            await msg.pin(reason="Painel de squads")
        except discord.HTTPException:
            pass
        self.n.db.salvar_painel("squad", ch.id, msg.id)
        log.info("Painel de squads publicado em #%s", ch.name)
        return f"Painel de squads publicado em #{ch.name}"

    async def garantir_aviso(self):
        """Mensagem fixa no topo de #squad-partida apontando para #abrir-squad."""
        partida, abrir = self.n.canal("squad_partida"), self.n.canal("abrir_squad")
        if partida is None or abrir is None:
            return
        emb = discord.Embed(
            title="📡 Squads em recrutamento",
            description=("Os squads abertos aparecem **logo abaixo**, do mais antigo para o mais novo.\n\n"
                         "> ✅ **Eu vou** ─ entra no squad e libera a call para você\n"
                         "> 🔊 **Ir para a call** ─ atalho para a call do squad\n"
                         "> 🚪 **Sair** ─ libera a sua vaga\n\n"
                         f"🎯 Quer montar o seu? Vá em {abrir.mention}."),
            color=textos.COR)
        emb.set_author(name="GHOST RECON® | OPERAÇÃO BRASIL")
        emb.set_footer(text="Cards somem sozinhos quando o squad acaba")
        v = discord.ui.View()
        v.add_item(discord.ui.Button(label="Abrir meu squad", emoji="🎯",
                                     url=f"https://discord.com/channels/{self.n.guild.id}/{abrir.id}"))
        salvo = self.n.db.painel("squad_aviso")
        if salvo and salvo["canal_id"] == partida.id:
            try:
                await partida.get_partial_message(salvo["msg_id"]).edit(embed=emb, view=v)
                return
            except discord.NotFound:
                pass
        msg = await partida.send(embed=emb, view=v)
        try:
            await msg.pin(reason="Aviso de squads")
        except discord.HTTPException:
            pass
        self.n.db.salvar_painel("squad_aviso", partida.id, msg.id)

    async def categoria(self) -> discord.CategoryChannel:
        g = self.n.guild
        alvo = regras.slug(self.n.cfg.nome_categoria_squads)
        for c in g.categories:
            if regras.slug(c.name) == alvo:
                return c
        overwrites = {g.default_role: discord.PermissionOverwrite(**PERM_VOZ_PUBLICO),
                      g.self_role: discord.PermissionOverwrite(**PERM_VOZ_BOT)}
        posicao = None
        ch = self.n.canal("squad_partida")
        if ch is not None and ch.category is not None:
            posicao = ch.category.position + 1
        kw = {"position": posicao} if posicao is not None else {}
        cat = await g.create_category(self.n.cfg.nome_categoria_squads, overwrites=overwrites,
                                      reason="Operação Brasil: calls dos squads", **kw)
        log.info("Categoria de squads criada: %s", cat.name)
        return cat

    # -- regras --------------------------------------------------------------
    def pode_criar(self, user: discord.abc.User) -> str | None:
        g = self.n.guild
        falta = faltando_permissoes(g) if g else []
        if falta:
            return "⚠️ O bot ainda não tem permissão para criar calls. Avise a equipe."
        s = self.n.db.squad_do_usuario(user.id)
        if s:
            return (f"Você já está no squad **{s['nome']}**. Saia dele (botão **🚪 Sair** no card) "
                    "antes de abrir outro.")
        if len(self.n.db.squads_ativos()) >= self.n.cfg.squad_max:
            return "Todas as calls de squad estão ocupadas agora. Tente de novo em alguns minutos."
        espera = COOLDOWN_CRIAR - (time.time() - self.ultimo_criado.get(user.id, 0))
        if espera > 0:
            return f"Aguarde **{int(espera) + 1}s** para abrir outro squad."
        return None

    # -- criar ---------------------------------------------------------------
    async def criar(self, interaction: discord.Interaction, esc: dict, nome: str, id_jogo: str, obs: str,
                    assistente: AssistenteSquad | None = None):
        n, g, autor = self.n, self.n.guild, interaction.user
        erro = self.pode_criar(autor)
        if erro:
            await interaction.followup.send(erro, ephemeral=True)
            return
        nome_ok = limpar_nome(nome)
        if not nome_ok:
            await interaction.followup.send("Nome inválido: use de 3 a 24 caracteres, sem links ou menções.",
                                            ephemeral=True)
            return
        ch = n.canal("squad_partida")
        if ch is None:
            await interaction.followup.send("Canal de squads não encontrado. Avise a equipe.", ephemeral=True)
            return
        jogo = C.JOGOS_SQUAD[esc["jogo"]]
        self.ultimo_criado[autor.id] = time.time()
        sid = n.db.criar_squad(autor.id, esc["jogo"], esc["plataforma"], esc["modo"], esc.get("estilo"), nome_ok,
                               limpar_texto(obs, 200), limpar_texto(id_jogo, 32), jogo["vagas"])
        try:
            cat = await self.categoria()
            overwrites = {
                g.default_role: discord.PermissionOverwrite(**PERM_VOZ_PUBLICO),
                g.self_role: discord.PermissionOverwrite(**PERM_VOZ_BOT),
                autor: discord.PermissionOverwrite(**PERM_VOZ_INTEGRANTE),
            }
            for r in n.cargos_equipe():
                overwrites[r] = discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)
            voz = await g.create_voice_channel(f"{jogo['emoji']} {nome_ok}", category=cat, overwrites=overwrites,
                                               user_limit=jogo["vagas"],
                                               reason=f"Squad #{sid:04d} aberto por {autor}")
            n.db.atualizar_squad(sid, voz_id=voz.id)
            s = n.db.squad(sid)
            arq = banner(f"squad_{s['jogo']}.png")
            msg = await ch.send(embed=embed_squad(s, g), view=view_squad(s, g.id),
                                allowed_mentions=discord.AllowedMentions.none(), **({"file": arq} if arq else {}))
            n.db.atualizar_squad(sid, msg_id=msg.id)
        except discord.HTTPException as e:
            log.exception("Falha ao criar o squad %s: %s", sid, e)
            await self.encerrar(sid, "falha ao criar")
            await interaction.followup.send("Não consegui criar a call agora. Tente novamente em instantes.",
                                            ephemeral=True)
            return
        self.vazio_desde[sid] = time.time()
        log.info("Squad #%04d '%s' aberto por %s (%s)", sid, nome_ok, autor, jogo["curto"])

        await self._boas_vindas(voz, n.db.squad(sid))
        movido = await self._mover(autor, voz)
        v = discord.ui.View()
        v.add_item(discord.ui.Button(label="Entrar na call", emoji="🔊", url=link_canal(g.id, voz.id)))
        v.add_item(discord.ui.Button(label="Ver card", emoji="🃏",
                                     url=f"https://discord.com/channels/{g.id}/{ch.id}/{msg.id}"))
        texto = (f"✅ Squad **{nome_ok}** aberto! A call {voz.mention} é exclusiva do seu esquadrão.\n"
                 + ("Você já foi movido para a call. 🎧" if movido else
                    "Clique em **Entrar na call** para entrar."))
        if assistente is not None:
            await assistente.concluir(texto, v)
            await interaction.followup.send("Pronto! 🎯", ephemeral=True)
        else:
            await interaction.followup.send(texto, view=v, ephemeral=True)

    async def _boas_vindas(self, voz: discord.VoiceChannel, s: dict):
        jogo = C.JOGOS_SQUAD[s["jogo"]]
        emb = discord.Embed(
            title=f"🎖️ Bem-vindos, {s['nome']}!",
            description=(f"> {jogo['emoji']} **{jogo['curto']}** ‧ {C.item(C.PLATAFORMAS_SQUAD, s['plataforma'])}\n"
                         f"> {C.item(C.MODOS[s['jogo']], s['modo'])}"),
            color=jogo["cor"])
        emb.set_author(name=f"SQUAD #{s['id']:04d}  •  CALL EXCLUSIVA")
        emb.add_field(name="👑 Líder", value=f"<@{s['lider_id']}>", inline=True)
        emb.add_field(name="👥 Vagas", value=f"**{s['vagas']}** jogadores", inline=True)
        emb.add_field(name="⏱️ Auto-limpeza", value=f"**{self.n.cfg.squad_vazio_min} min** vazia", inline=True)
        emb.add_field(name="📋 Dicas", inline=False, value=(
            "• Só quem clicou em **✅ Eu vou** (e a equipe) entra nesta call.\n"
            "• Use este chat para trocar IDs e combinar a missão.\n"
            "• O líder encerra pelo botão **🔒 Encerrar** no card."))
        _usar_banner(emb, f"squad_{s['jogo']}.png")
        arq = banner(f"squad_{s['jogo']}.png")
        try:
            await voz.send(embed=emb, allowed_mentions=discord.AllowedMentions.none(),
                           **({"file": arq} if arq else {}))
        except discord.HTTPException:
            pass

    async def _mover(self, membro: discord.abc.User, voz: discord.VoiceChannel) -> bool:
        """Se a pessoa já estiver em alguma call do servidor, leva direto para a call do squad."""
        if not isinstance(membro, discord.Member) or membro.voice is None or membro.voice.channel is None:
            return False
        if membro.voice.channel.id == voz.id:
            return True
        try:
            await membro.move_to(voz, reason="Squad: entrar na call do esquadrão")
            return True
        except discord.HTTPException:
            return False

    # -- entrar / sair -------------------------------------------------------
    async def entrar(self, interaction: discord.Interaction, sid: int):
        n, g, user = self.n, self.n.guild, interaction.user
        async with self.lock(sid):
            s = n.db.squad(sid)
            if not s or s["status"] != "ativo":
                await interaction.followup.send("Este squad já foi encerrado.", ephemeral=True)
                return
            if user.id in integrantes(s):
                await interaction.followup.send("Você já está neste squad. 😉", ephemeral=True,
                                                view=self._view_call(s))
                return
            outro = n.db.squad_do_usuario(user.id)
            if outro:
                await interaction.followup.send(f"Você já está no squad **{outro['nome']}**. Saia dele primeiro.",
                                                ephemeral=True)
                return
            if len(integrantes(s)) >= s["vagas"]:
                await interaction.followup.send("Esquadrão completo. Fica para a próxima! 🎖️", ephemeral=True)
                return
            voz = g.get_channel(s["voz_id"]) if s.get("voz_id") else None
            if voz is None:
                await interaction.followup.send("A call deste squad não existe mais.", ephemeral=True)
                await self.encerrar(sid, "call apagada")
                return
            try:
                await voz.set_permissions(user, reason=f"Squad #{sid:04d}: entrou",
                                          **PERM_VOZ_INTEGRANTE)
            except discord.HTTPException as e:
                log.warning("Squad %s: não foi possível liberar a call para %s: %s", sid, user, e)
                await interaction.followup.send("Não consegui liberar a call para você agora. Tente de novo.",
                                                ephemeral=True)
                return
            s["membros"].append(user.id)
            n.db.atualizar_squad(sid, membros=s["membros"])
        await self.atualizar_card(sid)
        ocup = len(integrantes(s))
        try:
            await voz.send(f"✅ <@{user.id}> entrou no squad ({ocup}/{s['vagas']})."
                           + (" **Esquadrão completo!** 🎖️" if ocup >= s["vagas"] else ""),
                           allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException:
            pass
        movido = await self._mover(user, voz)
        await interaction.followup.send(
            f"🎖️ Você entrou no squad **{s['nome']}**! "
            + ("Já te levei para a call." if movido else "Clique abaixo para entrar na call."),
            view=self._view_call(s), ephemeral=True)

    def _view_call(self, s: dict) -> discord.ui.View:
        v = discord.ui.View()
        if s.get("voz_id"):
            v.add_item(discord.ui.Button(label="Entrar na call", emoji="🔊",
                                         url=link_canal(self.n.guild.id, s["voz_id"])))
        return v

    async def sair(self, interaction: discord.Interaction, sid: int):
        n, g, user = self.n, self.n.guild, interaction.user
        novo_lider = None
        async with self.lock(sid):
            s = n.db.squad(sid)
            if not s or s["status"] != "ativo":
                await interaction.followup.send("Este squad já foi encerrado.", ephemeral=True)
                return
            if user.id not in integrantes(s):
                await interaction.followup.send("Você não faz parte deste squad.", ephemeral=True)
                return
            voz = g.get_channel(s["voz_id"]) if s.get("voz_id") else None
            if user.id == s["lider_id"] and not s["membros"]:
                encerrar = True
            else:
                encerrar = False
                if user.id == s["lider_id"]:          # liderança passa para o próximo da lista
                    novo_lider = s["membros"].pop(0)
                    s["lider_id"] = novo_lider
                    n.db.atualizar_squad(sid, lider_id=novo_lider, membros=s["membros"], id_jogo="")
                else:
                    s["membros"].remove(user.id)
                    n.db.atualizar_squad(sid, membros=s["membros"])
                if voz is not None:
                    try:
                        await voz.set_permissions(user, overwrite=None, reason=f"Squad #{sid:04d}: saiu")
                    except discord.HTTPException:
                        pass
        if encerrar:
            await self.encerrar(sid, "o líder saiu")
            await interaction.followup.send("Squad encerrado e call apagada. Até a próxima! 👋", ephemeral=True)
            return
        if voz is not None and isinstance(user, discord.Member) and user.voice and user.voice.channel \
                and user.voice.channel.id == voz.id:
            try:
                await user.move_to(None, reason="Saiu do squad")
            except discord.HTTPException:
                pass
        await self.atualizar_card(sid)
        if voz is not None:
            aviso = f"🚪 <@{user.id}> saiu do squad ({len(integrantes(s))}/{s['vagas']})."
            if novo_lider:
                aviso += f" 👑 Novo líder: <@{novo_lider}>."
            try:
                await voz.send(aviso, allowed_mentions=discord.AllowedMentions.none())
            except discord.HTTPException:
                pass
        await interaction.followup.send(f"Você saiu do squad **{s['nome']}**.", ephemeral=True)

    async def encerrar_por_botao(self, interaction: discord.Interaction, sid: int):
        s = self.n.db.squad(sid)
        if not s or s["status"] != "ativo":
            await interaction.followup.send("Este squad já foi encerrado.", ephemeral=True)
            return
        if interaction.user.id != s["lider_id"] and not self.n.eh_equipe(interaction.user):
            await interaction.followup.send("Só o **líder** do squad ou a equipe podem encerrar.", ephemeral=True)
            return
        quem = "líder" if interaction.user.id == s["lider_id"] else "equipe"
        await self.encerrar(sid, f"encerrado pelo {quem} ({interaction.user})")
        await interaction.followup.send("Squad encerrado e call apagada. 🏁", ephemeral=True)

    # -- encerrar ------------------------------------------------------------
    async def encerrar(self, sid: int, motivo: str):
        if not self.n.db.encerrar_squad(sid, motivo):
            return
        s = self.n.db.squad(sid)
        self.vazio_desde.pop(sid, None)
        g = self.n.guild
        voz = g.get_channel(s["voz_id"]) if s.get("voz_id") else None
        if voz is not None:
            try:
                await voz.delete(reason=f"Squad #{sid:04d} encerrado: {motivo}")
            except discord.HTTPException as e:
                log.warning("Squad %s: não foi possível apagar a call: %s", sid, e)
        ch = self.n.canal("squad_partida")
        if ch is not None and s.get("msg_id"):
            try:
                await ch.get_partial_message(s["msg_id"]).delete()
            except discord.HTTPException:
                pass
        log.info("Squad #%04d '%s' encerrado: %s", sid, s["nome"], motivo)

    async def atualizar_card(self, sid: int):
        s = self.n.db.squad(sid)
        ch = self.n.canal("squad_partida")
        if not s or s["status"] != "ativo" or ch is None or not s.get("msg_id"):
            return
        try:
            await ch.get_partial_message(s["msg_id"]).edit(embed=embed_squad(s, self.n.guild),
                                                           view=view_squad(s, self.n.guild.id))
        except discord.NotFound:
            arq = banner(f"squad_{s['jogo']}.png")
            msg = await ch.send(embed=embed_squad(s, self.n.guild), view=view_squad(s, self.n.guild.id),
                                allowed_mentions=discord.AllowedMentions.none(), **({"file": arq} if arq else {}))
            self.n.db.atualizar_squad(sid, msg_id=msg.id)
        except discord.HTTPException as e:
            log.warning("Squad %s: falha ao atualizar o card: %s", sid, e)

    def _agendar_card(self, sid: int, atraso: float = 3.0):
        """Agrupa várias entradas/saídas da call numa única edição do card."""
        if sid in self._agendados and not self._agendados[sid].done():
            return

        async def _depois():
            await asyncio.sleep(atraso)
            await self.atualizar_card(sid)
        self._agendados[sid] = asyncio.get_running_loop().create_task(_depois())

    # -- eventos e vigia -----------------------------------------------------
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, antes: discord.VoiceState,
                                    depois: discord.VoiceState):
        ids = {c.id for c in (antes.channel, depois.channel) if c is not None}
        if not ids or (antes.channel and depois.channel and antes.channel.id == depois.channel.id):
            return
        for s in self.n.db.squads_ativos():
            if s.get("voz_id") in ids:
                voz = self.n.guild.get_channel(s["voz_id"])
                if voz is not None and len(voz.voice_states) == 0:
                    self.vazio_desde[s["id"]] = time.time()
                else:
                    self.vazio_desde.pop(s["id"], None)
                self._agendar_card(s["id"])

    @tasks.loop(minutes=1)
    async def vigia(self):
        g = self.n.guild
        if g is None:
            return
        limite = self.n.cfg.squad_vazio_min * 60
        agora = time.time()
        for s in self.n.db.squads_ativos():
            voz = g.get_channel(s["voz_id"]) if s.get("voz_id") else None
            if voz is None:
                await self.encerrar(s["id"], "call apagada")
                continue
            if len(voz.voice_states) > 0:
                self.vazio_desde.pop(s["id"], None)
                continue
            desde = self.vazio_desde.setdefault(s["id"], agora)
            if agora - desde >= limite:
                await self.encerrar(s["id"], f"call vazia por {self.n.cfg.squad_vazio_min} min")

    @vigia.before_loop
    async def _antes(self):
        await self.bot.wait_until_ready()

    # -- comandos da equipe --------------------------------------------------
    @grupo.command(name="painel", description="Publica ou atualiza o painel de squads")
    async def cmd_painel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.garantir_canal()
        r = await self.garantir_painel()
        await self.garantir_aviso()
        await interaction.followup.send(r, ephemeral=True)

    @grupo.command(name="lista", description="Mostra os squads ativos")
    async def cmd_lista(self, interaction: discord.Interaction):
        ativos = self.n.db.squads_ativos()
        if not ativos:
            await interaction.response.send_message("Nenhum squad ativo.", ephemeral=True)
            return
        linhas = [f"`#{s['id']:04d}` **{s['nome']}** · {C.JOGOS_SQUAD[s['jogo']]['emoji']} · "
                  f"{len(integrantes(s))}/{s['vagas']} · líder <@{s['lider_id']}> · <#{s['voz_id']}>"
                  for s in ativos]
        await interaction.response.send_message("\n".join(linhas)[:1900], ephemeral=True)

    @grupo.command(name="remover-salas", description="Apaga as salas fixas de Breakpoint e Wildlands (com confirmação)")
    async def cmd_remover_salas(self, interaction: discord.Interaction):
        g = self.n.guild
        cats, calls, outros = salas_antigas(g)
        if not calls and not cats:
            await interaction.response.send_message("Não há salas fixas de Breakpoint/Wildlands para remover. ✅",
                                                    ephemeral=True)
            return
        ocupadas = [c for c in calls if len(c.voice_states) > 0]
        emb = discord.Embed(
            title="🗑️ Remover salas fixas",
            description=(f"Serão apagadas **{len(calls)} calls** em **{len(cats)} categoria(s)**:\n"
                         + "\n".join(f"• {c.name} ({sum(1 for x in calls if x.category_id == c.id)} calls)"
                                      for c in cats)
                         + "\n\nCalls com gente dentro são **puladas**. As categorias só são apagadas se "
                           "ficarem vazias.\n**Não dá para desfazer.**"),
            color=textos.COR_ERRO)
        if ocupadas:
            emb.add_field(name="🔊 Com gente agora (serão puladas)", value=", ".join(c.name for c in ocupadas)[:1000])
        if outros:
            emb.add_field(name="🛡️ Preservados (não são salas fixas)",
                          value=", ".join(c.name for c in outros)[:1000])
        v = ConfirmarRemocao(interaction.user.id)
        await interaction.response.send_message(embed=emb, view=v, ephemeral=True)
        await v.wait()
        if not v.confirmado:
            return
        calls_ok, cats_ok, puladas = await remover_salas(self.n, interaction.user)
        await interaction.edit_original_response(
            content=(f"✅ {calls_ok} calls e {cats_ok} categoria(s) apagadas."
                     + (f"\n⚠️ Puladas: {', '.join(puladas)}" if puladas else "")))

    @grupo.command(name="encerrar", description="Encerra um squad e apaga a call")
    @app_commands.describe(numero="Número do squad (veja em /squads lista)")
    async def cmd_encerrar(self, interaction: discord.Interaction, numero: int):
        await interaction.response.defer(ephemeral=True)
        s = self.n.db.squad(numero)
        if not s or s["status"] != "ativo":
            await interaction.followup.send("Squad não encontrado ou já encerrado.", ephemeral=True)
            return
        await self.encerrar(numero, f"encerrado pela equipe ({interaction.user})")
        await interaction.followup.send(f"Squad #{numero:04d} encerrado.", ephemeral=True)


# ---------------------------------------------------------------------------
# Remoção das antigas salas fixas (substituídas pelos squads)
# ---------------------------------------------------------------------------
CATEGORIAS_SALAS = ("╭─── 💀 Breakpoint | Salas", "╭─── 🌿 Wildlands | Salas")
PADRAO_SALA = re.compile(r"(breakpoint|wildlands)\s+(pc|xbox|ps)\s*\d+$", re.I)


def salas_antigas(g: discord.Guild) -> tuple[list[discord.CategoryChannel], list[discord.VoiceChannel], list]:
    """Categorias '... | Salas' e as calls 'Breakpoint PC 1' etc. dentro delas. Outros canais são preservados."""
    alvos = {regras.slug(n) for n in CATEGORIAS_SALAS}
    cats = [c for c in g.categories if regras.slug(c.name) in alvos]
    calls, outros = [], []
    for c in cats:
        for ch in c.channels:
            nome = re.sub(r"[^\w\s]", "", ch.name).strip()
            if isinstance(ch, discord.VoiceChannel) and PADRAO_SALA.search(nome):
                calls.append(ch)
            else:
                outros.append(ch)
    return cats, calls, outros


class ConfirmarRemocao(discord.ui.View):
    def __init__(self, autor_id: int):
        super().__init__(timeout=120)
        self.autor_id = autor_id
        self.confirmado: bool | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.autor_id

    @discord.ui.button(label="Apagar as salas", emoji="🗑️", style=discord.ButtonStyle.danger)
    async def sim(self, interaction: discord.Interaction, _b):
        self.confirmado = True
        await interaction.response.edit_message(content="⏳ Apagando...", embed=None, view=None)
        self.stop()

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def nao(self, interaction: discord.Interaction, _b):
        self.confirmado = False
        await interaction.response.edit_message(content="Nada foi apagado.", embed=None, view=None)
        self.stop()


async def remover_salas(n: Nucleo, ator: discord.abc.User) -> tuple[int, int, list[str]]:
    """Apaga as calls fixas vazias e as categorias que ficarem vazias. Retorna (calls, categorias, puladas)."""
    g = n.guild
    cats, calls, _ = salas_antigas(g)
    apagadas, puladas = 0, []
    for ch in calls:
        if len(ch.voice_states) > 0:
            puladas.append(f"{ch.name} (tem gente na call)")
            continue
        try:
            await ch.delete(reason=f"Salas fixas substituídas pelos squads (por {ator})")
            apagadas += 1
        except discord.HTTPException as e:
            puladas.append(f"{ch.name} ({e.status})")
    cats_apagadas = 0
    for c in cats:
        restantes = [ch for ch in g.channels if getattr(ch, "category_id", None) == c.id]
        if not restantes:
            try:
                await c.delete(reason=f"Categoria de salas fixas removida (por {ator})")
                cats_apagadas += 1
            except discord.HTTPException as e:
                puladas.append(f"categoria {c.name} ({e.status})")
    log.info("Salas fixas removidas por %s: %d calls, %d categorias. Puladas: %s", ator, apagadas, cats_apagadas,
             puladas)
    await n.registrar(None, ator, "Salas de voz fixas removidas",
                      f"{apagadas} calls e {cats_apagadas} categorias apagadas."
                      + (f"\nPuladas: {', '.join(puladas)}" if puladas else ""))
    return apagadas, cats_apagadas, puladas


async def setup(bot: commands.Bot, n: Nucleo) -> Squads:
    global NUCLEO
    NUCLEO = n
    bot.add_view(PainelSquadView())
    bot.add_dynamic_items(BotaoSquad)
    c = Squads(bot, n)
    await bot.add_cog(c, guild=discord.Object(n.cfg.guild_id))
    return c
