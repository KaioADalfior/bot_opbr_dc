"""Gera a matriz de permissões efetivas (docs/matriz-de-permissoes.md) usando o simulador."""
import sys, os, tempfile
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config, main
from gr_setup import discord_api, estrutura as E
from gr_setup.permissoes import P
from gr_setup.provisionador import Contexto, Estado
from gr_setup.validador import Validador
from tests.fake_discord import FakeDiscord, TOKEN

def gerar(destino: Path):
    fake = FakeDiscord(E.permissoes_necessarias_do_bot(), comunidade=True, taxa_429=0)
    tmp = Path(tempfile.mkdtemp())
    os.environ.update({"DISCORD_BOT_TOKEN": TOKEN, "DISCORD_GUILD_ID": fake.gid, "DISCORD_GUILD_NAME": "Ghost Recon Brasil"})
    real = discord_api.DiscordAPI
    with mock.patch.object(config, "PASTA_LOGS", tmp), mock.patch.object(config, "PASTA_RELATORIOS", tmp), \
         mock.patch.object(config, "PASTA_ESTADO", tmp), mock.patch("time.sleep", lambda *_: None), \
         mock.patch.object(main, "DiscordAPI", lambda t, **k: real(t, sessao=fake)):
        main.main(["aplicar", "--sim-confirmo"])
        api = real(TOKEN, sessao=fake)
        v = Validador(Contexto(api, fake.gid), Estado(tmp / f"estado-{fake.gid}.json", True))
    personas = [("Membro", ()), ("VIP", ("vip",)), ("Organizador", ("organizador",)),
                ("Moderador", ("moderador",)), ("Administração", ("administracao",))]
    def sig(e, voz):
        if not e & P.VIEW_CHANNEL: return "—"
        s = ["👁"]
        if voz:
            if e & P.CONNECT: s.append("🎙")
        else:
            if e & P.SEND_MESSAGES: s.append("✍")
            if e & P.CREATE_PUBLIC_THREADS: s.append("🧵")
            if e & P.MENTION_EVERYONE: s.append("📣")
        return "".join(s)
    linhas = ["# Matriz de permissões efetivas", "",
              "Gerada automaticamente por `tests/gerar_matriz.py` a partir da estrutura do projeto "
              "(cálculo oficial de permissões do Discord). Cada membro foi simulado com os cargos "
              "Membro + PC + Ghost Recon Breakpoint + Casual + Notificações de Eventos, mais o cargo da coluna.", "",
              "Legenda: — não vê · 👁 vê · ✍ envia mensagens · 🧵 cria threads · 📣 menciona @everyone/cargos · 🎙 conecta e fala.",
              "O Líder Fundador (com Administrador) e o dono do servidor têm acesso total.", "",
              "| Categoria | Canal | " + " | ".join(p for p, _ in personas) + " |",
              "|---|---|" + "---|" * len(personas)]
    for cat, canal in E.todos_os_canais():
        voz = canal.tipo == "voz"
        cols = [sig(v.efetivas(canal.chave, *x) or 0, voz) for _, x in personas]
        linhas.append(f"| {cat.nome} | {canal.nome} | " + " | ".join(cols) + " |")
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")

if __name__ == "__main__":
    gerar(Path(__file__).resolve().parents[1] / "docs" / "matriz-de-permissoes.md")
