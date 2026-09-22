"""Train binary damage segmentation once annotated YOLO-seg data exists."""
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--model", default="yolo11n-seg.pt")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()
    from ultralytics import YOLO
    model = YOLO(args.model)
    result = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        project="runs/returnreview",
        name="damage-seg",
    )
    print(result)


if __name__ == "__main__":
    main()
