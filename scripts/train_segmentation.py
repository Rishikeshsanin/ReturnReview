"""Train binary damage segmentation on a validated YOLO-seg dataset."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--model", default="yolo11n-seg.pt")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260924)
    parser.add_argument("--project", default="runs/returnreview")
    parser.add_argument("--name", default="damage-seg")
    args = parser.parse_args()

    from ultralytics import YOLO

    data_path = str(Path(args.data).resolve())
    project_path = str(Path(args.project).resolve())

    model = YOLO(args.model)
    result = model.train(
        data=data_path,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        workers=args.workers,
        seed=args.seed,
        deterministic=True,
        project=project_path,
        name=args.name,
        exist_ok=False,
        plots=True,
    )
    print(f"training_project={project_path}")
    print(result)


if __name__ == "__main__":
    main()
