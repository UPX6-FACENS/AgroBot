"""Gera o PDF de estudo para a apresentacao do Doutor da Roca.
Execute: python docs/gerar_relatorio_apresentacao.py
Saida:   docs/relatorio_apresentacao.pdf
"""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether, Image as RLImage,
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas as pdfcanvas

# ── Paleta ────────────────────────────────────────────────────────────────────
VERDE_ESCURO   = colors.HexColor("#1B4332")
VERDE_MEDIO    = colors.HexColor("#2D6A4F")
VERDE_CLARO    = colors.HexColor("#52B788")
VERDE_PALIDO   = colors.HexColor("#D8F3DC")
AMARELO        = colors.HexColor("#F9C74F")
LARANJA        = colors.HexColor("#F3722C")
VERMELHO       = colors.HexColor("#E63946")
AZUL           = colors.HexColor("#264653")
CINZA_ESCURO   = colors.HexColor("#2D3436")
CINZA_CLARO    = colors.HexColor("#F4F4F4")
BRANCO         = colors.white

W, H = A4
MARGEM = 1.8 * cm

# ── Pasta de imagens ──────────────────────────────────────────────────────────
RAIZ = Path(__file__).resolve().parent.parent
IMG  = RAIZ / "docs" / "img"
OUT  = RAIZ / "docs" / "relatorio_apresentacao.pdf"


# ── Helpers de estilo ─────────────────────────────────────────────────────────
def estilo_base():
    estilos = getSampleStyleSheet()
    base = dict(
        fontName="Helvetica", fontSize=10, leading=15,
        textColor=CINZA_ESCURO, spaceAfter=4,
    )
    estilos.add(ParagraphStyle("BodyPT",    **base))
    estilos.add(ParagraphStyle("BodyJust",  alignment=TA_JUSTIFY, **base))
    estilos.add(ParagraphStyle("BoldLabel", fontName="Helvetica-Bold", fontSize=10,
                                leading=14, textColor=VERDE_ESCURO, spaceAfter=2))
    estilos.add(ParagraphStyle("Titulo",    fontName="Helvetica-Bold", fontSize=22,
                                leading=28, textColor=BRANCO, alignment=TA_CENTER))
    estilos.add(ParagraphStyle("Subtitulo", fontName="Helvetica", fontSize=13,
                                leading=18, textColor=BRANCO, alignment=TA_CENTER))
    estilos.add(ParagraphStyle("SecTitle",  fontName="Helvetica-Bold", fontSize=14,
                                leading=20, textColor=VERDE_ESCURO, spaceAfter=6))
    estilos.add(ParagraphStyle("SubTitle",  fontName="Helvetica-Bold", fontSize=11,
                                leading=16, textColor=VERDE_MEDIO, spaceAfter=4))
    estilos.add(ParagraphStyle("Mono",      fontName="Courier", fontSize=8.5,
                                leading=13, textColor=CINZA_ESCURO,
                                backColor=CINZA_CLARO, spaceAfter=2))
    estilos.add(ParagraphStyle("Tag",       fontName="Helvetica-Bold", fontSize=8,
                                leading=11, textColor=BRANCO, alignment=TA_CENTER))
    estilos.add(ParagraphStyle("Rodape",    fontName="Helvetica", fontSize=8,
                                leading=11, textColor=colors.grey, alignment=TA_CENTER))
    estilos.add(ParagraphStyle("Pergunta",  fontName="Helvetica-Bold", fontSize=10.5,
                                leading=15, textColor=AZUL, spaceAfter=3))
    estilos.add(ParagraphStyle("Resposta",  fontName="Helvetica", fontSize=10,
                                leading=15, textColor=CINZA_ESCURO,
                                leftIndent=12, spaceAfter=10))
    return estilos


ES = estilo_base()


# ── Componentes graficos ──────────────────────────────────────────────────────
class BandaCabecalho(Flowable):
    """Faixa verde no topo da capa."""
    def __init__(self, h=5.5*cm):
        super().__init__()
        self._h = h
        self.width  = W
        self.height = h

    def draw(self):
        c = self.canv
        # gradiente simulado com retangulos
        steps = 60
        for i in range(steps):
            t = i / steps
            r = VERDE_ESCURO.red   + t * (VERDE_MEDIO.red   - VERDE_ESCURO.red)
            g = VERDE_ESCURO.green + t * (VERDE_MEDIO.green - VERDE_ESCURO.green)
            b = VERDE_ESCURO.blue  + t * (VERDE_MEDIO.blue  - VERDE_ESCURO.blue)
            c.setFillColorRGB(r, g, b)
            slice_w = self.width / steps
            c.rect(i * slice_w, 0, slice_w + 0.5, self._h, fill=1, stroke=0)
        # circulo decorativo
        c.setFillColor(colors.HexColor("#FFFFFF20"))
        c.circle(W - 2*cm, self._h - 1*cm, 3.5*cm, fill=1, stroke=0)
        c.circle(W - 4*cm, self._h + 0.5*cm, 2*cm, fill=1, stroke=0)


