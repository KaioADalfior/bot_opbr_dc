"""Testes de contribuição (ticket) e VIP (concessão pela equipe e automático para boosters)."""
from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import discord  # noqa: E402

from bot import regras  # noqa: E402
from bot.cogs import tickets as T  # noqa: E402
from bot.cogs import vip as V  # noqa: E402
from bot.config import Config  # noqa: E402
from bot.db import Banco  # noqa: E402
from bot.nucleo import Nucleo  # noqa: E402


class Cargo:
    """Cargo simples e comparável (posição na hierarquia)."""
    def __init__(self, id, nome, pos):
        self.id, self.name, self.position = id, nome, pos

    def __le__(self, o): return self.position <= o.position
    def __eq__(self, o): return isinstance(o, Cargo) and o.id == self.id
    def __hash__(self): return self.id


def membro(uid, equipe=False, booster=False):
    m = MagicMock(spec=discord.Member)
    m.id = uid
    m.mention = f"<@{uid}>"
    m.guild_permissions.administrator = False
    m.guild.owner_id = 1
    m.guild.id = 123456789012345678
    m.roles = [MagicMock(id=500)] if equipe else []
    m.premium_since = datetime.now(timezone.utc) if booster else None
    m.send = AsyncMock()

    async def add(r, reason=None): m.roles.append(r)
    async def rem(r, reason=None): m.roles.remove(r)
    m.add_roles = AsyncMock(side_effect=add)
    m.remove_roles = AsyncMock(side_effect=rem)
    m.display_avatar.url = "https://cdn.discordapp.com/x.png"
    return m


