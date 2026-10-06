# 02 — Bot temporário de configuração

A API oficial do Discord só aceita criação de canais, cargos e permissões feita por uma **aplicação autorizada**. Por isso usamos um bot criado por você, usado **somente** durante a implantação e removido em seguida. Nunca use o token da sua conta pessoal (self-bot), o que viola os Termos do Discord.

## 1. Criar a aplicação

1. Acesse <https://discord.com/developers/applications> e entre com a conta **dona do servidor**.
2. **New Application** → nome: `Configurador GRB` → aceite os termos → **Create**.
3. Em **General Information**, copie o **Application ID** e cole em `DISCORD_APPLICATION_ID` no `.env` (opcional, facilita o comando `convite`).

## 2. Configurar o bot com segurança

1. Aba **Installation**: em **Install Link**, selecione **None** e salve (necessário para desligar o *Public Bot*).
2. Aba **Bot**:
   - **Public Bot: desligado** — só você poderá adicioná-lo a servidores.
   - **Requires OAuth2 Code Grant: desligado**.
   - **Privileged Gateway Intents** (Presence, Server Members, Message Content): **todos desligados** — o script não usa o gateway.
3. Clique em **Reset Token** → confirme → **Copy**. Cole no `.env` em `DISCORD_BOT_TOKEN=`.
   - O token aparece uma única vez. Se perder, gere outro (o anterior deixa de funcionar).
   - **Nunca** cole o token em chats, prints, vídeos, lives ou repositórios. Quem tem o token controla o bot.

## 3. Autorizar no servidor com permissões mínimas

No PowerShell (veja [docs/03](03-execucao-no-windows.md)):

```powershell
python main.py convite
```

O comando imprime um link como:

```
https://discord.com/oauth2/authorize?client_id=SEU_APP_ID&scope=bot&permissions=7416613883871222&guild_id=SEU_SERVIDOR&disable_guild_select=true
```

Abra o link, confira que o servidor é **Ghost Recon Brasil**, revise a lista e clique em **Autorizar**.

### Por que estas permissões (e não Administrador)?

O Discord só deixa um bot **conceder** permissões (a cargos ou em permissões de canal) que **ele mesmo possui**. Como o script cria o cargo Moderador com “Banir membros”, por exemplo, o bot precisa ter “Banir membros”. O conjunto pedido é exatamente a união do que a estrutura concede, mais o necessário para operar — **sem Administrador**. Consequência: o bot não pode criar um cargo com Administrador, por isso o **Líder Fundador** recebe Administrador **manualmente** por você.

| Grupo | Permissões |
|---|---|
| Operação do script | Gerenciar cargos, Gerenciar canais, Gerenciar servidor (Onboarding), Ver canais, Enviar mensagens, Inserir links, Ver histórico, Fixar mensagens |
| Concedidas a Administração/Moderador/Organizador | Expulsar, Banir, Castigar, Gerenciar mensagens, threads, apelidos, webhooks, expressões, eventos; Ver registro de auditoria; Ver análises; Silenciar, Ensurdecer, Mover membros; Voz prioritária; Mencionar @everyone; Ignorar modo lento; Criar expressões/eventos |
| Usadas em permissões de canal | Adicionar reações, Anexar arquivos, Threads (criar/enviar), Enquetes, Mensagens de voz, TTS, Usar comandos de aplicativos, Conectar, Falar, Vídeo, Detecção de voz |

Valor inteiro: **7416613883871222** (calculado por `python main.py plano`).

## 4. Hierarquia: o cargo do bot precisa ficar acima dos cargos do projeto

Ao entrar, o bot ganha um cargo gerenciado com o nome dele. Os cargos criados pelo script nascem abaixo dele. Se algum cargo do projeto ficar acima do bot (por exemplo, se você arrastar o Líder Fundador para o topo antes de terminar), o script avisa e não consegue corrigir aquele cargo. Solução: **Configurações do Servidor** > **Cargos** > arraste o cargo `Configurador GRB` para o topo, rode `aplicar` e depois reorganize como quiser.

## 5. Durante a implantação

- `python main.py verificar` confere token, servidor, permissões e hierarquia sem alterar nada.
- O bot recebe, em cada canal do projeto, uma permissão de canal própria (para enxergar canais privados e publicar nos somente leitura). Ela **some automaticamente** quando o bot é removido, porque o cargo gerenciado dele é apagado junto.

## 6. Remover o bot depois da implantação (não afeta canais e cargos)

Faça isso **depois** de `python main.py validar` sem falhas e das mensagens publicadas:

1. **Configurações do Servidor** > **Integrações** > `Configurador GRB` > **Remover integração** (*Remove Integration*). Alternativa: lista de membros > botão direito no bot > **Expulsar**.
   - Canais, cargos, permissões e mensagens criados **permanecem**.
   - O cargo gerenciado do bot e as permissões de canal dele são removidos automaticamente.
2. No Portal do Desenvolvedor > **Bot** > **Reset Token** (invalida o token antigo). Se não for reutilizar, **General Information** > **Delete App**. As mensagens publicadas continuam no servidor.
3. Apague o valor de `DISCORD_BOT_TOKEN` do `.env` (ou apague o arquivo `.env`).
4. Confira em **Configurações do Servidor** > **Registro de auditoria** que todas as ações foram as esperadas.

Para rodar o script novamente no futuro (por exemplo, para validar), basta criar um novo token, autorizar de novo com `python main.py convite` e repetir a remoção ao terminar. Mantenha a pasta `estado/` — ela permite ao script reconhecer o que já criou.
