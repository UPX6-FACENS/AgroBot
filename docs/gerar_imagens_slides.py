"""Gera as imagens para os slides em docs/img/ (PNG 1920x1080, 16:9).

Todos os números saem do modelo e do conjunto de teste na hora (reaproveita
scripts/06_relatorio_validacao.py) — nada é digitado à mão. Só roda onde
existem dados/ e checkpoints/ (PC do Samuel):

    python docs/gerar_imagens_slides.py

Os prints reais da conversa (07) e do terminal (08) vêm do teste ao vivo com o
WhatsApp de 2026-11-05: o 07 é recorte de um print de tela, o 08 é o log real.
"""

import importlib.util
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "docs" / "img"
SAIDA.mkdir(parents=True, exist_ok=True)

# --- estilo -----------------------------------------------------------------
for f in ["arial.ttf", "arialbd.ttf", "consola.ttf"]:
    try:
        font_manager.fontManager.addfont(f"C:/Windows/Fonts/{f}")
    except OSError:
        pass
plt.rcParams.update({
    "font.family": "Arial", "font.size": 18, "axes.edgecolor": "#BDBCB5",
    "axes.labelcolor": "#52514E", "xtick.color": "#52514E", "ytick.color": "#52514E",
    "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "white",
})
TINTA = "#0B0B0B"
TINTA2 = "#52514E"
GRADE = "#E1E0D9"
VERDE = "#2E6B30"
# rampa ordinal validada (dataviz validate_palette --ordinal): direto > duvida > humano
ROTA_COR = {"direto": "#1F5A22", "duvida": "#3F8A43", "humano": "#7DB57E"}
NOMES = {"lagarta_cartucho": "Lagarta-do-cartucho", "lagarta_espiga": "Lagarta-da-espiga",
         "milho_sadio": "Milho saudável", "vaquinha": "Vaquinha"}
W, H, DPI = 16, 9, 120


def titulo(fig, t, sub=None):
    fig.text(0.05, 0.93, t, fontsize=34, fontweight="bold", color=TINTA, va="top")
    if sub:
        fig.text(0.05, 0.855, sub, fontsize=19, color=TINTA2, va="top")


def salvar(fig, nome):
    fig.savefig(SAIDA / nome, dpi=DPI)
    plt.close(fig)
    print("ok", nome)


# --- dados: predições do modelo no conjunto de teste ---------------------------
spec = importlib.util.spec_from_file_location("rel", RAIZ / "scripts" / "06_relatorio_validacao.py")
rel = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(RAIZ))
spec.loader.exec_module(rel)
classes, yv, yp, confs, _ = rel.predizer_teste()
acerto = yv == yp
n = len(yv)
ALTA, MEDIA = rel.ALTA, rel.MEDIA

acc = acerto.mean()
baseline = np.bincount(yv).max() / n
direto = confs >= ALTA
duvida = (confs >= MEDIA) & ~direto
humano = confs < MEDIA
erros = ~acerto
segurados = (erros & ~direto).sum() / erros.sum()

f1 = {}
for i, c in enumerate(classes):
    tp = ((yp == i) & (yv == i)).sum()
    prec = tp / max((yp == i).sum(), 1)
    rec = tp / max((yv == i).sum(), 1)
    f1[c] = 2 * prec * rec / max(prec + rec, 1e-9)
f1_macro = np.mean(list(f1.values()))


def pct(x, casas=1):
    return f"{x * 100:.{casas}f}%".replace(".", ",")


