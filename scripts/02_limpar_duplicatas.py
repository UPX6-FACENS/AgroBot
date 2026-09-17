#!/usr/bin/env python3
"""
02_limpar_duplicatas.py — remove imagem repetida, corrompida, pequena demais ou borrada.

Por que isso importa: iNaturalist, GBIF e Roboflow se sobrepoem MUITO. Se a mesma
foto cair em treino e em teste, sua acuracia vai mentir e a banca pode perceber.

Uso:
    pip install pillow imagehash opencv-python-headless
    python 02_limpar_duplicatas.py --dir dados/bruto
    python 02_limpar_duplicatas.py --dir dados/bruto --aplicar   # de fato move

Sem --aplicar ele so relata. Os descartes vao para dados/descartado/<motivo>/,
nunca sao apagados — voce pode querer revisar.
"""

import argparse
import shutil
from collections import defaultdict
from pathlib import Path

import cv2
import imagehash
from PIL import Image

MIN_LADO = 224          # menor que isso nao serve para MobileNet/EfficientNet
LIMIAR_BORRAO = 60.0    # variancia do Laplaciano; calibre olhando os descartes
DIST_HASH = 4           # distancia de Hamming para considerar duplicata


def variancia_laplaciano(caminho: Path) -> float:
    """Variancia do Laplaciano pelo MAXIMO entre blocos 4x4 da imagem, nao
    pela imagem inteira. Motivo (achado ao calibrar com dados/descartado/):
    foto de macro com profundidade de campo rasa (inseto nitido, fundo
    desfocado de proposito) tem variancia BAIXA na imagem inteira mesmo
    sendo uma otima foto — a media dilui o bloco nitido com o fundo turvo.
    Uma foto de verdade borrada (mao tremida) fica com TODOS os blocos com
    variancia baixa; e' essa a diferenca que queremos capturar."""
    img = cv2.imread(str(caminho), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return -1.0
    h, w = img.shape
    n = 4
    bh, bw = h // n, w // n
    if bh < 8 or bw < 8:
        return float(cv2.Laplacian(img, cv2.CV_64F).var())
    melhores = []
    for i in range(n):
        for j in range(n):
            bloco = img[i * bh:(i + 1) * bh, j * bw:(j + 1) * bw]
            melhores.append(cv2.Laplacian(bloco, cv2.CV_64F).var())
    return float(max(melhores))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="dados/bruto")
    ap.add_argument("--aplicar", action="store_true")
    args = ap.parse_args()

    raiz = Path(args.dir)
    descarte = Path("dados/descartado")

    hashes: dict[imagehash.ImageHash, Path] = {}
    contagem = defaultdict(int)

    arquivos = sorted(p for p in raiz.rglob("*") if p.suffix.lower() in
                      {".jpg", ".jpeg", ".png", ".webp"})
    print(f"{len(arquivos)} arquivos encontrados\n")

    for p in arquivos:
        motivo = None

        try:
            with Image.open(p) as im:
                im.verify()
            with Image.open(p) as im:
                im = im.convert("RGB")
                w, h = im.size
                h_img = imagehash.phash(im)
        except Exception:
            motivo = "corrompida"
            h_img = None
            w = h = 0

        if motivo is None and min(w, h) < MIN_LADO:
            motivo = "pequena"

        if motivo is None:
            v = variancia_laplaciano(p)
            if 0 <= v < LIMIAR_BORRAO:
                motivo = "borrada"

        if motivo is None and h_img is not None:
            for h_ref, p_ref in hashes.items():
                if h_img - h_ref <= DIST_HASH:
                    motivo = "duplicata"
                    break
            if motivo is None:
                hashes[h_img] = p

        if motivo:
            contagem[motivo] += 1
            if args.aplicar:
                alvo = descarte / motivo / p.parent.name
                alvo.mkdir(parents=True, exist_ok=True)
                shutil.move(str(p), str(alvo / p.name))

    print("Descartes:")
    for k, v in sorted(contagem.items()):
        print(f"  {k:12s} {v}")
    total = sum(contagem.values())
    print(f"\nsobram {len(arquivos) - total} imagens")
    if not args.aplicar:
        print("\n(simulacao — rode de novo com --aplicar para mover de verdade)")
    else:
        print("\nOlhe dados/descartado/borrada/ antes de confiar no limiar.")
        print("Se tiver foto boa la, aumente LIMIAR_BORRAO; se sobrou foto ruim, diminua.")


if __name__ == "__main__":
    main()
