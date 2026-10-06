"""Testes do módulo de squads (#squad-partida) com Discord simulado."""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import discord  # noqa: E402

from bot.cogs import squads as S  # noqa: E402
from bot.config import Config  # noqa: E402
from bot.db import Banco  # noqa: E402
from bot.nucleo import Nucleo  # noqa: E402


def membro(uid, equipe=False, na_call=None):
    m = MagicMock(spec=discord.Member)
    m.id = uid
    m.mention = f"<@{uid}>"
    m.guild_permissions.administrator = False
    m.guild.owner_id = 1
    m.roles = [MagicMock(id=500)] if equipe else []
    m.voice = MagicMock(channel=na_call) if na_call else None
    m.move_to = AsyncMock()
    m.__str__ = lambda self: f"user{uid}"
    return m


def interacao(user):
    it = MagicMock()
    it.user = user
    it.followup.send = AsyncMock()
    it.response.send_message = AsyncMock()
    return it


class TestUtilidades(unittest.TestCase):
    def test_nome(self):
        self.assertEqual(S.limpar_nome("  Fantasmas   de Auroa "), "Fantasmas de Auroa")
        self.assertIsNone(S.limpar_nome("discord.gg/abc"))
        self.assertIsNone(S.limpar_nome("ab"))
        self.assertEqual(S.limpar_nome("@everyone **Ghosts**"), "everyone Ghosts")
        self.assertEqual(len(S.limpar_nome("x" * 60)), 24)

    def test_texto(self):
        self.assertNotIn("@everyone", S.limpar_texto("oi @everyone <@123>", 200))


