"""Criação/correção idempotente de cargos, categorias e canais."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import estrutura as E
from .discord_api import DiscordAPI, ErroAPI
from .permissoes import P, nomes, permissoes_base

log = logging.getLogger("gr_setup")

TIPO_TEXTO, TIPO_VOZ, TIPO_CATEGORIA, TIPO_ANUNCIO = 0, 2, 4, 5
TIPOS_TEXTUAIS = (TIPO_TEXTO, TIPO_ANUNCIO)


def slug(nome: str) -> str:
    nome = nome.split("・", 1)[1] if "・" in nome else nome
    nome = re.sub(r"^[^\w]+", "", nome, flags=re.UNICODE)
    return re.sub(r"\s+", " ", nome).strip().casefold()


def classe_tipo(tipo: int) -> str:
    if tipo in TIPOS_TEXTUAIS:
        return "texto"
    if tipo in (TIPO_VOZ, 13):
        return "voz"
    if tipo == TIPO_CATEGORIA:
        return "categoria"
    return f"outro-{tipo}"


def classe_planejada(canal: E.Canal) -> str:
    return "voz" if canal.tipo == "voz" else "texto"


@dataclass
class Resultado:
    criados: list[str] = field(default_factory=list)
    existentes: list[str] = field(default_factory=list)
    corrigidos: list[str] = field(default_factory=list)
    falhas: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    nao_gerenciados: list[str] = field(default_factory=list)

    def como_dict(self):
        return self.__dict__.copy()


class Estado:
    """Mapa chave -> ID salvo em disco (não contém segredos)."""

    def __init__(self, caminho: Path, simular: bool):
        self.caminho = caminho
        self.simular = simular
        self.dados = {"cargos": {}, "categorias": {}, "canais": {}, "mensagens": {}, "nomes_aceitos": {}}
        if caminho.exists():
            try:
                self.dados.update(json.loads(caminho.read_text(encoding="utf-8")))
                self.dados.setdefault("nomes_aceitos", {})
            except ValueError:
                log.warning("Arquivo de estado corrompido; será recriado: %s", caminho)

    def salvar(self):
        if self.simular:
            return
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.caminho.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.dados, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.caminho)


class Contexto:
    """Carrega e mantém o retrato atual do servidor."""

    def __init__(self, api: DiscordAPI, guild_id: str):
        self.api = api
        self.gid = guild_id
        self.recarregar()

    def recarregar(self):
        self.bot = self.api.eu()
        self.guild = self.api.servidor(self.gid)
        self.roles = {r["id"]: r for r in self.api.cargos(self.gid)}
        self.channels = {c["id"]: c for c in self.api.canais(self.gid)}
        self.bot_member = self.api.membro(self.gid, self.bot["id"])

    @property
    def everyone_id(self):
        return self.gid

    @property
    def comunidade(self) -> bool:
        return "COMMUNITY" in self.guild.get("features", [])

    @property
    def bot_role_id(self) -> str | None:
        for rid in self.bot_member.get("roles", []):
            r = self.roles.get(rid)
            if r and r.get("managed") and (r.get("tags") or {}).get("bot_id") == self.bot["id"]:
                return rid
        return None

    @property
    def bot_topo(self) -> int:
        pos = [self.roles[r]["position"] for r in self.bot_member.get("roles", []) if r in self.roles]
        return max(pos) if pos else 0

    def bot_permissoes(self) -> int:
        rp = {rid: int(r["permissions"]) for rid, r in self.roles.items()}
        return permissoes_base(rp, self.everyone_id, self.bot_member.get("roles", []),
                               eh_dono=self.guild.get("owner_id") == self.bot["id"])


class Provisionador:
    def __init__(self, api: DiscordAPI, ctx: Contexto, estado: Estado, simular: bool,
                 adotar_existentes: bool = False):
        self.api = api
        self.ctx = ctx
        self.estado = estado
        self.simular = simular
        self.adotar = adotar_existentes
        self.r = Resultado()
        self.ids_cargos: dict[str, str] = {}      # chave -> id
        self.gerenciados_cargos: set[str] = set()
        self.ids_cat: dict[str, str] = {}
        self.gerenciados_canais: set[str] = set()  # ids
        self.ids_canais: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Verificações prévias
    # ------------------------------------------------------------------
    def verificacoes_previas(self, nome_esperado: str) -> list[str]:
        bloqueios = []
        g = self.ctx.guild
        log.info("Servidor encontrado: %s (ID %s)", g["name"], g["id"])
        if nome_esperado and g["name"].strip() != nome_esperado.strip():
            bloqueios.append(
                f"O nome do servidor é '{g['name']}', mas o esperado (DISCORD_GUILD_NAME) é "
                f"'{nome_esperado}'. Confira o ID ou ajuste DISCORD_GUILD_NAME no .env.")
        perms = self.ctx.bot_permissoes()
        if perms & P.ADMINISTRATOR:
            self.r.avisos.append("O bot está com permissão Administrador. Funciona, mas não é o mínimo "
                                 "necessário. Prefira o convite gerado por 'python main.py convite'.")
        else:
            faltando = E.permissoes_necessarias_do_bot() & ~perms
            if faltando:
                bloqueios.append("O bot não possui as permissões necessárias: " + ", ".join(nomes(faltando))
                                 + ". Reautorize-o com o link de 'python main.py convite'.")
        if not self.ctx.bot_role_id:
            self.r.avisos.append("Cargo gerenciado do bot não encontrado; canais privados podem ficar "
                                 "invisíveis para o bot.")
        if not self.ctx.comunidade:
            self.r.avisos.append("A Comunidade ainda não está ativada: #anuncios será criado como texto e "
                                 "convertido para canal de anúncios quando você ativar a Comunidade e "
                                 "executar 'aplicar' novamente.")
        total = len(self.ctx.channels)
        if total + E.resumo_contagem()["total_canais"] > 500:
            self.r.avisos.append(f"O servidor já tem {total} canais; o limite do Discord é 500.")
        if len(self.ctx.roles) + len(E.CARGOS) > 250:
            self.r.avisos.append(f"O servidor já tem {len(self.ctx.roles)} cargos; o limite é 250.")
        return bloqueios

    # ------------------------------------------------------------------
    # Cargos
    # ------------------------------------------------------------------
    def _corpo_cargo(self, c: E.Cargo, usar_cor_legada=False) -> dict:
        corpo = {"name": c.nome, "permissions": str(c.permissoes), "hoist": c.separado,
                 "mentionable": c.mencionavel}
        if usar_cor_legada:
            corpo["color"] = c.cor
        else:
            corpo["colors"] = {"primary_color": c.cor, "secondary_color": None, "tertiary_color": None}
        return corpo

    def _nome_ok(self, chave_estado: str, atual: str, desejado: str) -> bool:
        """Compara nomes tolerando a normalização que o Discord aplica (ex.: espaços em canais de texto)."""
        if atual == desejado or atual == self.estado.dados["nomes_aceitos"].get(chave_estado):
            return True
        return atual.casefold().replace(" ", "-") == desejado.casefold().replace(" ", "-")

    def _aceitar_nome(self, chave_estado: str, desejado: str, retornado: str):
        if retornado != desejado:
            self.estado.dados["nomes_aceitos"][chave_estado] = retornado

    def _cor_atual(self, role) -> int:
        cores = role.get("colors") or {}
        return int(cores.get("primary_color", role.get("color", 0)) or 0)

    def cargos(self):
        log.info("\n== Cargos ==")
        salvos = self.estado.dados["cargos"]
        por_nome = {}
        for r in self.ctx.roles.values():
            if not r.get("managed") and r["id"] != self.ctx.everyone_id:
                por_nome.setdefault(slug(r["name"]), []).append(r)
        for c in E.CARGOS:
            role = self.ctx.roles.get(salvos.get(c.chave, ""))
            gerenciado = role is not None
            if role is None:
                candidatos = por_nome.get(slug(c.nome), [])
                if len(candidatos) > 1:
                    self.r.avisos.append(f"Há {len(candidatos)} cargos chamados '{c.nome}'; usando o mais alto.")
                if candidatos:
                    role = max(candidatos, key=lambda x: x["position"])
                    gerenciado = self.adotar
            if role is None:
                self._criar_cargo(c)
                continue
            self.ids_cargos[c.chave] = role["id"]
            if gerenciado:
                self.gerenciados_cargos.add(c.chave)
                salvos[c.chave] = role["id"]
                self._corrigir_cargo(c, role)
            else:
                self.r.nao_gerenciados.append(f"Cargo '{c.nome}' já existia e não foi alterado "
                                              f"(use --adotar-existentes para gerenciá-lo).")
                if int(role["permissions"]) != c.permissoes:
                    self.r.avisos.append(f"Cargo preexistente '{c.nome}' tem permissões diferentes do "
                                         f"projeto: {', '.join(nomes(int(role['permissions']))) or 'nenhuma'}.")
        self.estado.salvar()

    def _criar_cargo(self, c: E.Cargo):
        desc = f"Cargo '{c.nome}'"
        if self.simular:
            self.ids_cargos[c.chave] = f"sim-cargo-{c.chave}"
            self.gerenciados_cargos.add(c.chave)
            self.r.criados.append(desc + " (simulação)")
            log.info("  [SIMULAÇÃO] criaria %s", desc)
            return
        try:
            try:
                novo = self.api.post(f"/guilds/{self.ctx.gid}/roles", self._corpo_cargo(c))
            except ErroAPI as e:
                if e.status == 400 and "colors" in json.dumps(e.corpo):
                    novo = self.api.post(f"/guilds/{self.ctx.gid}/roles", self._corpo_cargo(c, True))
                else:
                    raise
        except ErroAPI as e:
            self.r.falhas.append(f"{desc}: {e}")
            log.error("  FALHA ao criar %s: %s", desc, e)
            return
        self.ctx.roles[novo["id"]] = novo
        self.ids_cargos[c.chave] = novo["id"]
        self.gerenciados_cargos.add(c.chave)
        self.estado.dados["cargos"][c.chave] = novo["id"]
        self.estado.salvar()
        self.r.criados.append(desc)
        log.info("  + criado %s", desc)

    def _corrigir_cargo(self, c: E.Cargo, role):
        desc = f"Cargo '{c.nome}'"
        dif = {}
        if not self._nome_ok(f"cargos:{c.chave}", role["name"], c.nome):
            dif["name"] = c.nome
        if int(role["permissions"]) != c.permissoes:
            dif["permissions"] = str(c.permissoes)
        if bool(role.get("hoist")) != c.separado:
            dif["hoist"] = c.separado
        if bool(role.get("mentionable")) != c.mencionavel:
            dif["mentionable"] = c.mencionavel
        if self._cor_atual(role) != c.cor:
            dif["colors"] = {"primary_color": c.cor, "secondary_color": None, "tertiary_color": None}
        if c.chave == "lider" and int(role["permissions"]) & P.ADMINISTRATOR:
            # O dono ativou Administrador manualmente: respeitar.
            dif.pop("permissions", None)
        if not dif:
            self.r.existentes.append(desc)
            log.info("  = já existe %s", desc)
            return
        if role["position"] >= self.ctx.bot_topo:
            self.r.avisos.append(f"{desc} está acima do cargo do bot; diferenças não corrigidas: {list(dif)}")
            return
        if self.simular:
            self.r.corrigidos.append(f"{desc}: {list(dif)} (simulação)")
            log.info("  [SIMULAÇÃO] corrigiria %s: %s", desc, list(dif))
            return
        try:
            atualizado = self.api.patch(f"/guilds/{self.ctx.gid}/roles/{role['id']}", dif)
            self.ctx.roles[role["id"]] = atualizado
            if "name" in dif:
                self._aceitar_nome(f"cargos:{c.chave}", c.nome, atualizado["name"])
            self.r.corrigidos.append(f"{desc}: {list(dif)}")
            log.info("  ~ corrigido %s: %s", desc, list(dif))
        except ErroAPI as e:
            self.r.falhas.append(f"Corrigir {desc}: {e}")
            log.error("  FALHA ao corrigir %s: %s", desc, e)

    def ordenar_cargos(self):
        """Ordena os cargos do projeto entre si, reutilizando as posições que já ocupam."""
        if not self.simular:
            # Cada criação desloca as posições dos demais cargos (inclusive o do bot):
            # é preciso reler a lista atual antes de calcular a ordem.
            self.ctx.roles = {r["id"]: r for r in self.api.cargos(self.ctx.gid)}
        gerenciados = [c for c in E.CARGOS if c.chave in self.gerenciados_cargos
                       and self.ids_cargos.get(c.chave, "").isdigit()]
        if len(gerenciados) < 2:
            return
        roles = [self.ctx.roles[self.ids_cargos[c.chave]] for c in gerenciados]
        atual = sorted(roles, key=lambda r: (r["position"], int(r["id"])), reverse=True)
        desejado_ids = [self.ids_cargos[c.chave] for c in gerenciados]
        if [r["id"] for r in atual] == desejado_ids:
            self.r.existentes.append("Hierarquia de cargos já está na ordem planejada")
            return
        posicoes = sorted((r["position"] for r in roles), reverse=True)
        if len(set(posicoes)) != len(posicoes):
            base = min(posicoes)
            posicoes = list(range(base + len(posicoes) - 1, base - 1, -1))
        if max(posicoes) >= self.ctx.bot_topo:
            self.r.falhas.append(f"Não foi possível ordenar os cargos (posição do cargo do bot: {self.ctx.bot_topo}; "
                                 f"posições necessárias: {min(posicoes)}–{max(posicoes)}). Arraste o cargo do bot "
                                 "para o topo da lista em Configurações do Servidor > Cargos, ou ordene os cargos "
                                 "manualmente, e execute novamente.")
            return
        corpo = [{"id": rid, "position": pos} for rid, pos in zip(desejado_ids, posicoes)]
        if self.simular:
            self.r.corrigidos.append("Ordem da hierarquia de cargos (simulação)")
            return
        try:
            novos = self.api.patch(f"/guilds/{self.ctx.gid}/roles", corpo)
            for r in novos:
                self.ctx.roles[r["id"]] = r
            self.r.corrigidos.append("Ordem da hierarquia de cargos")
            log.info("  ~ hierarquia de cargos ordenada")
        except ErroAPI as e:
            self.r.falhas.append(f"Ordenar cargos: {e}")

    # ------------------------------------------------------------------
    # Overwrites
    # ------------------------------------------------------------------
    def _alvo_id(self, alvo: str) -> str | None:
        if alvo == "@everyone":
            return self.ctx.everyone_id
        if alvo == "@bot":
            return self.ctx.bot_role_id
        return self.ids_cargos.get(alvo)

    def _ids_controlados(self) -> set[str]:
        ids = {self.ctx.everyone_id}
        if self.ctx.bot_role_id:
            ids.add(self.ctx.bot_role_id)
        ids.update(v for v in self.ids_cargos.values())
        return ids

    def overwrites_api(self, ow: E.Overwrites) -> list[dict]:
        ow = dict(ow)
        ow["@bot"] = (E.permissoes_canal_do_bot(), 0)
        saida = []
        for alvo, (a, d) in ow.items():
            tid = self._alvo_id(alvo)
            if tid is None:
                if alvo != "@bot":
                    self.r.avisos.append(f"Alvo de permissão '{alvo}' sem ID; ignorado.")
                continue
            saida.append({"id": tid, "type": 0, "allow": str(a), "deny": str(d)})
        return saida

    @staticmethod
    def _norm_ow(lista: list[dict], ids: set[str] | None = None) -> dict:
        out = {}
        for o in lista:
            if ids is not None and str(o["id"]) not in ids:
                continue
            a, d = int(o.get("allow", 0)), int(o.get("deny", 0))
            if a or d:
                out[str(o["id"])] = (a, d)
        return out

    # ------------------------------------------------------------------
    # Categorias e canais
    # ------------------------------------------------------------------
    def _procurar(self, nome: str, classe: str, parent_id: str | None, chave_estado: str,
                  secao: str):
        salvo = self.estado.dados[secao].get(chave_estado)
        if salvo and salvo in self.ctx.channels:
            return self.ctx.channels[salvo], True
        alvo = slug(nome)
        candidatos = [c for c in self.ctx.channels.values()
                      if classe_tipo(c["type"]) == classe and slug(c["name"]) == alvo
                      and c["id"] not in self.gerenciados_canais]
        if classe != "categoria":
            # Só reconhece canais na categoria esperada: evita confundir, por exemplo,
            # o #geral padrão criado pelo Discord com o #geral do projeto.
            candidatos = [c for c in candidatos if c.get("parent_id") == parent_id]
        if candidatos:
            c = sorted(candidatos, key=lambda x: int(x["id"]))[0]
            return c, self.adotar
        return None, False

    def categorias_e_canais(self):
        log.info("\n== Categorias e canais ==")
        for i_cat, cat in enumerate(E.CATEGORIAS):
            existente, gerenciado = self._procurar(cat.nome, "categoria", None, cat.chave, "categorias")
            cat_id = self._garantir(
                existente, gerenciado, f"Categoria '{cat.nome}'", "categorias", cat.chave,
                {"name": cat.nome, "type": TIPO_CATEGORIA, "position": i_cat},
                cat.overwrites, parent_id=None, planejado=None)
            self.ids_cat[cat.chave] = cat_id
            if not cat_id:
                for canal in cat.canais:
                    self.r.falhas.append(f"Canal '{canal.nome}' não processado: categoria '{cat.nome}' "
                                         f"indisponível. Corrija a falha da categoria e execute novamente.")
                continue
            for i, canal in enumerate(cat.canais):
                ow = E.overwrites_do_canal(cat, canal)
                tipo = TIPO_VOZ if canal.tipo == "voz" else TIPO_TEXTO
                if canal.tipo == "anuncio" and self.ctx.comunidade:
                    tipo = TIPO_ANUNCIO
                corpo = {"name": canal.nome, "type": tipo, "position": i}
                if cat_id:
                    corpo["parent_id"] = cat_id
                if canal.tipo == "voz":
                    corpo["user_limit"] = canal.limite_usuarios
                else:
                    corpo["topic"] = canal.topico
                    if canal.tipo != "anuncio":  # canais de anúncio não têm modo lento
                        corpo["rate_limit_per_user"] = canal.modo_lento
                existente, gerenciado = self._procurar(canal.nome, classe_planejada(canal), cat_id,
                                                       canal.chave, "canais")
                cid = self._garantir(existente, gerenciado, f"Canal '{canal.nome}'", "canais",
                                     canal.chave, corpo, ow, parent_id=cat_id, planejado=canal)
                if cid:
                    self.ids_canais[canal.chave] = cid
        self.estado.salvar()

    def _garantir(self, existente, gerenciado, desc, secao, chave, corpo, ow, parent_id, planejado):
        if existente is None:
            return self._criar_canal(desc, secao, chave, corpo, ow)
        cid = existente["id"]
        if not gerenciado:
            self.r.nao_gerenciados.append(f"{desc} já existia e não foi alterado "
                                          f"(use --adotar-existentes para gerenciá-lo).")
            return cid
        self.gerenciados_canais.add(cid)
        self.estado.dados[secao][chave] = cid
        self._corrigir_canal(existente, desc, corpo, ow, parent_id, planejado, f"{secao}:{chave}")
        return cid

    def _criar_canal(self, desc, secao, chave, corpo, ow):
        corpo = dict(corpo)
        corpo["permission_overwrites"] = self.overwrites_api(ow)
        if self.simular or (corpo.get("parent_id") or "").startswith("sim-"):
            fake = f"sim-{secao}-{chave}"
            self.r.criados.append(desc + " (simulação)")
            log.info("  [SIMULAÇÃO] criaria %s", desc)
            return fake
        try:
            novo = self.api.post(f"/guilds/{self.ctx.gid}/channels", corpo)
        except ErroAPI as e:
            self.r.falhas.append(f"{desc}: {e}")
            log.error("  FALHA ao criar %s: %s", desc, e)
            return None
        self.ctx.channels[novo["id"]] = novo
        self.gerenciados_canais.add(novo["id"])
        self.estado.dados[secao][chave] = novo["id"]
        self.estado.salvar()
        self.r.criados.append(desc)
        log.info("  + criado %s", desc)
        return novo["id"]

    def _corrigir_canal(self, atual, desc, corpo, ow, parent_id, planejado, chave_estado=""):
        dif = {}
        if not self._nome_ok(chave_estado, atual["name"], corpo["name"]):
            dif["name"] = corpo["name"]
        ids = self._ids_controlados()
        desejado = self._norm_ow(self.overwrites_api(ow))
        existente = self._norm_ow(atual.get("permission_overwrites", []), ids)
        if desejado != existente:
            # Preserva overwrites de alvos que o projeto não controla.
            estranhos = [o for o in atual.get("permission_overwrites", []) if str(o["id"]) not in ids]
            dif["permission_overwrites"] = self.overwrites_api(ow) + [
                {"id": o["id"], "type": o["type"], "allow": str(o["allow"]), "deny": str(o["deny"])}
                for o in estranhos]
        if parent_id and atual.get("parent_id") != parent_id and not parent_id.startswith("sim-"):
            dif["parent_id"] = parent_id
        if planejado is not None:
            if planejado.tipo != "voz":
                if (atual.get("topic") or "") != planejado.topico:
                    dif["topic"] = planejado.topico
                if planejado.tipo != "anuncio" and int(atual.get("rate_limit_per_user") or 0) != planejado.modo_lento:
                    dif["rate_limit_per_user"] = planejado.modo_lento
            elif int(atual.get("user_limit") or 0) != planejado.limite_usuarios:
                dif["user_limit"] = planejado.limite_usuarios
            if planejado.tipo == "anuncio" and self.ctx.comunidade and atual["type"] == TIPO_TEXTO:
                dif["type"] = TIPO_ANUNCIO
        if not dif:
            self.r.existentes.append(desc)
            log.info("  = já existe %s", desc)
            return
        if self.simular:
            self.r.corrigidos.append(f"{desc}: {sorted(dif)} (simulação)")
            log.info("  [SIMULAÇÃO] corrigiria %s: %s", desc, sorted(dif))
            return
        try:
            novo = self.api.patch(f"/channels/{atual['id']}", dif)
            self.ctx.channels[novo["id"]] = novo
            if "name" in dif:
                self._aceitar_nome(chave_estado, corpo["name"], novo["name"])
            self.r.corrigidos.append(f"{desc}: {sorted(dif)}")
            log.info("  ~ corrigido %s: %s", desc, sorted(dif))
        except ErroAPI as e:
            self.r.falhas.append(f"Corrigir {desc}: {e}")
            log.error("  FALHA ao corrigir %s: %s", desc, e)

    def ordenar_canais(self):
        log.info("\n== Ordem de categorias e canais ==")
        mudancas = []
        cats = [(cat, self.ids_cat.get(cat.chave)) for cat in E.CATEGORIAS]
        cats = [(c, i) for c, i in cats if i and i in self.gerenciados_canais and i in self.ctx.channels]

        def em_ordem(ids):
            atuais = [self.ctx.channels[i] for i in ids]
            ordenados = sorted(atuais, key=lambda c: (c["position"], int(c["id"])))
            return [c["id"] for c in ordenados] == ids

        ids_cats = [i for _, i in cats]
        if not em_ordem(ids_cats):
            mudancas += [{"id": cid, "position": pos} for pos, cid in enumerate(ids_cats)]
        for cat, cat_id in cats:
            filhos = [self.ids_canais.get(c.chave) for c in cat.canais]
            for classe in ("texto", "voz"):
                ids = [i for i, c in zip(filhos, cat.canais)
                       if i and i in self.gerenciados_canais and i in self.ctx.channels
                       and classe_planejada(c) == classe]
                if ids and not em_ordem(ids):
                    mudancas += [{"id": cid, "position": pos} for pos, cid in enumerate(ids)]
        if not mudancas:
            self.r.existentes.append("Ordem de categorias e canais já está correta")
            log.info("  = ordem já correta")
            return
        if self.simular:
            self.r.corrigidos.append(f"Ordem de {len(mudancas)} categorias/canais (simulação)")
            return
        try:
            self.api.patch(f"/guilds/{self.ctx.gid}/channels", mudancas)
            self.r.corrigidos.append(f"Ordem de {len(mudancas)} categorias/canais")
            log.info("  ~ ordem ajustada para %d itens", len(mudancas))
        except ErroAPI as e:
            self.r.falhas.append(f"Ordenar canais: {e}")

    # ------------------------------------------------------------------
    def executar(self):
        self.cargos()
        self.ordenar_cargos()
        self.categorias_e_canais()
        if not self.simular:
            self.ctx.channels = {c["id"]: c for c in self.api.canais(self.ctx.gid)}
        self.ordenar_canais()
        self.estado.salvar()
        return self.r
