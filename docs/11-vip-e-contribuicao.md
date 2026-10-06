# 11 — VIP e contribuição

## O que o bot faz

| Onde | O que acontece |
|---|---|
| `💎｜contribuição` (categoria **🏅 VIPs**) | Painel **💎 Apoie a Operação Brasil**. O bot cria o canal sozinho, logo abaixo de `🏅｜vips`. Os membros só leem e clicam no botão. |
| Botão **💎 Quero contribuir** | Abre um menu com as formas de contribuir: 💸 Apoio financeiro, 🎬 Conteúdo e lives, 🎨 Arte e design, 🧭 Organizar eventos, 🤝 Parceria e ✨ Outra ideia. Em seguida, um formulário curto. |
| Canal privado `contribuicao-0001` | Conversa entre o membro e a equipe, como nos tickets de denúncia. |
| Botões da equipe no ticket | 🙋 Assumir · **💎 Conceder VIP** · ➖ Remover VIP · 🔒 Encerrar · 🔓 Reabrir |
| Ao encerrar | O transcript protegido por link e senha vai para o membro (DM) e para `relatórios`, igual aos outros tickets. |
| **Boost** | Quem **impulsiona o servidor vira VIP na hora**, e o bot agradece em `🏅｜vips`. Quando o impulso acaba, o VIP sai. |

**Regras de segurança**

- Só a equipe (Líder, Administração e Moderação) concede ou remove VIP. Ninguém altera o próprio VIP.
- O VIP dado pela equipe **não cai** quando um impulso acaba. Só perde o VIP quem o ganhou **por boost**.
- "Remover VIP" de quem está impulsionando é bloqueado, porque o VIP volta automaticamente enquanto o impulso durar.
- Cada membro pode ter **1 conversa de contribuição** aberta por vez.
- Toda concessão e remoção fica registrada em `logs-de-moderação`.
- O bot **não recebe pagamentos** e não pede dados de cartão. Se houver apoio financeiro, a forma é combinada pela equipe na conversa privada.

## Configurar (uma vez)

1. **Ligar a intent de membros.** No **Portal do Desenvolvedor**, abra a aplicação **Operação Brasil**, vá na aba **Bot** e, em **Privileged Gateway Intents**, ligue **SERVER MEMBERS INTENT**. Salve.
   - Sem isso, o bot não inicia: aparece o erro de intents e o bot explica o que fazer.
   - Para não usar o VIP automático, coloque `MEMBERS_INTENT=0` no `bot\.env`.
2. **Ordem dos cargos.** Em **Configurações do Servidor › Cargos**, arraste o cargo do bot **Operação Brasil** para **acima de 💎 VIP**. O Discord só deixa um bot dar cargos que estão abaixo do cargo dele. Se estiver errado, o log mostra `VIP: O cargo do bot (...) precisa ficar ACIMA de '💎 VIP'`.
3. Pare o bot com **Ctrl+C** e ligue de novo com `python -m bot`. No log deve aparecer:
   - `Canal #💎｜contribuição criado.`
   - `Painel contribuicao publicado em #💎｜contribuição`
   - `Pronto: VIP conferido.` Se já houver boosters, aparece também `VIP por boost sincronizado: +N`.

**Opcional:** o bot também confere os boosters a cada 6 horas, para o caso de algum evento de impulso ter sido perdido com o bot desligado.

## Roteiro de teste

- [ ] Uma conta comum clica em **Quero contribuir**, escolhe uma forma e envia. O canal privado `contribuicao-000X` aparece só para ela e para a equipe.
- [ ] Ela tenta abrir outra conversa e recebe "já tem uma conversa".
- [ ] Você clica em **💎 Conceder VIP**. Ela ganha o cargo, recebe uma DM e o registro aparece nos logs.
- [ ] Você clica em **🔒 Encerrar**. O transcript vai por DM e para `relatórios`, e o canal é apagado.
- [ ] Alguém impulsiona o servidor: recebe VIP e aparece o agradecimento em `🏅｜vips`.

## Ajustes em `bot\.env`

| Variável | Padrão | Para quê |
|---|---|---|
| `CARGO_VIP` | `vip` | Nome (sem emoji) ou ID do cargo VIP |
| `BOOST_DA_VIP` | `1` | `0` desliga o VIP automático para boosters |
| `MEMBERS_INTENT` | `1` | `0` se não quiser ligar a intent de membros (desliga o VIP por boost) |
| `MAX_CONTRIBUICOES_ABERTAS` | `1` | Conversas abertas por membro |
| `CANAL_CONTRIBUICAO` / `CANAL_VIPS` | `contribuição` / `vips` | Nome ou ID dos canais |