class FaixaSecao(Flowable):
    """Faixa colorida que serve de cabecalho de secao."""
    def __init__(self, titulo, cor=VERDE_MEDIO, numero=""):
        super().__init__()
        self._titulo = titulo
        self._cor    = cor
        self._num    = numero
        self.width   = W - 2 * MARGEM
        self.height  = 1.0 * cm

    def draw(self):
        c = self.canv
        c.setFillColor(self._cor)
        c.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)
        if self._num:
            c.setFillColor(colors.HexColor("#FFFFFF50"))
            c.setFont("Helvetica-Bold", 20)
            c.drawString(4, 2, self._num)
            c.setFillColor(BRANCO)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(28, 6, self._titulo.upper())
        else:
            c.setFillColor(BRANCO)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(10, 6, self._titulo.upper())


class CaixaDestaque(Flowable):
    """Caixa colorida de destaque (para frases-chave)."""
    def __init__(self, texto, cor_fundo=VERDE_PALIDO, cor_borda=VERDE_CLARO,
                 cor_texto=VERDE_ESCURO, largura=None):
        super().__init__()
        self._texto = texto
        self._fundo = cor_fundo
        self._borda = cor_borda
        self._ctexto = cor_texto
        self.width  = largura or (W - 2 * MARGEM)
        self.height = 1.4 * cm

    def draw(self):
        c = self.canv
        c.setFillColor(self._fundo)
        c.setStrokeColor(self._borda)
        c.setLineWidth(1.5)
        c.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=1)
        # barra lateral
        c.setFillColor(self._borda)
        c.roundRect(0, 0, 5, self.height, 3, fill=1, stroke=0)
        c.setFillColor(self._ctexto)
        c.setFont("Helvetica-BoldOblique", 10.5)
        c.drawString(14, self.height / 2 - 5, self._texto)


def tag(texto, cor):
    return Paragraph(
        f'<font color="white"><b>{texto}</b></font>',
        ParagraphStyle("_tag", parent=ES["Tag"], backColor=cor,
                       borderPadding=(3, 6, 3, 6), borderRadius=4,
                       borderColor=cor, borderWidth=0)
    )


def linha_hr(cor=VERDE_CLARO, espessura=0.8):
    return HRFlowable(width="100%", thickness=espessura, color=cor, spaceAfter=6)


def p(texto, estilo="BodyPT"):
    return Paragraph(texto, ES[estilo])


def sp(h=0.3):
    return Spacer(1, h * cm)


def tabela(dados, col_w, estilos_extra=None, header=True):
    ts = [
        ("BACKGROUND", (0, 0), (-1, 0), VERDE_ESCURO),
        ("TEXTCOLOR",  (0, 0), (-1, 0), BRANCO),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 9),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BRANCO, VERDE_PALIDO]),
        ("FONTNAME",   (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 1), (-1, -1), 9),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [4]),
    ]
    if not header:
        ts = [s for s in ts if s[0] not in
              ("BACKGROUND", "TEXTCOLOR", "FONTNAME") or s[2] != (0, 0)]
    if estilos_extra:
        ts += estilos_extra
    t = Table(dados, colWidths=col_w, repeatRows=1 if header else 0)
    t.setStyle(TableStyle(ts))
    return t


def imagem_se_existe(nome, largura=None, altura=None):
    p_img = IMG / nome
    if not p_img.exists():
        return sp(0.2)
    kw = {}
    if largura: kw["width"]  = largura
    if altura:  kw["height"] = altura
    return RLImage(str(p_img), **kw)


# ── Callback de rodape/cabecalho por pagina ───────────────────────────────────
def rodape(canv, doc):
    canv.saveState()
    canv.setFont("Helvetica", 7.5)
    canv.setFillColor(colors.grey)
    canv.drawCentredString(W / 2, 1.1 * cm,
        f"Doutor da Roca · Engenharia de Computacao · Facens · UPX6 · {doc.page}")
    canv.restoreState()


