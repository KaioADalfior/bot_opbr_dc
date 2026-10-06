# Relatório de testes (pré-entrega)

**Data:** 03/10/2026 · **Python:** 3.13 · **Comando:** `python -m unittest discover -s tests -t . -v`
**Resultado:** ✅ 8 testes, 0 falhas (atualizado após a reformulação de nomes, patentes e regras).

> **Importante:** estes testes rodaram contra um **simulador local da API do Discord** (`tests/fake_discord.py`), não contra o seu servidor real. O simulador reproduz as regras relevantes (hierarquia de cargos, “só concede o que possui”, canais de anúncio exigem Comunidade, requisitos do Onboarding, respostas 429). A validação definitiva acontece quando você executar `python main.py validar` no servidor real — até lá, o projeto **não** está implantado.

## Cenários executados

| Teste | O que comprova | Resultado |
|---|---|---|
| Fluxo completo | `verificar` e `simular` não fazem nenhuma escrita; `aplicar` cria 29 cargos, 12 categorias e 60 canais; canais padrão do Discord (`geral`, `Geral`) ficam intactos | ✅ |
| Idempotência | 2ª execução de `aplicar`: **zero** requisições de escrita, nenhum item duplicado | ✅ |
| Comunidade | Após ativar a Comunidade, `aplicar` converte `#anuncios` para tipo Anúncio sem recriar | ✅ |
| Mensagens | Simulação não publica; publicação real; 2ª execução não duplica; modelos fixados | ✅ |
| Onboarding | Rascunho aceito pelas regras (≥7 canais padrão, ≥5 com envio); fica desativado; IDs das perguntas preservados ao regravar | ✅ |
| Deriva | Liberar envio em `#anuncios` manualmente → `validar` acusa FALHA → `aplicar` corrige → `validar` OK | ✅ |
| Permissões de terceiros | Permissão de canal de outro alvo (ex.: bot futuro) é preservada na correção | ✅ |
| Segredos | Nenhum log/relatório contém o token | ✅ |
| Sem exclusões | Nenhuma requisição DELETE (bloqueadas no cliente) | ✅ |
| Limite de requisições | 23 respostas 429 simuladas em 774 requisições, todas repetidas com sucesso | ✅ |
| Cargo preexistente | “VIP” com Administrador criado antes: não é alterado nem duplicado; `validar` acusa o risco | ✅ |
| `--adotar-existentes` | Cargo preexistente “PC” com poderes é corrigido para 0 | ✅ |
| Bot sem permissão | Faltando “Banir membros”: bloqueia antes de qualquer escrita | ✅ |
| Servidor errado | ID que o bot não acessa: aborta | ✅ |
| Nome divergente | `DISCORD_GUILD_NAME` diferente: bloqueia antes de qualquer escrita | ✅ |
| Renomear e editar | Canal/cargo gerenciado com nome antigo é renomeado; mensagens já publicadas são editadas e só as que faltam são publicadas; 3ª execução não escreve | ✅ |
| Outro bot | Canal com mensagem de bot anterior (sem conteúdo visível): não duplica; `--forcar` publica | ✅ |

## Testes obrigatórios do projeto (§10) no simulador

| # | Verificação | Simulador | No servidor real |
|---|---|---|---|
| 1 | Todas as categorias existem | ✅ | rodar `validar` |
| 2 | Canais nas categorias corretas | ✅ | rodar `validar` |
| 3 | 12 salas Breakpoint (4 por plataforma) | ✅ | rodar `validar` |
| 4 | 12 salas Wildlands (4 por plataforma) | ✅ | rodar `validar` |
| 5 | 4 salas Rainbow Six Siege | ✅ | rodar `validar` |
| 6 | Salas gerais identificadas | ✅ | rodar `validar` |
| 7 | `#anuncios` sem envio para membros (e tipo Anúncio) | ✅ | rodar `validar` após Comunidade |
| 8 | `#regras` / `#boas-vindas` | ✅ | rodar `validar` |
| 9 | MODS pública (correção obrigatória) e EQUIPE privada | ✅ (9a, 9b) | rodar `validar` |
| 10 | VIP sem permissões administrativas | ✅ | rodar `validar` |
| 11 | Cargos de plataforma sem privilégios | ✅ | rodar `validar` |
| 12 | Canais de suporte | ✅ | rodar `validar` |
| 13 | `#denuncias` não expõe relatos | ✅ | rodar `validar` |
| 14 | Lives com publicação manual autorizada | ✅ | rodar `validar` + teste manual |
| 15 | Canais de bots futuros sem funções inexistentes | ✅ | rodar `validar` |
| 16 | Segunda execução não duplica | ✅ | rodar `aplicar` 2× e `validar` |
| 17 | Relatório identifica erros e pendências | ✅ | gerado em `relatorios\` |

Permissões validadas como **efetivas** (cálculo oficial: @everyone → cargos → permissões de canal), para as personas Membro comum, VIP, Organizador, Moderador e Administração — ver [docs/matriz-de-permissoes.md](docs/matriz-de-permissoes.md).

## Pendentes por natureza (manuais, aparecem como PENDENTE no `validar`)

Administrador no Líder Fundador (E5) · Comunidade (M1) · verificação (M2) · filtro de mídia (M3) · 2FA de moderação (M4) · canal de regras (M5) · canal de atualizações (M6) · descrição (M8) · Descoberta (D1–D3, dependem de 1.000 membros e 8 semanas). Procedimentos em [docs/04](docs/04-configuracao-manual.md).
