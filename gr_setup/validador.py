"""Validação da estrutura final e das permissões EFETIVAS (somente leitura)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from . import estrutura as E
from .mensagens import MENSAGENS
from .permissoes import P, PODERES, nomes, permissoes_base, permissoes_canal
from .provisionador import (TIPO_ANUNCIO, TIPO_VOZ, Contexto, Estado, classe_planejada,
                            classe_tipo, slug)

OK, FALHA, PENDENTE, AVISO, INFO = "OK", "FALHA", "PENDENTE", "AVISO", "INFO"


@dataclass
class Checagem:
    numero: str
    descricao: str
    status: str
    detalhe: str = ""


class Resolucao:
    """Localiza os recursos do projeto (estado salvo -> nome), sem alterar nada."""

    def __init__(self, ctx: Contexto, estado: Estado):
        self.ctx = ctx
        self.cargos: dict[str, dict] = {}
        self.categorias: dict[str, dict] = {}
        self.canais: dict[str, dict] = {}
        salvos = estado.dados
        for c in E.CARGOS:
            r = ctx.roles.get(salvos["cargos"].get(c.chave, ""))
            if r is None:
                cand = [x for x in ctx.roles.values()
                        if not x.get("managed") and slug(x["name"]) == slug(c.nome)]
                r = max(cand, key=lambda x: x["position"]) if cand else None
            if r:
                self.cargos[c.chave] = r
        for cat in E.CATEGORIAS:
            ch = ctx.channels.get(salvos["categorias"].get(cat.chave, ""))
            if ch is None:
                cand = [x for x in ctx.channels.values()
                        if classe_tipo(x["type"]) == "categoria" and slug(x["name"]) == slug(cat.nome)]
                ch = sorted(cand, key=lambda x: int(x["id"]))[0] if cand else None
            if ch:
                self.categorias[cat.chave] = ch
            pid = ch["id"] if ch else None
            for canal in cat.canais:
                x = ctx.channels.get(salvos["canais"].get(canal.chave, ""))
                if x is None:
                    cand = [y for y in ctx.channels.values()
                            if classe_tipo(y["type"]) == classe_planejada(canal)
                            and slug(y["name"]) == slug(canal.nome)]
                    cand = [y for y in cand if y.get("parent_id") == pid]
                    x = sorted(cand, key=lambda y: int(y["id"]))[0] if cand else None
                if x:
                    self.canais[canal.chave] = x


class Validador:
    def __init__(self, ctx: Contexto, estado: Estado):
        self.ctx = ctx
        self.res = Resolucao(ctx, estado)
        self.checks: list[Checagem] = []
        self.role_perms = {rid: int(r["permissions"]) for rid, r in ctx.roles.items()}

    # -- utilidades ---------------------------------------------------------
    def add(self, numero, desc, ok: bool | None, detalhe="", status_falso=FALHA):
        status = OK if ok else (status_falso if ok is not None else PENDENTE)
        self.checks.append(Checagem(numero, desc, status, detalhe))

    def _persona(self, *chaves: str) -> list[str]:
        base = ["membro", "plat_pc", "jogo_breakpoint", "estilo_casual", "notif_eventos"]
        return [self.res.cargos[k]["id"] for k in base + list(chaves) if k in self.res.cargos]

    def efetivas(self, canal_chave: str, *extras: str) -> int | None:
        ch = self.res.canais.get(canal_chave)
        if ch is None:
            return None
        roles = self._persona(*extras)
        base = permissoes_base(self.role_perms, self.ctx.everyone_id, roles)
        return permissoes_canal(base, ch.get("permission_overwrites", []), self.ctx.everyone_id,
                                roles, canal_voz=ch["type"] == TIPO_VOZ)

    def pode(self, canal_chave, perm, *extras) -> bool | None:
        e = self.efetivas(canal_chave, *extras)
        return None if e is None else bool(e & perm)

    # -- checagens ------------------------------------------------------------
    def executar(self) -> list[Checagem]:
        r = self.res
        # 1 - categorias
        faltando = [c.nome for c in E.CATEGORIAS if c.chave not in r.categorias]
        self.add("1", "Todas as categorias existem", not faltando,
                 f"Faltando: {faltando}" if faltando else f"{len(E.CATEGORIAS)} categorias")

        # 2 - canais nas categorias corretas
        errados, ausentes = [], []
        for cat, canal in E.todos_os_canais():
            ch = r.canais.get(canal.chave)
            if ch is None:
                ausentes.append(canal.nome)
            elif cat.chave in r.categorias and ch.get("parent_id") != r.categorias[cat.chave]["id"]:
                errados.append(canal.nome)
        self.add("2", "Canais existem e estão nas categorias corretas", not errados and not ausentes,
                 f"Ausentes: {ausentes} | Fora da categoria: {errados}" if (errados or ausentes)
                 else f"{sum(1 for _ in E.todos_os_canais())} canais conferidos")

        # 3/4 - salas fixas de Breakpoint/Wildlands foram substituídas pelos squads do bot
        sobras = [c["name"] for c in self.ctx.channels.values()
                  if c["type"] == 4 and slug(c["name"]) in (slug("╭─── 💀 Breakpoint | Salas"),
                                                           slug("╭─── 🌿 Wildlands | Salas"))]
        self.add("3", "Salas fixas antigas removidas (squads pelo bot)", not sobras,
                 f"Ainda existem: {sobras}. Use /squads remover-salas" if sobras else "")
        # 5 - Radios do Siege
        for numero, chave, esperado in (("5", "r6", 4),):
            cat = r.categorias.get(chave)
            qtd = 0
            por_plat = {}
            if cat:
                filhos = [c for c in self.ctx.channels.values()
                          if c.get("parent_id") == cat["id"] and c["type"] == TIPO_VOZ]
                qtd = len(filhos)
                for f in filhos:
                    m = re.search(r"(pc|xbox|ps)[\s-]*\d+$", f["name"], re.IGNORECASE)
                    if m:
                        por_plat[m.group(1).lower()] = por_plat.get(m.group(1).lower(), 0) + 1
            nome = next(c.nome for c in E.CATEGORIAS if c.chave == chave)
            ok = qtd == esperado and (chave == "r6" or por_plat == {"pc": 4, "xbox": 4, "ps": 4})
            self.add(numero, f"Exatamente {esperado} salas de voz em '{nome}'", ok,
                     f"Encontradas {qtd} {por_plat if por_plat else ''}".strip())

        # 6 - salas gerais
        ok6 = all(r.canais.get(k, {}).get("type") == TIPO_VOZ for k in ("voz_breakpoint", "voz_wildlands"))
        self.add("6", "Salas de voz gerais de Breakpoint e Wildlands identificadas", ok6,
                 ", ".join(r.canais[k]["name"] for k in ("voz_breakpoint", "voz_wildlands") if k in r.canais))

        # 7 - anúncios
        pode_enviar = self.pode("anuncios", P.SEND_MESSAGES)
        pode_thread = self.pode("anuncios", P.CREATE_PUBLIC_THREADS)
        self.add("7", "#anuncios: membro comum não envia mensagens nem cria threads",
                 None if pode_enviar is None else not (pode_enviar or pode_thread))
        adm = self.pode("anuncios", P.SEND_MESSAGES, "administracao")
        self.add("7b", "#anuncios: Administração pode publicar", adm)
        tipo = r.canais.get("anuncios", {}).get("type")
        if self.ctx.comunidade:
            self.add("7c", "#anuncios é do tipo Anúncio", tipo == TIPO_ANUNCIO,
                     "" if tipo == TIPO_ANUNCIO else "Execute 'aplicar' novamente para converter.")
        else:
            self.add("7c", "#anuncios é do tipo Anúncio", None,
                     "Requer Comunidade ativada; depois execute 'aplicar' novamente.")

        # 8 - regras e boas-vindas
        for k in ("regras", "boas_vindas", "comece_aqui"):
            ver = self.pode(k, P.VIEW_CHANNEL | P.READ_MESSAGE_HISTORY)
            env = self.pode(k, P.SEND_MESSAGES)
            eq = self.pode(k, P.SEND_MESSAGES, "administracao")
            self.add("8", f"#{slug(r.canais[k]['name']) if k in r.canais else k}: todos leem, "
                     f"só a equipe publica", None if ver is None else (ver and not env and eq))

        # 9 - MODS pública e EQUIPE privada
        ver_mods = all(self.pode(c.chave, P.VIEW_CHANNEL) for c in next(x for x in E.CATEGORIAS if x.chave == "mods").canais)
        so_leitura = all(self.pode(k, P.SEND_MESSAGES) is False
                         for k in ("mods_publicados", "regras_mods", "publicar_mod"))
        disc = self.pode("discussao_mods", P.SEND_MESSAGES)
        self.add("9a", "Categoria MODS (modificações dos jogos) é pública, com canais de consulta "
                 "somente leitura", ver_mods and so_leitura and disc)
        equipe = next(c for c in E.CATEGORIAS if c.chave == "equipe")
        oculto = all(self.pode(c.chave, P.VIEW_CHANNEL) is False for c in equipe.canais)
        oculto_vip = all(self.pode(c.chave, P.VIEW_CHANNEL, "vip") is False for c in equipe.canais)
        mod_ve = all(self.pode(c.chave, P.VIEW_CHANNEL, "moderador") for c in equipe.canais)
        org = (self.pode("chat_equipe", P.VIEW_CHANNEL, "organizador")
               and self.pode("logs_moderacao", P.VIEW_CHANNEL, "organizador") is False)
        self.add("9b", "Categoria EQUIPE é privada (membros e VIPs não veem; Moderador vê; "
                 "Organizador só chat e reunião)", oculto and oculto_vip and mod_ve and org)

        # 10/11 - cargos sem poderes
        for numero, grupo, desc in (
            ("10", ("apoio",), "VIP não possui permissões administrativas"),
            ("11", ("plataforma",), "Cargos de plataforma não concedem privilégios"),
            ("11b", ("jogo", "estilo", "notificacao", "reconhecimento", "patente"),
             "Cargos de patente, jogo, estilo, notificação e reconhecimento não concedem privilégios"),
        ):
            problemas = [c.nome for c in E.CARGOS if c.grupo in grupo and c.chave in r.cargos
                         and int(r.cargos[c.chave]["permissions"]) & int(PODERES)]
            faltam = [c.nome for c in E.CARGOS if c.grupo in grupo and c.chave not in r.cargos]
            self.add(numero, desc, not problemas and not faltam,
                     f"Com poderes: {problemas} | Ausentes: {faltam}" if (problemas or faltam) else "")
        self.add("10b", "VIP pode conversar em #vips; membro comum só lê",
                 self.pode("vips", P.SEND_MESSAGES, "vip") and self.pode("vips", P.SEND_MESSAGES) is False)

        # 12 - suporte
        sup = [self.pode(k, P.SEND_MESSAGES) for k in ("suporte_geral", "suporte_dicas", "duvidas")]
        self.add("12", "#suporte-geral, #suporte-dicas e #duvidas aceitam mensagens de membros",
                 None if None in sup else all(sup))

        # 13 - denúncias
        d = self.efetivas("denuncias")
        self.add("13", "#denuncias não expõe relatos (membro comum não escreve, não cria thread, não reage)",
                 None if d is None else not d & (P.SEND_MESSAGES | P.CREATE_PUBLIC_THREADS
                                                 | P.CREATE_PRIVATE_THREADS | P.ADD_REACTIONS
                                                 | P.SEND_MESSAGES_IN_THREADS))

        # 14 - lives
        lv = r.canais.get("lives", {})
        self.add("14", "#divulgacao-de-lives: membros publicam com modo lento; equipe/dono publicam sem limite",
                 None if not lv else (self.pode("lives", P.SEND_MESSAGES)
                                      and int(lv.get("rate_limit_per_user") or 0) > 0
                                      and self.pode("lives", P.BYPASS_SLOWMODE, "administracao")),
                 f"Modo lento: {lv.get('rate_limit_per_user')}s. O dono do servidor ignora o modo lento.")

        # 15 - canais de bots futuros
        sem_cmd = all(not re.search(r"(^|\s)/[a-z]", m["texto"]) for v in MENSAGENS.values() for m in v)
        self.add("15", "Canais para bots futuros não anunciam funcionalidades inexistentes",
                 sem_cmd and self.pode("comandos", P.SEND_MESSAGES) is False
                 and self.pode("publicar_mod", P.SEND_MESSAGES) is False,
                 "Textos sem comandos de barra; #comandos e #publicar-mod em somente leitura")

        # 16 - duplicações
        dup = []
        for cat, canal in E.todos_os_canais():
            ch = r.canais.get(canal.chave)
            if ch:
                iguais = [c for c in self.ctx.channels.values() if c.get("parent_id") == ch.get("parent_id")
                          and classe_tipo(c["type"]) == classe_tipo(ch["type"]) and slug(c["name"]) == slug(ch["name"])]
                if len(iguais) > 1:
                    dup.append(canal.nome)
        for cat in E.CATEGORIAS:
            iguais = [c for c in self.ctx.channels.values()
                      if classe_tipo(c["type"]) == "categoria" and slug(c["name"]) == slug(cat.nome)]
            if len(iguais) > 1:
                dup.append(cat.nome)
        for c in E.CARGOS:
            iguais = [x for x in self.ctx.roles.values() if slug(x["name"]) == slug(c.nome)]
            if len(iguais) > 1:
                dup.append(f"cargo {c.nome}")
        self.add("16", "Sem categorias, canais ou cargos duplicados", not dup, f"Duplicados: {dup}" if dup else "")

        # Extras de segurança
        voz_ok = all(self.pode(k, P.CONNECT | P.SPEAK) and not self.pode(k, P.MUTE_MEMBERS | P.MOVE_MEMBERS)
                     for k in ("radio_1", "voz_breakpoint", "voz_wildlands"))
        self.add("E1", "Salas de voz: membros entram e falam, sem poderes de moderação", voz_ok)
        org = r.cargos.get("organizador")
        self.add("E2", "Organizador de Operações não bane nem expulsa",
                 org is not None and not int(org["permissions"]) & (P.BAN_MEMBERS | P.KICK_MEMBERS))
        mod = r.cargos.get("moderador")
        self.add("E3", "Moderador não administra servidor, cargos ou canais",
                 mod is not None and not int(mod["permissions"]) & (P.ADMINISTRATOR | P.MANAGE_GUILD
                                                                   | P.MANAGE_ROLES | P.MANAGE_CHANNELS))
        admin = r.cargos.get("administracao")
        self.add("E4", "Administração não tem a permissão Administrador",
                 admin is not None and not int(admin["permissions"]) & P.ADMINISTRATOR)
        lider = r.cargos.get("lider")
        self.add("E5", "Líder Fundador com Administrador (ativação manual pelo dono)",
                 None if lider is None or not int(lider["permissions"]) & P.ADMINISTRATOR else True,
                 "Ative manualmente: Configurações do Servidor > Cargos > Líder Fundador > Permissões.")
        ordem = [r.cargos[c.chave] for c in E.CARGOS if c.chave in r.cargos]
        ordenado = sorted(ordem, key=lambda x: (x["position"], int(x["id"])), reverse=True)
        self.add("E6", "Hierarquia dos cargos na ordem planejada", [x["id"] for x in ordem] == [x["id"] for x in ordenado])
        mencao = [k for k in ("geral", "squad_partida", "clips") if self.pode(k, P.MENTION_EVERYONE)]
        self.add("E7", "Membros comuns não mencionam @everyone/@here nos canais do projeto", not mencao,
                 f"Problema em: {mencao}" if mencao else "")
        everyone_perm = self.role_perms.get(self.ctx.everyone_id, 0)
        perigosas = everyone_perm & int(PODERES & ~P.MENTION_EVERYONE)
        self.add("E8", "@everyone sem permissões de moderação no nível do servidor", not perigosas,
                 ", ".join(nomes(perigosas)))

        # Configurações manuais (lidas do servidor)
        g = self.ctx.guild
        self.add("M1", "Comunidade ativada", self.ctx.comunidade or None)
        self.add("M2", "Nível de verificação ≥ Baixo (e-mail verificado)",
                 (g.get("verification_level", 0) >= 1) or None, f"Atual: {g.get('verification_level')}")
        self.add("M3", "Filtro de conteúdo explícito para todos os membros",
                 (g.get("explicit_content_filter", 0) == 2) or None, f"Atual: {g.get('explicit_content_filter')}")
        self.add("M4", "2FA exigida para ações de moderação", (g.get("mfa_level", 0) == 1) or None,
                 "Somente o dono ativa, e precisa ter 2FA na própria conta.")
        regras = r.canais.get("regras")
        self.add("M5", "Canal de regras definido como #regras",
                 (regras is not None and g.get("rules_channel_id") == regras["id"]) or None)
        eq = r.canais.get("chat_equipe")
        self.add("M6", "Canal de atualizações da comunidade é privado da equipe",
                 (eq is not None and g.get("public_updates_channel_id") == eq["id"]) or None,
                 "Recomendado: #chat-da-equipe")
        self.add("M7", "Idioma principal Português (Brasil)", (g.get("preferred_locale") == "pt-BR") or None,
                 f"Atual: {g.get('preferred_locale')}")
        self.add("M8", "Descrição do servidor preenchida", bool(g.get("description")) or None)

        # Descoberta (informativo)
        membros = g.get("approximate_member_count") or 0
        criado = datetime.fromtimestamp(((int(g["id"]) >> 22) + 1420070400000) / 1000, tz=timezone.utc)
        semanas = (datetime.now(timezone.utc) - criado).days // 7
        self.checks.append(Checagem("D1", "Descoberta: mínimo de 1.000 membros", INFO if membros < 1000 else OK,
                                    f"Atual: {membros}"))
        self.checks.append(Checagem("D2", "Descoberta: servidor com pelo menos 8 semanas", INFO if semanas < 8 else OK,
                                    f"Idade: {semanas} semana(s), criado em {criado:%d/%m/%Y}"))
        self.checks.append(Checagem("D3", "Descoberta: já habilitada",
                                    OK if "DISCOVERABLE" in g.get("features", []) else INFO,
                                    "A aprovação depende de requisitos verificados pelo Discord."))
        return self.checks
