#!/usr/bin/env python3
"""
06_relatorio_validacao.py — gera as tabelas de validacao para o relatorio.

Tudo e' calculado na hora a partir dos dados e do modelo exportado
(checkpoints/modelo.onnx) — nada e' copiado a mao. A avaliacao usa o
conjunto de TESTE (dados/split/teste), que o treino nunca viu: o val foi
usado pra escolher o melhor epoch, entao reportar o val seria otimista.

Secoes (cada uma cabe num print de tela):
    dataset    volume por classe, split e fonte/licenca
    modelo     acuracia, precisao/revocacao/F1 por classe, matriz de confusao
    roteador   quanto cai em cada rota e quanto acerta em cada uma
    limiar     varredura do limiar "direto": cobertura x acuracia
    porteiro   quantas fotos do teste o filtro de qualidade deixa passar
    latencia   tempo de inferencia em CPU
    demo       resposta final do bot para uma foto de cada classe

Uso:
    python scripts/06_relatorio_validacao.py                 # tudo
    python scripts/06_relatorio_validacao.py --secao modelo  # uma secao
    python scripts/06_relatorio_validacao.py --secao demo --com-llm

Saida extra (imagens para o relatorio):
    checkpoints/relatorio/matriz_confusao_teste.png
    checkpoints/relatorio/curva_limiar.png
"""

import argparse
import csv
import logging
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from pipeline import porteiro  # noqa: E402
from pipeline.modelo import _carregar, _preprocessar  # noqa: E402
from pipeline.roteador import ALTA, MEDIA, decidir_rota  # noqa: E402

DIR_SPLIT = RAIZ / "dados" / "split"
DIR_SAIDA = RAIZ / "checkpoints" / "relatorio"
EXTENSOES = {".jpg", ".jpeg", ".png", ".webp"}


# ---------------------------------------------------------------- formatacao

def tabela(cabecalho, linhas, titulo=None):
    """Tabela em texto com bordas, alinhada — pensada pra print de tela."""
    linhas = [[str(c) for c in l] for l in linhas]
    larguras = [max(len(str(cabecalho[i])), *(len(l[i]) for l in linhas if l[0] != "---"))
                for i in range(len(cabecalho))]
    sep = "+" + "+".join("-" * (w + 2) for w in larguras) + "+"

    def fmt(l):
        celulas = []
        for i, c in enumerate(l):
            # numero alinha a direita, texto a esquerda
            num = c.replace(".", "").replace("%", "").replace(",", "").replace(" ms", "").strip().isdigit()
            celulas.append(c.rjust(larguras[i]) if num else c.ljust(larguras[i]))
        return "| " + " | ".join(celulas) + " |"

    if titulo:
        print(f"\n{titulo}")
    print(sep)
    print(fmt([str(c) for c in cabecalho]))
    print(sep.replace("-", "="))
    for l in linhas:
        if l and l[0] == "---":
            print(sep)
            continue
        print(fmt(l))
    print(sep)


def titulo_secao(texto):
    print("\n" + "=" * 72)
    print(f"  {texto}")
    print("=" * 72)


def pct(x):
    return f"{100 * x:.1f}%"


# ---------------------------------------------------------------- dados

def listar(dir_):
    return sorted(p for p in dir_.iterdir() if p.suffix.lower() in EXTENSOES)


def classes_do_split():
    return sorted(p.name for p in (DIR_SPLIT / "treino").iterdir() if p.is_dir())


_cache_predicoes = None


def predizer_teste():
    """Roda o modelo ONNX em todo o conjunto de teste (uma vez so)."""
    global _cache_predicoes
    if _cache_predicoes is not None:
        return _cache_predicoes

    sessao, classes = _carregar()
    y_verd, y_prev, confs, caminhos = [], [], [], []
    for idx, classe in enumerate(classes):
        for arq in listar(DIR_SPLIT / "teste" / classe):
            img = Image.open(arq)
            logits = sessao.run(None, {"foto": _preprocessar(img)})[0][0]
            probs = np.exp(logits - logits.max())
            probs /= probs.sum()
            y_verd.append(idx)
            y_prev.append(int(probs.argmax()))
            confs.append(float(probs.max()))
            caminhos.append(arq)
    _cache_predicoes = (classes, np.array(y_verd), np.array(y_prev),
                        np.array(confs), caminhos)
    return _cache_predicoes


# ---------------------------------------------------------------- secoes

