#!/usr/bin/env python3
"""
05_treinar_cnn.py — treina o classificador de pragas por transfer learning.

Segue a stack definida em docs/02-arquitetura.md secao 9: MobileNetV3-Large
pre-treinada na ImageNet, so o classificador e' re-treinado (o "extrator de
features" fica congelado) — roda em CPU em minutos, sem precisar de GPU.

Augmentation (docs/04-guia-dataset.md, Fase 5) so entra no TREINO, nunca em
validacao/teste: rotacao, brilho/contraste, blur leve, recorte aleatorio,
ruido leve. Sem flip vertical (planta nao fica de cabeca pra baixo) e sem
distorcer cor agressivamente (a cor da lagarta e' informacao).

Classes com muito mais foto que outras (lagarta_cartucho tem ~30x mais que
lagarta_espiga agora) usam peso na loss — sem isso o modelo aprende a
sempre chutar a classe majoritaria e ainda parece ter acuracia alta.

Uso:
    python scripts/05_treinar_cnn.py
    python scripts/05_treinar_cnn.py --epocas 12 --lote 32

Saida:
    checkpoints/modelo_melhor.pt   (pesos do melhor epoch por F1-macro no val)
    checkpoints/modelo.onnx        (exportado para rodar em producao)
    checkpoints/matriz_confusao.png
    checkpoints/classes.json       (ordem das classes — o worker precisa disso)
"""

import argparse
import json
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

MEDIA_IMAGENET = [0.485, 0.456, 0.406]
DESVIO_IMAGENET = [0.229, 0.224, 0.225]


def ruido_leve(tensor, sigma=0.03):
    return tensor + torch.randn_like(tensor) * sigma


def montar_transforms():
    treino = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(30),
        transforms.ColorJitter(brightness=0.3, contrast=0.3),
        transforms.RandomApply([transforms.GaussianBlur(3)], p=0.3),
        transforms.ToTensor(),
        transforms.Lambda(ruido_leve),
        transforms.Normalize(MEDIA_IMAGENET, DESVIO_IMAGENET),
    ])
    val = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(MEDIA_IMAGENET, DESVIO_IMAGENET),
    ])
    return treino, val


def montar_modelo(num_classes: int):
    pesos = models.MobileNet_V3_Large_Weights.DEFAULT
    modelo = models.mobilenet_v3_large(weights=pesos)
    for p in modelo.features.parameters():
        p.requires_grad = False
    in_features = modelo.classifier[-1].in_features
    modelo.classifier[-1] = nn.Linear(in_features, num_classes)
    return modelo


def pesos_por_classe(dataset: datasets.ImageFolder) -> torch.Tensor:
    contagem = torch.zeros(len(dataset.classes))
    for _, y in dataset.samples:
        contagem[y] += 1
    peso = contagem.sum() / (len(contagem) * contagem)
    return peso


def treinar_um_epoch(modelo, loader, otim, perda_fn, device):
    modelo.train()
    total, acertos, perda_acum = 0, 0, 0.0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        otim.zero_grad()
        saida = modelo(x)
        perda = perda_fn(saida, y)
        perda.backward()
        otim.step()
        perda_acum += perda.item() * x.size(0)
        acertos += (saida.argmax(1) == y).sum().item()
        total += x.size(0)
    return perda_acum / total, acertos / total


