# 09 — Bot "Operação Brasil": tickets de denúncia e envio de mods

Primeiro módulo do bot permanente da comunidade. Roda no seu PC para testes e depois pode ir para a VPS (seção 8).

## O que ele faz

| Onde | O que acontece |
|---|---|
| `🚨｜denúncias` | Painel fixado com o botão **Abrir atendimento privado** → formulário (assunto, relato, envolvidos, provas) → canal privado `denuncia-0001` visível **só para o autor e a equipe**. |
| `📤｜publicar-mod` | Painel **Central de envio de mods** com os botões **Enviar mod** e **Regras para mods** → assistente privado com menus de **jogo** (Wildlands/Breakpoint), **plataformas** (PC/Xbox/PlayStation, várias) e **categoria** (Gráficos, Gameplay, Armas, Visual, Interface, Áudio, Mundo, Utilitário) → formulário (nome, versão, link oficial, créditos, descrição) → canal privado `mod-0001-nome`. |
| Canal do ticket | Botões para a equipe: 🙋 Assumir · ✅ Aprovar · ✏️ Pedir alterações · ❌ Rejeitar · 🔒 Encerrar · 🔓 Reabrir. |
| `📦｜mods-publicados` | Só recebe mods **aprovados** por alguém da equipe. |
| `🗂️｜logs-de-moderação` | Registro de cada abertura e ação (quem fez, quando e o motivo). |
| `📑｜relatórios` | **Link do transcript** (página protegida por senha) de cada ticket finalizado, com a senha em spoiler (canal privado da equipe). |
| DM do autor | Ao finalizar, o autor recebe o botão **🔓 Visualizar transcript** e a **senha aleatória** na mensagem privada. |
| `╭─── 🎫 Tickets` | Categoria privada criada pelo bot para os canais de atendimento. |

**Regras de segurança implementadas**

- Nada é publicado automaticamente: a aprovação da equipe é obrigatória.
- Quem enviou **não pode** aprovar, rejeitar ou pedir alterações no próprio envio, mesmo sendo da equipe.
- Só Líder Fundador, Administração e Moderador (ou o dono) usam os botões.
- Duplicatas são recusadas (mesmo link ou mesmo nome no mesmo jogo, se ainda estiver em análise ou já aprovado).
- Links: só `https://`. **Recusados:** encurtadores, links diretos para executáveis e scripts, e endereços IP. **Sinalizados para a equipe:** hospedagens genéricas (Mediafire, Mega, Drive…), sites desconhecidos e domínios suspeitos. O bot **nunca baixa nem abre** links ou arquivos.
- Limite por membro: 1 atendimento de denúncia e 2 mods em análise ao mesmo tempo (ajustável).
- Aprovação "à prova de clique duplo": se dois membros da equipe clicarem juntos, só um vale.
- Encerramento automático: denúncias paradas e pedidos de alteração sem resposta por **7 dias**. Mods aguardando a equipe não expiram.
- Tickets finalizados ficam somente leitura para o autor, com transcrição salva para a equipe.
- O bot **não recebe Administrador**. Permissões: ver canais, enviar mensagens, inserir links, anexar arquivos, ler histórico, gerenciar canais, gerenciar cargos/permissões e fixar mensagens.

**Comandos (somente equipe com "Gerenciar servidor")**

- `/tickets paineis` — publica os painéis de novo (se alguém apagou).
- `/tickets info numero:12` — mostra o ticket e o histórico de ações.

## 1. Criar a aplicação do bot (nova, separada do bot de configuração)

1. Acesse <https://discord.com/developers/applications> e clique em **New Application** → `Operação Brasil`.
2. Aba **Installation** → em **Install Link**, selecione **None** e salve.
3. Aba **Bot**:
   - Coloque a foto e o nome.
   - Desligue **Public Bot**.
   - Em **Privileged Gateway Intents**, ligue **Message Content Intent** (usado só para as transcrições). Se preferir não ligar, use `MESSAGE_CONTENT_INTENT=0` no `.env`.
   - Clique em **Reset Token** e copie o token.

## 2. Configurar no seu PC

No PowerShell, na pasta `server-ghost`, com o `.venv` ativo:

```powershell
python -m pip install -r bot\requirements.txt
Copy-Item bot\.env.example bot\.env
notepad bot\.env
```

Preencha `BOT_TOKEN` (o token **novo**) e `GUILD_ID` (o mesmo ID do servidor).

## 3. Autorizar no servidor

```powershell
python -m bot convite
```

Abra o link, confira o servidor e clique em **Autorizar**.

## 4. Ligar o bot

```powershell
python -m bot
```

Deixe a janela aberta: o bot fica online enquanto ela estiver aberta. Na primeira vez ele:

- cria a categoria privada `╭─── 🎫 Tickets`;
- garante o próprio acesso aos canais que usa;
- publica e fixa os painéis em `🚨｜denúncias` e `📤｜publicar-mod`;
- registra os comandos `/tickets`.

Para desligar, use **Ctrl+C**. O log fica em `bot\dados\bot.log` e o banco de tickets em `bot\dados\operacao_brasil.sqlite3`. **Faça backup da pasta `bot\dados`.**

## 5. Atualizar os avisos antigos dos canais

As mensagens publicadas antes diziam que o sistema "ainda não estava disponível". **Depois de testar e confirmar que o bot funciona**, rode (com o bot de configuração ainda no servidor):

```powershell
python main.py mensagens --simular
python main.py mensagens
```

As mensagens de `denúncias`, `publicar-mod` e `regras-para-mods` serão **editadas** para apontar para os novos painéis.

## 6. Roteiro de teste (faça antes de anunciar)

