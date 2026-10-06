"""Simulador local da API do Discord para testes automatizados (não acessa a internet).

Reproduz as regras relevantes ao projeto:
- autenticação "Bot <token>";
- novo cargo nasce na posição 1 e sem "permissions" herda as do @everyone;
- o bot só concede (em cargos e overwrites) permissões que possui;
- o bot só edita/ordena cargos abaixo do seu cargo mais alto;
- canais de anúncio exigem a feature COMMUNITY; troca de tipo só texto<->anúncio;
- mensagens exigem Ver canal + Enviar mensagens efetivos para o bot;
- Onboarding exige >= 7 canais padrão, 5 deles com envio liberado ao @everyone;
- respostas 429 aleatórias para testar o tratamento de limite de requisições.
"""
from __future__ import annotations

import itertools
import json
import random
import re
from urllib.parse import urlparse

from gr_setup.permissoes import P, permissoes_base, permissoes_canal

# Token FALSO, só para os testes. Montado em partes para não ser confundido com um token real
# pelos detectores de segredos (como o do GitHub).
TOKEN = ".".join(["MTAxMjM0NTY3ODkwMTIzNDU2Nzg", "Gabcde", "abcdefghijklmnopqrstuvwxyz" + "0123456789AB"])
EVERYONE_DEFAULT = int(
    P.CREATE_INSTANT_INVITE | P.ADD_REACTIONS | P.STREAM | P.VIEW_CHANNEL | P.SEND_MESSAGES
    | P.EMBED_LINKS | P.ATTACH_FILES | P.READ_MESSAGE_HISTORY | P.MENTION_EVERYONE
    | P.USE_EXTERNAL_EMOJIS | P.CONNECT | P.SPEAK | P.USE_VAD | P.CHANGE_NICKNAME
    | P.USE_APPLICATION_COMMANDS | P.REQUEST_TO_SPEAK | P.CREATE_PUBLIC_THREADS
    | P.CREATE_PRIVATE_THREADS | P.USE_EXTERNAL_STICKERS | P.SEND_MESSAGES_IN_THREADS
    | P.USE_EMBEDDED_ACTIVITIES | P.SEND_VOICE_MESSAGES | P.SEND_POLLS | P.USE_SOUNDBOARD
)


class Resp:
    def __init__(self, status, body=None, headers=None):
        self.status_code = status
        # Cópia profunda: como na API real, a resposta é um retrato daquele momento.
        self._body = json.loads(json.dumps(body)) if body is not None else None
        self.headers = headers or {}
        self.text = json.dumps(body) if body is not None else ""

    def json(self):
        if self._body is None:
            raise ValueError("sem corpo")
        return self._body


