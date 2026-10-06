# Ghost Recon Brasil — implantação automatizada do servidor Discord

> **Nenhum operador fica para trás.**

Projeto que cria e valida, pela **API oficial do Discord** e com um **bot temporário**, a estrutura completa do servidor *Ghost Recon Brasil*: 29 cargos (incluindo 8 patentes), 12 categorias e 60 canais (28 de texto e 32 de voz), com permissões, mensagens iniciais e um rascunho opcional do Onboarding.

- Sem self-bot, sem token pessoal, sem automação do aplicativo do Discord.
- **Idempotente**: pode rodar quantas vezes quiser; nada é duplicado.
- **Nunca apaga** canais, cargos ou mensagens (o código bloqueia requisições DELETE).
- **Não altera** canais e cargos que já existiam antes (a menos que você peça com `--adotar-existentes`).
- Modo **simulação**, **validação de permissões efetivas**, logs sem segredos e relatórios.

Comunidade independente de fãs, **sem afiliação com a Ubisoft**.

---

## Roteiro completo (siga nesta ordem)

| # | Etapa | Onde | Guia |
|---|---|---|---|
| 1 | Criar o servidor, ícone e nome | App do Discord | [docs/01](docs/01-servidor-e-comunidade.md) §1–2 |
| 2 | Instalar Python e dependências | PowerShell | [docs/03](docs/03-execucao-no-windows.md) §1–3 |
| 3 | Criar o bot temporário e gerar o convite | Portal do Desenvolvedor | [docs/02](docs/02-bot-temporario.md) |
| 4 | `verificar` → `simular` → **`aplicar`** | PowerShell | [docs/03](docs/03-execucao-no-windows.md) §4–6 |
| 5 | Ativar a Comunidade (regras = `#📜｜regras`, atualizações = `#🔒｜chat-da-equipe`) | App | [docs/01](docs/01-servidor-e-comunidade.md) §4–8 |
| 6 | `aplicar` de novo (converte `#anuncios` em canal de anúncios) | PowerShell | [docs/03](docs/03-execucao-no-windows.md) §6 |
| 7 | `mensagens --simular` → `mensagens` | PowerShell | [docs/03](docs/03-execucao-no-windows.md) §7 |
| 8 | (Opcional) `onboarding --simular` → `onboarding` | PowerShell | [docs/03](docs/03-execucao-no-windows.md) §8 |
| 9 | `validar` e conferir o relatório | PowerShell | [docs/03](docs/03-execucao-no-windows.md) §9 |
| 10 | Configurações manuais (2FA, triagem, Onboarding, Guia, convite…) | App | [docs/04](docs/04-configuracao-manual.md) |
| 11 | **Remover o bot e redefinir o token** | App + Portal | [docs/02](docs/02-bot-temporario.md) §6 |

## Comandos (PowerShell, dentro desta pasta, com `.venv` ativo)

```powershell
python main.py plano        # estrutura planejada (offline)
python main.py convite      # link de autorização do bot com permissões mínimas
python main.py verificar    # confere token, servidor, permissões e hierarquia — não altera nada
python main.py simular      # mostra o que seria criado/corrigido — não altera nada
python main.py aplicar      # cria/corrige (pede para digitar o nome do servidor)
python main.py mensagens --simular
python main.py mensagens
python main.py onboarding --simular
python main.py onboarding   # grava como RASCUNHO desativado; você ativa no app
python main.py validar      # testes de estrutura e permissões efetivas + relatório
python -m unittest discover -s tests -t . -v   # testes automatizados offline
```

## Organização dos arquivos

```
server-ghost/
├─ README.md                  este guia
├─ RELATORIO-DE-TESTES.md     resultados dos testes executados antes da entrega
├─ requirements.txt           requests + python-dotenv
├─ .env.example               modelo de configuração (copie para .env)
├─ .gitignore                 impede que .env, logs e estado sejam versionados
├─ config.py                  leitura do .env e logs com ocultação de tokens
├─ main.py                    linha de comando (plano, convite, verificar, simular, aplicar…)
├─ gr_setup/
│  ├─ estrutura.py            PLANTA do servidor: cargos, categorias, canais, permissões
│  ├─ mensagens.py            textos das mensagens iniciais
│  ├─ permissoes.py           flags oficiais e cálculo de permissões efetivas
│  ├─ discord_api.py          cliente REST v10 com limites de requisição e novas tentativas
│  ├─ provisionador.py        criação/correção idempotente
│  ├─ publicacao.py           mensagens iniciais e rascunho de Onboarding
│  ├─ validador.py            testes obrigatórios e permissões efetivas
│  └─ relatorio.py            relatórios Markdown/JSON
├─ docs/
│  ├─ 01-servidor-e-comunidade.md    criar servidor, Comunidade, segurança, Descoberta
│  ├─ 02-bot-temporario.md           criar, autorizar e remover o bot de configuração
│  ├─ 03-execucao-no-windows.md      instalação, comandos e recuperação de falhas
│  ├─ 04-configuracao-manual.md      tudo o que é feito no app depois do script
│  ├─ 05-arquitetura.md              árvore, cargos, permissões e decisões de projeto
│  ├─ 06-mensagens-iniciais.md       textos que serão publicados
│  ├─ 07-identidade-visual.md        paleta, ícone, nomes e cuidados com marcas
│  ├─ 08-bots-futuros.md             plano para moderação, LFG, tickets, voz e lives
│  └─ matriz-de-permissoes.md        quem vê/escreve/fala em cada canal
├─ tests/                     simulador da API e testes de ponta a ponta
├─ estado/                    mapa chave→ID criado pelo script (não contém segredos)
├─ logs/                      log de cada execução (tokens ocultados)
└─ relatorios/                relatórios de cada execução
```

## Por que API REST direta em vez de discord.py?

A versão atual do discord.py (2.7.1, de 03/03/2026) é excelente para bots que ficam online, mas exige conexão ao *gateway* e dependências nativas. Para uma **implantação única**, chamadas REST diretas à API v10 são mais simples, transparentes e auditáveis: cada criação é uma requisição explícita, o modo simulação é trivial e a única dependência é `requests` — que funciona no Python 3.14 instalado no seu computador. Os bots futuros (que ficam online) podem usar discord.py normalmente.

## Segurança em uma frase

O token fica só no `.env` (ignorado pelo Git e ocultado nos logs), o bot **não** recebe Administrador, o script confere ID **e** nome do servidor e pede confirmação digitada, e depois da implantação o bot é removido e o token redefinido.

## Fase 2 — Bot "Operação Brasil"

Bot permanente da comunidade, na pasta `bot\`. O primeiro módulo trata de **tickets de denúncia** e do **envio e aprovação de mods**. Guia completo: [docs/09-bot-tickets.md](docs/09-bot-tickets.md).

```powershell
python -m pip install -r bot\requirements.txt
Copy-Item bot\.env.example bot\.env   # preencha BOT_TOKEN e GUILD_ID
python -m bot convite                  # link de autorização
python -m bot                          # liga o bot (Ctrl+C desliga)
```
