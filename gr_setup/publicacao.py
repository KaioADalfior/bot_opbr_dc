"""Publicação das mensagens iniciais e (opcional) do rascunho de Onboarding."""
from __future__ import annotations

import logging
import time

from . import estrutura as E
from .discord_api import DiscordAPI, ErroAPI
from .mensagens import embeds_de
from .provisionador import Resultado
from .validador import Resolucao

log = logging.getLogger("gr_setup")


def _normalizar(txt: str | None) -> str:
    return " ".join((txt or "").split())


def publicar_mensagens(api: DiscordAPI, res: Resolucao, estado, simular: bool,
                       forcar: bool = False) -> Resultado:
    r = Resultado()
    log.info("\n== Mensagens iniciais ==")
    for _cat, canal in E.todos_os_canais():
        if not canal.mensagem:
            continue
        ch = res.canais.get(canal.chave)
        if ch is None:
            r.falhas.append(f"Canal '{canal.nome}' não encontrado; execute 'aplicar' antes.")
            continue
        try:
            historico = api.mensagens(ch["id"], 100)
        except ErroAPI as e:
            r.falhas.append(f"Ler histórico de '{canal.nome}': {e}")
            continue
        ja_publicadas = {_normalizar(e.get("description")) for m in historico for e in m.get("embeds", [])}
        # Sem a intent "Message Content", um bot não enxerga embeds de OUTRO bot. Se outro bot
        # (ex.: um bot de configuração anterior) já publicou aqui, não arriscamos duplicar.
        outros = [m for m in historico if (m.get("author") or {}).get("bot")
                  and m["author"]["id"] != res.ctx.bot["id"] and not m.get("embeds")]
        if outros and not forcar:
            r.avisos.append(f"'{canal.nome}': há mensagens de outro bot que não podem ser comparadas; "
                            f"canal ignorado (use --forcar para publicar mesmo assim).")
            continue
        ids = {k: c["id"] for k, c in res.canais.items()}
        por_id = {m["id"]: m for m in historico}
        rastreadas = [por_id[mid] for mid in estado.dados["mensagens"].get(canal.chave, [])
                      if mid in por_id and por_id[mid]["author"]["id"] == res.ctx.bot["id"]]
        for i, emb in enumerate(embeds_de(canal.mensagem, ids)):
            desc = f"Mensagem '{emb['title']}' em '{canal.nome}'"
            if i < len(rastreadas):
                atual = (rastreadas[i].get("embeds") or [{}])[0]
                if (_normalizar(atual.get("description")) == _normalizar(emb["description"])
                        and (atual.get("title") or "") == emb["title"]):
                    r.existentes.append(desc)
                    log.info("  = já publicada: %s", desc)
                    continue
                if simular:
                    r.corrigidos.append(desc + " (simulação: seria editada)")
                    log.info("  [SIMULAÇÃO] editaria %s", desc)
                    continue
                try:
                    api.patch(f"/channels/{ch['id']}/messages/{rastreadas[i]['id']}",
                              {"embeds": [emb], "allowed_mentions": {"parse": []}})
                    r.corrigidos.append(desc + " (editada)")
                    log.info("  ~ editada: %s", desc)
                except ErroAPI as e:
                    r.falhas.append(f"Editar {desc}: {e}")
                    log.error("  FALHA: %s: %s", desc, e)
                continue
            if _normalizar(emb["description"]) in ja_publicadas:
                r.existentes.append(desc)
                log.info("  = já publicada: %s", desc)
                continue
            if simular:
                r.criados.append(desc + " (simulação)")
                log.info("  [SIMULAÇÃO] publicaria %s", desc)
                continue
            try:
                msg = api.post(f"/channels/{ch['id']}/messages",
                               {"embeds": [emb], "allowed_mentions": {"parse": []}})
                estado.dados["mensagens"].setdefault(canal.chave, []).append(msg["id"])
                estado.salvar()
                r.criados.append(desc)
                log.info("  + publicada: %s", desc)
                if canal.fixar_mensagem and i == 0:
                    _fixar(api, ch["id"], msg["id"], desc, r)
            except ErroAPI as e:
                r.falhas.append(f"{desc}: {e}")
                log.error("  FALHA: %s: %s", desc, e)
    return r


def _fixar(api, cid, mid, desc, r):
    try:
        api.put(f"/channels/{cid}/messages/pins/{mid}")
    except ErroAPI as e:
        if e.status != 404:
            r.avisos.append(f"Não foi possível fixar {desc}: {e}")
            return
        try:  # rota antiga, ainda aceita em algumas versões
            api.put(f"/channels/{cid}/pins/{mid}")
        except ErroAPI as e2:
            r.avisos.append(f"Não foi possível fixar {desc}: {e2}")
            return
    r.corrigidos.append(f"Fixada: {desc}")


