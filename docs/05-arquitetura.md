# 05 — Arquitetura, cargos, permissões e decisões

## Visão geral

```
 Você (dono)                         Discord (API oficial v10)
 ───────────                         ─────────────────────────
 .env (token do bot) ──► main.py ──► discord_api.py ──HTTPS──► /guilds, /roles, /channels, /messages, /onboarding
                           │            (limites de requisição, novas tentativas, sem DELETE)
                           ├─ estrutura.py   planta declarativa (cargos, categorias, canais, permissões)
                           ├─ provisionador  compara planta × servidor → cria / corrige / preserva
                           ├─ publicacao     mensagens iniciais + rascunho de Onboarding
                           ├─ validador      permissões efetivas por "persona" + checagens
                           └─ relatorio      relatorios\*.md|json   logs\*.log   estado\estado-<ID>.json
```

**Idempotência:** cada item da planta tem uma chave fixa (ex.: `squad_raid`). O ID criado fica em `estado\`. Na execução seguinte, o script procura primeiro pelo ID salvo e, se não houver, pelo nome (ignorando o emoji) **dentro da categoria esperada**. Encontrou → confere e corrige divergências; não encontrou → cria. Recursos com o mesmo nome que já existiam antes **não são alterados** sem `--adotar-existentes`.

**Correções que o script faz em recursos dele:** permissões de canal (preservando permissões de terceiros, ex. de bots futuros), categoria, tópico, modo lento, limite de voz, tipo texto→anúncio, permissões/cor/exibição dos cargos e ordem. **Nunca** renomeia, apaga ou mexe em canais/cargos alheios.

## Limites do Discord verificados

| Recurso | Projeto | Limite |
|---|---|---|
| Canais + categorias | 72 | 500 por servidor |
| Canais por categoria | máx. 12 | 50 |
| Cargos | 29 (+ cargo do bot) | 250 |
| Modo lento | máx. 6 h | 21600 s |
| Regras na triagem | 10 | 16 |
| Canais padrão do Onboarding | 12 (7 com envio) | mín. 7, 5 com envio |

## Árvore de categorias e canais

```
╭─── 📌 Central                              (todos leem; só Líder/Administração publicam)
   📢｜anúncios           [Anúncio*]
   👋｜boas-vindas
   📜｜regras
   🧭｜comece-aqui
╭─── 🏅 VIPs
   🏅｜vips               (todos leem; VIP e equipe escrevem)
╭─── 🔥 Alistamento                          (Organizador menciona cargos e fixa)
   🔥｜squad-raid         modo lento 5 min, threads
   🎮｜squad-partida      modo lento 5 min, threads
╭─── 🌐 Chat
   💬｜geral
   📷｜fotos-e-memes
   👕｜outfits
   💡｜sugestões          modo lento 2 min
   🤖｜comandos           somente leitura até existirem bots
   🎬｜clips-e-highlights modo lento 30 s
   🔴｜divulgação-de-lives modo lento 6 h, sem threads
   🔊 Bate Papo (GERAL)  (voz)
╭─── 🆘 Ajuda
   🛠️｜suporte-geral
   🧠｜suporte-dicas
   ❓｜dúvidas
   🚨｜denúncias          somente leitura (Moderador e Administração escrevem)
╭─── 🧩 Mods                                 (PÚBLICA — modificações dos jogos)
   📦｜mods-publicados    somente leitura
   🗨️｜discussão-mods
   📋｜regras-para-mods   somente leitura
   📤｜publicar-mod       somente leitura até o bot existir
╭─── 💀 Breakpoint
   💀｜chat-geral-breakpoint
   📝｜raid-semanal       modo lento 1 min; Organizador menciona e fixa
   🔊 💀 Breakpoint Geral
╭─── 🌿 Wildlands
   🌿｜chat-geral-wildlands
   🔊 🌿 Wildlands Geral
╭─── 👮 Rainbow Six Siege
   🔊 👮 Radio 01 · Radio 02 · Radio 03 · Radio 04
╭─── 💀 Breakpoint | Salas
   🔊 💀 Breakpoint PC 1–4 · XBOX 1–4 · PS 1–4      (12)
╭─── 🌿 Wildlands | Salas
   🔊 🌿 Wildlands PC 1–4 · XBOX 1–4 · PS 1–4         (12)
╭─── 🛡️ Equipe                               (PRIVADA)
   🔒｜chat-da-equipe     Líder, Administração, Moderador, Organizador
   🗂️｜logs-de-moderação  Líder, Administração, Moderador
   📑｜relatórios         Líder, Administração, Moderador
   🎙️ Reunião da Equipe  Líder, Administração, Moderador, Organizador
