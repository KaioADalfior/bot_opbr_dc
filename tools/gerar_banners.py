"""Gera os banners dos embeds (bot/assets). Uso: python tools/gerar_banners.py

Precisa da fonte Inter Display (https://rsms.me/inter/). Os PNGs já vêm prontos no projeto;
rode só se quiser mudar textos ou cores.
"""
import math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
from pathlib import Path
F = os.environ.get("FONTES_INTER", "/usr/share/fonts/opentype/inter/")
SAIDA = Path(__file__).resolve().parents[1] / "bot" / "assets"
def font(n,s): return ImageFont.truetype(F+n,s)
def spaced(d,xy,txt,f,fill,sp):
    x,y=xy
    for ch in txt:
        d.text((x,y),ch,font=f,fill=fill); x+=d.textlength(ch,font=f)+sp
    return x
def width(d,txt,f,sp): return sum(d.textlength(c,font=f)+sp for c in txt)-sp
def hexrgb(h): return ((h>>16)&255,(h>>8)&255,h&255)

def base(W,H,acc,seed=1):
    random.seed(seed)
    img=Image.new("RGB",(W,H),(9,13,18))
    # vertical gradient + accent glow from left
    glow=Image.new("RGB",(W,H),(0,0,0)); g=ImageDraw.Draw(glow)
    g.ellipse((-W*0.35,-H*0.8,W*0.45,H*1.8),fill=tuple(int(c*0.55) for c in acc))
    glow=glow.filter(ImageFilter.GaussianBlur(120))
    img=Image.blend(img,glow,0.55)
    d=ImageDraw.Draw(img,"RGBA")
    # topographic contour lines
    for k in range(14):
        cx,cy=W*0.78+random.randint(-40,40),H*0.5+random.randint(-30,30)
        r=40+k*28
        pts=[]
        for t in range(0,361,4):
            a=math.radians(t); rr=r*(1+0.12*math.sin(3*a+k)+0.06*math.cos(5*a+k*0.7))
            pts.append((cx+rr*math.cos(a)*1.6,cy+rr*math.sin(a)))
        d.line(pts,fill=(255,255,255,14),width=2)
    # grid
    for x in range(0,W,40): d.line([(x,0),(x,H)],fill=(255,255,255,7))
    for y in range(0,H,40): d.line([(0,y),(W,y)],fill=(255,255,255,7))
    # diagonal hazard band bottom
    d.rectangle((0,H-10,W,H),fill=acc+(255,))
    for x in range(-40,W,34):
        d.polygon([(x,H-10),(x+16,H-10),(x+6,H),(x-10,H)],fill=(9,13,18,170))
    # left accent bar
    d.rectangle((0,0,10,H-10),fill=acc+(255,))
    # corner brackets
    c=(255,255,255,90); L=26
    for (x,y,sx,sy) in ((W-36,24,1,1),(W-36,H-34,1,-1)):
        d.line([(x,y),(x+L*sx*-1+L,y)],fill=c,width=3)
    return img,d

def crosshair(d,cx,cy,r,col):
    d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=col,width=3)
    d.ellipse((cx-r*0.45,cy-r*0.45,cx+r*0.45,cy+r*0.45),outline=col,width=2)
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        d.line([(cx+dx*r*0.6,cy+dy*r*0.6),(cx+dx*r*1.35,cy+dy*r*1.35)],fill=col,width=3)
    d.ellipse((cx-4,cy-4,cx+4,cy+4),fill=col)

def painel():
    W,H=1200,380; acc=(56,189,248)
    img,d=base(W,H,acc,3)
    crosshair(d,W-190,H/2-8,92,(56,189,248,150))
    spaced(d,(64,70),"GHOST RECON® | OPERAÇÃO BRASIL",font("InterDisplay-Bold.otf",22),(56,189,248),4)
    spaced(d,(60,108),"CENTRAL DE",font("InterDisplay-Black.otf",74),(240,244,248),2)
    spaced(d,(60,188),"ESQUADRÕES",font("InterDisplay-Black.otf",92),(255,255,255),2)
    d.rectangle((64,300,64+70,304),fill=acc+(255,))
    spaced(d,(150,290),"MONTE SEU SQUAD  •  GANHE UMA CALL EXCLUSIVA",font("InterDisplay-SemiBold.otf",20),(170,182,196),2)
    img.save(SAIDA / "painel_squads.png",optimize=True)

def card(chave,nome,sub,acc_hex,emblema):
    W,H=1200,300; acc=hexrgb(acc_hex)
    img,d=base(W,H,acc,hash(chave)%100)
    crosshair(d,W-170,H/2-6,74,acc+(140,))
    spaced(d,(62,62),"SQUAD  •  "+sub,font("InterDisplay-Bold.otf",22),acc,4)
    f=font("InterDisplay-Black.otf",104 if len(nome)<11 else 86)
    spaced(d,(56,96),nome,f,(255,255,255),2)
    spaced(d,(62,226),emblema,font("InterDisplay-SemiBold.otf",20),(170,182,196),3)
    img.save(SAIDA / f"squad_{chave}.png",optimize=True)

