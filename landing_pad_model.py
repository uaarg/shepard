from ultralytics import YOLO

model =YOLO('yolo11n.pt')

model.train(
    data="landingpad.yaml",  # your dataset YAML
    epochs=50,
    imgsz=640,
    batch=16,
    lr0=0.01,
    name="landingpad_run"
)

results = model("landing_pad_dataset/images/val/sample.jpeg")
results.show()