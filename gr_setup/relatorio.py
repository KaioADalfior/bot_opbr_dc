"""Geração de relatórios (Markdown + JSON) sem segredos."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .provisionador import Resultado
from .validador import Checagem

PENDENCIAS_MANUAIS = [
    "Ativar a Comunidade (se ainda não estiver ativa) e executar 'aplicar' de novo para converter #anuncios.",
    "Ativar Administrador no cargo '👑 Líder Fundador' e atribuí-lo a você.",
    "Configurar Triagem de Regras (Configuração de Segurança > Proteção contra DM e Spam).",
    "Revisar e ativar Onboarding e Guia do Servidor.",
    "Configurar Proteção contra ataques e CAPTCHA, AutoMod e 2FA para moderação.",
    "Preencher descrição, idioma e ícone; criar convite permanente.",
    "Testar a entrada com uma conta secundária.",
    "Remover o bot temporário e redefinir o token no Portal do Desenvolvedor.",
]


def salvar(pasta: Path, comando: str, simular: bool, resultado: Resultado | None = None,
           checks: list[Checagem] | None = None, extras: dict | None = None) -> Path:
    pasta.mkdir(exist_ok=True)
    agora = datetime.now()
    base = pasta / f"{agora:%Y%m%d-%H%M%S}-{comando}{'-simulacao' if simular else ''}"
    linhas = [f"# Relatório — {comando}{' (SIMULAÇÃO: nada foi alterado)' if simular else ''}",
              "", f"Gerado em {agora:%d/%m/%Y %H:%M:%S}", ""]
    dados = {"comando": comando, "simulacao": simular, "data": agora.isoformat()}
    if extras:
        dados.update(extras)
        linhas += ["## Contexto", ""] + [f"- **{k}:** {v}" for k, v in extras.items()] + [""]
    if resultado:
        d = resultado.como_dict()
        dados["resultado"] = d
        titulos = {"criados": "Criados", "corrigidos": "Corrigidos", "existentes": "Já existiam (sem mudança)",
                   "nao_gerenciados": "Preexistentes não alterados", "avisos": "Avisos", "falhas": "Falhas"}
        linhas += ["## Resumo", "", "| Situação | Quantidade |", "|---|---|"]
        linhas += [f"| {t} | {len(d[k])} |" for k, t in titulos.items()] + [""]
        for k, t in titulos.items():
            if d[k]:
                linhas += [f"## {t}", ""] + [f"- {x}" for x in d[k]] + [""]
    if checks:
        dados["checagens"] = [c.__dict__ for c in checks]
        cont = {}
        for c in checks:
            cont[c.status] = cont.get(c.status, 0) + 1
        linhas += ["## Validação", "", " · ".join(f"**{k}**: {v}" for k, v in sorted(cont.items())), "",
                   "| # | Verificação | Status | Detalhe |", "|---|---|---|---|"]
        icone = {"OK": "✅", "FALHA": "❌", "PENDENTE": "⏳", "AVISO": "⚠️", "INFO": "ℹ️"}
        for c in checks:
            det = c.detalhe.replace("|", "/")
            linhas.append(f"| {c.numero} | {c.descricao} | {icone.get(c.status, '')} {c.status} | {det} |")
        linhas.append("")
    linhas += ["## Etapas manuais pendentes (conferir em docs/04-configuracao-manual.md)", ""]
    linhas += [f"- [ ] {p}" for p in PENDENCIAS_MANUAIS]
    base.with_suffix(".md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    base.with_suffix(".json").write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
    return base.with_suffix(".md")