# --- 01 cartões de KPI ------------------------------------------------------
fig = plt.figure(figsize=(W, H))
titulo(fig, "Resultados do classificador", f"{n} fotos de teste que o modelo nunca viu no treino")
cartoes = [
    (pct(acc), "acurácia geral", f"chutar sempre a praga mais comum\ndaria {pct(baseline)}"),
    (pct(acerto[direto].mean()), "de acerto quando\no bot afirma a praga", f"{pct(direto.mean())} das fotos têm\nconfiança ≥ {int(ALTA * 100)}%"),
    (pct(segurados), "dos erros viram\n\"manda outra foto\"", "o roteador de confiança segura\no erro antes de virar recomendação"),
    (pct(f1_macro), "F1-macro", "média entre as 4 classes, sem\nfavorecer a classe com mais fotos"),
]
for k, (num, rot, nota) in enumerate(cartoes):
    x = 0.05 + k * 0.23
    ax = fig.add_axes([x, 0.2, 0.21, 0.5])
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.04",
                                fc="#F4F8F2", ec="#CFE0CB", lw=1.5, transform=ax.transAxes))
    ax.text(0.5, 0.66, num, ha="center", fontsize=52, fontweight="bold", color=VERDE, transform=ax.transAxes)
    ax.text(0.5, 0.56, rot, ha="center", va="top", fontsize=19, color=TINTA, transform=ax.transAxes)
    ax.text(0.5, 0.25, nota, ha="center", va="top", fontsize=13.5, color=TINTA2, transform=ax.transAxes)
salvar(fig, "01-resultados.png")

# --- 02 F1 por classe -------------------------------------------------------
fig = plt.figure(figsize=(W, H))
titulo(fig, "Desempenho por praga", "F1 no conjunto de teste (equilíbrio entre precisão e revocação)")
ax = fig.add_axes([0.27, 0.12, 0.62, 0.66])
ordem = sorted(classes, key=lambda c: f1[c])
vals = [f1[c] * 100 for c in ordem]
ax.barh(range(len(ordem)), vals, height=0.56, color=VERDE)
ax.set_yticks(range(len(ordem)))
ax.set_yticklabels([f"{NOMES[c]}\n{(yv == classes.index(c)).sum()} fotos" for c in ordem], fontsize=18)
for i, v in enumerate(vals):
    ax.text(v + 1, i, f"{v:.1f}%".replace(".", ","), va="center", fontsize=20, fontweight="bold", color=TINTA)
ax.set_xlim(0, 100)
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
ax.grid(axis="x", color=GRADE, lw=1)
ax.set_axisbelow(True)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)
fig.text(0.27, 0.04, "Lagarta-da-espiga é a mais fraca: há poucas fotos públicas dela (é a classe com menos exemplos).",
         fontsize=15, color=TINTA2)
salvar(fig, "02-desempenho-por-praga.png")

# --- 03 matriz de confusão --------------------------------------------------
cm = np.zeros((len(classes), len(classes)), int)
for a, b in zip(yv, yp):
    cm[a, b] += 1
frac = cm / cm.sum(axis=1, keepdims=True)
fig = plt.figure(figsize=(W, H))
titulo(fig, "Onde o modelo acerta e onde confunde", "Matriz de confusão — cada linha soma 100% das fotos daquela praga")
ax = fig.add_axes([0.3, 0.17, 0.42, 0.62])
ax.imshow(frac, cmap="Greens", vmin=0, vmax=1)
rot = [NOMES[c].replace("Lagarta-", "Lagarta-\n") for c in classes]
ax.set_xticks(range(len(classes)))
ax.set_xticklabels(rot, fontsize=15)
ax.set_yticks(range(len(classes)))
ax.set_yticklabels([NOMES[c] for c in classes], fontsize=16)
ax.set_xlabel("O que o modelo respondeu", fontsize=16, labelpad=10)
ax.set_ylabel("Praga real", fontsize=16)
for i in range(len(classes)):
    for j in range(len(classes)):
        cor = "white" if frac[i, j] > 0.5 else TINTA
        ax.text(j, i, f"{frac[i, j] * 100:.0f}%\n({cm[i, j]})", ha="center", va="center",
                fontsize=16, color=cor, fontweight="bold" if i == j else "normal")