Use sua conta e uma conta secundária, ou um amigo sem cargo de equipe:

- [ ] Conta comum abre um atendimento em `denúncias` → o canal privado aparece só para ela e para a equipe.
- [ ] Conta comum tenta abrir um segundo atendimento → recebe a mensagem de limite.
- [ ] Conta comum clica em **Encerrar** → recebe "Somente a equipe".
- [ ] Você encerra → o autor fica só leitura, a transcrição aparece em `relatórios` e o registro em `logs-de-moderação`.
- [ ] Conta comum envia um mod com link `https://bit.ly/...` → recusado.
- [ ] Conta comum envia um mod com link do Nexus Mods → canal privado criado.
- [ ] Você pede alterações → o autor é mencionado com o motivo.
- [ ] Você aprova → o mod aparece em `mods-publicados` uma única vez.
- [ ] Enviar o mesmo link de novo → recusado como duplicado.
- [ ] Você envia um mod e tenta aprovar o próprio envio → bloqueado.
- [ ] Reinicie o bot (Ctrl+C e `python -m bot`) → os botões antigos continuam funcionando.

## 7. Remover o bot de configuração

Quando o `validar` estiver sem falhas e as mensagens estiverem atualizadas, remova o **Configurador GRB** ([docs/02](02-bot-temporario.md) §6). O bot **Operação Brasil** é independente e continua funcionando.

## 8. Levar para a VPS (Hostinger) depois

1. Envie a pasta `bot` para a VPS, por exemplo em `/opt/operacao-brasil/bot`, junto com `bot/.env` e `bot/dados`.
2. Instale as dependências:
   ```bash
   sudo apt update && sudo apt install -y python3-venv
   cd /opt/operacao-brasil
   python3 -m venv .venv
   .venv/bin/pip install -r bot/requirements.txt
   ```
3. Instale o serviço `bot/deploy/operacao-brasil.service`:
   ```bash
   sudo useradd -r -s /usr/sbin/nologin operacao
   sudo chown -R operacao: /opt/operacao-brasil
   sudo cp bot/deploy/operacao-brasil.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now operacao-brasil
   journalctl -u operacao-brasil -f
   ```
4. **Desligue o bot no PC antes de ligar na VPS**, para não rodarem os dois ao mesmo tempo.

## 9. Próximos módulos planejados

LFG (squads e raids), moderação e logs, e aviso de lives. Todos entram como novos módulos deste mesmo bot, com o mesmo token.

## Transcript protegido por link

Ao **Encerrar**, **Aprovar** ou **Rejeitar** um ticket, o bot:

1. Lê toda a conversa: textos, embeds e imagens de até 3 MB, que ficam embutidas. Outros arquivos aparecem só pelo nome e nunca são baixados.
2. Monta a página no visual do servidor, com busca, imagens ampliáveis e opção de imprimir ou salvar em PDF.
3. Criptografa o conteúdo com AES-256-GCM e uma **senha aleatória** `XXXX-XXXX-XXXX-XXXX`, usando PBKDF2-SHA256 com 310 mil iterações.
4. Publica a página num **link impossível de adivinhar** (`https://…/t/<código aleatório>`), servido pelo próprio bot.
5. Envia na **DM do autor** o botão **🔓 Visualizar transcript** e a senha.
6. Envia em **`relatórios`** o mesmo botão e a senha em spoiler. O arquivo `.html` só é anexado quando não há link público (túnel desligado ou `WEB_ATIVO=0`).
7. **Apaga o canal do ticket.** Se a equipe usar **Reabrir**, o bot cria um canal novo.

O membro clica no botão e a página abre no navegador. Ele digita a senha e vê a conversa. Sem a senha, a página não mostra nada: a descriptografia acontece no navegador e o servidor nunca vê o conteúdo aberto.

### Como o link fica acessível

| Onde o bot roda | Configuração em `bot\.env` | Resultado |
|---|---|---|
| **Seu PC (agora)** | `URL_PUBLICA=` (vazio) e `WEB_TUNEL=cloudflared` | O bot abre sozinho um túnel gratuito da Cloudflare e gera links `https://xxxx.trycloudflare.com/t/...`. **O endereço muda a cada vez que o bot reinicia**, e os links antigos param de abrir. As páginas continuam salvas em `bot\dados\transcripts\`. |
| **VPS com domínio (depois)** | `URL_PUBLICA=https://transcripts.seudominio.com.br` e `WEB_TUNEL=` | Links permanentes, com HTTPS via Caddy ou Nginx apontando para a porta `8088`. |
| Sem link | `WEB_ATIVO=0` | Volta a enviar o arquivo `.html` anexado. |

**Instalar o cloudflared no Windows (uma vez):**

```powershell
winget install --id Cloudflare.cloudflared
```

Feche e abra o PowerShell de novo, ative o `.venv` e rode `python -m bot`. No log deve aparecer `Túnel Cloudflare ativo: https://....trycloudflare.com`.

**Observações**

- O Discord não informa o e-mail dos membros aos bots. Por isso a senha vai pela DM.
- Os links expiram depois de `TRANSCRIPT_DIAS`, que por padrão é 30 dias. Os arquivos ficam em `bot\dados\transcripts\` e são apagados automaticamente quando expiram.
- O computador precisa estar ligado com o bot rodando para o link abrir. Na VPS, ele fica sempre no ar.
- Os túneis rápidos da Cloudflare são gratuitos e servem para testes e uso pessoal. Para uso contínuo, prefira a VPS com domínio.
- Exemplo offline para testar: `docs\exemplo-transcript.html`, senha `ABCD-EFGH-JKLM-NPQR`.
