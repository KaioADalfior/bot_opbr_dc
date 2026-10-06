# 12 — Mensagens dos canais e validação

O bot **Operação Brasil** agora é o dono de **todas as mensagens dos canais**. O texto fica em `bot/conteudo.py`. Cada canal recebe:

- um **banner** no visual do servidor, na cor da categoria;
- embeds organizados em blocos e campos;
- o rodapé "Ghost Recon® | Operação Brasil".

| Canal | O que aparece |
|---|---|
| Canais de texto comuns (regras, comece-aqui, geral, suporte...) | Banner + mensagem fixa |
| `denúncias`, `publicar-mod`, `abrir-squad`, `contribuição` | O **painel com botões** do módulo |
| `squad-partida` | Aviso fixo + cards dos squads abertos |

## Primeira vez: trocar as mensagens antigas

1. **Atualize as permissões do bot.** Ele ganhou **Gerenciar mensagens**, para apagar as mensagens antigas do Configurador, e **Adicionar reações / Enviar mensagens em threads**, para ajustar permissões de canais.
   - Pare o bot com **Ctrl+C**.
   - Rode `python -m bot convite`, abra o link e clique em **Autorizar**.
2. Rode `python -m bot verificar` (não conecta ao Discord) e corrija o que aparecer com ❌.
3. Rode `python -m bot`. No log deve aparecer `✅ Operação Brasil online e sem erros`.
4. No Discord, use **`/servidor publicar simular:True`** para ver o plano:
   - 🆕 canais que vão receber a mensagem nova;
   - 🗑️ mensagens antigas do Configurador que serão apagadas;
   - ⚠️ canais onde o bot não tem acesso.
5. Use **`/servidor publicar`** e clique em **🚀 Publicar agora**.
6. Use **`/servidor verificar`**. O ideal é tudo ✅. O relatório completo é salvo em `bot\dados\relatorios\`.

**Canais privados da equipe:** se `chat-da-equipe`, `logs-de-moderação` ou `relatórios` aparecerem como "sem permissão", adicione o cargo do bot nesses canais. O caminho é **Editar canal › Permissões**, marcando **Ver canal, Enviar mensagens, Inserir links, Anexar arquivos e Ver histórico**. Depois rode `/servidor publicar` de novo.

## Para mudar um texto depois

1. Edite `bot/conteudo.py`.
2. Rode `python -m bot verificar`. Ele confere os limites do Discord e se os canais citados existem.
3. Reinicie o bot. **As mensagens já publicadas são atualizadas sozinhas**, editando a mesma mensagem, sem duplicar.

Os banners são gerados por `tools/gerar_banners.py`. Os PNGs já vêm prontos.

## O que o `/servidor verificar` confere

- Todos os canais e categorias da estrutura existem, e as salas fixas antigas foram removidas.
- Permissões do bot no servidor (sem Administrador), cargo do bot acima do 💎 VIP, intents ligadas.
- O bot consegue publicar em todos os canais que usa.
- `abrir-squad`, `squad-partida` e `contribuição` não aceitam mensagens de membros.
- Os 5 painéis estão publicados: denúncias, mods, contribuição, abrir squad e aviso de squads.
- As mensagens dos canais estão publicadas e atualizadas, sem sobras do Configurador.
- O link público dos transcripts está ativo e os squads ativos estão consistentes.
- Todos os boosters têm VIP.

## Script de configuração (`main.py`)

O comando `python main.py mensagens` foi **desativado**, para não duplicar mensagens com o bot antigo. Os comandos `validar`, `aplicar` e `onboarding` continuam funcionando. Depois de publicar com o bot novo e conferir o `/servidor verificar`, você pode **remover o Configurador GRB** do servidor ([docs/02](02-bot-temporario.md) §6) e resetar o token dele.