class TestFluxoSquad(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        cfg = Config(token="a.b.c", guild_id=123456789012345678, conteudo_mensagens=True, inatividade_dias=7,
                     max_denuncias=1, max_mods=2, banco=Path(":memory:"))
        self.bot = MagicMock()
        self.n = Nucleo(self.bot, cfg, Banco(":memory:"))
        S.NUCLEO = self.n
        self.cog = S.Squads(self.bot, self.n)
        self.bot.get_cog = lambda nome: self.cog

        # call de voz simulada
        self.voz = MagicMock(spec=discord.VoiceChannel)
        self.voz.id = 9000
        self.voz.mention = "<#9000>"
        self.voz.voice_states = {}
        self.voz.set_permissions = AsyncMock()
        self.voz.send = AsyncMock()
        self.voz.delete = AsyncMock()
        # canal #squad-partida
        self.card = MagicMock(edit=AsyncMock(), delete=AsyncMock())
        self.canal = MagicMock(spec=discord.TextChannel)
        self.canal.id = 7000
        self.canal.send = AsyncMock(return_value=MagicMock(id=7100))
        self.canal.get_partial_message = MagicMock(return_value=self.card)
        g = MagicMock()
        g.id = cfg.guild_id
        g.me.guild_permissions = discord.Permissions.all()
        g.get_channel = lambda cid: self.voz if cid == 9000 and not self.voz_apagada else None
        g.get_member = lambda uid: None
        g.create_voice_channel = AsyncMock(return_value=self.voz)
        self.voz_apagada = False
        self.g = g
        mock.patch.object(Nucleo, "guild", new_callable=mock.PropertyMock, return_value=g).start()
        self.addCleanup(mock.patch.stopall)
        self.n.canal = lambda chave: self.canal if chave == "squad_partida" else None
        self.n.cargos_equipe = lambda: [MagicMock(id=500)]
        self.cog.categoria = AsyncMock(return_value=MagicMock())

    async def abrir(self, lider, jogo="breakpoint", nome="Fantasmas de Auroa"):
        it = interacao(lider)
        esc = {"jogo": jogo, "plataforma": "pc", "modo": "campanha", "estilo": "furtivo"}
        await self.cog.criar(it, esc, nome, "Kaio#GR", "Extremo, com microfone", None)
        return it

    async def test_ciclo_completo(self):
        lider = membro(10, na_call=MagicMock(id=1))   # já está em outra call → é movido
        it = await self.abrir(lider)
        self.assertIn("aberto", it.followup.send.call_args.args[0])
        lider.move_to.assert_awaited_with(self.voz, reason=mock.ANY)
        kw = self.g.create_voice_channel.call_args
        self.assertEqual(kw.args[0], "💀 Fantasmas de Auroa")
        self.assertEqual(kw.kwargs["user_limit"], 4)
        ow = kw.kwargs["overwrites"]
        self.assertFalse(ow[self.g.default_role].connect)       # público não entra
        self.assertTrue(ow[lider].connect)                       # líder entra
        s = self.n.db.squad(1)
        self.assertEqual((s["voz_id"], s["msg_id"]), (9000, 7100))
        emb = self.canal.send.call_args.kwargs["embed"]
        self.assertIn("`1/4`", emb.description)
        self.assertEqual(emb.image.url, "attachment://squad_breakpoint.png")
        self.assertEqual(self.canal.send.call_args.kwargs["file"].filename, "squad_breakpoint.png")

        # Não pode abrir um segundo squad
        it = await self.abrir(lider, nome="Outro")
        self.assertIn("já está no squad", it.followup.send.call_args.args[0])

        # 3 jogadores entram → completo
        for uid in (20, 30, 40):
            await self.cog.entrar(interacao(membro(uid)), 1)
        s = self.n.db.squad(1)
        self.assertEqual(s["membros"], [20, 30, 40])
        self.assertEqual(self.voz.set_permissions.await_count, 3)
        view = self.card.edit.call_args.kwargs["view"]
        self.assertTrue(view.children[0].item.disabled)          # botão "Eu vou" travado
        self.assertIn("completo", view.children[0].item.label.lower())

        # 5º jogador recusado
        it = interacao(membro(50))
        await self.cog.entrar(it, 1)
        self.assertIn("completo", it.followup.send.call_args.args[0])

        # Entrar de novo no mesmo squad
        it = interacao(membro(20))
        await self.cog.entrar(it, 1)
        self.assertIn("já está neste squad", it.followup.send.call_args.args[0])

        # Membro comum não encerra
        it = interacao(membro(30))
        await self.cog.encerrar_por_botao(it, 1)
        self.assertIn("Só o **líder**", it.followup.send.call_args.args[0])

        # Líder sai → liderança passa para o próximo
        await self.cog.sair(interacao(lider), 1)
        s = self.n.db.squad(1)
        self.assertEqual(s["lider_id"], 20)
        self.assertEqual(s["membros"], [30, 40])
        self.assertIn("Novo líder", self.voz.send.call_args.args[0])

        # Novo líder encerra → call e card apagados
        await self.cog.encerrar_por_botao(interacao(membro(20)), 1)
        self.assertEqual(self.n.db.squad(1)["status"], "encerrado")
        self.voz.delete.assert_awaited()
        self.card.delete.assert_awaited()
        # encerrar duas vezes não apaga de novo
        await self.cog.encerrar(1, "teste")
        self.assertEqual(self.voz.delete.await_count, 1)

    async def test_siege_tem_5_vagas(self):
        await self.abrir(membro(10), jogo="r6", nome="Time Alfa")
        self.assertEqual(self.n.db.squad(1)["vagas"], 5)
        self.assertEqual(self.g.create_voice_channel.call_args.args[0], "👮 Time Alfa")

    async def test_vigia_fecha_call_vazia_e_apagada(self):
        await self.abrir(membro(10))
        self.cog.vazio_desde[1] = time.time() - 60          # vazia há 1 min: continua
        await self.cog.vigia.coro(self.cog)
        self.assertEqual(self.n.db.squad(1)["status"], "ativo")
        self.voz.voice_states = {10: MagicMock()}            # alguém na call: nunca fecha
        self.cog.vazio_desde[1] = time.time() - 3600
        await self.cog.vigia.coro(self.cog)
        self.assertEqual(self.n.db.squad(1)["status"], "ativo")
        self.voz.voice_states = {}
        self.cog.vazio_desde[1] = time.time() - 11 * 60      # vazia há 11 min: fecha
        await self.cog.vigia.coro(self.cog)
        self.assertEqual(self.n.db.squad(1)["status"], "encerrado")

        await self.abrir(membro(11), nome="Segundo")
        self.voz_apagada = True                              # alguém apagou a call na mão
        await self.cog.vigia.coro(self.cog)
        self.assertEqual(self.n.db.squad(2)["motivo"], "call apagada")

    async def test_lider_sozinho_sai_encerra(self):
        lider = membro(10)
        await self.abrir(lider)
        it = interacao(lider)
        await self.cog.sair(it, 1)
        self.assertEqual(self.n.db.squad(1)["status"], "encerrado")
        self.assertIn("encerrado", it.followup.send.call_args.args[0])

    async def test_sem_permissao(self):
        self.g.me.guild_permissions = discord.Permissions(view_channel=True, send_messages=True)
        it = await self.abrir(membro(10))
        self.assertIn("permissão", it.followup.send.call_args.args[0])
        self.g.create_voice_channel.assert_not_awaited()

    async def test_cria_abrir_squad_e_move_painel(self):
        abrir = MagicMock(spec=discord.TextChannel)
        abrir.id, abrir.name, abrir.mention = 6000, "🎯｜abrir-squad", "<#6000>"
        abrir.send = AsyncMock(return_value=MagicMock(id=6100, pin=AsyncMock()))
        abrir.overwrites_for = lambda alvo: discord.PermissionOverwrite()
        abrir.set_permissions = AsyncMock()
        self.canal.name = "🎮｜squad-partida"
        self.canal.position = 5
        self.canal.overwrites_for = lambda alvo: discord.PermissionOverwrite()
        self.canal.set_permissions = AsyncMock()
        criado = []
        self.n.canal = lambda chave: {"squad_partida": self.canal,
                                      "abrir_squad": abrir if criado else None}.get(chave)

        async def criar(nome, **kw):
            criado.append((nome, kw))
            return abrir
        self.g.create_text_channel = criar
        await self.cog.garantir_canal()
        self.assertEqual(criado[0][0], "🎯｜abrir-squad")
        self.assertEqual(criado[0][1]["position"], 5)            # logo acima de #squad-partida
        todos = abrir.set_permissions.call_args_list[-1].kwargs["overwrite"]
        self.assertFalse(todos.send_messages)                      # membros só usam botões

        # painel antigo estava em #squad-partida → apagado e republicado em #abrir-squad
        self.n.db.salvar_painel("squad", self.canal.id, 7777)
        self.g.get_channel = lambda cid: self.canal if cid == 7000 else None
        await self.cog.garantir_painel()
        self.canal.get_partial_message.assert_any_call(7777)
        self.card.delete.assert_awaited()
        self.assertEqual(self.n.db.painel("squad")["canal_id"], 6000)
        self.assertIn("<#7000>", abrir.send.call_args.kwargs["embed"].fields[0].value)

    def test_assistente_modos_por_jogo(self):
        a = S.AssistenteSquad(10)
        a._marcar()
        self.assertTrue(a.sel_modo.disabled and a.btn_ok.disabled)
        a.esc.update(jogo="r6", plataforma="ps")
        a._marcar()
        self.assertIn("ranqueada", [o.value for o in a.sel_modo.options])
        self.assertTrue(a.btn_ok.disabled)                     # falta o modo
        a.esc["modo"] = "ranqueada"
        a._marcar()
        self.assertFalse(a.btn_ok.disabled)
        emb = S._embed_assistente(a.esc)
        self.assertIn("**4** jogadores", emb.fields[0].value)


if __name__ == "__main__":
    unittest.main()


class TestRemoverSalas(unittest.IsolatedAsyncioTestCase):
    async def test_remove_so_salas_vazias(self):
        cfg = Config(token="a.b.c", guild_id=1, conteudo_mensagens=True, inatividade_dias=7,
                     max_denuncias=1, max_mods=2, banco=Path(":memory:"))
        n = Nucleo(MagicMock(), cfg, Banco(":memory:"))
        n.registrar = AsyncMock()

        def cat(cid, nome):
            c = MagicMock(spec=discord.CategoryChannel)
            c.id, c.name, c.delete = cid, nome, AsyncMock()
            return c

        def voz(cid, nome, cat_id, gente=0):
            v = MagicMock(spec=discord.VoiceChannel)
            v.id, v.name, v.category_id = cid, nome, cat_id
            v.voice_states = {i: 1 for i in range(gente)}
            v.delete = AsyncMock(side_effect=lambda **kw: canais.remove(v))
            return v

        bp, wl, geral = cat(1, "╭─── 💀 Breakpoint | Salas"), cat(2, "╭─── 🌿 Wildlands | Salas"), cat(3, "╭─── 💀 Breakpoint")
        calls = [voz(10 + i, f"💀 Breakpoint {p} {k}", 1) for i, (p, k) in
                 enumerate((p, k) for p in ("PC", "XBOX", "PS") for k in range(1, 5))]
        ocupada = voz(40, "🌿 Wildlands PC 1", 2, gente=2)
        estranho = voz(41, "🌿 Sala do Kaio", 2)
        protegida = voz(50, "💀 Breakpoint Geral", 3)
        bp.channels, wl.channels, geral.channels = calls, [ocupada, estranho], [protegida]
        canais = [*calls, ocupada, estranho, protegida]
        g = MagicMock()
        g.categories = [bp, wl, geral]
        type(g).channels = mock.PropertyMock(side_effect=lambda: list(canais))
        mock.patch.object(Nucleo, "guild", new_callable=mock.PropertyMock, return_value=g).start()
        self.addCleanup(mock.patch.stopall)

        cats, alvo, outros = S.salas_antigas(g)
        self.assertEqual((len(cats), len(alvo)), (2, 13))
        self.assertEqual(outros, [estranho])
        apagadas, cats_ok, puladas = await S.remover_salas(n, "Kaio")
        self.assertEqual(apagadas, 12)                 # a ocupada é pulada
        bp.delete.assert_awaited()                     # ficou vazia → apagada
        wl.delete.assert_not_awaited()                 # ainda tem canais → preservada
        geral.delete.assert_not_awaited()
        protegida.delete.assert_not_awaited()
        estranho.delete.assert_not_awaited()
        self.assertTrue(any("Wildlands PC 1" in p for p in puladas))
