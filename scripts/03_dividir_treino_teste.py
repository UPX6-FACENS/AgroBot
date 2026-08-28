#!/usr/bin/env python3
"""
03_dividir_treino_teste.py — separa treino / validacao / teste SEM VAZAMENTO.

O erro classico deste tipo de projeto: uma observacao do iNaturalist tem 2 a 5 fotos
do MESMO inseto, tiradas no mesmo minuto. Se duas delas caem em treino e teste, o
modelo ja viu a resposta e a acuracia sobe sem significar nada.

Por isso o split e' feito por OBSERVACAO (o prefixo do nome do arquivo, que o
script 01 gravou como a chave da ocorrencia GBIF), nunca por foto.

Regra separada e importante:
    Toda foto tirada por voces em campo vai OBRIGATORIAMENTE para o TESTE.
    E' o unico conjunto que mede o que o sistema vai enfrentar de verdade.
    Coloque essas fotos em dados/bruto_campo/<classe>/.

Uso:
    python 03_dividir_treino_teste.py
"""

import random
import shutil
from collections import defaultdict
from pathlib import Path

RAIZ_WEB = Path("dados/bruto")         # fotos publicas (GBIF etc.)
RAIZ_CAMPO = Path("dados/bruto_campo") # fotos tiradas por voces
SAIDA = Path("dados/split")
PROP = {"treino": 0.70, "val": 0.15, "teste": 0.15}
SEMENTE = 42


def id_observacao(p: Path) -> str:
    """'4562231_2.jpg' -> '4562231'. Fotos da mesma observacao ficam juntas."""
    return p.stem.split("_")[0]


def main():
    random.seed(SEMENTE)
    for split in PROP:
        for classe_dir in RAIZ_WEB.iterdir():
            if classe_dir.is_dir():
                (SAIDA / split / classe_dir.name).mkdir(parents=True, exist_ok=True)

    resumo = defaultdict(lambda: defaultdict(int))

    # --- fotos publicas: split por observacao ---
    for classe_dir in sorted(p for p in RAIZ_WEB.iterdir() if p.is_dir()):
        classe = classe_dir.name
        grupos = defaultdict(list)
        for foto in classe_dir.glob("*"):
            if foto.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                grupos[id_observacao(foto)].append(foto)

        ids = sorted(grupos)
        random.shuffle(ids)
        n = len(ids)
        c_treino = int(n * PROP["treino"])
        c_val = int(n * (PROP["treino"] + PROP["val"]))

        for i, obs in enumerate(ids):
            split = "treino" if i < c_treino else ("val" if i < c_val else "teste")
            for foto in grupos[obs]:
                shutil.copy2(foto, SAIDA / split / classe / foto.name)
                resumo[classe][split] += 1

    # --- fotos de campo: TODAS para teste ---
    if RAIZ_CAMPO.exists():
        for classe_dir in sorted(p for p in RAIZ_CAMPO.iterdir() if p.is_dir()):
            classe = classe_dir.name
            alvo = SAIDA / "teste_campo" / classe
            alvo.mkdir(parents=True, exist_ok=True)
            for foto in classe_dir.glob("*"):
                if foto.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                    shutil.copy2(foto, alvo / foto.name)
                    resumo[classe]["teste_campo"] += 1

    print(f"{'classe':<20} {'treino':>8} {'val':>8} {'teste':>8} {'campo':>8}")
    print("-" * 56)
    for classe in sorted(resumo):
        r = resumo[classe]
        print(f"{classe:<20} {r['treino']:>8} {r['val']:>8} "
              f"{r['teste']:>8} {r['teste_campo']:>8}")

    print("\nDois numeros vao para o relatorio, sempre os dois:")
    print("  acuracia em 'teste'        -> imagens publicas, condicao facil")
    print("  acuracia em 'teste_campo'  -> foto real de lavoura, o numero que importa")
    print("\nSe o segundo for muito menor, isso NAO e' fracasso: e' o achado do trabalho.")
    print("Explique por que caiu (fundo, luz, escala, distancia) na secao de resultados.")


if __name__ == "__main__":
    main()
