"""Gera docs/05-guia-apresentacao.pdf — o passo a passo do dia da apresentação.

Para mudar o guia, edite os textos abaixo e rode:
    pip install reportlab
    python docs/gerar_guia_pdf.py

Usa as fontes do Windows (Arial e Consolas). Não coloque telefones completos,
e-mails ou chaves aqui: o PDF vai para o GitHub.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (CondPageBreak, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

SAIDA = Path(__file__).resolve().parent / "05-guia-apresentacao.pdf"

FONTES = "C:/Windows/Fonts/"
pdfmetrics.registerFont(TTFont("Arial", FONTES + "arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-B", FONTES + "arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Mono", FONTES + "consola.ttf"))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-B", italic="Arial", boldItalic="Arial-B")

VERDE = colors.HexColor("#2E6B30")
VERDE_CLARO = colors.HexColor("#E8F2E4")
CINZA = colors.HexColor("#F2F2F2")
TEXTO = colors.HexColor("#222222")
AMARELO = colors.HexColor("#FFF6D6")
AMARELO_BORDA = colors.HexColor("#E0B400")
VERMELHO_CLARO = colors.HexColor("#FBE9E7")
VERMELHO = colors.HexColor("#C0392B")

LARGURA = 17 * cm

st = {
    "titulo": ParagraphStyle("t", fontName="Arial-B", fontSize=21, leading=25, textColor=VERDE),
    "sub": ParagraphStyle("s", fontName="Arial", fontSize=10.5, leading=14, textColor=colors.HexColor("#555555")),
    "h1": ParagraphStyle("h1", fontName="Arial-B", fontSize=14, leading=18, textColor=colors.white),
    "h2": ParagraphStyle("h2", fontName="Arial-B", fontSize=11, leading=14, textColor=VERDE),
    "p": ParagraphStyle("p", fontName="Arial", fontSize=10, leading=13.5, textColor=TEXTO),
    "code": ParagraphStyle("c", fontName="Mono", fontSize=9, leading=12, textColor=colors.HexColor("#111111")),
    "cel": ParagraphStyle("cel", fontName="Arial", fontSize=9, leading=12, textColor=TEXTO),
    "celb": ParagraphStyle("celb", fontName="Arial-B", fontSize=9, leading=12, textColor=colors.white),
}

story = []


def m(t):
    """Trecho em fonte de código, dentro de um parágrafo."""
    return f"<font name='Mono'>{t}</font>"


def p(t):
    story.append(Paragraph(t, st["p"]))
    story.append(Spacer(1, 4))


def h2(t):
    story.append(CondPageBreak(4 * cm))
    story.append(Spacer(1, 4))
    story.append(Paragraph(t, st["h2"]))
    story.append(Spacer(1, 3))


def secao(t, nova_pagina=False):
    if nova_pagina:
        story.append(PageBreak())
    else:
        story.append(CondPageBreak(6 * cm))
        story.append(Spacer(1, 10))
    tb = Table([[Paragraph(t, st["h1"])]], colWidths=[LARGURA])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), VERDE),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.append(tb)
    story.append(Spacer(1, 6))


def code(*linhas):
    txt = "<br/>".join(l.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
                       for l in linhas)
    tb = Table([[Paragraph(txt, st["code"])]], colWidths=[LARGURA - 0.8 * cm])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CINZA), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ("LINEBEFORE", (0, 0), (0, -1), 2.5, VERDE)]))
    return tb


def passo(n, titulo, texto=None, *blocos):
    itens = [Paragraph(f"<b>{n}. {titulo}</b>", st["p"])]
    if texto:
        itens += [Spacer(1, 2), Paragraph(texto, st["p"])]
    for b in blocos:
        itens += [Spacer(1, 3), b if not isinstance(b, str) else Paragraph(b, st["p"])]
    tb = Table([[itens]], colWidths=[LARGURA])
    tb.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 2),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.append(KeepTogether(tb))


def caixa(t, cor=AMARELO, borda=AMARELO_BORDA):
    tb = Table([[Paragraph(t, st["p"])]], colWidths=[LARGURA])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), cor), ("BOX", (0, 0), (-1, -1), 0.8, borda),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story.append(Spacer(1, 3))
    story.append(KeepTogether(tb))
    story.append(Spacer(1, 6))


def tabela(cab, linhas, larguras):
    dados = [[Paragraph(c, st["celb"]) for c in cab]] + [[Paragraph(c, st["cel"]) for c in l] for l in linhas]
    tb = Table(dados, colWidths=larguras, repeatRows=1)
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), VERDE),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, VERDE_CLARO]),
                            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5),
                            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.append(tb)
    story.append(Spacer(1, 6))


def checklist(titulo, itens):
    linhas = [[Paragraph(f"<b>{titulo}</b>", st["h2"])]]
    linhas += [[Paragraph(f"{m('[&nbsp;&nbsp;]')}&nbsp; {i}", st["cel"])] for i in itens]
    tb = Table(linhas, colWidths=[LARGURA])
    tb.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, VERDE), ("BACKGROUND", (0, 0), (-1, 0), VERDE_CLARO),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story.append(KeepTogether(tb))
    story.append(Spacer(1, 8))


# =========================================================== capa + checklist
story.append(Paragraph("Doutor da Roça — Guia da apresentação", st["titulo"]))
story.append(Spacer(1, 4))
story.append(Paragraph("Tudo para ligar, demonstrar, explicar e desligar o bot de WhatsApp · UPX Facens 2026", st["sub"]))
story.append(Spacer(1, 12))

checklist("Antes do dia (uma vez só, de preferência 1 ou 2 dias antes)", [
    "Notebook com Git, Python 3.12+, Docker Desktop e ngrok instalados (Parte 2)",
    "Projeto baixado com git clone e bibliotecas instaladas (pip install)",
    f"Copiados do PC do Samuel: pasta {m('checkpoints')} (modelo) e arquivo {m('whatsapp\\.env')} (chave do Claude)",
    f"Rodado {m('docker compose up -d')} uma vez com internet boa (baixa ~1 GB de imagens)",
    "ngrok ligado na conta do Samuel (authtoken)",
    "Ensaio completo feito no notebook, com o QR Code escaneado pelo celular do bot (final 2008)",
    "4 ou 5 fotos boas salvas no celular que vai mandar (vaquinha, milho saudável, uma selfie, uma borrada)",
    "Vídeo de tela gravado com a demonstração funcionando (plano C, Parte 7)",
    "Bot DESLIGADO no PC do Samuel (só uma máquina pode estar ligada)",
])
checklist("No dia, antes de apresentar (10 minutos)", [
    "Notebook na tomada e com internet (Wi-Fi ou roteador do celular)",
    "Docker Desktop aberto, mostrando Engine running",
    "Janela 1: Evolution + webhook ligados (Parte 3, passo 2)",
    "Janela 2: ngrok ligado (Parte 3, passo 3)",
    f"Janela 3: {m('configurar.ps1')} mostrou WhatsApp CONECTADO (Parte 3, passo 4)",
    "Teste: mandar oi do celular de teste e receber resposta",
    "Celular do bot com internet e bateria (ele precisa estar ligado)",
])
checklist("Depois da apresentação", [
    "Ctrl+C no webhook e no ngrok, e docker compose down (Parte 5)",
])

# =========================================================== como funciona
secao("Parte 1 — Como o bot funciona (para explicar à banca)", nova_pagina=True)
p("O produtor tira uma foto da planta, manda no WhatsApp e recebe em segundos o nome da praga e o que fazer, "
  "começando pelas opções mais baratas. A ideia central do projeto é <b>separar quem decide de quem escreve</b>: "
  "a rede neural decide a praga (decisão fechada e medida), a base de conhecimento técnica traz o manejo e o "
  "Claude só reescreve em linguagem simples. Nenhum componente generativo escolhe a praga ou inventa produto.")

h2("O caminho de uma foto")
tabela(["Etapa", "O que faz", "Se falhar..."], [
    ["1. Porteiro de qualidade", "Mede nitidez e tamanho da foto (OpenCV)", "Pede outra foto, mais de perto"],
    ["2. Porteiro de assunto", "Claude responde só SIM/NÃO: tem planta ou inseto na foto?", "\"Não encontrei planta de milho nem inseto\""],
    ["3. Rede neural (CNN)", "MobileNetV3 escolhe entre 4 classes: lagarta-do-cartucho, lagarta-da-espiga, vaquinha, milho saudável", "—"],
    ["4. Roteador de confiança", "≥ 80%: afirma · 50–80%: \"pode ser X\", pede outra foto · < 50%: encaminha à Casa da Agricultura", "Prefere dizer \"não sei\" a errar"],
    ["5. Base de conhecimento", "Busca a ficha técnica da praga (Embrapa, Epagri, CATI)", "—"],
    ["6. Claude (redação)", "Reescreve a ficha em linguagem simples, ~90 palavras", "Usa uma resposta de reserva tirada da ficha"],
    ["7. Rodapé fixo", "Aviso legal (não é receita) + \"Acertei?\" — sempre por código, nunca pelo LLM", "—"],
], [3.8 * cm, 8.4 * cm, 4.8 * cm])

h2("Números do modelo (710 fotos de teste que o treino nunca viu)")
tabela(["Métrica", "Valor", "Como explicar"], [
    ["Acurácia geral", "<b>86,3%</b>", "Chutar sempre a praga mais comum daria 65,4%"],
    ["F1-macro", "<b>81,4%</b>", "Métrica principal: não premia só acertar a classe com mais fotos"],
    ["Respostas diretas (≥ 80%)", "77,5% das fotos, <b>93,1%</b> de acerto", "Quando o bot afirma, quase sempre acerta"],
    ["Erros segurados pelo roteador", "<b>60,8%</b>", "Viram \"manda outra foto\" em vez de recomendação errada"],
    ["Vaquinha / milho saudável", "100% de acerto nas respostas diretas", "Melhores classes para a demonstração"],
    ["Lagarta-da-espiga", "F1 69,7%", "Classe mais fraca: menos fotos públicas (58 no teste)"],
    ["Velocidade", "~8 ms por foto · modelo de 16,8 MB", "Roda em CPU comum; o tempo total vem do Claude (~3 s)"],
], [4.6 * cm, 5.2 * cm, 7.2 * cm])
p(f"Para gerar de novo estas tabelas e os gráficos (matriz de confusão, curva de limiar): "
  f"{m('python scripts/06_relatorio_validacao.py')}.")

h2("Decisões de projeto que valem comentar")
p("• <b>Cigarrinha-do-milho fica fora do classificador</b> de propósito: é a praga de maior prejuízo do país, mas há só "
  "46 fotos públicas no mundo e o sintoma aparece 30 dias depois da infecção.<br/>"
  "• <b>Nunca prescreve agrotóxico</b>: receituário agronômico é exigência legal. Recomenda manejo cultural e biológico "
  "e encaminha o químico para a Casa da Agricultura.<br/>"
  "• <b>Errar para o lado do \"não sei\"</b>: dizer a praga errada faz o produtor gastar dinheiro e perder a lavoura; "
  "dizer \"não sei\" custa só uma ida à Casa da Agricultura.<br/>"
  "• <b>Evolution API</b> conecta o número como aparelho vinculado (QR Code). A API oficial da Meta foi testada e "
  "descartada: a conta de teste não podia enviar mensagens para o Brasil (erro 130497).")

h2("As 4 peças que precisam estar ligadas")
tabela(["Peça", "O que faz", "Como liga"], [
    ["<b>Docker (Evolution API)</b>", "Conecta no WhatsApp do bot, como um WhatsApp Web", f"Docker Desktop + {m('docker compose up -d')}"],
    ["<b>Webhook (Python)</b>", "Recebe a foto, roda o diagnóstico e responde", m("python -m uvicorn main:app --port 8001")],
    ["<b>ngrok</b>", "Cria um endereço na internet que aponta para o webhook", m("ngrok http 8001")],
    ["<b>Celular do bot</b>", "Número de final 2008, conectado como aparelho vinculado", "QR Code (só na primeira vez em cada computador)"],
], [4 * cm, 6.6 * cm, 6.4 * cm])

# =========================================================== preparar notebook
secao("Parte 2 — Preparar o notebook (antes do dia, uma vez só)")

passo(1, "Instalar os programas",
      "<b>Git</b> (git-scm.com) · <b>Python 3.12 ou mais novo</b> (python.org — na instalação, marque "
      "<b>Add python.exe to PATH</b>) · <b>Docker Desktop</b> (docker.com — pede para ativar o WSL2 e reiniciar) · "
      "<b>ngrok</b>, pelo PowerShell:",
      code("winget install ngrok.ngrok"))
caixa("Se o Docker Desktop disser <i>Virtualization support not detected</i>, a virtualização está desligada na BIOS. "
      "Confira em Gerenciador de Tarefas > Desempenho > CPU > Virtualização. Se estiver desabilitada, ative "
      "Intel VT-x / AMD SVM na BIOS do notebook.")

passo(2, "Baixar o projeto",
      "Abra o PowerShell na pasta onde quer guardar (ex.: Área de Trabalho) e rode:",
      code("git clone https://github.com/UPX6-FACENS/AgroBot.git"))

passo(3, "Copiar os arquivos que NÃO estão no GitHub",
      "Por segurança e tamanho, eles ficam fora do GitHub. Copie da pasta "
      f"{m('UPx6-ProjetoChatBotAgricultura')} no PC do Samuel, por pendrive ou Google Drive:"
      f"<br/>• {m('checkpoints\\modelo.onnx')} e {m('checkpoints\\classes.json')} -> para {m('AgroBot\\checkpoints\\')} "
      "(crie a pasta)"
      f"<br/>• {m('whatsapp\\.env')} -> para {m('AgroBot\\whatsapp\\.env')}"
      "<br/>Sem o modelo o bot não diagnostica; sem o .env ele nem liga.")
caixa(f"O {m('.env')} tem a chave paga do Claude e a senha da Evolution. Não mande em grupo nem poste em lugar público. "
      "Se vazar, apague a chave em console.anthropic.com/settings/keys e crie outra.",
      cor=VERMELHO_CLARO, borda=VERMELHO)

passo(4, "Instalar as bibliotecas do Python",
      "No PowerShell:",
      code("cd AgroBot\\whatsapp",
           "python -m venv venv",
           "venv\\Scripts\\activate",
           "pip install -r requirements.txt"),
      f"Se o PowerShell reclamar de <i>execução de scripts desabilitada</i>, rode antes "
      f"{m('Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass')} e repita o activate.")

passo(5, "Baixar as imagens do Docker",
      f"Com o Docker Desktop aberto e internet boa, dentro de {m('AgroBot\\whatsapp')}:",
      code("docker compose up -d"),
      "A primeira vez baixa ~1 GB. Faça antes do dia para não depender da internet da faculdade.")

passo(6, "Ligar o ngrok na conta",
      "Entre em dashboard.ngrok.com com a conta do Samuel, copie o token em <i>Your Authtoken</i> e rode:",
      code("ngrok config add-authtoken COLE_O_TOKEN_AQUI"),
      f"Com a mesma conta, o endereço é sempre {m('https://thumping-squad-qualifier.ngrok-free.dev')}. "
      "A conta grátis só deixa o ngrok aberto em <b>um computador por vez</b>.")

passo(7, "Fazer o ensaio completo",
      "Siga a Parte 3 inteira no notebook, incluindo escanear o QR Code com o celular do bot (final 2008). "
      "Depois de escanear uma vez, a conexão fica salva no Docker do notebook: no dia é só ligar.")

passo(8, "Preparar as fotos e o vídeo reserva",
      "Salve no celular de teste 4 ou 5 fotos nítidas (no PC do Samuel: "
      f"{m('dados\\split\\teste\\vaquinha')} e {m('dados\\split\\teste\\milho_sadio')}), mais uma selfie e "
      "uma foto borrada. Grave a tela do celular fazendo a demonstração inteira: se algo falhar no dia, "
      "vocês mostram o vídeo.")

# =========================================================== ligar
secao("Parte 3 — Ligar o bot (no dia)")
caixa("<b>Antes de tudo:</b> o notebook precisa de internet (ngrok e Claude). Se o Wi-Fi da faculdade bloquear, "
      "use o roteador do celular. Confira que o bot NÃO está ligado em outro computador.")

passo(1, "Abrir o Docker Desktop",
      "Pelo menu Iniciar. Espere aparecer <b>Engine running</b> (verde) no canto inferior — uns 30 segundos.")

passo(2, "Janela 1 — subir a Evolution e o webhook",
      "Abra um PowerShell e rode. Deixe esta janela aberta a apresentação inteira:",
      code("cd AgroBot\\whatsapp",
           "docker compose up -d",
           "venv\\Scripts\\activate",
           "python -m uvicorn main:app --port 8001"),
      f"Confira abrindo {m('http://localhost:8001')} no navegador: deve aparecer <i>AgroBot webhook online</i>.")

passo(3, "Janela 2 — ligar o ngrok",
      "Abra outro PowerShell e rode (deixe aberta também):",
      code("ngrok http 8001"),
      f"Confira se a linha <b>Forwarding</b> mostra {m('https://thumping-squad-qualifier.ngrok-free.dev')}.")

passo(4, "Janela 3 — apontar a Evolution para o ngrok",
      "Abra um terceiro PowerShell e rode:",
      code("cd AgroBot\\whatsapp",
           "powershell -ExecutionPolicy Bypass -File .\\configurar.ps1 -NgrokUrl https://thumping-squad-qualifier.ngrok-free.dev"),
      "O script cria a instância se precisar, configura o webhook e termina com:"
      "<br/>• <b>WhatsApp CONECTADO</b> -> pronto."
      f"<br/>• <b>WhatsApp ainda NAO conectado</b> -> abra {m('http://localhost:8080/manager')}, entre com a URL e a "
      "chave que o script mostrou, clique na instância <b>agrobot</b> e escaneie o QR Code com o celular do bot "
      "(WhatsApp > Aparelhos conectados > Conectar um aparelho). O QR vale ~40 segundos; se expirar, gere outro.")

passo(5, "Teste rápido",
      "Do celular de teste (final 8639), mande <b>oi</b> para o número do bot (final 2008). Em poucos segundos ele "
      "responde pedindo uma foto. Respondeu? Está tudo pronto.")

h2("O que aparece na janela 1 (dá para mostrar à banca)")
code_log = code("mensagem recebida | tipo=imageMessage | de=***8639 | fromMe=False",
                "classificacao: vaquinha (100%) | rota=direto",
                "foto fora do assunto (nao e' milho nem inseto)",
                "Feedback registrado: positivo")
story.append(code_log)
story.append(Spacer(1, 4))
p("O número aparece mascarado e o texto das mensagens não é gravado no log, por privacidade.")

# =========================================================== roteiro
secao("Parte 4 — Roteiro sugerido da demonstração")
tabela(["Mande", "O bot responde", "O que isso mostra"], [
    ["\"oi\"", "Pede uma foto da praga", "Bot orienta o produtor"],
    ["Foto nítida de vaquinha", "Nome da praga, o que ela faz, manejo do mais barato ao mais caro, aviso legal e \"Acertei?\"",
     "CNN decide a praga; o Claude só reescreve a ficha técnica"],
    ["Foto de milho saudável", "\"Não vi sinal de praga\"", "Classe negativa: o bot também diz quando está tudo bem"],
    ["Selfie ou print de tela", "\"Não encontrei planta de milho nem inseto\"", "Porteiro de assunto: não inventa praga"],
    ["Foto borrada ou muito pequena", "Pede outra foto, mais de perto", "Porteiro de qualidade"],
    ["Polegar para cima (digitado como mensagem) depois de um diagnóstico", "\"Obrigado pelo retorno!\"",
     f"Feedback gravado em {m('whatsapp\\feedback.jsonl')} para melhorar o modelo"],
], [4.2 * cm, 6.6 * cm, 6.2 * cm])
p("Se o bot responder <i>\"Pode ser X, mas não tenho certeza\"</i>, não é erro: entre 50% e 80% de confiança ele "
  "prefere pedir outra foto a arriscar. É um ótimo momento para explicar o roteador de confiança.")

# =========================================================== desligar
secao("Parte 5 — Desligar (para não gastar a API do Claude)")
passo(1, "Parar o webhook e o ngrok", "Nas janelas 1 e 2, aperte <b>Ctrl+C</b>.")
passo(2, "Parar a Evolution", f"Em {m('AgroBot\\whatsapp')}:", code("docker compose down"))
p("Pronto: nada mais responde e nada é cobrado. A conexão com o WhatsApp fica salva; na próxima vez não precisa de "
  "QR Code. Para conferir que desligou: " + m("docker ps") + " não deve listar nada com <i>agrobot</i>.")
caixa("Para desconectar de vez: no celular do bot (final 2008), WhatsApp > Aparelhos conectados > remover o aparelho.",
      cor=VERDE_CLARO, borda=VERDE)

# =========================================================== ajustes
secao("Parte 6 — Ajustes que podem ser necessários")
h2("Deixar outra pessoa (ex.: alguém da banca) conversar com o bot")
p(f"Edite {m('whatsapp\\.env')} e acrescente o número em {m('ALLOWED_NUMBERS')}, separado por vírgula, no formato "
  "55 + DDD + número, sem espaços. Coloque <b>as duas formas</b> (com e sem o 9 depois do DDD), porque o WhatsApp às "
  "vezes identifica o número sem o 9:")
story.append(code("ALLOWED_NUMBERS=55159XXXXXXXX,5515XXXXXXXX,..."))
story.append(Spacer(1, 4))
p("Depois <b>reinicie o webhook</b> (Ctrl+C na janela 1 e rode o uvicorn de novo). Ele só lê o .env ao ligar.")

h2("Chave e créditos do Claude")
p("A chave fica em " + m("ANTHROPIC_API_KEY") + " no .env. Ela é criada em <b>console.anthropic.com/settings/keys</b> "
  "e o saldo fica em <b>console.anthropic.com/settings/billing</b>. Cada foto custa bem menos de 1 centavo de dólar "
  "(Claude Haiku 4.5), então o crédito atual sobra para a apresentação. Se o crédito acabar, o bot continua "
  "funcionando com a resposta de reserva (mais \"seca\") e o porteiro de assunto deixa todas as fotos passarem.")

h2("O endereço do ngrok mudou")
p(f"Rode o {m('configurar.ps1')} de novo com o endereço novo (Parte 3, passo 4). Só isso.")

# =========================================================== planos B e C
secao("Parte 7 — Se o notebook falhar: planos B e C")
p("<b>Plano B — PC do Samuel.</b> Lá já está tudo instalado e o WhatsApp já foi conectado. Abra o Docker Desktop e "
  f"siga a Parte 3 dentro da pasta {m('UPx6-ProjetoChatBotAgricultura\\whatsapp')} (no PC não precisa do "
  f"{m('venv\\Scripts\\activate')}: as bibliotecas estão instaladas direto no Python). Antes, desligue o notebook "
  "(Parte 5) para não responder em dobro.")
p("<b>Plano C — vídeo.</b> Mostre o vídeo de tela gravado no ensaio (Parte 2, passo 8) e explique a arquitetura "
  "com a Parte 1 deste guia.")

# =========================================================== cuidados
secao("Parte 8 — Cuidados (as \"pegadinhas\")")
tabela(["Cuidado", "Por quê"], [
    ["Só uma máquina com o bot ligado", "Duas Evolutions no mesmo número = toda resposta sai em dobro"],
    ["Quem é dono do número do bot não deve digitar na conversa com um número liberado durante a demo",
     "O bot também processa mensagens que o próprio dono digita nessas conversas e responderia junto"],
    ["Feedback precisa ser digitado", "Reagir com emoji em cima da mensagem é ignorado; mande o polegar como mensagem"],
    ["Mensagens com mais de 2 minutos são ignoradas", "Evita responder o acúmulo de quando o bot estava desligado — "
     "por isso o relógio do notebook precisa estar certo"],
    ["Grupos são sempre ignorados", "O bot só responde conversa individual com número liberado"],
    ["Celular do bot ligado e com internet", "A Evolution funciona como WhatsApp Web: precisa do celular vinculado ativo"],
    ["Evolution não é a API oficial do WhatsApp", "Serve para projeto acadêmico e demonstração; use um número que "
     "possa correr um pequeno risco de bloqueio"],
], [6.2 * cm, 10.8 * cm])

# =========================================================== problemas
secao("Parte 9 — Se algo der errado")
tabela(["O que acontece", "Causa provável e solução"], [
    ["O bot não responde nada",
     "1) Janela 1 ou 2 foi fechada: ligue de novo. 2) O endereço do ngrok mudou: rode o configurar.ps1 de novo. "
     "3) Quem mandou não está no ALLOWED_NUMBERS (Parte 6). 4) O celular do bot está sem internet."],
    ["Bot responde duas vezes", f"A Evolution está ligada em dois computadores. Rode {m('docker compose down')} no outro."],
    ["Erro com <i>dockerDesktopLinuxEngine</i> ou <i>docker não reconhecido</i>",
     "O Docker Desktop não está aberto. Abra e espere o <b>Engine running</b>."],
    ["ngrok diz <i>endpoint already online</i> (ERR_NGROK_334)", "O ngrok está aberto em outro computador. Feche lá."],
    ["Instância presa em <i>connecting</i> (laranja)", "O QR Code expirou. Gere outro no /manager e escaneie na hora."],
    ["<i>No module named ...</i> ao ligar o webhook", f"O ambiente do Python não está ativo: rode {m('venv\\Scripts\\activate')}."],
    ["<i>401 Unauthorized</i> no configurar.ps1", f"A chave da Evolution mudou no .env. Rode {m('docker compose up -d')} de novo."],
    ["Janela 1 mostra <i>405 Method Not Allowed</i>", "O webhook foi configurado sem /webhook no final. Rode o configurar.ps1."],
    ["Bot ignora mensagens novas", "Relógio do notebook adiantado mais de 2 minutos. Sincronize a hora do Windows."],
    ["Logo ao ligar, a janela 1 enche de eventos", "É o acúmulo de mensagens de quando estava desligado; o bot "
     f"descarta as antigas. Se demorar: {m('docker compose restart evolution-api')}."],
    ["Resposta curta, sem texto bem escrito", "O Claude não respondeu (sem internet ou sem crédito). O bot continua "
     "com a resposta de reserva."],
    ["Uma praga de verdade foi recusada como \"fora do assunto\"",
     "Mande outra foto mais de perto. Se acontecer muito, a regra fica em PROMPT_ASSUNTO em pipeline\\llm.py."],
], [5.2 * cm, 11.8 * cm])

# =========================================================== anexo
secao("Anexo — Onde fica cada coisa no repositório")
tabela(["Pasta / arquivo", "Conteúdo"], [
    [m("whatsapp/"), "O bot do WhatsApp que roda na apresentação (webhook, filtros, configurar.ps1, docker-compose)"],
    [m("pipeline/"), "Diagnóstico: porteiros, CNN, roteador, base de conhecimento e Claude"],
    [m("kb/fichas-pragas-milho.md"), "Fichas técnicas das pragas (fonte do texto das respostas)"],
    [m("scripts/01 a 06"), "Montar o dataset, treinar o modelo e gerar o relatório de validação"],
    [m("docs/"), "Persona, arquitetura, panorama das pragas, guia do dataset e este guia"],
    [m("api/"), "Alternativa com Twilio/Meta (não usada na demonstração)"],
    [m("checkpoints/") + " (fora do Git)", "Modelo treinado: modelo.onnx e classes.json"],
    [m("whatsapp/.env") + " (fora do Git)", "Chave do Claude, senha da Evolution e números liberados"],
    [m("dados/") + " (fora do Git)", "Fotos do dataset; só existem no PC do Samuel"],
], [5.4 * cm, 11.6 * cm])
p(f"Para editar este guia: mude os textos em {m('docs/gerar_guia_pdf.py')} e rode {m('python docs/gerar_guia_pdf.py')}.")


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Arial", 8)
    canvas.setFillColor(colors.HexColor("#888888"))
    canvas.drawString(2 * cm, 1.2 * cm, "Doutor da Roça · Guia da apresentação")
    canvas.drawRightString(19 * cm, 1.2 * cm, f"página {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(str(SAIDA), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                        bottomMargin=2 * cm, title="Doutor da Roça — Guia da apresentação", author="Grupo UPX Facens")
doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
print(f"PDF gerado: {SAIDA}")
