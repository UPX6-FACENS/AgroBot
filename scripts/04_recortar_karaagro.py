#!/usr/bin/env python3
"""
04_recortar_karaagro.py — recorta o dataset KaraAgro AI Maize pelas caixas
de anotacao (PASCAL VOC) e gera fotos no mesmo estilo das do GBIF.

Contexto (ver docs/04-guia-dataset.md, secao 1.2): o GBIF sozinho nao tem
volume suficiente de LARVA de lagarta-do-cartucho (a maioria das fotos
publicas e' de mariposa adulta). O KaraAgro AI Maize
(Harvard Dataverse, DOI 10.7910/DVN/CXUMDS, licenca CC BY) tem 512+ fotos
de campo em Gana, cada uma com objetos anotados:

    fall-armyworm-larva            <- a lagarta em si
    fall-armyworm-larval-damage    <- folha raspada, o "cartucho raspado"
    fall-armyworm-frass            <- excremento no cartucho
    fall-armyworm-egg              <- postura de ovos

Os quatro sao sinais que o produtor pode fotografar (ver docs/03), entao
todos viram exemplos da classe `lagarta_cartucho`.

Uso:
    1. Baixe um ou mais arquivos faw_NN.rar/.zip do Dataverse e extraia
       (imagem .jpeg + anotacao .xml, mesmo nome) para uma pasta, ex.:
           dados/_karaagro_raw/extraido/
    2. python scripts/04_recortar_karaagro.py --dir dados/_karaagro_raw/extraido

Saida:
    dados/bruto/lagarta_cartucho/<nome_da_foto>_<n>.jpg
    dados/creditos.csv  (acrescenta, nao sobrescreve)
"""

import argparse
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

FONTE = "KaraAgro AI Maize (Harvard Dataverse, DOI 10.7910/DVN/CXUMDS)"
LICENCA = "CC BY"
AUTOR = "KaraAgro AI Foundation"

# Caixa muito pequena (< 40px de lado) fica ilegivel depois do resize para
# o classificador (224px) — mais atrapalha o treino do que ajuda.
LADO_MINIMO_PX = 40

# Margem de contexto ao redor da caixa anotada — sem isso, o recorte fica
# colado no objeto e perde a folha ao redor, que tambem e' sinal visual.
MARGEM = 0.15


def caixas_do_xml(caminho_xml: Path):
    """Algumas anotacoes do KaraAgro vem com xmin/xmax ou ymin/ymax trocados
    — normaliza com min/max em vez de confiar na ordem do XML."""
    tree = ET.parse(caminho_xml)
    for obj in tree.findall(".//object"):
        nome = obj.findtext("name", "").strip()
        box = obj.find("bndbox")
        if box is None:
            continue
        x1 = int(float(box.findtext("xmin")))
        y1 = int(float(box.findtext("ymin")))
        x2 = int(float(box.findtext("xmax")))
        y2 = int(float(box.findtext("ymax")))
        yield nome, (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))


def recortar_com_margem(img: Image.Image, caixa):
    """Devolve None se a caixa, mesmo normalizada, nao cabe na imagem
    (coordenada fora dos limites — outro problema visto nos dados do
    KaraAgro)."""
    xmin, ymin, xmax, ymax = caixa
    xmin, ymin = max(0, xmin), max(0, ymin)
    xmax, ymax = min(img.width, xmax), min(img.height, ymax)
    if xmax <= xmin or ymax <= ymin:
        return None

    w, h = xmax - xmin, ymax - ymin
    mx, my = int(w * MARGEM), int(h * MARGEM)
    esq = max(0, xmin - mx)
    topo = max(0, ymin - my)
    dir_ = min(img.width, xmax + mx)
    fundo = min(img.height, ymax + my)
    return img.crop((esq, topo, dir_, fundo))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="pasta com pares .jpeg/.xml extraidos")
    ap.add_argument("--classe", default="lagarta_cartucho")
    ap.add_argument(
        "--objetos",
        default="fall-armyworm-larva,fall-armyworm-larval-damage,"
                "fall-armyworm-frass,fall-armyworm-egg",
        help="nomes de objeto do XML a recortar, separados por virgula",
    )
    ap.add_argument("--saida", default="dados/bruto")
    args = ap.parse_args()

    objetos_alvo = set(args.objetos.split(","))
    raiz = Path(args.dir)
    pasta_saida = Path(args.saida) / args.classe
    pasta_saida.mkdir(parents=True, exist_ok=True)

    creditos_path = Path("dados/creditos.csv")
    creditos_path.parent.mkdir(parents=True, exist_ok=True)
    novo = not creditos_path.exists()

    xmls = sorted(raiz.rglob("*.xml"))
    print(f"{len(xmls)} anotacoes encontradas em {raiz}")

    contagem_por_tipo = {}
    total_recortado = 0
    fotos_sem_imagem = 0

    with creditos_path.open("a", newline="", encoding="utf-8") as fcsv:
        w = csv.writer(fcsv)
        if novo:
            w.writerow(["arquivo", "classe", "fonte", "gbif_occurrence_key",
                        "url_original", "licenca", "autor"])

        for caminho_xml in xmls:
            caminho_img = caminho_xml.with_suffix(".jpeg")
            if not caminho_img.exists():
                caminho_img = caminho_xml.with_suffix(".jpg")
            if not caminho_img.exists():
                fotos_sem_imagem += 1
                continue

            try:
                img = Image.open(caminho_img).convert("RGB")
            except Exception:
                fotos_sem_imagem += 1
                continue

            # vira a chave de observacao no script 03, que agrupa cortando no
            # PRIMEIRO "_" do nome do arquivo. Nomes originais do KaraAgro nao
            # seguem um padrao unico (tem UUID-com-hifen, mas tambem
            # "IMG_20210610_..." e "uuid_xxxx") — sem sanitizar, script 03
            # juntaria centenas de fotos de origens diferentes num so grupo
            # "IMG" ou "uuid", quebrando o split sem vazamento.
            base = caminho_img.stem.replace("_", "-")
            idx = 0
            for nome, caixa in caixas_do_xml(caminho_xml):
                if nome not in objetos_alvo:
                    continue
                xmin, ymin, xmax, ymax = caixa
                if (xmax - xmin) < LADO_MINIMO_PX or (ymax - ymin) < LADO_MINIMO_PX:
                    continue

                recorte = recortar_com_margem(img, caixa)
                if recorte is None:
                    continue
                nome_arquivo = f"{base}_{idx}.jpg"
                destino = pasta_saida / nome_arquivo
                recorte.save(destino, "JPEG", quality=90)

                w.writerow([str(destino), args.classe, FONTE, base, "", LICENCA, AUTOR])
                contagem_por_tipo[nome] = contagem_por_tipo.get(nome, 0) + 1
                total_recortado += 1
                idx += 1

    print(f"\nRecortadas: {total_recortado}")
    for nome, n in sorted(contagem_por_tipo.items()):
        print(f"  {nome}: {n}")
    if fotos_sem_imagem:
        print(f"\nAviso: {fotos_sem_imagem} XML sem imagem correspondente (ignorados)")
    print(f"\nGravado em {pasta_saida}/ e creditos.csv atualizado.")


if __name__ == "__main__":
    main()
