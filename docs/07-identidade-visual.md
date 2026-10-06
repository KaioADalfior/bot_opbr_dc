# 07 — Identidade visual

## Conceito

Tático e organizado, sem parecer força militar real: azul de “visor noturno” sobre fundo grafite, destaques ciano e verde para status. Ícones simples, nomes curtos.

## Paleta

| Uso | Cor | Hex |
|---|---|---|
| Fundo | Grafite azulado | `#101722` |
| Superfície / cartões | Azul petróleo escuro | `#1D2939` |
| Principal / destaque | Ciano | `#38BDF8` |
| Disponível / operações | Verde | `#22C55E` |
| Texto | Gelo | `#E6EDF5` |

Aplicação automática pelo script: cor dos embeds das mensagens (ciano; verde no canal da equipe) e cores dos cargos:

| Grupo | Cargos e cores |
|---|---|
| Equipe | 👑 Líder Fundador `#F1C40F` · 🛡️ Administração `#E74C3C` · ⚔️ Moderador `#E67E22` · 🧭 Organizador `#2ECC71` |
| Apoio | 💎 VIP `#A855F7` |
| Patentes (oficiais superiores) | ★★★ Coronel `#D4AF37` · ★★ Tenente-Coronel `#DDBF5A` · ★ Major `#E6CF7E` |
| Patentes (oficiais) | ☆☆☆ Capitão `#C0C7D1` · ☆ Tenente `#D5DBE3` |
| Patentes (praças) | ❯❯❯ Sargento `#7FA34A` · ❯❯ Cabo `#93B562` · ❯ Soldado `#A7C47D` |
| Reconhecimento | 🎖️ Veterano `#38BDF8` · 🤝 Colaborador `#7DD3FC` · 👤 Membro `#94A3B8` · 🌱 Novato `#CBD5E1` |
| Jogos | 🌿 Wildlands `#65A30D` · 💀 Breakpoint `#78716C` · 👮 Siege `#3B82F6` |
| Plataformas | 🖥️ PC `#9CA3AF` · 🟩 Xbox `#16A34A` · 🟦 PlayStation `#2563EB` |
| Estilos | 😎 Casual `#FACC15` · 🌑 Furtivo `#475569` · 🎯 Tático `#DC2626` · 🌎 Livre `#14B8A6` |
| Notificações | 🔔 Eventos `#F59E0B` · 📢 Operações `#F97316` |

O nome de cada membro aparece na cor do cargo **mais alto** que ele tem.

Cores de cargo editáveis em `gr_setup\estrutura.py` (o próximo `aplicar` sincroniza).

## Ícone do servidor (manual)

- Arte própria: por exemplo, um **retículo/mira estilizado** ou **silhueta de capacete com visor** em ciano sobre `#101722`, com as iniciais **GRB**.
- 512×512 px no mínimo, legível em 32 px, sem texto pequeno.
- **Não use** a caveira/logotipo da franquia, logos da Ubisoft ou do Rainbow Six, artes oficiais ou capturas com marcas d'água. Não use “Oficial” no nome.
- Envio: **Configurações do Servidor** > **Perfil do Servidor** > **Ícone**.

## Banner, plano de fundo do convite e outros

Dependem do nível de impulsos do servidor (o painel indica o requisito de cada item). Sugestão de arte: faixa `#101722` → `#1D2939` com linhas de topografia em ciano 20% e o slogan **“Nenhum operador fica para trás.”** em `#E6EDF5`.

Ícones de cargo (emoji/imagem ao lado do nome) também dependem de impulsos; quando disponíveis: 🛡️ equipe, 💎 VIP, 🎖️ Veterano.

## Convenção de nomes

- Categorias: `╭─── emoji Nome` (ex.: `╭─── 💀 Breakpoint`).
- Canais de texto: `emoji｜nome-em-minúsculas` (ex.: `🔥｜squad-raid`). O Discord não aceita espaços em canais de texto, por isso usamos a barra larga `｜`.
- Voz: `emoji Nome` (ex.: `💀 Breakpoint PC 1`, `👮 Radio 01`, `🔊 Bate Papo (GERAL)`).
- Emoji com significado: 💀 Breakpoint, 🌿 Wildlands, 👮 Siege, 🔥 raids, 🏅 VIP.
- Patentes demonstrativas: `★★★ Coronel`, `★★ Tenente-Coronel`, `★ Major`, `☆☆☆ Capitão`, `☆ Tenente`, `❯❯❯ Sargento`, `❯❯ Cabo`, `❯ Soldado`.
- Todos os cargos têm emoji no início (👑 Líder Fundador, 🛡️ Administração, ⚔️ Moderador, 🧭 Organizador, 💎 VIP, 🎖️ Veterano…).

## Aviso de não afiliação

Inclua em descrição pública, `#boas-vindas` (já incluso) e artes: *“Comunidade de fãs, sem afiliação com a Ubisoft.”* Tom Clancy's, Ghost Recon e Rainbow Six são marcas de seus respectivos donos.
