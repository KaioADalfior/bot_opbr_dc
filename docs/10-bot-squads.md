# 10 — Squads: #abrir-squad e #squad-partida

Módulo do bot **Operação Brasil** que monta esquadrões com **call de voz exclusiva**.

| Canal | Para que serve |
|---|---|
| `🎯｜abrir-squad` | Painel **🎮 Central de Esquadrões** com o botão **Abrir squad**, que funciona como o painel de tickets. O bot cria esse canal sozinho, logo acima de `squad-partida`. |
| `🎮｜squad-partida` | Recebe os **cards** dos squads abertos, onde o pessoal clica em **✅ Eu vou**. No topo fica um aviso fixo apontando para `abrir-squad`. |

## Como funciona para o membro

1. Em `🎯｜abrir-squad`, clica em **🎯 Abrir squad** no painel **🎮 Central de Esquadrões**.
2. Numa janela que só ele vê, escolhe nos menus:
   - **Jogo:** 💀 Breakpoint, 🌿 Wildlands ou 👮 Rainbow Six Siege.
   - **Plataforma:** 🖥️ PC, 🟩 Xbox ou 🟦 PlayStation.
   - **Modo:** muda conforme o jogo. Por exemplo, Campanha cooperativa, Exploração, Ghost War, Modo Fantasma, Ranqueada...
   - **Estilo** (opcional): 😎 Casual, 🌑 Furtivo, 🎯 Tático ou 🌎 Livre.
3. Clica em **Continuar** e preenche:
   - **nome do squad**, que vira o nome da call;
   - seu nick ou ID no jogo (opcional);
   - observações (opcional).
4. O bot:
   - cria a call **`💀 Nome do Squad`** na categoria `╭─── 🎮 Squads Ativos`. Todos veem a call, mas **só o squad e a equipe entram**. O limite é de 4 pessoas no Ghost Recon e 5 no Siege;
   - publica o **card** do squad em `🎮｜squad-partida`;
   - se o líder já estiver em alguma call, **move ele direto** para a call nova.
5. Outros jogadores clicam em **✅ Eu vou** no card. Cada um ganha acesso à call e é movido para lá se já estiver em voz. O card mostra quem está no squad e quem está na call (🔊).
6. Quando lota, o botão vira **Esquadrão completo**.

**Botões do card**

| Botão | Quem usa | O que faz |
|---|---|---|
| ✅ Eu vou | Qualquer membro | Entra no squad e ganha acesso à call. |
| 🚪 Sair | Integrantes | Libera a vaga e sai da call. Se o líder sair, a liderança passa para o próximo. Se ele estiver sozinho, o squad acaba. |
| 🔊 Ir para a call | Todos | Atalho para a call. |
| 🔒 Encerrar | Líder ou equipe | Apaga a call e o card. |

**Regras automáticas**

- Cada membro participa de **1 squad por vez**, como líder ou integrante.
- É preciso esperar 60 segundos entre um squad aberto e o próximo.
- Ficam no máximo 25 squads abertos ao mesmo tempo (`SQUAD_MAX`).
- A call é **apagada sozinha** depois de **10 minutos vazia** (`SQUAD_VAZIO_MIN`). Isso também vale se ninguém entrar logo após a criação.
- Se alguém apagar a call na mão, o card some.
- Os membros **não digitam** em `abrir-squad` nem em `squad-partida`: os canais ficam só com o painel, o aviso e os cards ativos. Para desligar isso, use `SQUAD_TRAVAR_CANAL=0`.
- O nome do squad aceita de 3 a 24 caracteres, sem links nem menções.

**Comandos da equipe** (exigem "Gerenciar servidor")

- `/squads painel`: publica ou atualiza o painel.
- `/squads lista`: mostra os squads ativos.
- `/squads encerrar numero:12`: encerra um squad.
- `/squads remover-salas`: apaga as antigas salas fixas (veja abaixo).

## Remover as salas fixas de Breakpoint e Wildlands

As categorias `╭─── 💀 Breakpoint | Salas` e `╭─── 🌿 Wildlands | Salas` (24 calls, como `Breakpoint PC 1`) foram substituídas pelos squads.

1. No Discord, digite `/squads remover-salas`.
2. O bot mostra, só para você, o que será apagado. Clique em **🗑️ Apagar as salas**.

**Proteções**

- Só apaga calls com nome no padrão `Breakpoint/Wildlands PC/XBOX/PS N` dentro dessas duas categorias.
- Calls **com gente dentro** são puladas. Rode o comando de novo depois.
- A categoria só é apagada se ficar vazia.
- `💀 Breakpoint Geral`, `🌿 Wildlands Geral`, `🔊 Bate Papo` e as `Radios` do Siege **não são tocados**.
- O registro fica em `logs-de-moderação`.
- **Não dá para desfazer.**

O script de configuração (`main.py`) também foi atualizado para **não recriar** essas salas. O `validar` agora confere se elas foram removidas.

**Depois:** em **Configurações do Servidor › Onboarding**, confira a pergunta de plataforma, que apontava para essas salas. As opções continuam dando os cargos de plataforma. Se quiser, adicione `🎯｜abrir-squad` aos canais padrão.

## Ativar (uma vez)

O bot precisa de permissões novas: **Conectar, Falar, Vídeo, Usar detecção de voz e Mover membros**.

1. Pare o bot com **Ctrl+C**.
2. Rode `python -m bot convite`, abra o link e clique em **Autorizar** de novo. Isso atualiza as permissões do cargo do bot.
3. Rode `python -m bot`. No log deve aparecer `Canal #🎯｜abrir-squad criado.` e `Painel de squads publicado em #🎯｜abrir-squad`.
4. Opcional: rode `python main.py mensagens` com o Configurador para atualizar a mensagem antiga fixada no canal, que ainda pede para "usar o modelo".

Se o log mostrar `Squads: o bot precisa das permissões [...]`, refaça o passo 2.

## Roteiro de teste

- [ ] Abrir um squad estando numa call: você é movido para a call nova com o nome do squad.
- [ ] Uma conta comum clica em **Eu vou**: entra na call, e o card mostra 2/4.
- [ ] Uma terceira conta, sem clicar em Eu vou, tenta entrar na call: é bloqueada.
- [ ] Uma conta comum clica em **Encerrar**: recebe "Só o líder".
- [ ] O líder clica em **Sair**: a liderança passa para o próximo.
- [ ] Todos saem da call e, depois de cerca de 10 minutos, a call e o card somem.
