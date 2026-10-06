# 04 — Configuração manual após o script

Itens que a API não permite, que dependem do dono ou que é mais seguro fazer olhando a interface. Marque cada um ao concluir. Os nomes seguem a interface em português (entre parênteses, o nome em inglês para quando a tradução variar).

## Checklist

- [ ] 1. Comunidade ativada e `aplicar` executado de novo
- [ ] 2. Administrador no Líder Fundador e cargos atribuídos
- [ ] 3. Triagem de regras
- [ ] 4. Onboarding (canais padrão + perguntas)
- [ ] 5. Guia do Servidor
- [ ] 6. Canal de anúncios
- [ ] 7. Proteção contra ataques, AutoMod e alertas
- [ ] 8. 2FA para moderação
- [ ] 9. Eventos
- [ ] 10. Descrição, idioma e identidade
- [ ] 11. Convite público
- [ ] 12. Revisão de permissões e hierarquia
- [ ] 13. Limpeza dos canais padrão do Discord
- [ ] 14. Teste da experiência de entrada
- [ ] 15. Requisitos de Descoberta acompanhados
- [ ] 16. Bot temporário removido e token redefinido

---

## 1. Comunidade

Siga [docs/01](01-servidor-e-comunidade.md) §4 escolhendo `📜｜regras` e `🔒｜chat-da-equipe`. Em seguida: `python main.py aplicar` (converte `#anuncios`) e `python main.py validar` (itens M1–M8).

## 2. Líder Fundador e atribuição de cargos

1. **Configurações do Servidor** > **Cargos** > **Líder Fundador** > aba **Permissões** > ative **Administrador** > **Salvar**. (O bot não pode conceder Administrador.)
2. Atribua a você: lista de membros > botão direito no seu nome > **Cargos** > Líder Fundador. Como dono, você já tem controle total; o cargo serve para identificação e para outros líderes no futuro.
3. Equipe: atribua Administração, Moderador ou Organizador de Operações só a pessoas de confiança **com 2FA ativo**.
4. Membro/Novato/Veterano/Colaborador/VIP: atribuição manual pela equipe por enquanto. Alternativa para Novato automático: no Onboarding, inclua o cargo **Novato** em todas as opções da pergunta obrigatória de plataforma.

## 3. Triagem de regras

**Configuração de Segurança** (*Safety Setup*) > **Proteção contra DM e Spam** > **Editar** > ative **Membros devem aceitar regras antes de falar ou enviar DM**. Cadastre (até 16), resumindo as Normas de Conduta:

1. Proibido em salas públicas: política, religião, futebol, pornografia, óbitos, acidentes, ofensas, correntes e spam/links maliciosos.
2. Evite repetir a mesma mensagem.
3. Conflitos pessoais se resolvem fora do servidor; não exponha discussões.
4. Proibido divulgar outros servidores sem autorização.
5. Críticas construtivas são bem-vindas; você é responsável por elas.
6. Nas salas de voz de jogo, não atrapalhe o squad; conversa paralela vai para Bate Papo (GERAL).
7. Proibido modificador de voz ou mecanismos intrusivos.
8. Proibido divulgar informações pessoais de terceiros.

## 4. Onboarding {#onboarding}

**Configurações do Servidor** > **Onboarding** (desktop). Se você rodou `python main.py onboarding`, os itens já estarão preenchidos — revise e pule para o passo 4.

1. **Canais Padrão** (*Default Channels*): selecione `anuncios`, `boas-vindas`, `regras`, `comece-aqui`, `geral`, `squad-partida`, `squad-raid`, `duvidas`, `suporte-geral`, `suporte-dicas`, `denuncias`, `clips-e-highlights`. Regra oficial: no mínimo 7, sendo 5 com envio liberado ao @everyone (aqui são 7).
2. **Perguntas de Personalização** (*Customization Questions*) > **Adicionar uma pergunta**:

