import cv2
import numpy as np
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = YOLO('yolov8n.pt')

def decode_base64_image(base64_str):
    img_bytes = base64.b64decode(base64_str.split(",")[1])
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return img

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            frame = decode_base64_image(data)

            results = model(frame)[0]
            people = [box for box in results.boxes if int(box.cls) == 0]

            boxes = []
            for box in people:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                boxes.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "conf": conf})

            response = {
                "count": len(people),
                "boxes": boxes
            }

            await websocket.send_json(response)
    except WebSocketDisconnect:
        print("Client disconnected")
