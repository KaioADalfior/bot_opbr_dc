"""Estrutura declarativa do servidor Ghost Recon Brasil.

Este arquivo é a "planta" do servidor. O script compara esta planta com o que
existe no Discord e cria/corrige apenas o que falta, sem duplicar nada.

Alvos de permissão (overwrites):
  "@everyone"  -> cargo padrão de todos os membros
  "@bot"       -> cargo gerenciado do bot TEMPORÁRIO de configuração
                  (é apagado automaticamente quando o bot sai do servidor)
  <chave>      -> chave de um cargo definido em CARGOS
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .permissoes import P

# ---------------------------------------------------------------------------
# Paleta (identidade visual)
# ---------------------------------------------------------------------------
COR_FUNDO = 0x101722
COR_SUPERFICIE = 0x1D2939
COR_AZUL = 0x38BDF8
COR_VERDE = 0x22C55E
COR_TEXTO = 0xE6EDF5

# ---------------------------------------------------------------------------
# Conjuntos de permissões reutilizáveis
# ---------------------------------------------------------------------------
LEITURA = P.VIEW_CHANNEL | P.READ_MESSAGE_HISTORY

BLOQUEIO_ESCRITA = (
    P.SEND_MESSAGES | P.SEND_MESSAGES_IN_THREADS | P.CREATE_PUBLIC_THREADS
    | P.CREATE_PRIVATE_THREADS | P.ATTACH_FILES | P.EMBED_LINKS | P.SEND_POLLS
    | P.SEND_VOICE_MESSAGES | P.SEND_TTS_MESSAGES | P.MENTION_EVERYONE
)

ESCRITA_MEMBRO = (
    LEITURA | P.SEND_MESSAGES | P.SEND_MESSAGES_IN_THREADS | P.EMBED_LINKS
    | P.ATTACH_FILES | P.ADD_REACTIONS
)

ESCRITA_EQUIPE = (
    ESCRITA_MEMBRO | P.CREATE_PUBLIC_THREADS | P.MENTION_EVERYONE
    | P.MANAGE_MESSAGES | P.PIN_MESSAGES | P.MANAGE_THREADS
)

VOZ_MEMBRO = P.VIEW_CHANNEL | P.CONNECT | P.SPEAK | P.STREAM | P.USE_VAD

ACESSO_EQUIPE = (
    ESCRITA_MEMBRO | P.CREATE_PUBLIC_THREADS | P.CONNECT | P.SPEAK | P.STREAM
    | P.USE_VAD
)

# Permissões de cargo (nível do servidor)
PERM_ADMINISTRACAO = (
    P.VIEW_AUDIT_LOG | P.MANAGE_GUILD | P.MANAGE_CHANNELS | P.MANAGE_ROLES
    | P.MANAGE_WEBHOOKS | P.MANAGE_GUILD_EXPRESSIONS | P.CREATE_GUILD_EXPRESSIONS
    | P.MANAGE_EVENTS | P.CREATE_EVENTS | P.KICK_MEMBERS | P.BAN_MEMBERS
    | P.MODERATE_MEMBERS | P.MANAGE_MESSAGES | P.PIN_MESSAGES | P.MANAGE_THREADS
    | P.MANAGE_NICKNAMES | P.MUTE_MEMBERS | P.DEAFEN_MEMBERS | P.MOVE_MEMBERS
    | P.MENTION_EVERYONE | P.VIEW_GUILD_INSIGHTS | P.PRIORITY_SPEAKER
    | P.BYPASS_SLOWMODE
)
PERM_MODERADOR = (
    P.KICK_MEMBERS | P.BAN_MEMBERS | P.MODERATE_MEMBERS | P.MANAGE_MESSAGES
    | P.PIN_MESSAGES | P.MANAGE_THREADS | P.MANAGE_NICKNAMES | P.MUTE_MEMBERS
    | P.DEAFEN_MEMBERS | P.MOVE_MEMBERS | P.VIEW_AUDIT_LOG | P.BYPASS_SLOWMODE
)
PERM_ORGANIZADOR = P.MANAGE_EVENTS | P.CREATE_EVENTS

# Permissões que o bot usa diretamente para operar
PERM_OPERACAO_BOT = (
    P.VIEW_CHANNEL | P.SEND_MESSAGES | P.EMBED_LINKS | P.READ_MESSAGE_HISTORY
    | P.PIN_MESSAGES | P.MANAGE_ROLES | P.MANAGE_CHANNELS | P.MANAGE_GUILD
)


# ---------------------------------------------------------------------------
# Cargos (ordem = hierarquia, do mais alto para o mais baixo)
# ---------------------------------------------------------------------------
@dataclass
class Cargo:
    chave: str
    nome: str
    permissoes: int = 0
    cor: int = 0
    separado: bool = False      # "hoist": exibir separado na lista de membros
    mencionavel: bool = False
    grupo: str = ""
    observacao: str = ""


CARGOS: list[Cargo] = [
    # Liderança e equipe
    Cargo("lider", "👑 Líder Fundador", int(PERM_ADMINISTRACAO), 0xF1C40F, True, False, "lideranca",
          "Controle total. A permissão Administrador deve ser ativada MANUALMENTE pelo dono "
          "(o bot de configuração não recebe Administrador, então não pode concedê-la)."),
    Cargo("administracao", "🛡️ Administração", int(PERM_ADMINISTRACAO), 0xE74C3C, True, False, "equipe",
          "Gestão do servidor sem a permissão Administrador."),
    Cargo("moderador", "⚔️ Moderador", int(PERM_MODERADOR), 0xE67E22, True, False, "equipe",
          "Moderação de membros, mensagens e voz. Não gerencia servidor, canais nem cargos."),
    Cargo("organizador", "🧭 Organizador de Operações", int(PERM_ORGANIZADOR), 0x2ECC71, True, False, "equipe",
          "Gerencia eventos. Não bane nem expulsa. Pode mencionar cargos só nos canais de raid."),
    Cargo("vip", "💎 VIP", 0, 0xA855F7, True, False, "apoio",
          "Reconhecimento de apoiadores. Nenhum privilégio administrativo."),
    # Patentes demonstrativas (sem permissões; apenas destaque visual na lista de membros)
    # Oficiais superiores: estrelas cheias (dourado) | intermediários/subalternos: estrelas vazadas (prata)
    # Praças: setas » (verde-oliva)
    Cargo("pat_coronel", "★★★ Coronel", 0, 0xD4AF37, True, False, "patente"),
    Cargo("pat_tencoronel", "★★ Tenente-Coronel", 0, 0xDDBF5A, True, False, "patente"),
    Cargo("pat_major", "★ Major", 0, 0xE6CF7E, True, False, "patente"),
    Cargo("pat_capitao", "☆☆☆ Capitão", 0, 0xC0C7D1, True, False, "patente"),
    Cargo("pat_tenente", "☆ Tenente", 0, 0xD5DBE3, True, False, "patente"),
    Cargo("pat_sargento", "❯❯❯ Sargento", 0, 0x7FA34A, True, False, "patente"),
    Cargo("pat_cabo", "❯❯ Cabo", 0, 0x93B562, True, False, "patente"),
    Cargo("pat_soldado", "❯ Soldado", 0, 0xA7C47D, True, False, "patente"),
    # Reconhecimento
    Cargo("veterano", "🎖️ Veterano", 0, 0x38BDF8, False, False, "reconhecimento"),
    Cargo("colaborador", "🤝 Colaborador", 0, 0x7DD3FC, False, False, "reconhecimento"),
    Cargo("membro", "👤 Membro", 0, 0x94A3B8, False, False, "reconhecimento"),
    Cargo("novato", "🌱 Novato", 0, 0xCBD5E1, False, False, "reconhecimento"),
    # Jogos
    Cargo("jogo_wildlands", "🌿 Ghost Recon Wildlands", 0, 0x65A30D, False, False, "jogo"),
    Cargo("jogo_breakpoint", "💀 Ghost Recon Breakpoint", 0, 0x78716C, False, False, "jogo"),
    Cargo("jogo_r6", "👮 Rainbow Six Siege", 0, 0x3B82F6, False, False, "jogo"),
    # Plataformas
    Cargo("plat_pc", "🖥️ PC", 0, 0x9CA3AF, False, False, "plataforma"),
    Cargo("plat_xbox", "🟩 Xbox", 0, 0x16A34A, False, False, "plataforma"),
    Cargo("plat_ps", "🟦 PlayStation", 0, 0x2563EB, False, False, "plataforma"),
    # Estilos
    Cargo("estilo_casual", "😎 Casual", 0, 0xFACC15, False, False, "estilo"),
    Cargo("estilo_furtivo", "🌑 Furtivo", 0, 0x475569, False, False, "estilo"),
    Cargo("estilo_tatico", "🎯 Tático", 0, 0xDC2626, False, False, "estilo"),
    Cargo("estilo_livre", "🌎 Livre", 0, 0x14B8A6, False, False, "estilo"),
    # Notificações
    Cargo("notif_eventos", "🔔 Notificações de Eventos", 0, 0xF59E0B, False, False, "notificacao"),
    Cargo("notif_operacoes", "📢 Notificações de Operações", 0, 0xF97316, False, False, "notificacao"),
]
CARGOS_POR_CHAVE = {c.chave: c for c in CARGOS}
EQUIPE_ESCRITA = ("lider", "administracao")


# ---------------------------------------------------------------------------
# Canais
# ---------------------------------------------------------------------------
Overwrites = dict[str, tuple[int, int]]   # alvo -> (allow, deny)


@dataclass
class Canal:
    chave: str
    nome: str
    tipo: str                       # "texto" | "anuncio" | "voz"
    topico: str = ""
    modo_lento: int = 0             # segundos (0 = desativado; máximo 21600)
    limite_usuarios: int = 0        # voz (0 = sem limite)
    extras: Overwrites = field(default_factory=dict)
    mensagem: str | None = None     # chave em mensagens.py
    fixar_mensagem: bool = False


@dataclass
class Categoria:
    chave: str
    nome: str
    overwrites: Overwrites
    canais: list[Canal]
    privada: bool = False


def _ow(*pares: tuple[str, int, int]) -> Overwrites:
    return {alvo: (int(a), int(d)) for alvo, a, d in pares}


def _equipe_escreve(extra_alvos: tuple[str, ...] = ()) -> list[tuple[str, int, int]]:
    return [(c, ESCRITA_EQUIPE, 0) for c in EQUIPE_ESCRITA + extra_alvos]


# Base de qualquer categoria pública: ninguém comum menciona @everyone/@here.
def _publica(*extras: tuple[str, int, int]) -> Overwrites:
    base = [("@everyone", 0, P.MENTION_EVERYONE)]
    base += [(c, P.MENTION_EVERYONE, 0) for c in EQUIPE_ESCRITA]
    return _ow(*base, *extras)


def _somente_leitura(extra_escrita: tuple[str, ...] = ()) -> Overwrites:
    return _ow(("@everyone", LEITURA, BLOQUEIO_ESCRITA), *_equipe_escreve(extra_escrita))


def _privada_equipe() -> Overwrites:
    return _ow(
        ("@everyone", 0, P.VIEW_CHANNEL | P.CONNECT),
        ("lider", ACESSO_EQUIPE | P.MANAGE_MESSAGES | P.PIN_MESSAGES, 0),
        ("administracao", ACESSO_EQUIPE | P.MANAGE_MESSAGES | P.PIN_MESSAGES, 0),
        ("moderador", ACESSO_EQUIPE, 0),
    )


def _voz_publica() -> Overwrites:
    return _publica(("@everyone", VOZ_MEMBRO, P.MENTION_EVERYONE))


ORGANIZADOR_RAID = ("organizador", P.MENTION_EVERYONE | P.PIN_MESSAGES | P.MANAGE_THREADS, 0)
SEM_THREADS = ("@everyone", 0, P.CREATE_PUBLIC_THREADS | P.CREATE_PRIVATE_THREADS)


CATEGORIAS: list[Categoria] = [
    Categoria("central", "╭─── 📌 Central", _somente_leitura(), [
        Canal("anuncios", "📢｜anúncios", "anuncio",
              "Comunicados oficiais, operações, eventos e mudanças. Somente a equipe publica.",
              mensagem="anuncios"),
        Canal("boas_vindas", "👋｜boas-vindas", "texto",
              "Bem-vindo ao Ghost Recon Brasil. Nenhum operador fica para trás.",
              mensagem="boas_vindas"),
        Canal("regras", "📜｜regras", "texto",
              "Regras da comunidade. Leia antes de participar.", mensagem="regras"),
        Canal("comece_aqui", "🧭｜comece-aqui", "texto",
              "Como encontrar grupos, escolher jogos e plataformas e pedir ajuda.",
              mensagem="comece_aqui"),
    ]),
    Categoria("vips", "╭─── 🏅 VIPs", _publica(
        ("@everyone", LEITURA, BLOQUEIO_ESCRITA),
        ("vip", ESCRITA_MEMBRO, 0),
        *_equipe_escreve(),
    ), [
        Canal("vips", "🏅｜vips", "texto",
              "Espaço de apoiadores da comunidade. Todos leem; VIPs e equipe conversam.",
              mensagem="vips"),
        Canal("contribuicao", "💎｜contribuição", "texto",
              "Quer apoiar a comunidade? Clique em Quero contribuir e fale com a equipe em privado. "
              "Boosters viram VIP automaticamente.",
              extras=_ow(("vip", 0, BLOQUEIO_ESCRITA))),
    ]),
    Categoria("alistamento", "╭─── 🔥 Alistamento", _publica(ORGANIZADOR_RAID), [
        Canal("squad_raid", "🔥｜squad-raid", "texto",
              "Procure participantes para raids. Use o modelo fixado. Uma publicação a cada 5 min.",
              modo_lento=300, mensagem="squad_raid", fixar_mensagem=True),
        Canal("abrir_squad", "🎯｜abrir-squad", "texto",
              "Abra seu squad pelo painel: escolha o jogo, dê um nome e ganhe uma call exclusiva."),
        Canal("squad_partida", "🎮｜squad-partida", "texto",
              "Squads abertos: clique em ✅ Eu vou no card para entrar na call do esquadrão.",
              modo_lento=300, mensagem="squad_partida", fixar_mensagem=True),
    ]),
    Categoria("chat", "╭─── 🌐 Chat", _publica(("@everyone", VOZ_MEMBRO, P.MENTION_EVERYONE)), [
        Canal("geral", "💬｜geral", "texto", "Conversa geral da comunidade."),
        Canal("fotos_memes", "📷｜fotos-e-memes", "texto", "Memes, imagens e momentos engraçados."),
        Canal("outfits", "👕｜outfits", "texto",
              "Personagens, roupas, equipamentos visuais e personalizações."),
        Canal("sugestoes", "💡｜sugestões", "texto",
              "Ideias para eventos e melhorias do servidor. Use o modelo fixado.",
              modo_lento=120, mensagem="sugestoes", fixar_mensagem=True),
        Canal("comandos", "🤖｜comandos", "texto",
              "Reservado para futuras integrações de bots. Ainda não há comandos ativos.",
              extras=_ow(
                  ("@everyone", P.USE_APPLICATION_COMMANDS,
                   P.SEND_MESSAGES | P.SEND_MESSAGES_IN_THREADS | P.CREATE_PUBLIC_THREADS
                   | P.CREATE_PRIVATE_THREADS | P.MENTION_EVERYONE),
                  *_equipe_escreve(),
              ), mensagem="comandos"),
        Canal("clips", "🎬｜clips-e-highlights", "texto",
              "Jogadas marcantes, infiltrações, eliminações e momentos engraçados. Vídeos e links.",
              modo_lento=30, mensagem="clips", fixar_mensagem=True),
        Canal("lives", "🔴｜divulgação-de-lives", "texto",
              "Divulgue sua live: 1 publicação por transmissão. Modo lento de 6 h para membros.",
              modo_lento=21600, extras=_ow(SEM_THREADS),
              mensagem="lives", fixar_mensagem=True),
        Canal("voz_bate_papo", "🔊 Bate Papo (GERAL)", "voz"),
    ]),
    Categoria("ajuda", "╭─── 🆘 Ajuda", _publica(), [
        Canal("suporte_geral", "🛠️｜suporte-geral", "texto",
              "Problemas com acesso, cargos, canais e organização do servidor.",
              mensagem="suporte_geral"),
        Canal("suporte_dicas", "🧠｜suporte-dicas", "texto",
              "Dicas técnicas, configurações e problemas comuns dos jogos.",
              mensagem="suporte_dicas"),
        Canal("duvidas", "❓｜dúvidas", "texto",
              "Perguntas sobre a comunidade, jogos, esquadrões e operações.",
              mensagem="duvidas"),
        Canal("denuncias", "🚨｜denúncias", "texto",
              "Não publique denúncias aqui. Leia a orientação para contato privado com a equipe.",
              extras=_ow(
                  ("@everyone", LEITURA, BLOQUEIO_ESCRITA | P.ADD_REACTIONS),
                  *_equipe_escreve(("moderador",)),
              ), mensagem="denuncias"),
    ]),
    Categoria("mods", "╭─── 🧩 Mods", _publica(), [
        Canal("mods_publicados", "📦｜mods-publicados", "texto",
              "Mods aprovados pela equipe. Somente consulta.",
              extras=_somente_leitura(), mensagem="mods_publicados"),
        Canal("discussao_mods", "🗨️｜discussão-mods", "texto",
              "Compatibilidade, instalação, atualizações e experiências com mods. "
              "Não envie executáveis.", mensagem="discussao_mods", fixar_mensagem=True),
        Canal("regras_mods", "📋｜regras-para-mods", "texto",
              "Critérios de envio, aprovação e publicação de mods.",
              extras=_somente_leitura(), mensagem="regras_mods"),
        Canal("publicar_mod", "📤｜publicar-mod", "texto",
              "Envio de mods para avaliação. O envio automatizado estará disponível futuramente.",
              extras=_somente_leitura(), mensagem="publicar_mod"),
    ]),
    Categoria("breakpoint", "╭─── 💀 Breakpoint", _publica(
        ("@everyone", VOZ_MEMBRO, P.MENTION_EVERYONE)), [
        Canal("chat_breakpoint", "💀｜chat-geral-breakpoint", "texto",
              "Missões, atualizações, equipamentos, builds e cooperação em Breakpoint.",
              mensagem="chat_breakpoint"),
        Canal("raid_semanal", "📝｜raid-semanal", "texto",
              "Planejamento, inscrições e organização da raid semanal.",
              modo_lento=60, extras=_ow(ORGANIZADOR_RAID), mensagem="raid_semanal",
              fixar_mensagem=True),
        Canal("voz_breakpoint", "💀 Breakpoint Geral", "voz"),
    ]),
    Categoria("wildlands", "╭─── 🌿 Wildlands", _publica(
        ("@everyone", VOZ_MEMBRO, P.MENTION_EVERYONE)), [
        Canal("chat_wildlands", "🌿｜chat-geral-wildlands", "texto",
              "Missões, campanha cooperativa, exploração, equipamentos e dicas de Wildlands.",
              mensagem="chat_wildlands"),
        Canal("voz_wildlands", "🌿 Wildlands Geral", "voz"),
    ]),
    Categoria("r6", "╭─── 👮 Rainbow Six Siege", _voz_publica(), [
        Canal(f"radio_{n}", f"👮 Radio {n:02d}", "voz") for n in range(1, 5)
    ]),
    # As antigas categorias "Breakpoint | Salas" e "Wildlands | Salas" (24 calls fixas) foram substituídas
    # pelos squads do bot Operação Brasil (#abrir-squad), que criam uma call exclusiva para cada esquadrão.
    Categoria("equipe", "╭─── 🛡️ Equipe", _privada_equipe(), [
        Canal("chat_equipe", "🔒｜chat-da-equipe", "texto",
              "Conversa privada da equipe de administração e moderação.",
              extras=_ow(("organizador", ACESSO_EQUIPE, 0)), mensagem="chat_equipe"),
        Canal("logs_moderacao", "🗂️｜logs-de-moderação", "texto",
              "Registros de moderação (manuais agora; futuramente também do bot).",
              mensagem="logs_moderacao"),
        Canal("relatorios", "📑｜relatórios", "texto",
              "Relatórios de ocorrências e decisões da equipe. Dados pessoais só o necessário.",
              mensagem="relatorios"),
        Canal("reuniao_equipe", "🎙️ Reunião da Equipe", "voz",
              extras=_ow(("organizador", ACESSO_EQUIPE, 0))),
    ], privada=True),
]

# Limites de usuários opcionais para as Radios do Siege (desativados por padrão).
# As calls dos squads de Ghost Recon já são criadas pelo bot com limite de 4.
APLICAR_LIMITES_DE_VOZ = False
LIMITES_SUGERIDOS = {"r6": 5}
if APLICAR_LIMITES_DE_VOZ:
    for _cat in CATEGORIAS:
        if _cat.chave in LIMITES_SUGERIDOS:
            for _c in _cat.canais:
                _c.limite_usuarios = LIMITES_SUGERIDOS[_cat.chave]


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------
def mesclar(base: Overwrites, extras: Overwrites) -> Overwrites:
    resultado = dict(base)
    for alvo, (a, d) in extras.items():
        ba, bd = resultado.get(alvo, (0, 0))
        resultado[alvo] = (((ba & ~d) | a), ((bd & ~a) | d))
    return resultado


def overwrites_do_canal(cat: Categoria, canal: Canal) -> Overwrites:
    return mesclar(cat.overwrites, canal.extras)


def todos_os_canais():
    for cat in CATEGORIAS:
        for canal in cat.canais:
            yield cat, canal


def bits_usados_em_overwrites() -> int:
    total = 0
    for cat in CATEGORIAS:
        for a, d in cat.overwrites.values():
            total |= a | d
        for canal in cat.canais:
            for a, d in canal.extras.values():
                total |= a | d
    return total


def permissoes_canal_do_bot() -> int:
    """O que o cargo do bot recebe em cada canal (para ver canais privados e
    poder aplicar overwrites). Desaparece junto com o cargo do bot."""
    # Somente permissões aplicáveis a canais (nada de Gerenciar servidor/cargos aqui).
    return int(bits_usados_em_overwrites() | P.VIEW_CHANNEL | P.SEND_MESSAGES | P.EMBED_LINKS
               | P.READ_MESSAGE_HISTORY | P.PIN_MESSAGES)


def permissoes_necessarias_do_bot() -> int:
    """Permissões mínimas do bot temporário: o Discord só deixa um bot conceder
    (em cargos ou overwrites) permissões que ele próprio possui."""
    total = int(PERM_OPERACAO_BOT) | bits_usados_em_overwrites()
    for c in CARGOS:
        total |= c.permissoes
    assert not total & P.ADMINISTRATOR
    return total


def resumo_contagem() -> dict:
    texto = sum(1 for _, c in todos_os_canais() if c.tipo in ("texto", "anuncio"))
    voz = sum(1 for _, c in todos_os_canais() if c.tipo == "voz")
    return {"categorias": len(CATEGORIAS), "texto": texto, "voz": voz,
            "total_canais": len(CATEGORIAS) + texto + voz, "cargos": len(CARGOS)}
