"""Armazenamento local (SQLite) de tickets, painéis e registro de auditoria."""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from . import regras

ESQUEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo          TEXT NOT NULL,              -- 'denuncia' | 'mod'
    autor_id      INTEGER NOT NULL,
    canal_id      INTEGER,
    status        TEXT NOT NULL,
    assumido_por  INTEGER,
    dados         TEXT NOT NULL DEFAULT '{}', -- JSON com os campos do formulário
    link_norm     TEXT,
    nome_norm     TEXT,
    publicado_msg INTEGER,
    criado_em     TEXT NOT NULL,
    atualizado_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_tickets_autor ON tickets(autor_id, tipo, status);
CREATE INDEX IF NOT EXISTS ix_tickets_link ON tickets(link_norm);
CREATE TABLE IF NOT EXISTS acoes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER,
    ator_id   INTEGER NOT NULL,
    acao      TEXT NOT NULL,
    detalhe   TEXT,
    data      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS squads (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    lider_id      INTEGER NOT NULL,
    jogo          TEXT NOT NULL,
    plataforma    TEXT NOT NULL,
    modo          TEXT NOT NULL,
    estilo        TEXT,
    nome          TEXT NOT NULL,
    obs           TEXT,
    id_jogo       TEXT,
    vagas         INTEGER NOT NULL,
    membros       TEXT NOT NULL DEFAULT '[]', -- JSON: IDs de quem clicou em "Eu vou" (sem o líder)
    voz_id        INTEGER,
    msg_id        INTEGER,
    status        TEXT NOT NULL,              -- 'ativo' | 'encerrado'
    motivo        TEXT,
    criado_em     TEXT NOT NULL,
    encerrado_em  TEXT
);
CREATE INDEX IF NOT EXISTS ix_squads_status ON squads(status);
CREATE TABLE IF NOT EXISTS vips (
    user_id       INTEGER PRIMARY KEY,
    origem        TEXT NOT NULL,              -- 'boost' | 'contribuicao'
    concedido_por INTEGER,
    ticket_id     INTEGER,
    desde         TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mensagens_canal (
    chave         TEXT PRIMARY KEY,
    canal_id      INTEGER NOT NULL,
    msg_id        INTEGER NOT NULL,
    hash          TEXT NOT NULL,
    atualizado_em TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS paineis (
    chave    TEXT PRIMARY KEY,
    canal_id INTEGER NOT NULL,
    msg_id   INTEGER NOT NULL
);
"""


def agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Banco:
    def __init__(self, caminho: Path | str):
        if str(caminho) != ":memory:":
            Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(str(caminho), check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        with self.lock, self.con:
            self.con.executescript(ESQUEMA)

    # -- tickets --------------------------------------------------------------
    def criar_ticket(self, tipo: str, autor_id: int, dados: dict, link_norm: str | None = None,
                     nome_norm: str | None = None) -> int:
        with self.lock, self.con:
            cur = self.con.execute(
                "INSERT INTO tickets (tipo, autor_id, status, dados, link_norm, nome_norm, criado_em, atualizado_em)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (tipo, autor_id, regras.ABERTO, json.dumps(dados, ensure_ascii=False), link_norm, nome_norm,
                 agora(), agora()))
            return cur.lastrowid

    def definir_canal(self, tid: int, canal_id: int):
        with self.lock, self.con:
            self.con.execute("UPDATE tickets SET canal_id=?, atualizado_em=? WHERE id=?", (canal_id, agora(), tid))

    def ticket(self, tid: int) -> dict | None:
        r = self.con.execute("SELECT * FROM tickets WHERE id=?", (tid,)).fetchone()
        return self._dict(r)

    def ticket_por_canal(self, canal_id: int) -> dict | None:
        r = self.con.execute("SELECT * FROM tickets WHERE canal_id=?", (canal_id,)).fetchone()
        return self._dict(r)

    def ativos_do_autor(self, autor_id: int, tipo: str) -> list[dict]:
        q = f"SELECT * FROM tickets WHERE autor_id=? AND tipo=? AND status IN ({','.join('?' * len(regras.ATIVOS))})"
        return [self._dict(r) for r in self.con.execute(q, (autor_id, tipo, *regras.ATIVOS))]

    def ativos(self) -> list[dict]:
        q = f"SELECT * FROM tickets WHERE status IN ({','.join('?' * len(regras.ATIVOS))})"
        return [self._dict(r) for r in self.con.execute(q, tuple(regras.ATIVOS))]

    def com_transcript(self) -> list[dict]:
        """Tickets que já geraram um transcript com link."""
        q = "SELECT * FROM tickets WHERE dados LIKE '%transcript_token%' ORDER BY id"
        return [d for d in (self._dict(r) for r in self.con.execute(q)) if d["dados"].get("transcript_token")]

    def duplicado_mod(self, link_norm: str, nome_norm: str) -> dict | None:
        """Mod já enviado (ativo ou aprovado) com o mesmo link, ou com o mesmo nome."""
        q = ("SELECT * FROM tickets WHERE tipo='mod' AND status IN (?,?,?) AND (link_norm=? OR nome_norm=?)"
             " ORDER BY id LIMIT 1")
        r = self.con.execute(q, (regras.ABERTO, regras.ALTERACOES, regras.APROVADO, link_norm, nome_norm)).fetchone()
        return self._dict(r)

    def mudar_status(self, tid: int, de: set[str], para: str) -> bool:
        """Atualização atômica: só muda se o status atual estiver em 'de' (evita aprovação dupla)."""
        with self.lock, self.con:
            q = f"UPDATE tickets SET status=?, atualizado_em=? WHERE id=? AND status IN ({','.join('?' * len(de))})"
            cur = self.con.execute(q, (para, agora(), tid, *de))
            return cur.rowcount == 1

    def assumir(self, tid: int, ator_id: int):
        with self.lock, self.con:
            self.con.execute("UPDATE tickets SET assumido_por=?, atualizado_em=? WHERE id=?", (ator_id, agora(), tid))

    def atualizar_dados(self, tid: int, dados: dict):
        with self.lock, self.con:
            self.con.execute("UPDATE tickets SET dados=?, atualizado_em=? WHERE id=?",
                             (json.dumps(dados, ensure_ascii=False), agora(), tid))

    def definir_publicacao(self, tid: int, msg_id: int):
        with self.lock, self.con:
            self.con.execute("UPDATE tickets SET publicado_msg=?, atualizado_em=? WHERE id=?", (msg_id, agora(), tid))

    # -- auditoria --------------------------------------------------------------
    def registrar(self, ticket_id: int | None, ator_id: int, acao: str, detalhe: str = ""):
        with self.lock, self.con:
            self.con.execute("INSERT INTO acoes (ticket_id, ator_id, acao, detalhe, data) VALUES (?,?,?,?,?)",
                             (ticket_id, ator_id, acao, detalhe[:1500], agora()))

    def historico(self, ticket_id: int) -> list[dict]:
        return [dict(r) for r in self.con.execute("SELECT * FROM acoes WHERE ticket_id=? ORDER BY id", (ticket_id,))]

    # -- painéis ----------------------------------------------------------------
    def painel(self, chave: str) -> dict | None:
        r = self.con.execute("SELECT * FROM paineis WHERE chave=?", (chave,)).fetchone()
        return dict(r) if r else None

    def salvar_painel(self, chave: str, canal_id: int, msg_id: int):
        with self.lock, self.con:
            self.con.execute("INSERT OR REPLACE INTO paineis (chave, canal_id, msg_id) VALUES (?,?,?)",
                             (chave, canal_id, msg_id))

    @staticmethod
    def _dict(r) -> dict | None:
        if r is None:
            return None
        d = dict(r)
        d["dados"] = json.loads(d.get("dados") or "{}")
        return d

    # -- squads ---------------------------------------------------------------
    @staticmethod
    def _squad(r) -> dict | None:
        if r is None:
            return None
        d = dict(r)
        d["membros"] = json.loads(d.get("membros") or "[]")
        return d

    def criar_squad(self, lider_id: int, jogo: str, plataforma: str, modo: str, estilo: str | None, nome: str,
                    obs: str, id_jogo: str, vagas: int) -> int:
        with self.lock, self.con:
            cur = self.con.execute(
                "INSERT INTO squads (lider_id, jogo, plataforma, modo, estilo, nome, obs, id_jogo, vagas, status,"
                " criado_em) VALUES (?,?,?,?,?,?,?,?,?,'ativo',?)",
                (lider_id, jogo, plataforma, modo, estilo, nome, obs, id_jogo, vagas, agora()))
            return cur.lastrowid

    def squad(self, sid: int) -> dict | None:
        return self._squad(self.con.execute("SELECT * FROM squads WHERE id=?", (sid,)).fetchone())

    def squads_ativos(self) -> list[dict]:
        return [self._squad(r) for r in self.con.execute("SELECT * FROM squads WHERE status='ativo' ORDER BY id")]

    def squad_do_usuario(self, uid: int) -> dict | None:
        """Squad ativo em que a pessoa é líder ou integrante."""
        for s in self.squads_ativos():
            if s["lider_id"] == uid or uid in s["membros"]:
                return s
        return None

    def atualizar_squad(self, sid: int, **campos):
        if "membros" in campos:
            campos["membros"] = json.dumps(campos["membros"])
        cols = ", ".join(f"{k}=?" for k in campos)
        with self.lock, self.con:
            self.con.execute(f"UPDATE squads SET {cols} WHERE id=?", (*campos.values(), sid))

    def encerrar_squad(self, sid: int, motivo: str) -> bool:
        """Atômico: só um encerramento vale (evita apagar a call duas vezes)."""
        with self.lock, self.con:
            cur = self.con.execute("UPDATE squads SET status='encerrado', motivo=?, encerrado_em=? "
                                   "WHERE id=? AND status='ativo'", (motivo, agora(), sid))
            return cur.rowcount == 1

    # -- VIPs -----------------------------------------------------------------
    def vip(self, user_id: int) -> dict | None:
        r = self.con.execute("SELECT * FROM vips WHERE user_id=?", (user_id,)).fetchone()
        return dict(r) if r else None

    def vips(self, origem: str | None = None) -> list[dict]:
        if origem:
            return [dict(r) for r in self.con.execute("SELECT * FROM vips WHERE origem=?", (origem,))]
        return [dict(r) for r in self.con.execute("SELECT * FROM vips")]

    def salvar_vip(self, user_id: int, origem: str, concedido_por: int | None = None, ticket_id: int | None = None):
        """Contribuição tem prioridade: um VIP por contribuição não vira 'boost' (e não perde o VIP sem boost)."""
        atual = self.vip(user_id)
        if atual and atual["origem"] == "contribuicao" and origem == "boost":
            return
        with self.lock, self.con:
            self.con.execute("INSERT OR REPLACE INTO vips (user_id, origem, concedido_por, ticket_id, desde) "
                             "VALUES (?,?,?,?,?)", (user_id, origem, concedido_por, ticket_id, agora()))

    def remover_vip(self, user_id: int):
        with self.lock, self.con:
            self.con.execute("DELETE FROM vips WHERE user_id=?", (user_id,))

    # -- mensagens fixas dos canais -------------------------------------------
    def mensagem_canal(self, chave: str) -> dict | None:
        r = self.con.execute("SELECT * FROM mensagens_canal WHERE chave=?", (chave,)).fetchone()
        return dict(r) if r else None

    def salvar_mensagem_canal(self, chave: str, canal_id: int, msg_id: int, h: str):
        with self.lock, self.con:
            self.con.execute("INSERT OR REPLACE INTO mensagens_canal VALUES (?,?,?,?,?)",
                             (chave, canal_id, msg_id, h, agora()))
