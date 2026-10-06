"""Testes de ponta a ponta contra o simulador local da API.

Executar:  py -m unittest discover -s tests -v
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import config  # noqa: E402
import main  # noqa: E402
from gr_setup import discord_api, estrutura as E  # noqa: E402
from gr_setup.permissoes import P  # noqa: E402
from tests.fake_discord import TOKEN, FakeDiscord  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.patches = [
            mock.patch.object(config, "PASTA_LOGS", t / "logs"),
            mock.patch.object(config, "PASTA_RELATORIOS", t / "relatorios"),
            mock.patch.object(config, "PASTA_ESTADO", t / "estado"),
            mock.patch("time.sleep", lambda *_: None),
        ]
        for p in self.patches:
            p.start()
        self.fake = self.criar_fake()
        os.environ.update({"DISCORD_BOT_TOKEN": TOKEN, "DISCORD_GUILD_ID": self.fake.gid,
                           "DISCORD_GUILD_NAME": "Ghost Recon Brasil"})
        fake = self.fake
        real = discord_api.DiscordAPI
        self.p_api = mock.patch.object(main, "DiscordAPI", lambda token, **kw: real(token, sessao=fake))
        self.p_api.start()
        self.dir = t

    def criar_fake(self):
        return FakeDiscord(E.permissoes_necessarias_do_bot())

    def tearDown(self):
        self.p_api.stop()
        for p in self.patches:
            p.stop()
        config.fechar_log()
        self.tmp.cleanup()

    def run_cmd(self, *args):
        return main.main(list(args))

    def escritas(self):
        return [x for x in self.fake.log if x[0] != "GET"]

    def nossos_canais(self):
        return [c for c in self.fake.channels.values() if c["name"] not in
                ("Canais de texto", "geral", "Canais de voz", "Geral")]


class TestFluxoCompleto(Base):
    def test_fluxo(self):
        # 1. Verificação e simulação não alteram nada
        self.assertEqual(self.run_cmd("verificar"), 0)
        self.assertEqual(self.run_cmd("simular"), 0)
        self.assertEqual(self.escritas(), [], "simulação não pode escrever")

        # 2. Primeira execução real
        self.assertEqual(self.run_cmd("aplicar", "--sim-confirmo"), 0)
        cont = E.resumo_contagem()
        self.assertEqual(len(self.fake.roles), 2 + cont["cargos"])
        self.assertEqual(len(self.nossos_canais()), cont["total_canais"])
        # canais padrão do Discord intocados
        self.assertTrue(any(c["name"] == "geral" and c["type"] == 0 for c in self.fake.channels.values()))

        # 3. Segunda execução: idempotente (nenhuma criação/alteração)
        n_antes = len(self.fake.channels), len(self.fake.roles)
        self.fake.log.clear()
        self.assertEqual(self.run_cmd("aplicar", "--sim-confirmo"), 0)
        self.assertEqual((len(self.fake.channels), len(self.fake.roles)), n_antes)
        self.assertEqual(self.escritas(), [], f"2ª execução escreveu: {self.escritas()}")

        # 4. Validação estrutural e de permissões efetivas
        self.assertEqual(self.run_cmd("validar"), 0)

        # 5. Ativar Comunidade -> converte #anuncios para Anúncio
        self.fake.features = ["COMMUNITY", "NEWS"]
        self.assertEqual(self.run_cmd("aplicar", "--sim-confirmo"), 0)
        anuncios = [c for c in self.fake.channels.values() if c["name"] == "📢｜anúncios"]
        self.assertEqual(len(anuncios), 1)
        self.assertEqual(anuncios[0]["type"], 5)

        # 6. Mensagens: simulação, publicação e repetição sem duplicar
        self.fake.log.clear()
        self.assertEqual(self.run_cmd("mensagens", "--legado", "--simular"), 0)
        self.assertEqual(self.escritas(), [])
        self.assertEqual(self.run_cmd("mensagens", "--legado", "--sim-confirmo"), 0)
        total = sum(len(v) for v in self.fake.messages.values())
        self.assertGreater(total, 20)
        self.assertEqual(self.run_cmd("mensagens", "--legado", "--sim-confirmo"), 0)
        self.assertEqual(sum(len(v) for v in self.fake.messages.values()), total)
        self.assertTrue(self.fake.pins)

        # 7. Onboarding (rascunho) atende às regras do Discord
        self.assertEqual(self.run_cmd("onboarding", "--simular"), 0)
        self.assertEqual(self.run_cmd("onboarding"), 0)
        self.assertFalse(self.fake.onboarding_data["enabled"])
        self.assertEqual(len(self.fake.onboarding_data["prompts"]), 5)
        ids1 = [p["id"] for p in self.fake.onboarding_data["prompts"]]
        self.assertEqual(self.run_cmd("onboarding"), 0)
        self.assertEqual(ids1, [p["id"] for p in self.fake.onboarding_data["prompts"]])

        # 8. Deriva: alguém liberou envio em #anuncios -> aplicar corrige
        a = anuncios[0]
        for o in a["permission_overwrites"]:
            if o["id"] == self.fake.gid:
                o["allow"] = str(int(o["allow"]) | P.SEND_MESSAGES)
                o["deny"] = str(int(o["deny"]) & ~P.SEND_MESSAGES)
        self.assertEqual(self.run_cmd("validar"), 1, "validação deveria acusar a falha")
        self.assertEqual(self.run_cmd("aplicar", "--sim-confirmo"), 0)
        self.assertEqual(self.run_cmd("validar"), 0)

        # 9. Overwrite de terceiros é preservado ao corrigir
        estranho = {"id": "999", "type": 1, "allow": str(int(P.SEND_MESSAGES)), "deny": "0"}
        a["permission_overwrites"].append(estranho)
        a["topic"] = "alterado"
        self.assertEqual(self.run_cmd("aplicar", "--sim-confirmo"), 0)
        self.assertIn("999", [o["id"] for o in a["permission_overwrites"]])

        # 10. Nenhum token nos logs/relatórios
        for arq in self.dir.rglob("*"):
            if arq.is_file():
                self.assertNotIn(TOKEN, arq.read_text(encoding="utf-8"), arq.name)

        # 11. Nunca usou DELETE
        self.assertFalse([x for x in self.fake.log if x[0] == "DELETE"])


class TestPreexistentes(Base):
    def test_cargo_vip_preexistente_com_admin_nao_e_alterado(self):
        rid = "777000000000000001"
        self.fake.roles[rid] = {"id": rid, "name": "VIP", "position": 1, "permissions": str(int(P.ADMINISTRATOR)),
                                "managed": False, "color": 0, "hoist": False, "mentionable": False}
        self.fake.roles[self.fake.bot_role]["position"] = 2
        self.fake.roles[self.fake.bot_role]["permissions"] = str(E.permissoes_necessarias_do_bot())
        self.assertEqual(self.run_cmd("aplicar", "--sim-confirmo"), 0)
        self.assertEqual(self.fake.roles[rid]["permissions"], str(int(P.ADMINISTRATOR)))
        self.assertEqual(sum(1 for r in self.fake.roles.values() if r["name"] in ("VIP", "💎 VIP")), 1)
        self.assertEqual(self.run_cmd("validar"), 1, "validação deve acusar VIP com poderes")

    def test_adotar_existentes_corrige(self):
        rid = "777000000000000002"
        self.fake.roles[rid] = {"id": rid, "name": "PC", "position": 1, "permissions": str(int(P.KICK_MEMBERS)),
                                "managed": False, "color": 0, "hoist": False, "mentionable": False}
        self.fake.roles[self.fake.bot_role]["position"] = 2
        self.assertEqual(self.run_cmd("aplicar", "--sim-confirmo", "--adotar-existentes"), 0)
        self.assertEqual(self.fake.roles[rid]["permissions"], "0")


class TestBloqueios(Base):
    def criar_fake(self):
        return FakeDiscord(int(E.permissoes_necessarias_do_bot() & ~P.BAN_MEMBERS))

    def test_bot_sem_permissao_bloqueia(self):
        with self.assertRaises(SystemExit) as cm:
            self.run_cmd("aplicar", "--sim-confirmo")
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(self.escritas(), [])

    def test_servidor_errado_bloqueia(self):
        os.environ["DISCORD_GUILD_ID"] = "123456789012345678"
        with self.assertRaises(SystemExit) as cm:
            self.run_cmd("verificar")
        self.assertEqual(cm.exception.code, 2)

    def test_nome_divergente_bloqueia(self):
        os.environ["DISCORD_GUILD_NAME"] = "Outro Servidor"
        self.fake.roles[self.fake.bot_role]["permissions"] = str(E.permissoes_necessarias_do_bot())
        with self.assertRaises(SystemExit) as cm:
            self.run_cmd("aplicar", "--sim-confirmo")
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(self.escritas(), [])


class TestOutroBot(Base):
    def test_nao_duplica_mensagens_de_bot_anterior(self):
        self.fake.features = ["COMMUNITY", "NEWS"]
        self.assertEqual(self.run_cmd("aplicar", "--sim-confirmo"), 0)
        cid = next(c["id"] for c in self.fake.channels.values() if c["name"] == "📜｜regras")
        self.fake.messages[cid].append({"id": "1", "author": {"id": "555", "bot": True}, "content": "", "embeds": []})
        self.assertEqual(self.run_cmd("mensagens", "--legado", "--sim-confirmo"), 0)
        self.assertEqual(len(self.fake.messages[cid]), 1, "não deve publicar onde outro bot já publicou")
        self.assertEqual(self.run_cmd("mensagens", "--legado", "--sim-confirmo", "--forcar"), 0)
        from gr_setup.mensagens import MENSAGENS
        self.assertEqual(len(self.fake.messages[cid]), 1 + len(MENSAGENS["regras"]))


class TestRenomearEEditar(Base):
    def test_renomeia_gerenciados_e_edita_mensagens(self):
        from gr_setup import mensagens as M
        self.fake.features = ["COMMUNITY", "NEWS"]
        self.assertEqual(self.run_cmd("aplicar", "--sim-confirmo"), 0)
        # Nome antigo em um canal gerenciado -> aplicar renomeia
        regras = next(c for c in self.fake.channels.values() if c["name"] == "📜｜regras")
        regras["name"] = "📜・regras"
        cargo = next(r for r in self.fake.roles.values() if r["name"] == "❯ Soldado")
        cargo["name"] = "Soldado"
        self.assertEqual(self.run_cmd("aplicar", "--sim-confirmo"), 0)
        self.assertEqual(regras["name"], "📜｜regras")
        self.assertEqual(cargo["name"], "❯ Soldado")
        # Publica só 2 das 4 mensagens de regras; depois sincroniza: posta as que faltam
        originais = list(M.MENSAGENS["regras"])
        with mock.patch.dict(M.MENSAGENS, {"regras": originais[:2]}):
            self.assertEqual(self.run_cmd("mensagens", "--legado", "--sim-confirmo"), 0)
        self.assertEqual(len(self.fake.messages[regras["id"]]), 2)
        self.fake.messages[regras["id"]][0]["embeds"][0]["description"] = "texto antigo"
        self.assertEqual(self.run_cmd("mensagens", "--legado", "--sim-confirmo"), 0)
        msgs = self.fake.messages[regras["id"]]
        self.assertEqual(len(msgs), 4, "deve editar as existentes e publicar só as que faltam")
        self.assertNotEqual(msgs[0]["embeds"][0]["description"], "texto antigo")
        self.assertIn("<#", msgs[2]["embeds"][0]["description"], "menção clicável ao canal de voz")
        n = len(self.fake.log)
        self.assertEqual(self.run_cmd("mensagens", "--legado", "--sim-confirmo"), 0)
        self.assertFalse([x for x in self.fake.log[n:] if x[0] != "GET"], "3ª execução não escreve")


if __name__ == "__main__":
    unittest.main()