def secao_dataset():
    titulo_secao("1. DATASET — volume por classe e por conjunto")
    classes = classes_do_split()
    linhas, tot = [], Counter()
    for c in classes:
        n = {s: len(listar(DIR_SPLIT / s / c)) for s in ("treino", "val", "teste")}
        soma = sum(n.values())
        tot.update(n)
        tot["total"] += soma
        linhas.append([c, n["treino"], n["val"], n["teste"], soma])
    linhas.append(["---"])
    linhas.append(["TOTAL", tot["treino"], tot["val"], tot["teste"], tot["total"]])
    tabela(["Classe", "Treino", "Validacao", "Teste", "Total"], linhas,
           "Divisao treino/val/teste (por observacao, sem vazamento):")

    t = tot["total"]
    print(f"Proporcao: treino {pct(tot['treino'] / t)} | val {pct(tot['val'] / t)}"
          f" | teste {pct(tot['teste'] / t)}")

    desc = RAIZ / "dados" / "descartado"
    if desc.exists():
        motivos = sorted(p.name for p in desc.iterdir() if p.is_dir())
        linhas, tot = [], Counter()
        for c in classes:
            n = [sum(1 for a in (desc / m / c).glob("*") if a.suffix.lower() in EXTENSOES)
                 if (desc / m / c).exists() else 0 for m in motivos]
            tot.update(dict(zip(motivos, n)))
            linhas.append([c, *n, sum(n)])
        linhas.append(["---"])
        linhas.append(["TOTAL", *(tot[m] for m in motivos), sum(tot.values())])
        tabela(["Classe", *motivos, "Total"], linhas,
               "Limpeza automatica (scripts/02_limpar_duplicatas.py) — fotos removidas:")

    creditos = RAIZ / "dados" / "creditos.csv"
    if creditos.exists():
        fontes, licencas = Counter(), Counter()
        with open(creditos, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                fontes[r["fonte"]] += 1
                lic = r["licenca"].lower()
                if "zero" in lic or "cc0" in lic:
                    lic = "CC0 (dominio publico)"
                elif "nc" in lic:
                    lic = "CC BY-NC* (uso local)"
                elif "sa" in lic:
                    lic = "CC BY-SA"
                else:
                    lic = "CC BY"
                licencas[lic] += 1
        tabela(["Fonte", "Registros"], fontes.most_common(),
               "Rastreabilidade — origem de cada foto (dados/creditos.csv):")
        tabela(["Licenca", "Registros"], licencas.most_common())


def secao_modelo():
    from sklearn.metrics import (accuracy_score, confusion_matrix,
                                 f1_score, precision_recall_fscore_support)

    titulo_secao("2. CLASSIFICADOR (MobileNetV3-Large) — conjunto de TESTE")
    classes, yv, yp, confs, _ = predizer_teste()

    p, r, f1, sup = precision_recall_fscore_support(yv, yp, zero_division=0)
    linhas = [[c, pct(p[i]), pct(r[i]), pct(f1[i]), sup[i]]
              for i, c in enumerate(classes)]
    linhas.append(["---"])
    linhas.append(["Media macro", pct(p.mean()), pct(r.mean()), pct(f1.mean()), sup.sum()])
    tabela(["Classe", "Precisao", "Revocacao", "F1", "Fotos"], linhas,
           "Metricas por classe:")

    print(f"Acuracia geral ......... {pct(accuracy_score(yv, yp))}")
    print(f"F1-macro ............... {pct(f1_score(yv, yp, average='macro'))}"
          "   <- metrica principal (nao premia so acertar a classe majoritaria)")
    majoritaria = Counter(yv.tolist()).most_common(1)[0]
    print(f"Baseline 'chutar sempre {classes[majoritaria[0]]}': "
          f"{pct(majoritaria[1] / len(yv))} de acuracia")

    cm = confusion_matrix(yv, yp)
    abrev = [c[:12] for c in classes]
    linhas = [[abrev[i], *cm[i]] for i in range(len(classes))]
    tabela(["Real \\ Previsto", *abrev], linhas, "Matriz de confusao (teste):")

    DIR_SAIDA.mkdir(parents=True, exist_ok=True)
    _salvar_matriz(cm, classes, DIR_SAIDA / "matriz_confusao_teste.png")
    print(f"Imagem salva: {DIR_SAIDA.relative_to(RAIZ)}/matriz_confusao_teste.png")


def secao_roteador():
    titulo_secao("3. ROTEADOR DE CONFIANCA — 'errar para o lado do nao sei'")
    classes, yv, yp, confs, _ = predizer_teste()
    rotas = np.array([decidir_rota(c) for c in confs])
    acerto = yv == yp

    descricao = {
        "direto": f">= {ALTA:.0%}: afirma o diagnostico",
        "duvida": f"{MEDIA:.0%}-{ALTA:.0%}: pede outra foto",
        "humano": f"< {MEDIA:.0%}: encaminha p/ Casa da Agricultura",
    }
    linhas = []
    for rota in ("direto", "duvida", "humano"):
        m = rotas == rota
        n = int(m.sum())
        acc = pct(acerto[m].mean()) if n else "-"
        linhas.append([rota, descricao[rota], n, pct(n / len(rotas)), acc])
    tabela(["Rota", "Regra", "Fotos", "% do teste", "Acuracia na rota"], linhas)

    m = rotas == "direto"
    erros_afirmados = int((~acerto & m).sum())
    erros_total = int((~acerto).sum())
    print(f"Erros do modelo no teste ........................ {erros_total}")
    print(f"Desses, quantos o bot AFIRMARIA ao produtor ..... {erros_afirmados}")
    if erros_total:
        print(f"-> o roteador segura {pct(1 - erros_afirmados / erros_total)} dos erros "
              "antes de virarem recomendacao errada")

    # acuracia da rota direto por classe
    linhas = []
    for i, c in enumerate(classes):
        mc = (yv == i)
        md = mc & m
        linhas.append([c, int(mc.sum()), pct(md.sum() / mc.sum()),
                       pct(acerto[md].mean()) if md.sum() else "-"])
    tabela(["Classe real", "Fotos", "% resp. direta", "Acuracia direta"], linhas,
           "Por classe:")


def secao_limiar():
    titulo_secao("4. VARREDURA DO LIMIAR — cobertura x acuracia")
    classes, yv, yp, confs, _ = predizer_teste()
    acerto = yv == yp
    limiares = [0.0, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95]
    linhas, cob, acc = [], [], []
    for t in limiares:
        m = confs >= t
        c = m.mean()
        a = acerto[m].mean() if m.sum() else float("nan")
        cob.append(c)
        acc.append(a)
        marca = "  <- atual" if abs(t - ALTA) < 1e-9 else ""
        linhas.append([f"{t:.2f}{marca}", int(m.sum()), pct(c), pct(a), int((~acerto & m).sum())])
    tabela(["Limiar", "Respondidas", "Cobertura", "Acuracia", "Erros afirmados"], linhas,
           "Se o bot so respondesse quando a confianca >= limiar:")

    DIR_SAIDA.mkdir(parents=True, exist_ok=True)
    _salvar_curva(confs, acerto, DIR_SAIDA / "curva_limiar.png")
    print(f"Imagem salva: {DIR_SAIDA.relative_to(RAIZ)}/curva_limiar.png")


def secao_porteiro():
    titulo_secao("5. PORTEIRO DE QUALIDADE — filtro antes da CNN")
    classes = classes_do_split()
    linhas, tot = [], Counter()
    for c in classes:
        cont = Counter()
        for arq in listar(DIR_SPLIT / "teste" / c):
            ok, motivo = porteiro.verificar(Image.open(arq))
            cont["ok" if ok else motivo] += 1
        n = sum(cont.values())
        tot.update(cont)
        linhas.append([c, n, cont["ok"], cont["borrada"], cont["pequena"], pct(cont["ok"] / n)])
    n = sum(tot.values())
    linhas.append(["---"])
    linhas.append(["TOTAL", n, tot["ok"], tot["borrada"], tot["pequena"], pct(tot["ok"] / n)])
    tabela(["Classe", "Fotos", "Aprovadas", "Borradas", "Pequenas", "% aprovada"], linhas)
    print(f"Regras: lado minimo {porteiro.LADO_MINIMO}px | "
          f"nitidez (var. Laplaciano, melhor bloco 4x4) >= {porteiro.LIMIAR_BORRAO}")
    print("Esperado: quase tudo aprova — o teste ja passou pela limpeza do dataset.")


def secao_latencia(n=200):
    titulo_secao("6. DESEMPENHO — tempo de resposta em CPU")
    sessao, _ = _carregar()
    _, _, _, _, caminhos = predizer_teste()
    amostra = caminhos[:: max(1, len(caminhos) // n)][:n]
    imgs = [Image.open(p).convert("RGB") for p in amostra]

    t_pre, t_inf, t_port = [], [], []
    for img in imgs:
        t0 = time.perf_counter()
        porteiro.verificar(img)
        t1 = time.perf_counter()
        x = _preprocessar(img)
        t2 = time.perf_counter()
        sessao.run(None, {"foto": x})
        t3 = time.perf_counter()
        t_port.append(t1 - t0)
        t_pre.append(t2 - t1)
        t_inf.append(t3 - t2)

    def ms(v, q):
        return f"{1000 * np.percentile(v, q):.1f} ms"

    total = np.array(t_port) + np.array(t_pre) + np.array(t_inf)
    linhas = [
        ["Porteiro (qualidade)", ms(t_port, 50), ms(t_port, 95)],
        ["Pre-processamento", ms(t_pre, 50), ms(t_pre, 95)],
        ["Inferencia CNN (ONNX)", ms(t_inf, 50), ms(t_inf, 95)],
        ["---"],
        ["Total sem LLM", ms(total, 50), ms(total, 95)],
    ]
    tabela(["Etapa", "Mediana", "p95"], linhas, f"{len(imgs)} fotos do teste, CPU:")
    tam = (RAIZ / "checkpoints" / "modelo.onnx").stat().st_size / 1e6
    print(f"Tamanho do modelo ONNX: {tam:.1f} MB")
    print("Limite do webhook do WhatsApp: responder em < 1 s -> folga ampla.")


def secao_demo(com_llm):
    titulo_secao("7. DEMONSTRACAO — resposta final que o produtor recebe")
    if com_llm:
        _carregar_env()
    else:
        os.environ.pop("ANTHROPIC_API_KEY", None)
        # sem chave o LLM falha de proposito e cai no fallback mecanico;
        # silencia o traceback esperado pra nao poluir o print
        logging.getLogger("pipeline.resposta").setLevel(logging.CRITICAL)
    modo = "LLM (Claude Haiku 4.5) redigindo" if com_llm else "fallback mecanico, sem LLM"
    print(f"Modo: {modo}")

    from pipeline.diagnostico import diagnosticar
    from pipeline.modelo import classificar

    classes, yv, yp, confs, caminhos = predizer_teste()
    for i, c in enumerate(classes):
        # foto do teste com a maior confianca correta — exemplo representativo
        idx = [k for k in range(len(yv)) if yv[k] == i and yp[k] == i]
        if not idx:
            continue
        k = max(idx, key=lambda j: confs[j])
        img = Image.open(caminhos[k])
        prev, conf = classificar(img)
        print("\n" + "-" * 72)
        print(f"Foto: {caminhos[k].relative_to(RAIZ)}")
        print(f"Classe real: {c} | CNN: {prev} ({conf:.0%}) | rota: {decidir_rota(conf)}")
        print("-" * 72)
        print(diagnosticar(img))


# ---------------------------------------------------------------- graficos

def _salvar_matriz(cm, classes, caminho):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    norm = cm / cm.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    im = ax.imshow(norm, cmap="Greens", vmin=0, vmax=1)
    ax.set_xticks(range(len(classes)))
    ax.set_yticks(range(len(classes)))
    ax.set_xticklabels(classes, rotation=30, ha="right")
    ax.set_yticklabels(classes)
    ax.set_xlabel("Previsto")
    ax.set_ylabel("Real")
    ax.set_title("Matriz de confusao — conjunto de teste")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, f"{cm[i, j]}\n({norm[i, j]:.0%})", ha="center", va="center",
                    fontsize=9, color="white" if norm[i, j] > 0.5 else "black")
    fig.colorbar(im, ax=ax, label="Fracao da classe real")
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


def _salvar_curva(confs, acerto, caminho):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ts = np.linspace(0, 0.99, 100)
    cob = [(confs >= t).mean() for t in ts]
    acc = [acerto[confs >= t].mean() if (confs >= t).any() else np.nan for t in ts]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(ts, acc, label="Acuracia das respostas dadas", color="#2e7d32", lw=2)
    ax.plot(ts, cob, label="Cobertura (% de fotos respondidas)", color="#1565c0", lw=2)
    ax.axvline(ALTA, color="gray", ls="--", lw=1)
    ax.text(ALTA + 0.01, 0.05, f"limiar atual = {ALTA:.2f}", color="gray")
    ax.set_xlabel("Limiar de confianca")
    ax.set_ylim(0, 1.02)
    ax.set_title("Troca entre responder mais e errar menos (teste)")
    ax.legend(loc="lower left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


def _carregar_env():
    env = RAIZ / ".env"
    if not env.exists():
        return
    for linha in env.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            k, v = linha.split("=", 1)
            if v.strip():
                os.environ.setdefault(k.strip(), v.strip())


# ---------------------------------------------------------------- main

SECOES = ["dataset", "modelo", "roteador", "limiar", "porteiro", "latencia", "demo"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--secao", choices=SECOES, action="append",
                    help="roda so essa secao (pode repetir); padrao: todas")
    ap.add_argument("--com-llm", action="store_true",
                    help="na demo, usa o Claude (le ANTHROPIC_API_KEY do .env)")
    args = ap.parse_args()

    # emoji das respostas quebra em console Windows cp1252
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    for s in args.secao or SECOES:
        if s == "demo":
            secao_demo(args.com_llm)
        else:
            globals()[f"secao_{s}"]()
    print()


if __name__ == "__main__":
    main()
