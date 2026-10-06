# 08 — Plano para os bots futuros

Nada aqui foi implementado. Este é o roteiro para a próxima fase, com o que a estrutura já deixou preparado.

## Princípios para qualquer bot

1. **Uma aplicação por função** (ou um bot modular), cada uma com **permissões mínimas** e **sem Administrador**.
2. Cargo do bot **acima** apenas dos cargos que ele precisa gerenciar e **abaixo** da equipe.
3. Token em variável de ambiente/cofre, nunca no código; hospedagem com reinício automático e logs sem segredos.
4. Permissões de canal do bot adicionadas só nos canais que ele usa (o script do projeto preserva essas permissões ao rodar de novo).
5. Antes de anunciar em `#anuncios`, testar em servidor de testes e atualizar as mensagens dos canais (`gr_setup\mensagens.py`).
6. Biblioteca sugerida para bots online: **discord.py 2.7+** (Python), com comandos de barra e componentes (botões, modais).

## Bots e integrações planejados

| Bot | Canais preparados | Como encaixar | Permissões típicas |
|---|---|---|---|
| **Moderação / logs** | `🗂️｜logs-de-moderação`, `📑｜relatórios` | Registrar castigos, banimentos, mensagens apagadas e entradas/saídas. Complementa o AutoMod nativo. | Ver auditoria, Gerenciar mensagens, Castigar, Expulsar, Banir (se for executar punições) |
| **Denúncias / tickets** | `🚨｜denúncias` | Botão “Falar com a equipe” no canal → **thread privada** ou canal privado por ticket, visível só ao autor e à equipe. Transcrição salva em `📑｜relatórios`. Depois, atualizar a mensagem de `#denuncias`. | Criar threads privadas, Gerenciar threads, Enviar mensagens, Gerenciar canais (se usar canais) |
| **LFG (procura de grupo)** | `🔥｜squad-raid`, `🎮｜squad-partida`, `📝｜raid-semanal` | Comando/botão com formulário (jogo, plataforma, horário, vagas) → publicação padronizada com botões Entrar/Sair, lista de espera e lembrete. Considere converter os canais para **fórum** com tags quando o bot existir. | Enviar mensagens, Inserir links, Criar threads públicas, Gerenciar threads |
| **Salas de voz temporárias** | categorias de salas por plataforma | Canal “➕ Criar sala” que cria uma sala temporária e a apaga quando esvazia. Decidir com você se substitui ou complementa as 24 salas fixas (nada é removido sem sua decisão). | Gerenciar canais, Mover membros, Conectar |
| **Envio de mods** | `📤｜publicar-mod`, `📦｜mods-publicados`, `📋｜regras-para-mods` | `/enviar-mod` ou botão → modal (nome, jogo, versão, link oficial, autor/créditos, instruções) → ticket privado → fila da equipe com botões **Aprovar / Rejeitar / Pedir alterações / Encerrar / Reabrir** → publicação controlada em `mods-publicados` → registro em `logs-de-moderacao`. Regras: autor não aprova o próprio envio; detecção de duplicados; sinalizar encurtadores, executáveis e falta de créditos; **nunca baixar ou executar arquivos**; tratamento de rejeitados/abandonados (prazo de expiração). | Enviar mensagens, Inserir links, Criar threads privadas, Gerenciar threads |
| **Divulgação de lives** | `🔴｜divulgação-de-lives` | Integração com APIs oficiais (Twitch EventSub, YouTube Data API) para avisar quando **você** entrar ao vivo; para membros, cadastro opcional e limite de frequência. Verificar regras e cotas de cada plataforma. Até lá, publicação manual. | Enviar mensagens, Inserir links, Mencionar cargos de notificação (só se você quiser) |
| **Níveis / reconhecimento** (opcional) | — | Atribuir Membro/Veterano por tempo ou participação. | Gerenciar cargos (abaixo do bot) |
| **Comandos gerais** | `🤖｜comandos` | Liberar envio no canal (`SEND_MESSAGES` para @everyone, com modo lento) quando houver comandos reais. | Usar comandos de aplicativos |

## Seleção de cargos

O **Onboarding nativo** já substitui um bot de seleção de jogos, plataformas, estilos e notificações. Não é necessário bot para isso.

## Checklist para ativar cada bot

- [ ] Criar aplicação, desligar *Public Bot*, ativar apenas os *intents* necessários.
- [ ] Gerar convite com permissões mínimas e autorizar.
- [ ] Posicionar o cargo do bot na hierarquia.
- [ ] Adicionar permissões de canal só onde necessário.
- [ ] Testar com contas de membro, VIP e moderador.
- [ ] Atualizar o texto do canal e anunciar em `#anuncios`.
- [ ] Registrar em `📑｜relatórios` o que foi ativado e quem administra o bot.
