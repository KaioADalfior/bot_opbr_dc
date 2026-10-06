"""Tickets privados: denúncias e envio/aprovação de mods."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

from .. import catalogo as C
from .. import regras, textos, transcript
from ..nucleo import PERM_PARTICIPANTE, Nucleo, overwrite_seguro

log = logging.getLogger("operacao_brasil")

ROTULO_ACAO = {
    "assumir": ("🙋 Assumir", discord.ButtonStyle.secondary),
    "aprovar": ("✅ Aprovar", discord.ButtonStyle.success),
    "alteracoes": ("✏️ Pedir alterações", discord.ButtonStyle.primary),
    "rejeitar": ("❌ Rejeitar", discord.ButtonStyle.danger),
    "encerrar": ("🔒 Encerrar", discord.ButtonStyle.secondary),
    "reabrir": ("🔓 Reabrir", discord.ButtonStyle.secondary),
    "vip_dar": ("💎 Conceder VIP", discord.ButtonStyle.success),
    "vip_remover": ("➖ Remover VIP", discord.ButtonStyle.secondary),
}
ACOES_POR_TIPO = {
    "denuncia": ["assumir", "encerrar", "reabrir"],
    "mod": ["assumir", "aprovar", "alteracoes", "rejeitar", "encerrar", "reabrir"],
    "contribuicao": ["assumir", "vip_dar", "vip_remover", "encerrar", "reabrir"],
}
NOME_ACAO = {"assumir": "Ticket assumido", "aprovar": "Mod aprovado", "alteracoes": "Alterações solicitadas",
             "rejeitar": "Mod rejeitado", "encerrar": "Ticket encerrado", "reabrir": "Ticket reaberto",
             "vip_dar": "VIP concedido", "vip_remover": "VIP removido"}

# Formas de contribuir (menu do painel de contribuição)
FORMAS = {
    "financeiro": {"nome": "Apoio financeiro", "emoji": "💸", "descricao": "Ajudar com custos do servidor e eventos"},
    "conteudo": {"nome": "Conteúdo, lives e clipes", "emoji": "🎬", "descricao": "Vídeos, transmissões, guias"},
    "arte": {"nome": "Arte e design", "emoji": "🎨", "descricao": "Banners, emojis, artes da comunidade"},
    "organizacao": {"nome": "Organizar eventos e raids", "emoji": "🧭", "descricao": "Ajudar a equipe com operações"},
    "parceria": {"nome": "Parceria", "emoji": "🤝", "descricao": "Clã, canal, servidor ou projeto parceiro"},
    "outro": {"nome": "Outra ideia", "emoji": "✨", "descricao": "Conte para a equipe"},
}

NUCLEO: Nucleo | None = None  # definido em setup()


def nucleo() -> Nucleo:
    assert NUCLEO is not None
    return NUCLEO


# ---------------------------------------------------------------------------
# Botões dos tickets (persistentes, sobrevivem a reinícios)
# ---------------------------------------------------------------------------
class BotaoTicket(discord.ui.DynamicItem[discord.ui.Button], template=r"grb:t:(?P<acao>[a-z_]+):(?P<tid>\d+)"):
    def __init__(self, acao: str, tid: int, desativado: bool = False):
        rotulo, estilo = ROTULO_ACAO[acao]
        super().__init__(discord.ui.Button(label=rotulo, style=estilo, custom_id=f"grb:t:{acao}:{tid}",
                                           disabled=desativado))
        self.acao = acao
        self.tid = tid

    @classmethod
    async def from_custom_id(cls, interaction, item, match: re.Match[str], /):
        return cls(match["acao"], int(match["tid"]))

    async def callback(self, interaction: discord.Interaction):
        if self.acao in ("rejeitar", "alteracoes"):
            # Valida antes de abrir o formulário de motivo
            erro = _pre_validar(interaction, self.tid, self.acao)
            if erro:
                await interaction.response.send_message(erro, ephemeral=True)
                return
            await interaction.response.send_modal(ModalMotivo(self.acao, self.tid))
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        await executar_acao(interaction, self.tid, self.acao)


def montar_view(ticket: dict) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    for acao in ACOES_POR_TIPO[ticket["tipo"]]:
        origens, _, _ = regras.TRANSICOES[acao]
        view.add_item(BotaoTicket(acao, ticket["id"], desativado=ticket["status"] not in origens))
    link = ticket["dados"].get("link")
    if ticket["tipo"] == "mod" and link and regras.analisar_link(link).valido:
        view.add_item(discord.ui.Button(label="Abrir página informada", emoji="🔗", url=link, row=2))
    return view


def _cabecalho_mod(d: dict) -> list[tuple[str, str, bool]]:
    campos = [("🎮 Jogo", C.rotulo_jogo(d.get("jogo_chave")) if d.get("jogo_chave") else d.get("jogo", "—"), True),
              ("💻 Plataformas", C.rotulo_plataformas(d.get("plataformas")), True),
              ("🏷️ Categoria", C.rotulo_categoria(d.get("categoria")), True)]
    if d.get("versao"):
        campos.append(("🔢 Versão / compatibilidade", d["versao"][:1024], True))
    campos.append(("✍️ Autor / créditos", d.get("creditos", "—")[:1024], True))
    return campos


def embed_ticket(ticket: dict) -> discord.Embed:
    d = ticket["dados"]
    if ticket["tipo"] == "contribuicao":
        f = FORMAS.get(d.get("forma"), FORMAS["outro"])
        emb = discord.Embed(title=f"💎 Contribuição #{ticket['id']:04d} — {f['emoji']} {f['nome']}"[:256],
                            description=d.get("mensagem", "")[:4000], color=0xA855F7)
        emb.set_author(name="Quero contribuir com a Operação Brasil")
        if d.get("contato"):
            emb.add_field(name="🕐 Disponibilidade / observações", value=d["contato"][:1024], inline=False)
        if d.get("vip_por"):
            emb.add_field(name="💎 VIP", value=f"Concedido por <@{d['vip_por']}>", inline=True)
    elif ticket["tipo"] == "denuncia":
        emb = discord.Embed(title=f"🚨 Atendimento #{ticket['id']:04d} — {d.get('assunto', '')}"[:256],
                            description=d.get("relato", "")[:4000], color=textos.COR_ALERTA)
        if d.get("envolvidos"):
            emb.add_field(name="Envolvidos", value=d["envolvidos"][:1024], inline=False)
        if d.get("provas"):
            emb.add_field(name="Provas / links", value=d["provas"][:1024], inline=False)
    else:
        emb = discord.Embed(title=f"📦 {d.get('nome', 'Mod')}"[:256],
                            description=(d.get("descricao", "") or "")[:4000],
                            color=C.cor_jogo(d.get("jogo_chave"), textos.COR))
        emb.set_author(name=f"Envio de mod #{ticket['id']:04d} • em análise pela equipe")
        for nome, valor, inline in _cabecalho_mod(d):
            emb.add_field(name=nome, value=valor or "—", inline=inline)
        emb.add_field(name="🔗 Link informado (não verificado)", value=d.get("link", "—")[:1024], inline=False)
        if d.get("alertas"):
            emb.add_field(name="⚠️ Pontos de atenção para a equipe",
                          value="\n".join(f"• {a}" for a in d["alertas"])[:1024], inline=False)
    emb.add_field(name="👤 Enviado por", value=f"<@{ticket['autor_id']}>", inline=True)
    emb.add_field(name="📌 Status", value=regras.ROTULOS.get(ticket["status"], ticket["status"]), inline=True)
    if ticket.get("assumido_por"):
        emb.add_field(name="🙋 Responsável", value=f"<@{ticket['assumido_por']}>", inline=True)
    emb.timestamp = datetime.fromisoformat(ticket["criado_em"]) if ticket.get("criado_em") else None
    if not emb.author:
        emb.set_author(name={"denuncia": "ATENDIMENTO PRIVADO", "mod": "ENVIO DE MOD",
                             "contribuicao": "CONTRIBUIÇÃO"}.get(ticket["tipo"], "TICKET"))
    emb.set_footer(text="Somente a equipe usa os botões • Quem enviou não pode avaliar o próprio envio")
    return emb
async def atualizar_controle(canal: discord.TextChannel, ticket: dict):
    mid = ticket["dados"].get("controle_msg")
    if not mid:
        return
    try:
        msg = await canal.fetch_message(mid)
        await msg.edit(embed=embed_ticket(ticket), view=montar_view(ticket))
    except discord.HTTPException as e:
        log.warning("Não foi possível atualizar o painel do ticket %s: %s", ticket["id"], e)


def _pre_validar(interaction: discord.Interaction, tid: int, acao: str) -> str | None:
    n = nucleo()
    t = n.db.ticket(tid)
    if t is None:
        return "Ticket não encontrado."
    try:
        regras.verificar_acao(acao, t["tipo"], t["status"], t["autor_id"], interaction.user.id,
                              n.eh_equipe(interaction.user))
    except regras.AcaoNegada as e:
        return str(e)
    return None


class ModalMotivo(discord.ui.Modal):
    motivo = discord.ui.TextInput(label="Motivo / o que precisa mudar", style=discord.TextStyle.paragraph,
                                  min_length=5, max_length=1000)

    def __init__(self, acao: str, tid: int):
        super().__init__(title=("Rejeitar mod" if acao == "rejeitar" else "Pedir alterações")[:45])
        self.acao = acao
        self.tid = tid

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        await executar_acao(interaction, self.tid, self.acao, str(self.motivo.value))


async def _travar_autor(canal: discord.TextChannel, autor_id: int, travar: bool):
    m = await nucleo().membro(autor_id)
    if m is None:
        return
    if travar:
        await canal.set_permissions(m, view_channel=True, read_message_history=True, send_messages=False,
                                    reason="Ticket finalizado")
    else:
        await canal.set_permissions(m, reason="Ticket reaberto", **PERM_PARTICIPANTE)


async def _avisar_autor(autor_id: int, texto: str):
    m = await nucleo().membro(autor_id)
    if m is None:
        return
    try:
        await m.send(texto)
    except discord.HTTPException:
        pass  # DMs fechadas: o aviso já está no canal do ticket


async def _publicar_mod(ticket: dict, aprovador: discord.abc.User) -> discord.Message:
    n = nucleo()
    ch = n.canal("mods_publicados")
    if ch is None:
        raise RuntimeError("Canal de mods publicados não encontrado.")
    d = ticket["dados"]
    emb = discord.Embed(title=f"📦 {d.get('nome', 'Mod')}"[:256], url=d.get("link") or None,
                        description=(d.get("descricao", "") or "")[:4000],
                        color=C.cor_jogo(d.get("jogo_chave"), textos.COR_OK))
    emb.set_author(name=f"{C.rotulo_jogo(d.get('jogo_chave'))} • Mod aprovado pela equipe")
    for nome, valor, inline in _cabecalho_mod(d):
        if nome.startswith("🎮"):
            continue
        emb.add_field(name=nome, value=valor or "—", inline=inline)
    emb.add_field(name="🙌 Sugerido por", value=f"<@{ticket['autor_id']}>", inline=True)
    emb.add_field(name="✅ Aprovado por", value=aprovador.mention, inline=True)
    emb.set_footer(text=f"Mod #{ticket['id']:04d} • Use por sua conta e risco: faça backup e confira a "
                        "compatibilidade com sua versão.")
    view = discord.ui.View(timeout=None)
    if d.get("link") and regras.analisar_link(d["link"]).valido:
        view.add_item(discord.ui.Button(label="Página oficial do mod", emoji="📥", url=d["link"]))
    return await ch.send(embed=emb, view=view, allowed_mentions=discord.AllowedMentions.none())


FINALIZADORAS = ("aprovar", "rejeitar", "encerrar")


def _cabecalho_transcript(t: dict, acao: str, ator, motivo: str, autor_nome: str) -> dict:
    d = t["dados"]
    agora = datetime.now(timezone.utc)
    if t["tipo"] == "mod":
        titulo = f"Mod #{t['id']:04d} — {d.get('nome', '')}"
        sub = f"Envio de mod · {C.rotulo_jogo(d.get('jogo_chave'))}"
    elif t["tipo"] == "contribuicao":
        f = FORMAS.get(d.get("forma"), FORMAS["outro"])
        titulo = f"Contribuição #{t['id']:04d} — {f['nome']}"
        sub = "Conversa privada sobre contribuição"
    else:
        titulo = f"Atendimento #{t['id']:04d} — {d.get('assunto', '')}"
        sub = "Atendimento privado com a equipe"
    chips = [("Autor", autor_nome), ("Aberto em", _data_br(t.get("criado_em"))),
             ("Encerrado em", agora.astimezone(BRT).strftime("%d/%m/%Y %H:%M")),
             ("Resultado", regras.ROTULOS.get(t["status"], t["status"])),
             ("Por", getattr(ator, "display_name", str(ator)))]
    if t["tipo"] == "mod":
        chips += [("Plataformas", C.rotulo_plataformas(d.get("plataformas"))),
                  ("Categoria", C.rotulo_categoria(d.get("categoria")))]
    if motivo:
        chips.append(("Motivo", motivo[:180]))
    return {"titulo": titulo[:200], "subtitulo": sub, "chips": chips}


BRT = timezone(timedelta(hours=-3))


def _data_br(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(iso).astimezone(BRT).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return iso


def view_transcript(url: str) -> discord.ui.View:
    v = discord.ui.View(timeout=None)
    v.add_item(discord.ui.Button(label="Visualizar transcript", emoji="🔓", url=url))
    return v


async def _finalizar(canal: discord.TextChannel, t: dict, acao: str, ator, motivo: str, automatico: bool) -> str:
    """Gera o transcript HTML protegido, entrega ao autor (DM) e à equipe e apaga o canal."""
    n = nucleo()
    autor = await n.membro(t["autor_id"])
    autor_nome = autor.display_name if autor else str(t["autor_id"])
    html, senha = await transcript.gerar(canal, t, _cabecalho_transcript(t, acao, ator, motivo, autor_nome))
    resultado = {"aprovar": "✅ aprovado e publicado", "rejeitar": "❌ não aprovado",
                 "encerrar": "🔒 encerrado"}[acao]
    tipo_txt = "mod" if t["tipo"] == "mod" else "atendimento"

    # Link público (se o servidor web/túnel estiver ativo)
    link = None
    if n.web is not None:
        token = n.web.salvar(html)
        link = n.web.link(token)
        t["dados"]["transcript_token"] = token
        n.db.atualizar_dados(t["id"], t["dados"])
    dias = n.cfg.transcript_dias

    def botao() -> discord.ui.View | None:
        return view_transcript(link) if link else None

    enviadas: list[list[int]] = []  # [canal, mensagem] com o botão, para atualizar se o endereço mudar

    # Equipe: link + senha (e o arquivo como cópia de segurança) no canal privado de relatórios
    rel = n.canal("relatorios")
    if rel is not None:
        emb = discord.Embed(title=f"📄 Transcript #{t['id']:04d}", color=textos.COR,
                            description=f"Ticket de **{tipo_txt}** {resultado}"
                                        + (" (inatividade)" if automatico else "") + f".\nAutor: <@{t['autor_id']}>")
        emb.add_field(name="🔑 Senha", value=f"||`{senha}`||", inline=True)
        if link:
            emb.add_field(name="⏳ Link válido por", value=f"{dias} dias", inline=True)
        if link:
            m = await rel.send(embed=emb, view=botao(), allowed_mentions=discord.AllowedMentions.none())
            enviadas.append([int(m.channel.id), int(m.id)])
        else:
            emb.set_footer(text="Sem link público no momento: abra o arquivo anexo no navegador.")
            await rel.send(embed=emb, file=transcript.arquivo(html, t["id"]),
                           allowed_mentions=discord.AllowedMentions.none())

    # Autor: mensagem privada com o link (ou o arquivo, se não houver link) + senha
    entregue = False
    if autor is not None:
        emb = discord.Embed(
            title=f"{ {'mod': '📦', 'contribuicao': '💎'}.get(t['tipo'], '🚨') } Seu {tipo_txt} #{t['id']:04d} foi {resultado.split(' ', 1)[1]}",
            color=textos.COR_OK if acao == "aprovar" else (textos.COR_ERRO if acao == "rejeitar" else textos.COR),
            description=(f"**Motivo:** {motivo}\n\n" if motivo else "")
            + ("O histórico completo da conversa está disponível numa página protegida.\n\n"
               "**Como abrir:** clique em **🔓 Visualizar transcript** e digite a senha abaixo."
               if link else
               "O histórico completo da conversa está no arquivo anexo, protegido por senha.\n\n"
               "**Como abrir:** baixe o arquivo, abra no navegador e digite a senha abaixo."))
        emb.add_field(name="🔑 Sua senha", value=f"`{senha}`", inline=True)
        if link:
            emb.add_field(name="⏳ Disponível por", value=f"{dias} dias", inline=True)
        emb.set_footer(text="Operação Brasil • Não compartilhe a senha. A equipe nunca pede sua senha do Discord.")
        try:
            if link:
                m = await autor.send(embed=emb, view=botao())
                enviadas.append([int(m.channel.id), int(m.id)])
            else:
                await autor.send(embed=emb, file=transcript.arquivo(html, t["id"]))
            entregue = True
        except discord.HTTPException:
            entregue = False

    if link:
        t["dados"]["transcript_url"] = link
        t["dados"]["transcript_msgs"] = enviadas
        n.db.atualizar_dados(t["id"], t["dados"])

    try:
        await canal.delete(reason=f"Ticket #{t['id']:04d} {acao} — transcript gerado")
        n.db.definir_canal(t["id"], None)
    except discord.HTTPException as e:
        log.warning("Não foi possível apagar o canal do ticket %s: %s", t["id"], e)
    return "" if entregue else " (não foi possível enviar a DM ao autor: DMs fechadas ou saiu do servidor)"


async def executar_acao(interaction: discord.Interaction | None, tid: int, acao: str, motivo: str = "",
                        automatico: bool = False):
    """Executa uma ação de equipe sobre o ticket, com validação, auditoria e avisos."""
    n = nucleo()
    t = n.db.ticket(tid)

    async def responder(txt: str):
        if interaction is None:
            return
        try:
            await interaction.followup.send(txt, ephemeral=True)
        except discord.HTTPException:
            pass

    if t is None:
        await responder("Ticket não encontrado.")
        return
    ator = interaction.user if interaction else n.bot.user
    try:
        destino = regras.verificar_acao(acao, t["tipo"], t["status"], t["autor_id"], ator.id,
                                        True if automatico else n.eh_equipe(ator))
    except regras.AcaoNegada as e:
        await responder(f"⛔ {e}")
        return
    origens = regras.TRANSICOES[acao][0]
    if destino and not n.db.mudar_status(tid, origens, destino):
        await responder("Este ticket acabou de ser atualizado por outra pessoa. Confira o status.")
        return
    canal = n.guild.get_channel(t["canal_id"]) if t.get("canal_id") else None

    try:
        if acao == "aprovar":
            try:
                msg = await _publicar_mod(t, ator)
            except Exception as e:  # noqa: BLE001
                n.db.mudar_status(tid, {regras.APROVADO}, t["status"])  # desfaz
                log.exception("Falha ao publicar mod %s", tid)
                await responder(f"Não foi possível publicar o mod: {e}. Nada foi alterado.")
                return
            n.db.definir_publicacao(tid, msg.id)
        if acao == "assumir":
            n.db.assumir(tid, ator.id)
        if acao in ("vip_dar", "vip_remover"):
            from . import vip as V
            alvo = await n.membro(t["autor_id"])
            if alvo is None:
                await responder("O membro não está mais no servidor.")
                return
            if acao == "vip_dar":
                erro = await V.dar_vip(n, alvo, "contribuicao", ator.id, tid)
                t["dados"]["vip_por"] = ator.id
            else:
                if V.eh_booster(alvo) and n.cfg.boost_vip:
                    await responder("⚠️ Este membro impulsiona o servidor: o VIP dele é automático enquanto o "
                                    "impulso durar. Nada foi alterado.")
                    return
                erro = await V.tirar_vip(n, alvo, f"VIP removido por {ator}")
                t["dados"].pop("vip_por", None)
            if erro:
                await responder(f"⛔ {erro}")
                return
            n.db.atualizar_dados(tid, t["dados"])
        if acao == "reabrir" and canal is None:
            autor = await n.membro(t["autor_id"])
            if autor is None:
                n.db.mudar_status(tid, {regras.ABERTO}, t["status"])
                await responder("O autor não está mais no servidor; não é possível reabrir.")
                return
            canal = await _criar_canal_ticket(autor, n.db.ticket(tid), t["tipo"],
                                              t["dados"].get("nome", "") if t["tipo"] == "mod" else "",
                                              f"🔓 {autor.mention}, seu atendimento foi reaberto pela equipe.")

        t = n.db.ticket(tid)
        extra = ""
        if canal is not None:
            textos_canal = {
                "assumir": f"🙋 {ator.mention} assumiu este atendimento.",
                "aprovar": f"✅ Mod **aprovado** por {ator.mention} e publicado no canal de mods publicados.",
                "alteracoes": f"✏️ <@{t['autor_id']}>, a equipe pediu alterações:\n>>> {motivo}",
                "rejeitar": f"❌ Mod **rejeitado** por {ator.mention}.\n>>> {motivo}",
                "encerrar": ("🔒 Atendimento encerrado automaticamente por inatividade." if automatico
                             else f"🔒 Atendimento encerrado por {ator.mention}."),
                "reabrir": f"🔓 Atendimento reaberto por {ator.mention}.",
                "vip_dar": f"💎 <@{t['autor_id']}> agora é **VIP**! Obrigado por apoiar a Operação Brasil. "
                           f"(concedido por {ator.mention})",
                "vip_remover": f"➖ VIP de <@{t['autor_id']}> removido por {ator.mention}.",
            }
            await canal.send(textos_canal[acao],
                             allowed_mentions=discord.AllowedMentions(users=[discord.Object(t["autor_id"])]))
            if acao in FINALIZADORAS:
                extra = await _finalizar(canal, t, acao, ator, motivo, automatico)
            else:
                if acao == "reabrir":
                    await _travar_autor(canal, t["autor_id"], False)
                await atualizar_controle(canal, t)

        avisos_dm = {
            "alteracoes": "✏️ A equipe pediu alterações no seu mod #{id:04d}. Responda no canal do atendimento.",
            "reabrir": "🔓 Seu atendimento #{id:04d} foi reaberto.",
            "vip_dar": "💎 Você agora é **VIP** na Operação Brasil! Obrigado pelo apoio.",
        }
        if acao in avisos_dm:
            await _avisar_autor(t["autor_id"], avisos_dm[acao].format(id=tid))

        cor = {"aprovar": textos.COR_OK, "rejeitar": textos.COR_ERRO, "vip_dar": 0xA855F7}.get(acao, textos.COR)
        await n.registrar(t, ator.id, NOME_ACAO[acao] + (" (automático)" if automatico else ""),
                          (motivo + extra).strip(), cor)
        fim = " Transcript enviado ao autor e em #relatórios; canal apagado." if acao in FINALIZADORAS else ""
        await responder(f"Feito: {NOME_ACAO[acao].lower()} (#{tid:04d}).{fim}{extra}")
    except discord.HTTPException as e:
        log.exception("Erro do Discord na ação %s do ticket %s", acao, tid)
        await responder(f"Ação registrada, mas houve um erro do Discord: {e}")


# ---------------------------------------------------------------------------
# Formulários de abertura
# ---------------------------------------------------------------------------
async def _criar_canal_ticket(autor: discord.Member, ticket: dict, prefixo: str, titulo: str,
                              saudacao: str | None = None) -> discord.TextChannel:
    n = nucleo()
    g = n.guild
    cat = await n.categoria_tickets()
    overwrites = {
        g.default_role: discord.PermissionOverwrite(view_channel=False),
        g.self_role: discord.PermissionOverwrite(**PERM_PARTICIPANTE),
        autor: discord.PermissionOverwrite(**PERM_PARTICIPANTE),
    }
    for r in n.cargos_equipe():
        overwrites[r] = discord.PermissionOverwrite(**PERM_PARTICIPANTE)
    nome = regras.nome_canal_ticket(prefixo, ticket["id"], titulo)
    canal = await g.create_text_channel(
        nome, category=cat, overwrites=overwrites,
        topic=f"Ticket #{ticket['id']:04d} ({ticket['tipo']}) — privado entre o autor e a equipe.",
        reason=f"Ticket #{ticket['id']:04d} aberto por {autor} ({autor.id})")
    n.db.definir_canal(ticket["id"], canal.id)
    ticket = n.db.ticket(ticket["id"])
    msg = await canal.send(content=saudacao or f"{autor.mention}, a equipe foi avisada e responderá aqui.",
                           embed=embed_ticket(ticket), view=montar_view(ticket),
                           allowed_mentions=discord.AllowedMentions(users=[autor]))
    ticket["dados"]["controle_msg"] = msg.id
    n.db.atualizar_dados(ticket["id"], ticket["dados"])
    return canal


class ModalDenuncia(discord.ui.Modal, title="Atendimento privado"):
    assunto = discord.ui.TextInput(label="Assunto", max_length=100,
                                   placeholder="Ex.: ofensas em chamada de voz")
    relato = discord.ui.TextInput(label="O que aconteceu?", style=discord.TextStyle.paragraph,
                                  max_length=1500, min_length=10)
    envolvidos = discord.ui.TextInput(label="Quem está envolvido? (nome ou ID)", required=False, max_length=200)
    provas = discord.ui.TextInput(label="Provas (links) — opcional", style=discord.TextStyle.paragraph,
                                  required=False, max_length=500,
                                  placeholder="Você também poderá enviar imagens dentro do canal privado.")

    async def on_submit(self, interaction: discord.Interaction):
        n = nucleo()
        if len(n.db.ativos_do_autor(interaction.user.id, "denuncia")) >= n.cfg.max_denuncias:
            await interaction.response.send_message(
                "Você já tem um atendimento aberto. Continue a conversa por lá.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        dados = {"assunto": str(self.assunto.value), "relato": str(self.relato.value),
                 "envolvidos": str(self.envolvidos.value or ""), "provas": str(self.provas.value or "")}
        tid = n.db.criar_ticket("denuncia", interaction.user.id, dados)
        ticket = n.db.ticket(tid)
        try:
            canal = await _criar_canal_ticket(interaction.user, ticket, "denuncia", "")
        except discord.HTTPException as e:
            n.db.mudar_status(tid, regras.ATIVOS, regras.ENCERRADO)
            log.exception("Falha ao criar canal da denúncia %s", tid)
            await interaction.followup.send(f"Não foi possível abrir o atendimento ({e}). Avise a equipe.",
                                            ephemeral=True)
            return
        await n.registrar(n.db.ticket(tid), interaction.user, "Atendimento aberto", dados["assunto"],
                          textos.COR_ALERTA)
        await interaction.followup.send(f"✅ Atendimento aberto em {canal.mention}. Só você e a equipe veem.",
                                        ephemeral=True)


def _embed_assistente(esc: dict) -> discord.Embed:
    pronto = bool(esc.get("jogo") and esc.get("plataformas"))
    emb = discord.Embed(
        title="📤 Assistente de envio de mod",
        description=("Escolha nos menus abaixo e depois clique em **Continuar** para preencher os detalhes.\n"
                     "Só você vê esta mensagem."),
        color=C.cor_jogo(esc.get("jogo"), textos.COR))
    emb.add_field(name="1️⃣ Jogo", value=C.rotulo_jogo(esc.get("jogo")) if esc.get("jogo") else "⬜ *não escolhido*",
                  inline=True)
    emb.add_field(name="2️⃣ Plataformas", value=C.rotulo_plataformas(esc.get("plataformas"))
                  if esc.get("plataformas") else "⬜ *não escolhido*", inline=True)
    emb.add_field(name="3️⃣ Categoria", value=C.rotulo_categoria(esc.get("categoria"))
                  if esc.get("categoria") else "⬜ *opcional*", inline=True)
    emb.set_footer(text="✅ Pronto para continuar" if pronto else "Escolha o jogo e ao menos uma plataforma")
    return emb


class AssistenteMod(discord.ui.View):
    """Passo 1 do envio: menus de seleção (jogo, plataformas, categoria). Só o autor vê (efêmero)."""

    def __init__(self, autor_id: int):
        super().__init__(timeout=600)
        self.autor_id = autor_id
        self.esc: dict = {"jogo": None, "plataformas": [], "categoria": None}
        self.origem: discord.Interaction | None = None
        self.sel_jogo = discord.ui.Select(
            placeholder="🎮 Escolha o jogo do mod", min_values=1, max_values=1, row=0,
            options=[discord.SelectOption(label=j["nome"], value=k, emoji=j["emoji"], description=j["descricao"])
                     for k, j in C.JOGOS.items()])
        self.sel_plat = discord.ui.Select(
            placeholder="💻 Plataformas compatíveis (pode marcar várias)", min_values=1,
            max_values=len(C.PLATAFORMAS), row=1,
            options=[discord.SelectOption(label=p["nome"], value=k, emoji=p["emoji"], description=p["descricao"])
                     for k, p in C.PLATAFORMAS.items()])
        self.sel_cat = discord.ui.Select(
            placeholder="🏷️ Categoria do mod (opcional)", min_values=1, max_values=1, row=2,
            options=[discord.SelectOption(label=c["nome"], value=k, emoji=c["emoji"], description=c["descricao"])
                     for k, c in C.CATEGORIAS.items()])
        self.btn_continuar = discord.ui.Button(label="Continuar", emoji="➡️", style=discord.ButtonStyle.success,
                                               row=3, disabled=True)
        self.btn_cancelar = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.secondary, row=3)
        for item, cb in ((self.sel_jogo, self._jogo), (self.sel_plat, self._plat), (self.sel_cat, self._cat),
                         (self.btn_continuar, self._continuar), (self.btn_cancelar, self._cancelar)):
            item.callback = cb
            self.add_item(item)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.autor_id

    def _marcar(self):
        for sel, valores in ((self.sel_jogo, [self.esc["jogo"]]), (self.sel_plat, self.esc["plataformas"]),
                             (self.sel_cat, [self.esc["categoria"]])):
            for opt in sel.options:
                opt.default = opt.value in valores
        self.btn_continuar.disabled = not (self.esc["jogo"] and self.esc["plataformas"])

    async def _atualizar(self, interaction: discord.Interaction):
        self._marcar()
        await interaction.response.edit_message(embed=_embed_assistente(self.esc), view=self)

    async def _jogo(self, interaction: discord.Interaction):
        self.esc["jogo"] = self.sel_jogo.values[0]
        await self._atualizar(interaction)

    async def _plat(self, interaction: discord.Interaction):
        self.esc["plataformas"] = [k for k in C.PLATAFORMAS if k in self.sel_plat.values]
        await self._atualizar(interaction)

    async def _cat(self, interaction: discord.Interaction):
        self.esc["categoria"] = self.sel_cat.values[0]
        await self._atualizar(interaction)

    async def _continuar(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ModalMod(dict(self.esc), self))

    async def _cancelar(self, interaction: discord.Interaction):
        self.stop()
        await interaction.response.edit_message(content="Envio cancelado.", embed=None, view=None)

    async def concluir(self, texto: str):
        self.stop()
        if self.origem is not None:
            try:
                await self.origem.edit_original_response(content=texto, embed=None, view=None)
            except discord.HTTPException:
                pass


class ModalMod(discord.ui.Modal):
    """Passo 2 do envio: detalhes do mod."""
    nome = discord.ui.TextInput(label="Nome do mod", max_length=80, placeholder="Ex.: Tactical Realism Overhaul")
    versao = discord.ui.TextInput(label="Versão do mod / do jogo (opcional)", max_length=60, required=False,
                                  placeholder="Ex.: v2.1 — compatível com o patch atual")
    link = discord.ui.TextInput(label="Link oficial do mod (https://...)", max_length=300,
                                placeholder="Página do autor (ex.: Nexus Mods). Sem encurtadores.")
    creditos = discord.ui.TextInput(label="Autor / créditos", max_length=150, placeholder="Quem criou o mod")
    descricao = discord.ui.TextInput(label="Descrição, instalação e remoção", style=discord.TextStyle.paragraph,
                                     max_length=1500, min_length=20,
                                     placeholder="O que o mod faz, como instalar e como desinstalar.")

    def __init__(self, escolhas: dict, assistente: AssistenteMod | None = None):
        jogo = C.JOGOS.get(escolhas.get("jogo") or "", {})
        super().__init__(title=f"Enviar mod • {jogo.get('curto', 'Ghost Recon')}"[:45])
        self.escolhas = escolhas
        self.assistente = assistente

    async def on_submit(self, interaction: discord.Interaction):
        n = nucleo()
        esc = self.escolhas
        if esc.get("jogo") not in C.JOGOS or not esc.get("plataformas"):
            await interaction.response.send_message("Escolha o jogo e a plataforma antes de continuar.",
                                                    ephemeral=True)
            return
        analise = regras.analisar_link(str(self.link.value))
        if not analise.valido:
            await interaction.response.send_message(f"⛔ Link recusado: {analise.erro}", ephemeral=True)
            return
        if analise.bloqueado:
            await interaction.response.send_message(
                "⛔ Link recusado: " + " ".join(analise.alertas) + " Envie o link da página oficial do mod.",
                ephemeral=True)
            return
        if len(n.db.ativos_do_autor(interaction.user.id, "mod")) >= n.cfg.max_mods:
            await interaction.response.send_message(
                f"Você já tem {n.cfg.max_mods} envio(s) em análise. Aguarde a avaliação.", ephemeral=True)
            return
        nome_norm = f"{esc['jogo']}:{regras.normalizar_nome(str(self.nome.value))}"
        dup = n.db.duplicado_mod(analise.normalizado, nome_norm)
        if dup:
            await interaction.response.send_message(
                f"Este mod já foi enviado (#{dup['id']:04d}, {regras.ROTULOS[dup['status']]}). "
                "Se for uma versão nova, fale com a equipe.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        dados = {"nome": str(self.nome.value).strip(), "jogo_chave": esc["jogo"],
                 "jogo": C.JOGOS[esc["jogo"]]["nome"], "plataformas": esc["plataformas"],
                 "categoria": esc.get("categoria"), "versao": str(self.versao.value or "").strip(),
                 "link": str(self.link.value).strip(), "creditos": str(self.creditos.value).strip(),
                 "descricao": str(self.descricao.value).strip(), "alertas": list(analise.alertas)}
        for url in regras.extrair_links(dados["descricao"]):
            a = regras.analisar_link(url)
            if a.bloqueado or not a.valido:
                dados["alertas"].append(f"Link suspeito na descrição: {url[:80]}")
        tid = n.db.criar_ticket("mod", interaction.user.id, dados, analise.normalizado, nome_norm)
        ticket = n.db.ticket(tid)
        try:
            canal = await _criar_canal_ticket(interaction.user, ticket, "mod", dados["nome"])
        except discord.HTTPException as e:
            n.db.mudar_status(tid, regras.ATIVOS, regras.ENCERRADO)
            log.exception("Falha ao criar canal do mod %s", tid)
            await interaction.followup.send(f"Não foi possível abrir o envio ({e}). Avise a equipe.",
                                            ephemeral=True)
            return
        await n.registrar(n.db.ticket(tid), interaction.user, "Mod enviado para avaliação",
                          f"{dados['nome']} — {dados['jogo']} — {C.rotulo_plataformas(dados['plataformas'])}",
                          C.cor_jogo(esc["jogo"]))
        if self.assistente is not None:
            await self.assistente.concluir(f"✅ **{dados['nome']}** enviado! Acompanhe em {canal.mention}.")
        await interaction.followup.send(
            f"✅ Envio recebido! Acompanhe a análise em {canal.mention}.", ephemeral=True)


class ModalContribuicao(discord.ui.Modal):
    def __init__(self, forma: str):
        f = FORMAS[forma]
        super().__init__(title=f"💎 Contribuir — {f['nome']}"[:45])
        self.forma = forma
        self.mensagem = discord.ui.TextInput(
            label="Como você quer contribuir?", style=discord.TextStyle.paragraph, min_length=10, max_length=1200,
            placeholder="Conte sua ideia. A equipe vai conversar com você num canal privado.")
        self.contato = discord.ui.TextInput(
            label="Disponibilidade / observações (opcional)", required=False, max_length=200,
            placeholder="Ex.: à noite, fins de semana")
        self.add_item(self.mensagem)
        self.add_item(self.contato)

    async def on_submit(self, interaction: discord.Interaction):
        n = nucleo()
        if len(n.db.ativos_do_autor(interaction.user.id, "contribuicao")) >= n.cfg.max_contribuicoes:
            await interaction.response.send_message("Você já tem uma conversa de contribuição aberta. "
                                                    "Continue por lá. 😉", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        dados = {"forma": self.forma, "mensagem": str(self.mensagem.value), "contato": str(self.contato.value or "")}
        tid = n.db.criar_ticket("contribuicao", interaction.user.id, dados)
        f = FORMAS[self.forma]
        try:
            canal = await _criar_canal_ticket(
                interaction.user, n.db.ticket(tid), "contribuicao", "",
                f"💎 {interaction.user.mention}, obrigado por querer apoiar a Operação Brasil! "
                "A equipe foi avisada e vai conversar com você aqui.")
        except discord.HTTPException as e:
            n.db.mudar_status(tid, regras.ATIVOS, regras.ENCERRADO)
            log.exception("Falha ao criar canal de contribuição %s", tid)
            await interaction.followup.send(f"Não foi possível abrir a conversa ({e}). Avise a equipe.",
                                            ephemeral=True)
            return
        await n.registrar(n.db.ticket(tid), interaction.user, "Contribuição aberta", f"{f['emoji']} {f['nome']}",
                          0xA855F7)
        await interaction.followup.send(f"✅ Conversa aberta em {canal.mention}. Só você e a equipe veem.",
                                        ephemeral=True)


class EscolherForma(discord.ui.View):
    """Menu efêmero: escolher a forma de contribuição abre o formulário."""

    def __init__(self):
        super().__init__(timeout=300)
        sel = discord.ui.Select(placeholder="💎 Escolha como você quer contribuir", options=[
            discord.SelectOption(label=f["nome"], value=k, emoji=f["emoji"], description=f["descricao"])
            for k, f in FORMAS.items()])
        sel.callback = self._escolha
        self.sel = sel
        self.add_item(sel)

    async def _escolha(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ModalContribuicao(self.sel.values[0]))


class PainelView(discord.ui.View):
    """Botões fixos dos painéis (custom_id estável = continuam funcionando após reinícios)."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=textos.PAINEL_DENUNCIA["botao"], emoji="📨", style=discord.ButtonStyle.danger,
                       custom_id="grb:painel:denuncia")
    async def denuncia(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(ModalDenuncia())

    @discord.ui.button(label=textos.PAINEL_CONTRIBUICAO["botao"], emoji="💎", style=discord.ButtonStyle.primary,
                       custom_id="grb:painel:contribuicao")
    async def contribuicao(self, interaction: discord.Interaction, _):
        n = nucleo()
        if len(n.db.ativos_do_autor(interaction.user.id, "contribuicao")) >= n.cfg.max_contribuicoes:
            await interaction.response.send_message("Você já tem uma conversa de contribuição aberta. "
                                                    "Continue por lá. 😉", ephemeral=True)
            return
        emb = discord.Embed(title="💎 Como você quer contribuir?",
                            description="Escolha uma opção no menu. Depois, conte sua ideia em poucas linhas.",
                            color=0xA855F7)
        await interaction.response.send_message(embed=emb, view=EscolherForma(), ephemeral=True)

    @discord.ui.button(label=textos.PAINEL_MOD["botao"], emoji="📤", style=discord.ButtonStyle.success,
                       custom_id="grb:painel:mod")
    async def mod(self, interaction: discord.Interaction, _):
        n = nucleo()
        if len(n.db.ativos_do_autor(interaction.user.id, "mod")) >= n.cfg.max_mods:
            await interaction.response.send_message(
                f"Você já tem {n.cfg.max_mods} envio(s) em análise. Aguarde a avaliação.", ephemeral=True)
            return
        assistente = AssistenteMod(interaction.user.id)
        assistente.origem = interaction
        await interaction.response.send_message(embed=_embed_assistente(assistente.esc), view=assistente,
                                                ephemeral=True)


def view_painel(chave: str, link_regras: str | None = None) -> discord.ui.View:
    v = PainelView()
    manter = f"grb:painel:{chave}"
    for item in list(v.children):
        if getattr(item, "custom_id", None) != manter:
            v.remove_item(item)
    if link_regras:
        v.add_item(discord.ui.Button(label="Regras para mods" if chave == "mod" else "Regras do servidor",
                                     emoji="📋", url=link_regras))
    return v


def embed_painel_contribuicao(guild: discord.Guild | None, boost_vip: bool = True) -> discord.Embed:
    t = textos.PAINEL_CONTRIBUICAO
    emb = discord.Embed(title=t["titulo"], description=t["texto"], color=0xA855F7)
    emb.set_author(name="GHOST RECON® | OPERAÇÃO BRASIL")
    emb.add_field(name="🚀 Impulsione o servidor", inline=True, value=(
        "Todo **booster vira VIP automaticamente**, enquanto o impulso durar." if boost_vip else
        "Impulsos ajudam o servidor a liberar recursos."))
    emb.add_field(name="💬 Fale com a equipe", inline=True,
                  value="Clique em **Quero contribuir** e abra uma conversa **privada** com a equipe.")
    emb.add_field(name="💎 O que o VIP ganha", value=t["beneficios"], inline=False)
    emb.add_field(name="🛡️ Segurança", value=t["seguranca"], inline=False)
    if (Path(__file__).resolve().parents[1] / "assets" / "painel_vip.png").is_file():
        emb.set_image(url="attachment://painel_vip.png")
    emb.set_footer(text="Operação Brasil • Nenhum operador fica para trás")
    return emb


BANNERS_PAINEL = {"denuncia": "painel_denuncia.png", "mod": "painel_mods.png", "contribuicao": "painel_vip.png"}


def arquivo_banner(chave: str) -> discord.File | None:
    nome = BANNERS_PAINEL.get(chave)
    arq = Path(__file__).resolve().parents[1] / "assets" / (nome or "_")
    return discord.File(arq, filename=nome) if nome and arq.is_file() else None


def arquivo_banner_vip() -> discord.File | None:
    return arquivo_banner("contribuicao")


def embed_painel(chave: str, guild: discord.Guild | None) -> discord.Embed:
    if chave == "contribuicao":
        return embed_painel_contribuicao(guild, nucleo().cfg.boost_vip)
    txt = textos.PAINEL_DENUNCIA if chave == "denuncia" else textos.PAINEL_MOD
    emb = discord.Embed(title=txt["titulo"], description=txt["texto"],
                        color=textos.COR_ALERTA if chave == "denuncia" else textos.COR)
    if chave == "mod":
        emb.add_field(name="🎮 Jogos", value="\n".join(f"{j['emoji']} {j['nome']}" for j in C.JOGOS.values()),
                      inline=True)
        emb.add_field(name="🏷️ Categorias", value="\n".join(f"{c['emoji']} {c['nome']}"
                                                          for c in list(C.CATEGORIAS.values())[:8]), inline=True)
    emb.set_author(name="GHOST RECON® | OPERAÇÃO BRASIL")
    nome = BANNERS_PAINEL.get(chave)
    if nome and (Path(__file__).resolve().parents[1] / "assets" / nome).is_file():
        emb.set_image(url=f"attachment://{nome}")
    elif guild is not None and guild.icon:
        emb.set_thumbnail(url=guild.icon.url)
    emb.set_footer(text="Operação Brasil • Nenhum operador fica para trás")
    return emb


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------
class Tickets(commands.Cog):
    grupo = app_commands.Group(name="tickets", description="Administração dos tickets",
                               default_permissions=discord.Permissions(manage_guild=True), guild_only=True)

    def __init__(self, bot: commands.Bot, n: Nucleo):
        self.bot = bot
        self.n = n

    async def preparar(self):
        await self.n.categoria_tickets()
        await self.n.garantir_acesso_bot()
        await self.garantir_canal_contribuicao()
        await self.garantir_paineis()
        if self.n.web is not None:
            self.n.web.ao_mudar_url = self.atualizar_links_transcript
            await self.atualizar_links_transcript()
        if not self.inatividade.is_running():
            self.inatividade.start()

    async def garantir_canal_contribuicao(self):
        """Cria #💎｜contribuição na categoria VIPs (se não existir). Membros só usam o botão."""
        g = self.n.guild
        ch = self.n.canal("contribuicao")
        if ch is None:
            vips = self.n.canal("vips")
            if vips is None:
                log.warning("Canal de VIPs não encontrado; não sei onde criar o canal de contribuição.")
                return
            try:
                ch = await g.create_text_channel(
                    self.n.cfg.nome_canal_contribuicao, category=vips.category, position=vips.position + 1,
                    topic="Quer apoiar a comunidade? Clique em Quero contribuir e fale com a equipe em privado. "
                          "Boosters viram VIP automaticamente.",
                    reason="Operação Brasil: canal de contribuição")
                log.info("Canal #%s criado.", ch.name)
            except discord.HTTPException as e:
                log.warning("Não foi possível criar o canal de contribuição: %s", e)
                return
        # 1º o próprio acesso do bot (a categoria VIPs bloqueia escrita para @everyone)
        try:
            if not ch.overwrites_for(g.self_role).send_messages:
                await ch.set_permissions(g.self_role, reason="Operação Brasil: painel de contribuição",
                                         overwrite=overwrite_seguro(g, discord.PermissionOverwrite(
                                             view_channel=True, send_messages=True, embed_links=True,
                                             attach_files=True, read_message_history=True, pin_messages=True)))
        except discord.Forbidden:
            log.warning("Sem permissão para liberar o bot em #%s. Dê ao cargo '%s' (em Editar canal > Permissões): "
                        "Ver canal, Enviar mensagens, Inserir links, Anexar arquivos e Fixar mensagens.",
                        ch.name, g.self_role.name)
        # 2º membros e VIPs só usam o botão
        for alvo in [g.default_role, *[r for r in g.roles if regras.slug(r.name) == "vip"]]:
            atual = ch.overwrites_for(alvo)
            if atual.send_messages is False:
                continue
            atual.update(send_messages=False)
            try:
                await ch.set_permissions(alvo, overwrite=overwrite_seguro(g, atual),
                                         reason="Contribuição: só pelo botão")
            except discord.Forbidden:
                log.warning("Não consegui impedir '%s' de escrever em #%s; ajuste manualmente se quiser.",
                            alvo.name, ch.name)

    async def garantir_paineis(self, forcar: bool = False) -> list[str]:
        """Publica os painéis; se já existirem, apenas os atualiza (texto, botões e visual)."""
        feitos = []
        g = self.n.guild
        for chave, canal_chave, canal_regras in (("denuncia", "denuncias", None),
                                                 ("mod", "publicar_mod", "regras_mods"),
                                                 ("contribuicao", "contribuicao", None)):
            ch = self.n.canal(canal_chave)
            if ch is None:
                feitos.append(f"Canal de {chave} não encontrado")
                continue
            link = None
            if canal_regras:
                cr = self.n.canal(canal_regras)
                if cr is not None:
                    link = f"https://discord.com/channels/{g.id}/{cr.id}"
            emb, view = embed_painel(chave, g), view_painel(chave, link)
            salvo = self.n.db.painel(chave)
            if salvo and salvo["canal_id"] == ch.id and not forcar:
                try:
                    msg = await ch.fetch_message(salvo["msg_id"])
                    arq = arquivo_banner(chave)
                    extra = {"attachments": [arq] if arq else []}
                    await msg.edit(embed=emb, view=view, **extra)
                    feitos.append(f"Painel '{chave}' atualizado em #{ch.name}")
                    continue
                except discord.NotFound:
                    pass
            arq = arquivo_banner(chave)
            try:
                msg = await ch.send(embed=emb, view=view, **({"file": arq} if arq else {}))
            except discord.Forbidden:
                feitos.append(f"Sem permissão para publicar em #{ch.name}")
                log.error("Sem permissão para publicar o painel '%s' em #%s. Dê ao cargo do bot: Ver canal, "
                          "Enviar mensagens, Inserir links e Anexar arquivos nesse canal.", chave, ch.name)
                continue
            try:
                await msg.pin(reason="Painel de tickets")
            except discord.HTTPException:
                pass
            self.n.db.salvar_painel(chave, ch.id, msg.id)
            feitos.append(f"Painel '{chave}' publicado em #{ch.name}")
            log.info("Painel %s publicado em #%s", chave, ch.name)
        return feitos

    async def _achar_msgs_antigas(self, t: dict, token: str) -> list[list[int]]:
        """Para transcripts gerados antes desta versão: procura as mensagens com o botão."""
        achadas: list[list[int]] = []
        alvo = f"/t/{token}"

        def tem_link(m: discord.Message) -> bool:
            return any(alvo in (getattr(c, "url", None) or "")
                       for linha in m.components for c in getattr(linha, "children", []))

        locais = []
        rel = self.n.canal("relatorios")
        if rel is not None:
            locais.append(rel)
        try:
            usuario = self.bot.get_user(t["autor_id"]) or await self.bot.fetch_user(t["autor_id"])
            locais.append(usuario.dm_channel or await usuario.create_dm())
        except discord.HTTPException:
            pass
        for local in locais:
            try:
                async for m in local.history(limit=200):
                    if m.author.id == self.bot.user.id and tem_link(m):
                        achadas.append([m.channel.id, m.id])
            except discord.HTTPException:
                pass
        return achadas

    async def atualizar_links_transcript(self) -> int:
        """O endereço do túnel muda a cada reinício: troca o botão das mensagens antigas pelo endereço atual."""
        web = self.n.web
        if web is None or not web.url_publica:
            return 0
        editados = 0
        for t in self.n.db.com_transcript():
            d = t["dados"]
            token = d["transcript_token"]
            if not web.existe(token):
                continue
            url = web.link(token)
            msgs = d.get("transcript_msgs")
            if d.get("transcript_url") == url and msgs is not None:
                continue
            if msgs is None:
                msgs = await self._achar_msgs_antigas(t, token)
            restantes = []
            for canal_id, msg_id in msgs:
                try:
                    msg = self.bot.get_partial_messageable(canal_id).get_partial_message(msg_id)
                    await msg.edit(view=view_transcript(url))
                    restantes.append([canal_id, msg_id])
                    editados += 1
                except discord.NotFound:
                    pass  # mensagem apagada
                except discord.HTTPException as e:
                    log.warning("Não foi possível atualizar o link do transcript #%04d: %s", t["id"], e)
                    restantes.append([canal_id, msg_id])
            d["transcript_url"], d["transcript_msgs"] = url, restantes
            self.n.db.atualizar_dados(t["id"], d)
        if editados:
            log.info("Links de transcript atualizados para o endereço atual: %d mensagem(ns).", editados)
        return editados

    @tasks.loop(hours=1)
    async def inatividade(self):
        if self.n.web is not None:
            removidos = self.n.web.limpar_expirados()
            if removidos:
                log.info("%d transcript(s) expirado(s) removido(s).", removidos)
        limite = datetime.now(timezone.utc) - timedelta(days=self.n.cfg.inatividade_dias)
        for t in self.n.db.ativos():
            canal = self.n.guild.get_channel(t["canal_id"]) if t.get("canal_id") else None
            if canal is None:
                if self.n.db.mudar_status(t["id"], regras.ATIVOS, regras.ENCERRADO):
                    await self.n.registrar(t, self.bot.user.id, "Ticket encerrado (canal apagado)")
                continue
            # Mods aguardando a equipe não expiram; expiram denúncias paradas e pedidos de alteração sem resposta.
            if t["tipo"] == "mod" and t["status"] == regras.ABERTO:
                continue
            ultimo = discord.utils.snowflake_time(canal.last_message_id) if canal.last_message_id else canal.created_at
            if ultimo < limite:
                await executar_acao(None, t["id"], "encerrar", automatico=True)

    @inatividade.before_loop
    async def _antes(self):
        await self.bot.wait_until_ready()

    @grupo.command(name="paineis", description="Publica de novo os painéis de denúncia e de envio de mods")
    async def paineis(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        feitos = await self.garantir_paineis()
        await self.n.registrar(None, interaction.user, "Painéis republicados", "\n".join(feitos))
        await interaction.followup.send("\n".join(feitos) or "Nada a fazer.", ephemeral=True)

    @grupo.command(name="info", description="Mostra status e histórico de um ticket")
    @app_commands.describe(numero="Número do ticket (ex.: 12)")
    async def info(self, interaction: discord.Interaction, numero: int):
        if not self.n.eh_equipe(interaction.user):
            await interaction.response.send_message("Somente a equipe.", ephemeral=True)
            return
        t = self.n.db.ticket(numero)
        if t is None:
            await interaction.response.send_message("Ticket não encontrado.", ephemeral=True)
            return
        emb = embed_ticket(t)
        hist = self.n.db.historico(numero)[-10:]
        if hist:
            emb.add_field(name="Histórico (últimas ações)", inline=False,
                          value="\n".join(f"`{h['data'][:16]}` <@{h['ator_id']}> — {h['acao']}" for h in hist)[:1024])
        await interaction.response.send_message(embed=emb, ephemeral=True)


async def setup(bot: commands.Bot, n: Nucleo):
    global NUCLEO
    NUCLEO = n
    bot.add_view(PainelView())
    bot.add_dynamic_items(BotaoTicket)
    cog = Tickets(bot, n)
    await bot.add_cog(cog, guild=discord.Object(n.cfg.guild_id))
    return cog
