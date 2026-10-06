"""Testes das mensagens fixas dos canais (/servidor publicar) e da checagem de instalação."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import discord  # noqa: E402

from bot import conteudo as K  # noqa: E402
from bot.cogs import servidor as SV  # noqa: E402
from bot.config import Config  # noqa: E402
from bot.db import Banco  # noqa: E402
from bot.nucleo import Nucleo  # noqa: E402
from bot.preflight import checar_conteudo  # noqa: E402
from gr_setup import estrutura as E  # noqa: E402


class TestConteudo(unittest.TestCase):
    def test_canais_iguais_a_estrutura(self):
        """O bot e o script de configuração precisam concordar sobre nomes e categorias."""
        oficial = {c.chave: (c.nome, cat.chave, c.tipo) for cat in E.CATEGORIAS for c in cat.canais}
        bot = {k: v[:3] for k, v in K.CANAIS.items()}
        self.assertEqual(bot, oficial)
        self.assertEqual({k: v[0] for k, v in K.CATEGORIAS.items()}, {c.chave: c.nome for c in E.CATEGORIAS})

    def test_limites_do_discord(self):
        self.assertEqual(checar_conteudo(), [])

    def test_todo_canal_de_texto_tem_mensagem_ou_painel(self):
        texto = {k for k, v in K.CANAIS.items() if v[2] in ("texto", "anuncio")}
        sem = texto - set(K.MENSAGENS) - K.CANAIS_DE_PAINEL
        self.assertEqual(sem, set())

    def test_sem_textos_desatualizados(self):
        tudo = str(K.MENSAGENS).lower()
        for velho in ("nenhum bot ou comando está ativo", "ainda estão sendo definidas", "use o modelo fixado em cada",
                      "breakpoint pc 1", "estará disponível futuramente"):
            self.assertNotIn(velho, tudo)


def canal_texto(cid, nome, cat=None, pode=True):
    ch = MagicMock(spec=discord.TextChannel)
    ch.id, ch.name, ch.category = cid, nome, cat
    perms = discord.Permissions(view_channel=pode, send_messages=pode, embed_links=pode, attach_files=pode,
                                read_message_history=True, manage_messages=True)
    ch.permissions_for = lambda alvo: perms
    ch.history = MagicMock(return_value=_aiter([]))
    ch.send = AsyncMock(side_effect=lambda **kw: MagicMock(id=cid * 10, pin=AsyncMock()))
    ch.fetch_message = AsyncMock(side_effect=discord.NotFound(MagicMock(status=404), "x"))
    ch.parcial = MagicMock(edit=AsyncMock(), delete=AsyncMock())
    ch.get_partial_message = MagicMock(return_value=ch.parcial)
    ch.set_permissions = AsyncMock()
    return ch


def _aiter(itens):
    async def gen():
        for i in itens:
            yield i
    return gen()


class TestPublicacao(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        cfg = Config(token="a.b.c", guild_id=1556051792067035288, conteudo_mensagens=True, inatividade_dias=7,
                     max_denuncias=1, max_mods=2, banco=Path(":memory:"))
        self.n = Nucleo(MagicMock(), cfg, Banco(":memory:"))
        cats = {}
        for k, v in K.CATEGORIAS.items():
            cats[k] = MagicMock(spec=discord.CategoryChannel)
            cats[k].name = v[0]
        self.canais = {}
        for i, (chave, (nome, cat, tipo, _)) in enumerate(K.CANAIS.items()):
            if tipo == "voz":
                ch = MagicMock(spec=discord.VoiceChannel)
                ch.id, ch.name, ch.category = 5000 + i, nome, cats[cat]
            else:
                ch = canal_texto(1000 + i, nome, cats[cat])
            self.canais[chave] = ch
        g = MagicMock()
        g.id = cfg.guild_id
        g.channels = list(self.canais.values())
        g.me.id = 999
        self.g = g
        mock.patch.object(Nucleo, "guild", new_callable=mock.PropertyMock, return_value=g).start()
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(SV, "ids_do_configurador", return_value={}).start()

    def test_localizar_e_renderizar(self):
        self.assertIs(SV.localizar(self.g, "regras"), self.canais["regras"])
        self.assertIs(SV.localizar(self.g, "voz_bate_papo"), self.canais["voz_bate_papo"])
        txt = SV.renderizar("Leia {c:regras} e {c:inexistente}", self.g)
        self.assertIn(f"<#{self.canais['regras'].id}>", txt)
        self.assertIn("**#inexistente**", txt)

    def test_montar(self):
        embeds, arquivos, h = SV.montar("regras", self.g)
        self.assertEqual(len(embeds), 1 + len(K.MENSAGENS["regras"]))     # banner + blocos
        self.assertEqual(embeds[0].image.url, "attachment://canal_regras.png")
        self.assertEqual(arquivos[0].filename, "canal_regras.png")
        self.assertEqual(embeds[-1].footer.text, K.RODAPE)
        _, _, h2 = SV.montar("regras", self.g)
        self.assertEqual(h, h2)                                              # determinístico
        self.assertLessEqual(sum(len(e) for e in embeds), 6000)

    async def test_plano_publica_atualiza_e_remove_antigas(self):
        antiga = MagicMock(id=777, author=MagicMock(id=123, bot=True),
                           embeds=[discord.Embed(title="Bem-vindo ao Ghost Recon Brasil")])
        humano = MagicMock(id=778, author=MagicMock(id=5, bot=False), embeds=[])
        self.canais["boas_vindas"].history = MagicMock(return_value=_aiter([antiga, humano]))
        painel_velho = MagicMock(id=779, author=MagicMock(id=123, bot=True),
                                 embeds=[discord.Embed(title="Como falar com a equipe em privado")])
        self.canais["denuncias"].history = MagicMock(return_value=_aiter([painel_velho]))
        self.canais["chat_equipe"].permissions_for = lambda a: discord.Permissions(view_channel=False)

        p = await SV.planejar(MagicMock(), self.n)
        publicar = {i.chave for i in p.de("publicar")}
        self.assertIn("regras", publicar)
        self.assertNotIn("denuncias", publicar)                # painel, não mensagem
        self.assertEqual({(i.chave, i.msg_id) for i in p.de("apagar")}, {("boas_vindas", 777), ("denuncias", 779)})
        self.assertEqual([i.chave for i in p.de("sem_permissao")], ["chat_equipe"])

        problemas = await SV.executar(self.n, p)
        self.assertEqual(problemas, [])
        self.canais["regras"].send.assert_awaited()
        self.assertEqual(self.canais["boas_vindas"].parcial.delete.await_count, 1)
        salvo = self.n.db.mensagem_canal("regras")
        self.assertEqual(salvo["canal_id"], self.canais["regras"].id)

        # Rodando de novo: tudo em dia; mudando o texto: vira "atualizar"
        for ch in self.canais.values():
            if isinstance(ch, MagicMock) and hasattr(ch, "fetch_message"):
                ch.fetch_message = AsyncMock(return_value=MagicMock())
                ch.history = MagicMock(return_value=_aiter([]))
        p2 = await SV.planejar(MagicMock(), self.n)
        self.assertEqual(p2.de("publicar"), [])
        self.assertIn("regras", {i.chave for i in p2.de("ok")})
        with mock.patch.dict(K.MENSAGENS, {"duvidas": [{"titulo": "❓ Dúvidas", "texto": "Texto novo"}]}):
            p3 = await SV.planejar(MagicMock(), self.n)
        self.assertEqual([i.chave for i in p3.de("atualizar")], ["duvidas"])

    def test_resumo(self):
        p = SV.Plano([SV.Item("publicar", "regras", self.canais["regras"]), SV.Item("ok", "geral")])
        emb = SV.resumo_plano(p)
        self.assertIn("1", emb.description)
        self.assertIn("Publicar (1)", emb.fields[0].name)


class TestRelatorio(unittest.TestCase):
    def test_salvar(self):
        import tempfile
        checks = [SV.Checagem("ok", "A"), SV.Checagem("falha", "B", "detalhe | com barra")]
        with tempfile.TemporaryDirectory() as d:
            arq = SV.salvar_relatorio(checks, Path(d))
            txt = arq.read_text(encoding="utf-8")
        self.assertIn("❌ | B | detalhe / com barra", txt)
        emb = SV.embed_verificacao(checks)
        self.assertEqual(emb.color.value, 0xEF4444)


if __name__ == "__main__":
    unittest.main()


class TestInicializacao(unittest.IsolatedAsyncioTestCase):
    async def test_bot_carrega_todos_os_modulos(self):
        from bot.__main__ import OperacaoBrasil
        cfg = Config(token="a.b.c", guild_id=1, conteudo_mensagens=True, inatividade_dias=7, max_denuncias=1,
                     max_mods=2, banco=Path(":memory:"), web_ativo=False)
        bot = OperacaoBrasil(cfg)
        with mock.patch.object(bot.tree, "sync", AsyncMock(return_value=[])):
            await bot.setup_hook()
        self.assertEqual(set(bot.cogs), {"Tickets", "Squads", "Vip", "Servidor"})
        comandos = {c.name for c in bot.tree.get_commands(guild=discord.Object(1))}
        self.assertEqual(comandos, {"tickets", "squads", "servidor"})
        self.assertTrue(bot.intents.members and bot.intents.voice_states and bot.intents.message_content)
        self.assertFalse(discord.VoiceClient.warn_nacl)
        await bot.close()