# ── CONTEuDO ──────────────────────────────────────────────────────────────────
def construir_pdf():
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=MARGEM, rightMargin=MARGEM,
        topMargin=MARGEM,  bottomMargin=1.8 * cm,
    )

    story = []
    largura_util = W - 2 * MARGEM

    # ══════════════════════════════════════════════════════════════════════════
    # CAPA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(BandaCabecalho(6 * cm))
    story.append(sp(-0.3))

    # titulos sobre a faixa (sobreposicao via posicao negativa nao funciona
    # no platypus; usamos paragrafos com backColor para simular)
    story.append(Paragraph(
        '<font color="#FFFFFF"><b>🌽 DOUTOR DA ROcA</b></font>',
        ParagraphStyle("CapaTit", fontName="Helvetica-Bold", fontSize=26,
                       leading=32, textColor=BRANCO, alignment=TA_CENTER,
                       backColor=VERDE_ESCURO, spaceAfter=4,
                       borderPadding=(10, 0, 4, 0))
    ))
    story.append(Paragraph(
        '<font color="#D8F3DC">Chatbot de WhatsApp para identificacao de pragas do milho</font>',
        ParagraphStyle("CapaSub", fontName="Helvetica", fontSize=13,
                       leading=18, textColor=VERDE_PALIDO, alignment=TA_CENTER,
                       backColor=VERDE_ESCURO, spaceAfter=0,
                       borderPadding=(0, 0, 12, 0))
    ))

    story.append(sp(0.6))
    story.append(linha_hr(VERDE_CLARO, 1.5))
    story.append(sp(0.3))

    # Metadados
    meta = [
        ["📚 Projeto", "UPX6 -- Engenharia de Computacao · Facens · 2026"],
        ["👨‍🏫 Orientador", "Prof. Lucas Monteiro"],
        ["👥 Integrantes", "Matheus Cravo · Murilo Garcia · Rafael Reis"],
        ["",             "Samuel Delgado (lider) · Victor Rodrigues · Vitor Pitaluga"],
        ["📋 Objetivo", "Ajudar o pequeno produtor a identificar praga por foto,"],
        ["",            "sem agronomo, sem app, direto no WhatsApp."],
    ]
    t_meta = Table(meta, colWidths=[3.5*cm, largura_util - 3.5*cm])
    t_meta.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",  (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",  (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), VERDE_ESCURO),
        ("VALIGN",    (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t_meta)
    story.append(sp(0.5))

    story.append(CaixaDestaque(
        '"Separamos quem decide de quem escreve." -- principio central do projeto'
    ))

    story.append(sp(0.6))
    story.append(linha_hr())
    story.append(p("GUIA DE ESTUDO PARA A APRESENTAcaO TeCNICA", "SecTitle"))
    story.append(p(
        "Este documento cobre: arquitetura completa do sistema, decisoes tecnicas com justificativa, "
        "resultados numericos, e as perguntas mais provaveis da banca com as respostas prontas.",
        "BodyJust"
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 1. PROBLEMA E PERSONA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(FaixaSecao("1. Problema e Persona", VERDE_ESCURO, "1"))
    story.append(sp(0.4))

    story.append(p("Quem e o usuario", "SubTitle"))
    story.append(p(
        "<b>Ze do Sitio</b>, 52 anos, Piedade/SP -- planta milho e hortalicas em ~8 ha. "
        "Estudou ate a 5ª serie. Usa WhatsApp como principal interface digital. "
        "Prefere audio a texto. Internet 4G instavel; sem sinal no fundo da lavoura.",
        "BodyJust"
    ))
    story.append(sp(0.3))

    story.append(p("A dor em uma frase", "SubTitle"))
    story.append(CaixaDestaque(
        '"Perde safra porque nao identifica a praga a tempo e nao tem dinheiro para agronomo."',
        cor_fundo=colors.HexColor("#FFF3CD"),
        cor_borda=AMARELO,
        cor_texto=colors.HexColor("#7D4E00"),
    ))
    story.append(sp(0.4))

    story.append(p("O que ele quer", "SubTitle"))
    passos = [
        ["1", "Tirar uma foto da folha ou do bicho"],
        ["2", "Mandar no WhatsApp -- sem instalar nada, sem criar conta"],
        ["3", "Receber uma resposta simples: o que e e o que fazer"],
        ["4", "Saber qual opcao e mais barata primeiro"],
    ]
    t_passos = Table(passos, colWidths=[0.8*cm, largura_util - 0.8*cm])
    t_passos.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, -1), VERDE_CLARO),
        ("TEXTCOLOR",     (0, 0), (0, -1), BRANCO),
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("ALIGN",         (0, 0), (0, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (1, 0), (1, -1), [CINZA_CLARO, BRANCO]),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (1, 0), (1, -1), 10),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.lightgrey),
    ]))
    story.append(t_passos)
    story.append(sp(0.4))

    # Decisao de escopo
    story.append(p("Por que so milho?", "SubTitle"))
    story.append(p(
        "Decisao de escopo do semestre. Fechar numa cultura permitiu coletar dataset de qualidade "
        "(foto de campo real com licenca aberta) e garantir fichas de manejo curadas. "
        "Hortalicas ficam fora -- a persona tambem planta alface, mas dados de pragas de folhosa "
        "nao tem volume suficiente no GBIF com licenca redistribuivel.",
        "BodyJust"
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 2. ARQUITETURA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(FaixaSecao("2. Arquitetura do Sistema", AZUL, "2"))
    story.append(sp(0.4))

    story.append(p("Fluxo completo de uma mensagem", "SubTitle"))

    fluxo = [
        ["Etapa", "Componente", "O que acontece"],
        ["① Recepcao",   "FastAPI / WhatsApp",   "Webhook recebe a foto. Responde 200 OK imediato (evita reenvio da Meta)"],
        ["② Porteiro",   "Claude Haiku (SIM/NaO)","Verifica se e planta ou inseto. Rejeita selfie, print, etc."],
        ["③ Qualidade",  "porteiro.py",            "Rejeita foto borrada (Laplaciano) ou muito pequena"],
        ["④ Classificacao","CNN MobileNetV3 ONNX", "Classifica em 4 classes. Devolve (classe, confianca 0-1)"],
        ["⑤ Roteamento", "roteador.py",            "≥80% → direto   50-79% → duvida   <50% → humano"],
        ["⑥ Conhecimento","kb.py (KB curada)",     "Busca a ficha da praga por filtro estruturado"],
        ["⑦ Redacao",    "Claude Haiku (texto)",   "LLM redige em ≤70 palavras a partir da ficha. Nao decide nada."],
        ["⑧ Entrega",    "Evolution API",          "Resposta no WhatsApp do produtor"],
    ]
    story.append(tabela(fluxo, [2.0*cm, 3.5*cm, largura_util - 5.5*cm]))
    story.append(sp(0.4))

    # Regra de ouro
    story.append(CaixaDestaque(
        "Regra de ouro: o LLM nunca decide a praga -- ele so redige o que a CNN + KB ja determinaram.",
        cor_fundo=colors.HexColor("#EAF4FB"), cor_borda=AZUL, cor_texto=AZUL
    ))
    story.append(sp(0.5))

    # Imagem do fluxo se existir
    img_fluxo = imagem_se_existe("06-como-funciona.png", largura=largura_util)
    story.append(img_fluxo)
    story.append(sp(0.2))

    story.append(p("Por que 200 OK imediato?", "SubTitle"))
    story.append(p(
        "A Meta reenvia o webhook se nao receber resposta em poucos segundos -- sem isso, "
        "o produtor receberia a mesma mensagem duas ou tres vezes. "
        "O diagnostico acontece de forma assincrona (ou sincrona rapida sem LLM), e a "
        "resposta e enviada de volta pela Evolution API.",
        "BodyJust"
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 3. DECISaO CENTRAL: CNN vs VLM
    # ══════════════════════════════════════════════════════════════════════════
    story.append(FaixaSecao("3. A Decisao Central: Como a IA Decide", VERDE_MEDIO, "3"))
    story.append(sp(0.4))

    story.append(p("Tres caminhos avaliados", "SubTitle"))
    comp = [
        ["Criterio",          "A. VLM direto\n(GPT-4o / Gemini)", "B. CNN propria", "C. Hibrido ✅\n(escolhido)"],
        ["Como funciona",     "Manda a foto p/ LLM multimodal", "Treina rede nas 4 classes", "CNN decide · RAG busca · LLM escreve"],
        ["Medir acuracia?",   "❌ Dificil (saida livre)",         "✅ Matriz de confusao",    "✅ Matriz de confusao"],
        ["Risco alucinacao",  "🔴 Alto",                          "✅ Nulo no diagnostico",   "✅ Controlado"],
        ["Custo por foto",    "💰 Pago sempre",                   "✅ ~R$ 0 (CPU)",            "✅ So texto vai ao LLM"],
        ["Defesa na banca",   "⚠️ Fraca: 'chamamos uma API'",     "✅ Boa",                    "🏆 Forte: engenharia real"],
    ]
    story.append(tabela(comp, [3.0*cm, 3.5*cm, 3.0*cm, largura_util-9.5*cm],
                        estilos_extra=[
                            ("BACKGROUND", (3, 0), (3, 0), VERDE_ESCURO),
                            ("BACKGROUND", (3, 1), (3, -1), colors.HexColor("#D8F3DC")),
                        ]))
    story.append(sp(0.5))

    story.append(CaixaDestaque(
        'Para a banca: "Separamos quem decide de quem escreve" -- a CNN e fechada e mensuravel, o LLM nao mente.',
        cor_fundo=VERDE_PALIDO, cor_borda=VERDE_CLARO, cor_texto=VERDE_ESCURO,
    ))

    story.append(sp(0.4))

    story.append(p("O Roteador de Confianca -- componente mais importante", "SubTitle"))
    story.append(p(
        "Os erros nao custam a mesma coisa. Dizer <i>'e vaquinha'</i> quando e lagarta faz o "
        "produtor gastar dinheiro com o produto errado e ainda perder a lavoura. "
        "Dizer <i>'nao sei'</i> custa apenas uma ida a Casa da Agricultura.",
        "BodyJust"
    ))
    story.append(sp(0.3))

    roteador_dados = [
        ["Confianca", "Rota", "O que acontece", "Cor"],
        ["≥ 80%",    "direto",  "Diagnostico direto com manejo completo",        "🟢"],
        ["50-79%",   "duvida",  "Pede outra foto, ja adianta o sinal da praga",  "🟡"],
        ["< 50%",    "humano",  "Encaminha para Casa da Agricultura / CATI",     "🔴"],
    ]
    story.append(tabela(roteador_dados, [2.0*cm, 2.0*cm, largura_util-5.0*cm, 1.0*cm],
                        estilos_extra=[
                            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#D8F3DC")),
                            ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#FFF3CD")),
                            ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#FFE5E5")),
                        ]))

    img_rot = imagem_se_existe("04-roteador-confianca.png", largura=largura_util)
    story.append(sp(0.3))
    story.append(img_rot)

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 4. DATASET E CLASSES
    # ══════════════════════════════════════════════════════════════════════════
    story.append(FaixaSecao("4. Dataset e Classes Treinadas", colors.HexColor("#4A4E69"), "4"))
    story.append(sp(0.4))

    story.append(p("As 4 classes", "SubTitle"))
    classes = [
        ["Classe",             "Especie",                 "Por que entra",                              "Fotos"],
        ["lagarta_cartucho",   "Spodoptera frugiperda",   "Praga nº 1 do milho; dano visual inconfundivel", "2.943"],
        ["lagarta_espiga",     "Helicoverpa zea",         "Decisiva para milho verde de feira",         "351"],
        ["vaquinha",           "Diabrotica speciosa",     "Especie BR; furo redondo na folha",          "458"],
        ["milho_sadio",        "--",                       "Classe negativa -- sem ela, planta boa vira praga","627"],
    ]
    story.append(tabela(classes, [3.5*cm, 3.5*cm, largura_util-8.5*cm, 1.5*cm]))
    story.append(sp(0.4))

    story.append(p("Por que essas fontes e nao outras?", "SubTitle"))
    fontes = [
        ["Fonte",         "Usada?", "Motivo"],
        ["GBIF (CC0/CC-BY)",              "✅ SIM",  "Fotos de campo com licenca redistribuivel; filtradas por lifeStage"],
        ["KaraAgro AI Maize (Harvard Dataverse)", "✅ SIM", "Bounding boxes de lagarta + 'healthy' para milho_sadio"],
        ["PlantVillage",  "❌ NaO", "So doenca foliar em fundo cinza uniforme -- nao representa campo real"],
        ["IP102",         "❌ NaO", "Especies nao coincidem; licenca nao autoriza redistribuicao"],
        ["iNaturalist API","⚠️ PARCIAL","lagarta_elasmo: so 17 fotos utilizaveis → classe descartada com dado"],
    ]
    story.append(tabela(fontes, [4.0*cm, 1.8*cm, largura_util-5.8*cm],
                        estilos_extra=[
                            ("TEXTCOLOR", (1, 2), (1, 3), VERMELHO),
                            ("TEXTCOLOR", (1, 1), (1, 1), VERDE_CLARO),
                        ]))
    story.append(sp(0.4))

    story.append(CaixaDestaque(
        "Cigarrinha-do-milho fica fora de proposito: 46 fotos publicas no mundo, sintoma 30 dias depois da infeccao.",
        cor_fundo=colors.HexColor("#FFF0F0"), cor_borda=VERMELHO, cor_texto=VERMELHO
    ))
    story.append(sp(0.4))

    story.append(p("Augmentation aplicado", "SubTitle"))
    story.append(p(
        "Rotacao, brilho/contraste, blur leve, recorte aleatorio -- simula exatamente "
        "a foto ruim que vai chegar do celular do Ze no meio da lavoura com sol forte.",
        "BodyJust"
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 5. MODELO
    # ══════════════════════════════════════════════════════════════════════════
    story.append(FaixaSecao("5. O Classificador (CNN)", colors.HexColor("#6B4226"), "5"))
    story.append(sp(0.4))

    story.append(p("Escolhas tecnicas do modelo", "SubTitle"))
    modelo_info = [
        ["Aspecto",          "Decisao",                     "Justificativa"],
        ["Arquitetura",      "MobileNetV3-Large",           "Leve, roda em CPU; projetado para mobile/edge"],
        ["Treinamento",      "Transfer learning (ImageNet)","Dataset pequeno (<5k fotos) -- sem pesos pre-treinados, nao converge bem"],
        ["Exportacao",       "ONNX (16,8 MB)",              "Independente de framework; sem instalar PyTorch em producao"],
        ["Inferencia",       "ONNX Runtime · CPU",          "~8 ms por foto; custo zero de hardware"],
        ["Pre-processamento","Resize 256 → CenterCrop 224", "Identico ao treino -- qualquer diferenca derruba acuracia"],
        ["Normalizacao",     "Media/desvio ImageNet",       "Pesos pre-treinados foram ajustados com esses valores"],
    ]
    story.append(tabela(modelo_info, [2.5*cm, 3.5*cm, largura_util-6.0*cm]))
    story.append(sp(0.4))

    story.append(p("Por que nao ResNet-50 ou EfficientNet?", "SubTitle"))
    story.append(p(
        "ResNet-50 leva ~200 ms em CPU e o modelo pesa ~90 MB. "
        "Com menos de 5.000 imagens de treino, o ganho de acuracia nao justifica o custo de operacao. "
        "MobileNetV3 foi projetado para o exato cenario deste projeto: inferencia em hardware barato.",
        "BodyJust"
    ))
    story.append(sp(0.3))

    img_perf = imagem_se_existe("02-desempenho-por-praga.png", largura=largura_util)
    story.append(img_perf)

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 6. RESULTADOS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(FaixaSecao("6. Resultados (710 fotos de teste)", VERDE_ESCURO, "6"))
    story.append(sp(0.4))

    story.append(p("Metricas principais", "SubTitle"))
    resultados = [
        ["Metrica",                                "Valor",   "Contexto"],
        ["Acuracia geral",                         "86,3%",   "Baseline (chutar sempre lagarta_cartucho) = 65,4%"],
        ["F1-macro",                               "81,4%",   "Metrica principal -- penaliza classes desbalanceadas"],
        ["Precisao (confianca ≥ 80%)",             "93,1%",   "Em 77,5% dos casos o bot respondeu diretamente"],
        ["Erros contidos pelo roteador",           "60,8%",   "Viraram 'manda outra foto' em vez de resposta errada"],
        ["Tempo de inferencia (CPU, ONNX)",        "~8 ms",   "Por foto -- sem GPU, sem nuvem"],
        ["Tamanho do modelo",                      "16,8 MB", "Carrega em <1 s, cabe em qualquer servidor"],
    ]
    story.append(tabela(resultados, [5.0*cm, 2.0*cm, largura_util-7.0*cm],
                        estilos_extra=[
                            ("TEXTCOLOR", (1, 1), (1, -1), VERDE_ESCURO),
                            ("FONTNAME",  (1, 1), (1, -1), "Helvetica-Bold"),
                            ("FONTSIZE",  (1, 1), (1, -1), 11),
                        ]))
    story.append(sp(0.4))

    story.append(CaixaDestaque(
        "Numero mais importante: 93,1% de precisao quando o bot ESCOLHEU responder -- nao a acuracia geral.",
        cor_fundo=VERDE_PALIDO, cor_borda=VERDE_CLARO, cor_texto=VERDE_ESCURO,
    ))
    story.append(sp(0.4))

    # Imagens de resultados
    img_res = imagem_se_existe("01-resultados.png", largura=largura_util)
    story.append(img_res)
    story.append(sp(0.3))

    img_mc = imagem_se_existe("03-matriz-confusao.png", largura=largura_util)
    story.append(img_mc)

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 7. BASE DE CONHECIMENTO E LLM
    # ══════════════════════════════════════════════════════════════════════════
    story.append(FaixaSecao("7. Base de Conhecimento e LLM", colors.HexColor("#5C4033"), "7"))
    story.append(sp(0.4))

    story.append(p("Como a KB funciona", "SubTitle"))
    story.append(p(
        "Quatro fichas curadas a mao em <code>kb/fichas-pragas-milho.md</code>, com fontes da "
        "<b>Embrapa</b>, <b>Epagri</b>, <b>Incaper</b> e <b>CATI</b>. "
        "Cada ficha tem campos fixos: nome popular, como reconhecer o dano, manejo do mais "
        "barato para o mais caro, quando encaminhar para tecnico.",
        "BodyJust"
    ))
    story.append(sp(0.3))
    story.append(p(
        "A busca e por <b>filtro estruturado</b> (praga_id), nao por embedding vetorial. "
        "A CNN ja decidiu a praga -- o RAG so precisa puxar a ficha certa. "
        "Busca vetorial so entra para perguntas livres futuras ("posso usar sabao?").",
        "BodyJust"
    ))
    story.append(sp(0.4))

    story.append(p("O papel do LLM (Claude Haiku)", "SubTitle"))
    llm_tabela = [
        ["O LLM FAZ",                                   "O LLM NaO FAZ"],
        ["Redige a resposta em portugues simples",       "Decide qual e a praga"],
        ["Respeita limite de 70 palavras",               "Inventa produto ou dose"],
        ["Lista manejo do mais barato ao mais caro",     "Escolhe informacao fora da ficha"],
        ["Porteiro de assunto (SIM/NaO antes da CNN)",  "Prescreve agrotoxico"],
    ]
    story.append(tabela(llm_tabela, [largura_util/2, largura_util/2],
                        estilos_extra=[
                            ("BACKGROUND", (0, 0), (0, 0), VERDE_ESCURO),
                            ("BACKGROUND", (1, 0), (1, 0), VERMELHO),
                            ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#D8F3DC")),
                            ("BACKGROUND", (1, 1), (1, -1), colors.HexColor("#FFE5E5")),
                        ]))
    story.append(sp(0.4))

    story.append(p("Fallback sem LLM", "SubTitle"))
    story.append(p(
        "Se a API do Claude cair (rede, chave invalida, rate limit), o <code>resposta.py</code> "
        "monta uma resposta mecanica direto da ficha. O produtor <b>sempre</b> recebe alguma "
        "resposta -- nunca um erro 500 silencioso.",
        "BodyJust"
    ))
    story.append(sp(0.3))

    story.append(p("Exemplo de resposta gerada", "SubTitle"))
    exemplo = (
        "🐛 Parece LAGARTA-DO-CARTUCHO no milho.\n\n"
        "O que ela faz: come o miolo da planta nova e seca o cartucho.\n\n"
        "O que fazer, comecando pelo mais barato:\n"
        "1. Olhe 10 plantas. Se mais de 2 tiverem o cartucho raspado, vale tratar.\n"
        "2. Bt (Bacillus thuringiensis) -- biologico, barato, aplicar no fim da tarde.\n"
        "3. Se estiver tomando conta, leve uma folha na Casa da Agricultura.\n\n"
        "⚠️ Isso e uma ajuda, nao e receita. Para veneno, precisa de receituario.\n\n"
        "Acertei? 👍 👎"
    )
    # Caixa simulando bolha de WhatsApp
    caixa_wp = Table(
        [[Paragraph(exemplo.replace("\n", "<br/>"), ES["BodyPT"])]],
        colWidths=[largura_util * 0.7]
    )
    caixa_wp.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#DCF8C6")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [8]),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#AAD7A0")),
    ]))
    story.append(Table(
        [[None, caixa_wp]],
        colWidths=[largura_util * 0.3, largura_util * 0.7]
    ))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 8. SEGURANcA, LGPD E eTICA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(FaixaSecao("8. Seguranca, LGPD e etica", colors.HexColor("#9B2226"), "8"))
    story.append(sp(0.4))

    etica = [
        ["Decisao",                         "Como esta implementado"],
        ["Nunca prescrever agrotoxico",      "O sistema recomenda manejo cultural/biologico livremente; "
                                             "para quimico, encaminha para a Casa da Agricultura. "
                                             "Receituario agronomico e exigencia legal no Brasil."],
        ["Errar para o lado do 'nao sei'",   "Falso positivo confiante e o pior resultado possivel: "
                                             "o produtor compra o produto errado e perde a lavoura mesmo assim. "
                                             "Dizer 'nao sei' custa apenas uma ida a CATI."],
        ["LGPD -- telefone",                  "Armazenado com hash. Nome so se ele quiser."],
        ["LGPD -- foto",                      "EXIF removido na ingestao (foto de campo tem geolocalizacao)."],
        ["LGPD -- consentimento",             "Primeira mensagem pede consentimento explicito. "
                                             "Termo assinado na visita ao produtor."],
        ["LGPD -- retencao",                  "Fotos por 12 meses. Comando 'APAGAR MEUS DADOS' implementado."],
    ]
    story.append(tabela(etica, [4.0*cm, largura_util-4.0*cm]))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 9. STACK TeCNICA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(FaixaSecao("9. Stack Tecnica", colors.HexColor("#023E8A"), "9"))
    story.append(sp(0.4))

    stack = [
        ["Camada",          "Tecnologia",                   "Por que"],
        ["Bot WhatsApp",    "Evolution API + FastAPI",       "Webhook HTTPS; roda com Docker; QR Code simples"],
        ["API",             "FastAPI (Python)",              "Mesma linguagem do modelo; async nativo; docs automaticas"],
        ["Classificador",   "MobileNetV3 → ONNX Runtime",   "Roda em CPU; ~8 ms; 16,8 MB; sem PyTorch em producao"],
        ["LLM",             "Claude Haiku 4.5 (Anthropic)", "Rapido, barato, instrucao seguida com precisao"],
        ["KB",              "Markdown parseado em Python",   "Corpus pequeno; filtro estruturado suficiente"],
        ["Treino",          "PyTorch + Transfer Learning",   "Colab gratuito; semana de treino; exporta ONNX"],
        ["Dados",           "GBIF + KaraAgro AI Maize",     "Fotos de campo com licenca aberta redistribuivel"],
        ["Infra",           "Docker Compose + ngrok",        "Reprodutibilidade para banca; HTTPS publico no dev"],
    ]
    story.append(tabela(stack, [3.0*cm, 3.5*cm, largura_util-6.5*cm]))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 10. PERGUNTAS DA BANCA
    # ══════════════════════════════════════════════════════════════════════════
    story.append(FaixaSecao("10. Perguntas Provaveis da Banca", VERMELHO, "10"))
    story.append(sp(0.4))

    story.append(CaixaDestaque(
        "Leia as perguntas em voz alta antes da apresentacao. A resposta deve sair em ate 30 segundos.",
        cor_fundo=colors.HexColor("#FFF0F0"), cor_borda=VERMELHO, cor_texto=VERMELHO
    ))
    story.append(sp(0.4))

    perguntas_respostas = [
        (
            "Por que nao usar o GPT-4o ou o Gemini direto na foto?",
            "Porque a saida seria texto livre -- sem como medir acuracia, sem matriz de confusao. "
            "Nossa CNN tem saida fechada (4 classes) e um numero de confianca mensuravel. "
            "O LLM so entra para redigir, onde nao decide nada e nao pode inventar praga."
        ),
        (
            "86% de acuracia e bom ou ruim?",
            "O baseline (chutar sempre a classe maior) daria 65,4%. O numero mais importante nao e "
            "a acuracia geral, e a precisao nas respostas que o bot escolheu dar: 93,1%. "
            "Os outros casos o roteador segurou e pediu outra foto."
        ),
        (
            "E em foto real de lavoura, nao de dataset?",
            "A queda e esperada -- literatura mede queda de ~94% (dataset limpo) para ~55% em campo. "
            "O roteador conservador compensa: prefere dizer 'nao sei' a arriscar diagnostico errado."
        ),
        (
            "Por que MobileNetV3 e nao ResNet-50 ou EfficientNet?",
            "ResNet-50 leva ~200 ms em CPU e pesa ~90 MB. Com menos de 5.000 imagens, o ganho "
            "de acuracia nao justifica o custo. MobileNetV3 foi projetado para inferencia em "
            "hardware barato -- exatamente o nosso cenario."
        ),
        (
            "O que e o roteador de confianca e por que 80% e 50%?",
            "Componente que decide se o bot responde, pede outra foto, ou encaminha para humano. "
            "Os limiares sao conservadores de proposito: falso positivo confiante faz o produtor "
            "comprar o produto errado e perder a lavoura. Os valores finais vem da curva "
            "precisao/revocacao no conjunto de validacao."
        ),
        (
            "Como garante que o LLM nao inventa produto?",
            "O system prompt proibe explicitamente inventar informacao fora do texto fornecido. "
            "O trecho que o LLM recebe tem no maximo ~300 palavras da ficha curada. "
            "Para quimico, o prompt instrui a dizer so 'existe produto registrado, exige receituario'."
        ),
        (
            "O que acontece se chegar foto de outra cultura (ex: alface)?",
            "O porteiro de assunto (Claude SIM/NaO) so verifica se ha planta ou inseto. "
            "Se passar, a CNN classifica -- mas a confianca vai ser baixa e o roteador encaminha "
            "para humano. O bot nunca diz 'e lagarta na alface'."
        ),
        (
            "Qual e o custo de operacao?",
            "Praticamente zero no MVP. CNN roda em CPU local (~R$ 0). "
            "O canal WhatsApp e gratuito para conversas de servico iniciadas pelo usuario "
            "dentro de 24 h (desde nov/2024). O LLM entra so no texto -- tokens baratos."
        ),
        (
            "Por que voces nao treinaram a cigarrinha-do-milho?",
            "e a praga de maior prejuizo do pais (R$ 33 bi/ano), mas tem 46 fotos publicas no mundo. "
            "O sintoma aparece 30 dias depois da infeccao e nao existe nivel de controle por imagem. "
            "e tratada por calendario, nao por foto -- entao fica fora do classificador de proposito."
        ),
        (
            "Por que a lagarta-elasmo foi descartada?",
            "O grupo procurou e encontrou so 17 fotos utilizaveis no iNaturalist -- abaixo de "
            "qualquer limiar de treino confiavel. A classe foi descartada com dado, nao por suposicao. "
            "Fica documentado e volta se aparecer mais volume."
        ),
    ]

    for i, (q, r) in enumerate(perguntas_respostas, 1):
        bloco = KeepTogether([
            Paragraph(f"P{i}. {q}", ES["Pergunta"]),
            Paragraph(r, ES["Resposta"]),
            linha_hr(colors.HexColor("#DDDDDD"), 0.5),
        ])
        story.append(bloco)

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # 11. RESUMO RaPIDO (cola de bolso)
    # ══════════════════════════════════════════════════════════════════════════
    story.append(FaixaSecao("11. Cola de Bolso -- Fatos para nao esquecer", AMARELO, ""))
    story.append(sp(0.4))

    cola = [
        ["🌱", "Persona",        "Ze do Sitio · 52 anos · Piedade/SP · 8 ha · WhatsApp como internet"],
        ["🧠", "Principio",      "CNN decide a praga · KB traz o manejo · LLM so escreve"],
        ["📊", "Classes",        "4: lagarta_cartucho (2.943) · lagarta_espiga (351) · vaquinha (458) · milho_sadio (627)"],
        ["🎯", "Acuracia",       "86,3% geral · 93,1% quando o bot escolheu responder · baseline 65,4%"],
        ["⚡", "Velocidade",     "~8 ms por foto · modelo ONNX de 16,8 MB · roda em CPU"],
        ["🔀", "Roteador",       "≥80% → direto · 50-79% → duvida · <50% → humano"],
        ["📚", "KB",             "4 fichas curadas · Embrapa + Epagri + CATI · busca por filtro, nao vetor"],
        ["🤖", "LLM",            "Claude Haiku · so redige · nunca decide · ≤70 palavras · sem dose de produto"],
        ["⚖️", "etica",          "Nunca prescreve agrotoxico · LGPD · hash de telefone · EXIF removido"],
        ["💰", "Custo",          "~R$ 0/mes no MVP · canal WhatsApp gratuito (servico, janela 24h)"],
        ["🚫", "Cigarrinha",     "Fora de proposito: 46 fotos no mundo · sintoma 30 dias depois"],
        ["🚫", "LLM direto",     "Nao: saida livre, sem acuracia mensuravel, risco de alucinacao"],
    ]
    t_cola = Table(cola, colWidths=[0.6*cm, 2.5*cm, largura_util - 3.1*cm])
    t_cola.setStyle(TableStyle([
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("FONTNAME",    (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTNAME",    (2, 0), (2, -1), "Helvetica"),
        ("TEXTCOLOR",   (1, 0), (1, -1), VERDE_ESCURO),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [CINZA_CLARO, BRANCO]),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (2, 0), (2, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.lightgrey),
    ]))
    story.append(t_cola)
    story.append(sp(0.5))

    story.append(CaixaDestaque(
        "Frase final se a banca perguntar 'vale a pena?': 'O Ze esta usando. Ele achou a lagarta.'",
        cor_fundo=VERDE_PALIDO, cor_borda=VERDE_CLARO, cor_texto=VERDE_ESCURO
    ))

    # ── Build ──────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
    print(f"✅ PDF gerado em: {OUT}")


if __name__ == "__main__":
    construir_pdf()
