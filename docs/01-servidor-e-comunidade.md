# 01 — Criar o servidor e configurá-lo como Comunidade

**Documentação oficial consultada em 03/10/2026:**

| Artigo | Última atualização indicada |
|---|---|
| [Ativar o Servidor da Comunidade](https://support.discord.com/hc/pt-br/articles/360047132851-Enabling-Your-Community-Server) | 03/06/2024 |
| [Ativando o Descobrir Servidores](https://support.discord.com/hc/pt-br/articles/360030843331-Enabling-Server-Discovery) | 23/07/2026 |
| [FAQ da Integração da Comunidade (Onboarding)](https://support.discord.com/hc/pt-br/articles/11074987197975-Community-Onboarding-FAQ) | 25/06/2026 |
| [Server Guide FAQ](https://support.discord.com/hc/en-us/articles/13497665141655-Server-Guide-FAQ) | 28/09/2023 |
| [Rules Screening FAQ](https://support.discord.com/hc/pt-br/articles/1500000466882-Rules-Screening-FAQ) | 23/10/2023 |
| [Activity Alerts + Security Actions](https://support.discord.com/hc/pt-br/articles/17439993574167-Activity-Alerts-Security-Actions) | 11/01/2024 |
| [Four Steps to a Super Safe Server](https://discord.com/safety/360043653152-four-steps-to-a-super-safe-server) | — |
| [Discord Server Setup Guide](https://support.discord.com/hc/en-us/articles/33023827550359-Discord-Server-Setup-Guide) | 02/07/2025 |

> A interface do Discord muda com frequência. Os nomes abaixo seguem a documentação em português; quando um item não estiver exatamente onde descrito, procure pelo nome em **Configurações do Servidor** (a barra lateral tem campo de busca em versões recentes) ou pelo equivalente em inglês entre parênteses.

**Ordem recomendada para este projeto:** criar o servidor (§1–3) → rodar o script `aplicar` ([docs/03](03-execucao-no-windows.md)) → ativar a Comunidade (§4–8) usando os canais que o script criou → `aplicar` de novo → demais etapas. Assim você não precisa deixar o Discord criar canais extras de regras e moderação.

---

## 1. Criar o servidor inicial

1. No aplicativo do Discord (desktop), clique no **+ (Adicionar um servidor)** na barra lateral esquerda.
2. Escolha **Criar o meu** (*Create My Own*) — não use modelos, para começar limpo.
3. Escolha **Para um clube ou comunidade** (*For a club or community*).
4. Nome: **Ghost Recon Brasil**. Ícone: pode adicionar agora ou depois (§2).
5. Clique em **Criar**.

O Discord cria automaticamente as categorias “Canais de texto” (`#geral`) e “Canais de voz” (`Geral`). **O script não mexe nelas.** Depois de validar a nova estrutura, apague-as manualmente se quiser (clique com o botão direito > Excluir) — exclusões são sempre manuais neste projeto.

## 2. Nome, ícone, descrição e identidade visual

1. Clique no nome do servidor (canto superior esquerdo) > **Configurações do Servidor** > **Perfil do Servidor** (*Server Profile*).
2. **Ícone:** imagem quadrada de pelo menos 512×512 px, com a identidade própria (veja [docs/07](07-identidade-visual.md)). **Não use o logotipo do Ghost Recon, da Ubisoft ou do Rainbow Six.**
3. **Banner e plano de fundo do convite:** dependem do nível de impulsos (*Boost*) do servidor; o próprio painel mostra o nível exigido. Prepare as artes, mas não conte com elas no início.
4. A **descrição pública** é preenchida depois de ativar a Comunidade (§12).

## 3. Acessar as configurações do servidor

- Desktop: clique no **nome do servidor** > **Configurações do Servidor**.
- Celular: toque no nome do servidor > **Configurações** (ícone de engrenagem).
- Várias opções (Onboarding, Configuração de Segurança, Guia do Servidor) **só podem ser configuradas no desktop**.

## 4. Ativar a Comunidade

Requisitos oficiais (o assistente ajusta os dois primeiros automaticamente):

1. **Nível de verificação:** membros precisam ter **e-mail verificado** antes de enviar mensagens.
2. **Filtro de conteúdo explícito:** verificar mídia de **todos os membros**.
3. **Canal de regras**.
4. **Canal de atualizações da comunidade** (para avisos do Discord a administradores e moderadores).
5. Cumprir as [Diretrizes da Comunidade](https://discord.com/guidelines).

Passo a passo:

1. **Configurações do Servidor** > **Ativar Comunidade** (*Enable Community*) > **Começar** (*Get Started*).
2. **Etapa 1 — Verificações de segurança:** marque as duas opções (e-mail verificado e verificação de mídia de todos os membros).
3. **Etapa 2 — Configuração básica:**
   - Canal de regras/diretrizes: selecione **`📜｜regras`** (não deixe o Discord criar um novo).
   - Canal de atualizações da comunidade: selecione **`🔒｜chat-da-equipe`** (privado da equipe).
4. **Etapa 3 — Finalizar:** confira as opções padrão — recomendado **Notificações padrão: somente @menções** e **remover permissões de moderação do @everyone** (o script já não as concede) — e aceite as Diretrizes.
5. Clique em **Concluir configuração** (*Finish Setup*).

Depois, rode `python main.py aplicar` novamente: o script converte `#anuncios` em **canal de anúncios** (só é possível com Comunidade ativa).

## 5. O que marcar em cada etapa (resumo)

| Etapa | Escolha | Por quê |
|---|---|---|
| Verificação | E-mail verificado (mínimo exigido) | Requisito da Comunidade. Considere **Médio** (conta com mais de 5 min) para dificultar contas descartáveis. |
| Filtro de mídia | Todos os membros | Requisito da Comunidade e da Descoberta. |
| Regras | `📜｜regras` | Canal somente leitura criado pelo script. |
| Atualizações | `🔒｜chat-da-equipe` | Privado; avisos do Discord não ficam públicos. |
| Notificações padrão | Somente @menções | Evita barulho em servidores públicos. |

## 6. Canal de regras

- Já criado pelo script: todos leem, só a equipe publica.
- O texto das regras é publicado por `python main.py mensagens` ([docs/06](06-mensagens-iniciais.md)).
- Para mudar o canal depois: **Configurações do Servidor** > **Visão geral da Comunidade** (*Community Overview*) > **Canal de regras ou diretrizes**.

## 7. Canal privado de atualizações da comunidade e moderação

- Use `🔒｜chat-da-equipe` (privado: somente Líder, Administração, Moderador e Organizador).
- Para mudar: **Visão geral da Comunidade** > **Canal de atualizações da comunidade**.
- Se preferir um canal só para avisos do Discord, peça e criamos `atualizacoes-discord` na categoria EQUIPE (não foi criado para não alterar a estrutura solicitada).

## 8. Verificação de segurança e filtro de conteúdo explícito

**Configurações do Servidor** > (seção Moderação) **Configuração de Segurança** (*Safety Setup*):

- **Nível de verificação:** pelo menos *Baixo* (e-mail verificado). *Médio* ou *Alto* (10 min no servidor) ajudam contra ataques; *Alto* atrasa novos membros honestos — teste com moderação.
- **Filtro de conteúdo explícito:** *Filtrar mensagens de todos os membros*.
- Configure também **AutoMod** (filtros de palavras, spam de menções e links suspeitos). Sugestão: bloquear menções em massa, palavras de golpe comuns (“nitro grátis”, “steam gift”) e termos como `.exe`, `.scr`, `.bat` em links.

## 9. Triagem de regras (Rules Screening)

1. **Configurações do Servidor** > **Configuração de Segurança** > **Proteção contra DM e Spam** > **Editar**.
2. Ative **“Membros devem aceitar regras antes de falar ou enviar DM”**.
3. Cadastre até **16 regras curtas** (resuma as 10 regras de `#regras`).
4. Requer Comunidade ativa. Membros verificados manualmente ignoram a triagem.

## 10. Proteção contra ataques (raids) e atividades suspeitas

1. **Configurações do Servidor** > **Configuração de Segurança** > **Proteção contra ataques e CAPTCHA**.
2. Ative a proteção, escolha o canal de alertas (`🗂️｜logs-de-moderação`) e mantenha o CAPTCHA para contas suspeitas durante ataques.
3. Em emergências: menu do servidor > **Ações de Segurança** > **Pausar convites** e/ou **Pausar Mensagens Diretas**.
4. Quem pode usar: quem tem Administrador, Expulsar, Castigar, Banir ou Gerenciar servidor (Líder, Administração e Moderador neste projeto).

## 11. Exigir 2FA para ações de moderação

1. **Antes:** o dono precisa ativar a autenticação em dois fatores na própria conta (**Configurações de Usuário** > **Minha Conta** > **Ativar autenticação em duas etapas**).
2. **Configurações do Servidor** > **Configuração de Segurança** > ative **exigir 2FA para ações de moderação** (*Require 2FA for moderator actions*).
3. Somente o **dono** pode ativar; a API não permite alterar isso, por isso é manual.
4. Peça a todos da equipe que ativem 2FA antes de receberem cargos de moderação. É também requisito da Descoberta.

## 12. Idioma, descrição, informações e identidade

**Configurações do Servidor** > **Visão geral da Comunidade**:

- **Idioma principal:** Português (Brasil).
- **Descrição do servidor** (aparece em convites e, se aprovado, no Explorar). Sugestão:

  > Comunidade brasileira de Ghost Recon Wildlands, Breakpoint e Rainbow Six Siege. Monte seu esquadrão no PC, Xbox ou PlayStation, participe de raids e operações e compartilhe seus melhores momentos. Nenhum operador fica para trás. Comunidade de fãs, sem afiliação com a Ubisoft.

## 13. Onboarding e Guia do Servidor

**Configurações do Servidor** > **Onboarding** (desktop). Detalhes completos em [docs/04](04-configuracao-manual.md#onboarding). Resumo:

- **Canais Padrão:** mínimo **7**, sendo **5 com envio liberado para @everyone**.
- **Perguntas de Personalização:** cada resposta atribui cargos e canais.
- **Guia do Servidor:** liberado depois de concluir Canais Padrão e Perguntas; tem mensagem de boas-vindas, **3 a 5 tarefas para novos membros** e **páginas de recursos** (canais somente leitura viram páginas). O Guia substitui a antiga Tela de Boas-vindas.
- Opcional: `python main.py onboarding` grava um rascunho com os canais e perguntas deste projeto.

## 14. Canais padrão para novos membros

Recomendados (12): `anuncios`, `boas-vindas`, `regras`, `comece-aqui`, `geral`, `squad-partida`, `squad-raid`, `duvidas`, `suporte-geral`, `suporte-dicas`, `denuncias`, `clips-e-highlights`. Destes, 7 aceitam mensagens do @everyone (`geral`, `squad-partida`, `squad-raid`, `duvidas`, `suporte-geral`, `suporte-dicas`, `clips-e-highlights`), atendendo à exigência de 5.

## 15. Perguntas de seleção

| Pergunta | Tipo | Opções → cargos (+ canais) |
|---|---|---|
| Quais jogos você joga? | Múltipla, obrigatória | Wildlands, Breakpoint, Siege → cargos de jogo (+ chats, raid semanal, salas gerais, Radios) |
| Em qual plataforma você joga? | Múltipla, obrigatória | PC, Xbox, PlayStation → cargos de plataforma (+ salas da plataforma) |
| Qual é o seu estilo de jogo? | Única, opcional | Casual, Furtivo, Tático, Livre |
| Quer receber avisos? | Múltipla, opcional | Eventos, Operações → cargos de notificação |
| O que mais te interessa? | Múltipla, opcional | Mods, Clips e lives, Memes e outfits, Apoiar a comunidade → canais |

## 16. Testar a experiência de um novo membro

1. No Onboarding, use **Visualizar** (*Preview*) em cada seção.
2. Teste real: crie um convite e entre com uma **conta secundária** (ou peça a um amigo). Confira: triagem de regras, perguntas, canais exibidos, que não consegue escrever em `#anuncios`/`#regras`/`#denuncias`, que não vê a categoria EQUIPE e que entra e fala nas salas de voz.
3. Alternativa sem conta extra: **Configurações do Servidor** > **Cargos** > selecione um cargo > **Ver servidor como cargo** (*View Server As Role*).

## 17. Convite de divulgação

1. Clique com o botão direito no canal `👋｜boas-vindas` > **Convidar pessoas** > **Editar link de convite**.
2. **Expirar depois de:** Nunca. **Número máximo de usos:** Sem limite. **Não** marque participação temporária.
3. Gere e guarde o link. Ele aponta para `boas-vindas`, o primeiro canal que o novo membro vê.
4. **Configurações do Servidor** > **Convites** lista e permite revogar convites. URL personalizada (vanity) depende do nível de impulsos.

## 18. Opções para tornar o servidor público

- **Imediato:** Comunidade ativa + convite permanente divulgado em suas lives, redes e perfis.
- **Sites de listagem de terceiros:** possíveis, mas confira as regras e a reputação de cada um.
- **Descobrir/Explorar do Discord:** só após cumprir os requisitos abaixo — **ativar a Comunidade NÃO coloca o servidor no Explorar.**

---

## Descoberta (Descobrir Servidores / Explorar)

Requisitos oficiais vigentes em 03/10/2026 (artigo atualizado em 23/07/2026):

| Requisito | Situação deste servidor |
|---|---|
| Comunidade ativada | ✅ **imediato** (§4) |
| Configurações de segurança (verificação, filtro de mídia) | ✅ **imediato** (§8) |
| **2FA exigida para moderação** | ✅ **imediato**, só o dono ativa (§11) |
| Nome, descrição e nomes de canais “limpos” (sem palavrões/conteúdo impróprio) | ✅ **imediato** — a estrutura usa nomes neutros |
| **Pelo menos 1.000 membros** | ⏳ depende de crescimento |
| **Pelo menos 8 semanas de existência** | ⏳ depende de tempo |
| **Requisitos de atividade** (o Discord não publica números exatos) | 🔁 verificar periodicamente |
| Cumprir as Diretrizes da Comunidade e os Termos | 🔁 contínuo |

**Onde encontrar:** **Configurações do Servidor** > **Descoberta** (*Discovery*) — a aba só aparece com a Comunidade ativa. Ela mostra uma lista de verificação com o que já foi cumprido. Quando todos os itens estiverem verdes, aparece a opção para **ativar a Descoberta**. A listagem continua sujeita a revisão e pode ser removida se os requisitos deixarem de ser atendidos.

**Verificar periodicamente:** mensalmente, abra a aba Descoberta e rode `python main.py validar` (itens D1–D3 do relatório mostram membros, idade do servidor e se a Descoberta está ativa).

**Preparando a apresentação pública**

- Descrição clara (§12), em português, citando jogos e plataformas e o aviso de “comunidade de fãs, sem afiliação com a Ubisoft”.
- Ícone próprio e legível; banner/splash quando o nível de impulsos permitir.
- Categorias de interesse e palavras-chave na aba Descoberta: jogos, cooperativo, tático, Brasil.

**O que evitar**

- Nomes que sugiram ser oficial (“Ghost Recon Oficial”, “Ubisoft Brasil”), logotipos da franquia.
- Palavrões, termos sexuais ou violentos no nome, descrição e nomes de canais.
- Canais públicos de “sorteio”, “nitro grátis”, compra/venda de contas ou divulgação ilimitada.
- Prometer benefícios VIP pagos que não existem.

**Não há garantia** de aprovação no Explorar mesmo cumprindo todos os requisitos.
