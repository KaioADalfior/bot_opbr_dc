"""Catálogo de jogos, plataformas e categorias usados no envio de mods."""
from __future__ import annotations

JOGOS = {
    "wildlands": {"nome": "Ghost Recon Wildlands", "curto": "Wildlands", "emoji": "🌿",
                  "descricao": "Bolívia • lançado em 2017", "cor": 0x65A30D},
    "breakpoint": {"nome": "Ghost Recon Breakpoint", "curto": "Breakpoint", "emoji": "💀",
                   "descricao": "Arquipélago de Auroa • lançado em 2019", "cor": 0x38BDF8},
}

PLATAFORMAS = {
    "pc": {"nome": "PC", "emoji": "🖥️", "descricao": "Ubisoft Connect, Steam ou Epic"},
    "xbox": {"nome": "Xbox", "emoji": "🟩", "descricao": "Só se o mod for compatível com console"},
    "ps": {"nome": "PlayStation", "emoji": "🟦", "descricao": "Só se o mod for compatível com console"},
}

CATEGORIAS = {
    "graficos": {"nome": "Gráficos / ReShade", "emoji": "🎨", "descricao": "Iluminação, cores, filtros, clima"},
    "gameplay": {"nome": "Gameplay / Realismo", "emoji": "🎯", "descricao": "IA, dano, balística, dificuldade"},
    "armas": {"nome": "Armas e equipamentos", "emoji": "🔫", "descricao": "Armas, acessórios, gadgets"},
    "visual": {"nome": "Visual / Outfits", "emoji": "👕", "descricao": "Roupas, personagens, camuflagens"},
    "interface": {"nome": "Interface / HUD", "emoji": "🧭", "descricao": "HUD, mapa, menus, mira"},
    "audio": {"nome": "Áudio", "emoji": "🔊", "descricao": "Sons de armas, rádio, ambiente"},
    "mundo": {"nome": "Mundo / Missões", "emoji": "🗺️", "descricao": "Mapas, missões, eventos, veículos"},
    "utilitario": {"nome": "Utilitário / Outros", "emoji": "🧰", "descricao": "Ferramentas, correções, diversos"},
}


def rotulo_jogo(chave: str | None) -> str:
    j = JOGOS.get(chave or "")
    return f"{j['emoji']} {j['nome']}" if j else "—"


def rotulo_plataformas(chaves: list[str] | None) -> str:
    itens = [f"{PLATAFORMAS[c]['emoji']} {PLATAFORMAS[c]['nome']}" for c in (chaves or []) if c in PLATAFORMAS]
    return " · ".join(itens) or "—"


def rotulo_categoria(chave: str | None) -> str:
    c = CATEGORIAS.get(chave or "")
    return f"{c['emoji']} {c['nome']}" if c else "—"


def cor_jogo(chave: str | None, padrao: int = 0x38BDF8) -> int:
    return JOGOS.get(chave or "", {}).get("cor", padrao)


# ---------------------------------------------------------------------------
# Squads (#squad-partida)
# ---------------------------------------------------------------------------
JOGOS_SQUAD = {
    "breakpoint": {"nome": "Ghost Recon Breakpoint", "curto": "Breakpoint", "emoji": "💀", "vagas": 4,
                   "descricao": "Auroa • esquadrão de até 4", "cor": 0x38BDF8},
    "wildlands": {"nome": "Ghost Recon Wildlands", "curto": "Wildlands", "emoji": "🌿", "vagas": 4,
                  "descricao": "Bolívia • esquadrão de até 4", "cor": 0x65A30D},
    "r6": {"nome": "Rainbow Six Siege", "curto": "Siege", "emoji": "👮", "vagas": 5,
           "descricao": "Time de até 5", "cor": 0x3B82F6},
}

PLATAFORMAS_SQUAD = {
    "pc": {"nome": "PC", "emoji": "🖥️", "descricao": "Ubisoft Connect, Steam ou Epic"},
    "xbox": {"nome": "Xbox", "emoji": "🟩", "descricao": "Xbox One / Series X|S"},
    "ps": {"nome": "PlayStation", "emoji": "🟦", "descricao": "PS4 / PS5"},
}

_MODOS_GR_COMUNS = {
    "campanha": {"nome": "Campanha cooperativa", "emoji": "🗺️", "descricao": "Missões da história em grupo"},
    "exploracao": {"nome": "Exploração / Farm", "emoji": "🧭", "descricao": "Free roam, loot, bases, colecionáveis"},
    "tatico": {"nome": "Operação tática / Roleplay", "emoji": "🎯", "descricao": "Infiltração planejada, sem HUD"},
    "pvp": {"nome": "Ghost War (PvP)", "emoji": "⚔️", "descricao": "Partidas contra outros jogadores"},
}
MODOS = {
    "breakpoint": {**_MODOS_GR_COMUNS,
                   "faccao": {"nome": "Missões de facção / diárias", "emoji": "📅",
                              "descricao": "Tarefas da semana e eventos"},
                   "outro": {"nome": "Outro", "emoji": "✨", "descricao": "Descreva nas observações"}},
    "wildlands": {**_MODOS_GR_COMUNS,
                  "fantasma": {"nome": "Modo Fantasma", "emoji": "👻", "descricao": "Morreu, perdeu o personagem"},
                  "outro": {"nome": "Outro", "emoji": "✨", "descricao": "Descreva nas observações"}},
    "r6": {
        "ranqueada": {"nome": "Ranqueada", "emoji": "🏆", "descricao": "Partidas valendo ranque"},
        "nao_ranqueada": {"nome": "Não ranqueada", "emoji": "🎯", "descricao": "Regras de ranqueada, sem ranque"},
        "rapida": {"nome": "Partida rápida", "emoji": "⚡", "descricao": "Casual, para aquecer"},
        "arcade": {"nome": "Arcade / Evento", "emoji": "🎉", "descricao": "Modos temporários"},
        "treino": {"nome": "Treino / Personalizada", "emoji": "🧪", "descricao": "Táticas, mapas, x1"},
        "outro": {"nome": "Outro", "emoji": "✨", "descricao": "Descreva nas observações"},
    },
}

ESTILOS = {
    "casual": {"nome": "Casual", "emoji": "😎", "descricao": "Sem pressão, para se divertir"},
    "furtivo": {"nome": "Furtivo", "emoji": "🌑", "descricao": "Silencioso, sem ser detectado"},
    "tatico": {"nome": "Tático", "emoji": "🎯", "descricao": "Comunicação e coordenação"},
    "livre": {"nome": "Livre", "emoji": "🌎", "descricao": "Cada um no seu ritmo"},
}


def item(tabela: dict, chave: str | None) -> str:
    v = tabela.get(chave or "")
    return f"{v['emoji']} {v['nome']}" if v else "—"
