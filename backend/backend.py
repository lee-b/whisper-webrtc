from pprint import pprint
from fastapi import FastAPI, Body, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import whisper
import webrtc
import uvicorn
import asyncio
import time
import nest_asyncio
nest_asyncio.apply()

app = FastAPI()

origins_allowed = [
    "http://localhost:5173",
]

model_name = "tiny"
model = whisper.load_model(model_name)
preffered_lang = "en"


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_allowed,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
async def main():
    return {"ping": "pong"}

@app.post("/initmodel")
async def initmodel(item: dict = Body(...)):
    global model_name, preffered_lang, model
    
    model_name_temp = item["model"]
    if model_name_temp != model_name:
        model_name = model_name_temp
        model = whisper.load_model(model_name)
    preffered_lang = item["language"]
    return {"model": model_name, "language": preffered_lang}

@app.post("/offer")
async def offer(item: dict = Body(...)):
    sdp = item["sdp"]
    type = item["type"]
    resp = await webrtc.offer(sdp, type) 
    return resp

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    filename = file.filename
    with open("data/"+filename, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return {"filename": filename}

async def Transribe(filename, language, webrtcdatachannel):

    async def flush(channel):
        await channel._RTCDataChannel__transport._data_channel_flush()
        await channel._RTCDataChannel__transport._transmit()
    
    def on_message(message):
        webrtcdatachannel.send(message)
        asyncio.get_event_loop().run_until_complete(flush(webrtcdatachannel))

    result = model.transcribe("data/"+filename, language=language, webrtcsend_method=on_message)

@app.post("/infer")
async def infer(item: dict = Body(...)):
    filename = item["filename"]
    if model_name.endswith(".en"):
        language = "en"
    else:
        language = preffered_lang

    asyncio.create_task(Transribe(filename, language, webrtc.webrtcdatachannel))
    return []

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)