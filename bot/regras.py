"""Regras de negócio puras (sem Discord): validação de links, normalização e estados.

Mantidas separadas para poderem ser testadas sem conexão.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# ---------------------------------------------------------------------------
# Nomes
# ---------------------------------------------------------------------------

def slug(nome: str) -> str:
    """'👑 Líder Fundador' -> 'líder fundador'; '🚨｜denúncias' -> 'denúncias'."""
    for sep in ("｜", "・", "|"):
        if sep in nome:
            nome = nome.split(sep, 1)[1]
            break
    nome = re.sub(r"^[^\w]+", "", nome, flags=re.UNICODE)
    return re.sub(r"\s+", " ", nome).strip().casefold()


def sem_acentos(txt: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", txt) if not unicodedata.combining(c))


def nome_canal_ticket(prefixo: str, numero: int, titulo: str = "") -> str:
    base = sem_acentos(titulo).lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")[:40]
    return f"{prefixo}-{numero:04d}" + (f"-{base}" if base else "")


def normalizar_nome(nome: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", sem_acentos(nome).lower()).strip()


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------
ENCURTADORES = {
    "bit.ly", "tinyurl.com", "cutt.ly", "goo.gl", "t.co", "is.gd", "rb.gy", "shorturl.at",
    "ow.ly", "buff.ly", "adf.ly", "shorte.st", "linktr.ee", "tiny.cc", "rebrand.ly", "s.id",
    "v.gd", "bl.ink", "lnkd.in", "t.ly", "short.io", "encurtador.com.br",
}
HOSPEDAGEM_ARQUIVOS = {
    "mediafire.com", "mega.nz", "mega.io", "drive.google.com", "dropbox.com", "1drv.ms",
    "onedrive.live.com", "cdn.discordapp.com", "media.discordapp.net", "wetransfer.com",
    "anonfiles.com", "gofile.io", "pixeldrain.com", "sendspace.com", "4shared.com",
}
CONFIAVEIS = {"nexusmods.com", "moddb.com", "github.com", "modworkshop.net"}
EXTENSOES_PERIGOSAS = (
    ".exe", ".scr", ".bat", ".cmd", ".msi", ".ps1", ".vbs", ".js", ".jar", ".apk", ".com",
    ".pif", ".hta", ".lnk", ".reg", ".dll",
)
PARAMS_RASTREIO = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}


def _dominio(host: str) -> str:
    host = (host or "").lower().split(":")[0]
    return host[4:] if host.startswith("www.") else host


def _pertence(host: str, conjunto: set[str]) -> bool:
    return any(host == d or host.endswith("." + d) for d in conjunto)


@dataclass
class AnaliseLink:
    valido: bool
    normalizado: str = ""
    dominio: str = ""
    alertas: list[str] = field(default_factory=list)
    bloqueado: bool = False
    erro: str = ""


def analisar_link(url: str) -> AnaliseLink:
    """Valida e classifica um link SEM acessá-lo (nada é baixado nem executado)."""
    url = (url or "").strip()
    if not re.match(r"^https://", url, re.I):
        return AnaliseLink(False, erro="O link precisa começar com https://")
    if re.search(r"\s", url):
        return AnaliseLink(False, erro="O link não pode conter espaços.")
    partes = urlsplit(url)
    host = _dominio(partes.hostname or "")
    if not host or "." not in host:
        return AnaliseLink(False, erro="Link inválido.")
    if partes.username or partes.password:
        return AnaliseLink(False, erro="Links com usuário/senha embutidos não são aceitos.")
    alertas: list[str] = []
    bloqueado = False
    if _pertence(host, ENCURTADORES):
        alertas.append("Encurtador de link: o destino real fica oculto.")
        bloqueado = True
    caminho = partes.path.lower()
    if caminho.endswith(EXTENSOES_PERIGOSAS):
        alertas.append("O link aponta diretamente para um arquivo executável/script.")
        bloqueado = True
    if _pertence(host, HOSPEDAGEM_ARQUIVOS):
        alertas.append("Hospedagem genérica de arquivos: confirme a origem e os créditos do autor.")
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
        alertas.append("Link para endereço IP em vez de domínio.")
        bloqueado = True
    if host.startswith("xn--") or ".xn--" in host:
        alertas.append("Domínio com caracteres internacionais (possível imitação de site).")
    if not _pertence(host, CONFIAVEIS) and not alertas:
        alertas.append("Domínio fora da lista de sites de mods conhecidos: conferir manualmente.")
    query = urlencode([(k, v) for k, v in parse_qsl(partes.query) if k.lower() not in PARAMS_RASTREIO])
    normal = urlunsplit(("https", host, partes.path.rstrip("/"), query, "")).lower()
    return AnaliseLink(True, normal, host, alertas, bloqueado)


def extrair_links(texto: str) -> list[str]:
    return re.findall(r"https?://[^\s<>()]+", texto or "")


# ---------------------------------------------------------------------------
# Estados dos tickets
# ---------------------------------------------------------------------------
ABERTO = "aberto"            # denúncia aberta / mod aguardando análise
ALTERACOES = "alteracoes"    # mod: alterações solicitadas ao autor
APROVADO = "aprovado"        # mod: aprovado e publicado
REJEITADO = "rejeitado"      # mod: rejeitado
ENCERRADO = "encerrado"      # encerrado sem decisão (resolvido, abandonado ou duplicado)

ATIVOS = {ABERTO, ALTERACOES}
ROTULOS = {
    ABERTO: "🟡 Aberto / aguardando análise",
    ALTERACOES: "🟠 Alterações solicitadas",
    APROVADO: "🟢 Aprovado e publicado",
    REJEITADO: "🔴 Rejeitado",
    ENCERRADO: "⚫ Encerrado",
}

# acao -> (estados de origem permitidos, estado de destino, tipos de ticket)
TRANSICOES = {
    "aprovar": ({ABERTO, ALTERACOES}, APROVADO, {"mod"}),
    "rejeitar": ({ABERTO, ALTERACOES}, REJEITADO, {"mod"}),
    "alteracoes": ({ABERTO}, ALTERACOES, {"mod"}),
    "encerrar": ({ABERTO, ALTERACOES}, ENCERRADO, {"mod", "denuncia", "contribuicao"}),
    "reabrir": ({REJEITADO, ENCERRADO}, ABERTO, {"mod", "denuncia", "contribuicao"}),
    "assumir": ({ABERTO, ALTERACOES}, None, {"mod", "denuncia", "contribuicao"}),
    "vip_dar": ({ABERTO}, None, {"contribuicao"}),
    "vip_remover": ({ABERTO}, None, {"contribuicao"}),
}


class AcaoNegada(Exception):
    pass


def verificar_acao(acao: str, tipo: str, status: str, autor_id: int, ator_id: int,
                   ator_eh_equipe: bool) -> str | None:
    """Retorna o novo status (ou None se não muda) ou levanta AcaoNegada com o motivo."""
    if acao not in TRANSICOES:
        raise AcaoNegada("Ação desconhecida.")
    origens, destino, tipos = TRANSICOES[acao]
    if tipo not in tipos:
        raise AcaoNegada("Esta ação não se aplica a este tipo de ticket.")
    if not ator_eh_equipe:
        raise AcaoNegada("Somente a equipe (Líder, Administração ou Moderador) pode fazer isso.")
    if acao in ("aprovar", "rejeitar", "alteracoes") and ator_id == autor_id:
        raise AcaoNegada("Você não pode avaliar o seu próprio envio.")
    if acao in ("vip_dar", "vip_remover") and ator_id == autor_id:
        raise AcaoNegada("Você não pode alterar o seu próprio VIP.")
    if status not in origens:
        raise AcaoNegada(f"Não é possível '{acao}' um ticket com status {ROTULOS.get(status, status)}.")
    return destino