class FakeDiscord:
    def __init__(self, bot_perms: int, comunidade=False, taxa_429=0.05, semente=7):
        self.ids = itertools.count(1_200_000_000_000_000_000)
        self.rand = random.Random(semente)
        self.taxa_429 = taxa_429
        self.gid = str(next(self.ids))
        self.owner_id = str(next(self.ids))
        self.bot_id = str(next(self.ids))
        self.app_id = self.bot_id
        self.features = ["COMMUNITY", "NEWS"] if comunidade else []
        self.guild_extra = {"verification_level": 0, "explicit_content_filter": 0, "mfa_level": 0,
                            "rules_channel_id": None, "public_updates_channel_id": None,
                            "preferred_locale": "pt-BR", "description": None}
        self.roles = {self.gid: {"id": self.gid, "name": "@everyone", "position": 0,
                                 "permissions": str(EVERYONE_DEFAULT), "managed": False,
                                 "color": 0, "hoist": False, "mentionable": False}}
        self.bot_role = str(next(self.ids))
        self.roles[self.bot_role] = {"id": self.bot_role, "name": "Configurador GRB", "position": 1,
                                     "permissions": str(bot_perms), "managed": True,
                                     "tags": {"bot_id": self.bot_id}, "color": 0, "hoist": False,
                                     "mentionable": False}
        self.channels = {}
        self.messages = {}
        self.pins = {}
        self.onboarding_data = {"guild_id": self.gid, "prompts": [], "default_channel_ids": [],
                                "enabled": False, "mode": 0}
        self.log = []
        # Canais padrão de um servidor novo criado pelo app (pt-BR)
        ct = self._novo_canal({"name": "Canais de texto", "type": 4})
        self._novo_canal({"name": "geral", "type": 0, "parent_id": ct["id"]})
        cv = self._novo_canal({"name": "Canais de voz", "type": 4})
        self._novo_canal({"name": "Geral", "type": 2, "parent_id": cv["id"]})

    # ------------------------------------------------------------------
    def _bot_perms(self):
        rp = {k: int(v["permissions"]) for k, v in self.roles.items()}
        return permissoes_base(rp, self.gid, [self.bot_role])

    def _bot_topo(self):
        return self.roles[self.bot_role]["position"]

    def _bot_perm_canal(self, cid):
        ch = self.channels[cid]
        return permissoes_canal(self._bot_perms(), ch.get("permission_overwrites", []), self.gid,
                                [self.bot_role], canal_voz=ch["type"] == 2)

    def _erro(self, status, code, msg):
        return Resp(status, {"code": code, "message": msg})

    def _novo_canal(self, body):
        cid = str(next(self.ids))
        tipo = body.get("type", 0)
        irmaos = [c for c in self.channels.values() if c.get("parent_id") == body.get("parent_id")]
        ch = {"id": cid, "guild_id": self.gid, "name": body["name"], "type": tipo,
              "position": body.get("position", len(irmaos)), "parent_id": body.get("parent_id"),
              "permission_overwrites": [
                  {"id": o["id"], "type": o.get("type", 0), "allow": str(o.get("allow", "0")),
                   "deny": str(o.get("deny", "0"))} for o in body.get("permission_overwrites", [])
                  if int(o.get("allow", 0)) or int(o.get("deny", 0))],
              "topic": body.get("topic") or None, "rate_limit_per_user": body.get("rate_limit_per_user", 0),
              "user_limit": body.get("user_limit", 0)}
        if tipo == 2:
            ch.pop("topic")
        self.channels[cid] = ch
        self.messages[cid] = []
        return ch

    def _valida_overwrites(self, ows):
        bot = self._bot_perms()
        if bot & P.ADMINISTRATOR:
            return None
        for o in ows or []:
            bits = int(o.get("allow", 0)) | int(o.get("deny", 0))
            if bits & ~bot:
                return self._erro(403, 50013, "Missing Permissions (overwrite)")
        return None

    # ------------------------------------------------------------------
    def request(self, method, url, headers=None, params=None, data=None, timeout=None):
        if headers.get("Authorization") != f"Bot {TOKEN}":
            return self._erro(401, 0, "401: Unauthorized")
        rota = urlparse(url).path.replace("/api/v10", "")
        body = json.loads(data) if data else None
        self.log.append((method, rota))
        if method != "GET" and self.rand.random() < self.taxa_429:
            return Resp(429, {"message": "You are being rate limited.", "retry_after": 0.01, "global": False},
                        {"Retry-After": "1", "X-RateLimit-Scope": "user"})
        h = {"X-RateLimit-Remaining": str(self.rand.randint(0, 3)), "X-RateLimit-Reset-After": "0.001"}
        r = self._rota(method, rota, body)
        r.headers.update(h)
        return r

    def _rota(self, m, rota, body):
        g = self.gid
        if m == "GET" and rota == "/users/@me":
            return Resp(200, {"id": self.bot_id, "username": "Configurador GRB", "bot": True})
        if m == "GET" and rota == "/oauth2/applications/@me":
            return Resp(200, {"id": self.app_id})
        if m == "GET" and rota == "/users/@me/guilds":
            return Resp(200, [{"id": g, "name": "Ghost Recon Brasil"}])
        if m == "GET" and rota == f"/guilds/{g}":
            return Resp(200, {"id": g, "name": "Ghost Recon Brasil", "owner_id": self.owner_id,
                              "features": self.features, "approximate_member_count": 3, **self.guild_extra})
        if m == "GET" and rota == f"/guilds/{g}/roles":
            return Resp(200, list(self.roles.values()))
        if m == "GET" and rota == f"/guilds/{g}/channels":
            return Resp(200, [c for c in self.channels.values()])
        if m == "GET" and rota == f"/guilds/{g}/members/{self.bot_id}":
            return Resp(200, {"user": {"id": self.bot_id}, "roles": [self.bot_role]})
        if rota == f"/guilds/{g}/roles" and m == "POST":
            perms = int(body.get("permissions", self.roles[g]["permissions"]))
            if perms & ~self._bot_perms():
                return self._erro(403, 50013, "Missing Permissions")
            for r in self.roles.values():
                if r["id"] != g:
                    r["position"] += 1
            rid = str(next(self.ids))
            cor = (body.get("colors") or {}).get("primary_color", body.get("color", 0))
            role = {"id": rid, "name": body["name"], "position": 1, "permissions": str(perms),
                    "managed": False, "color": cor, "colors": {"primary_color": cor},
                    "hoist": body.get("hoist", False), "mentionable": body.get("mentionable", False)}
            self.roles[rid] = role
            return Resp(200, role)
        if rota == f"/guilds/{g}/roles" and m == "PATCH":
            for item in body:
                if item["position"] >= self._bot_topo() or self.roles[item["id"]]["position"] >= self._bot_topo():
                    return self._erro(403, 50013, "Missing Permissions")
            for item in body:
                self.roles[item["id"]]["position"] = item["position"]
            return Resp(200, list(self.roles.values()))
        mt = re.fullmatch(rf"/guilds/{g}/roles/(\d+)", rota)
        if mt and m == "PATCH":
            role = self.roles[mt.group(1)]
            if role["position"] >= self._bot_topo():
                return self._erro(403, 50013, "Missing Permissions")
            if "permissions" in body and int(body["permissions"]) & ~self._bot_perms():
                return self._erro(403, 50013, "Missing Permissions")
            for k, v in body.items():
                if k == "colors":
                    role["colors"] = v
                    role["color"] = v["primary_color"]
                else:
                    role[k] = v
            return Resp(200, role)
        if rota == f"/guilds/{g}/channels" and m == "POST":
            if body.get("type") == 5 and "NEWS" not in self.features:
                return self._erro(400, 50024, "Cannot execute action on this channel type")
            if body.get("parent_id") and body["parent_id"] not in self.channels:
                return self._erro(400, 50035, "Invalid Form Body (parent_id)")
            err = self._valida_overwrites(body.get("permission_overwrites"))
            if err:
                return err
            if len(self.channels) >= 500:
                return self._erro(400, 30013, "Maximum number of guild channels reached (500)")
            return Resp(201, self._novo_canal(body))
        if rota == f"/guilds/{g}/channels" and m == "PATCH":
            for item in body:
                self.channels[item["id"]]["position"] = item["position"]
            return Resp(204)
        mc = re.fullmatch(r"/channels/(\d+)", rota)
        if mc and m == "PATCH":
            ch = self.channels[mc.group(1)]
            if "type" in body:
                if "NEWS" not in self.features or {ch["type"], body["type"]} != {0, 5}:
                    return self._erro(400, 50024, "Cannot execute action on this channel type")
            err = self._valida_overwrites(body.get("permission_overwrites"))
            if err:
                return err
            for k, v in body.items():
                if k == "permission_overwrites":
                    v = [{"id": o["id"], "type": o.get("type", 0), "allow": str(o["allow"]),
                          "deny": str(o["deny"])} for o in v]
                ch[k] = v
            return Resp(200, ch)
        mm = re.fullmatch(r"/channels/(\d+)/messages", rota)
        if mm:
            cid = mm.group(1)
            ef = self._bot_perm_canal(cid)
            if not ef & P.VIEW_CHANNEL:
                return self._erro(403, 50001, "Missing Access")
            if m == "GET":
                return Resp(200, list(reversed(self.messages[cid]))[:100])
            if not ef & P.SEND_MESSAGES:
                return self._erro(403, 50013, "Missing Permissions")
            emb = [{k: v for k, v in e.items()} for e in body.get("embeds", [])]
            for e in emb:
                e["description"] = e["description"].strip()
            msg = {"id": str(next(self.ids)), "channel_id": cid, "author": {"id": self.bot_id},
                   "content": body.get("content", ""), "embeds": emb}
            self.messages[cid].append(msg)
            return Resp(200, msg)
        me = re.fullmatch(r"/channels/(\d+)/messages/(\d+)", rota)
        if me and m == "PATCH":
            msg = next((x for x in self.messages[me.group(1)] if x["id"] == me.group(2)), None)
            if msg is None:
                return self._erro(404, 10008, "Unknown Message")
            if msg["author"]["id"] != self.bot_id:
                return self._erro(403, 50005, "Cannot edit a message authored by another user")
            emb = [dict(e) for e in body.get("embeds", [])]
            for e in emb:
                e["description"] = e["description"].strip()
            msg["embeds"] = emb
            return Resp(200, msg)
        mp = re.fullmatch(r"/channels/(\d+)/messages/pins/(\d+)", rota)
        if mp and m == "PUT":
            if not self._bot_perm_canal(mp.group(1)) & P.PIN_MESSAGES:
                return self._erro(403, 50013, "Missing Permissions")
            self.pins.setdefault(mp.group(1), set()).add(mp.group(2))
            return Resp(204)
        if rota == f"/guilds/{g}/onboarding":
            if m == "GET":
                return Resp(200, self.onboarding_data)
            if m == "PUT":
                if "COMMUNITY" not in self.features:
                    return self._erro(403, 50013, "Missing Permissions")
                defaults = body["default_channel_ids"]
                enviaveis = 0
                for cid in defaults:
                    ch = self.channels[cid]
                    rp = {k: int(v["permissions"]) for k, v in self.roles.items()}
                    base = permissoes_base(rp, self.gid, [])
                    ef = permissoes_canal(base, ch["permission_overwrites"], self.gid, [])
                    if ef & P.VIEW_CHANNEL and ef & P.SEND_MESSAGES:
                        enviaveis += 1
                if len(defaults) < 7 or enviaveis < 5:
                    return self._erro(400, 350000, "Onboarding default channel requirements not met")
                self.onboarding_data = {"guild_id": g, **body}
                return Resp(200, self.onboarding_data)
        return self._erro(404, 0, f"404 rota simulada inexistente: {m} {rota}")
