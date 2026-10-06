"""Mensagens iniciais (português brasileiro).

Regras deste arquivo:
- Nenhum comando ou bot é anunciado como funcionando.
- Nenhum dado pessoal, link real ou credencial.
- Nenhuma promessa de benefício pago.
Revise e ajuste os textos antes de executar `python main.py mensagens`.
"""
from __future__ import annotations

import re

from .estrutura import COR_AZUL, COR_VERDE

SLOGAN = "Nenhum operador fica para trás."

# Cada entrada: lista de embeds {titulo, texto, cor?}. Um embed = uma mensagem.
MENSAGENS: dict[str, list[dict]] = {
    "boas_vindas": [{
        "titulo": "Bem-vindo ao Ghost Recon Brasil",
        "texto": (
            f"**{SLOGAN}**\n\n"
            "Somos uma comunidade brasileira de jogadores de **Ghost Recon Wildlands**, "
            "**Ghost Recon Breakpoint** e **Rainbow Six Siege**. Aqui você encontra esquadrão, "
            "organiza operações, troca experiências e faz amizades — seja você casual, furtivo, "
            "tático, veterano ou recém-chegado.\n\n"
            "**Por onde começar**\n"
            "1. Leia as regras em {c:regras}.\n"
            "2. Veja o passo a passo em {c:comece_aqui}.\n"
            "3. Escolha seus jogos, plataformas e estilo em **Canais e Cargos** (topo da lista de canais).\n"
            "4. Procure um esquadrão em {c:squad_partida} ou {c:squad_raid}.\n"
            "5. Diga um oi em {c:geral}.\n\n"
            "_Comunidade independente, feita por fãs. Não somos afiliados à Ubisoft._"
        ),
    }],
    "regras": [
        {
            "titulo": "📜 Normas de Conduta do Servidor | Server Conduct Standards",
            "texto": (
                "**Português:**\n"
                "Estas regras foram formuladas com o objetivo de proporcionar a todos uma experiência "
                "agradável neste servidor. Caso não concorde com as diretrizes a seguir, sugerimos, "
                "respeitosamente, procurar um servidor mais alinhado com suas preferências. Se optar por "
                "permanecer, saiba que sua presença é muito bem-vinda. Vamos às regras:\n\n"
                "**English:**\n"
                "These rules were formulated with the aim of providing everyone with a pleasant experience "
                "on this server. If you do not agree with the following guidelines, we respectfully suggest "
                "looking for a server more in line with your preferences. If you choose to stay, know that "
                "your presence is very welcome. Let's go to the rules:"
            ),
        },
        {
            "titulo": "Regras 1 a 4",
            "texto": (
                "**1. Conteúdo Proibido nas Salas Públicas**\n"
                "Não é permitido publicar em salas públicas textos, vídeos, imagens e áudios sobre:\n"
                "a) Política;\n"
                "b) Religião;\n"
                "c) Futebol;\n"
                "d) Pornografia (sensualidade/nudez);\n"
                "e) Óbito (pessoas/animais);\n"
                "f) Acidentes;\n"
                "g) Desrespeito/ofensas pessoais/agressões verbais;\n"
                "h) Mensagens de corrente e/ou similares;\n"
                "i) Spam/links maliciosos.\n\n"
                "**2. Evite Repetições Excessivas**\n"
                "Evite enviar a mesma mensagem várias vezes, a fim de não poluir os canais de "
                "comunicação (#texto).\n\n"
                "**3. Comportamento Respeitoso e Resolução de Conflitos**\n"
                "Comportamentos desrespeitosos, ataques desnecessários ou pessoais devem ser resolvidos "
                "entre os envolvidos, fora do servidor. Administradores, moderadores e membros deste "
                "servidor não devem ser envolvidos gratuitamente. Ações que desestabilizem ou afetem as "
                "relações entre os membros **NÃO SERÃO TOLERADAS**. Não se deve utilizar quaisquer canais "
                "deste servidor para expor **ÁUDIOS, VÍDEOS, IMAGENS e/ou TEXTOS** sobre as discussões. "
                "A confirmação dessa atitude resultará em banimento imediato e permanente do(s) "
                "responsável(eis).\n\n"
                "**4. Proibição de Divulgação de Outros Servidores**\n"
                "Fica terminantemente proibida a divulgação de outros servidores Discord em nossos canais "
                "(texto/voz) sem a devida autorização. Antes da divulgação de conteúdo próprio ou de "
                "terceiros, consulte a nossa moderação. O conteúdo publicado (textos/imagens/vídeos) "
                "estará sujeito à exclusão sem aviso prévio. A reincidência ocasionará a expulsão "
                "imediata do autor."
            ),
        },
        {
            "titulo": "Regras 5 a 8",
            "texto": (
                "**5. Opiniões e Críticas Construtivas**\n"
                "Opiniões e críticas construtivas são sempre bem-vindas. Contudo, lembre-se de que você "
                "é responsável por elas.\n\n"
                "**6. Comportamento nos Canais de Voz (Jogos)**\n"
                "Ao entrar nos **CANAIS DE VOZ (JOGOS)**, seja prudente. Não atrapalhe a comunicação do "
                "Squad! Ao ouvir músicas/áudios ou assistir à TV, desative o seu microfone. Conversas "
                "paralelas também atrapalham a jogatina. Uma sugestão? Mude para o canal de voz "
                "{c:voz_bate_papo} e fale à vontade.\n\n"
                "**7. Modificadores de Voz e Mecanismos Intrusivos**\n"
                "Modificadores de voz ou quaisquer mecanismos que dificultem/interfiram na comunicação "
                "nos canais não serão tolerados.\n\n"
                "**8. Proteção de Informações Pessoais**\n"
                "A divulgação de informações pessoais (fotos, nome, endereço, documentos, etc.) de "
                "terceiros, sem autorização prévia comprovada, é terminantemente proibida. Causará "
                "banimento imediato do(s) responsável(eis), sem prejuízo de possíveis ações judiciais "
                "por parte dos denunciantes.\n\n"
                "Agradecemos a sua compreensão e cooperação para manter um ambiente positivo para "
                "todos os membros.\n\n"
                "**English:**\n"
                "In short: no spam, no promoting other servers, no sharing of personal information and "
                "no voice modifiers."
            ),
        },
        {
            "titulo": "Mas o que nós somos? | So, what are we?",
            "texto": (
                "Somos uma comunidade totalmente focada em Ghost Recon, The Division e outros jogos da "
                "saga Tom Clancy's, aqui para dicas e ajuda em missões e raids, onde você também verá: "
                "notícias, jogatinas e dicas para aumentar a sua experiência na saga Tom Clancy's.\n\n"
                "We are a community fully focused on Ghost Recon, The Division and other games from the "
                "Tom Clancy's saga, here for tips and help with missions and raids, where you will also "
                "find: news, gaming sessions and tips to improve your experience in the Tom Clancy's saga.\n\n"
                "**Aproveite bem o servidor e até a próxima! | Make good use of the server and see you "
                "next time!**\n\n"
                "_Comunidade de fãs, sem afiliação com a Ubisoft. | Fan community, not affiliated with Ubisoft._"
            ),
        },
    ],
    "anuncios": [{
        "titulo": "Canal de anúncios oficiais",
        "texto": (
            "Aqui a equipe publica comunicados oficiais: operações, eventos, mudanças no servidor "
            "e avisos importantes. Somente a equipe publica neste canal.\n\n"
            "Quer ser avisado de eventos e operações? Escolha as opções de notificação em "
            "**Canais e Cargos**."
        ),
    }],
    "comece_aqui": [
        {
            "titulo": "Comece aqui",
            "texto": (
                "**1. Escolha jogos, plataformas e estilo**\n"
                "Abra **Canais e Cargos** no topo da lista de canais e selecione o que você joga "
                "(Wildlands, Breakpoint, Siege), sua plataforma (PC, Xbox, PlayStation) e seu estilo "
                "(Casual, Furtivo, Tático, Livre). Você pode mudar quando quiser.\n\n"
                "**2. Encontre um grupo**\n"
                "• {c:squad_partida} — campanha, exploração, partidas casuais ou táticas.\n"
                "• {c:squad_raid} — raids e atividades cooperativas organizadas.\n"
                "Use o modelo fixado em cada canal e responda dentro da thread da publicação.\n\n"
                "**3. Participe de uma raid**\n"
                "Acompanhe {c:raid_semanal}. Antes de formar a equipe, confirme jogo, plataforma, "
                "versão, requisitos da atividade e se os participantes conseguem jogar juntos — "
                "compatibilidade entre plataformas varia conforme o jogo e o modo."
            ),
        },
        {
            "titulo": "Salas de voz, lives e ajuda",
            "texto": (
                "**4. Use as salas de voz**\n"
                "• Para jogar em grupo, abra um squad em {c:abrir_squad}: o bot cria uma call exclusiva "
                "com o nome do seu esquadrão.\n"
                "• Salas gerais: {c:voz_breakpoint}, {c:voz_wildlands} e {c:voz_bate_papo} para conversar.\n"
                "• Rainbow Six Siege: **Radio 01** a **Radio 04**.\n"
                "Se a sala estiver ocupada por outro grupo, abra um squad.\n\n"
                "**5. Divulgue sua live**\n"
                "Publique em {c:lives} seguindo as regras fixadas no canal.\n\n"
                "**6. Envie sugestões**\n"
                "Use o modelo fixado em {c:sugestoes}.\n\n"
                "**7. Precisa de ajuda?**\n"
                "• Servidor, acesso e cargos: {c:suporte_geral}\n"
                "• Dicas e problemas dos jogos: {c:suporte_dicas}\n"
                "• Perguntas gerais: {c:duvidas}\n"
                "• Contato privado com a equipe: veja {c:denuncias}."
            ),
        },
    ],
    "vips": [{
        "titulo": "Área VIP",
        "texto": (
            "Este espaço é dedicado a quem deseja apoiar voluntariamente a comunidade, ajudar na "
            "manutenção do servidor ou contribuir com iniciativas comunitárias.\n\n"
            "**Situação atual:** as formas de apoio ainda estão sendo definidas pela equipe. "
            "Não há benefícios pagos, assinaturas ou doações ativas neste momento. Quando existir "
            "alguma forma oficial de apoio, ela será anunciada em {c:anuncios} e explicada aqui.\n\n"
            "**Quem conversa aqui:** todos podem ler; membros com o cargo **VIP** e a equipe "
            "podem escrever.\n\n"
            "O cargo VIP é um reconhecimento: não concede poderes de moderação ou administração.\n\n"
            "⚠️ A equipe nunca pede senhas, códigos ou pagamentos por mensagem direta."
        ),
    }],
    "squad_raid": [{
        "titulo": "Como publicar em #squad-raid",
        "texto": (
            "Copie o modelo abaixo, preencha e publique. Combine os detalhes em uma **thread** "
            "da sua publicação para manter o canal organizado.\n\n"
            "```\n"
            "Jogo:\n"
            "Plataforma:\n"
            "Atividade/Raid:\n"
            "Data e horário (Brasília):\n"
            "Vagas:\n"
            "Requisitos (nível, equipamento, experiência):\n"
            "Voz: (sala do servidor)\n"
            "Contato: (responda na thread)\n"
            "```\n"
            "**Importante**\n"
            "• Cada raid tem regras e limites próprios — informe os da sua.\n"
            "• Confirme a compatibilidade entre plataformas e versões antes de fechar o grupo.\n"
            "• Uma publicação a cada 5 minutos (modo lento). Não repita o mesmo anúncio; "
            "edite o original quando preencher as vagas.\n"
            "• Este canal é para formar grupos; conversas vão para {c:geral}."
        ),
    }],
    "squad_partida": [{
        "titulo": "Como montar um squad",
        "texto": (
            "Aqui aparecem os **squads abertos**. Para abrir o seu, vá em {c:abrir_squad}.\n\n"
            "• Em {c:abrir_squad}, clique em **Abrir squad**, escolha jogo, plataforma e modo e dê um nome.\n"
            "• O bot cria uma **call de voz exclusiva** com esse nome.\n"
            "• Para entrar no squad de alguém, clique em **✅ Eu vou** no card.\n"
            "• Confirme se todos conseguem jogar juntos na plataforma e versão escolhidas."
        ),
    }],
    "sugestoes": [{
        "titulo": "Como enviar uma sugestão",
        "texto": (
            "```\n"
            "Sugestão:\n"
            "Por que ajudaria a comunidade:\n"
            "Como poderia funcionar:\n"
            "```\n"
            "Uma sugestão por mensagem. Discuta na thread da sugestão e use reações para mostrar "
            "apoio. A equipe avalia as ideias e comunica decisões em {c:anuncios}."
        ),
    }],
    "comandos": [{
        "titulo": "Canal reservado para integrações futuras",
        "texto": (
            "Este canal receberá comandos de bots da comunidade quando eles forem implementados. "
            "**No momento, nenhum bot ou comando está ativo.**\n\n"
            "Quando houver integrações, a equipe vai anunciar em {c:anuncios} e explicar aqui como "
            "usá-las. Para conversar, use {c:geral}."
        ),
    }],
    "clips": [{
        "titulo": "Clips e highlights",
        "texto": (
            "Compartilhe jogadas marcantes, infiltrações, eliminações e momentos engraçados.\n\n"
            "• Envie o vídeo/imagem ou o link (YouTube, Twitch, Medal etc.).\n"
            "• Diga o jogo e, se quiser, a plataforma.\n"
            "• Comentários vão na thread do clipe.\n"
            "• Sem conteúdo ofensivo, dados pessoais ou divulgação de canal fora de contexto — "
            "divulgação de lives fica em {c:lives}."
        ),
    }],
    "lives": [{
        "titulo": "Regras de divulgação de lives",
        "texto": (
            "• Uma publicação por transmissão: link + jogo + o que você está fazendo.\n"
            "• Modo lento de **6 horas** para membros (a equipe pode ajustar este limite).\n"
            "• Somente lives relacionadas aos jogos da comunidade ou à própria comunidade.\n"
            "• Não repita a divulgação em outros canais nem por mensagem direta a membros.\n"
            "• Conversas sobre a live vão para {c:geral}.\n\n"
            "As publicações são feitas manualmente. Uma integração automática com plataformas de "
            "transmissão poderá ser avaliada no futuro; ela ainda não existe."
        ),
    }],
    "suporte_geral": [{
        "titulo": "Suporte do servidor",
        "texto": (
            "Use este canal para problemas com acesso, cargos, canais e organização do servidor. "
            "Descreva o problema e, se possível, envie um print (sem dados pessoais).\n\n"
            "Para assuntos sensíveis ou denúncias, **não** use este canal: veja {c:denuncias}."
        ),
    }],
    "suporte_dicas": [{
        "titulo": "Dicas e problemas dos jogos",
        "texto": (
            "Dúvidas técnicas, configurações, desempenho, conexão e problemas comuns dos jogos. "
            "Informe jogo, plataforma e o que já tentou. Não compartilhe dados de conta nem "
            "arquivos executáveis."
        ),
    }],
    "duvidas": [{
        "titulo": "Dúvidas",
        "texto": (
            "Perguntas sobre a comunidade, os jogos, a formação de esquadrões e as operações. "
            "Antes de perguntar, dê uma olhada em {c:comece_aqui}."
        ),
    }],
    "denuncias": [{
        "titulo": "Como falar com a equipe em privado",
        "texto": (
            "**Não publique denúncias, provas ou nomes em canais públicos.**\n\n"
            "Para falar com a equipe em privado, use o botão **Abrir atendimento privado** no painel "
            "fixado neste canal. Um canal visível só para você e para a equipe será criado.\n\n"
            "Se o botão não responder:\n"
            "1. Envie uma mensagem direta a um membro com cargo **Moderador** ou **Administração** "
            "(eles aparecem separados na lista de membros).\n"
            "2. Explique o ocorrido e envie as provas somente nessa conversa privada.\n"
            "3. Desconfie de quem pedir senha, código, dados pessoais ou pagamento — a equipe "
            "nunca faz isso.\n"
            "4. Violações graves das regras do Discord também podem ser denunciadas diretamente "
            "ao Discord pelas ferramentas oficiais de denúncia no aplicativo."
        ),
    }],
    "mods_publicados": [{
        "titulo": "Mods publicados",
        "texto": (
            "Aqui serão listados os mods **revisados e aprovados** pela equipe. "
            "Nenhum mod foi publicado ainda.\n\n"
            "Nenhum mod é publicado automaticamente apenas por ter sido enviado. Mesmo mods "
            "aprovados são usados por sua conta e risco: faça backup e confira a compatibilidade "
            "com sua versão e plataforma. Critérios em {c:regras_mods}."
        ),
    }],
    "discussao_mods": [{
        "titulo": "Discussão sobre mods",
        "texto": (
            "Converse sobre compatibilidade, instalação, atualizações e experiências com mods de "
            "Wildlands e Breakpoint.\n\n"
            "• **Não envie executáveis** nem arquivos de origem desconhecida; prefira links das "
            "páginas oficiais dos autores.\n"
            "• Dê crédito aos autores.\n"
            "• Nada de cheats, mods para trapaça online ou conteúdo pirateado.\n"
            "• Mods podem violar termos de uso ou causar problemas: use por sua conta e risco."
        ),
    }],
    "regras_mods": [{
        "titulo": "Regras para envio e publicação de mods",
        "texto": (
            "**Critérios de aprovação**\n"
            "1. Mod para Ghost Recon Wildlands ou Breakpoint, com jogo e versão compatíveis informados.\n"
            "2. Link para a página oficial do autor ou repositório reconhecido — sem encurtadores.\n"
            "3. Créditos claros ao(s) autor(es) e respeito à licença/permissões de distribuição.\n"
            "4. Instruções de instalação e de remoção.\n"
            "5. Sem cheats, vantagens online injustas, malware, conteúdo pirateado ou ofensivo.\n\n"
            "**Processo**\n"
            "• Todo envio passa por análise da equipe; nada é publicado automaticamente.\n"
            "• Quem envia não pode aprovar o próprio envio.\n"
            "• Links suspeitos, executáveis desconhecidos ou falta de créditos levam a análise "
            "adicional ou recusa.\n"
            "• A equipe pode aprovar, recusar ou pedir alterações; envios duplicados ou abandonados "
            "são encerrados.\n\n"
            "Para enviar um mod, use o botão **Enviar mod** no painel fixado em {c:publicar_mod}."
        ),
    }],
    "publicar_mod": [{
        "titulo": "Envio de mods para avaliação",
        "texto": (
            "Use o botão **Enviar mod** no painel fixado neste canal. O envio abre um canal privado "
            "entre você e a equipe, onde o mod é analisado.\n\n"
            "Antes de enviar, leia {c:regras_mods}. Dúvidas gerais: {c:discussao_mods}."
        ),
    }],
    "chat_breakpoint": [{
        "titulo": "Ghost Recon Breakpoint",
        "texto": (
            "Missões, atualizações, equipamentos, builds e cooperação. Para formar grupo, use "
            "{c:abrir_squad} (o bot cria uma call só para o seu squad) ou {c:squad_raid}; para conversar, "
            "{c:voz_breakpoint}."
        ),
    }],
    "raid_semanal": [{
        "titulo": "Raid semanal",
        "texto": (
            "Planejamento, inscrições e organização da raid semanal.\n\n"
            "**Como funciona (manual, por enquanto)**\n"
            "1. Um Organizador de Operações publica data, horário, plataforma e requisitos.\n"
            "2. Para participar, responda na thread do anúncio com jogo, plataforma e disponibilidade.\n"
            "3. O organizador confirma a equipe na própria thread.\n\n"
            "**Antes de formar a equipe**, confirme compatibilidade de plataforma e versão, "
            "requisitos e o limite de participantes da atividade.\n\n"
            "Não há inscrição automática, lista de espera ou confirmação por bot neste momento."
        ),
    }],
    "chat_wildlands": [{
        "titulo": "Ghost Recon Wildlands",
        "texto": (
            "Missões, campanha cooperativa, exploração, equipamentos, dicas e experiências. "
            "Para formar grupo, abra um squad em {c:abrir_squad} (o bot cria uma call só para ele); "
            "para conversar, {c:voz_wildlands}. Confirme plataforma e versão antes de chamar alguém."
        ),
    }],
    "chat_equipe": [{
        "titulo": "Canal da equipe",
        "texto": (
            "Canal privado da administração, moderação e organização de operações.\n\n"
            "• Configurações manuais pendentes: veja `docs/04-configuracao-manual.md` no projeto "
            "de configuração.\n"
            "• Use {c:relatorios} para registrar ocorrências e {c:logs_moderacao} para ações "
            "de moderação.\n"
            "• Ative a autenticação em dois fatores (2FA) na sua conta."
        ),
        "cor": COR_VERDE,
    }],
    "logs_moderacao": [{
        "titulo": "Logs de moderação",
        "texto": (
            "Registre aqui as ações de moderação (advertências, castigos, expulsões, banimentos):\n"
            "```\nData:\nMembro (ID):\nAção:\nMotivo:\nResponsável:\n```\n"
            "No futuro, um bot de moderação poderá registrar ações automaticamente aqui. "
            "O registro de auditoria nativo do Discord continua disponível em "
            "Configurações do Servidor."
        ),
    }],
    "relatorios": [{
        "titulo": "Relatórios da equipe",
        "texto": (
            "Use para ocorrências e decisões. Registre apenas os dados necessários e não copie "
            "informações pessoais além do indispensável.\n"
            "```\nData:\nResumo:\nEnvolvidos (IDs):\nProvas (links internos):\nDecisão:\n```"
        ),
    }],
}

_TOKEN = re.compile(r"\{c:([a-z0-9_]+)\}")


def resolver_mencoes(texto: str, ids: dict[str, str] | None = None) -> str:
    """Troca {c:chave} por uma menção clicável <#ID> (ou pelo nome do canal, sem ID)."""
    from .estrutura import todos_os_canais
    nomes = {c.chave: c.nome for _, c in todos_os_canais()}

    def troca(mo):
        chave = mo.group(1)
        if ids and ids.get(chave, "").isdigit():
            return f"<#{ids[chave]}>"
        return f"**{nomes.get(chave, chave)}**"
    return _TOKEN.sub(troca, texto)


def embeds_de(chave: str, ids: dict[str, str] | None = None) -> list[dict]:
    saida = []
    for item in MENSAGENS[chave]:
        saida.append({
            "title": item["titulo"],
            "description": resolver_mencoes(item["texto"], ids),
            "color": item.get("cor", COR_AZUL),
        })
    return saida
