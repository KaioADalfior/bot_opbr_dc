"""Mensagens fixas dos canais, publicadas pelo bot Operação Brasil.

Fonte única do texto dos canais. Para mudar um texto, edite aqui e use /servidor publicar
(ou apenas reinicie o bot: mensagens já publicadas são atualizadas sozinhas).

Marcadores: {c:chave} vira a menção do canal (ex.: {c:regras} -> #📜｜regras).
Cada canal tem uma lista de blocos; cada bloco vira um embed:
    {"titulo": ..., "texto": ..., "campos": [(nome, valor, inline), ...]}
"""
from __future__ import annotations

# chave -> (nome no Discord, categoria, tipo, fixar a mensagem)
CANAIS = {
    "anuncios": ("📢｜anúncios", "central", "anuncio", False),
    "boas_vindas": ("👋｜boas-vindas", "central", "texto", False),
    "regras": ("📜｜regras", "central", "texto", False),
    "comece_aqui": ("🧭｜comece-aqui", "central", "texto", False),
    "vips": ("🏅｜vips", "vips", "texto", False),
    "contribuicao": ("💎｜contribuição", "vips", "texto", False),
    "squad_raid": ("🔥｜squad-raid", "alistamento", "texto", True),
    "abrir_squad": ("🎯｜abrir-squad", "alistamento", "texto", False),
    "squad_partida": ("🎮｜squad-partida", "alistamento", "texto", True),
    "geral": ("💬｜geral", "chat", "texto", False),
    "fotos_memes": ("📷｜fotos-e-memes", "chat", "texto", False),
    "outfits": ("👕｜outfits", "chat", "texto", False),
    "sugestoes": ("💡｜sugestões", "chat", "texto", True),
    "comandos": ("🤖｜comandos", "chat", "texto", False),
    "clips": ("🎬｜clips-e-highlights", "chat", "texto", True),
    "lives": ("🔴｜divulgação-de-lives", "chat", "texto", True),
    "voz_bate_papo": ("🔊 Bate Papo (GERAL)", "chat", "voz", False),
    "suporte_geral": ("🛠️｜suporte-geral", "ajuda", "texto", False),
    "suporte_dicas": ("🧠｜suporte-dicas", "ajuda", "texto", False),
    "duvidas": ("❓｜dúvidas", "ajuda", "texto", False),
    "denuncias": ("🚨｜denúncias", "ajuda", "texto", False),
    "mods_publicados": ("📦｜mods-publicados", "mods", "texto", False),
    "discussao_mods": ("🗨️｜discussão-mods", "mods", "texto", True),
    "regras_mods": ("📋｜regras-para-mods", "mods", "texto", False),
    "publicar_mod": ("📤｜publicar-mod", "mods", "texto", False),
    "chat_breakpoint": ("💀｜chat-geral-breakpoint", "breakpoint", "texto", False),
    "raid_semanal": ("📝｜raid-semanal", "breakpoint", "texto", True),
    "voz_breakpoint": ("💀 Breakpoint Geral", "breakpoint", "voz", False),
    "chat_wildlands": ("🌿｜chat-geral-wildlands", "wildlands", "texto", False),
    "voz_wildlands": ("🌿 Wildlands Geral", "wildlands", "voz", False),
    "radio_1": ("👮 Radio 01", "r6", "voz", False),
    "radio_2": ("👮 Radio 02", "r6", "voz", False),
    "radio_3": ("👮 Radio 03", "r6", "voz", False),
    "radio_4": ("👮 Radio 04", "r6", "voz", False),
    "chat_equipe": ("🔒｜chat-da-equipe", "equipe", "texto", False),
    "logs_moderacao": ("🗂️｜logs-de-moderação", "equipe", "texto", False),
    "relatorios": ("📑｜relatórios", "equipe", "texto", False),
    "reuniao_equipe": ("🎙️ Reunião da Equipe", "equipe", "voz", False),
}