ax.set_xticks(np.arange(-0.5, len(classes)), minor=True)
ax.set_yticks(np.arange(-0.5, len(classes)), minor=True)
ax.grid(which="minor", color="white", lw=3)
ax.tick_params(which="both", length=0)
for s in ax.spines.values():
    s.set_visible(False)
fig.text(0.75, 0.55, "Diagonal = acertos.\n\nO erro mais comum é\nlagarta-do-cartucho\nconfundida com vaquinha\n" f"({cm[classes.index('lagarta_cartucho'), classes.index('vaquinha')]} fotos).",
         fontsize=16, color=TINTA2, va="center")
salvar(fig, "03-matriz-confusao.png")

# --- 04 roteador de confiança -----------------------------------------------
rotas = [("direto", f"Afirma o diagnóstico\n(confiança ≥ {int(ALTA * 100)}%)", direto),
         ("duvida", f"\"Pode ser X\" e pede outra foto\n({int(MEDIA * 100)}–{int(ALTA * 100)}%)", duvida),
         ("humano", f"Encaminha à Casa da Agricultura\n(< {int(MEDIA * 100)}%)", humano)]
fig = plt.figure(figsize=(W, H))
titulo(fig, "Roteador de confiança: errar para o lado do \"não sei\"",
       f"Dos erros do modelo, {pct(segurados)} não chegam ao produtor como recomendação errada")
ax = fig.add_axes([0.05, 0.56, 0.9, 0.12])
esq = 0
for chave, rot_, m in rotas:
    w = m.mean() * 100
    ax.barh(0, w, left=esq, height=1, color=ROTA_COR[chave], edgecolor="white", linewidth=2)
    if w > 8:
        ax.text(esq + w / 2, 0, f"{w:.1f}%".replace(".", ","), ha="center", va="center", fontsize=22,
                fontweight="bold", color="white")
    else:
        ax.text(esq + w / 2, 0.75, f"{w:.1f}%".replace(".", ","), ha="center", va="bottom", fontsize=18,
                fontweight="bold", color=TINTA)
    esq += w
ax.set_xlim(0, 100)
ax.axis("off")
fig.text(0.05, 0.72, "Para onde vão as fotos", fontsize=20, fontweight="bold", color=TINTA)
ax2 = fig.add_axes([0.36, 0.08, 0.54, 0.36])
fig.text(0.05, 0.47, "Acerto em cada rota", fontsize=20, fontweight="bold", color=TINTA)
for i, (chave, rot_, m) in enumerate(rotas):
    v = acerto[m].mean() * 100
    ax2.barh(i, v, height=0.6, color=ROTA_COR[chave])
    ax2.text(v + 1, i, f"{v:.1f}%".replace(".", ","), va="center", fontsize=19, fontweight="bold", color=TINTA)
    fig.text(0.05, 0.08 + 0.36 * (1 - (i + 0.5) / 3), rot_, fontsize=16, color=TINTA, va="center")
    fig.patches.append(FancyBboxPatch((0.022, 0.08 + 0.36 * (1 - (i + 0.5) / 3) - 0.015), 0.018, 0.03,
                                      boxstyle="round,pad=0,rounding_size=0.004", fc=ROTA_COR[chave], ec="none",
                                      transform=fig.transFigure, figure=fig))
ax2.set_ylim(2.6, -0.6)
ax2.set_xlim(0, 100)
ax2.set_yticks([])
ax2.set_xticks([0, 50, 100])
ax2.set_xticklabels(["0%", "50%", "100%"])
ax2.grid(axis="x", color=GRADE)
ax2.set_axisbelow(True)
ax2.spines["left"].set_visible(False)
salvar(fig, "04-roteador-confianca.png")

