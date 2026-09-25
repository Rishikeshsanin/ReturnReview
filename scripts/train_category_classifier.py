"""Train a lightweight cardboard-box category classifier using MobileNetV3-Small."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import MobileNet_V3_Small_Weights, mobilenet_v3_small


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--epochs",type=int,default=8)
    p.add_argument("--batch",type=int,default=16)
    p.add_argument("--lr",type=float,default=1e-3)
    p.add_argument("--seed",type=int,default=20260925)
    args=p.parse_args()

    torch.manual_seed(args.seed)
    root=Path(args.root)
    weights=MobileNet_V3_Small_Weights.DEFAULT
    mean=weights.transforms().mean
    std=weights.transforms().std

    train_tf=transforms.Compose([
        transforms.Resize((224,224)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.15,contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean,std=std),
    ])
    eval_tf=transforms.Compose([
        transforms.Resize((224,224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean,std=std),
    ])

    train_ds=datasets.ImageFolder(root/"train",transform=train_tf)
    val_ds=datasets.ImageFolder(root/"val",transform=eval_tf)
    if train_ds.class_to_idx != val_ds.class_to_idx:
        raise SystemExit("Train/val class mappings differ")

    train_loader=DataLoader(train_ds,batch_size=args.batch,shuffle=True,num_workers=2)
    val_loader=DataLoader(val_ds,batch_size=args.batch,shuffle=False,num_workers=2)

    model=mobilenet_v3_small(weights=weights)
    for param in model.features.parameters():
        param.requires_grad=False
    in_features=model.classifier[3].in_features
    model.classifier[3]=nn.Linear(in_features,2)

    criterion=nn.CrossEntropyLoss()
    optimizer=torch.optim.AdamW(model.classifier.parameters(),lr=args.lr)
    best_acc=-1.0
    best_state=None
    history=[]

    for epoch in range(1,args.epochs+1):
        model.train()
        total=correct=0
        loss_sum=0.0
        for x,y in train_loader:
            optimizer.zero_grad()
            logits=model(x)
            loss=criterion(logits,y)
            loss.backward()
            optimizer.step()
            loss_sum+=float(loss.item())*len(y)
            correct+=int((logits.argmax(1)==y).sum().item())
            total+=len(y)

        model.eval()
        vtotal=vcorrect=0
        with torch.no_grad():
            for x,y in val_loader:
                pred=model(x).argmax(1)
                vcorrect+=int((pred==y).sum().item())
                vtotal+=len(y)
        val_acc=vcorrect/vtotal if vtotal else 0.0
        row={
            "epoch":epoch,
            "train_loss":loss_sum/total if total else None,
            "train_accuracy":correct/total if total else None,
            "val_accuracy":val_acc,
        }
        history.append(row)
        print(json.dumps(row),flush=True)
        if val_acc>best_acc:
            best_acc=val_acc
            best_state={k:v.cpu() for k,v in model.state_dict().items()}

    if best_state is None:
        raise SystemExit("Training produced no checkpoint")
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    torch.save({
        "state_dict":best_state,
        "architecture":"mobilenet_v3_small",
        "classes":train_ds.classes,
        "class_to_idx":train_ds.class_to_idx,
        "image_size":224,
        "normalization":{"mean":mean,"std":std},
        "best_val_accuracy":best_acc,
        "seed":args.seed,
    },out)
    (out.with_suffix(".training.json")).write_text(json.dumps({
        "best_val_accuracy":best_acc,
        "history":history,
        "classes":train_ds.classes,
        "class_to_idx":train_ds.class_to_idx,
    },indent=2)+"\n")
    print(out)


if __name__=="__main__":
    main()
