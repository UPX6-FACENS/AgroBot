"""Monta a resposta final — AINDA SEM LLM.

docs/02-arquitetura.md secao 5 descreve um LLM que so REDIGE, a partir do
trecho recuperado, num template fixo de ~90 palavras. Ainda nao temos
chave de API de LLM configurada (decisao do time: qual provedor, quem
paga) — enquanto isso nao acontece, esta versao monta a resposta direto
a partir do texto da ficha (que ja foi escrito em linguagem simples,
pensando no produtor, entao serve como substituto razoavel).

Trocar isto por uma chamada de LLM de verdade e' so questao de: pegar a
ficha inteira (kb.buscar_ficha), pedir pro LLM redigir seguindo as regras
da secao 5, e usar o resultado aqui em vez do texto mecanico."""

import re

from pipeline import kb
from pipeline.roteador import decidir_rota


def _primeiro_item_numerado(texto: str) -> str:
    """Pega o texto do item '1.' de uma lista numerada em markdown e
    limpa negrito/quebra de linha — usado pra extrair 'o primeiro sinal'
    e 'a primeira medida' sem precisar resumir com LLM."""
    m = re.search(r"1\.\s+(.+?)(?:\n\d+\.|\Z)", texto, re.DOTALL)
    trecho = m.group(1) if m else texto
    trecho = re.sub(r"\*\*(.+?)\*\*", r"\1", trecho)
    trecho = re.sub(r"\s+", " ", trecho).strip()
    return trecho


def _nome_curto(ficha: dict) -> str:
    """A ficha as vezes junta dois nomes na mesma frase (ex.: 'Vaquinha
    (o besouro adulto), larva-alfinete (a larva no solo)') — pega so o
    primeiro, sem negrito nem parenteses."""
    nome = ficha.get("nome_popular", "").split("\n")[0]
    nome = re.sub(r"\*\*(.+?)\*\*", r"\1", nome)
    primeira_frase = nome.split(".")[0]
    primeiro_nome = primeira_frase.split(",")[0]
    primeiro_nome = re.sub(r"\(.+?\)", "", primeiro_nome)
    return primeiro_nome.strip()


def montar_resposta(classe: str, confianca: float) -> str:
    rota = decidir_rota(confianca)
    pct = int(round(confianca * 100))

    if rota == "humano":
        return (
            "😕 Não consegui identificar essa foto com segurança.\n\n"
            "Melhor levar uma folha ou uma foto bem nítida na Casa da "
            "Agricultura / CATI mais perto de você."
        )

    if classe == "milho_sadio":
        if rota == "direto":
            return (
                f"🌽 Não vi sinal de praga nessa planta ({pct}% de confiança). "
                "Parece saudável!\n\n"
                "Se notar folha raspada, furada ou planta murchando, manda outra foto."
            )
        return (
            f"🌽 Parece que está saudável ({pct}% de confiança), mas não tenho certeza.\n\n"
            "Consegue tirar outra foto mais de perto da folha?"
        )

    ficha = kb.buscar_ficha(classe)
    if ficha is None:
        return (
            "Identifiquei algo na foto, mas não achei a ficha de manejo "
            "dessa praga na nossa base. Avisa o time do projeto."
        )

    nome = _nome_curto(ficha)
    dano = _primeiro_item_numerado(ficha.get("como_reconhecer_o_dano", ""))
    manejo = _primeiro_item_numerado(ficha.get("manejo_ordenado_por_custo", ""))

    if rota == "direto":
        return (
            f"🐛 Parece {nome.upper()} no milho ({pct}% de confiança).\n\n"
            f"O que ela faz: {dano}\n\n"
            "O que fazer, começando pelo mais barato:\n"
            f"1. {manejo}\n"
            "2. Se estiver tomando conta, leve uma folha na Casa da Agricultura.\n\n"
            "⚠️ Isso é uma ajuda, não é receita. Para veneno, é preciso receituário agronômico.\n\n"
            "Acertei? 👍 👎"
        )

    # rota == "duvida"
    return (
        f"🤔 Pode ser {nome.upper()} ({pct}% de confiança), mas não tenho certeza.\n\n"
        f"Sinal pra confirmar: {dano}\n\n"
        "Consegue tirar outra foto bem em cima da folha ou do bicho, com boa luz?"
    )