# --- 05 curva do limiar -----------------------------------------------------
lims = np.linspace(0, 0.99, 100)
cob = np.array([(confs >= t).mean() for t in lims]) * 100
prec = np.array([acerto[confs >= t].mean() if (confs >= t).any() else np.nan for t in lims]) * 100
fig = plt.figure(figsize=(W, H))
titulo(fig, "Por que o limiar de 80%?", "Quanto mais exigente, mais o bot acerta — mas responde menos fotos direto")
ax = fig.add_axes([0.08, 0.12, 0.72, 0.66])
ax.plot(lims * 100, prec, color=VERDE, lw=3)
ax.plot(lims * 100, cob, color="#8A8984", lw=3)
i80 = int(np.argmin(abs(lims - ALTA)))
ax.axvline(ALTA * 100, color=TINTA2, ls="--", lw=1.5)
for y, cor in [(prec[i80], VERDE), (cob[i80], "#8A8984")]:
    ax.plot(ALTA * 100, y, "o", ms=11, color=cor, mec="white", mew=2)
ax.text(prec[-1] * 0 + 101, prec[-6], "Acerto das\nrespostas diretas", color=VERDE, fontsize=17, fontweight="bold", va="center")
ax.text(101, cob[-6], "Fotos respondidas\ndireto", color="#6E6D68", fontsize=17, fontweight="bold", va="center")
ax.annotate(f"limiar escolhido: {int(ALTA * 100)}%\nacerto {pct(prec[i80] / 100)} · respondidas {pct(cob[i80] / 100)}",
            (ALTA * 100, 52), xytext=(42, 40), fontsize=16, color=TINTA,
            arrowprops=dict(arrowstyle="->", color=TINTA2))
ax.set_xlim(0, 100)
ax.set_ylim(0, 102)
ax.set_xlabel("Confiança mínima para afirmar o diagnóstico (%)")
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
ax.grid(color=GRADE)
ax.set_axisbelow(True)
salvar(fig, "05-por-que-80.png")

# --- 06 fluxo do sistema ----------------------------------------------------
fig = plt.figure(figsize=(W, H))
titulo(fig, "Como o AgroBot responde", "Quem decide a praga é a rede neural; o Claude só escreve em linguagem simples")
ax = fig.add_axes([0, 0, 1, 0.82])
ax.set_xlim(0, 16)
ax.set_ylim(0, 8)
ax.axis("off")


def caixa(x, y, w, h, texto, sub, cor="#F4F8F2", borda="#9DC49A", destaque=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.18",
                                fc=VERDE if destaque else cor, ec=VERDE if destaque else borda, lw=1.8))
    c1 = "white" if destaque else TINTA
    c2 = "#E8F2E4" if destaque else TINTA2
    ax.text(x + w / 2, y + h * 0.64, texto, ha="center", va="center", fontsize=16.5, fontweight="bold", color=c1)
    ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center", fontsize=12.5, color=c2)


def seta(x1, y1, x2, y2, rotulo=None):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color=TINTA2, lw=2, mutation_scale=20))
    if rotulo:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.22, rotulo, ha="center", fontsize=12.5, color=TINTA2)


Y = 4.6
etapas = [("Foto no\nWhatsApp", "produtor"), ("Porteiro de\nqualidade", "nítida? grande?"),
          ("Porteiro de\nassunto", "tem planta/inseto?"), ("Rede neural\n(CNN)", "escolhe a praga"),
          ("Roteador de\nconfiança", "quão certo está?")]
xs = [0.5 + i * 3.05 for i in range(len(etapas))]
for i, (t, s) in enumerate(etapas):
    caixa(xs[i], Y, 2.5, 1.7, t, s, destaque=(i == 3))
    if i:
        seta(xs[i - 1] + 2.55, Y + 0.85, xs[i] - 0.05, Y + 0.85)
