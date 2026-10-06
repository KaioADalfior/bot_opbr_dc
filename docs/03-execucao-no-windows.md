# 03 — Execução no Windows

O projeto está em **`C:\Users\Kaio\Documents\server-ghost`**. Foi encontrado no seu computador o Python **3.14** (`AppData\Local\Programs\Python\Python314`); o projeto funciona com Python 3.10 ou superior.

## 1. Abrir o terminal na pasta do projeto

1. Pressione **Win**, digite **PowerShell** e abra **Windows PowerShell** (ou **Terminal**).
2. Entre na pasta:

```powershell
cd "$env:USERPROFILE\Documents\server-ghost"
```

Dica: no Explorador de Arquivos, abra a pasta, clique com o botão direito em área vazia > **Abrir no Terminal**.

## 2. Conferir o Python

```powershell
py --version
```

Deve mostrar `Python 3.14.x` (ou outra 3.10+). Se aparecer erro, instale pelo site oficial <https://www.python.org/downloads/> marcando **Add python.exe to PATH**.

## 3. Criar o ambiente virtual e instalar as dependências (uma vez)

```powershell
py -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass   # vale só para esta janela
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

O prompt passa a mostrar `(.venv)`. **Em toda nova janela do PowerShell**, repita apenas:

```powershell
cd "$env:USERPROFILE\Documents\server-ghost"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

> O `Set-ExecutionPolicy -Scope Process` não altera configurações permanentes do Windows: vale somente para a janela aberta.

Teste offline (não precisa de token):

```powershell
python -m unittest discover -s tests -t . -v
python main.py plano
```

## 4. Configurar o `.env`

```powershell
Copy-Item .env.example .env
notepad .env
```

Preencha `DISCORD_BOT_TOKEN`, `DISCORD_GUILD_ID` e confira `DISCORD_GUILD_NAME=Ghost Recon Brasil` (veja [docs/02](02-bot-temporario.md)).

Para obter o ID do servidor: Discord > **Configurações de Usuário** > **Avançado** > ative **Modo de desenvolvedor**; depois clique com o botão direito no ícone do servidor > **Copiar ID do servidor**.

Gere o link de autorização e autorize o bot:

```powershell
python main.py convite
```

## 5. Verificar e simular (não alteram nada)

```powershell
python main.py verificar
python main.py simular
```

- `verificar` confirma: token de **bot** válido, bot presente no servidor certo, nome igual a `DISCORD_GUILD_NAME`, permissões necessárias, posição do cargo do bot e status da Comunidade.
- `simular` lista tudo o que seria criado ou corrigido e salva um relatório em `relatorios\…-aplicar-simulacao.md`.

## 6. Aplicar (primeira execução real)

```powershell
python main.py aplicar
```

O script mostra nome e ID do servidor e pede para você **digitar o nome exato do servidor** para confirmar. Depois cria cargos → ordena a hierarquia → cria categorias e canais com permissões → ordena tudo. Ao final, mostra o resumo (criados, corrigidos, já existentes, preexistentes não alterados, avisos, falhas) e o caminho do relatório.

Depois de ativar a Comunidade ([docs/01](01-servidor-e-comunidade.md) §4), rode `python main.py aplicar` **de novo** para converter `#anuncios` em canal de anúncios. Rodar outras vezes é seguro: o que já está correto não é tocado.

## 7. Mensagens iniciais

Revise os textos em [docs/06](06-mensagens-iniciais.md) (fonte: `gr_setup\mensagens.py`). Depois:

```powershell
python main.py mensagens --simular
python main.py mensagens
```

O script não publica de novo uma mensagem que já está no canal. Modelos de publicação (squad, sugestões, lives, clips, raid semanal, discussão de mods) são fixados.

## 8. (Opcional) Rascunho do Onboarding

Requer Comunidade ativa.

```powershell
python main.py onboarding --simular
python main.py onboarding
```

Grava as 5 perguntas e os 12 canais padrão **desativado**. Revise e ative em **Configurações do Servidor** > **Onboarding**. Se o Onboarding já estiver ativo, o script não o desativa. Se a API recusar, siga a configuração manual em [docs/04](04-configuracao-manual.md#onboarding).

## 9. Validar

```powershell
python main.py validar
```

Executa os testes obrigatórios (estrutura, contagem de salas, permissões **efetivas** calculadas para membro comum, VIP, Organizador, Moderador e Administração, duplicações, configurações manuais, Descoberta) e gera `relatorios\…-validar.md`. Itens **PENDENTE** são etapas manuais; **FALHA** precisa de correção (normalmente `python main.py aplicar` resolve).

Para abrir o relatório mais recente:

```powershell
Get-ChildItem relatorios\*.md | Sort-Object LastWriteTime | Select-Object -Last 1 | ForEach-Object { notepad $_.FullName }
```

## 10. Recuperação em caso de falha

| Situação | O que fazer |
|---|---|
| Queda de internet, janela fechada, `Ctrl+C` no meio | Rode `python main.py aplicar` de novo. O progresso fica em `estado\estado-<ID>.json` e nada é duplicado. |
| `HTTP 429` / “Limite de requisições” no log | Normal. O script espera o tempo indicado pelo Discord e repete sozinho. |
| `HTTP 401` / token inválido | Token errado ou redefinido. Gere outro no Portal (**Bot** > **Reset Token**) e atualize o `.env`. |
| “o bot não está no servidor” | Rode `python main.py convite` e autorize no servidor correto. |
| “não possui as permissões necessárias” | Reautorize com o link de `convite` (a lista exata aparece no erro). |
| “cargo acima do cargo do bot” / falha ao ordenar cargos | Arraste o cargo do bot para o topo em **Cargos** e rode `aplicar`. |
| “nome do servidor é X, mas o esperado é Y” | Confira `DISCORD_GUILD_ID` ou ajuste `DISCORD_GUILD_NAME`. Proteção contra alterar o servidor errado. |
| “já existia e não foi alterado” | Havia um recurso com o mesmo nome antes do script. Se ele deve ser gerenciado, rode `python main.py aplicar --adotar-existentes` (pode alterar permissões dele). |
| Perdeu a pasta `estado\` | Os recursos passam a ser vistos como preexistentes. Use `python main.py aplicar --adotar-existentes` uma vez. |
| Quer desfazer | O script nunca apaga nada. Apague manualmente no app; os IDs do que foi criado estão em `estado\estado-<ID>.json`. Depois rode `aplicar` se quiser recriar. |
| `ModuleNotFoundError: requests` | O ambiente virtual não está ativo: repita o §3 (ativação). |
| Erro desconhecido | Veja o arquivo em `logs\` (tokens são ocultados automaticamente) e o relatório em `relatorios\`. |
