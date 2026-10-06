"""Testes do bot Operação Brasil (regras, banco e fluxos dos tickets com Discord simulado)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import discord  # noqa: E402

from bot import regras  # noqa: E402
from bot.cogs import tickets as T  # noqa: E402
from bot.config import Config  # noqa: E402
from bot.db import Banco  # noqa: E402
from bot.nucleo import Nucleo  # noqa: E402


class TestRegras(unittest.TestCase):
    def test_links(self):
        ok = regras.analisar_link("https://www.nexusmods.com/ghostreconbreakpoint/mods/123?utm_source=x")
        self.assertTrue(ok.valido and not ok.bloqueado)
        self.assertEqual(ok.normalizado, "https://nexusmods.com/ghostreconbreakpoint/mods/123")
        self.assertFalse(regras.analisar_link("http://nexusmods.com/x").valido)
        self.assertTrue(regras.analisar_link("https://bit.ly/abc").bloqueado)
        self.assertTrue(regras.analisar_link("https://site.com/mod.exe").bloqueado)
        self.assertTrue(regras.analisar_link("https://1.2.3.4/mod").bloqueado)
        m = regras.analisar_link("https://www.mediafire.com/file/abc/mod.zip")
        self.assertTrue(m.valido and not m.bloqueado and m.alertas)

    def test_transicoes(self):
        V = regras.verificar_acao
        self.assertEqual(V("aprovar", "mod", "aberto", 1, 2, True), "aprovado")
        with self.assertRaises(regras.AcaoNegada):
            V("aprovar", "mod", "aberto", 1, 1, True)          # autoaprovação
        with self.assertRaises(regras.AcaoNegada):
            V("aprovar", "mod", "aberto", 1, 2, False)         # não é equipe
        with self.assertRaises(regras.AcaoNegada):
            V("aprovar", "mod", "aprovado", 1, 2, True)        # já aprovado
        with self.assertRaises(regras.AcaoNegada):
            V("aprovar", "denuncia", "aberto", 1, 2, True)     # tipo errado
        self.assertEqual(V("reabrir", "denuncia", "encerrado", 1, 1, True), "aberto")

    def test_nomes(self):
        self.assertEqual(regras.slug("👑 Líder Fundador"), "líder fundador")
        self.assertEqual(regras.slug("🚨｜denúncias"), "denúncias")
        self.assertEqual(regras.nome_canal_ticket("mod", 7, "Realismo Total!"), "mod-0007-realismo-total")


class TestBanco(unittest.TestCase):
    def test_fluxo(self):
        b = Banco(":memory:")
        tid = b.criar_ticket("mod", 10, {"nome": "X"}, "https://a.com/x", "breakpoint:x")
        self.assertEqual(len(b.ativos_do_autor(10, "mod")), 1)
        self.assertIsNotNone(b.duplicado_mod("https://a.com/x", "outro"))
        self.assertTrue(b.mudar_status(tid, {"aberto"}, "aprovado"))
        self.assertFalse(b.mudar_status(tid, {"aberto"}, "aprovado"), "segunda aprovação deve falhar")
        self.assertIsNotNone(b.duplicado_mod("https://a.com/x", "outro"), "aprovado continua bloqueando duplicata")
        b.registrar(tid, 99, "Mod aprovado")
        self.assertEqual(b.historico(tid)[0]["acao"], "Mod aprovado")


def membro(uid, equipe=False):
    m = MagicMock(spec=discord.Member)
    m.id = uid
    m.mention = f"<@{uid}>"
    m.guild_permissions.administrator = False
    m.guild.owner_id = 1
    m.roles = [MagicMock(id=500)] if equipe else []
    m.send = AsyncMock()
    return m


class TestFluxoTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        cfg = Config(token="a.b.c", guild_id=123456789012345678, conteudo_mensagens=True, inatividade_dias=7,
                     max_denuncias=1, max_mods=2, banco=Path(":memory:"))
        self.bot = MagicMock()
        self.n = Nucleo(self.bot, cfg, Banco(":memory:"))
        T.NUCLEO = self.n
        self.canal_ticket = MagicMock(spec=discord.TextChannel)
        self.canal_ticket.id = 777
        self.canal_ticket.mention = "<#777>"
        self.canal_ticket.send = AsyncMock(return_value=MagicMock(id=888))
        self.canal_ticket.set_permissions = AsyncMock()
        self.canal_ticket.fetch_message = AsyncMock(return_value=MagicMock(edit=AsyncMock()))
        self.publicados = MagicMock(spec=discord.TextChannel)
        self.publicados.send = AsyncMock(return_value=MagicMock(id=999))
        self.relatorios = MagicMock(spec=discord.TextChannel)
        self.relatorios.send = AsyncMock()
        g = MagicMock()
        g.get_channel = lambda cid: self.canal_ticket if cid == 777 else None
        g.create_text_channel = AsyncMock(return_value=self.canal_ticket)
        self.guild = g
        canais = {"mods_publicados": self.publicados, "relatorios": self.relatorios, "logs": None}
        mock.patch.object(Nucleo, "guild", new_callable=mock.PropertyMock, return_value=g).start()
        self.n.canal = lambda chave: canais.get(chave)
        self.n.cargos_equipe = lambda: [MagicMock(id=500)]
        self.n.categoria_tickets = AsyncMock(return_value=MagicMock())
        self.n.membro = AsyncMock(side_effect=lambda uid: membro(uid))
        self.n.transcricao = AsyncMock(return_value=MagicMock())
        self.canal_ticket.delete = AsyncMock()
        self.p_tr = mock.patch("bot.transcript.gerar", AsyncMock(return_value=(b"<html></html>", "ABCD-EFGH-JKLM-NPQR")))
        self.p_tr.start()
        self.addCleanup(mock.patch.stopall)

    def interacao(self, user):
        it = MagicMock()
        it.user = user
        it.response.send_message = AsyncMock()
        it.response.defer = AsyncMock()
        it.response.send_modal = AsyncMock()
        it.followup.send = AsyncMock()
        return it

    async def enviar_mod(self, autor, link="https://www.nexusmods.com/ghostreconbreakpoint/mods/1", nome="Mod A"):
        modal = T.ModalMod({"jogo": "breakpoint", "plataformas": ["pc"], "categoria": "gameplay"})
        for campo, valor in (("nome", nome), ("versao", "v1"), ("link", link),
                             ("creditos", "Autor X"), ("descricao", "Descrição longa o suficiente aqui.")):
            getattr(modal, campo)._value = valor
        it = self.interacao(autor)
        await modal.on_submit(it)
        return it

    async def test_envio_aprovacao_e_regras(self):
        autor, mod1, mod2 = membro(10), membro(20, equipe=True), membro(30, equipe=True)
        it = await self.enviar_mod(autor)
        self.assertIn("Envio recebido", it.followup.send.call_args.args[0])
        tid = 1
        self.assertEqual(self.n.db.ticket(tid)["canal_id"], 777)

        # Duplicata é recusada
        it = await self.enviar_mod(membro(11))
        self.assertIn("já foi enviado", it.response.send_message.call_args.args[0])
        # Encurtador é recusado
        it = await self.enviar_mod(membro(12), link="https://bit.ly/xyz", nome="Outro")
        self.assertIn("recusado", it.response.send_message.call_args.args[0])

        # Membro comum não aprova
        it = self.interacao(membro(40))
        await T.executar_acao(it, tid, "aprovar")
        self.assertIn("Somente a equipe", it.followup.send.call_args.args[0])
        # Autor (mesmo sendo equipe) não aprova o próprio envio
        autor_equipe = membro(10, equipe=True)
        it = self.interacao(autor_equipe)
        await T.executar_acao(it, tid, "aprovar")
        self.assertIn("próprio envio", it.followup.send.call_args.args[0])
        # Equipe aprova -> publica uma vez
        it = self.interacao(mod1)
        await T.executar_acao(it, tid, "aprovar")
        self.assertEqual(self.n.db.ticket(tid)["status"], regras.APROVADO)
        self.assertEqual(self.publicados.send.await_count, 1)
        self.relatorios.send.assert_awaited()  # transcrição
        # Segunda aprovação não publica de novo
        it = self.interacao(mod2)
        await T.executar_acao(it, tid, "aprovar")
        self.assertEqual(self.publicados.send.await_count, 1)
        hist = [h["acao"] for h in self.n.db.historico(tid)]
        self.assertIn("Mod aprovado", hist)

    async def test_falha_ao_publicar_desfaz(self):
        await self.enviar_mod(membro(10))
        self.publicados.send = AsyncMock(side_effect=discord.HTTPException(MagicMock(status=403), "sem acesso"))
        it = self.interacao(membro(20, equipe=True))
        await T.executar_acao(it, 1, "aprovar")
        self.assertEqual(self.n.db.ticket(1)["status"], regras.ABERTO)

    async def test_denuncia_limite_e_encerrar_reabrir(self):
        autor = membro(10)
        modal = T.ModalDenuncia()
        for campo, valor in (("assunto", "Ofensas"), ("relato", "Fulano me ofendeu na call."),
                             ("envolvidos", ""), ("provas", "")):
            getattr(modal, campo)._value = valor
        it = self.interacao(autor)
        await modal.on_submit(it)
        self.assertIn("Atendimento aberto", it.followup.send.call_args.args[0])
        it = self.interacao(autor)
        await modal.on_submit(it)
        self.assertIn("já tem um atendimento", it.response.send_message.call_args.args[0])
        eq = membro(20, equipe=True)
        await T.executar_acao(self.interacao(eq), 1, "encerrar")
        self.assertEqual(self.n.db.ticket(1)["status"], regras.ENCERRADO)
        self.canal_ticket.delete.assert_awaited()                       # canal apagado
        self.assertIsNone(self.n.db.ticket(1)["canal_id"])
        rel_kwargs = self.relatorios.send.call_args.kwargs                # equipe recebe arquivo + senha
        self.assertIn("ABCD-EFGH-JKLM-NPQR", rel_kwargs["embed"].fields[0].value)
        self.assertTrue(rel_kwargs["file"].filename.endswith(".html"))
        criados = self.guild.create_text_channel.await_count
        # com servidor web: DM traz botão de link e nenhum arquivo
        web = MagicMock()
        web.salvar.return_value = "tok_tok_tok_tok_tok_tok_tok"
        web.link.return_value = "https://exemplo.trycloudflare.com/t/tok_tok_tok_tok_tok_tok_tok"
        self.n.web = web
        await T.executar_acao(self.interacao(eq), 1, "reabrir")
        self.assertEqual(self.n.db.ticket(1)["status"], regras.ABERTO)
        self.assertEqual(self.guild.create_text_channel.await_count, criados + 1)  # canal recriado

    async def test_dm_com_link(self):
        autor = membro(10)
        self.n.membro = AsyncMock(return_value=autor)
        web = MagicMock()
        web.salvar.return_value = "tok_tok_tok_tok_tok_tok_tok"
        web.link.return_value = "https://exemplo.trycloudflare.com/t/tok_tok_tok_tok_tok_tok_tok"
        self.n.web = web
        modal = T.ModalDenuncia()
        for campo, valor in (("assunto", "Teste"), ("relato", "Relato de teste longo."), ("envolvidos", ""),
                             ("provas", "")):
            getattr(modal, campo)._value = valor
        await modal.on_submit(self.interacao(autor))
        await T.executar_acao(self.interacao(membro(20, equipe=True)), 1, "encerrar")
        kw = autor.send.call_args.kwargs
        self.assertNotIn("file", kw)
        botao = kw["view"].children[0]
        self.assertEqual(botao.url, web.link.return_value)
        self.assertIn("ABCD-EFGH-JKLM-NPQR", kw["embed"].fields[0].value)
        self.assertEqual(self.n.db.ticket(1)["dados"]["transcript_token"], "tok_tok_tok_tok_tok_tok_tok")

    async def test_links_atualizados_apos_reinicio(self):
        autor = membro(10)
        autor.send = AsyncMock(return_value=MagicMock(id=5001, channel=MagicMock(id=4001)))
        self.relatorios.send = AsyncMock(return_value=MagicMock(id=5002, channel=MagicMock(id=4002)))
        self.n.membro = AsyncMock(return_value=autor)
        tok = "tok_tok_tok_tok_tok_tok_tok"
        web = MagicMock()
        web.salvar.return_value = tok
        web.url_publica = "https://antigo.trycloudflare.com"
        web.link.side_effect = lambda t: f"{web.url_publica}/t/{t}"
        web.existe.return_value = True
        self.n.web = web
        modal = T.ModalDenuncia()
        for campo, valor in (("assunto", "Teste"), ("relato", "Relato de teste longo."), ("envolvidos", ""),
                             ("provas", "")):
            getattr(modal, campo)._value = valor
        await modal.on_submit(self.interacao(autor))
        await T.executar_acao(self.interacao(membro(20, equipe=True)), 1, "encerrar")
        d = self.n.db.ticket(1)["dados"]
        self.assertEqual(d["transcript_msgs"], [[4002, 5002], [4001, 5001]])
        self.assertNotIn("file", self.relatorios.send.call_args.kwargs)  # com link: sem arquivo

        cog = T.Tickets(self.bot, self.n)
        self.assertEqual(await cog.atualizar_links_transcript(), 0)  # mesmo endereço: nada a fazer
        web.url_publica = "https://novo.trycloudflare.com"          # bot reiniciou
        editadas = []
        def parcial(cid):
            pm = MagicMock()
            def msg(mid):
                m = MagicMock()
                async def edit(view):
                    editadas.append((cid, mid, view.children[0].url))
                m.edit = edit
                return m
            pm.get_partial_message = msg
            return pm
        self.bot.get_partial_messageable = parcial
        self.assertEqual(await cog.atualizar_links_transcript(), 2)
        self.assertTrue(all(u == f"https://novo.trycloudflare.com/t/{tok}" for _, _, u in editadas))
        self.assertEqual(self.n.db.ticket(1)["dados"]["transcript_url"], f"https://novo.trycloudflare.com/t/{tok}")

    def test_view_e_ids(self):
        t = {"id": 5, "tipo": "mod", "status": regras.REJEITADO, "dados": {}, "autor_id": 1}
        v = T.montar_view(t)
        ids = {i.item.custom_id: i.item.disabled for i in v.children}
        self.assertFalse(ids["grb:t:reabrir:5"])
        self.assertTrue(ids["grb:t:aprovar:5"])
        self.assertEqual(len(T.view_painel("mod").children), 1)


    async def test_assistente_selecao(self):
        a = T.AssistenteMod(10)
        self.assertTrue(a.btn_continuar.disabled)
        it = self.interacao(membro(10))
        it.response.edit_message = AsyncMock()
        a.sel_jogo._values = ["wildlands"]
        await a._jogo(it)
        a.sel_plat._values = ["ps", "pc"]
        await a._plat(it)
        self.assertEqual(a.esc["plataformas"], ["pc", "ps"])
        self.assertFalse(a.btn_continuar.disabled)
        emb = it.response.edit_message.call_args.kwargs["embed"]
        self.assertIn("Wildlands", emb.fields[0].value)
        it2 = self.interacao(membro(10))
        await a._continuar(it2)
        modal = it2.response.send_modal.call_args.args[0]
        self.assertIsInstance(modal, T.ModalMod)
        self.assertIn("Wildlands", modal.title)

    def test_painel_mod(self):
        emb = T.embed_painel("mod", None)
        self.assertIn("Central de envio", emb.title)
        v = T.view_painel("mod", "https://discord.com/channels/1/2")
        self.assertEqual(len(v.children), 2)



class TestTranscript(unittest.TestCase):
    def test_criptografia_e_modelo(self):
        from bot import transcript as TR
        senha = TR.gerar_senha()
        self.assertRegex(senha, r"^[A-Z2-9]{4}(-[A-Z2-9]{4}){3}$")
        dados = {"cabecalho": {"titulo": "Atendimento #0001"}, "pessoas": {}, "mensagens": [{"texto": "olá"}]}
        pacote = TR.criptografar(dados, senha)
        self.assertEqual(TR.descriptografar(pacote, senha), dados)
        with self.assertRaises(Exception):
            TR.descriptografar(pacote, "ERRA-DAAA-AAAA-AAAA")
        html = TR.montar_html(1, pacote)
        self.assertIn("Transcript protegido #0001", html)
        self.assertNotIn("__PACOTE__", html)
        self.assertNotIn("olá", html, "conteúdo não pode aparecer em texto claro")



class TestServidorWeb(unittest.IsolatedAsyncioTestCase):
    async def test_publica_e_protege(self):
        import os
        import tempfile
        import time
        import aiohttp
        from bot.web import ServidorTranscripts
        pasta = Path(tempfile.mkdtemp())
        srv = ServidorTranscripts(pasta, "127.0.0.1", 18765, url_publica="https://exemplo.trycloudflare.com",
                                  tunel="", validade_dias=30)
        await srv.iniciar()
        try:
            token = srv.salvar(b"<html>ok</html>")
            self.assertEqual(srv.link(token), f"https://exemplo.trycloudflare.com/t/{token}")
            async with aiohttp.ClientSession() as s:
                async with s.get(f"http://127.0.0.1:18765/t/{token}") as r:
                    self.assertEqual(r.status, 200)
                    self.assertIn("frame-ancestors 'none'", r.headers["Content-Security-Policy"])
                    self.assertEqual(await r.text(), "<html>ok</html>")
                async with s.get("http://127.0.0.1:18765/t/../../config.py") as r:
                    self.assertEqual(r.status, 404)
                async with s.get("http://127.0.0.1:18765/t/naoexiste_naoexiste_naoexiste") as r:
                    self.assertEqual(r.status, 404)
                velho = time.time() - 40 * 86400
                os.utime(pasta / f"{token}.html", (velho, velho))
                async with s.get(f"http://127.0.0.1:18765/t/{token}") as r:
                    self.assertEqual(r.status, 410)
            self.assertEqual(srv.limpar_expirados(), 1)
        finally:
            await srv.parar()


if __name__ == "__main__":
    unittest.main()
