"""Evaluate the lightweight cardboard-box category classifier on held-out test images."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import mobilenet_v3_small


def load_model(path:Path):
    payload=torch.load(path,map_location="cpu",weights_only=False)
    model=mobilenet_v3_small(weights=None)
    model.classifier[3]=nn.Linear(model.classifier[3].in_features,2)
    model.load_state_dict(payload["state_dict"])
    model.eval()
    norm=payload["normalization"]
    tf=transforms.Compose([
        transforms.Resize((payload.get("image_size",224),payload.get("image_size",224))),
        transforms.ToTensor(),
        transforms.Normalize(mean=norm["mean"],std=norm["std"]),
    ])
    return model,tf,payload


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--model",required=True)
    p.add_argument("--test-root",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()

    model,tf,payload=load_model(Path(args.model))
    ds=datasets.ImageFolder(Path(args.test_root),transform=tf)
    if ds.class_to_idx != payload["class_to_idx"]:
        raise SystemExit("Checkpoint/test class mapping mismatch")
    loader=DataLoader(ds,batch_size=16,shuffle=False,num_workers=2)

    y_true=[]; y_pred=[]; probs=[]
    with torch.no_grad():
        for x,y in loader:
            logits=model(x)
            pr=torch.softmax(logits,dim=1)
            pred=pr.argmax(1)
            y_true.extend(y.tolist()); y_pred.extend(pred.tolist()); probs.extend(pr.tolist())

    positive_idx=payload["class_to_idx"]["cardboard_box"]
    tp=sum(t==positive_idx and p==positive_idx for t,p in zip(y_true,y_pred))
    tn=sum(t!=positive_idx and p!=positive_idx for t,p in zip(y_true,y_pred))
    fp=sum(t!=positive_idx and p==positive_idx for t,p in zip(y_true,y_pred))
    fn=sum(t==positive_idx and p!=positive_idx for t,p in zip(y_true,y_pred))
    total=len(y_true)
    precision=tp/(tp+fp) if tp+fp else 0.0
    recall=tp/(tp+fn) if tp+fn else 0.0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
    payload_out={
        "product_verification":{
            "test_samples":total,
            "accuracy":(tp+tn)/total if total else 0.0,
            "precision":precision,
            "recall":recall,
            "f1":f1,
            "false_accept_rate":fp/(fp+tn) if fp+tn else 0.0,
            "false_reject_rate":fn/(fn+tp) if fn+tp else 0.0,
            "confusion":{"tp":tp,"tn":tn,"fp":fp,"fn":fn},
            "model":"mobilenet_v3_small",
            "best_validation_accuracy":payload.get("best_val_accuracy"),
        },
        "provenance":"Held-out source-split cardboard positives and disjoint generic COCO negatives.",
    }
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload_out,indent=2)+"\n")
    print(json.dumps(payload_out,indent=2))


if __name__=="__main__":
    main()
