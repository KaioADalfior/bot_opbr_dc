"""Flags de permissão da API do Discord (v10) e cálculo de permissões efetivas.

Valores conferidos em https://docs.discord.com/developers/topics/permissions
(verificação feita em 03/10/2026).
"""
from __future__ import annotations

from enum import IntFlag


class P(IntFlag):
    CREATE_INSTANT_INVITE = 1 << 0
    KICK_MEMBERS = 1 << 1
    BAN_MEMBERS = 1 << 2
    ADMINISTRATOR = 1 << 3
    MANAGE_CHANNELS = 1 << 4
    MANAGE_GUILD = 1 << 5
    ADD_REACTIONS = 1 << 6
    VIEW_AUDIT_LOG = 1 << 7
    PRIORITY_SPEAKER = 1 << 8
    STREAM = 1 << 9
    VIEW_CHANNEL = 1 << 10
    SEND_MESSAGES = 1 << 11
    SEND_TTS_MESSAGES = 1 << 12
    MANAGE_MESSAGES = 1 << 13
    EMBED_LINKS = 1 << 14
    ATTACH_FILES = 1 << 15
    READ_MESSAGE_HISTORY = 1 << 16
    MENTION_EVERYONE = 1 << 17
    USE_EXTERNAL_EMOJIS = 1 << 18
    VIEW_GUILD_INSIGHTS = 1 << 19
    CONNECT = 1 << 20
    SPEAK = 1 << 21
    MUTE_MEMBERS = 1 << 22
    DEAFEN_MEMBERS = 1 << 23
    MOVE_MEMBERS = 1 << 24
    USE_VAD = 1 << 25
    CHANGE_NICKNAME = 1 << 26
    MANAGE_NICKNAMES = 1 << 27
    MANAGE_ROLES = 1 << 28
    MANAGE_WEBHOOKS = 1 << 29
    MANAGE_GUILD_EXPRESSIONS = 1 << 30
    USE_APPLICATION_COMMANDS = 1 << 31
    REQUEST_TO_SPEAK = 1 << 32
    MANAGE_EVENTS = 1 << 33
    MANAGE_THREADS = 1 << 34
    CREATE_PUBLIC_THREADS = 1 << 35
    CREATE_PRIVATE_THREADS = 1 << 36
    USE_EXTERNAL_STICKERS = 1 << 37
    SEND_MESSAGES_IN_THREADS = 1 << 38
    USE_EMBEDDED_ACTIVITIES = 1 << 39
    MODERATE_MEMBERS = 1 << 40
    VIEW_CREATOR_MONETIZATION_ANALYTICS = 1 << 41
    USE_SOUNDBOARD = 1 << 42
    CREATE_GUILD_EXPRESSIONS = 1 << 43
    CREATE_EVENTS = 1 << 44
    USE_EXTERNAL_SOUNDS = 1 << 45
    SEND_VOICE_MESSAGES = 1 << 46
    SET_VOICE_CHANNEL_STATUS = 1 << 48
    SEND_POLLS = 1 << 49
    USE_EXTERNAL_APPS = 1 << 50
    PIN_MESSAGES = 1 << 51
    BYPASS_SLOWMODE = 1 << 52


NENHUMA = P(0)
TODAS = P(0)
for _flag in P:
    TODAS |= _flag

# Nomes em português para relatórios.
NOMES_PT = {
    P.CREATE_INSTANT_INVITE: "Criar convite",
    P.KICK_MEMBERS: "Expulsar membros",
    P.BAN_MEMBERS: "Banir membros",
    P.ADMINISTRATOR: "Administrador",
    P.MANAGE_CHANNELS: "Gerenciar canais",
    P.MANAGE_GUILD: "Gerenciar servidor",
    P.ADD_REACTIONS: "Adicionar reações",
    P.VIEW_AUDIT_LOG: "Ver registro de auditoria",
    P.PRIORITY_SPEAKER: "Voz prioritária",
    P.STREAM: "Vídeo / transmitir",
    P.VIEW_CHANNEL: "Ver canal",
    P.SEND_MESSAGES: "Enviar mensagens",
    P.SEND_TTS_MESSAGES: "Enviar mensagens TTS",
    P.MANAGE_MESSAGES: "Gerenciar mensagens",
    P.EMBED_LINKS: "Inserir links",
    P.ATTACH_FILES: "Anexar arquivos",
    P.READ_MESSAGE_HISTORY: "Ver histórico de mensagens",
    P.MENTION_EVERYONE: "Mencionar @everyone, @here e todos os cargos",
    P.USE_EXTERNAL_EMOJIS: "Usar emojis externos",
    P.VIEW_GUILD_INSIGHTS: "Ver análises do servidor",
    P.CONNECT: "Conectar (voz)",
    P.SPEAK: "Falar (voz)",
    P.MUTE_MEMBERS: "Silenciar membros",
    P.DEAFEN_MEMBERS: "Ensurdecer membros",
    P.MOVE_MEMBERS: "Mover membros",
    P.USE_VAD: "Usar detecção de voz",
    P.CHANGE_NICKNAME: "Alterar apelido",
    P.MANAGE_NICKNAMES: "Gerenciar apelidos",
    P.MANAGE_ROLES: "Gerenciar cargos / permissões",
    P.MANAGE_WEBHOOKS: "Gerenciar webhooks",
    P.MANAGE_GUILD_EXPRESSIONS: "Gerenciar expressões",
    P.USE_APPLICATION_COMMANDS: "Usar comandos de aplicativos",
    P.REQUEST_TO_SPEAK: "Pedir para falar",
    P.MANAGE_EVENTS: "Gerenciar eventos",
    P.MANAGE_THREADS: "Gerenciar threads",
    P.CREATE_PUBLIC_THREADS: "Criar threads públicas",
    P.CREATE_PRIVATE_THREADS: "Criar threads privadas",
    P.USE_EXTERNAL_STICKERS: "Usar figurinhas externas",
    P.SEND_MESSAGES_IN_THREADS: "Enviar mensagens em threads",
    P.USE_EMBEDDED_ACTIVITIES: "Usar atividades",
    P.MODERATE_MEMBERS: "Castigar membros (timeout)",
    P.VIEW_CREATOR_MONETIZATION_ANALYTICS: "Ver análises de monetização",
    P.USE_SOUNDBOARD: "Usar soundboard",
    P.CREATE_GUILD_EXPRESSIONS: "Criar expressões",
    P.CREATE_EVENTS: "Criar eventos",
    P.USE_EXTERNAL_SOUNDS: "Usar sons externos",
    P.SEND_VOICE_MESSAGES: "Enviar mensagens de voz",
    P.SET_VOICE_CHANNEL_STATUS: "Definir status do canal de voz",
    P.SEND_POLLS: "Criar enquetes",
    P.USE_EXTERNAL_APPS: "Usar apps externos",
    P.PIN_MESSAGES: "Fixar mensagens",
    P.BYPASS_SLOWMODE: "Ignorar modo lento",
}

