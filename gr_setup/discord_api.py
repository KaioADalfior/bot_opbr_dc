"""Cliente mínimo da API REST oficial do Discord (v10).

- Autenticação exclusivamente com token de BOT ("Authorization: Bot ...").
- Respeita os limites de requisição (cabeçalhos X-RateLimit-* e respostas 429).
- Repete automaticamente erros temporários (5xx / falhas de rede).
- Nunca registra o token em logs.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.parse

import requests

API_BASE = "https://discord.com/api/v10"
USER_AGENT = "DiscordBot (https://github.com/ghost-recon-brasil-setup, 1.0) GhostReconBrasilSetup"

log = logging.getLogger("gr_setup.api")

# Códigos de erro JSON documentados em
# https://docs.discord.com/developers/topics/opcodes-and-status-codes
ERROS_CONHECIDOS = {
    10003: "Canal desconhecido (foi apagado?)",
    10004: "Servidor desconhecido: confira DISCORD_GUILD_ID",
    10011: "Cargo desconhecido (foi apagado?)",
    30005: "Limite de 250 cargos do servidor atingido",
    30013: "Limite de 500 canais do servidor atingido",
    50001: "Sem acesso: o bot não está no servidor ou não vê o canal",
    50013: "Permissões insuficientes: confira as permissões e a posição do cargo do bot",
    50024: "Operação não permitida neste tipo de canal",
    50035: "Dados inválidos enviados à API",
}


class ErroAPI(Exception):
    def __init__(self, status: int, metodo: str, rota: str, corpo):
        self.status = status
        self.metodo = metodo
        self.rota = rota
        self.corpo = corpo
        self.codigo = corpo.get("code") if isinstance(corpo, dict) else None
        dica = ERROS_CONHECIDOS.get(self.codigo, "")
        msg = corpo.get("message") if isinstance(corpo, dict) else str(corpo)[:300]
        if isinstance(corpo, dict) and corpo.get("errors"):
            msg += " | detalhes: " + json.dumps(corpo["errors"], ensure_ascii=False)[:1500]
        super().__init__(f"HTTP {status} em {metodo} {rota}: {msg} (código {self.codigo}) {dica}".strip())


class DiscordAPI:
    def __init__(self, token: str, motivo_auditoria: str = "Configuração Ghost Recon Brasil",
                 sessao: requests.Session | None = None, max_tentativas: int = 6,
                 pausa_minima: float = 0.25):
        if not token or token.count(".") < 2:
            raise ValueError("DISCORD_BOT_TOKEN ausente ou com formato inválido.")
        self._token = token
        self.sessao = sessao or requests.Session()
        self.motivo = urllib.parse.quote(motivo_auditoria, safe="")
        self.max_tentativas = max_tentativas
        self.pausa_minima = pausa_minima
        self.contador = {"GET": 0, "POST": 0, "PATCH": 0, "PUT": 0, "DELETE": 0}

    # -- núcleo -------------------------------------------------------------
    def _cabecalhos(self, escrita: bool) -> dict:
        h = {"Authorization": f"Bot {self._token}", "User-Agent": USER_AGENT}
        if escrita:
            h["Content-Type"] = "application/json"
            h["X-Audit-Log-Reason"] = self.motivo
        return h

    def requisicao(self, metodo: str, rota: str, corpo=None, params=None):
        if metodo == "DELETE":
            # Proteção extra: este projeto nunca apaga recursos.
            raise RuntimeError("Operações DELETE são bloqueadas neste projeto.")
        url = API_BASE + rota
        escrita = metodo != "GET"
        for tentativa in range(1, self.max_tentativas + 1):
            try:
                resp = self.sessao.request(
                    metodo, url, headers=self._cabecalhos(escrita), params=params,
                    data=json.dumps(corpo) if corpo is not None else None, timeout=30,
                )
            except requests.RequestException as exc:
                espera = min(2 ** tentativa, 30)
                log.warning("Falha de rede em %s %s (%s). Nova tentativa em %ss.",
                            metodo, rota, type(exc).__name__, espera)
                time.sleep(espera)
                continue

            self.contador[metodo] = self.contador.get(metodo, 0) + 1

            if resp.status_code == 429:
                try:
                    dados = resp.json()
                except ValueError:
                    dados = {}
                espera = float(dados.get("retry_after", resp.headers.get("Retry-After", 1)))
                escopo = "global" if dados.get("global") else resp.headers.get("X-RateLimit-Scope", "rota")
                log.warning("Limite de requisições (%s). Aguardando %.2fs antes de repetir %s %s.",
                            escopo, espera, metodo, rota)
                time.sleep(espera + 0.1)
                continue

            if resp.status_code >= 500:
                espera = min(2 ** tentativa, 30)
                log.warning("Erro %s do Discord em %s %s. Nova tentativa em %ss.",
                            resp.status_code, metodo, rota, espera)
                time.sleep(espera)
                continue

            # Respeita o bucket da rota proativamente
            restante = resp.headers.get("X-RateLimit-Remaining")
            reset_after = resp.headers.get("X-RateLimit-Reset-After")
            if restante is not None and reset_after is not None and restante == "0":
                time.sleep(float(reset_after) + 0.05)
            elif escrita and self.pausa_minima:
                time.sleep(self.pausa_minima)

            if resp.status_code == 204:
                return None
            try:
                dados = resp.json()
            except ValueError:
                dados = resp.text
            if resp.status_code >= 400:
                raise ErroAPI(resp.status_code, metodo, rota, dados)
            return dados
        raise ErroAPI(0, metodo, rota, {"message": "Número máximo de tentativas excedido"})

    def get(self, rota, params=None):
        return self.requisicao("GET", rota, params=params)

    def post(self, rota, corpo):
        return self.requisicao("POST", rota, corpo)

    def patch(self, rota, corpo):
        return self.requisicao("PATCH", rota, corpo)

    def put(self, rota, corpo=None):
        return self.requisicao("PUT", rota, corpo)

    # -- atalhos -----------------------------------------------------------
    def eu(self):
        return self.get("/users/@me")

    def aplicacao(self):
        return self.get("/oauth2/applications/@me")

    def meus_servidores(self):
        return self.get("/users/@me/guilds", params={"limit": 200})

    def servidor(self, gid):
        return self.get(f"/guilds/{gid}", params={"with_counts": "true"})

    def cargos(self, gid):
        return self.get(f"/guilds/{gid}/roles")

    def canais(self, gid):
        return self.get(f"/guilds/{gid}/channels")

    def membro(self, gid, uid):
        return self.get(f"/guilds/{gid}/members/{uid}")

    def mensagens(self, cid, limite=50):
        return self.get(f"/channels/{cid}/messages", params={"limit": limite})

    def onboarding(self, gid):
        return self.get(f"/guilds/{gid}/onboarding")