# ---------------------------------------------------------------------------
# Onboarding (opcional). Grava como RASCUNHO desativado por padrão: você revisa
# e ativa no aplicativo (Configurações do Servidor > Onboarding).
# ---------------------------------------------------------------------------
CANAIS_PADRAO = ["anuncios", "boas_vindas", "regras", "comece_aqui", "geral", "abrir_squad", "squad_partida",
                 "squad_raid", "duvidas", "suporte_geral", "suporte_dicas", "denuncias", "clips"]

PERGUNTAS = [
    {"titulo": "Quais jogos você joga?", "unica": False, "obrigatoria": True, "opcoes": [
        ("Ghost Recon Wildlands", "Campanha, exploração e cooperativo", "🌿", ["jogo_wildlands"],
         ["chat_wildlands", "voz_wildlands"]),
        ("Ghost Recon Breakpoint", "Missões, raids e cooperativo", "💀", ["jogo_breakpoint"],
         ["chat_breakpoint", "raid_semanal", "voz_breakpoint"]),
        ("Rainbow Six Siege", "Partidas em esquadrão", "👮", ["jogo_r6"],
         ["radio_1", "radio_2", "radio_3", "radio_4"]),
    ]},
    {"titulo": "Em qual plataforma você joga?", "unica": False, "obrigatoria": True, "opcoes": [
        ("PC", None, "💻", ["plat_pc"], []),
        ("Xbox", None, "🟩", ["plat_xbox"], []),
        ("PlayStation", None, "🟦", ["plat_ps"], []),
    ]},
    {"titulo": "Qual é o seu estilo de jogo?", "unica": True, "obrigatoria": False, "opcoes": [
        ("Casual", "Jogo pela diversão, sem pressão", "🙂", ["estilo_casual"], []),
        ("Furtivo", "Infiltração e silêncio", "🌑", ["estilo_furtivo"], []),
        ("Tático", "Planejamento e coordenação", "🎯", ["estilo_tatico"], []),
        ("Livre", "Um pouco de tudo", "🌎", ["estilo_livre"], []),
    ]},
    {"titulo": "Quer receber avisos?", "unica": False, "obrigatoria": False, "opcoes": [
        ("Eventos", "Avisos de eventos da comunidade", "📅", ["notif_eventos"], []),
        ("Operações", "Avisos de raids e operações", "📡", ["notif_operacoes"], ["raid_semanal"]),
    ]},
    {"titulo": "O que mais te interessa?", "unica": False, "obrigatoria": False, "opcoes": [
        ("Mods", "Modificações de Wildlands e Breakpoint", "🧩", [],
         ["mods_publicados", "discussao_mods", "regras_mods", "publicar_mod"]),
        ("Clips e lives", "Destaques e transmissões da comunidade", "🎬", [], ["clips", "lives"]),
        ("Memes e outfits", "Imagens, memes e personalizações", "😂", [], ["fotos_memes", "outfits"]),
        ("Apoiar a comunidade", "Área VIP e sugestões", "💎", [], ["vips", "sugestoes"]),
    ]},
]


def _snowflake(seq: int) -> str:
    return str(((int(time.time() * 1000) - 1420070400000) << 22) + seq)


def montar_onboarding(res: Resolucao, atual: dict | None, ativar: bool) -> tuple[dict, list[str]]:
    faltas = []
    ids_existentes = {}
    for p in (atual or {}).get("prompts", []):
        ids_existentes[p["title"]] = (p["id"], {o["title"]: o["id"] for o in p.get("options", [])})
    seq = 0
    prompts = []
    for p in PERGUNTAS:
        pid, opc_ids = ids_existentes.get(p["titulo"], (None, {}))
        if pid is None:
            seq += 1
            pid = _snowflake(seq)
        opcoes = []
        for titulo, desc, emoji, cargos, canais in p["opcoes"]:
            oid = opc_ids.get(titulo)
            if oid is None:
                seq += 1
                oid = _snowflake(seq)
            role_ids = [res.cargos[k]["id"] for k in cargos if k in res.cargos]
            channel_ids = [res.canais[k]["id"] for k in canais if k in res.canais]
            faltas += [f"cargo {k}" for k in cargos if k not in res.cargos]
            faltas += [f"canal {k}" for k in canais if k not in res.canais]
            opcoes.append({"id": oid, "title": titulo, "description": desc, "emoji_name": emoji.replace("\ufe0f", ""),
                           "role_ids": role_ids, "channel_ids": channel_ids})
        prompts.append({"id": pid, "type": 0, "title": p["titulo"], "single_select": p["unica"],
                        "required": p["obrigatoria"], "in_onboarding": True, "options": opcoes})
    padrao = [res.canais[k]["id"] for k in CANAIS_PADRAO if k in res.canais]
    faltas += [f"canal padrão {k}" for k in CANAIS_PADRAO if k not in res.canais]
    corpo = {"prompts": prompts, "default_channel_ids": padrao, "enabled": ativar, "mode": 0}
    return corpo, faltas
