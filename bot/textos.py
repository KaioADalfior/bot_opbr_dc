"""Textos exibidos pelo bot (português brasileiro)."""

COR = 0x38BDF8
COR_OK = 0x22C55E
COR_ALERTA = 0xF59E0B
COR_ERRO = 0xEF4444
COR_NEUTRA = 0x64748B

PAINEL_DENUNCIA = {
    "titulo": "🚨 Fale com a equipe em privado",
    "texto": (
        "Precisa denunciar algo ou tratar de um assunto sensível com a equipe?\n\n"
        "Clique em **Abrir atendimento privado**. Um canal privado será criado, visível **somente para "
        "você e para a equipe** (Líder, Administração e Moderação).\n\n"
        "• Descreva o ocorrido com calma; você pode enviar prints e provas **dentro do canal privado**.\n"
        "• Não exponha conflitos, nomes ou provas em canais públicos.\n"
        "• Use com responsabilidade: denúncias falsas também são infração.\n"
        "• A equipe **nunca** pede senha, código ou pagamento.\n\n"
        "Violações graves das regras do Discord também podem ser denunciadas diretamente ao Discord "
        "pelas ferramentas oficiais do aplicativo."
    ),
    "botao": "Abrir atendimento privado",
}

PAINEL_MOD = {
    "titulo": "📤 Central de envio de mods",
    "texto": (
        "Tem um mod de **Ghost Recon Wildlands** ou **Breakpoint** que vale a pena a comunidade conhecer?\n"
        "Envie para a equipe avaliar.\n\n"
        "**Como funciona**\n"
        "**1.** Clique em **Enviar mod**.\n"
        "**2.** Escolha o **jogo**, as **plataformas** e a **categoria** nos menus.\n"
        "**3.** Preencha nome, versão, link oficial, créditos e instruções.\n"
        "**4.** Um canal privado é aberto para você acompanhar a análise.\n"
        "**5.** Se for aprovado, o mod aparece no canal de mods publicados. ✅\n\n"
        "⛔ **Não são aceitos:** encurtadores de link, links diretos para executáveis, cheats ou trapaças "
        "online, conteúdo pirateado ou sem créditos ao autor.\n"
        "🛡️ O bot **nunca baixa nem executa** arquivos. Toda publicação passa pela equipe."
    ),
    "botao": "Enviar mod",
}

AVISO_LOCK_AUTOR = "Este atendimento foi finalizado. Você ainda pode ler o histórico, mas não enviar mensagens."

PAINEL_SQUAD = {
    "titulo": "🎮 Central de Esquadrões",
    "intro": ("Monte seu squad em segundos e ganhe uma **call de voz exclusiva** com o nome que você escolher. "
              "Chega de procurar sala vazia: o esquadrão é seu."),
    "passos": (
        "`1` Clique em **🎯 Abrir squad**\n"
        "`2` Escolha **jogo**, **plataforma**, **modo** e **estilo**\n"
        "`3` Dê um **nome** ao squad (vira o nome da call)\n"
        "`4` O card vai para {partida} e o pessoal entra com **✅ Eu vou**"
    ),
}

PAINEL_CONTRIBUICAO = {
    "titulo": "💎 Apoie a Operação Brasil",
    "texto": (
        "A comunidade é feita por fãs, para fãs. Se você quer ajudar a manter o servidor, os eventos e as "
        "operações funcionando, existem duas formas:"
    ),
    "beneficios": (
        "• Cargo **💎 VIP** em destaque na lista de membros\n"
        "• Acesso para conversar no chat **🏅 VIPs**\n"
        "• Nosso reconhecimento eterno 🫡"
    ),
    "seguranca": (
        "A conversa acontece num **canal privado** com a equipe (Líder, Administração e Moderação). "
        "A equipe **nunca** pede senha, código ou dados do seu cartão."
    ),
    "botao": "Quero contribuir",
}
