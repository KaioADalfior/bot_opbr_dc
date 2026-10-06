# 13 — Subir o bot na VPS (Hostinger + Easypanel)

O bot roda como um **App** do Easypanel, em Docker, ao lado do seu site e sem conflito de portas. O próprio Easypanel publica os transcripts com **HTTPS** no seu domínio.

```
GitHub (código, privado) ──► Easypanel faz o build (Dockerfile) ──► container "bot"
                                                                     ├─ variáveis: token, servidor, URL
                                                                     ├─ pasta /app/bot/dados  ⇄  /opt/operacao-brasil/dados na VPS
                                                                     └─ porta 8088  ⇄  https://transcripts.gropbr.daksolucoes.tech
```

> Os nomes dos botões do Easypanel podem variar um pouco entre versões. A ordem dos passos é a mesma.

---

## Parte 1 — No PC: preparar

1. Se ainda não fez: `/servidor publicar` e `/servidor verificar` no Discord. A remoção das mensagens antigas do Configurador só funciona no PC.
2. **Mande o código para o GitHub** (repositório privado `KaioADalfior/bot_opbr_dc`). O script confere sozinho que **nenhum segredo** vai junto (`.env`, `bot/.env`, `bot/dados`, tokens):

   ```powershell
   winget install --id Git.Git
   ```

   Feche e abra o PowerShell, depois:

   ```powershell
   cd C:\Users\Kaio\Documents\server-ghost
   Set-ExecutionPolicy -Scope Process Bypass
   .\enviar-github.ps1
   ```

   Na primeira vez, ele pergunta seu nome e e-mail e abre o navegador para você entrar no GitHub. Para as próximas atualizações, use `.\enviar-github.ps1 "o que mudou"`.

## Parte 2 — DNS do domínio

No painel onde o domínio está (se for na Hostinger: **hPanel › Domínios › DNS**), crie:

| Tipo | Nome | Aponta para | TTL |
|---|---|---|---|
| A | `transcripts.gropbr` | IP da sua VPS | padrão |

Esse registro fica na zona DNS do domínio `daksolucoes.tech`. O resultado é `transcripts.gropbr.daksolucoes.tech`.

Pode levar alguns minutos para propagar.

## Parte 3 — Na VPS: pasta de dados

**Primeiro pare o bot no PC (Ctrl+C).** Nunca rode os dois ao mesmo tempo.

No PowerShell do PC, envie a pasta de dados. Ela tem os tickets, painéis, squads, VIPs e transcripts; sem ela, o bot publicaria os painéis de novo, duplicados.

```powershell
cd C:\Users\Kaio\Documents\server-ghost
ssh root@IP-DA-VPS "mkdir -p /opt/operacao-brasil"
scp -r bot\dados root@IP-DA-VPS:/opt/operacao-brasil/
ssh root@IP-DA-VPS "chown -R 1000:1000 /opt/operacao-brasil/dados && ls -la /opt/operacao-brasil/dados"
```

A senha do `root` é a que você definiu no **hPanel › VPS**. Também dá para usar o **Terminal do navegador** do hPanel para os comandos `mkdir`/`chown`.

## Parte 4 — No Easypanel: criar o App

Abra o Easypanel (o endereço aparece no painel da VPS na Hostinger, geralmente `http://IP-DA-VPS:3000`).

1. **Conectar o GitHub (uma vez):** **Settings › GitHub** → cole um *token* do GitHub. Gere em github.com › Settings › Developer settings › Personal access tokens, com acesso de leitura ao repositório `bot_opbr_dc`.
2. **Create Project** → `operacao-brasil`.
3. Dentro do projeto: **+ Service › App** → nome `bot`.
4. **Source › GitHub:** dono `KaioADalfior`, repositório `bot_opbr_dc`, branch `main`, caminho `/`. **Build:** **Dockerfile** (arquivo `Dockerfile`). Salve.
5. **Environment:** cole as linhas abaixo, com os valores do seu `bot\.env`.

   ```
   BOT_TOKEN=cole-o-token-do-bot-aqui
   GUILD_ID=1556051792067035288
   MESSAGE_CONTENT_INTENT=1
   MEMBERS_INTENT=1
   URL_PUBLICA=https://transcripts.gropbr.daksolucoes.tech
   WEB_HOST=0.0.0.0
   WEB_PORTA=8088
   WEB_TUNEL=
   ```

   Copie também qualquer outra variável que você mudou no `bot\.env`, como `CARGO_VIP`, `SQUAD_VAZIO_MIN` etc. Salve.
6. **Mounts › Add Bind Mount:** **Host Path** `/opt/operacao-brasil/dados` → **Mount Path** `/app/bot/dados`. Salve.
7. **Domains › Add Domain:** `transcripts.gropbr.daksolucoes.tech`, **HTTPS ligado**, **Port** `8088`. Salve.
8. **Deploy settings:** se houver a opção **Zero Downtime**, **desligue**. Durante a atualização, dois bots ao mesmo tempo responderiam em dobro.
9. Clique em **Deploy**.

## Parte 5 — Conferir

- Na aba **Logs** do App deve aparecer `✅ Operação Brasil online e sem erros`.
- Na aba **Console** do App (se houver), rode `python -m bot verificar`.
- Abra `https://transcripts.gropbr.daksolucoes.tech`. Deve aparecer "servidor de transcripts ativo".
- No Discord: `/servidor verificar`. O item **Link público dos transcripts** deve mostrar o seu domínio.
- Teste: abra e encerre um ticket e clique em **🔓 Visualizar transcript** na DM.

Os links antigos, do túnel do PC, são atualizados sozinhos para o domínio novo quando o bot liga.

## Atualizar o bot depois

No PC:

```powershell
git add .
git commit -m "o que mudou"
git push
```

No Easypanel, clique em **Deploy** (ou ligue o **Auto Deploy**). Os dados ficam na pasta da VPS e não se perdem.

## Backup dos dados

Na VPS, via `ssh root@IP-DA-VPS` ou o terminal do hPanel:

```bash
apt install -y sqlite3
mkdir -p /opt/operacao-brasil/backups
echo '30 4 * * * root sqlite3 /opt/operacao-brasil/dados/operacao_brasil.sqlite3 ".backup /opt/operacao-brasil/backups/ob-$(date +\%F).sqlite3" && find /opt/operacao-brasil/backups -mtime +14 -delete' > /etc/cron.d/operacao-brasil
```

## Problemas comuns

| Sintoma | Causa provável |
|---|---|
| Log: `PrivilegedIntentsRequired` | Ligar **SERVER MEMBERS INTENT** e **MESSAGE CONTENT INTENT** no Portal do Desenvolvedor |
| Log: `unable to open database` / `Permission denied` em dados | Faltou `chown -R 1000:1000 /opt/operacao-brasil/dados` |
| Painéis duplicados no Discord | A pasta `dados` do PC não foi copiada. Apague as duplicatas e copie a pasta. |
| Respostas em dobro nos botões | O bot ainda está ligado no PC, ou o Zero Downtime está ligado |
| Domínio sem HTTPS / não abre | DNS ainda propagando, ou a porta no Domain não é `8088` |