# Permissões consideradas "de poder" (administrativas ou de moderação).
PODERES = (
    P.ADMINISTRATOR | P.MANAGE_GUILD | P.MANAGE_ROLES | P.MANAGE_CHANNELS
    | P.KICK_MEMBERS | P.BAN_MEMBERS | P.MODERATE_MEMBERS | P.MANAGE_MESSAGES
    | P.MANAGE_THREADS | P.MANAGE_NICKNAMES | P.MANAGE_WEBHOOKS
    | P.MANAGE_GUILD_EXPRESSIONS | P.VIEW_AUDIT_LOG | P.MUTE_MEMBERS
    | P.DEAFEN_MEMBERS | P.MOVE_MEMBERS | P.MENTION_EVERYONE | P.MANAGE_EVENTS
)

# Permissões que dependem de "Enviar mensagens" (regra implícita do Discord).
DEPENDEM_DE_ENVIAR = (
    P.SEND_TTS_MESSAGES | P.MENTION_EVERYONE | P.ATTACH_FILES | P.EMBED_LINKS
    | P.SEND_POLLS | P.SEND_VOICE_MESSAGES
)
# Permissões de texto (somem quando não há VIEW_CHANNEL).
# Permissões de voz (somem quando não há CONNECT).
DEPENDEM_DE_CONECTAR = (
    P.SPEAK | P.STREAM | P.USE_VAD | P.PRIORITY_SPEAKER | P.MUTE_MEMBERS
    | P.DEAFEN_MEMBERS | P.MOVE_MEMBERS | P.USE_SOUNDBOARD | P.USE_EXTERNAL_SOUNDS
    | P.USE_EMBEDDED_ACTIVITIES | P.SET_VOICE_CHANNEL_STATUS | P.REQUEST_TO_SPEAK
)


def nomes(perms: int) -> list[str]:
    return [NOMES_PT.get(f, f.name) for f in P if perms & f]


def permissoes_base(role_perms: dict[str, int], everyone_id: str, roles_membro: list[str],
                    eh_dono: bool = False) -> int:
    """Permissões no nível do servidor (antes dos overwrites)."""
    if eh_dono:
        return int(TODAS)
    perms = role_perms.get(everyone_id, 0)
    for rid in roles_membro:
        perms |= role_perms.get(rid, 0)
    if perms & P.ADMINISTRATOR:
        return int(TODAS)
    return perms


def permissoes_canal(base: int, overwrites: list[dict], everyone_id: str,
                     roles_membro: list[str], membro_id: str | None = None,
                     canal_voz: bool = False) -> int:
    """Calcula permissões efetivas seguindo a ordem oficial do Discord."""
    if base & P.ADMINISTRATOR:
        return int(TODAS)
    perms = base
    ow_by_id = {str(o["id"]): o for o in overwrites}

    ev = ow_by_id.get(str(everyone_id))
    if ev:
        perms &= ~int(ev.get("deny", 0))
        perms |= int(ev.get("allow", 0))

    allow = 0
    deny = 0
    for rid in roles_membro:
        o = ow_by_id.get(str(rid))
        if o and int(o.get("type", 0)) == 0:
            allow |= int(o.get("allow", 0))
            deny |= int(o.get("deny", 0))
    perms &= ~deny
    perms |= allow

    if membro_id:
        o = ow_by_id.get(str(membro_id))
        if o and int(o.get("type", 0)) == 1:
            perms &= ~int(o.get("deny", 0))
            perms |= int(o.get("allow", 0))

    # Regras implícitas
    if not perms & P.VIEW_CHANNEL:
        return 0
    if not canal_voz and not perms & P.SEND_MESSAGES:
        perms &= ~int(DEPENDEM_DE_ENVIAR)
    if canal_voz and not perms & P.CONNECT:
        perms &= ~int(DEPENDEM_DE_CONECTAR)
    return perms