```
\* Tipo Anúncio requer Comunidade; antes disso o canal é criado como texto e convertido no `aplicar` seguinte.

Matriz detalhada de quem vê/escreve/fala: [matriz-de-permissoes.md](matriz-de-permissoes.md).

## Cargos (ordem = hierarquia)

| Cargo | Permissões no servidor | Observações |
|---|---|---|
| **Líder Fundador** | Mesmas da Administração + **Administrador (manual)** | Controle total. Cargo único, conforme sua escolha. |
| **Administração** | Gerenciar servidor, canais, cargos, webhooks, expressões e eventos; expulsar, banir, castigar; gerenciar mensagens, threads e apelidos; voz (silenciar, ensurdecer, mover, prioritária); mencionar @everyone; ver auditoria e análises; fixar; ignorar modo lento | Sem Administrador. |
| **Moderador** | Expulsar, banir, castigar; gerenciar mensagens, threads, apelidos; fixar; silenciar, ensurdecer, mover; ver auditoria; ignorar modo lento | Não gerencia servidor, cargos nem canais. |
| **Organizador de Operações** | Gerenciar e criar eventos | Menciona cargos e fixa só em `squad-raid`, `squad-partida` e `raid-semanal`. Não bane/expulsa. Vê `chat-da-equipe` e `reuniao-da-equipe`. |
| VIP | nenhuma | Escreve em `#vips`. Sem poderes. |
| ★★★ Coronel · ★★ Tenente-Coronel · ★ Major · ☆☆☆ Capitão · ☆ Tenente · ❯❯❯ Sargento · ❯❯ Cabo · ❯ Soldado | nenhuma | Patentes demonstrativas, exibidas separadas, cores dourado → verde-oliva. |
| Veterano · Colaborador · Membro · Novato | nenhuma | Reconhecimento. |
| Ghost Recon Wildlands · Ghost Recon Breakpoint · Rainbow Six Siege | nenhuma | Atribuídos pelo Onboarding. |
| PC · Xbox · PlayStation | nenhuma | Atribuídos pelo Onboarding. |
| Casual · Furtivo · Tático · Livre | nenhuma | Atribuídos pelo Onboarding. |
| Notificações de Eventos · Notificações de Operações | nenhuma | Não mencionáveis por membros; equipe e Organizador podem mencioná-los. |

Todos os cargos sem poderes são criados com permissões **0** (sem isso o Discord copiaria as do @everyone).

## Decisões e ajustes documentados

| # | Pedido | Decisão | Motivo |
|---|---|---|---|
| 1 | “Líder / Fundador / Comandante” | **Um cargo: “Líder Fundador”** | Sua escolha. Renomeie à vontade no app: o script reconhece o cargo pelo ID salvo. |
| 2 | Líder com controle total | Administrador ativado **manualmente** | O bot não tem (nem deve ter) Administrador, e o Discord não deixa conceder o que não se possui. |
| 3 | Cargo para quem administra contribuições | **Não criado** | Não há contribuições ainda; Administração cobre. Crie “Tesouraria” quando existir apoio real. |
| 4 | VIP pode conversar em #vips? | **Sim**: todos leem; VIP e equipe escrevem | Explica o apoio publicamente e dá um espaço aos apoiadores. |
| 5 | MODS pública × teste “MODS é privada” | **MODS pública**, **EQUIPE privada** | A “Correção obrigatória” redefiniu MODS como modificações dos jogos e separou a moderação na EQUIPE. O teste 9 foi dividido em 9a (MODS pública) e 9b (EQUIPE privada). |
| 6 | `🔊・publicar-mod` | **Canal de texto `📤｜publicar-mod`** | Sua escolha. O futuro bot usará botão ou `/enviar-mod` com ticket privado (mais confiável que detectar entrada em voz). Emoji trocado para não sugerir canal de voz. |
| 7 | Fórum para squads | **Texto** | Sua escolha. Modelo fixado + threads + modo lento reproduzem a organização do fórum. |
| 8 | Subcategorias PC/Xbox/PS | **Não existem no Discord** (categorias não aninham) | Uma categoria por jogo, ordenada PC → Xbox → PS. Seis categorias poluiriam a barra lateral. Com o Onboarding, cada membro vê só as salas da plataforma escolhida. |
| 9 | Posição da EQUIPE | **Última** | Só a equipe a vê; mantém a ordem pública 01–11. |
| 10 | #comandos | **Somente leitura** até existirem bots | Evita virar outro chat geral e não promete comandos. |
| 11 | #denuncias | **Somente leitura**, sem reações | Evita exposição de relatos. |
| 12 | Limite de divulgação de lives | **Modo lento de 6 h** (máximo do Discord) | Equipe e dono ignoram o modo lento. Ajustável. |
| 13 | Limites das salas de voz | **Sem limite** | Pedido: só com justificativa. Opção pronta (4/4/5) em `estrutura.py`. |
| 14 | Canal de texto de Siege | **Não criado** | Sugestão separada: `👮｜chat-geral-siege` para combinar partidas e compartilhar dicas, já que Siege hoje só tem voz. Diga se quiser. |
| 15 | Moderador pode banir? | **Sim** | Banir é função típica de moderação; Organizador não pode. Remova em `estrutura.py` se preferir só Administração. |
| 16 | @everyone global | **Não alterado** | Para não mexer em canais antigos; menções em massa são bloqueadas nos canais do projeto. Recomendação manual em docs/04 §12. |
| 17 | Nomes com emojis | Texto `emoji｜nome`, voz `emoji Nome`, categorias `╭─── emoji Nome` | Padrão visual pedido por você (fotos de referência). |
| 18 | discord.py | **API REST v10 direta** com `requests` | Implantação única, sem gateway, simulação simples, compatível com Python 3.14. |
| 19 | Patentes demonstrativas | 8 cargos de patente sem permissões, exibidos separados | Destaque visual; não concedem poderes. |
| 20 | Regra 6 cita “Bate Papo (GERAL)” | Criada a sala de voz `🔊 Bate Papo (GERAL)` no Chat | Para a regra apontar para um canal que existe. |

## Efeito de muitos canais num servidor pequeno

31 salas de voz são muitas para um servidor que está começando: membros veem salas vazias. Mitigações já previstas, sem remover nada: (1) Onboarding mostra a cada membro só as salas da plataforma dele; (2) as salas ficam em categorias recolhíveis no final; (3) se a ocupação for baixa por meses, considere reduzir para 2 salas por plataforma — **somente com sua decisão**.
