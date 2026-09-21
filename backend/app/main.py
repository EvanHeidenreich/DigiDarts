import cv2
from fastapi import FastAPI

app = FastAPI(title="DigiDarts API")


@app.get("/health")
def health():
    return {"status": "ok", "opencv_version": cv2.__version__}