CATEGORIAS = {
    "central": ("╭─── 📌 Central", 0xE2B33C),
    "vips": ("╭─── 🏅 VIPs", 0xA855F7),
    "alistamento": ("╭─── 🔥 Alistamento", 0xF97316),
    "chat": ("╭─── 🌐 Chat", 0x14B8A6),
    "ajuda": ("╭─── 🆘 Ajuda", 0xF59E0B),
    "mods": ("╭─── 🧩 Mods", 0x06B6D4),
    "breakpoint": ("╭─── 💀 Breakpoint", 0x38BDF8),
    "wildlands": ("╭─── 🌿 Wildlands", 0x65A30D),
    "r6": ("╭─── 👮 Rainbow Six Siege", 0x3B82F6),
    "equipe": ("╭─── 🛡️ Equipe", 0xEF4444),
}

# Canais cujo conteúdo é um PAINEL com botões (publicado pelos módulos de tickets/squads/VIP).
CANAIS_DE_PAINEL = {"denuncias", "publicar_mod", "abrir_squad", "squad_partida", "contribuicao"}

RODAPE = "Ghost Recon® | Operação Brasil • Nenhum operador fica para trás"

MENSAGENS: dict[str, list[dict]] = {
    # ------------------------------------------------------------------ Central
    "boas_vindas": [{
        "titulo": "👋 Bem-vindo à Operação Brasil",
        "texto": (
            "**Nenhum operador fica para trás.**\n\n"
            "Somos uma comunidade brasileira de **Ghost Recon Wildlands**, **Ghost Recon Breakpoint** e "
            "**Rainbow Six Siege**. Aqui você encontra esquadrão, organiza operações, troca experiências e faz "
            "amizades, seja você casual, furtivo, tático, veterano ou recém-chegado."
        ),
        "campos": [
            ("📜 1. Leia as regras", "{c:regras}", True),
            ("🧭 2. Veja o briefing", "{c:comece_aqui}", True),
            ("🎭 3. Escolha seus cargos", "Em **Canais e Cargos**, no topo da lista", True),
            ("🎯 4. Monte um squad", "{c:abrir_squad}", True),
            ("🎮 5. Entre num squad", "{c:squad_partida}", True),
            ("💬 6. Diga um oi", "{c:geral}", True),
            ("\u200b", "-# Comunidade independente, feita por fãs. Não somos afiliados à Ubisoft.", False),
        ],
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
                "These rules were formulated with the aim of providing everyone with a pleasant experience on "
                "this server. If you do not agree with the following guidelines, we respectfully suggest looking "
                "for a server more in line with your preferences. If you choose to stay, know that your presence "
                "is very welcome. Let's go to the rules:"
            ),
        },
        {
            "titulo": "Regras 1 a 4",
            "texto": (
                "**1. Conteúdo Proibido nas Salas Públicas**\n"
                "Não é permitido publicar em salas públicas textos, vídeos, imagens e áudios sobre:\n"
                "a) Política;\nb) Religião;\nc) Futebol;\nd) Pornografia (sensualidade/nudez);\n"
                "e) Óbito (pessoas/animais);\nf) Acidentes;\ng) Desrespeito/ofensas pessoais/agressões verbais;\n"
                "h) Mensagens de corrente e/ou similares;\ni) Spam/links maliciosos.\n\n"
                "**2. Evite Repetições Excessivas**\n"
                "Evite enviar a mesma mensagem várias vezes, a fim de não poluir os canais de comunicação "
                "(#texto).\n\n"
                "**3. Comportamento Respeitoso e Resolução de Conflitos**\n"
                "Comportamentos desrespeitosos, ataques desnecessários ou pessoais devem ser resolvidos entre os "
                "envolvidos, fora do servidor. Administradores, moderadores e membros deste servidor não devem ser "
                "envolvidos gratuitamente. Ações que desestabilizem ou afetem as relações entre os membros **NÃO "
                "SERÃO TOLERADAS**. Não se deve utilizar quaisquer canais deste servidor para expor **ÁUDIOS, "
                "VÍDEOS, IMAGENS e/ou TEXTOS** sobre as discussões. A confirmação dessa atitude resultará em "
                "banimento imediato e permanente do(s) responsável(eis).\n\n"
                "**4. Proibição de Divulgação de Outros Servidores**\n"
                "Fica terminantemente proibida a divulgação de outros servidores Discord em nossos canais "
                "(texto/voz) sem a devida autorização. Antes da divulgação de conteúdo próprio ou de terceiros, "
                "consulte a nossa moderação. O conteúdo publicado (textos/imagens/vídeos) estará sujeito à "
                "exclusão sem aviso prévio. A reincidência ocasionará a expulsão imediata do autor."
            ),
        },
        {
            "titulo": "Regras 5 a 8",
            "texto": (
                "**5. Opiniões e Críticas Construtivas**\n"
                "Opiniões e críticas construtivas são sempre bem-vindas. Contudo, lembre-se de que você é "
                "responsável por elas.\n\n"
                "**6. Comportamento nos Canais de Voz (Jogos)**\n"
                "Ao entrar nos **CANAIS DE VOZ (JOGOS)**, seja prudente. Não atrapalhe a comunicação do Squad! Ao "
                "ouvir músicas/áudios ou assistir à TV, desative o seu microfone. Conversas paralelas também "
                "atrapalham a jogatina. Uma sugestão? Mude para o canal de voz {c:voz_bate_papo} e fale à "
                "vontade.\n\n"
                "**7. Modificadores de Voz e Mecanismos Intrusivos**\n"
                "Modificadores de voz ou quaisquer mecanismos que dificultem/interfiram na comunicação nos canais "
                "não serão tolerados.\n\n"
                "**8. Proteção de Informações Pessoais**\n"
                "A divulgação de informações pessoais (fotos, nome, endereço, documentos, etc.) de terceiros, sem "
                "autorização prévia comprovada, é terminantemente proibida. Causará banimento imediato do(s) "
                "responsável(eis), sem prejuízo de possíveis ações judiciais por parte dos denunciantes.\n\n"
                "Agradecemos a sua compreensão e cooperação para manter um ambiente positivo para todos os "
                "membros.\n\n"
                "**English:**\n"
                "In short: no spam, no promoting other servers, no sharing of personal information and no voice "
                "modifiers."
            ),
        },
        {
            "titulo": "Mas o que nós somos? | So, what are we?",
            "texto": (
                "Somos uma comunidade totalmente focada em Ghost Recon, The Division e outros jogos da saga Tom "
                "Clancy's, aqui para dicas e ajuda em missões e raids, onde você também verá: notícias, jogatinas "
                "e dicas para aumentar a sua experiência na saga Tom Clancy's.\n\n"
                "We are a community fully focused on Ghost Recon, The Division and other games from the Tom "
                "Clancy's saga, here for tips and help with missions and raids, where you will also find: news, "
                "gaming sessions and tips to improve your experience in the Tom Clancy's saga.\n\n"
                "**Aproveite bem o servidor e até a próxima! | Make good use of the server and see you next "
                "time!**\n\n"
                "-# Comunidade de fãs, sem afiliação com a Ubisoft. | Fan community, not affiliated with Ubisoft."
            ),
        },
    ],
    "anuncios": [{
        "titulo": "📢 Canal de anúncios oficiais",
        "texto": (
            "Aqui a equipe publica os **comunicados oficiais**: operações, eventos, mudanças no servidor e avisos "
            "importantes. Somente a equipe publica neste canal."
        ),
        "campos": [
            ("🔔 Quer ser avisado?", "Escolha **Eventos** e **Operações** em **Canais e Cargos**.", True),
            ("🛡️ Segurança", "A equipe **nunca** pede senha, código ou pagamento por DM.", True),
        ],
    }],
    "comece_aqui": [
        {
            "titulo": "🧭 Briefing do operador",
            "texto": "Tudo o que você precisa para começar, em poucos passos.",
            "campos": [
                ("🎭 1. Escolha jogos, plataformas e estilo",
                 "Abra **Canais e Cargos** no topo da lista e marque o que você joga (Wildlands, Breakpoint, Siege), "
                 "sua plataforma (PC, Xbox, PlayStation) e seu estilo (Casual, Furtivo, Tático, Livre). Dá para "
                 "mudar quando quiser.", False),
                ("🎯 2. Monte ou entre num squad",
                 "• Em {c:abrir_squad}, clique em **Abrir squad**, escolha o jogo e dê um nome: o bot cria uma "
                 "**call exclusiva** para o seu esquadrão.\n"
                 "• Em {c:squad_partida}, veja os squads abertos e clique em **✅ Eu vou** para entrar.", False),
                ("🔥 3. Raids e operações",
                 "Raids organizadas ficam em {c:squad_raid} e a raid da semana em {c:raid_semanal}. Antes de "
                 "fechar a equipe, confirme jogo, plataforma, versão e requisitos.", False),
            ],
        },
        {
            "titulo": "🎙️ Voz, lives, apoio e ajuda",
            "campos": [
                ("🔊 4. Salas de voz",
                 "• Para jogar em grupo: abra um squad em {c:abrir_squad}.\n"
                 "• Para conversar: {c:voz_breakpoint}, {c:voz_wildlands} e {c:voz_bate_papo}.\n"
                 "• Rainbow Six Siege: **Radio 01** a **Radio 04**.", False),
                ("🔴 5. Divulgue sua live", "Em {c:lives}, seguindo as regras fixadas.", True),
                ("💡 6. Envie sugestões", "Use o modelo fixado em {c:sugestoes}.", True),
                ("💎 7. Apoie a comunidade",
                 "Quem **impulsiona o servidor vira VIP** automaticamente. Para outras formas de ajudar, veja "
                 "{c:contribuicao}.", False),
                ("🆘 8. Precisa de ajuda?",
                 "• Servidor, acesso e cargos: {c:suporte_geral}\n"
                 "• Dicas e problemas dos jogos: {c:suporte_dicas}\n"
                 "• Perguntas gerais: {c:duvidas}\n"
                 "• Falar com a equipe em **privado**: botão em {c:denuncias}", False),
            ],
        },
    ],
    # ------------------------------------------------------------------ VIPs
    "vips": [{
        "titulo": "🏅 Área VIP",
        "texto": (
            "Espaço de quem **fortalece a Operação Brasil**. Todos podem ler; membros **💎 VIP** e a equipe "
            "conversam aqui."
        ),
        "campos": [
            ("🚀 Impulsione o servidor", "Todo **booster vira VIP automaticamente**, enquanto o impulso durar.", True),
            ("🤝 Contribua", "Arte, conteúdo, eventos, parcerias e mais: fale com a equipe em {c:contribuicao}.",
             True),
            ("ℹ️ Sobre o cargo",
             "O VIP é um **reconhecimento**: destaque na lista de membros e acesso para conversar aqui. Não dá "
             "poderes de moderação ou administração.", False),
            ("🛡️ Segurança", "A equipe **nunca** pede senha, código ou dados de cartão por DM.", False),
        ],
    }],
    # ------------------------------------------------------------------ Alistamento
    "squad_raid": [{
        "titulo": "🔥 Como publicar em squad-raid",
        "texto": (
            "Copie o modelo, preencha e publique. Combine os detalhes numa **thread** da sua publicação.\n"
            "```\n"
            "Jogo:\n"
            "Plataforma:\n"
            "Atividade/Raid:\n"
            "Data e horário (Brasília):\n"
            "Vagas:\n"
            "Requisitos (nível, equipamento, experiência):\n"
            "Voz: (sala do servidor)\n"
            "Contato: (responda na thread)\n"
            "```"
        ),
        "campos": [
            ("📌 Importante",
             "• Cada raid tem regras e limites próprios: informe os da sua.\n"
             "• Confirme a compatibilidade entre plataformas e versões antes de fechar o grupo.\n"
             "• Uma publicação a cada 5 minutos. Não repita o anúncio; edite o original.\n"
             "• Para jogar agora, sem agendar, prefira abrir um squad em {c:abrir_squad}.", False),
        ],
    }],
    # ------------------------------------------------------------------ Chat
    "geral": [{
        "titulo": "💬 Papo geral",
        "texto": "Conversa livre da comunidade: jogos, novidades, resenha e amizade. Bem-vindo à base! 🇧🇷",
        "campos": [
            ("📌 Lembretes",
             "• Respeite as {c:regras}: sem política, religião, futebol ou ofensas.\n"
             "• Procurando grupo? {c:abrir_squad}\n"
             "• Memes e prints? {c:fotos_memes}", False),
        ],
    }],
    "fotos_memes": [{
        "titulo": "📷 Fotos e memes",
        "texto": "Prints, fotos do modo foto, memes e momentos engraçados das operações.",
        "campos": [("📌 Lembretes",
                    "• Nada ofensivo, sensual ou com dados pessoais de ninguém.\n"
                    "• Vídeos de jogadas vão para {c:clips}.", False)],
    }],
    "outfits": [{
        "titulo": "👕 Outfits",
        "texto": "Mostre o seu operador: loadouts, camuflagens, combinações e builds de visual.",
        "campos": [("💡 Dica", "Diga o **jogo** e, se quiser, onde conseguiu cada peça. Isso ajuda quem quer "
                               "montar algo parecido.", False)],
    }],
    "sugestoes": [{
        "titulo": "💡 Como enviar uma sugestão",
        "texto": (
            "```\n"
            "Sugestão:\n"
            "Por que ajudaria a comunidade:\n"
            "Como poderia funcionar:\n"
            "```\n"
            "Uma sugestão por mensagem. Discuta na **thread** da sugestão e use reações para mostrar apoio. "
            "A equipe avalia as ideias e comunica as decisões em {c:anuncios}."
        ),
    }],
    "comandos": [{
        "titulo": "🤖 Como usar o bot Operação Brasil",
        "texto": "O bot funciona por **botões** nos canais. Não precisa decorar comando nenhum.",
        "campos": [
            ("🎯 Squads", "{c:abrir_squad} para abrir · {c:squad_partida} para entrar", True),
            ("🚨 Falar com a equipe", "Botão em {c:denuncias}", True),
            ("📤 Enviar mods", "Botão em {c:publicar_mod}", True),
            ("💎 Contribuir / VIP", "Botão em {c:contribuicao}", True),
            ("🔒 Privacidade",
             "Atendimentos acontecem em **canais privados**. Ao encerrar, você recebe o histórico por DM, "
             "protegido por senha.", False),
        ],
    }],
    "clips": [{
        "titulo": "🎬 Clips e highlights",
        "texto": "Compartilhe jogadas marcantes, infiltrações, eliminações e momentos engraçados.",
        "campos": [("📌 Como postar",
                    "• Envie o vídeo/imagem ou o link (YouTube, Twitch, Medal etc.).\n"
                    "• Diga o jogo e, se quiser, a plataforma.\n"
                    "• Comentários vão na **thread** do clipe.\n"
                    "• Divulgação de lives fica em {c:lives}.", False)],
    }],
    "lives": [{
        "titulo": "🔴 Regras de divulgação de lives",
        "texto": (
            "• Uma publicação por transmissão: **link + jogo + o que você está fazendo**.\n"
            "• Modo lento de **6 horas** para membros.\n"
            "• Somente lives dos jogos da comunidade ou da própria comunidade.\n"
            "• Não repita a divulgação em outros canais nem por DM.\n"
            "• Conversas sobre a live vão para {c:geral}."
        ),
    }],
    # ------------------------------------------------------------------ Ajuda
    "suporte_geral": [{
        "titulo": "🛠️ Suporte do servidor",
        "texto": (
            "Problemas com **acesso, cargos, canais ou organização** do servidor? Descreva aqui e, se possível, "
            "envie um print (sem dados pessoais)."
        ),
        "campos": [("🔒 Assunto sensível?", "Não use este canal: abra um atendimento privado em {c:denuncias}.",
                    False)],
    }],
    "suporte_dicas": [{
        "titulo": "🧠 Dicas e problemas dos jogos",
        "texto": "Dúvidas técnicas, configurações, desempenho, conexão e problemas comuns dos jogos.",
        "campos": [("📌 Para ajudarem você",
                    "Informe **jogo, plataforma** e o que já tentou. Nunca compartilhe dados de conta nem arquivos "
                    "executáveis.", False)],
    }],
    "duvidas": [{
        "titulo": "❓ Dúvidas",
        "texto": (
            "Perguntas sobre a comunidade, os jogos, os squads e as operações. Antes de perguntar, dê uma olhada "
            "em {c:comece_aqui}."
        ),
    }],
    # ------------------------------------------------------------------ Mods
    "mods_publicados": [{
        "titulo": "📦 Mods publicados",
        "texto": (
            "Aqui aparecem só os mods **revisados e aprovados** pela equipe. Nenhum mod é publicado "
            "automaticamente."
        ),
        "campos": [
            ("📤 Quer enviar um mod?", "Use o botão em {c:publicar_mod}.", True),
            ("📋 Critérios", "{c:regras_mods}", True),
            ("⚠️ Atenção",
             "Mesmo aprovados, mods são usados **por sua conta e risco**: faça backup e confira a "
             "compatibilidade com sua versão e plataforma.", False),
        ],
    }],
    "discussao_mods": [{
        "titulo": "🗨️ Discussão sobre mods",
        "texto": "Compatibilidade, instalação, atualizações e experiências com mods de Wildlands e Breakpoint.",
        "campos": [("📌 Regras",
                    "• **Não envie executáveis** nem arquivos de origem desconhecida; prefira os links oficiais "
                    "dos autores.\n"
                    "• Dê crédito aos autores.\n"
                    "• Nada de cheats, trapaça online ou conteúdo pirateado.\n"
                    "• Mods podem violar termos de uso ou causar problemas: use por sua conta e risco.", False)],
    }],
    "regras_mods": [{
        "titulo": "📋 Regras para envio e publicação de mods",
        "campos": [
            ("✅ Critérios de aprovação",
             "1. Mod para Ghost Recon Wildlands ou Breakpoint, com jogo e versão compatíveis informados.\n"
             "2. Link para a página oficial do autor ou repositório reconhecido, sem encurtadores.\n"
             "3. Créditos claros ao(s) autor(es) e respeito à licença e às permissões de distribuição.\n"
             "4. Instruções de instalação e de remoção.\n"
             "5. Sem cheats, vantagens online injustas, malware, conteúdo pirateado ou ofensivo.", False),
            ("🔎 Processo",
             "• Todo envio passa por análise da equipe; nada é publicado automaticamente.\n"
             "• Quem envia não pode aprovar o próprio envio.\n"
             "• Links suspeitos, executáveis desconhecidos ou falta de créditos levam a análise adicional ou "
             "recusa.\n"
             "• A equipe pode aprovar, recusar ou pedir alterações.", False),
            ("📤 Para enviar", "Use o botão **Enviar mod** em {c:publicar_mod}.", False),
        ],
    }],
    # ------------------------------------------------------------------ Jogos
    "chat_breakpoint": [{
        "titulo": "💀 Ghost Recon Breakpoint",
        "texto": "Missões, atualizações, equipamentos, builds e cooperação em Auroa.",
        "campos": [
            ("🎯 Formar grupo", "Abra um squad em {c:abrir_squad}", True),
            ("🔥 Raids", "{c:squad_raid} · {c:raid_semanal}", True),
            ("🔊 Conversar", "{c:voz_breakpoint}", True),
        ],
    }],
    "raid_semanal": [{
        "titulo": "📝 Raid semanal",
        "texto": "Planejamento, inscrições e organização da raid semanal.",
        "campos": [
            ("📋 Como funciona",
             "1. Um **Organizador de Operações** publica data, horário, plataforma e requisitos.\n"
             "2. Para participar, responda na **thread** do anúncio com jogo, plataforma e disponibilidade.\n"
             "3. O organizador confirma a equipe na própria thread.", False),
            ("⚠️ Antes de formar a equipe",
             "Confirme compatibilidade de plataforma e versão, requisitos e o limite de participantes da "
             "atividade.", False),
        ],
    }],
    "chat_wildlands": [{
        "titulo": "🌿 Ghost Recon Wildlands",
        "texto": "Missões, campanha cooperativa, exploração, equipamentos, dicas e experiências na Bolívia.",
        "campos": [
            ("🎯 Formar grupo", "Abra um squad em {c:abrir_squad}", True),
            ("🔊 Conversar", "{c:voz_wildlands}", True),
            ("💡 Dica", "Confirme plataforma e versão antes de chamar alguém.", True),
        ],
    }],
    # ------------------------------------------------------------------ Equipe
    "chat_equipe": [{
        "titulo": "🔒 Canal da equipe",
        "texto": "Canal privado da administração, moderação e organização de operações.",
        "campos": [
            ("🤖 Comandos do bot (só equipe)",
             "`/tickets paineis` · `/tickets info`\n"
             "`/squads lista` · `/squads encerrar` · `/squads painel` · `/squads remover-salas`\n"
             "`/servidor verificar` · `/servidor publicar`", False),
            ("🗂️ Registros", "Ações do bot e de moderação em {c:logs_moderacao}; transcripts em {c:relatorios}.",
             False),
            ("🔐 Segurança", "Ative a **autenticação em dois fatores (2FA)** na sua conta.", False),
        ],
    }],
    "logs_moderacao": [{
        "titulo": "🗂️ Logs de moderação",
        "texto": (
            "O bot registra aqui, **automaticamente**, a abertura e as ações dos tickets (denúncias, mods e "
            "contribuições) e as concessões de VIP."
        ),
        "campos": [
            ("✍️ Punições manuais",
             "Registre advertências, castigos, expulsões e banimentos com o modelo:\n"
             "```\nData:\nMembro (ID):\nAção:\nMotivo:\nResponsável:\n```", False),
            ("📚 Auditoria", "O registro de auditoria do Discord continua em **Configurações do Servidor**.", False),
        ],
    }],
    "relatorios": [{
        "titulo": "📑 Relatórios da equipe",
        "texto": (
            "Os **transcripts** dos tickets encerrados chegam aqui, com o botão **🔓 Visualizar transcript** e a "
            "senha em spoiler."
        ),
        "campos": [
            ("✍️ Ocorrências e decisões",
             "Registre só os dados necessários:\n"
             "```\nData:\nResumo:\nEnvolvidos (IDs):\nProvas (links internos):\nDecisão:\n```", False),
        ],
    }],
}

# Títulos usados pelo antigo bot de configuração (para reconhecer e remover as mensagens antigas).
TITULOS_LEGADOS = {
    "Bem-vindo ao Ghost Recon Brasil", "📜 Normas de Conduta do Servidor | Server Conduct Standards",
    "Regras 1 a 4", "Regras 5 a 8", "Mas o que nós somos? | So, what are we?", "Canal de anúncios oficiais",
    "Comece aqui", "Salas de voz, lives e ajuda", "Área VIP", "Como publicar em #squad-raid",
    "Como publicar em #squad-partida", "Como montar um squad", "Como enviar uma sugestão",
    "Canal reservado para integrações futuras", "Clips e highlights", "Regras de divulgação de lives",
    "Suporte do servidor", "Dicas e problemas dos jogos", "Dúvidas", "Como falar com a equipe em privado",
    "Mods publicados", "Discussão sobre mods", "Regras para envio e publicação de mods",
    "Envio de mods para avaliação", "Ghost Recon Breakpoint", "Raid semanal", "Ghost Recon Wildlands",
    "Canal da equipe", "Logs de moderação", "Relatórios da equipe", "Regras", "Normas de Conduta",
}