# saídas de recusa dos porteiros
caixa(xs[1], 1.9, 2.5, 1.3, "\"Manda outra\nfoto\"", "borrada ou pequena", cor="#F7F7F5", borda="#CCCBC4")
caixa(xs[2], 1.9, 2.5, 1.3, "\"Não encontrei\nmilho nem inseto\"", "selfie, print...", cor="#F7F7F5", borda="#CCCBC4")
seta(xs[1] + 1.25, Y - 0.05, xs[1] + 1.25, 3.25)
seta(xs[2] + 1.25, Y - 0.05, xs[2] + 1.25, 3.25)
# rotas: >=80% sobe, 50-80% desce na diagonal, <50% desce reto
xr = xs[4] + 1.25
caixa(xr - 1.65, 6.55, 3.3, 1.2, "Ficha técnica + Claude", "≥ 80%: diagnóstico + manejo barato", cor="#E8F2E4", borda=VERDE)
caixa(xs[3], 1.9, 2.5, 1.3, "\"Pode ser X...\"", "50–80%: pede outra foto", cor="#F7F7F5", borda="#CCCBC4")
caixa(xs[4], 1.9, 2.5, 1.3, "Casa da Agricultura", "< 50%: não arrisca", cor="#F7F7F5", borda="#CCCBC4")
seta(xr, Y + 1.75, xr, 6.5)
seta(xs[4] + 0.4, Y - 0.05, xs[3] + 1.6, 3.25)
seta(xr + 0.3, Y - 0.05, xr + 0.3, 3.25)
ax.text(0.5, 0.55, "Toda resposta termina com aviso legal (não é receita agronômica) e a pergunta \"Acertei?\" — fixos no código.",
        fontsize=13.5, color=TINTA2)
salvar(fig, "06-como-funciona.png")

# --- 08 log real do terminal ------------------------------------------------
LOG = [  # linhas reais do terminal do webhook (teste ao vivo de 2026-11-05), só com o fim (fromMe/id) cortado
    "17:42:36 | INFO | handlers | mensagem recebida | tipo=imageMessage | de=***8639",
    "17:42:36 | INFO | analise  | classificacao: vaquinha (100%) | rota=direto",
    "17:43:02 | INFO | handlers | Feedback registrado: positivo",
    "17:44:46 | INFO | analise  | classificacao: milho_sadio (100%) | rota=direto",
    "18:01:40 | INFO | handlers | mensagem recebida | tipo=imageMessage | de=***8639",
    "18:01:41 | INFO | analise  | foto reprovada no porteiro: pequena",
    "18:01:55 | INFO | handlers | mensagem recebida | tipo=imageMessage | de=***8639",
    "18:01:56 | INFO | analise  | foto fora do assunto (nao e' milho nem inseto)",
    "18:02:53 | INFO | analise  | classificacao: lagarta_espiga (56%) | rota=duvida",
    "18:03:27 | INFO | handlers | Feedback registrado: positivo",
]
fig = plt.figure(figsize=(W, H), facecolor="#1E1E1E")
fig.text(0.05, 0.92, "O bot funcionando ao vivo", fontsize=34, fontweight="bold", color="white", va="top")
fig.text(0.05, 0.845, "Log real do servidor durante o teste pelo WhatsApp (número mascarado, texto das mensagens não é gravado)",
         fontsize=17, color="#B5B5B0", va="top")
ax = fig.add_axes([0.04, 0.06, 0.92, 0.72])
ax.axis("off")
ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.015", fc="#0C0C0C",
                            ec="#3A3A3A", transform=ax.transAxes))
for i, linha in enumerate(LOG):
    cor = "#D4D4D4"
    if "rota=direto" in linha:
        cor = "#7CD67F"
    elif "rota=duvida" in linha:
        cor = "#E5C07B"
    elif "porteiro" in linha or "fora do assunto" in linha:
        cor = "#61AFEF"
    elif "Feedback" in linha:
        cor = "#C678DD"
    ax.text(0.025, 0.92 - i * 0.087, linha, fontsize=16.5, family="Consolas", color=cor, transform=ax.transAxes)
salvar(fig, "08-log-ao-vivo.png")