| Pergunta | Opções (cargos → canais) | Configuração |
|---|---|---|
| Quais jogos você joga? | ⛰️ Ghost Recon Wildlands → cargo *Ghost Recon Wildlands* → `chat-geral-wildlands`, `🌿 Wildlands Geral` · 🏝️ Ghost Recon Breakpoint → cargo *Ghost Recon Breakpoint* → `chat-geral-breakpoint`, `raid-semanal`, `💀 Breakpoint Geral` · 🧱 Rainbow Six Siege → cargo *Rainbow Six Siege* → `👮 Radio 01–04` | Permitir múltiplas respostas · Tornar obrigatório · Pergunte antes de um membro entrar |
| Em qual plataforma você joga? | 💻 PC → *PC* → `Breakpoint PC 1–4`, `Wildlands PC 1–4` · 🟩 Xbox → *Xbox* → salas xbox · 🟦 PlayStation → *PlayStation* → salas ps | Múltiplas · Obrigatória |
| Qual é o seu estilo de jogo? | Casual · Furtivo · Tático · Livre → cargo de mesmo nome | Uma resposta · Opcional |
| Quer receber avisos? | 📅 Eventos → *Notificações de Eventos* · 📡 Operações → *Notificações de Operações* + `raid-semanal` | Múltiplas · Opcional |
| O que mais te interessa? | 🧩 Mods → canais da categoria MODS · 🎬 Clips e lives → `clips-e-highlights`, `divulgacao-de-lives` · 😂 Memes e outfits → `fotos-e-memes`, `outfits` · 💎 Apoiar a comunidade → `vips`, `sugestoes` | Múltiplas · Opcional |

3. Canais não escolhidos continuam acessíveis em **Procurar canais** (*Browse Channels*). Os membros podem mudar respostas depois na aba **Canais e Cargos**.
4. Use **Visualizar** (*Preview*) e então **Ativar Onboarding**.

Observação: as plataformas indicam onde o membro joga; **não** significam que todos podem jogar juntos. A compatibilidade entre plataformas varia por jogo, modo e versão.

## 5. Guia do Servidor

Disponível depois de concluir Canais Padrão e Perguntas: **Onboarding** > **Guia do Servidor** (*Server Guide*).

- **Mensagem de boas-vindas:** “Bem-vindo ao Ghost Recon Brasil! Nenhum operador fica para trás. Escolha seus jogos, encontre seu esquadrão e boa operação.”
- **Tarefas para novos membros (3 a 5):**
  1. Leia as regras → `📜｜regras`
  2. Veja como começar → `🧭｜comece-aqui`
  3. Apresente-se → `💬｜geral`
  4. Encontre um esquadrão → `🎮｜squad-partida`
  5. Mostre um clipe → `🎬｜clips-e-highlights`
- **Páginas de recursos:** `📜｜regras`, `🧭｜comece-aqui`, `📋｜regras-para-mods` (canais somente leitura viram páginas).
- O Guia substitui a Tela de Boas-vindas; a triagem de regras continua aparecendo normalmente.

## 6. Canal de anúncios

- Confirme que `📢｜anúncios` aparece com o ícone de megafone (tipo Anúncio). Se não, rode `python main.py aplicar` com a Comunidade ativa.
- Ao publicar, use **Publicar** (*Publish*) se quiser que servidores que seguem o canal recebam a mensagem.
- Notificações: mencione `@Notificações de Eventos` ou `@Notificações de Operações` em vez de `@everyone` sempre que possível.

## 7. Proteção contra ataques, AutoMod e alertas

- **Configuração de Segurança** > **Proteção contra ataques e CAPTCHA**: ativar, canal de alertas `🗂️｜logs-de-moderação`.
- **Nível de verificação**: Médio recomendado; **Filtro de mídia**: todos os membros.
- **AutoMod** (mesma área): ativar bloqueio de spam de menções (ex.: 5+ menções), conteúdo suspeito de spam e palavras-chave personalizadas (golpes de Nitro, `.exe`, `.scr`, `.bat`, `.msi`, encurtadores suspeitos). Enviar alertas a `🗂️｜logs-de-moderação`.
- Em ataques: menu do servidor > **Ações de Segurança** > **Pausar convites** / **Pausar Mensagens Diretas**.

## 8. 2FA para moderação