def vip():
    W,H=1200,380; acc=(168,85,247)
    img,d=base(W,H,acc,7)
    # diamante estilizado
    cx,cy,r=W-190,H/2-8,88
    pts=[(cx,cy-r),(cx+r*0.9,cy-r*0.25),(cx,cy+r),(cx-r*0.9,cy-r*0.25)]
    d.polygon(pts,outline=(196,140,255,190),width=4)
    d.line([(cx-r*0.9,cy-r*0.25),(cx+r*0.9,cy-r*0.25)],fill=(196,140,255,150),width=3)
    for x in (-0.45,0,0.45):
        d.line([(cx+x*r,cy-r*0.25),(cx,cy+r)],fill=(196,140,255,110),width=2)
    d.line([(cx-r*0.45,cy-r*0.25),(cx,cy-r)],fill=(196,140,255,110),width=2)
    d.line([(cx+r*0.45,cy-r*0.25),(cx,cy-r)],fill=(196,140,255,110),width=2)
    spaced(d,(64,70),"GHOST RECON® | OPERAÇÃO BRASIL",font("InterDisplay-Bold.otf",22),(196,140,255),4)
    spaced(d,(60,108),"APOIE A",font("InterDisplay-Black.otf",74),(240,244,248),2)
    spaced(d,(60,188),"COMUNIDADE",font("InterDisplay-Black.otf",92),(255,255,255),2)
    d.rectangle((64,300,64+70,304),fill=acc+(255,))
    spaced(d,(150,290),"CONTRIBUA  •  IMPULSIONE  •  TORNE-SE VIP",font("InterDisplay-SemiBold.otf",20),(170,182,196),2)
    img.save(SAIDA / "painel_vip.png",optimize=True)