@torch.no_grad()
def avaliar(modelo, loader, perda_fn, device):
    modelo.eval()
    total, acertos, perda_acum = 0, 0, 0.0
    y_verdadeiro, y_previsto = [], []
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        saida = modelo(x)
        perda = perda_fn(saida, y)
        perda_acum += perda.item() * x.size(0)
        pred = saida.argmax(1)
        acertos += (pred == y).sum().item()
        total += x.size(0)
        y_verdadeiro += y.cpu().tolist()
        y_previsto += pred.cpu().tolist()
    return perda_acum / total, acertos / total, y_verdadeiro, y_previsto


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="dados/split")
    ap.add_argument("--epocas", type=int, default=10)
    ap.add_argument("--lote", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--saida", default="checkpoints")
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device: {device}")

    tf_treino, tf_val = montar_transforms()
    ds_treino = datasets.ImageFolder(f"{args.dir}/treino", transform=tf_treino)
    ds_val = datasets.ImageFolder(f"{args.dir}/val", transform=tf_val)
    assert ds_treino.classes == ds_val.classes, "treino e val com classes diferentes"
    classes = ds_treino.classes
    print(f"classes ({len(classes)}): {classes}")

    dl_treino = DataLoader(ds_treino, batch_size=args.lote, shuffle=True,
                            num_workers=0)
    dl_val = DataLoader(ds_val, batch_size=args.lote, shuffle=False,
                         num_workers=0)

    modelo = montar_modelo(len(classes)).to(device)
    peso = pesos_por_classe(ds_treino).to(device)
    print("peso por classe (inverso da frequencia):",
          {c: round(w, 2) for c, w in zip(classes, peso.tolist())})
    perda_fn = nn.CrossEntropyLoss(weight=peso)
    otim = torch.optim.Adam(
        [p for p in modelo.parameters() if p.requires_grad], lr=args.lr
    )

    saida = Path(args.saida)
    saida.mkdir(exist_ok=True)
    melhor_f1 = -1.0

    from sklearn.metrics import f1_score

    for epoch in range(1, args.epocas + 1):
        perda_tr, acc_tr = treinar_um_epoch(modelo, dl_treino, otim, perda_fn, device)
        perda_val, acc_val, y_verd, y_prev = avaliar(modelo, dl_val, perda_fn, device)
        f1_macro = f1_score(y_verd, y_prev, average="macro", zero_division=0)
        print(f"epoch {epoch:2d}/{args.epocas}  "
              f"treino: perda={perda_tr:.3f} acc={acc_tr:.3f}  "
              f"val: perda={perda_val:.3f} acc={acc_val:.3f} f1_macro={f1_macro:.3f}")

        if f1_macro > melhor_f1:
            melhor_f1 = f1_macro
            torch.save(modelo.state_dict(), saida / "modelo_melhor.pt")
            melhor_y_verd, melhor_y_prev = y_verd, y_prev

    print(f"\nMelhor F1-macro no val: {melhor_f1:.3f}")

    (saida / "classes.json").write_text(
        json.dumps(classes, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    from sklearn.metrics import classification_report, confusion_matrix
    print("\nRelatorio por classe (melhor epoch):")
    print(classification_report(melhor_y_verd, melhor_y_prev,
                                 target_names=classes, zero_division=0))

    cm = confusion_matrix(melhor_y_verd, melhor_y_prev)
    _salvar_matriz_confusao(cm, classes, saida / "matriz_confusao.png")

    # exporta o MELHOR checkpoint (nao o ultimo epoch) para ONNX
    modelo.load_state_dict(torch.load(saida / "modelo_melhor.pt"))
    modelo.eval()
    exemplo = torch.randn(1, 3, 224, 224)
    # dynamo=False: usa o exportador legado (TorchScript), compativel com
    # dynamic_axes. O exportador novo (dynamo=True, padrao no PyTorch 2.13)
    # tenta imprimir um emoji no log e quebra em console Windows com
    # codepage cp1252 — nada a ver com o modelo em si.
    torch.onnx.export(
        modelo, exemplo, str(saida / "modelo.onnx"),
        input_names=["foto"], output_names=["logits"],
        dynamic_axes={"foto": {0: "lote"}, "logits": {0: "lote"}},
        opset_version=17, dynamo=False,
    )
    print(f"\nExportado: {saida}/modelo.onnx")
    print(f"Salvo: {saida}/modelo_melhor.pt, {saida}/classes.json, "
          f"{saida}/matriz_confusao.png")


def _salvar_matriz_confusao(cm, classes, caminho):
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(classes)))
    ax.set_yticks(range(len(classes)))
    ax.set_xticklabels(classes, rotation=45, ha="right")
    ax.set_yticklabels(classes)
    ax.set_xlabel("Previsto")
    ax.set_ylabel("Verdadeiro")
    ax.set_title("Matriz de confusao (val)")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                     color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
