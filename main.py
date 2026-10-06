"""Ghost Recon Brasil — implantação automatizada da estrutura do servidor Discord.

Uso (no PowerShell, dentro da pasta do projeto, com o ambiente virtual ativo):

  python main.py plano          Mostra a estrutura planejada (não usa a internet)
  python main.py convite        Gera o link para autorizar o bot temporário
  python main.py verificar      Confere token, servidor, permissões e hierarquia (não altera nada)
  python main.py simular        Mostra o que seria criado/corrigido (não altera nada)
  python main.py aplicar        Cria/corrige cargos, categorias e canais (pede confirmação)
  python main.py mensagens      (desativado) As mensagens agora são do bot: /servidor publicar
  python main.py onboarding     (Opcional) grava o rascunho do Onboarding (use --simular antes)
  python main.py validar        Valida estrutura e permissões efetivas e gera relatório
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

import config
from gr_setup import estrutura as E
from gr_setup.discord_api import DiscordAPI, ErroAPI
from gr_setup.permissoes import nomes
from gr_setup.provisionador import Contexto, Estado, Provisionador, Resultado
from gr_setup import relatorio
from gr_setup.validador import FALHA, Resolucao, Validador

log = logging.getLogger("gr_setup")


def _api_e_contexto(cfg):
    erros = config.validar_basico(cfg)
    if erros:
        for e in erros:
            log.error("ERRO: %s", e)
        log.error("Edite o arquivo .env (veja .env.example) e tente novamente.")
        sys.exit(2)
    api = DiscordAPI(cfg.token)
    try:
        bot = api.eu()
    except ErroAPI as e:
        if e.status == 401:
            log.error("ERRO: token inválido ou redefinido. Gere um novo no Portal do Desenvolvedor.")
        else:
            log.error("ERRO ao autenticar: %s", e)
        sys.exit(2)
    if not bot.get("bot"):
        log.error("ERRO: o token não pertence a um bot. Este projeto só aceita token de BOT.")
        sys.exit(2)
    log.info("Autenticado como bot: %s (ID %s)", bot.get("username"), bot["id"])
    servidores = {g["id"]: g["name"] for g in api.meus_servidores()}
    if cfg.guild_id not in servidores:
        log.error("ERRO: o bot não está no servidor %s. Servidores do bot: %s",
                  cfg.guild_id, servidores or "nenhum")
        log.error("Use 'python main.py convite' para autorizá-lo no servidor correto.")
        sys.exit(2)
    try:
        ctx = Contexto(api, cfg.guild_id)
    except ErroAPI as e:
        log.error("ERRO ao ler o servidor: %s", e)
        sys.exit(2)
    return api, ctx


def _estado(gid, simular):
    return Estado(config.PASTA_ESTADO / f"estado-{gid}.json", simular)


def _imprimir_resultado(r: Resultado):
    log.info("\n== Resumo ==")
    log.info("Criados: %d | Corrigidos: %d | Já existiam: %d | Preexistentes não alterados: %d | "
             "Avisos: %d | Falhas: %d", len(r.criados), len(r.corrigidos), len(r.existentes),
             len(r.nao_gerenciados), len(r.avisos), len(r.falhas))
    for a in r.avisos:
        log.warning("AVISO: %s", a)
    for f in r.falhas:
        log.error("FALHA: %s", f)


# ---------------------------------------------------------------------------
def cmd_plano(_args, _cfg):
    cont = E.resumo_contagem()
    log.info("Estrutura planejada: %s\n", cont)
    for cat in E.CATEGORIAS:
        log.info("%s%s", cat.nome, "  [PRIVADA]" if cat.privada else "")
        for c in cat.canais:
            extra = []
            if c.modo_lento:
                extra.append(f"modo lento {c.modo_lento}s")
            if c.limite_usuarios:
                extra.append(f"limite {c.limite_usuarios}")
            rot = {"texto": "texto", "anuncio": "anúncio", "voz": "voz"}[c.tipo]
            log.info("   ├─ %-40s (%s%s)", c.nome, rot, (", " + ", ".join(extra)) if extra else "")
    log.info("\nCargos (do mais alto para o mais baixo):")
    for c in E.CARGOS:
        log.info("  - %-28s %s", c.nome, ", ".join(nomes(c.permissoes)) or "sem permissões extras")
    perm = E.permissoes_necessarias_do_bot()
    log.info("\nPermissões do bot temporário (inteiro para o link de convite): %d", perm)
    log.info("  %s", ", ".join(nomes(perm)))


def cmd_convite(_args, cfg):
    app_id = cfg.application_id
    if not app_id and cfg.token:
        try:
            app_id = DiscordAPI(cfg.token).aplicacao()["id"]
        except Exception as e:  # noqa: BLE001
            log.error("Não foi possível descobrir o Application ID pelo token: %s", e)
    if not app_id:
        log.error("Defina DISCORD_APPLICATION_ID (ou DISCORD_BOT_TOKEN) no .env.")
        sys.exit(2)
    perm = E.permissoes_necessarias_do_bot()
    url = (f"https://discord.com/oauth2/authorize?client_id={app_id}&scope=bot&permissions={perm}")
    if cfg.guild_id:
        url += f"&guild_id={cfg.guild_id}&disable_guild_select=true"
    log.info("Abra este link no navegador, confira o servidor e clique em Autorizar:\n\n%s\n", url)
    log.info("Permissões solicitadas (sem Administrador): %s", ", ".join(nomes(perm)))


def cmd_verificar(_args, cfg):
    api, ctx = _api_e_contexto(cfg)
    prov = Provisionador(api, ctx, _estado(cfg.guild_id, True), simular=True)
    bloqueios = prov.verificacoes_previas(cfg.nome_esperado)
    g = ctx.guild
    log.info("Membros (aprox.): %s | Canais: %d | Cargos: %d | Comunidade: %s",
             g.get("approximate_member_count"), len(ctx.channels), len(ctx.roles),
             "sim" if ctx.comunidade else "não")
    log.info("Posição do cargo do bot: %d (cargos do projeto precisam ficar abaixo dele)", ctx.bot_topo)
    for a in prov.r.avisos:
        log.warning("AVISO: %s", a)
    for b in bloqueios:
        log.error("BLOQUEIO: %s", b)
    if bloqueios:
        sys.exit(1)
    log.info("\nTudo pronto para 'python main.py simular'.")


def _provisionar(args, cfg, simular: bool):
    api, ctx = _api_e_contexto(cfg)
    estado = _estado(cfg.guild_id, simular)
    prov = Provisionador(api, ctx, estado, simular=simular, adotar_existentes=args.adotar_existentes)
    bloqueios = prov.verificacoes_previas(cfg.nome_esperado)
    if bloqueios:
        for b in bloqueios:
            log.error("BLOQUEIO: %s", b)
        sys.exit(1)
    if not simular and not args.sim_confirmo:
        log.info("\nATENÇÃO: o script vai CRIAR e CORRIGIR cargos, categorias e canais no servidor:")
        log.info("   %s (ID %s)", ctx.guild["name"], ctx.guild["id"])
        log.info("Nada será apagado. Recursos preexistentes não serão alterados.")
        resposta = input(f"Para confirmar, digite exatamente o nome do servidor ({ctx.guild['name']}): ")
        if resposta.strip() != ctx.guild["name"].strip():
            log.info("Confirmação não conferiu. Nenhuma alteração foi feita.")
            sys.exit(1)
    r = prov.executar()
    _imprimir_resultado(r)
    caminho = relatorio.salvar(config.PASTA_RELATORIOS, "aplicar", simular, r, extras={
        "Servidor": f"{ctx.guild['name']} ({ctx.guild['id']})",
        "Requisições": json.dumps(api.contador)})
    log.info("\nRelatório: %s", caminho)
    if not simular:
        log.info("Próximo passo: 'python main.py validar' (e depois 'python main.py mensagens --simular').")
    return 1 if r.falhas else 0


def cmd_simular(args, cfg):
    return _provisionar(args, cfg, True)


def cmd_aplicar(args, cfg):
    return _provisionar(args, cfg, False)


def cmd_mensagens(args, cfg):
    if not getattr(args, "legado", False):
        log.info("As mensagens dos canais agora são publicadas pelo bot Operação Brasil, com o visual novo.\n"
                 "No Discord, use /servidor publicar (e /servidor verificar para conferir).\n"
                 "Este comando foi desativado para não duplicar mensagens. (Para o modo antigo: --legado)")
        return 0
    from gr_setup.publicacao import publicar_mensagens
    api, ctx = _api_e_contexto(cfg)
    estado = _estado(cfg.guild_id, args.simular)
    res = Resolucao(ctx, estado)
    if not args.simular and not args.sim_confirmo:
        resp = input("Publicar as mensagens iniciais revisadas em gr_setup/mensagens.py? (digite SIM): ")
        if resp.strip().upper() != "SIM":
            log.info("Cancelado.")
            return 1
    r = publicar_mensagens(api, res, estado, args.simular, forcar=args.forcar)
    _imprimir_resultado(r)
    log.info("Relatório: %s", relatorio.salvar(config.PASTA_RELATORIOS, "mensagens", args.simular, r))
    return 1 if r.falhas else 0


def cmd_onboarding(args, cfg):
    from gr_setup.publicacao import montar_onboarding
    api, ctx = _api_e_contexto(cfg)
    if not ctx.comunidade:
        log.error("O Onboarding exige a Comunidade ativada. Ative-a e execute novamente.")
        return 1
    res = Resolucao(ctx, _estado(cfg.guild_id, True))
    try:
        atual = api.onboarding(cfg.guild_id)
    except ErroAPI:
        atual = None
    corpo, faltas = montar_onboarding(res, atual, ativar=args.ativar)
    if faltas:
        log.error("Recursos ausentes: %s. Execute 'aplicar' antes.", faltas)
        return 1
    log.info("Perguntas: %d | Canais padrão: %d | Ativar agora: %s",
             len(corpo["prompts"]), len(corpo["default_channel_ids"]), "sim" if args.ativar else "não (rascunho)")
    for p in corpo["prompts"]:
        log.info("  ? %s  -> %s", p["title"], ", ".join(o["title"] for o in p["options"]))
    if args.simular:
        log.info("[SIMULAÇÃO] nada foi enviado.")
        return 0
    if atual and atual.get("enabled") and not args.ativar:
        log.error("O Onboarding já está ATIVO. Para não desativá-lo, use --ativar ou edite pelo aplicativo.")
        return 1
    # O Discord limita quantas perguntas aparecem na entrada. Tentamos, nesta ordem:
    # 1) todas as perguntas; 2) só as 3 primeiras na entrada e as demais apenas em "Canais e Cargos";
    # 3) só as 3 primeiras.
    todas = corpo["prompts"]
    tentativas = [
        ("todas as perguntas na entrada", todas),
        ("3 perguntas na entrada + as demais só em 'Canais e Cargos'",
         [dict(p, in_onboarding=(i < 3)) for i, p in enumerate(todas)]),
        ("somente as 3 primeiras perguntas", todas[:3]),
    ]
    for descricao, prompts in tentativas:
        try:
            api.put(f"/guilds/{cfg.guild_id}/onboarding", dict(corpo, prompts=prompts))
            log.info("Onboarding gravado (%s). Revise em Configurações do Servidor > Onboarding.", descricao)
            if prompts is not todas:
                faltam = [p["title"] for p in todas if p not in prompts and dict(p, in_onboarding=False) not in prompts]
                if faltam:
                    log.info("Não couberam (adicione à mão se quiser): %s", faltam)
            return 0
        except ErroAPI as e:
            if "TOO_MANY_ONBOARDING_PROMPTS" in str(e):
                log.warning("O Discord recusou %s por excesso de perguntas; tentando versão menor.", descricao)
                continue
            log.error("Falha ao gravar Onboarding: %s", e)
            break
    log.error("Configure manualmente seguindo docs/04-configuracao-manual.md (seção Onboarding).")
    return 1


def cmd_validar(_args, cfg):
    api, ctx = _api_e_contexto(cfg)
    checks = Validador(ctx, _estado(cfg.guild_id, True)).executar()
    for c in checks:
        log.info("[%-8s] %-4s %s %s", c.status, c.numero, c.descricao, f"— {c.detalhe}" if c.detalhe else "")
    try:
        onb = api.onboarding(cfg.guild_id)
        extras_onb = f"ativado={onb.get('enabled')}, perguntas={len(onb.get('prompts', []))}, " \
                     f"canais padrão={len(onb.get('default_channel_ids', []))}"
    except ErroAPI as e:
        extras_onb = f"não foi possível ler ({e.status})"
    caminho = relatorio.salvar(config.PASTA_RELATORIOS, "validar", False, checks=checks, extras={
        "Servidor": f"{ctx.guild['name']} ({ctx.guild['id']})", "Onboarding": extras_onb})
    log.info("\nOnboarding: %s", extras_onb)
    log.info("Relatório: %s", caminho)
    return 1 if any(c.status == FALHA for c in checks) else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Implantação do servidor Ghost Recon Brasil")
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("plano")
    sub.add_parser("convite")
    sub.add_parser("verificar")
    for nome in ("simular", "aplicar"):
        p = sub.add_parser(nome)
        p.add_argument("--adotar-existentes", action="store_true",
                       help="Permite corrigir recursos com o mesmo nome que já existiam antes do script")
        p.add_argument("--sim-confirmo", action="store_true", help="Pula a pergunta de confirmação")
    p = sub.add_parser("mensagens")
    p.add_argument("--legado", action="store_true",
                   help="Usa o publicador antigo (o bot de configuração). Normalmente use /servidor publicar.")
    p.add_argument("--simular", action="store_true")
    p.add_argument("--sim-confirmo", action="store_true")
    p.add_argument("--forcar", action="store_true",
                   help="Publica mesmo em canais com mensagens de outro bot que não podem ser comparadas")
    p = sub.add_parser("onboarding")
    p.add_argument("--simular", action="store_true")
    p.add_argument("--ativar", action="store_true", help="Grava já ativado (padrão: rascunho desativado)")
    sub.add_parser("validar")
    args = parser.parse_args(argv)

    cfg = config.carregar()
    caminho_log = config.configurar_log(args.comando, cfg.token)
    comandos = {"plano": cmd_plano, "convite": cmd_convite, "verificar": cmd_verificar,
                "simular": cmd_simular, "aplicar": cmd_aplicar, "mensagens": cmd_mensagens,
                "onboarding": cmd_onboarding, "validar": cmd_validar}
    try:
        codigo = comandos[args.comando](args, cfg) or 0
    except KeyboardInterrupt:
        log.error("\nInterrompido pelo usuário. Execute novamente: o script continua de onde parou.")
        codigo = 130
    except ErroAPI as e:
        log.error("ERRO da API: %s", e)
        codigo = 1
    finally:
        log.info("Log desta execução: %s", caminho_log)
        config.fechar_log()
    return codigo


if __name__ == "__main__":
    sys.exit(main())
