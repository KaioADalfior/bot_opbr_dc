"""Permissões do cargo do bot Operação Brasil (sem Administrador)."""
import discord

PERMISSOES = discord.Permissions(
    view_channel=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True,
    add_reactions=True, send_messages_in_threads=True,   # para poder ajustar permissões de canais de membros
    manage_channels=True,   # canais de ticket, categoria Tickets, calls dos squads
    manage_roles=True,      # permissões dos canais e cargo VIP
    manage_messages=True,   # remover as mensagens antigas do bot de configuração
    pin_messages=True,      # fixar painéis e mensagens
    # Squads: criar a call do esquadrão, liberar a entrada de quem clicou em "Eu vou" e mover para a call
    connect=True, speak=True, stream=True, use_voice_activation=True, move_members=True,
)