class Base(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        cfg = Config(token="a.b.c", guild_id=123456789012345678, conteudo_mensagens=True, inatividade_dias=7,
                     max_denuncias=1, max_mods=2, banco=Path(":memory:"))
        self.bot = MagicMock()
        self.n = Nucleo(self.bot, cfg, Banco(":memory:"))
        T.NUCLEO = self.n
        self.vip = Cargo(900, "💎 VIP", 5)
        g = MagicMock()
        g.roles = [self.vip]
        g.me.guild_permissions = discord.Permissions(manage_roles=True)
        g.me.top_role = Cargo(1, "Operação Brasil", 20)
        self.membros = {}
        g.get_member = lambda uid: self.membros.get(uid)
        self.g = g
        mock.patch.object(Nucleo, "guild", new_callable=mock.PropertyMock, return_value=g).start()
        self.addCleanup(mock.patch.stopall)
        self.n.membro = AsyncMock(side_effect=lambda uid: self.membros.get(uid))
        self.n.cargos_equipe = lambda: [MagicMock(id=500)]
        self.n.registrar = AsyncMock()
        self.vips_canal = MagicMock(send=AsyncMock())
        self.n.canal = lambda chave: {"vips": self.vips_canal}.get(chave)


class TestContribuicao(Base):
    async def test_ticket_e_vip(self):
        canal = MagicMock(spec=discord.TextChannel)
        canal.id, canal.mention = 777, "<#777>"
        canal.send = AsyncMock(return_value=MagicMock(id=888))
        canal.fetch_message = AsyncMock(return_value=MagicMock(edit=AsyncMock()))
        self.g.get_channel = lambda cid: canal if cid == 777 else None
        self.g.create_text_channel = AsyncMock(return_value=canal)
        self.n.categoria_tickets = AsyncMock(return_value=MagicMock())
        autor, staff = membro(10), membro(20, equipe=True)
        self.membros.update({10: autor, 20: staff})

        modal = T.ModalContribuicao("conteudo")
        modal.mensagem._value = "Posso fazer vídeos e lives da comunidade."
        modal.contato._value = "à noite"
        it = MagicMock(user=autor)
        it.response.defer = AsyncMock()
        it.followup.send = AsyncMock()
        await modal.on_submit(it)
        self.assertIn("Conversa aberta", it.followup.send.call_args.args[0])
        t = self.n.db.ticket(1)
        self.assertEqual((t["tipo"], t["dados"]["forma"]), ("contribuicao", "conteudo"))
        self.assertEqual(self.g.create_text_channel.call_args.args[0], "contribuicao-0001")
        emb = canal.send.call_args_list[0].kwargs["embed"]
        self.assertIn("Contribuição #0001", emb.title)

        # Segunda conversa: bloqueada
        it2 = MagicMock(user=autor)
        it2.response.send_message = AsyncMock()
        await modal.on_submit(it2)
        self.assertIn("já tem uma conversa", it2.response.send_message.call_args.args[0])

        # Membro comum não concede VIP
        it3 = MagicMock(user=autor)
        it3.followup.send = AsyncMock()
        await T.executar_acao(it3, 1, "vip_dar")
        self.assertNotIn(self.vip, autor.roles)

        # Equipe concede VIP
        it4 = MagicMock(user=staff)
        it4.followup.send = AsyncMock()
        await T.executar_acao(it4, 1, "vip_dar")
        self.assertIn(self.vip, autor.roles)
        self.assertEqual(self.n.db.vip(10)["origem"], "contribuicao")
        autor.send.assert_awaited()                                  # DM de parabéns
        self.assertIn("agora é **VIP**", canal.send.call_args.args[0])

        # Equipe remove
        await T.executar_acao(it4, 1, "vip_remover")
        self.assertNotIn(self.vip, autor.roles)
        self.assertIsNone(self.n.db.vip(10))

    def test_regras(self):
        with self.assertRaises(regras.AcaoNegada):
            regras.verificar_acao("vip_dar", "contribuicao", regras.ABERTO, 10, 10, True)   # a si mesmo
        with self.assertRaises(regras.AcaoNegada):
            regras.verificar_acao("vip_dar", "denuncia", regras.ABERTO, 10, 20, True)       # tipo errado
        self.assertIsNone(regras.verificar_acao("vip_dar", "contribuicao", regras.ABERTO, 10, 20, True))

    def test_painel(self):
        v = T.view_painel("contribuicao")
        self.assertEqual([i.custom_id for i in v.children], ["grb:painel:contribuicao"])
        emb = T.embed_painel_contribuicao(None)
        self.assertIn("booster vira VIP", emb.fields[0].value)
        self.assertEqual(emb.image.url, "attachment://painel_vip.png")


class TestBoostVip(Base):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.cog = V.Vip(self.bot, self.n)

    async def test_boost_da_e_tira_vip(self):
        antes, depois = membro(30), membro(30, booster=True)
        self.membros[30] = depois
        await self.cog.on_member_update(antes, depois)
        self.assertIn(self.vip, depois.roles)
        self.assertEqual(self.n.db.vip(30)["origem"], "boost")
        self.vips_canal.send.assert_awaited()                         # agradecimento em #vips

        fim = membro(30)
        fim.roles = list(depois.roles)
        await self.cog.on_member_update(depois, fim)
        self.assertNotIn(self.vip, fim.roles)
        self.assertIsNone(self.n.db.vip(30))

    async def test_vip_por_contribuicao_nao_cai_com_fim_do_boost(self):
        m = membro(40)
        await V.dar_vip(self.n, m, "contribuicao", por=20)
        booster = membro(40, booster=True)
        booster.roles = list(m.roles)
        await self.cog.on_member_update(m, booster)                     # impulsionou
        self.assertEqual(self.n.db.vip(40)["origem"], "contribuicao")   # continua contribuição
        fim = membro(40)
        fim.roles = list(booster.roles)
        await self.cog.on_member_update(booster, fim)                   # parou de impulsionar
        self.assertIn(self.vip, fim.roles)                              # mantém o VIP

    async def test_sincronizar(self):
        b1, ex = membro(50, booster=True), membro(51)
        ex.roles = [self.vip]
        self.membros.update({50: b1, 51: ex})
        self.n.db.salvar_vip(51, "boost")
        self.n.db.salvar_vip(52, "boost")                               # saiu do servidor
        self.g.premium_subscribers = [b1]
        self.assertEqual(await self.cog.sincronizar(), (1, 1))
        self.assertIn(self.vip, b1.roles)
        self.assertNotIn(self.vip, ex.roles)
        self.assertIsNone(self.n.db.vip(52))

    def test_hierarquia(self):
        self.g.me.top_role = Cargo(1, "Operação Brasil", 3)            # abaixo do VIP
        self.assertIn("ACIMA", V.problema_cargo(self.n))


if __name__ == "__main__":
    unittest.main()


class TestOverwriteSeguro(unittest.TestCase):
    def test_tira_so_liberacoes_que_o_bot_nao_tem(self):
        from bot.nucleo import overwrite_seguro
        g = MagicMock()
        g.me.guild_permissions = discord.Permissions(view_channel=True, send_messages=True)
        ow = discord.PermissionOverwrite(view_channel=True, add_reactions=True, send_messages=False,
                                         mention_everyone=False)
        r = overwrite_seguro(g, ow)
        self.assertTrue(r.view_channel)
        self.assertIsNone(r.add_reactions)          # liberação que o bot não tem: removida
        self.assertFalse(r.send_messages)           # bloqueios mantidos
        self.assertFalse(r.mention_everyone)
