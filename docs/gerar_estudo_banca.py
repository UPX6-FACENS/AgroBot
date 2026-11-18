"""Gera o PDF interativo de estudo para a banca do AgroBot.

Execute (da raiz do repo):  python docs/gerar_estudo_banca.py
Saida:                       docs/06-estudo-banca.pdf

Formato "slide" 16:9 para ler na tela. Tudo e' clicavel: indice, mapa do
fluxo (cada caixa leva a sua etapa), barra de etapas, perguntas (cada uma
leva a sua resposta) e a barra de navegacao no rodape de toda pagina.

Os numeros vem de scripts/06_relatorio_validacao.py (conjunto de TESTE).
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import Paragraph

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "docs" / "06-estudo-banca.pdf"
IMG_MATRIZ = RAIZ / "checkpoints" / "relatorio" / "matriz_confusao_teste.png"
IMG_LIMIAR = RAIZ / "checkpoints" / "relatorio" / "curva_limiar.png"

W, H = 960, 540
M = 34  # margem lateral

# ── Fontes ───────────────────────────────────────────────────────────────────
FONTES = Path("C:/Windows/Fonts")
for nome, arq in [("UI", "segoeui.ttf"), ("UIB", "segoeuib.ttf"), ("UII", "segoeuii.ttf"),
                  ("UISB", "seguisb.ttf"), ("UIL", "segoeuil.ttf"), ("SYM", "seguisym.ttf"),
                  ("MONO", "consola.ttf")]:
    pdfmetrics.registerFont(TTFont(nome, str(FONTES / arq)))
addMapping("UI", 0, 0, "UI"); addMapping("UI", 1, 0, "UIB")
addMapping("UI", 0, 1, "UII"); addMapping("UI", 1, 1, "UIB")

# ── Paleta ───────────────────────────────────────────────────────────────────
C = colors.HexColor
FUNDO = C("#F6F4EE"); TINTA = C("#22302A"); SUAVE = C("#5E6B64"); LINHA = C("#DAD6CB")
VERDE = C("#1B4332"); VERDE2 = C("#2D6A4F"); VERDE3 = C("#52B788"); VERDE4 = C("#D8F3DC")
MILHO = C("#F2B705"); MILHO_CLARO = C("#FFF3C4")
VERMELHO = C("#C0392B"); VERMELHO_CLARO = C("#FBE3E0")
BRANCO = colors.white

ZONAS = {
    "canal":    ("Canal WhatsApp", C("#2A6F97"), C("#DCEBF5")),
    "filtro":   ("Filtros",        C("#C77D0A"), C("#FBEBD0")),
    "ia":       ("Diagnóstico",    C("#2D6A4F"), C("#D8F3DC")),
    "resposta": ("Resposta",       C("#6D4C7D"), C("#EDE3F2")),
}

CATS = {
    "visao":  ("Visão geral",          C("#2A6F97")),
    "modelo": ("IA / Modelo",          C("#2D6A4F")),
    "dados":  ("Dados",                C("#8A6D1F")),
    "llm":    ("LLM e conhecimento",   C("#6D4C7D")),
    "arq":    ("Arquitetura",          C("#C77D0A")),
    "etica":  ("Segurança e ética",    C("#C0392B")),
    "futuro": ("Limitações e futuro",  C("#5E6B64")),
}


def esc(t: str) -> str:
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # **negrito**  e  `codigo`
    partes = t.split("**")
    t = "".join(p if i % 2 == 0 else f"<b>{p}</b>" for i, p in enumerate(partes))
    partes = t.split("`")
    t = "".join(p if i % 2 == 0 else f'<font name="MONO" size="-1">{p}</font>' for i, p in enumerate(partes))
    return t


def estilo(size=10, font="UI", cor=TINTA, align=TA_LEFT, lead=1.32):
    return ParagraphStyle("s", fontName=font, fontSize=size, leading=size * lead,
                          textColor=cor, alignment=align)


# ══════════════════════════════════════════════════════════════════════════════
# CONTEUDO
# ══════════════════════════════════════════════════════════════════════════════

STEPS = [
    dict(n=1, z="canal", t="O produtor manda a foto",
         f="O produtor fotografa a folha, a espiga ou o inseto e envia no WhatsApp do AgroBot, como mandaria para um conhecido.",
         a=["Nenhum aplicativo novo para instalar.",
            "Se ele manda **texto**, o bot responde pedindo uma foto.",
            "**Áudio, vídeo, figurinha** ou documento: o bot explica que só entende foto da planta.",
            "Se ele responde com o **polegar** (positivo/negativo), vira feedback do último diagnóstico."],
         p="O público (persona João, 54 anos, ~8 ha em Sorocaba) já usa WhatsApp todo dia. Barreira de entrada zero vale mais que qualquer interface bonita.",
         c=["whatsapp/handlers.py → process_message()", "whatsapp/config.py → TIPOS_SEM_SUPORTE"],
         num=("0", "aplicativos para instalar"), qs=["q1", "q2"]),
    dict(n=2, z="canal", t="Evolution API recebe a mensagem",
         f="A Evolution API, rodando em Docker no notebook, fica conectada ao número do bot (por QR Code, como o WhatsApp Web) e transforma cada mensagem em um evento HTTP.",
         a=["Sobe com `docker compose`: Evolution (porta 8080) + Postgres + Redis, que guardam a sessão.",
            "Cada mensagem gera um evento **MESSAGES_UPSERT** em JSON.",
            "A Evolution faz um **POST** desse JSON no endereço do nosso webhook.",
            "Mensagens de grupo são ignoradas já na instância (`groupsIgnore`)."],
         p="A API oficial da Meta bloqueou o envio para números do Brasil na conta de teste (erro 130497). A Evolution é gratuita, open source e ideal para protótipo.",
         c=["whatsapp/docker-compose.yml", "whatsapp/configurar.ps1 (cria a instância e aponta o webhook)"],
         num=("3", "containers Docker"), qs=["q25", "q26"]),
    dict(n=3, z="canal", t="ngrok: o túnel até o notebook",
         f="O ngrok dá um endereço público HTTPS fixo que encaminha tudo para a porta 8001 do notebook, onde roda o nosso servidor Python.",
         a=["Domínio fixo da conta ngrok → `localhost:8001`.",
            "A Evolution manda os eventos para `https://<domínio>/webhook`.",
            "O painel `localhost:4040` mostra cada requisição: ótimo para depurar ao vivo.",
            "`ligar.bat` sobe Docker → bot → ngrok → configura o webhook, em sequência."],
         p="Permite rodar o sistema inteiro num notebook comum, sem servidor e sem configurar rede, já no formato de produção (webhook público com HTTPS).",
         c=["whatsapp/ligar.bat", "whatsapp/desligar.bat"],
         num=("8001", "porta do webhook"), qs=["q27"]),
    dict(n=4, z="canal", t="Webhook FastAPI filtra o evento",
         f="O servidor em Python (FastAPI) recebe o POST em /webhook e decide, na hora, se aquele evento merece ser processado.",
         a=["Mais de **120 s** de idade → descarta (fila antiga depois do bot ficar offline).",
            "Mensagem enviada **pelo próprio bot** → descarta (não responde a si mesmo).",
            "**Grupo** (@g.us) ou número fora da lista permitida → ignora.",
            "**ID já visto** → duplicata, ignora."],
         p="Sem esses filtros o bot responderia milhares de mensagens antigas de grupo ou entraria em loop respondendo a si mesmo. Isso aconteceu de verdade nos testes.",
         c=["whatsapp/main.py → receive_webhook()", "whatsapp/handlers.py → check_event()"],
         num=("120 s", "idade máxima de um evento"), qs=["q29"]),
    dict(n=5, z="canal", t="Responde já, processa em segundo plano",
         f="O webhook devolve 200 OK imediatamente e agenda o processamento da foto numa tarefa em segundo plano (BackgroundTasks).",
         a=["Resposta HTTP instantânea: a Evolution não reenvia nem trava.",
            "Em segundo plano: baixa a foto em base64 pela Evolution (`getBase64FromMediaMessage`).",
            "Decodifica a imagem (Pillow) **em memória**: a foto não é salva em disco.",
            "Chama `analisar_foto()`, a ponte para o pipeline de IA."],
         p="As chamadas ao Claude levam ~3 s; segurar o webhook esse tempo arrisca timeout e reenvio. Limitação conhecida: BackgroundTasks não é fila durável; em produção, Redis/RQ.",
         c=["whatsapp/main.py (background_tasks.add_task)", "whatsapp/evolution.py → get_image_base64()",
            "whatsapp/analise.py → analisar_foto()"],
         num=("~3 s", "por chamada ao LLM"), qs=["q28", "q31"]),
    dict(n=6, z="filtro", t="Porteiro de qualidade",
         f="Antes de gastar IA, o código confere se a foto dá para analisar: nem pequena demais, nem borrada.",
         a=["Menor lado **< 100 px** → \"foto muito pequena, manda de novo mais perto\".",
            "Nitidez = **variância do Laplaciano** (mede a força das bordas).",
            "Calculada em **16 blocos (4×4)**; vale o MELHOR bloco.",
            "Abaixo de **60** → \"foto embaçada, tenta com a mão firme\"."],
         p="Foto macro de inseto tem o bicho nítido e o fundo desfocado de propósito. Medir a imagem inteira reprovava fotos ótimas; medir o melhor bloco resolve. No teste, 99,9% das fotos boas passam.",
         c=["pipeline/porteiro.py → verificar()", "scripts/02_limpar_duplicatas.py (mesma lógica)"],
         num=("60", "limiar de nitidez"), qs=["q17"]),
    dict(n=7, z="filtro", t="Porteiro de assunto (Claude)",
         f="O Claude Haiku olha a foto e responde uma única palavra: SIM (tem planta ou inseto) ou NÃO (print, selfie, documento...).",
         a=["Foto reduzida para 768 px (menos tokens, mais rápido).",
            "O prompt pede só \"SIM\" ou \"NAO\"; `max_tokens = 5`.",
            "Regra explícita: **na dúvida, responda SIM**.",
            "Se a API falhar, a foto passa (**fail-open**): o roteador ainda protege."],
         p="A CNN SEMPRE escolhe uma das 4 classes: uma selfie virava \"vaquinha com alta confiança\". Aqui o Claude não escolhe praga, é só um filtro binário genérico.",
         c=["pipeline/llm.py → foto_e_do_assunto()", "pipeline/llm.py → PROMPT_ASSUNTO"],
         num=("1", "palavra de resposta"), qs=["q12", "q20"]),
    dict(n=8, z="ia", t="CNN classifica a praga",
         f="A MobileNetV3-Large (exportada em ONNX) recebe a foto e devolve uma probabilidade para cada uma das 4 classes. É ELA QUEM DECIDE a praga.",
         a=["Pré-processo idêntico ao do treino: redimensiona para 256, recorta o centro **224×224**, normaliza com média/desvio da ImageNet.",
            "Rede → 4 números (logits) → **softmax** → probabilidades que somam 100%.",
            "Sai a classe vencedora + a confiança (ex.: lagarta_cartucho, 0,94).",
            "Classes: lagarta_cartucho · lagarta_espiga · vaquinha · milho_sadio."],
         p="Classificar (\"qual praga?\") basta; não precisamos localizar cada inseto. Modelo leve: 16,8 MB, ~2,8 ms em CPU, custo zero por foto, e com métricas medidas no teste.",
         c=["pipeline/modelo.py → classificar()", "scripts/05_treinar_cnn.py (treino)"],
         num=("2,8 ms", "por foto, em CPU"), qs=["q4", "q5", "q6", "q7"]),
    dict(n=9, z="ia", t="Roteador de confiança",
         f="Uma regra simples decide o tom da resposta conforme a confiança da CNN: errar para o lado do \"não sei\".",
         a=["**≥ 80% → DIRETO**: afirma a praga e orienta o manejo.",
            "**50% a 79% → DÚVIDA**: \"pode ser X\", pede outra foto e adianta o sinal para comparar.",
            "**< 50% → HUMANO**: encaminha à Casa da Agricultura / CATI.",
            "No teste: 77,5% direto (93,1% de acerto) · 20% dúvida · 2,5% humano."],
         p="Os erros custam diferente: afirmar a praga errada faz gastar e perder a lavoura; \"não tenho certeza\" custa uma ida ao técnico. O limiar foi escolhido medindo a curva cobertura × acerto.",
         c=["pipeline/roteador.py → decidir_rota()", "scripts/06_relatorio_validacao.py (varredura do limiar)"],
         num=("60,8%", "dos erros barrados"), qs=["q13", "q14"]),
    dict(n=10, z="resposta", t="Busca a ficha da praga (RAG)",
         f="Com a praga decidida, o código busca a ficha técnica dela na base de conhecimento curada pelo grupo.",
         a=["`kb/fichas-pragas-milho.md`: uma seção por praga, com campos fixos.",
            "Classe → seção (ex.: lagarta_cartucho → LAGARTA-DO-CARTUCHO).",
            "Pega **como reconhecer o dano** e **manejo ordenado por custo**.",
            "milho_sadio e rota humano não precisam de ficha: resposta fixa no código."],
         p="É um RAG com recuperação por filtro estruturado: a CNN já escolheu a praga, então não há o que \"procurar\" por similaridade. 4 fichas não justificam banco vetorial.",
         c=["pipeline/kb.py → buscar_ficha()", "kb/fichas-pragas-milho.md (Embrapa, CATI, Incaper)"],
         num=("4", "fichas curadas"), qs=["q21", "q22"]),
    dict(n=11, z="resposta", t="Claude redige a resposta",
         f="O Claude Haiku 4.5 transforma o texto técnico da ficha numa mensagem curta de WhatsApp. Ele só REDIGE, nunca decide.",
         a=["Regras: usar **só o texto fornecido**; até **70 palavras**; **nunca dose nem nome de produto**; manejo do mais barato ao mais caro.",
            "Na rota dúvida o tom muda: \"pode ser\", pede nova foto.",
            "O **código** cola o rodapé fixo: aviso \"não é receita\" + \"Acertei?\".",
            "Se a API falhar: resposta mecânica montada direto da ficha."],
         p="O aviso legal é obrigatório (agrotóxico exige receituário agronômico), por isso fica no código e não no LLM. Num teste real uma resposta saiu sem o aviso, e foi isso que motivou a mudança.",
         c=["pipeline/llm.py → redigir(), SYSTEM_PROMPT, RODAPE_FIXO", "pipeline/resposta.py → montar_resposta()"],
         num=("70", "palavras no máximo"), qs=["q19", "q23", "q24"]),
    dict(n=12, z="resposta", t="Resposta e feedback",
         f="A resposta volta ao produtor pela Evolution, e a reação dele (positivo/negativo) é registrada junto do diagnóstico.",
         a=["`sendText` com atraso de 2–4 s (aparece \"digitando...\", conversa mais natural).",
            "O ID da mensagem enviada é guardado para o bot não responder a si mesmo.",
            "Guarda o último diagnóstico daquele número (praga + confiança).",
            "Se o produtor responde com o polegar, grava em `feedback.jsonl` (sem o telefone)."],
         p="O feedback é como se mede o acerto no mundo real, depois do teste em laboratório, e gera dados para retreinar o modelo.",
         c=["whatsapp/evolution.py → send_text()", "whatsapp/handlers.py → registrar_feedback()"],
         num=("2–4 s", "de \"digitando...\""), qs=["q32", "q33"]),
]


IO = {
    1: ("foto tirada no celular", "mensagem de imagem no WhatsApp"),
    2: ("mensagem no número do bot", "JSON MESSAGES_UPSERT via POST"),
    3: ("POST em https://<domínio>/webhook", "POST em localhost:8001/webhook"),
    4: ("evento JSON", "\"received\" ou o motivo do descarte"),
    5: ("ID da mensagem", "imagem decodificada, em memória"),
    6: ("imagem", "OK, ou \"pequena\" / \"borrada\""),
    7: ("imagem reduzida (768 px)", "SIM → segue · NÃO → pede foto do milho"),
    8: ("imagem 224×224 normalizada", "(\"lagarta_cartucho\", 0.94)"),
    9: ("confiança 0.94", "rota = \"direto\""),
    10: ("\"lagarta_cartucho\"", "texto do dano + manejo por custo"),
    11: ("ficha + rota + confiança", "mensagem ≤ 70 palavras + rodapé fixo"),
    12: ("texto final", "mensagem no celular + linha em feedback.jsonl"),
}

# (id, categoria, nivel, provavel, pergunta, resposta curta, se pedirem mais, cuidado, etapa)
QS = [
    ("q1", "visao", "Básica", True, "Qual problema o AgroBot resolve?",
     "O pequeno produtor de milho vê um dano na lavoura e não sabe qual praga é, nem o que fazer primeiro. O técnico demora, e errar a praga significa gastar com o produto errado e ainda perder produção. O AgroBot identifica a praga por **uma foto no WhatsApp** e responde em linguagem simples, começando pelo manejo **mais barato**.",
     "Persona: João Batista, 54 anos, ~8 ha em Sorocaba. Daí as escolhas: WhatsApp (nada para instalar), resposta curta (máx. 70 palavras) e sem jargão.",
     "Não diga que o bot substitui o agrônomo. Ele faz triagem e orientação inicial.", 1),
    ("q2", "visao", "Básica", False, "Por que WhatsApp e não um aplicativo próprio?",
     "Porque o produtor já usa. Um app novo exige instalar, criar conta e aprender a interface: barreira grande para esse público. No WhatsApp ele só manda a foto.",
     "Tecnicamente o canal é isolado: a pasta `pipeline/` não sabe nada de WhatsApp. A mesma função de diagnóstico é chamada pelo webhook da Evolution (`whatsapp/`) e pela API com adaptadores (`api/canais`: teste, Twilio, Meta). Trocar de canal não mexe na IA.",
     "", 1),
    ("q3", "visao", "Média", True, "Por que só milho e só essas 4 classes? E a cigarrinha?",
     "O escopo foi definido pelos dados disponíveis: escolhemos as pragas com fotos públicas suficientes para treinar e medir (lagarta-do-cartucho, lagarta-da-espiga, vaquinha) e a classe **milho saudável**, obrigatória para o modelo poder dizer \"não tem praga\".",
     "A cigarrinha é a praga nº 1 do milho no Brasil, mas só há ~46 fotos públicas no mundo e o sintoma aparece ~30 dias após a infecção: foto não resolve. Fica fora do classificador; a ideia é tratá-la por alerta de calendário. A lagarta-elasmo tem ficha, mas só 17 fotos boas: fora do treino por ora.",
     "Não prometa que o bot reconhece qualquer praga.", 8),
    ("q4", "modelo", "Básica", True, "Que modelo de IA identifica a praga?",
     "Uma **rede neural convolucional (CNN)**, a MobileNetV3-Large, pré-treinada na ImageNet e ajustada por **transfer learning** para as nossas 4 classes. Ela recebe a foto em 224×224 e devolve uma probabilidade para cada classe; ficamos com a maior.",
     "Exportada para ONNX (16,8 MB) e executada com onnxruntime em CPU: ~2,8 ms por foto. Não precisa de GPU nem de servidor caro.",
     "Não diga que é o ChatGPT/Claude que identifica a praga.", 8),
    ("q5", "modelo", "Média", True, "Por que MobileNetV3 e não YOLO, ResNet ou um modelo maior?",
     "Porque o problema é de **classificação** (\"qual praga é?\"), não de **detecção** (\"onde está cada inseto?\"). YOLO exigiria desenhar caixas à mão em cada foto. A MobileNetV3 é leve, rápida em CPU e, com transfer learning, funciona bem com poucos milhares de fotos.",
     "Um modelo maior (ResNet-50, ViT) tem muito mais parâmetros para pouca foto: mais risco de overfitting e mais custo de hospedagem, para ganho incerto. Com ~5 mil fotos, o gargalo é dado, não arquitetura.",
     "", 8),
    ("q6", "modelo", "Média", False, "O que é transfer learning? Por que congelar o backbone?",
     "A rede já aprendeu a enxergar bordas, texturas e formas em ~1,2 milhão de imagens da ImageNet. Reaproveitamos essa parte (o **extrator de características**, ou backbone) **congelada** e treinamos só a última camada, que decide entre as nossas 4 classes.",
     "Vantagens: treina em minutos na CPU, precisa de menos dados e reduz overfitting, porque poucos parâmetros mudam. Treino: Adam, lr 0,001, 10 épocas, lote 32. Evolução possível: descongelar os últimos blocos (fine-tuning) com taxa de aprendizado baixa.",
     "", 8),
    ("q7", "modelo", "Básica", True, "Qual a acurácia? 86% é bom?",
     "No **conjunto de teste** (710 fotos que o modelo nunca viu): **86,3% de acurácia** e **81,4% de F1-macro**. Mas o número que mais importa é outro: quando o bot **afirma** um diagnóstico (confiança ≥ 80%), ele acerta **93,1%**. Nos casos incertos ele não afirma: pede outra foto ou encaminha.",
     "Referência: chutar sempre \"lagarta-do-cartucho\" daria 65,4% de acurácia, porque ela é 65% do teste. Por isso a métrica principal é o F1-macro, que dá o mesmo peso a cada classe.",
     "Não arredonde para \"90%\" nem cite número de treino/validação como se fosse teste.", 9),
    ("q8", "modelo", "Média", True, "Por que F1-macro e não só acurácia?",
     "O dataset é desbalanceado: lagarta-do-cartucho tem 3.266 fotos e lagarta-da-espiga 351. Um modelo que ignorasse a espiga ainda teria acurácia alta. O **F1-macro** calcula o F1 de cada classe e tira a média simples, então a classe pequena pesa igual.",
     "**Precisão**: dos que o modelo chamou de X, quantos eram X. **Revocação**: dos que eram X, quantos ele achou. **F1**: média harmônica das duas. O melhor checkpoint do treino foi escolhido pelo F1-macro na validação.",
     "", 8),
    ("q9", "modelo", "Média", False, "Como lidaram com o desbalanceamento das classes?",
     "Com **peso na função de perda**: cada classe recebe peso inversamente proporcional ao seu número de fotos. Errar uma lagarta-da-espiga \"custa\" mais caro no treino do que errar uma de cartucho.",
     "Peso = total ÷ (nº de classes × fotos da classe), na CrossEntropyLoss. Somado a isso: checkpoint escolhido por F1-macro e mais dados. A espiga subiu de 98 para 351 fotos (incluindo licença CC BY-NC, só uso local) e o F1 dela foi de 0,35 para ~0,70.",
     "", 8),
    ("q10", "modelo", "Difícil", True, "Qual a pior classe e por quê?",
     "**Lagarta-da-espiga: F1 de 69,7%.** Tem menos fotos (351) e é parecida com a lagarta-do-cartucho: as duas são lagartas de mariposa. Das 58 fotos de espiga no teste, 38 acertaram, 6 viraram cartucho e 10 viraram vaquinha.",
     "O roteador ajuda: só 50% das fotos de espiga recebem resposta direta; o resto cai em \"dúvida\" e o bot pede outra foto. A solução de verdade é mais dados dessa classe.",
     "Não esconda o número: mostrar que conhecem a fraqueza conta ponto.", 9),
    ("q11", "modelo", "Difícil", False, "A vaquinha tem precisão de só 66,7%. O que acontece?",
     "A **revocação** dela é 99% (quase toda vaquinha é encontrada), mas o modelo chama outras coisas de vaquinha: **40 fotos de lagarta-do-cartucho** viraram vaquinha. Nossa **hipótese**: muitas fotos de cartucho são recortes de dano na folha (furos e raspagem), parecidos com os furos da vaquinha.",
     "Olhando pela classe real, a vaquinha tem 100% de acerto na resposta direta; o erro aparece do lado do cartucho. Melhorias: mais fotos de dano de cada praga e, talvez, separar \"inseto\" de \"dano\" nos rótulos.",
     "Apresente como hipótese, não como fato comprovado.", 8),
    ("q12", "modelo", "Média", True, "E se mandarem uma selfie ou foto de cachorro?",
     "A CNN sempre escolhe uma das 4 classes (é assim que a softmax funciona), então, sem proteção, uma selfie viraria \"vaquinha\". Por isso existe o **porteiro de assunto**: antes da CNN, o Claude Haiku responde só **SIM ou NÃO** para \"tem planta ou inseto nessa foto?\". Se NÃO, o bot pede uma foto do milho.",
     "O Claude não escolhe praga, é só um filtro binário. \"Na dúvida, SIM\", e se a API falhar a foto passa (fail-open): o roteador de confiança ainda segura casos ruins. Antes dele vem o porteiro de qualidade (foto pequena ou borrada).",
     "", 7),
    ("q13", "modelo", "Difícil", True, "Por que os limiares de 80% e 50%?",
     "Os erros não custam igual: afirmar a praga errada faz o produtor gastar e perder lavoura; dizer \"não tenho certeza\" custa uma ida à Casa da Agricultura. **Medimos no teste**: com 80%, o bot responde direto em 77,5% das fotos com **93,1% de acerto** e segura **60,8% dos erros** antes de virarem recomendação.",
     "Varredura: limiar 0,70 → 85% de cobertura e 91,6% de acerto; 0,90 → 66% de cobertura e 94%. Acima de 0,80 o acerto quase não sobe e a cobertura cai muito. Entre 50% e 80% o bot diz \"pode ser\" e pede outra foto; abaixo de 50% encaminha ao técnico.",
     "Não diga que o número foi \"chutado\".", 9),
    ("q14", "modelo", "Difícil", False, "A confiança que a rede dá é confiável?",
     "A probabilidade da softmax **não é calibrada por garantia**: redes costumam ser confiantes demais. Por isso não confiamos no número cru: validamos o limiar **empiricamente**, medindo quanto o modelo acerta em cada faixa de confiança no conjunto de teste.",
     "Melhoria conhecida: calibração por **temperature scaling** no conjunto de validação e recalcular a curva cobertura × acurácia.",
     "", 9),
    ("q15", "dados", "Básica", True, "De onde vieram as fotos de treino?",
     "Só de fontes públicas com licença aberta: **GBIF/iNaturalist** (fotos de naturalistas) e o dataset **KaraAgro AI Maize** (Harvard Dataverse, CC BY), do qual recortamos as regiões anotadas com caixa. Depois da limpeza ficaram **4.932 fotos**.",
     "Cada foto tem origem e licença registradas em `dados/creditos.csv`. Licenças: CC BY, CC0, CC BY-SA e CC BY-NC (esta só em uso local; o dataset não vai para o GitHub).",
     "", 8),
    ("q16", "dados", "Difícil", True, "Como garantiram que o teste não \"vazou\" para o treino?",
     "Uma observação do iNaturalist costuma ter várias fotos do **mesmo inseto**, tiradas no mesmo minuto. Se uma cai no treino e outra no teste, o modelo \"já viu a resposta\". Por isso a divisão 70/15/15 é feita **por observação, não por foto**: fotos da mesma observação ficam sempre juntas.",
     "Treino (3.536) ajusta os pesos; validação (686) escolhe o melhor epoch; teste (710) é usado só para reportar. Semente fixa (42): divisão reproduzível. Duplicatas removidas por hash perceptual (pHash, distância de Hamming ≤ 4).",
     "Não reporte métrica de validação como se fosse de teste.", 8),
    ("q17", "dados", "Média", False, "Como limparam os dados? Teve algum problema?",
     "O script de limpeza remove fotos pequenas, borradas e duplicadas: **3.239 removidas**. Achamos dois bugs reais: (1) o GBIF trazia a **mariposa adulta** nas classes de lagarta (93% eram adultos), corrigido filtrando pelo estágio de vida; (2) o detector de borrão descartava **fotos macro boas** (inseto nítido, fundo desfocado).",
     "Correção do (2): medir a nitidez (variância do Laplaciano) em 16 blocos 4×4 e usar o melhor bloco. Recuperou ~1.089 fotos boas. A mesma lógica é o porteiro de qualidade em produção.",
     "", 6),
    ("q18", "dados", "Média", False, "Usaram data augmentation?",
     "Sim, **só no treino**: recorte aleatório, espelhamento horizontal, rotação até 30°, brilho/contraste, blur leve e ruído. Simula foto de celular tirada no campo.",
     "**Sem** espelhamento vertical (planta não fica de cabeça para baixo) e sem mexer forte na cor: a cor da lagarta é informação. Validação, teste e produção usam só redimensionar + recorte central, idênticos.",
     "", 8),
    ("q19", "llm", "Difícil", True, "Se tem um LLM, ele não pode inventar coisa?",
     "O LLM **nunca decide a praga** e não cria conteúdo técnico: a CNN decide; o texto vem da **ficha curada**; o Claude só resume para o WhatsApp, com regras fixas: usar só o texto fornecido, máximo 70 palavras, **nunca dose nem nome de produto**, manejo do mais barato para o mais caro.",
     "O que é obrigatório não fica com o LLM: o aviso legal (\"não é receita\") e o \"Acertei?\" são colados **pelo código**. Casos simples (foto ruim, milho saudável, rota humano) têm resposta fixa, sem LLM. Se a API falhar, há resposta mecânica tirada da ficha.",
     "Não diga que o LLM \"nunca erra\"; diga que o risco foi limitado por design.", 11),
    ("q20", "llm", "Difícil", True, "Por que não deixar o Claude olhar a foto e diagnosticar sozinho?",
     "Porque não daria para **medir nem controlar**. A CNN tem métricas no teste (86,3%; 93,1% na rota direta), devolve uma confiança que alimenta o roteador, roda em ~3 ms e de graça. Um LLM generalista pode responder com segurança algo errado e muda de comportamento entre versões.",
     "Usamos o Claude onde ele é bom: redigir texto e um filtro SIM/NÃO genérico. Separar **quem decide** (CNN) de **quem escreve** (LLM) é a ideia central da arquitetura.",
     "", 7),
    ("q21", "llm", "Média", True, "Isso é RAG? Vocês usam banco vetorial?",
     "É um **RAG simplificado**: Recupera (a ficha da praga) → Aumenta (coloca o texto no prompt) → Gera (o Claude redige). A recuperação é um **filtro estruturado**: a classe da CNN aponta direto para a seção da ficha. Não precisa de banco vetorial porque a praga já foi decidida e são só 4 fichas.",
     "Busca vetorial (embeddings) faria sentido para **pergunta livre** do produtor (\"posso usar sabão?\"), que é evolução futura. Escolher a ferramenta mais simples que resolve foi decisão consciente.",
     "", 10),
    ("q22", "llm", "Básica", False, "De onde vem o conteúdo das respostas?",
     "Da base `kb/fichas-pragas-milho.md`, escrita e curada pelo grupo a partir de fontes técnicas como **Embrapa, CATI e Incaper**: como reconhecer o dano, nível de controle e manejo ordenado por custo, com a lista de fontes no final.",
     "Cada ficha tem campos com nome fixo (`como_reconhecer_o_dano`, `manejo_ordenado_por_custo`...). Por isso o código consegue recortar exatamente o trecho certo.",
     "Não cite fonte que não esteja na base.", 10),
    ("q23", "llm", "Média", False, "Por que Claude Haiku 4.5? Quanto custa?",
     "É um modelo pequeno, rápido (~3 s por resposta) e barato, que **segue bem instruções restritivas**, o que mais importa para redigir com segurança. Com **US$ 5 de crédito (≈ R$ 27,50)** cabem mais de 3.000 diagnósticos: menos de 1 centavo cada.",
     "Cada diagnóstico usa até 2 chamadas: o porteiro de assunto (1 palavra, `max_tokens=5`) e a redação (`max_tokens=300`). Custo direto do projeto: R$ 27,50 no cenário realista.",
     "", 11),
    ("q24", "llm", "Média", False, "E se a internet ou a API do Claude cair?",
     "O bot continua respondendo. Se a redação falhar, cai numa **resposta mecânica** montada direto da ficha (primeiro sinal de dano + primeira medida de manejo + aviso legal). Se o porteiro de assunto falhar, a foto passa e segue o fluxo normal.",
     "A CNN roda localmente: o diagnóstico em si não depende do Claude. Sem WhatsApp/ngrok, obviamente, a mensagem nem chega.",
     "", 11),
    ("q25", "arq", "Básica", True, "Como a mensagem sai do WhatsApp e chega no código?",
     "Celular → WhatsApp → **Evolution API** (em Docker, conectada ao número do bot por QR Code) → POST HTTP no nosso **webhook** através do túnel **ngrok** → **FastAPI** (Python) na porta 8001 → pipeline de diagnóstico → resposta enviada de volta pela Evolution.",
     "A Evolution usa Postgres e Redis próprios (no mesmo docker-compose) para guardar sessão e mensagens. Nosso código baixa a imagem pela rota `getBase64FromMediaMessage` e responde pela rota `sendText`.",
     "", 2),
    ("q26", "arq", "Média", True, "Por que Evolution API e não a API oficial do WhatsApp?",
     "Tentamos a API oficial (**Meta Cloud API**): na conta de teste, o envio para números do Brasil foi bloqueado (**erro 130497**). A Evolution é gratuita, open source e conecta como o WhatsApp Web: ideal para protótipo.",
     "Para produção, o caminho é a API oficial com número verificado. A arquitetura já prevê isso: `api/canais` tem adaptadores (Meta, Twilio, teste) e o pipeline não depende do canal.",
     "", 2),
    ("q27", "arq", "Média", False, "Para que serve o ngrok, se está tudo no notebook?",
     "O ngrok cria um **endereço público HTTPS fixo** que encaminha para a porta 8001 do notebook. A Evolution manda os eventos para esse endereço. Assim o bot roda num notebook comum, sem servidor e sem configuração de rede, e com o mesmo formato de produção.",
     "Em produção o webhook ficaria num servidor na nuvem com HTTPS próprio. O painel do ngrok (`localhost:4040`) ainda ajuda a depurar, mostrando cada requisição.",
     "", 3),
    ("q28", "arq", "Difícil", False, "Por que o webhook responde antes de analisar a foto?",
     "A Evolution espera resposta rápida do webhook. A CNN leva milissegundos, mas as chamadas ao Claude levam ~3 s. Então o FastAPI devolve **200 OK na hora** e processa a foto em **BackgroundTasks**, uma tarefa em segundo plano.",
     "Limitação: BackgroundTasks **não é fila durável**; se o processo cair no meio, aquela mensagem se perde. Para produção: fila com Redis + RQ (ou Celery) e workers separados.",
     "", 5),
    ("q29", "arq", "Média", False, "Como o bot evita responder duas vezes, a si mesmo ou a grupos?",
     "Todo evento passa pelo `check_event`: descarta mensagem com **mais de 120 s** (fila antiga), mensagem enviada **pelo próprio bot** (guardamos os IDs enviados), **grupos** (@g.us), números fora da lista permitida e **IDs já processados** (duplicata).",
     "Aprendemos na prática: com o bot desligado, acumularam milhares de mensagens de grupo e, ao religar, a Evolution travou. Correção: `groupsIgnore` na instância + limite de idade.",
     "", 4),
    ("q30", "arq", "Difícil", True, "Isso escala para milhares de produtores?",
     "A IA não é o gargalo: a CNN roda em ~3 ms em CPU. O que precisa mudar é a **infraestrutura**: API oficial do WhatsApp, fila durável (Redis/RQ) com workers, banco de dados para histórico e feedback e hospedagem na nuvem.",
     "Hoje os controles (IDs processados, último diagnóstico) ficam na memória do processo: servem para protótipo, não para várias instâncias. O custo do LLM cresce linearmente, mas é baixo (menos de 1 centavo por diagnóstico).",
     "Não diga que \"já está pronto para produção\".", 5),
    ("q31", "arq", "Básica", False, "Quanto tempo o produtor espera pela resposta?",
     "**Alguns segundos.** A parte local (qualidade + pré-processamento + CNN) leva ~**8 ms** de mediana. O resto é rede: baixar a foto, as chamadas ao Claude (~3 s) e um atraso proposital de 2–4 s no envio, que mostra \"digitando...\" e deixa a conversa natural.",
     "Medido em 200 fotos do teste: porteiro 2,2 ms, pré-processo 3,3 ms, CNN 2,8 ms (medianas).",
     "", 5),
    ("q32", "etica", "Média", True, "E a privacidade? LGPD?",
     "Coletamos o mínimo: a foto é analisada **em memória e não é salva**; nos logs o número aparece **mascarado** (***1234); o feedback grava só data, praga, confiança e positivo/negativo, **sem o telefone**. Chaves de API ficam no `.env`, fora do Git.",
     "Em modo de teste o bot só responde números de uma lista permitida (`ALLOWED_NUMBERS`). Para produção: termo de uso/consentimento na primeira mensagem e política de retenção de dados.",
     "", 12),
    ("q33", "etica", "Difícil", True, "E se o bot errar e o produtor perder a lavoura?",
     "O sistema foi desenhado para **errar para o lado do \"não sei\"**: só afirma com ≥ 80% de confiança, **nunca indica dose ou produto**, começa pelo manejo mais barato e **toda** resposta diz que não é receita (agrotóxico exige receituário agronômico). Na dúvida, encaminha à Casa da Agricultura/CATI.",
     "É ferramenta de **triagem e orientação**, não substitui o engenheiro agrônomo. O aviso é colado pelo código, não depende do LLM lembrar.",
     "", 9),
    ("q34", "futuro", "Difícil", True, "Testaram com produtores reais ou fotos de campo?",
     "**Não com produtores.** Testamos o fluxo completo no **WhatsApp real**, com fotos das 4 classes, e o modelo foi avaliado em 710 fotos de teste nunca vistas. Mas são fotos públicas, não da região de Sorocaba. É a principal limitação e o primeiro próximo passo.",
     "Plano: coletar fotos de campo e usá-las **só no teste**, para medir o desempenho real. O feedback (positivo/negativo) já está implementado para medir acerto em uso.",
     "Não invente um teste de campo que não aconteceu.", 12),
    ("q35", "futuro", "Básica", True, "Quais os próximos passos?",
     "1) Fotos de campo locais para teste real; 2) mais fotos de lagarta-da-espiga e incluir a lagarta-elasmo; 3) alerta de calendário para a cigarrinha; 4) API oficial do WhatsApp + fila Redis/RQ + nuvem; 5) painel com métricas de uso e feedback; 6) perguntas livres por texto (busca vetorial).",
     "Priorize: dados de campo primeiro (sem eles não sabemos o desempenho real), infraestrutura depois.",
     "", 12),
    ("q36", "futuro", "Média", False, "O que é de vocês e o que é ferramenta pronta?",
     "**Pronto:** bibliotecas (PyTorch, FastAPI, onnxruntime), o modelo base pré-treinado, a Evolution API e o Claude. **Nosso:** coleta e limpeza do dataset (com 2 bugs corrigidos), divisão sem vazamento, treino e avaliação, roteador com limiar medido, os dois porteiros, a base de conhecimento curada, os prompts com regras de segurança e a integração ponta a ponta.",
     "Analogia: usamos tijolo e cimento prontos; o projeto da casa e a obra são nossos.",
     "", 8),
]
QMAP = {q[0]: q for q in QS}

GLOSSARIO = [
    ("CNN", "Rede neural convolucional: tipo de rede especializada em imagens, que aprende filtros para bordas, texturas e formas."),
    ("Transfer learning", "Reaproveitar uma rede já treinada num conjunto enorme (ImageNet) e ajustar só o final para o nosso problema."),
    ("Backbone", "A parte da rede que extrai características da imagem. No AgroBot fica congelada."),
    ("Logits / Softmax", "Logits são as notas cruas da rede para cada classe; a softmax as converte em probabilidades que somam 100%."),
    ("ONNX", "Formato aberto de modelo. Permite rodar o modelo sem PyTorch, leve e rápido, com onnxruntime."),
    ("Acurácia", "Fração de acertos no total. Engana quando as classes são desbalanceadas."),
    ("Precisão / Revocação", "Precisão: quando diz X, quantas vezes é X. Revocação: dos X reais, quantos encontra."),
    ("F1-macro", "Média harmônica de precisão e revocação, calculada por classe e depois tirada a média simples."),
    ("Matriz de confusão", "Tabela real × previsto. A diagonal são os acertos; fora dela, quem é confundido com quem."),
    ("Overfitting", "Quando o modelo decora o treino e vai mal em dados novos."),
    ("Data augmentation", "Variações artificiais nas fotos de treino (girar, clarear...) para o modelo generalizar melhor."),
    ("Vazamento de dados", "Quando informação do teste aparece no treino e infla a métrica."),
    ("Webhook", "Endereço HTTP que um sistema chama para avisar outro de um evento (\"chegou mensagem\")."),
    ("Docker", "Empacota programas em containers que rodam igual em qualquer máquina."),
    ("ngrok", "Túnel que expõe uma porta local na internet com um endereço HTTPS público."),
    ("LLM", "Modelo de linguagem grande (aqui, Claude Haiku 4.5). No AgroBot só redige e faz o filtro SIM/NÃO."),
    ("RAG", "Retrieval-Augmented Generation: buscar um texto confiável e entregá-lo ao LLM para ele responder com base nele."),
    ("Banco vetorial", "Banco que busca textos por similaridade de significado (embeddings). Não foi necessário aqui."),
    ("Fail-open", "Se uma verificação falhar, o sistema deixa passar em vez de travar."),
    ("Fila durável", "Fila (ex.: Redis/RQ) que guarda tarefas mesmo se o processo cair. BackgroundTasks não é."),
]


# ══════════════════════════════════════════════════════════════════════════════
# MOTOR DE DESENHO
# ══════════════════════════════════════════════════════════════════════════════

class PDF:
    def __init__(self, destino, pagina_de=None):
        self.c = pdfcanvas.Canvas(str(destino), pagesize=(W, H))
        self.c.setTitle("AgroBot — Guia de estudo para a banca")
        self.c.setAuthor("Equipe AgroBot")
        self.c.setSubject("Como o AgroBot funciona + perguntas prováveis da banca")
        self.n = 0
        self.pagina_de = pagina_de or {}   # chave -> nº da página (da 1ª passada)
        self.registro = {}
        self.total = max(self.pagina_de.values()) if self.pagina_de else 0

    # coordenadas a partir do TOPO
    def Y(self, top):
        return H - top

    def nova(self, chave, secao="", titulo="", outline=None, nivel=0, capa=False):
        if self.n:
            self.c.showPage()
        self.n += 1
        c = self.c
        c.bookmarkPage(f"pg{self.n}")
        c.bookmarkPage(chave)
        self.registro[chave] = self.n
        if outline:
            c.addOutlineEntry(outline, chave, level=nivel, closed=nivel == 0 and False)
        c.setFillColor(FUNDO); c.rect(0, 0, W, H, stroke=0, fill=1)
        if capa:
            return
        # faixa superior
        c.setFillColor(VERDE); c.rect(0, H - 34, W, 34, stroke=0, fill=1)
        c.setFillColor(MILHO); c.rect(0, H - 37, W, 3, stroke=0, fill=1)
        c.setFont("UISB", 10); c.setFillColor(BRANCO)
        c.drawString(M, H - 22, "AgroBot")
        c.setFont("UI", 10); c.setFillColor(C("#B7D8C4"))
        c.drawString(M + 50, H - 22, "·  guia de estudo para a banca")
        if secao:
            c.setFont("UISB", 9.5); c.setFillColor(MILHO)
            c.drawRightString(W - M, H - 22, secao.upper())
        if titulo:
            c.setFont("UIB", 23); c.setFillColor(VERDE)
            c.drawString(M, self.Y(76), titulo)
        self.rodape()

    def rodape(self):
        c = self.c
        c.setStrokeColor(LINHA); c.setLineWidth(0.8)
        c.line(M, 40, W - M, 40)
        y, h = 12, 21
        if self.n > 1:
            self.botao(M, y, 92, h, "‹  Anterior", f"pg{self.n - 1}", cor=VERDE2)
        if self.total and self.n < self.total:
            self.botao(W - M - 92, y, 92, h, "Próxima  ›", f"pg{self.n + 1}", cor=VERDE2)
        itens = [("Início", "capa"), ("Índice", "indice"), ("Fluxo", "mapa"),
                 ("Números", "numeros"), ("Perguntas", "perguntas"), ("Glossário", "glossario")]
        bw, gap = 78, 6
        x0 = W / 2 - (len(itens) * bw + (len(itens) - 1) * gap) / 2
        for i, (rot, dest) in enumerate(itens):
            self.botao(x0 + i * (bw + gap), y, bw, h, rot, dest, cor=None)
        c.setFont("UI", 8); c.setFillColor(SUAVE)
        c.drawRightString(W - M - 100, y + 7, f"{self.n}/{self.total}")

    def botao(self, x, y, w, h, rotulo, dest, cor=VERDE2, fonte=9, cor_texto=None, raio=5):
        """x,y = canto inferior esquerdo (coordenadas PDF)."""
        c = self.c
        if cor is None:
            c.setFillColor(BRANCO); c.setStrokeColor(LINHA)
            c.roundRect(x, y, w, h, raio, stroke=1, fill=1)
            c.setFillColor(VERDE)
        else:
            c.setFillColor(cor); c.roundRect(x, y, w, h, raio, stroke=0, fill=1)
            c.setFillColor(cor_texto or BRANCO)
        c.setFont("UISB", fonte)
        c.drawCentredString(x + w / 2, y + h / 2 - fonte * 0.36, rotulo)
        self.link(x, y, w, h, dest)

    def link(self, x, y, w, h, dest):
        self.c.linkAbsolute("", dest, (x, y, x + w, y + h), thickness=0)

    def caixa(self, x, top, w, h, fill=BRANCO, stroke=LINHA, raio=8, lw=0.8):
        c = self.c
        c.setFillColor(fill)
        if stroke is None:
            c.roundRect(x, self.Y(top + h), w, h, raio, stroke=0, fill=1)
        else:
            c.setStrokeColor(stroke); c.setLineWidth(lw)
            c.roundRect(x, self.Y(top + h), w, h, raio, stroke=1, fill=1)

    def texto(self, t, x, top, w, size=10, font="UI", cor=TINTA, align=TA_LEFT,
              maxh=None, minsize=6.8, lead=1.32, raw=False):
        """Desenha um paragrafo com topo em `top`. Encolhe a fonte ate caber em maxh."""
        markup = t if raw else esc(t)
        s = size
        while True:
            p = Paragraph(markup, estilo(s, font, cor, align, lead))
            _, h = p.wrap(w, 10000)
            if maxh is None or h <= maxh or s <= minsize:
                break
            s -= 0.25
        if maxh is not None and h > maxh:
            print(f"  [aviso] texto não coube (pág {self.n}): {t[:50]}...")
        p.drawOn(self.c, x, self.Y(top) - h)
        return h

    def lista(self, itens, x, top, w, size=10, maxh=None, cor=TINTA, marcador="•", cor_marc=VERDE2,
              gap=5, minsize=7, fonte_marc="UIB"):
        s = size
        while True:
            alturas = []
            for it in itens:
                p = Paragraph(esc(it), estilo(s, "UI", cor))
                _, h = p.wrap(w - 14, 10000)
                alturas.append(h)
            total = sum(alturas) + gap * (len(itens) - 1)
            if maxh is None or total <= maxh or s <= minsize:
                break
            s -= 0.25
        y = top
        for it, h in zip(itens, alturas):
            self.c.setFillColor(cor_marc); self.c.setFont(fonte_marc, s)
            self.c.drawString(x, self.Y(y) - s * 1.0, marcador)
            p = Paragraph(esc(it), estilo(s, "UI", cor)); p.wrap(w - 14, 10000)
            p.drawOn(self.c, x + 14, self.Y(y) - h)
            y += h + gap
        return total

    def chip(self, x, top, rotulo, fundo, cor=BRANCO, size=8.5, font="UISB", padx=7, h=17):
        c = self.c
        w = pdfmetrics.stringWidth(rotulo, font, size) + 2 * padx
        c.setFillColor(fundo); c.roundRect(x, self.Y(top + h), w, h, h / 2, stroke=0, fill=1)
        c.setFillColor(cor); c.setFont(font, size)
        c.drawString(x + padx, self.Y(top + h) + h / 2 - size * 0.35, rotulo)
        return w

    def seta(self, x1, y1, x2, y2, cor=SUAVE, lw=1.6, ponta=6):
        """Coordenadas a partir do topo."""
        import math
        c = self.c
        c.setStrokeColor(cor); c.setFillColor(cor); c.setLineWidth(lw)
        Y1, Y2 = self.Y(y1), self.Y(y2)
        ang = math.atan2(Y2 - Y1, x2 - x1)
        bx, by = x2 - ponta * math.cos(ang), Y2 - ponta * math.sin(ang)
        c.line(x1, Y1, bx, by)
        pth = c.beginPath()
        pth.moveTo(x2, Y2)
        pth.lineTo(bx + ponta * 0.55 * math.sin(ang), by - ponta * 0.55 * math.cos(ang))
        pth.lineTo(bx - ponta * 0.55 * math.sin(ang), by + ponta * 0.55 * math.cos(ang))
        pth.close()
        c.drawPath(pth, stroke=0, fill=1)

    def salvar(self):
        self.c.showOutline()
        self.c.save()


# ══════════════════════════════════════════════════════════════════════════════
# PAGINAS
# ══════════════════════════════════════════════════════════════════════════════

def pg_capa(d: PDF):
    d.nova("capa", outline="Capa", capa=True)
    c = d.c
    c.setFillColor(VERDE); c.rect(0, 0, W * 0.58, H, stroke=0, fill=1)
    c.setFillColor(MILHO); c.rect(W * 0.58, 0, 5, H, stroke=0, fill=1)
    # "grãos" decorativos
    c.setFillColor(C("#24573F"))
    for i in range(7):
        for j in range(4):
            c.circle(W * 0.58 - 34 - j * 26, 60 + i * 26, 8, stroke=0, fill=1)
    c.setFont("UISB", 12); c.setFillColor(MILHO)
    c.drawString(56, H - 92, "UPX · FACENS · ENGENHARIA DA COMPUTAÇÃO")
    c.setFont("UIB", 64); c.setFillColor(BRANCO)
    c.drawString(52, H - 170, "AgroBot")
    d.texto("Guia de estudo técnico para a banca", 56, 196, 440, size=24, font="UIL", cor=BRANCO)
    d.texto("Como a aplicação funciona, etapa por etapa, e as perguntas que a banca provavelmente vai fazer, "
            "com respostas prontas para falar.", 56, 250, 400, size=12.5, cor=C("#CDE6D6"))
    c.setFont("UI", 10); c.setFillColor(C("#9CC5AE"))
    c.drawString(56, 70, "Tudo neste PDF é clicável: botões, caixas do fluxo, perguntas e o rodapé.")
    c.drawString(56, 54, "Números medidos no conjunto de TESTE (scripts/06_relatorio_validacao.py).")

    # lado direito: por onde começar
    x = W * 0.58 + 40
    c.setFont("UIB", 15); c.setFillColor(VERDE)
    c.drawString(x, H - 92, "Por onde começar")
    opcoes = [
        ("1", "Entender em 30 segundos", "A ideia central do sistema", "pitch", VERDE2),
        ("2", "Ver o fluxo completo", "12 etapas clicáveis, da foto à resposta", "mapa", C("#2A6F97")),
        ("3", "Decorar os números", "Os 12 números que mais vão perguntar", "numeros", C("#C77D0A")),
        ("4", "Treinar as perguntas", "36 perguntas com resposta curta", "perguntas", C("#6D4C7D")),
        ("5", "Testar-se", "Quiz rápido + roteiro do dia", "quiz", VERMELHO),
    ]
    top = 116
    for num, tit, sub, dest, cor in opcoes:
        bx, bw, bh = x, W - x - 40, 62
        d.caixa(bx, top, bw, bh, fill=BRANCO, stroke=LINHA, raio=10)
        c.setFillColor(cor); c.roundRect(bx, d.Y(top + bh), 8, bh, 4, stroke=0, fill=1)
        c.circle(bx + 36, d.Y(top + bh / 2), 15, stroke=0, fill=1)
        c.setFillColor(BRANCO); c.setFont("UIB", 14)
        c.drawCentredString(bx + 36, d.Y(top + bh / 2) - 5, num)
        c.setFillColor(TINTA); c.setFont("UISB", 13.5)
        c.drawString(bx + 62, d.Y(top + 26), tit)
        c.setFillColor(SUAVE); c.setFont("UI", 10)
        c.drawString(bx + 62, d.Y(top + 44), sub)
        c.setFillColor(cor); c.setFont("UIB", 16)
        c.drawRightString(bx + bw - 16, d.Y(top + bh / 2) - 6, "›")
        d.link(bx, d.Y(top + bh), bw, bh, dest)
        top += bh + 12


def pg_indice(d: PDF):
    d.nova("indice", "Índice", "Índice", outline="Índice")
    secoes = [
        ("Parte 1 · Entender", [
            ("O AgroBot em 30 segundos", "pitch"),
            ("Mapa do fluxo (clicável)", "mapa"),
            *[(f"Etapa {s['n']:02d} · {s['t']}", f"etapa{s['n']}") for s in STEPS],
        ]),
        ("Parte 2 · Aprofundar", [
            ("Simulação: 4 fotos, 4 caminhos", "caminhos"),
            ("Como o modelo foi treinado", "treino"),
            ("Resultados do modelo", "resultados"),
            ("Números para decorar", "numeros"),
        ]),
        ("Parte 3 · Banca", [
            ("Índice das perguntas", "perguntas"),
            *[(f"{CATS[k][0]}", f"cat_{k}") for k in CATS],
            ("Limitações: como falar delas", "limitacoes"),
            ("Glossário", "glossario"),
            ("Teste-se (quiz)", "quiz"),
            ("Gabarito do quiz", "gabarito"),
            ("Roteiro e checklist do dia", "roteiro"),
        ]),
    ]
    colx = [M, M + 300, M + 600]
    for (tit, itens), x in zip(secoes, colx):
        top = 100
        d.c.setFont("UIB", 12.5); d.c.setFillColor(VERDE2)
        d.c.drawString(x, d.Y(top + 12), tit)
        top += 24
        for rot, dest in itens:
            pg = d.pagina_de.get(dest, "")
            d.c.setFont("UI", 10.2); d.c.setFillColor(TINTA)
            d.c.drawString(x + 2, d.Y(top + 11), rot)
            d.c.setFillColor(SUAVE); d.c.setFont("UISB", 10)
            d.c.drawRightString(x + 282, d.Y(top + 11), str(pg))
            d.c.setStrokeColor(LINHA); d.c.setLineWidth(0.5)
            d.c.line(x, d.Y(top + 15.5), x + 284, d.Y(top + 15.5))
            d.link(x, d.Y(top + 16), 284, 17, dest)
            top += 17.5


def pg_pitch(d: PDF):
    d.nova("pitch", "Entender", "O AgroBot em 30 segundos", outline="Parte 1 · Entender")
    d.c.addOutlineEntry("O AgroBot em 30 segundos", "pitch", level=1)
    d.caixa(M, 96, W - 2 * M, 92, fill=VERDE, stroke=None, raio=12)
    d.texto("\u201cO produtor manda a foto da praga no WhatsApp. Uma rede neural treinada por nós identifica a praga "
            "entre 4 classes; uma regra de confiança decide se o bot afirma, pede outra foto ou encaminha ao técnico; "
            "e o Claude só transforma a ficha técnica dessa praga numa mensagem simples, com o aviso legal "
            "colado pelo código.\u201d", M + 24, 110, W - 2 * M - 48, size=13.2, cor=BRANCO, font="UI", maxh=70)
    d.c.setFont("UISB", 9); d.c.setFillColor(SUAVE)
    d.c.drawString(M, d.Y(204), "SE LEMBRAR DE APENAS TRÊS IDEIAS, LEMBRE DESTAS")
    ideias = [
        ("1", "A CNN decide, o LLM só escreve",
         "Quem escolhe a praga é a MobileNetV3, medida no teste. O Claude nunca escolhe praga: ele só redige "
         "a partir da ficha curada, sem dose nem produto. Isso torna o sistema auditável.", "q20", VERDE2),
        ("2", "Errar para o lado do \u201cnão sei\u201d",
         "Afirmar a praga errada custa dinheiro e lavoura. Por isso o bot só afirma com ≥ 80% de confiança: "
         "nesses casos acerta 93,1%, e 60,8% dos erros do modelo são barrados.", "q13", C("#C77D0A")),
        ("3", "Leve, barato e com plano B",
         "A CNN roda em 2,8 ms numa CPU comum, com 16,8 MB. O custo do projeto foi R$ 27,50. Se o Claude cair, "
         "há resposta mecânica; se a foto for ruim ou fora do assunto, há porteiros.", "q24", C("#6D4C7D")),
    ]
    w = (W - 2 * M - 2 * 16) / 3
    for i, (n, tit, txt, q, cor) in enumerate(ideias):
        x = M + i * (w + 16)
        top = 216
        d.caixa(x, top, w, 248, fill=BRANCO)
        d.c.setFillColor(cor); d.c.roundRect(x, d.Y(top + 6), w, 6, 3, stroke=0, fill=1)
        d.c.setFont("UIB", 34); d.c.drawString(x + 18, d.Y(top + 52), n)
        d.texto(tit, x + 18, top + 62, w - 36, size=15, font="UIB", cor=TINTA)
        d.texto(txt, x + 18, top + 96, w - 36, size=12, cor=TINTA, maxh=118)
        d.botao(x + 18, d.Y(top + 232), w - 36, 24, f"Ver a pergunta da banca  ›", q, cor=cor)


def pg_mapa(d: PDF):
    d.nova("mapa", "Fluxo", "Mapa do fluxo: da foto à resposta", outline="Mapa do fluxo", nivel=1)
    d.texto("Clique em qualquer caixa para abrir a explicação da etapa.", M, 86, 600, size=10.5, cor=SUAVE)
    # legenda
    x = W - M
    for z in reversed(list(ZONAS)):
        nome, cor, _ = ZONAS[z]
        wchip = pdfmetrics.stringWidth(nome, "UISB", 8.5) + 14
        x -= wchip + 6
        d.chip(x, 84, nome, cor)
    cols, bw, bh = 4, 196, 92
    gapx = (W - 2 * M - cols * bw) / (cols - 1)
    tops = [118, 238, 358]
    pos = {}
    for i, s in enumerate(STEPS):
        linha, col = divmod(i, cols)
        if linha == 1:
            col = cols - 1 - col  # serpentina
        x = M + col * (bw + gapx)
        top = tops[linha]
        pos[s["n"]] = (x, top)
        nome, cor, claro = ZONAS[s["z"]]
        d.caixa(x, top, bw, bh, fill=claro, stroke=cor, raio=10, lw=1.2)
        d.c.setFillColor(cor); d.c.circle(x + 22, d.Y(top + 22), 13, stroke=0, fill=1)
        d.c.setFillColor(BRANCO); d.c.setFont("UIB", 11.5)
        d.c.drawCentredString(x + 22, d.Y(top + 22) - 4, str(s["n"]))
        d.texto(s["t"], x + 42, top + 12, bw - 52, size=11.2, font="UIB", cor=TINTA, maxh=30)
        resumo = {
            1: "Foto da folha, espiga ou inseto", 2: "Docker + QR Code → evento HTTP",
            3: "Endereço HTTPS → porta 8001", 4: "Descarta antigo, grupo, duplicado",
            5: "200 OK já; baixa a foto depois", 6: "Pequena? Borrada? Pede outra",
            7: "Claude: SIM/NÃO tem planta?", 8: "MobileNetV3: praga + confiança",
            9: "≥80 afirma · 50–79 dúvida · <50 técnico", 10: "Ficha curada da praga",
            11: "Claude resume + aviso fixo", 12: "Envia + grava o feedback",
        }[s["n"]]
        d.texto(resumo, x + 14, top + 50, bw - 26, size=9.4, cor=SUAVE, maxh=34)
        d.link(x, d.Y(top + bh), bw, bh, f"etapa{s['n']}")
    # setas
    for a in range(1, 12):
        (x1, t1), (x2, t2) = pos[a], pos[a + 1]
        if t1 == t2:
            if x2 > x1:
                d.seta(x1 + bw + 3, t1 + bh / 2, x2 - 3, t2 + bh / 2)
            else:
                d.seta(x1 - 3, t1 + bh / 2, x2 + bw + 3, t2 + bh / 2)
        else:
            d.seta(x1 + bw / 2, t1 + bh + 3, x2 + bw / 2, t2 - 3)
    # saidas laterais (respostas antecipadas)
    d.c.setFont("UII", 8.4); d.c.setFillColor(VERMELHO)
    x6, t6 = pos[6]; x7, t7 = pos[7]
    d.c.drawString(x6 + 10, d.Y(t6 + bh + 12), "→ foto ruim: pede outra")
    d.c.drawString(x7 + 10, d.Y(t7 + bh + 12), "→ fora do assunto: pede foto do milho")


def barra_etapas(d: PDF, atual):
    top = 452
    d.c.setFont("UISB", 8); d.c.setFillColor(SUAVE)
    d.c.drawString(M, d.Y(top - 4), "ETAPAS")
    x0, w = M + 48, (W - 2 * M - 48) / 12
    for s in STEPS:
        nome, cor, claro = ZONAS[s["z"]]
        x = x0 + (s["n"] - 1) * w
        ativo = s["n"] == atual
        d.c.setFillColor(cor if ativo else claro)
        d.c.roundRect(x + 2, d.Y(top + 14), w - 4, 18, 9, stroke=0, fill=1)
        d.c.setFillColor(BRANCO if ativo else cor); d.c.setFont("UIB", 9)
        d.c.drawCentredString(x + w / 2, d.Y(top + 14) + 5.5, str(s["n"]))
        d.link(x + 2, d.Y(top + 14), w - 4, 18, f"etapa{s['n']}")


def pg_etapa(d: PDF, s):
    nome, cor, claro = ZONAS[s["z"]]
    d.nova(f"etapa{s['n']}", f"Etapa {s['n']} de 12 · {nome}", "",
           outline=f"{s['n']:02d}. {s['t']}", nivel=2)
    c = d.c
    # numero grande + titulo
    c.setFillColor(cor); c.roundRect(M, d.Y(110), 64, 64, 12, stroke=0, fill=1)
    c.setFillColor(BRANCO); c.setFont("UIB", 34)
    c.drawCentredString(M + 32, d.Y(110) + 19, str(s["n"]))
    c.setFillColor(TINTA); c.setFont("UIB", 23)
    c.drawString(M + 80, d.Y(72), s["t"])
    d.texto(s["f"], M + 80, 80, 560, size=11.2, cor=SUAVE, maxh=36)
    # numero-chave
    vx, vw = W - M - 220, 220
    d.caixa(vx, 50, vw, 62, fill=claro, stroke=None, raio=10)
    c.setFillColor(cor); c.setFont("UIB", 25)
    c.drawString(vx + 16, d.Y(88), s["num"][0])
    c.setFont("UI", 9.5); c.setFillColor(TINTA)
    c.drawString(vx + 16, d.Y(104), s["num"][1])
    c.setFont("UISB", 7.5); c.setFillColor(cor)
    c.drawRightString(vx + vw - 12, d.Y(64), "NÚMERO-CHAVE")
    # coluna esquerda: o que acontece + entrada/saida
    lx, lw, top = M, 470, 128
    d.caixa(lx, top, lw, 310, fill=BRANCO)
    c.setFont("UISB", 9); c.setFillColor(cor)
    c.drawString(lx + 18, d.Y(top + 22), "O QUE ACONTECE")
    d.lista(s["a"], lx + 18, top + 36, lw - 36, size=12.2, maxh=180, cor_marc=cor, gap=11)
    ent, sai = IO[s["n"]]
    it = top + 226
    pw = (lw - 36 - 30) / 2
    for k, (rot, val) in enumerate([("ENTRA", ent), ("SAI", sai)]):
        px = lx + 18 + k * (pw + 30)
        d.caixa(px, it, pw, 70, fill=claro, stroke=None, raio=8)
        c.setFont("UISB", 8); c.setFillColor(cor)
        c.drawString(px + 12, d.Y(it + 16), rot)
        d.texto(val, px + 12, it + 24, pw - 24, size=10, font="MONO", cor=TINTA, maxh=42, minsize=7.5)
    d.seta(lx + 18 + pw + 6, it + 35, lx + 18 + pw + 24, it + 35, cor=cor, lw=2)
    # coluna direita: por que + codigo + perguntas
    rx, rw = lx + lw + 14, W - M - (lx + lw + 14)
    hp = Paragraph(esc(s["p"]), estilo(10.8)).wrap(rw - 32, 1000)[1]
    hb = hp + 46
    d.caixa(rx, top, rw, hb, fill=MILHO_CLARO, stroke=None)
    c.setFont("UISB", 9); c.setFillColor(C("#8A6D1F"))
    c.drawString(rx + 16, d.Y(top + 22), "POR QUE FOI FEITO ASSIM?")
    d.texto(s["p"], rx + 16, top + 32, rw - 32, size=10.8)
    t2 = top + hb + 10
    hc = 34 + 15 * len(s["c"])
    d.caixa(rx, t2, rw, hc, fill=C("#EEF0EC"), stroke=None)
    c.setFont("UISB", 9); c.setFillColor(SUAVE)
    c.drawString(rx + 16, d.Y(t2 + 20), "ONDE ESTÁ NO CÓDIGO")
    yy = t2 + 28
    for linha in s["c"]:
        h = d.texto(linha, rx + 16, yy, rw - 32, size=8.8, font="MONO", cor=TINTA, maxh=14, minsize=7)
        yy += h + 2
    nq = len(s["qs"][:3])
    t3 = top + 310 - 18 - nq * 23
    c.setFont("UISB", 9); c.setFillColor(cor)
    c.drawString(rx, d.Y(t3 + 10), "A BANCA PODE PERGUNTAR")
    yy = t3 + 18
    for q in s["qs"][:3]:
        tq = QMAP[q][4]
        d.botao(rx, d.Y(yy + 20), rw, 20, "", q, cor=None)
        d.c.setFillColor(cor); d.c.setFont("UIB", 8.6)
        d.c.drawString(rx + 8, d.Y(yy + 13.5), q.upper())
        d.texto(tq, rx + 36, yy + 4, rw - 50, size=8.8, cor=TINTA, maxh=13, minsize=6.5)
        yy += 23
    barra_etapas(d, s["n"])


def pg_caminhos(d: PDF):
    d.nova("caminhos", "Aprofundar", "Simulação: 4 fotos, 4 caminhos", outline="Parte 2 · Aprofundar")
    d.c.addOutlineEntry("Simulação: 4 caminhos", "caminhos", level=1)
    d.texto("O mesmo pipeline, quatro destinos diferentes. É a melhor forma de explicar os porteiros e o roteador.",
            M, 86, 800, size=10.5, cor=SUAVE)
    casos = [
        ("Foto tremida", VERMELHO, ["Porteiro de qualidade: nitidez < 60", "Para aqui. Nem chama IA."],
         "Essa foto saiu meio embaçada, não consigo ter certeza. Tenta de novo com a mão mais firme, bem em cima do que você quer mostrar?",
         "texto fixo · pipeline/porteiro.py", 6),
        ("Selfie / print", C("#C77D0A"), ["Qualidade: OK", "Porteiro de assunto: Claude diz NÃO", "Para aqui. CNN nem roda."],
         "Não encontrei planta de milho nem inseto nessa foto. Manda uma foto bem de perto da folha, da espiga ou do bicho que está atacando o milho.",
         "texto fixo · pipeline/llm.py", 7),
        ("Lagarta meio de lado", C("#2A6F97"), ["Qualidade OK · assunto SIM", "CNN: lagarta-da-espiga 69%", "Roteador: 50–79% → DÚVIDA"],
         "Pode ser LAGARTA-DA-ESPIGA (69% de confiança), mas não tenho certeza. [sinal de dano para comparar] Consegue tirar outra foto bem em cima da folha ou do bicho, com boa luz?",
         "Claude redige em tom de dúvida (ilustrativo)", 9),
        ("Cartucho bem nítido", VERDE2, ["Qualidade OK · assunto SIM", "CNN: lagarta-do-cartucho 94%", "Roteador: ≥ 80% → DIRETO", "Ficha + Claude redige"],
         "Parece lagarta-do-cartucho (94%). [como reconhecer o dano] O que fazer, do mais barato ao mais caro: 1. ... 2. ...  Isso é uma ajuda, não é receita... Acertei?",
         "Claude + rodapé fixo do código (ilustrativo)", 11),
    ]
    w = (W - 2 * M - 3 * 12) / 4
    for i, (tit, cor, passos, msg, fonte, etapa) in enumerate(casos):
        x = M + i * (w + 12)
        top = 106
        d.caixa(x, top, w, 340, fill=BRANCO)
        d.c.setFillColor(cor); d.c.roundRect(x, d.Y(top + 34), w, 34, 8, stroke=0, fill=1)
        d.c.rect(x, d.Y(top + 34), w, 10, stroke=0, fill=1)
        d.c.setFillColor(BRANCO); d.c.setFont("UIB", 12.5)
        d.c.drawString(x + 14, d.Y(top + 22), tit)
        yy = top + 46
        for p in passos:
            d.c.setFillColor(cor); d.c.circle(x + 18, d.Y(yy + 7), 3.2, stroke=0, fill=1)
            h = d.texto(p, x + 28, yy, w - 40, size=9.6, cor=TINTA)
            yy += h + 6
        # balao de whatsapp
        bt = max(214, yy + 6)
        d.caixa(x + 10, bt, w - 20, 396 - bt, fill=C("#E7F7DC"), stroke=None, raio=10)
        d.c.setFont("UISB", 7.8); d.c.setFillColor(VERDE2)
        d.c.drawString(x + 20, d.Y(bt + 16), "RESPOSTA NO WHATSAPP")
        d.texto(msg, x + 20, bt + 24, w - 40, size=9.6, cor=TINTA, maxh=396 - bt - 50)
        d.texto(fonte, x + 20, 374, w - 40, size=7.6, font="UII", cor=SUAVE, maxh=18)
        d.botao(x + 10, d.Y(top + 334), w - 20, 20, f"Ver etapa {etapa}  ›", f"etapa{etapa}", cor=cor, fonte=8.5)


def pg_treino(d: PDF):
    d.nova("treino", "Aprofundar", "Como o modelo foi treinado", outline="Como o modelo foi treinado", nivel=1)
    etapas = [
        ("Coleta", "~8,2 mil fotos brutas", ["GBIF / iNaturalist (filtrando estágio de vida = larva)",
                                            "KaraAgro AI Maize: recortes pelas caixas anotadas",
                                            "Licença registrada foto a foto"], "q15"),
        ("Limpeza", "−3.239 fotos", ["1.912 pequenas", "1.156 borradas (melhor bloco 4×4)",
                                    "171 duplicadas (pHash)"], "q17"),
        ("Divisão", "70 / 15 / 15", ["Por OBSERVAÇÃO, nunca por foto", "Treino 3.536 · Val 686 · Teste 710",
                                    "Semente fixa 42"], "q16"),
        ("Treino", "MobileNetV3-Large", ["Backbone congelado (ImageNet)", "Peso por classe na perda",
                                        "Augmentation só no treino", "Adam · lr 0,001 · 10 épocas"], "q6"),
        ("Seleção", "melhor F1-macro", ["Escolhe a melhor época na validação", "Teste usado só no fim, 1 vez"], "q8"),
        ("Exportação", "ONNX 16,8 MB", ["Roda sem PyTorch (onnxruntime)", "~2,8 ms por foto em CPU"], "q4"),
    ]
    n = len(etapas)
    gap = 18
    w = (W - 2 * M - (n - 1) * gap) / n
    for i, (tit, dest, itens, q) in enumerate(etapas):
        x = M + i * (w + gap)
        top = 100
        d.caixa(x, top, w, 236, fill=BRANCO)
        d.c.setFillColor(VERDE2); d.c.circle(x + 20, d.Y(top + 22), 11, stroke=0, fill=1)
        d.c.setFillColor(BRANCO); d.c.setFont("UIB", 10); d.c.drawCentredString(x + 20, d.Y(top + 22) - 3.5, str(i + 1))
        d.c.setFillColor(TINTA); d.c.setFont("UIB", 12.5); d.c.drawString(x + 38, d.Y(top + 27), tit)
        d.c.setFillColor(VERDE2); d.c.setFont("UISB", 10.4); d.c.drawString(x + 12, d.Y(top + 54), dest)
        d.lista(itens, x + 10, top + 66, w - 18, size=9.2, maxh=130, gap=5, cor_marc=VERDE3)
        d.botao(x + 10, d.Y(top + 226), w - 20, 19, f"{q.upper()}  ›", q, cor=None, fonte=8.5)
        if i < n - 1:
            d.seta(x + w + 2, top + 118, x + w + gap - 2, top + 118, cor=VERDE3)
    # tabela do dataset
    top = 352
    d.c.setFont("UISB", 9); d.c.setFillColor(SUAVE)
    d.c.drawString(M, d.Y(top + 6), "FOTOS POR CLASSE (DEPOIS DA LIMPEZA)")
    dados = [("lagarta_cartucho", 3266), ("vaquinha", 688), ("milho_sadio", 627), ("lagarta_espiga", 351)]
    maxv = 3266
    bx0, bwmax = M + 130, W - 2 * M - 210
    for i, (cl, v) in enumerate(dados):
        y = top + 18 + i * 21
        d.c.setFont("MONO", 9.5); d.c.setFillColor(TINTA); d.c.drawString(M, d.Y(y + 12), cl)
        d.c.setFillColor(VERDE3 if cl != "lagarta_espiga" else MILHO)
        d.c.roundRect(bx0, d.Y(y + 15), bwmax * v / maxv, 14, 3, stroke=0, fill=1)
        d.c.setFillColor(TINTA); d.c.setFont("UISB", 9.5)
        d.c.drawString(bx0 + bwmax * v / maxv + 6, d.Y(y + 12), f"{v:,}".replace(",", "."))
    d.texto("Desbalanceado ~9×: por isso peso na perda e F1-macro como métrica principal.",
            W - M - 230, top + 70, 230, size=9, font="UII", cor=SUAVE)


def pg_resultados(d: PDF):
    d.nova("resultados", "Aprofundar", "Resultados do modelo (conjunto de teste)",
           outline="Resultados do modelo", nivel=1)
    c = d.c
    # cards topo
    cards = [("86,3%", "acurácia geral", "q7"), ("81,4%", "F1-macro (principal)", "q8"),
             ("93,1%", "acerto quando afirma", "q13"), ("65,4%", "baseline: chutar cartucho", "q7")]
    w = (470 - 30) / 4
    for i, (v, r, q) in enumerate(cards):
        x = M + i * (w + 10)
        d.caixa(x, 92, w, 60, fill=BRANCO)
        c.setFillColor(VERDE2 if i < 3 else SUAVE); c.setFont("UIB", 20); c.drawString(x + 10, d.Y(122), v)
        d.texto(r, x + 10, 127, w - 16, size=8.2, cor=SUAVE, maxh=22)
        d.link(x, d.Y(152), w, 60, q)
    # tabela por classe
    top = 166
    lin = [("Classe", "Precisão", "Revocação", "F1", "Fotos"),
           ("lagarta_cartucho", "98,2%", "84,1%", "90,6%", "464"),
           ("lagarta_espiga", "74,5%", "65,5%", "69,7%", "58"),
           ("milho_sadio", "76,1%", "97,6%", "85,6%", "85"),
           ("vaquinha", "66,7%", "99,0%", "79,7%", "103"),
           ("Média macro", "78,9%", "86,6%", "81,4%", "710")]
    colw = [150, 82, 86, 70, 62]
    d.caixa(M, top, sum(colw) + 20, 26 * len(lin) + 12, fill=BRANCO)
    for i, row in enumerate(lin):
        y = top + 10 + i * 26
        x = M + 10
        if i == 0:
            c.setFillColor(VERDE); c.roundRect(M + 4, d.Y(y + 22), sum(colw) + 12, 22, 4, stroke=0, fill=1)
        elif row[0] == "lagarta_espiga":
            c.setFillColor(MILHO_CLARO); c.rect(M + 4, d.Y(y + 22), sum(colw) + 12, 22, stroke=0, fill=1)
        for j, cel in enumerate(row):
            if i == 0:
                c.setFillColor(BRANCO); c.setFont("UISB", 9.5)
            elif i == len(lin) - 1:
                c.setFillColor(VERDE); c.setFont("UIB", 10)
            else:
                c.setFillColor(TINTA); c.setFont("MONO" if j == 0 else "UI", 9.8 if j else 9.4)
            if j == 0:
                c.drawString(x + 4, d.Y(y + 15), cel)
            else:
                c.drawRightString(x + colw[j] - 6, d.Y(y + 15), cel)
            x += colw[j]
    d.texto("A linha amarela é a classe mais fraca (poucas fotos, parecida com o cartucho). "
            "A vaquinha acha quase todas (revocação 99%), mas recebe 40 cartuchos por engano (precisão 66,7%).",
            M, top + 26 * len(lin) + 22, sum(colw) + 20, size=9.4, cor=SUAVE)
    d.botao(M, d.Y(436), 220, 20, "Q10 · Qual a pior classe?  ›", "q10", cor=None, fonte=8.5)
    d.botao(M + 230, d.Y(436), 240, 20, "Q11 · Por que a vaquinha erra?  ›", "q11", cor=None, fonte=8.5)
    # imagens
    ix = M + sum(colw) + 40
    if IMG_MATRIZ.exists():
        iw = 200; ih = iw * 825 / 975
        c.drawImage(ImageReader(str(IMG_MATRIZ)), ix, d.Y(92 + ih), iw, ih, mask="auto")
        d.texto("Matriz de confusão (teste)", ix, 98 + ih, iw, size=8.5, font="UII", cor=SUAVE, align=TA_CENTER)
    if IMG_LIMIAR.exists():
        jx = ix + 212; jw = W - M - jx; jh = jw * 630 / 1050
        c.drawImage(ImageReader(str(IMG_LIMIAR)), jx, d.Y(92 + jh), jw, jh, mask="auto")
        d.texto("Curva do limiar: cobertura × acerto", jx, 98 + jh, jw, size=8.5, font="UII", cor=SUAVE, align=TA_CENTER)
    # tabela do roteador
    rt = 300
    d.caixa(ix, rt, W - M - ix, 136, fill=BRANCO)
    c.setFont("UISB", 9); c.setFillColor(SUAVE); c.drawString(ix + 14, d.Y(rt + 20), "ROTEADOR NO TESTE")
    rotas = [("DIRETO  ≥ 80%", "550 fotos · 77,5%", "93,1% de acerto", VERDE2),
             ("DÚVIDA  50–79%", "142 fotos · 20,0%", "64,8% de acerto", C("#C77D0A")),
             ("HUMANO  < 50%", "18 fotos · 2,5%", "50,0% de acerto", VERMELHO)]
    for i, (r, a, b, cor) in enumerate(rotas):
        y = rt + 32 + i * 26
        c.setFillColor(cor); c.roundRect(ix + 14, d.Y(y + 18), 110, 18, 9, stroke=0, fill=1)
        c.setFillColor(BRANCO); c.setFont("UIB", 8.5); c.drawCentredString(ix + 69, d.Y(y + 18) + 5.5, r)
        c.setFillColor(TINTA); c.setFont("UI", 9.5); c.drawString(ix + 136, d.Y(y + 13), a)
        c.setFont("UISB", 9.5); c.drawString(ix + 260, d.Y(y + 13), b)
    d.texto("Dos 97 erros do modelo, só 38 seriam afirmados ao produtor: **60,8% barrados**.",
            ix + 14, rt + 112, W - M - ix - 28, size=9.4, cor=TINTA)


def pg_numeros(d: PDF):
    d.nova("numeros", "Aprofundar", "Números para decorar", outline="Números para decorar", nivel=1)
    d.texto("Clique em um número para ver a pergunta em que ele aparece.", M, 86, 600, size=10.5, cor=SUAVE)
    nums = [
        ("4.932", "fotos usadas (após limpeza)", "q15", C("#8A6D1F")),
        ("4", "classes: 3 pragas + milho sadio", "q3", C("#8A6D1F")),
        ("710", "fotos de teste, nunca vistas", "q16", C("#8A6D1F")),
        ("86,3%", "acurácia no teste", "q7", VERDE2),
        ("81,4%", "F1-macro (métrica principal)", "q8", VERDE2),
        ("65,4%", "baseline: chutar sempre cartucho", "q7", VERDE2),
        ("80 / 50", "limiares do roteador (%)", "q13", C("#C77D0A")),
        ("93,1%", "acerto quando o bot afirma", "q13", C("#C77D0A")),
        ("60,8%", "dos erros barrados pelo roteador", "q13", C("#C77D0A")),
        ("2,8 ms", "CNN por foto, em CPU", "q31", C("#2A6F97")),
        ("16,8 MB", "tamanho do modelo ONNX", "q4", C("#2A6F97")),
        ("~3 s", "por chamada ao Claude", "q28", C("#2A6F97")),
        ("R$ 27,50", "custo direto (US$ 5 de crédito)", "q23", C("#6D4C7D")),
        ("70", "palavras no máximo por resposta", "q19", C("#6D4C7D")),
        ("120 s", "evento mais velho que isso é descartado", "q29", C("#6D4C7D")),
        ("69,7%", "F1 da pior classe (lagarta-da-espiga)", "q10", VERMELHO),
    ]
    cols, gap = 4, 12
    w = (W - 2 * M - (cols - 1) * gap) / cols
    h = 80
    for i, (v, r, q, cor) in enumerate(nums):
        linha, col = divmod(i, cols)
        x = M + col * (w + gap)
        top = 104 + linha * (h + 9)
        d.caixa(x, top, w, h, fill=BRANCO)
        d.c.setFillColor(cor); d.c.roundRect(x, d.Y(top + h), 6, h, 3, stroke=0, fill=1)
        d.c.setFont("UIB", 26); d.c.drawString(x + 18, d.Y(top + 40), v)
        d.texto(r, x + 18, top + 50, w - 50, size=9.6, cor=SUAVE, maxh=26)
        d.c.setFont("UISB", 8); d.c.setFillColor(cor)
        d.c.drawRightString(x + w - 10, d.Y(top + 16), q.upper() + " ›")
        d.link(x, d.Y(top + h), w, h, q)


def pg_perguntas_indice(d: PDF):
    d.nova("perguntas", "Banca", "Perguntas prováveis da banca", outline="Parte 3 · Banca")
    d.c.addOutlineEntry("Índice das perguntas", "perguntas", level=1)
    d.c.setFont("UI", 10.2); d.c.setFillColor(SUAVE)
    d.c.drawString(M, d.Y(94), "Clique em uma pergunta para ir à resposta.   ")
    xx = M + pdfmetrics.stringWidth("Clique em uma pergunta para ir à resposta.   ", "UI", 10.2)
    d.c.setFont("SYM", 10.5); d.c.setFillColor(MILHO); d.c.drawString(xx, d.Y(94), "★")
    d.c.setFont("UI", 10.2); d.c.setFillColor(SUAVE)
    d.c.drawString(xx + 14, d.Y(94), "= muito provável. Comece por elas.")
    colunas = [["visao", "modelo"], ["dados", "llm"], ["arq", "etica", "futuro"]]
    colx = [M, M + 302, M + 604]
    cw = 286
    for grupo, x in zip(colunas, colx):
        top = 108
        for cat in grupo:
            nome, cor = CATS[cat]
            d.chip(x, top, nome.upper(), cor, size=8)
            top += 22
            for q in [q for q in QS if q[1] == cat]:
                d.c.setFont("UIB", 8.4); d.c.setFillColor(cor)
                d.c.drawString(x, d.Y(top + 10), q[0].upper())
                if q[3]:
                    d.c.setFont("SYM", 8.5); d.c.setFillColor(MILHO); d.c.drawString(x + 24, d.Y(top + 10), "★")
                d.c.setFont("UI", 8.9); d.c.setFillColor(TINTA)
                txt = q[4]
                while pdfmetrics.stringWidth(txt, "UI", 8.9) > cw - 40:
                    txt = txt[:-2]
                if txt != q[4]:
                    txt = txt.rstrip() + "…"
                d.c.drawString(x + 36, d.Y(top + 10), txt)
                d.link(x, d.Y(top + 13), cw, 14, q[0])
                top += 14.6
            top += 6


def card_q(d: PDF, q, top, h):
    qid, cat, nivel, provavel, perg, curta, mais, evite, etapa = q
    nome, cor = CATS[cat]
    c = d.c
    x, w = M, W - 2 * M
    c.bookmarkPage(qid, fit="XYZ", top=d.Y(top - 4), left=0, zoom=0)
    d.registro[qid] = d.n
    d.caixa(x, top, w, h, fill=BRANCO)
    c.setFillColor(cor); c.roundRect(x, d.Y(top + h), 7, h, 3.5, stroke=0, fill=1)
    # cabecalho
    cx = x + 20
    cx += d.chip(cx, top + 10, qid.upper(), cor, size=8.5) + 5
    cx += d.chip(cx, top + 10, nome, C("#EEF0EC"), cor=cor, size=8) + 5
    corn = {"Básica": VERDE3, "Média": MILHO, "Difícil": VERMELHO}[nivel]
    cx += d.chip(cx, top + 10, nivel, corn, cor=BRANCO if nivel != "Média" else TINTA, size=8) + 5
    if provavel:
        c.setFont("SYM", 10); c.setFillColor(MILHO); c.drawString(cx + 2, d.Y(top + 23), "★")
        c.setFont("UISB", 8.5); c.setFillColor(C("#8A6D1F")); c.drawString(cx + 15, d.Y(top + 23), "muito provável")
    # links a direita
    d.botao(x + w - 104, d.Y(top + 28), 92, 18, "‹  Perguntas", "perguntas", cor=None, fonte=8)
    d.botao(x + w - 204, d.Y(top + 28), 94, 18, f"Etapa {etapa} no fluxo", f"etapa{etapa}", cor=None, fonte=8)
    # pergunta
    hq = d.texto("\u201c" + perg + "\u201d", x + 20, top + 34, w - 40, size=14.5, font="UIB", cor=TINTA, maxh=22)
    corpo_top = top + 34 + hq + 8
    corpo_h = h - (corpo_top - top) - 12
    # colunas
    tem_evite = bool(evite)
    w1 = (w - 40) * (0.50 if tem_evite else 0.56)
    w3 = (w - 40) * 0.19 if tem_evite else 0
    w2 = (w - 40) - w1 - w3 - (24 if tem_evite else 12)
    # resposta curta
    d.caixa(x + 20, corpo_top, w1, corpo_h, fill=VERDE4, stroke=None, raio=7)
    c.setFont("UISB", 8); c.setFillColor(VERDE)
    c.drawString(x + 32, d.Y(corpo_top + 15), "RESPOSTA CURTA · FALE ISTO")
    d.texto(curta, x + 32, corpo_top + 22, w1 - 24, size=12.6, maxh=corpo_h - 30)
    # se pedirem mais
    x2 = x + 20 + w1 + 12
    d.caixa(x2, corpo_top, w2, corpo_h, fill=C("#F1F2EE"), stroke=None, raio=7)
    c.setFont("UISB", 8); c.setFillColor(SUAVE)
    c.drawString(x2 + 12, d.Y(corpo_top + 15), "SE PEDIREM MAIS DETALHE")
    d.texto(mais, x2 + 12, corpo_top + 22, w2 - 24, size=11.2, cor=TINTA, maxh=corpo_h - 30)
    if tem_evite:
        x3 = x2 + w2 + 12
        d.caixa(x3, corpo_top, w3, corpo_h, fill=VERMELHO_CLARO, stroke=None, raio=7)
        c.setFont("UISB", 8); c.setFillColor(VERMELHO)
        c.drawString(x3 + 12, d.Y(corpo_top + 15), "CUIDADO")
        d.texto(evite, x3 + 12, corpo_top + 22, w3 - 24, size=11.2, cor=C("#7A2219"), maxh=corpo_h - 30)


def pgs_perguntas(d: PDF):
    vistos = set()
    for i in range(0, len(QS), 2):
        par = QS[i:i + 2]
        cats = " · ".join(dict.fromkeys(CATS[q[1]][0] for q in par))
        d.nova(f"qpg{i}", f"Banca · {cats}", "")
        altura = 206
        for k, q in enumerate(par):
            top = 50 + k * (altura + 10)
            if q[1] not in vistos:
                vistos.add(q[1])
                chave = f"cat_{q[1]}"
                d.c.bookmarkPage(chave, fit="XYZ", top=d.Y(top - 4), left=0, zoom=0)
                d.registro[chave] = d.n
                d.c.addOutlineEntry(CATS[q[1]][0], chave, level=1)
            card_q(d, q, top, altura)


def pg_limitacoes(d: PDF):
    d.nova("limitacoes", "Banca", "Limitações: como falar delas com segurança",
           outline="Limitações", nivel=1)
    d.texto("A banca valoriza quem conhece os limites do próprio projeto. Use a fórmula: "
            "**reconhecer → explicar a causa → dizer o que já mitiga → próximo passo**.",
            M, 86, W - 2 * M, size=10.8, cor=SUAVE)
    itens = [
        ("Sem fotos de campo da região", "Avaliado só em fotos públicas.", "Teste com 710 fotos nunca vistas + feedback no bot.", "Coletar fotos locais só para teste."),
        ("Lagarta-da-espiga mais fraca", "Só 351 fotos; parecida com o cartucho.", "Roteador manda metade para \"dúvida\".", "Mais dados dessa classe."),
        ("Cigarrinha e elasmo fora", "~46 e 17 fotos públicas; sintoma tardio.", "Escopo honesto: 4 classes medidas.", "Alerta por calendário; 5ª classe."),
        ("Sem fila durável", "BackgroundTasks perde a tarefa se cair.", "Volume de protótipo; respostas rápidas.", "Redis + RQ com workers."),
        ("WhatsApp não oficial", "Meta bloqueou envio BR no teste (130497).", "Canal isolado do pipeline (api/canais).", "Migrar para a API oficial."),
        ("Estado em memória", "IDs e último diagnóstico no processo.", "Suficiente para 1 instância.", "Banco/Redis para escalar."),
        ("Softmax não calibrada", "Confiança pode ser otimista.", "Limiar validado empiricamente no teste.", "Temperature scaling."),
    ]
    heads = ["Limitação", "Por quê", "O que já mitiga", "Próximo passo"]
    colw = [210, 250, 250, W - 2 * M - 710]
    top = 118
    x = M
    d.c.setFillColor(VERDE); d.c.roundRect(M, d.Y(top + 24), W - 2 * M, 24, 5, stroke=0, fill=1)
    for hd, cw in zip(heads, colw):
        d.c.setFillColor(BRANCO); d.c.setFont("UISB", 9.5); d.c.drawString(x + 12, d.Y(top + 16), hd)
        x += cw
    top += 28
    for i, row in enumerate(itens):
        rh = 42
        d.caixa(M, top, W - 2 * M, rh, fill=BRANCO if i % 2 == 0 else C("#FAF9F5"), stroke=LINHA, raio=4)
        x = M
        for j, (cel, cw) in enumerate(zip(row, colw)):
            d.texto(cel, x + 12, top + 7, cw - 20, size=9.6 if j else 10, font="UISB" if j == 0 else "UI",
                    cor=TINTA if j != 3 else VERDE2, maxh=rh - 10)
            x += cw
        top += rh + 4


def pg_glossario(d: PDF):
    d.nova("glossario", "Banca", "Glossário rápido", outline="Glossário", nivel=1)
    cols = 2
    w = (W - 2 * M - 20) / cols
    porcol = (len(GLOSSARIO) + 1) // 2
    for i, (termo, defi) in enumerate(GLOSSARIO):
        col, lin = divmod(i, porcol)
        x = M + col * (w + 20)
        top = 92 + lin * 36
        d.c.setFont("UIB", 10.2); d.c.setFillColor(VERDE2)
        d.c.drawString(x, d.Y(top + 12), termo)
        d.texto(defi, x + 130, top + 1, w - 130, size=9.2, cor=TINTA, maxh=33)
        d.c.setStrokeColor(LINHA); d.c.setLineWidth(0.5)
        d.c.line(x, d.Y(top + 34), x + w, d.Y(top + 34))


QUIZ = [
    ("Quem decide qual é a praga: a CNN ou o Claude?", "A CNN (MobileNetV3). O Claude só redige.", "q20"),
    ("Qual a acurácia no teste? E o acerto quando o bot afirma?", "86,3%. Quando afirma (≥ 80%): 93,1%.", "q7"),
    ("Por que F1-macro?", "Classes desbalanceadas; dá peso igual a cada classe.", "q8"),
    ("O que acontece com confiança de 65%?", "Rota DÚVIDA: \"pode ser X\", pede outra foto.", "q13"),
    ("Por que uma selfie não vira \"vaquinha\"?", "Porteiro de assunto: Claude responde SIM/NÃO antes da CNN.", "q12"),
    ("Como evitaram vazamento entre treino e teste?", "Divisão por observação, não por foto.", "q16"),
    ("Isso é RAG? Usa banco vetorial?", "RAG com filtro estruturado; sem banco vetorial.", "q21"),
    ("Por que o webhook responde antes de analisar?", "Claude leva ~3 s; BackgroundTasks. Produção: Redis/RQ.", "q28"),
    ("Quem garante o aviso \"não é receita\"?", "O código (RODAPE_FIXO), não o LLM.", "q19"),
    ("Qual a principal limitação?", "Sem fotos de campo da região; avaliado em fotos públicas.", "q34"),
]


def pg_quiz(d: PDF):
    d.nova("quiz", "Banca", "Teste-se em 3 minutos", outline="Teste-se (quiz)", nivel=1)
    d.texto("Responda em voz alta, como se fosse para a banca. Depois confira no gabarito ou clique na pergunta.",
            M, 86, W - 2 * M, size=10.5, cor=SUAVE)
    w = (W - 2 * M - 16) / 2
    for i, (p, _, q) in enumerate(QUIZ):
        col, lin = divmod(i, 5)
        x = M + col * (w + 16)
        top = 110 + lin * 64
        d.caixa(x, top, w, 56, fill=BRANCO)
        d.c.setFillColor(VERDE2); d.c.circle(x + 24, d.Y(top + 28), 13, stroke=0, fill=1)
        d.c.setFillColor(BRANCO); d.c.setFont("UIB", 11); d.c.drawCentredString(x + 24, d.Y(top + 28) - 4, str(i + 1))
        d.texto(p, x + 48, top + 11, w - 140, size=10.6, font="UISB", maxh=36)
        d.botao(x + w - 82, d.Y(top + 38), 70, 20, f"{q.upper()} ›", q, cor=None, fonte=8.5)
    d.botao(W / 2 - 110, d.Y(446), 220, 26, "Ver o gabarito  ›", "gabarito", cor=VERDE2, fonte=10)


def pg_gabarito(d: PDF):
    d.nova("gabarito", "Banca", "Gabarito do quiz", outline="Gabarito", nivel=1)
    w = (W - 2 * M - 16) / 2
    for i, (p, r, q) in enumerate(QUIZ):
        col, lin = divmod(i, 5)
        x = M + col * (w + 16)
        top = 92 + lin * 68
        d.caixa(x, top, w, 60, fill=VERDE4, stroke=None)
        d.c.setFillColor(VERDE2); d.c.setFont("UIB", 11); d.c.drawString(x + 14, d.Y(top + 20), f"{i + 1}.")
        d.texto(p, x + 36, top + 8, w - 50, size=8.8, cor=SUAVE, maxh=14)
        d.texto(r, x + 36, top + 25, w - 50, size=10.6, font="UISB", cor=VERDE, maxh=30)
        d.link(x, d.Y(top + 60), w, 60, q)
    d.botao(W / 2 - 110, d.Y(446), 220, 26, "‹  Voltar ao quiz", "quiz", cor=None, fonte=10)


def pg_roteiro(d: PDF):
    d.nova("roteiro", "Banca", "Roteiro de fala + checklist do dia", outline="Roteiro e checklist", nivel=1)
    # roteiro de 1 minuto
    w1 = 520
    d.caixa(M, 92, w1, 350, fill=BRANCO)
    d.c.setFont("UISB", 9); d.c.setFillColor(VERDE2)
    d.c.drawString(M + 18, d.Y(114), "EXPLICANDO O FLUXO EM ~1 MINUTO (COM O MAPA NA TELA)")
    fala = [
        "**1.** O produtor manda a foto no WhatsApp. Não precisa instalar nada.",
        "**2.** A Evolution API, em Docker, recebe e chama o nosso webhook pelo ngrok. O FastAPI filtra mensagens antigas, de grupo e duplicadas, responde na hora e processa em segundo plano.",
        "**3.** Dois porteiros: um confere se a foto está nítida; o outro, com o Claude, só diz se tem planta ou inseto.",
        "**4.** A CNN, uma MobileNetV3 que nós treinamos com ~5 mil fotos, decide a praga em 3 ms e dá uma confiança.",
        "**5.** O roteador decide: acima de 80% afirma, entre 50 e 80% pede outra foto, abaixo manda ao técnico. Quando afirma, acerta 93%.",
        "**6.** O código busca a ficha da praga e o Claude só resume em linguagem simples, sem dose nem produto. O aviso de que não é receita é colado pelo código.",
        "**7.** O produtor responde se acertamos, e isso fica registrado para medir no mundo real.",
    ]
    d.lista(fala, M + 18, 128, w1 - 36, size=12, maxh=304, marcador="", gap=8)
    # checklist
    x2 = M + w1 + 16
    w2 = W - M - x2
    d.caixa(x2, 92, w2, 214, fill=MILHO_CLARO, stroke=None)
    d.c.setFont("UISB", 9); d.c.setFillColor(C("#8A6D1F"))
    d.c.drawString(x2 + 16, d.Y(114), "CHECKLIST ANTES DE APRESENTAR")
    check = [
        "Notebook com `checkpoints/modelo.onnx` + `classes.json` e `whatsapp/.env` (fora do Git).",
        "Docker Desktop aberto → rodar `whatsapp/ligar.bat`.",
        "Conferir a instância (Twin) conectada; se pedir, escanear o QR.",
        "Mandar 1 foto de teste antes da banca entrar.",
        "Ligar perto da hora, para não acumular fila.",
    ]
    d.lista(check, x2 + 16, 128, w2 - 32, size=10.6, maxh=170, marcador="☐", cor_marc=C("#8A6D1F"), gap=6, fonte_marc="SYM")
    d.caixa(x2, 316, w2, 126, fill=VERMELHO_CLARO, stroke=None)
    d.c.setFont("UISB", 9); d.c.setFillColor(VERMELHO)
    d.c.drawString(x2 + 16, d.Y(338), "SE A DEMO FALHAR AO VIVO")
    plano = [
        "Mantenha a calma e mostre o print da conversa real (docs/img/07-conversa-real.png) e o log (08).",
        "Diga o que falhou (rede, ngrok, QR) — mostra domínio da arquitetura.",
        "Volte ao mapa do fluxo e explique pela tela.",
    ]
    d.lista(plano, x2 + 16, 348, w2 - 32, size=9.2, maxh=88, cor_marc=VERMELHO, gap=4)


# ══════════════════════════════════════════════════════════════════════════════

def construir(destino, pagina_de=None):
    d = PDF(destino, pagina_de)
    pg_capa(d)
    pg_indice(d)
    pg_pitch(d)
    pg_mapa(d)
    for s in STEPS:
        pg_etapa(d, s)
    pg_caminhos(d)
    pg_treino(d)
    pg_resultados(d)
    pg_numeros(d)
    pg_perguntas_indice(d)
    pgs_perguntas(d)
    pg_limitacoes(d)
    pg_glossario(d)
    pg_quiz(d)
    pg_gabarito(d)
    pg_roteiro(d)
    d.salvar()
    return d.registro


if __name__ == "__main__":
    import tempfile, os
    tmp = Path(tempfile.gettempdir()) / "_agrobot_passada1.pdf"
    paginas = construir(tmp)          # 1a passada: descobre o numero de cada pagina
    os.remove(tmp)
    construir(SAIDA, paginas)         # 2a passada: indice com numeros e total certo
    print(f"OK: {SAIDA}  ({max(paginas.values())} páginas)")
