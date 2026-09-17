#!/usr/bin/env python3
"""
01_baixar_gbif.py — baixa fotos de campo de pragas do milho a partir do GBIF.

Por que GBIF e não Google Imagens:
  - A licença de cada registro vem declarada e é filtrável (CC0 / CC-BY).
  - Dá para exigir foto de CAMPO (basisOfRecord=HUMAN_OBSERVATION) e descartar
    espécime de museu com fundo branco, que destruiria o treino.
  - API pública, sem chave, sem conta.

Uso:
    pip install requests tqdm
    python 01_baixar_gbif.py --teste            # baixa 5 fotos por classe, para conferir
    python 01_baixar_gbif.py --max-por-classe 600

Saída:
    dados/bruto/<classe>/<gbif_key>_<n>.jpg
    dados/creditos.csv        <- licença e autor de CADA foto. NÃO PERCA ESTE ARQUIVO.

Regra de ouro: se a foto não tem licença registrada aqui, ela não entra no dataset.
"""

import argparse
import csv
import os
import time
from pathlib import Path

import requests

GBIF = "https://api.gbif.org/v1"

# Cuidado: o nome aceito no GBIF nem sempre é o nome que a literatura brasileira usa.
# Ex.: "Elasmopalpus lignosellus" retorna ZERO; o aceito é "Elasmopalpus lignosella".
# Por isso o script resolve o taxonKey pela API antes de baixar, em vez de chutar.
CLASSES = {
    "lagarta_cartucho": "Spodoptera frugiperda",
    "lagarta_espiga": "Helicoverpa zea",
    "vaquinha": "Diabrotica speciosa",
    "lagarta_elasmo": "Elasmopalpus lignosella",
}

# "lagarta_X" é o estágio larval — mas a maioria das fotos no GBIF/iNaturalist
# é de MARIPOSA ADULTA (quem fotografa bicho de jardim fotografa o que voa e
# pousa, não a larva escondida na folha). Medido ao vivo: Spodoptera frugiperda
# tem 1417 fotos de adulto contra 70 de larva; Helicoverpa zea, 2180 x 54.
# Sem este filtro, o classificador aprenderia "mariposa marrom" em vez do dano
# que o produtor realmente fotografa. "vaquinha" fica de fora do filtro porque
# ali a praga QUE SE FOTOGRAFA é o besouro adulto.
LIFE_STAGE_LARVA = {"lagarta_cartucho", "lagarta_espiga", "lagarta_elasmo"}
LIFE_STAGES_ACEITOS = ["Larva", "Caterpillar", "Immature"]

# Só licenças que permitem redistribuir. Se quiser mais volume e o trabalho for
# só acadêmico sem publicar o dataset, acrescente "CC_BY_NC_4_0" — mas então
# NÃO publique o dataset montado no GitHub.
LICENCAS = ["CC0_1_0", "CC_BY_4_0"]

HEADERS = {"User-Agent": "UPX-Facens-DoutorDaRoca/1.0 (projeto academico)"}


def resolver_taxon_key(nome_cientifico: str) -> int | None:
    r = requests.get(
        f"{GBIF}/species/match",
        params={"name": nome_cientifico, "strict": "false"},
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    d = r.json()
    key = d.get("usageKey")
    if not key:
        print(f"  !! nao consegui resolver '{nome_cientifico}' — confira a grafia")
        return None
    print(f"  taxonKey={key}  ({d.get('scientificName')}, match={d.get('matchType')})")
    return key


def buscar_ocorrencias(taxon_key: int, limite: int, life_stages: list[str] | None = None):
    """Pagina a busca do GBIF. Devolve (occ_key, url_foto, licenca, autor)."""
    achados = []
    offset = 0
    page = 300  # máximo aceito pela API
    while len(achados) < limite:
        params = [
            ("taxonKey", taxon_key),
            ("mediaType", "StillImage"),
            ("basisOfRecord", "HUMAN_OBSERVATION"),  # <- descarta museu. NÃO REMOVA.
            ("limit", page),
            ("offset", offset),
        ]
        params += [("license", l) for l in LICENCAS]
        if life_stages:
            params += [("lifeStage", s) for s in life_stages]

        r = requests.get(f"{GBIF}/occurrence/search", params=params,
                         headers=HEADERS, timeout=60)
        r.raise_for_status()
        d = r.json()
        results = d.get("results", [])
        if not results:
            break

        for occ in results:
            for m in occ.get("media", []):
                url = m.get("identifier")
                if not url:
                    continue
                achados.append((
                    occ.get("key"),
                    url,
                    m.get("license") or occ.get("license") or "",
                    m.get("rightsHolder") or occ.get("recordedBy") or "",
                ))

        offset += page
        if d.get("endOfRecords"):
            break
        time.sleep(0.3)  # boa educação com a API pública

    return achados[:limite]


def baixar(url: str, destino: Path) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        r.raise_for_status()
        ct = r.headers.get("Content-Type", "")
        if "image" not in ct:
            return False
        destino.write_bytes(r.content)
        # Descarta arquivo minúsculo (costuma ser ícone de erro ou thumb quebrado)
        if destino.stat().st_size < 8000:
            destino.unlink()
            return False
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-por-classe", type=int, default=500)
    ap.add_argument("--saida", default="dados/bruto")
    ap.add_argument("--teste", action="store_true", help="baixa so 5 por classe")
    args = ap.parse_args()

    limite = 5 if args.teste else args.max_por_classe
    raiz = Path(args.saida)
    raiz.mkdir(parents=True, exist_ok=True)

    creditos_path = Path("dados/creditos.csv")
    creditos_path.parent.mkdir(parents=True, exist_ok=True)
    novo = not creditos_path.exists()

    with creditos_path.open("a", newline="", encoding="utf-8") as fcsv:
        w = csv.writer(fcsv)
        if novo:
            w.writerow(["arquivo", "classe", "fonte", "gbif_occurrence_key",
                        "url_original", "licenca", "autor"])

        for classe, nome_sci in CLASSES.items():
            print(f"\n=== {classe}  ({nome_sci}) ===")
            key = resolver_taxon_key(nome_sci)
            if not key:
                continue

            life_stages = LIFE_STAGES_ACEITOS if classe in LIFE_STAGE_LARVA else None
            ocorrencias = buscar_ocorrencias(key, limite, life_stages)
            if life_stages:
                print(f"  filtrando por estagio de vida: {life_stages}")
            print(f"  {len(ocorrencias)} midias candidatas")

            pasta = raiz / classe
            pasta.mkdir(parents=True, exist_ok=True)

            ok = 0
            for i, (occ_key, url, lic, autor) in enumerate(ocorrencias):
                ext = ".jpg"
                # Nome do arquivo carrega a chave da OCORRÊNCIA, não da foto.
                # Isso é o que permite fazer o split sem vazamento depois (script 03).
                nome = f"{occ_key}_{i}{ext}"
                destino = pasta / nome
                if destino.exists():
                    continue
                if baixar(url, destino):
                    ok += 1
                    w.writerow([str(destino), classe, "GBIF", occ_key, url, lic, autor])
                time.sleep(0.2)

            print(f"  baixadas: {ok}")

    print("\nPronto. Confira dados/creditos.csv — sem ele voce nao consegue")
    print("provar a licenca das imagens na apresentacao.")


if __name__ == "__main__":
    main()