Ative 2FA na sua conta e depois **Configuração de Segurança** > **exigir 2FA para ações de moderação**. Só o dono pode ativar; requisito da Descoberta.

## 9. Eventos

- Crie em: menu do servidor > **Criar evento** > local **Canal de voz** (ex.: `💀 Breakpoint Geral`) ou **Em outro lugar**.
- Organizador de Operações tem **Gerenciar eventos** e **Criar eventos**; divulga em `#raid-semanal`/`#squad-raid` mencionando os cargos de notificação.
- Para a raid semanal, use a opção de repetição do evento, se estiver disponível no seu aplicativo; caso contrário, crie um evento por semana.

## 10. Descrição, idioma e identidade

**Visão geral da Comunidade**: idioma Português (Brasil) e a descrição sugerida em [docs/01](01-servidor-e-comunidade.md) §12. Ícone e artes: [docs/07](07-identidade-visual.md).

## 11. Convite público

Botão direito em `👋｜boas-vindas` > **Convidar pessoas** > **Editar link de convite** > Expirar: **Nunca**, Usos: **Sem limite** > **Gerar novo link**. Divulgue esse link nas lives e redes.

## 12. Revisão de permissões e hierarquia

1. **Cargos**, ordem final recomendada (de cima para baixo): Líder Fundador, Administração, Moderador, Organizador de Operações, [cargos de bots futuros], VIP, Veterano, Colaborador, Membro, Novato, jogos, plataformas, estilos, notificações. O script já ordena os cargos do projeto entre si.
2. Bots futuros: coloque o cargo de cada bot **logo acima** dos cargos que ele precisa gerenciar e **abaixo** da equipe. Nunca dê Administrador.
3. Confira [matriz-de-permissoes.md](matriz-de-permissoes.md) e use **Ver servidor como cargo** para Membro, VIP e Moderador.
4. `@everyone` (aba Cargos > @everyone): recomendado desativar **Mencionar @everyone, @here e todos os cargos** no nível do servidor também (o script já bloqueia nos canais do projeto, mas não altera o @everyone global para não afetar canais antigos).
5. Ajustes finos: modo lento em `#divulgacao-de-lives` (6 h), `#squad-raid`/`#squad-partida` (5 min), `#sugestoes` (2 min), `#raid-semanal` (1 min), `#clips-e-highlights` (30 s). Mude em **Editar canal** > **Modo lento** ou em `gr_setup\estrutura.py` e rode `aplicar`.
6. Limites de salas de voz: desativados de propósito. Para ativar (4 para Breakpoint/Wildlands, 5 para Siege), mude `APLICAR_LIMITES_DE_VOZ = True` em `gr_setup\estrutura.py` e rode `aplicar`.

## 13. Limpeza dos canais padrão do Discord

Após validar, apague manualmente as categorias “Canais de texto” e “Canais de voz” criadas pelo Discord (botão direito > **Excluir canal**/**Excluir categoria**). O script nunca apaga nada.

## 14. Teste da experiência de entrada

Com uma conta secundária (ou um amigo):

- [ ] Recebe a triagem de regras e as perguntas do Onboarding.
- [ ] Vê `boas-vindas`, `regras`, `comece-aqui`, `anuncios` e não consegue escrever neles.
- [ ] Não vê a categoria EQUIPE.
- [ ] Vê a categoria MODS, conversa só em `discussao-mods`.
- [ ] Escreve em `geral`, `squad-partida` (com modo lento) e `duvidas`; não escreve em `denuncias`, `comandos`, `publicar-mod`.
- [ ] Entra e fala em `breakpoint-pc-1` e `Radio 1`; não consegue silenciar/mover ninguém.
- [ ] Publica em `divulgacao-de-lives` e não consegue publicar de novo antes de 6 h.
- [ ] Não consegue mencionar `@everyone`.

## 15. Descoberta

Acompanhe mensalmente em **Configurações do Servidor** > **Descoberta** e pelos itens D1–D3 de `python main.py validar`. Requisitos e cuidados: [docs/01](01-servidor-e-comunidade.md#descoberta-descobrir-servidores--explorar).

## 16. Remover o bot temporário

[docs/02](02-bot-temporario.md) §6.
