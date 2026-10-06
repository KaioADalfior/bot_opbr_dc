"""Servidor web embutido que publica os transcripts protegidos por link.

- Cada transcript recebe um endereço impossível de adivinhar: /t/<token aleatório>.
- A página continua criptografada: sem a senha (enviada por DM), nada é exibido.
- Opcionalmente abre um túnel Cloudflare gratuito (cloudflared) para gerar um link público
  quando o bot roda no PC de casa. Na VPS, use URL_PUBLICA com o seu domínio.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import secrets
import shutil
import time
from pathlib import Path

from aiohttp import web

log = logging.getLogger("operacao_brasil")

TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{24,64}$")
CABECALHOS = {
    "Cache-Control": "no-store",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Robots-Tag": "noindex, nofollow",
    "Content-Security-Policy": ("default-src 'none'; img-src data: https://cdn.discordapp.com https://media.discordapp.net; "
                                "style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; "
                                "form-action 'none'; frame-ancestors 'none'"),
}


class ServidorTranscripts:
    def __init__(self, pasta: Path, host: str, porta: int, url_publica: str = "", tunel: str = "",
                 validade_dias: int = 30):
        self.pasta = pasta
        self.pasta.mkdir(parents=True, exist_ok=True)
        self.host, self.porta = host, porta
        self.url_publica = url_publica.rstrip("/")
        self.tunel = tunel
        self.validade = validade_dias * 86400
        self._runner: web.AppRunner | None = None
        self._proc: asyncio.subprocess.Process | None = None
        self._url_do_tunel = False
        self._parando = False
        self._reabrindo = False
        # Chamado (async, sem argumentos) quando o endereço público muda, p.ex. túnel reaberto.
        self.ao_mudar_url = None

    # -- armazenamento -----------------------------------------------------------
    def salvar(self, html: bytes) -> str:
        token = secrets.token_urlsafe(24)
        (self.pasta / f"{token}.html").write_bytes(html)
        return token

    def link(self, token: str) -> str | None:
        return f"{self.url_publica}/t/{token}" if self.url_publica else None

    def existe(self, token: str) -> bool:
        arq = self.pasta / f"{token}.html"
        return bool(TOKEN_RE.match(token or "")) and arq.is_file() \
            and time.time() - arq.stat().st_mtime <= self.validade

    def limpar_expirados(self) -> int:
        limite = time.time() - self.validade
        n = 0
        for arq in self.pasta.glob("*.html"):
            if arq.stat().st_mtime < limite:
                arq.unlink(missing_ok=True)
                n += 1
        return n

    # -- HTTP ----------------------------------------------------------------------
    async def _pagina(self, req: web.Request) -> web.StreamResponse:
        token = req.match_info.get("token", "")
        arq = self.pasta / f"{token}.html"
        if not TOKEN_RE.match(token) or not arq.is_file():
            return web.Response(status=404, text="Transcript não encontrado ou expirado.", headers=CABECALHOS)
        if time.time() - arq.stat().st_mtime > self.validade:
            return web.Response(status=410, text="Este transcript expirou.", headers=CABECALHOS)
        return web.Response(body=arq.read_bytes(), content_type="text/html", charset="utf-8", headers=CABECALHOS)

    async def _raiz(self, _req: web.Request) -> web.Response:
        return web.Response(text="Operação Brasil — servidor de transcripts ativo.", headers=CABECALHOS)

    async def iniciar(self):
        app = web.Application()
        app.router.add_get("/", self._raiz)
        app.router.add_get("/t/{token}", self._pagina)
        self._runner = web.AppRunner(app, access_log=None)
        await self._runner.setup()
        await web.TCPSite(self._runner, self.host, self.porta).start()
        log.info("Servidor de transcripts em http://%s:%s", self.host, self.porta)
        if not self.url_publica and self.tunel == "cloudflared":
            await self._abrir_tunel()
        if self.url_publica:
            log.info("Links públicos de transcript: %s/t/...", self.url_publica)
        else:
            log.warning("Sem URL pública: os transcripts serão enviados como arquivo anexo.")

    @staticmethod
    def _achar_cloudflared() -> str | None:
        """PATH primeiro; depois as pastas onde o winget/MSI costuma instalar no Windows."""
        exe = os.environ.get("CLOUDFLARED_PATH") or shutil.which("cloudflared")
        if exe and Path(exe).is_file():
            return exe
        candidatos = [
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "cloudflared" / "cloudflared.exe",
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "cloudflared" / "cloudflared.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / "cloudflared.exe",
        ]
        pacotes = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
        if os.environ.get("LOCALAPPDATA") and pacotes.is_dir():
            candidatos += list(pacotes.glob("Cloudflare.cloudflared*/**/cloudflared*.exe"))
        for c in candidatos:
            if str(c) not in ("", ".") and c.is_file():
                return str(c)
        return None

    async def _abrir_tunel(self):
        exe = self._achar_cloudflared()
        if not exe:
            log.warning("cloudflared não encontrado. Instale com: winget install --id Cloudflare.cloudflared "
                        "(ou informe o caminho do .exe em CLOUDFLARED_PATH no bot\\.env)")
            return
        self._proc = await asyncio.create_subprocess_exec(
            exe, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{self.porta}",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        padrao = re.compile(rb"https://[a-z0-9-]+\.trycloudflare\.com")
        try:
            async with asyncio.timeout(45):
                while True:
                    linha = await self._proc.stdout.readline()
                    if not linha:
                        break
                    m = padrao.search(linha)
                    if m:
                        self.url_publica = m.group(0).decode()
                        self._url_do_tunel = True
                        log.info("Túnel Cloudflare ativo: %s", self.url_publica)
                        break
        except TimeoutError:
            log.warning("O túnel Cloudflare não respondeu a tempo; transcripts irão como anexo.")
        if self._proc and self._proc.stdout:
            asyncio.get_running_loop().create_task(self._drenar())

    async def _drenar(self):
        """Consome a saída do cloudflared. Se o processo cair, reabre o túnel sozinho."""
        proc = self._proc
        try:
            while proc and await proc.stdout.readline():
                pass
        except Exception:  # noqa: BLE001
            pass
        if self._parando or self._reabrindo or proc is not self._proc:
            return
        log.warning("O túnel Cloudflare caiu. Reabrindo...")
        if self._url_do_tunel:
            self.url_publica = ""
        self._reabrindo = True
        espera = 5
        try:
            while not self._parando and not self.url_publica:
                await asyncio.sleep(espera)
                if self._proc and self._proc.returncode is None:
                    self._proc.terminate()  # tentativa anterior que não gerou endereço
                await self._abrir_tunel()
                espera = min(espera * 2, 300)
        finally:
            self._reabrindo = False
        if self.url_publica and self.ao_mudar_url is not None:
            try:
                await self.ao_mudar_url()
            except Exception:  # noqa: BLE001
                log.exception("Falha ao atualizar os links após reabrir o túnel")

    async def parar(self):
        self._parando = True
        if self._proc and self._proc.returncode is None:
            self._proc.terminate()
        if self._runner:
            await self._runner.cleanup()