def faixa(arquivo, topo, titulo, rodape, acc_hex, simbolo="mira", W=1200, H=300, seed=0):
    """Banner genérico: rótulo pequeno em cima, título grande, linha de apoio embaixo."""
    acc = hexrgb(acc_hex)
    img, d = base(W, H, acc, seed)
    cx, cy = W - 170, H / 2 - 6
    if simbolo == "mira":
        crosshair(d, cx, cy, 74, acc + (140,))
    elif simbolo == "escudo":
        r = 70
        d.polygon([(cx - r, cy - r * 0.8), (cx + r, cy - r * 0.8), (cx + r * 0.85, cy + r * 0.2), (cx, cy + r),
                   (cx - r * 0.85, cy + r * 0.2)], outline=acc + (170,), width=4)
        d.line([(cx, cy - r * 0.8), (cx, cy + r)], fill=acc + (110,), width=2)
    elif simbolo == "radar":
        for k in (1, 0.66, 0.33):
            d.ellipse((cx - 80 * k, cy - 80 * k, cx + 80 * k, cy + 80 * k), outline=acc + (120,), width=2)
        d.pieslice((cx - 80, cy - 80, cx + 80, cy + 80), -60, -20, fill=acc + (70,))
    elif simbolo == "alerta":
        r = 78
        d.polygon([(cx, cy - r), (cx + r, cy + r * 0.75), (cx - r, cy + r * 0.75)], outline=acc + (190,), width=5)
        d.rectangle((cx - 5, cy - r * 0.35, cx + 5, cy + r * 0.3), fill=acc + (190,))
        d.ellipse((cx - 6, cy + r * 0.42, cx + 6, cy + r * 0.56), fill=acc + (190,))
    oy = (H - 300) // 2
    spaced(d, (62, 62 + oy), topo, font("InterDisplay-Bold.otf", 22), acc, 4)
    tam = 104
    f = font("InterDisplay-Black.otf", tam)
    while width(d, titulo, f, 2) > W - 360 and tam > 50:
        tam -= 4
        f = font("InterDisplay-Black.otf", tam)
    spaced(d, (56, 96 + oy + (104 - tam) // 2), titulo, f, (255, 255, 255), 2)
    spaced(d, (62, 226 + oy), rodape, font("InterDisplay-SemiBold.otf", 20), (170, 182, 196), 3)
    img.save(SAIDA / arquivo, optimize=True)


# categoria -> (rótulo, cor, símbolo)
CATEGORIAS = {
    "central": ("QUARTEL-GENERAL", 0xE2B33C, "radar"),
    "vips": ("ÁREA VIP", 0xA855F7, "mira"),
    "alistamento": ("ALISTAMENTO", 0xF97316, "mira"),
    "chat": ("COMUNIDADE", 0x14B8A6, "radar"),
    "ajuda": ("SUPORTE", 0xF59E0B, "radar"),
    "mods": ("MODS", 0x06B6D4, "mira"),
    "breakpoint": ("GHOST RECON® BREAKPOINT", 0x38BDF8, "mira"),
    "wildlands": ("GHOST RECON® WILDLANDS", 0x65A30D, "mira"),
    "equipe": ("EQUIPE", 0xEF4444, "escudo"),
}

# canal -> (categoria, título grande, linha de apoio)
CANAIS = {
    "boas_vindas": ("central", "BEM-VINDO", "NENHUM OPERADOR FICA PARA TRÁS"),
    "regras": ("central", "REGRAS", "LEIA ANTES DE PARTICIPAR"),
    "anuncios": ("central", "ANÚNCIOS", "COMUNICADOS OFICIAIS DA EQUIPE"),
    "comece_aqui": ("central", "COMECE AQUI", "SEU PRIMEIRO BRIEFING"),
    "vips": ("vips", "VIPS", "QUEM FORTALECE A COMUNIDADE"),
    "squad_raid": ("alistamento", "SQUAD RAID", "FORME SUA EQUIPE PARA AS RAIDS"),
    "geral": ("chat", "PAPO GERAL", "CONVERSA LIVRE DA COMUNIDADE"),
    "fotos_memes": ("chat", "FOTOS & MEMES", "O LADO LEVE DA OPERAÇÃO"),
    "outfits": ("chat", "OUTFITS", "MOSTRE SEU OPERADOR"),
    "sugestoes": ("chat", "SUGESTÕES", "AJUDE A MELHORAR O SERVIDOR"),
    "comandos": ("chat", "COMANDOS", "COMO USAR O BOT OPERAÇÃO BRASIL"),
    "clips": ("chat", "CLIPS", "SUAS MELHORES JOGADAS"),
    "lives": ("chat", "LIVES", "DIVULGUE SUA TRANSMISSÃO"),
    "suporte_geral": ("ajuda", "SUPORTE", "ACESSO, CARGOS E CANAIS"),
    "suporte_dicas": ("ajuda", "DICAS", "PROBLEMAS E AJUSTES DOS JOGOS"),
    "duvidas": ("ajuda", "DÚVIDAS", "PERGUNTE À COMUNIDADE"),
    "mods_publicados": ("mods", "MODS APROVADOS", "REVISADOS PELA EQUIPE"),
    "discussao_mods": ("mods", "DISCUSSÃO", "INSTALAÇÃO, COMPATIBILIDADE E DICAS"),
    "regras_mods": ("mods", "REGRAS DE MODS", "CRITÉRIOS DE APROVAÇÃO"),
    "chat_breakpoint": ("breakpoint", "BREAKPOINT", "AUROA  •  MISSÕES, BUILDS E COOP"),
    "raid_semanal": ("breakpoint", "RAID SEMANAL", "PLANEJAMENTO E INSCRIÇÕES"),
    "chat_wildlands": ("wildlands", "WILDLANDS", "BOLÍVIA  •  CAMPANHA E EXPLORAÇÃO"),
    "chat_equipe": ("equipe", "CHAT DA EQUIPE", "ÁREA RESTRITA"),
    "logs_moderacao": ("equipe", "LOGS", "REGISTRO DE MODERAÇÃO"),
    "relatorios": ("equipe", "RELATÓRIOS", "TRANSCRIPTS E OCORRÊNCIAS"),
}


def gerar_todos():
    painel()
    card("breakpoint", "BREAKPOINT", "GHOST RECON®", 0x38BDF8, "AUROA  •  COOP ATÉ 4  •  OPERAÇÃO BRASIL")
    card("wildlands", "WILDLANDS", "GHOST RECON®", 0x65A30D, "BOLÍVIA  •  COOP ATÉ 4  •  OPERAÇÃO BRASIL")
    card("r6", "SIEGE", "RAINBOW SIX", 0x3B82F6, "TIME ATÉ 5  •  OPERAÇÃO BRASIL")
    vip()
    faixa("painel_denuncia.png", "GHOST RECON® | OPERAÇÃO BRASIL", "FALE COM A EQUIPE", "ATENDIMENTO PRIVADO E SEGURO",
          0xEF4444, "alerta", H=380)
    faixa("painel_mods.png", "GHOST RECON® | OPERAÇÃO BRASIL", "CENTRAL DE MODS", "ENVIE  •  A EQUIPE AVALIA  •  PUBLICAMOS",
          0x06B6D4, "mira", H=380)
    for i, (canal, (cat, titulo, apoio)) in enumerate(CANAIS.items()):
        rot, cor, simb = CATEGORIAS[cat]
        faixa(f"canal_{canal}.png", rot, titulo, apoio, cor, simb, seed=i + 11)
    print("Banners gerados em", SAIDA)


if __name__ == "__main__":
    gerar_todos()
